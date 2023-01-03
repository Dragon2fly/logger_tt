import logging
import time
import json
from urllib import request, parse, error
from collections import deque
from threading import Thread
from datetime import datetime


class StreamHandlerWithBuffer(logging.StreamHandler):
    def __init__(self, stream=None, buffer_time: float = 0.2, buffer_lines: int = 50, debug=False):
        super().__init__(stream)
        assert buffer_time >= 0 or buffer_lines >= 0, "At least one kind of buffer must be set"

        self.buffer_time = buffer_time
        self.buffer_lines = buffer_lines
        self.buffer = []
        self.debug = debug

        if self.buffer_time:
            watcher = Thread(target=self.watcher, daemon=True)
            watcher.start()

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
        while True:
            time.sleep(self.buffer_time)
            if self.buffer:
                self.acquire()
                self.export()
                self.release()


class TelegramHandler(logging.Handler):
    def __init__(self, token='', unique_ids=None, debug=False, check_interval=300):
        super().__init__()
        self._unique_ids = []       # type: list[tuple[int, int]|int]
        self.set_unique_ids(unique_ids)

        self._url = f"https://api.telegram.org/bot{token}/sendMessage"
        self.feedback = {x: {} for x in unique_ids}
        self.cache = {x: deque(maxlen=100) for x in unique_ids}

        # back ground thread resends the log if network error previously
        self.debug = debug
        self.check_interval = check_interval
        self.watcher = Thread(target=self.watcher, daemon=True)
        self.is_watching = False

    def _get_full_url(self, unique_id, text):
        if type(unique_id) in [int, str]:
            # unique_id is chat_id only
            url = f'{self._url}?chat_id={unique_id}&text={text}'
        else:
            # a tuple of chat_id, message_thread_id
            chat_id, message_thread_id = unique_id
            url = f'{self._url}?chat_id={chat_id}&message_thread_id={message_thread_id}&text={text}'
        return url

    def set_bot_token(self, token: str):
        self._url = f"https://api.telegram.org/bot{token}/sendMessage"

    def set_unique_ids(self, *ids):
        if not ids:
            self._unique_ids = []
        elif len(ids) == 1 and type(ids[0]) in [list, tuple]:
            self._unique_ids = ids[0]
        else:
            self._unique_ids = [ids]

    def send(self):
        for _id_ in self._unique_ids:
            while self.cache[_id_]:
                msg_out = self.cache[_id_][0]
                full_url = self._get_full_url(_id_, msg_out)

                try:
                    with request.urlopen(full_url) as fi:
                        data = fi.read()
                    self.feedback[_id_] = json.loads(data.decode())

                    # remove from the queue after sending successfully
                    self.cache[_id_].popleft()

                except json.JSONDecodeError as e:
                    self.feedback[_id_] = {'error': str(e), 'data': data}

                except error.HTTPError as e:
                    if e.code == 403:
                        # user blocked the bot
                        logging.getLogger().error(e)

                        # remove msg
                        self.cache[_id_].popleft()
                        break
                    else:
                        # resend this msg later
                        logging.getLogger().error(e)
                        break

                except Exception as e:
                    # resend this later
                    logging.getLogger().exception(e)
                    break

    def emit(self, record):
        msg = self.format(record)

        self.acquire()
        # cache msg in case of sending failure
        for _id_ in self._unique_ids:
            if getattr(record, 'unique_id', _id_):
                # redirect msg to appropriate cache only if unique_id context is provided
                self.cache[_id_].append(parse.quote_plus(msg))
        self.send()
        self.release()

        if any(self.cache.values()) and not self.is_watching:
            self.is_watching = True
            self.watcher.start()

    def watcher(self):
        """
        If buffer_time is used, this method will flush the buffer
        after every buffer_time seconds has passed.
        """
        if self.debug:
            logging.getLogger().debug(f'TelegramHandler watcher starts: {datetime.now()}')
        while True:
            time.sleep(self.check_interval)
            if any(self.cache.values()):
                logging.getLogger().debug(f'TelegramHandler found unsent messages: {datetime.now()}')
                self.acquire()
                self.send()
                self.release()
            else:
                logging.getLogger().debug(f'TelegramHandler watcher finished: {datetime.now()}')
                break

        self.is_watching = False
