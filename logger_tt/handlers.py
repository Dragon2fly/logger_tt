import logging
import time
import os
import json
from urllib import request, parse, error
from collections import deque, defaultdict
from threading import Thread, Event
from datetime import datetime


root_logger = logging.getLogger('logger_tt')


class StreamHandlerWithBuffer(logging.StreamHandler):
    def __init__(self, stream=None, buffer_time: float = 0.2, buffer_lines: int = 50, debug=False):
        super().__init__(stream)
        assert buffer_time >= 0 or buffer_lines >= 0, "At least one kind of buffer must be set"

        self.buffer_time = buffer_time
        self.buffer_lines = buffer_lines
        self.buffer = []
        self.debug = debug

        self._stop_event = Event()
        if self.buffer_time:
            watcher = Thread(target=self.watcher, daemon=True)
            watcher.start()

    def close(self) -> None:
        self._stop_event.set()

    def export(self):
        """Actual writing data out to the stream"""

        if self.debug:
            self.buffer.append(f'StreamHandlerWithBuffer flush: {datetime.now()}')

        msg = self.terminator.join(self.buffer)
        stream = self.stream
        # issue 35046: merged two stream.writes into one.
        stream.write(msg + self.terminator)
        self.flush()

        self.buffer.clear()

    def emit(self, record):
        """
        Emit a record.

        If a formatter is specified, it is used to format the record.
        The record is then written to the stream with a trailing newline.  If
        exception information is present, it is formatted using
        traceback.print_exception and appended to the stream.  If the stream
        has an 'encoding' attribute, it is used to determine how to do the
        output to the stream.
        """
        try:
            msg = self.format(record)
            self.buffer.append(msg)
            if self.buffer_lines and len(self.buffer) >= self.buffer_lines:
                self.export()

        except RecursionError:  # See issue 36272
            raise
        except Exception:
            self.handleError(record)

    def watcher(self):
        """
        If buffer_time is used, this method will flush the buffer
        after every buffer_time seconds has passed.
        """
        if self.debug:
            self.buffer.append(f'StreamHandlerWithBuffer watcher starts: {datetime.now()}')
        while not self._stop_event.is_set():
            time.sleep(self.buffer_time)
            if self.buffer:
                with self.lock:
                    self.export()


class TelegramMixing:
    _base_url: str
    feedback: dict

    def set_bot_token(self, token):
        self._base_url = f"https://api.telegram.org/bot{token}/sendMessage"
    
    def _build_message_url(self, unique_id: str, text: str):
        # remove name/label if presence
        unique_id = unique_id.split(':')[-1]

        # basic params
        params = {
            'chat_id': unique_id.split('@')[0],
            'text': text,
            'disable_web_page_preview': True
        }

        # add message_thread_id if present
        if '@' in unique_id:
            params['message_thread_id'] = unique_id.split('@')[1]

        # generate a full url
        url = f"{self._base_url}?{parse.urlencode(params)}"
        return url

    @staticmethod
    def __request_handle_http_errors(exception, url: str):
        root_logger.error(exception)
        if exception.code == 403:
            # user blocked the bot
            # drop message
            return True     # Stop retrying
        if exception.code == 414:
            # Request-URI Too Large
            root_logger.info(url)
            # drop message
            return True
        if exception.code == 429:
            # too many requests
            time.sleep(1)
            return False

        # other unhandled codes
        return False

    def _request(self, _id_, full_url):
        """Return True if success or 403 or 414, otherwise False"""
        try:
            with request.urlopen(full_url) as fi:
                data = fi.read()
            self.feedback[_id_] = json.loads(data.decode())
            return True
        except json.JSONDecodeError as e:
            self.feedback[_id_] = {'error': str(e), 'data': data}
            return True
        except error.HTTPError as e:
            return self.__request_handle_http_errors(e, full_url)
        except error.URLError as e:
            time.sleep(1)
            if "[Errno -2] Name or service not known" in e.reason:
                root_logger.error(e)
            return False
        except ConnectionResetError as e:
            root_logger.info(e)
            return False
        except Exception as e:
            root_logger.error(f"Unexpected error: {str(e)}")
            return False


class TelegramHandler(logging.Handler, TelegramMixing):
    LIMIT_LENGTH = 3072     # Telegram limits to 4096 chars, we set to around a half number

    def __init__(self, token='', unique_ids='', env_token_key='', env_unique_ids_key='',
                 debug=False, check_interval=600, grouping_interval=0, push_interval=0):
        """ Init telegram handler

        :param token: str, Telegram bot token
        :param unique_ids: str, where to send the log to, "[name:]chat_id[@message_thread_id]"
        :param env_token_key: str, environment variable name that holds Telegram bot token
        :param env_unique_ids_key: str, environment variable name that holds unique_ids
        :param debug: bool, print additional log for testing
        :param check_interval: check and resend failed message every this seconds

        For grouping multiple log message into one for each sending:
        :param grouping_interval: every log message has timestamp within this seconds
            will be grouped into one message before sending
        :param push_interval: how often the log should be sent out, min: 4 seconds
        """
        super().__init__()

        # whether to send log message immediately when received or
        # group them by grouping_interval and send later
        self.grouping_interval = max(0, int(grouping_interval))
        self.push_interval = push_interval or self.grouping_interval + 4
        if self.grouping_interval and check_interval <= self.push_interval:
            raise ValueError(f'"check_interval" is too small. Should be at least {2*self.push_interval}')

        if env_token_key:
            token = os.environ.get(env_token_key, token)
        if env_unique_ids_key:
            unique_ids = os.environ.get(env_unique_ids_key, unique_ids)

        self._unique_ids = []       # type: list[str]
        self.set_unique_ids(unique_ids)
        self.set_bot_token(token)
        self.feedback = {x: {} for x in self._unique_ids}

        self.message_queue = {x: deque(maxlen=100) for x in self._unique_ids}
        self.failed_messages = {x: deque(maxlen=100) for x in self._unique_ids}

        # background thread resends the log if network error previously
        self.debug = debug
        self.check_interval = check_interval
        self._stop_event = Event()
        self._init_threads()

        # reduce sending duplicated log
        self.last_record = None
        self.last_message_hash = None
        self.dup_count = 0

    def _init_threads(self):
        watcher_thread = Thread(target=self.watcher, daemon=True)
        watcher_thread.start()
        if self.grouping_interval:
            pusher_thread = Thread(target=self.interval_pusher, daemon=True)
            pusher_thread.start()

    def format(self, record):
        txt = super().format(record) + getattr(record, 'remark', '')
        return txt

    def close(self) -> None:
        self._stop_event.set()

    def set_unique_ids(self, ids):
        if not ids:
            self._unique_ids = []
        elif type(ids) is str:
            # str from environment variable
            self._unique_ids = [x.strip() for x in ids.split(';')]
        elif type(ids) is int:
            # from config, one value
            self._unique_ids = [str(ids)]
        else:
            raise TypeError(f'Expected str or int but got type: {type(ids)}')

    def _send_request(self, _id_, msg_queue) -> bool:
        while msg_queue[_id_]:
            record = msg_queue[_id_].popleft()
            msg_out = self.format(record)
            for x in range(0, len(msg_out), self.LIMIT_LENGTH):
                chunk = msg_out[x:x + self.LIMIT_LENGTH]
                full_url = self._build_message_url(_id_, chunk)
                if not self._request(_id_, full_url):
                    msg_queue[_id_].appendleft(record)
                    return False
        else:
            return True

    def send(self):
        for _id_ in self._unique_ids:
            # try to resend failed msg
            if not self._send_request(_id_, self.failed_messages):
                # skip the current _id_
                continue

            # then send msg of this time
            if not self._send_request(_id_, self.message_queue):
                # cache to resend it later
                failed_record = self.message_queue[_id_].popleft()
                self.failed_messages[_id_].append(failed_record)
                # skip the current _id_
                continue

    @staticmethod
    def _get_message_hash(record: logging.LogRecord) -> int:
        return hash(tuple(
            getattr(record, attr, None)
            for attr in ['msg', 'name', 'levelno', 'pathname', 'lineno', 'args', 'funcName']
        ))

    def _cache_records(self, record):
        """cache msg in case of sending failure"""

        # redirect msg to appropriate cache
        if getattr(record, 'dest_name', ''):
            dest_id = next(filter(lambda x: x.startswith(f'{record.dest_name}:'), self._unique_ids), None)
            if dest_id:
                self.message_queue[dest_id].append(record)
            else:
                # do nothing, drop the message completely
                pass
        else:
            # msg to all _id_
            for _id_ in self._unique_ids:
                self.message_queue[_id_].append(record)

    def emit(self, record):
        with self.lock:
            # check and update hashing
            current_hash = self._get_message_hash(record)
            if current_hash == self.last_message_hash:
                self.dup_count += 1
                return

            self.last_message_hash = current_hash

            # emit unique message
            if self.dup_count:
                # changed to a new record, no longer duplicated
                # send last msg, then send this time msg
                self.last_record.remark = f'\n (Message repeated {self.dup_count} times)'
                self._cache_records(self.last_record)

            self.dup_count = 0
            self._cache_records(record)
            self.last_record = record
            if self.grouping_interval:
                # msg will be sent by self.interval_pusher
                pass
            else:
                self.send()

    def msg_grouping(self):
        window_size = self.grouping_interval

        for _id_ in self._unique_ids:
            group = defaultdict(list)

            # step 1: group message that are in the same time window
            while self.message_queue[_id_]:
                record = self.message_queue[_id_].popleft()
                timestamp_window = record.created // window_size * window_size
                group[timestamp_window].append(record)

            # step 2: append msg from all the following record into the first one
            for grp, item in sorted(group.items()):
                if len(item) > 1:
                    following_msg = [self.format(x) for x in item[1:]]
                    item[0].msg += '\n'.join(following_msg)

                # then flushes the grouped record back to queue
                self.message_queue[_id_].append(item[0])

    def interval_pusher(self):
        if self.debug:
            root_logger.debug(f'TelegramHandler interval_pusher starts: {datetime.now()}')

        while not self._stop_event.is_set():
            time.sleep(self.push_interval)
            if any(self.message_queue.values()):
                with self.lock:
                    self.msg_grouping()
                    self.send()

    def watcher(self):
        """
        This method will resend the failed messages if they haven't been sent in emit
        """
        if self.debug:
            root_logger.debug(f'TelegramHandler watcher starts: {datetime.now()}')

        while not self._stop_event.is_set():
            time.sleep(self.check_interval)
            if any(self.failed_messages.values()) and not self.grouping_interval:
                if self.debug:
                    root_logger.debug(f'TelegramHandler found unsent messages: {datetime.now()}')
                with self.lock:
                    self.send()

            elif self.dup_count > 1:
                if self.debug:
                    root_logger.debug(f'TelegramHandler watcher emit duplicated msg at: {datetime.now()}')
                with self.lock:
                    self.last_record.remark = f'\n (Message repeated {self.dup_count} times)'
                    self._cache_records(self.last_record)
                    self.send()
                    self.dup_count = 0

