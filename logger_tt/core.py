import os
import socket
import sys
import logging
import atexit
import platform
import time
import pickle
import socketserver
import struct
import select
from logging import handlers
from multiprocessing import Queue as mpQueue, current_process
from queue import Queue as thQueue
from threading import Thread, main_thread
from contextlib import contextmanager

from .capture import PrintCapture

__author__ = "Duc Tin"
root_logger = logging.getLogger()


def in_main_process() -> bool:
    # run from python interpreter
    condition1 = current_process().name == 'MainProcess'

    # run after frozen by pyinstaller or nuitka
    # mimic multiprocessing.spawn.is_forking
    # detect sys.argv[1] as added by multiprocessing.freeze_support()
    condition2 = not (len(sys.argv) >= 2 and sys.argv[1] == '--multiprocessing-fork')
    # print('is_main_process:', condition1 and condition2, current_process().name, current_process().pid, sys.argv)
    return condition1 and condition2


@contextmanager
def temporary_logger(logger, temp_handlers: list):
    org_handlers = root_logger.handlers
    logger.handlers = temp_handlers
    try:
        yield
    finally:
        logger.handlers = org_handlers


class LogConfig:
    def __init__(self):
        self.qclass = None
        self.root_handlers = []
        self.q_listeners = []

        # tcp port for socket handler
        self._host = 'localhost'
        self._port = handlers.DEFAULT_TCP_LOGGING_PORT
        self.tcp_server = None
        self.env_port_var = 'logger_tt_{}'

        # other settings
        self.full_context = False
        self.__capture_print = False
        self.strict = False
        self.guess_level = False
        self.suppress_level_below = logging.WARNING
        self.limit_line_length = 1000
        self.analyze_raise_statement = False
        self.server_timeout = 5
        self.original_stdout = sys.stdout

        # suppress logger list for usage in filter
        self.suppress_list = set()

        # initialized counter
        self.__initialized = 0

        # use context injector
        self.__middle_handlers = []

        # track added logging level to undo later
        self.__added_logging_level = {}

    @property
    def initialized(self):
        return self.__initialized

    def from_dict(self, odict: dict):
        # store basic settings
        for key in ['full_context', 'strict', 'guess_level', 'analyze_raise_statement']:
            setattr(self, key, odict[key])

        # set capture_print
        self.capture_print = odict['capture_print']

        # set limit_line_length
        self.limit_line_length = max(0, int(odict['limit_line_length']))

        # suppress other logger
        level = odict.get('suppress_level_below', 'WARNING')
        if type(level) is str:
            if level.upper() not in ['DEBUG', 'INFO', 'NOTICE', 'WARNING', 'ERROR', 'CRITICAL']:
                raise ValueError(f'"level" string is incorrect: {level}')
            level = getattr(logging, level.upper())
        self.suppress_level_below = level
        self.suppress_loggers(odict.get("suppress"))

        # backup root handler:
        self.root_handlers = root_logger.handlers

        # host, port, and waiting time before exit for multiprocessing logging
        self._host = odict.get('host') or 'localhost'
        self._port = odict.get('port', handlers.DEFAULT_TCP_LOGGING_PORT)
        self.server_timeout = max(1, int(odict.get('server_timeout', 0)))

        # set logging mode accordingly
        self._set_mode(odict['use_multiprocessing'], odict['client_only'])

        self.__initialized += 1

    def _set_mode(self, use_multiprocessing, client_only: bool):
        """Select logging method according to platform and multiprocessing"""
        os_name = platform.system()
        if use_multiprocessing not in [True, False, 'fork', 'spawn', 'forkserver']:
            raise ValueError(f'Expected a bool or a multiprocessing start_method name, but got: {use_multiprocessing}')

        if not use_multiprocessing:
            # for normal usage, thread queue is more than enough
            self.qclass = thQueue
            self._replace_with_queue_handler()
        else:
            # multiprocessing
            if os_name == 'Linux' and use_multiprocessing == 'fork':
                # because of copy on write while forking, multiprocessing queue can be used
                self.qclass = mpQueue
                self._replace_with_queue_handler()
            else:
                # __main__ is imported from crash for each child process
                # so we must use socket to communicate between processes
                self._replace_with_socket_handler(client_only)

    def _replace_with_queue_handler(self):
        """ set up a central queue handler and start a listener thread """
        all_loggers = [root_logger] + [logging.getLogger(name) for name in root_logger.manager.loggerDict]

        for logger in all_loggers:
            if not logger.handlers:
                continue

            # backup current handlers then clear it
            all_handlers = logger.handlers
            logger.handlers = []

            # add queue handler
            queue = self.qclass()
            q_handler = handlers.QueueHandler(queue)
            logger.addHandler(q_handler)
            self.__middle_handlers.append(q_handler)

            ql = handlers.QueueListener(queue, *all_handlers, respect_handler_level=True)
            self.q_listeners.append(ql)

            # start listening
            atexit.register(ql.stop)
            ql.start()

        root_logger.debug('Logging queue listener started!')

    def _replace_with_socket_handler(self, client_only: bool):
        """ setup a central socket handler and start a listener server """

        # initiate server
        if in_main_process():
            if not client_only:
                # backup current handlers
                all_handlers = root_logger.handlers

                self.tcp_server = LogRecordSocketReceiver(self._host, self._port, all_handlers, self.server_timeout)
                serving = Thread(target=self.tcp_server.serve_until_stopped)
                serving.start()

                host, port = self.tcp_server.socket.getsockname()
                self._port = port   # get the real port number in case user used "0"

                # set environ variable for child processes
                pid = current_process().pid
                os.environ[self.env_port_var.format(pid)] = str(port)

                # log info
                root_logger.debug('Logging server started!')
                root_logger.debug(f'Server port: {self._port}')

            # add socket handler
            socket_handler = logging.handlers.SocketHandler(self._host, self._port)
            root_logger.handlers = []
            root_logger.addHandler(socket_handler)
        else:
            # add socket handler
            parent_pid = os.getppid()
            port = os.environ.get(self.env_port_var.format(parent_pid), self._port)
            socket_handler = logging.handlers.SocketHandler(self._host, int(port))
            root_logger.handlers = []
            root_logger.addHandler(socket_handler)
            root_logger.debug(f'Child picked up port: {port}')

        atexit.register(socket_handler.close)
        self.__middle_handlers.append(socket_handler)

    def replace_handler_stream(self, index: int, stream):
        """Replace a stream of the root logger's handler
            This is mainly for GUI app to redirect the log to a widget
        """
        if not in_main_process():
            # nothing to do in child processes as all logs are redirected to main
            return

        if len(self.root_handlers) < index:
            raise ValueError(f'Trying to replace stream of the handler at index {index} but index is out of range')

        handler = self.root_handlers[index]
        assert isinstance(handler, logging.StreamHandler), f"Not a stream handler: {handler}"
        assert hasattr(stream, 'write') and hasattr(stream, 'flush'), f"Doesn't look like a stream: {stream}"

        handler.stream = stream

    def suppress_loggers(self, loggers):
        if not loggers:
            return

        for name in loggers:
            logger = logging.getLogger(name)
            logger.level = self.suppress_level_below

        self.suppress_list.update(loggers)

    @property
    def capture_print(self):
        return self.__capture_print

    @capture_print.setter
    def capture_print(self, val):
        if val:
            sys.stdout = PrintCapture(sys.stdout, strict=self.strict, guess_level=self.guess_level)
        else:
            sys.stdout = self.original_stdout

    def set_context_injector(self, injector):
        for handler in self.__middle_handlers:
            handler.addFilter(injector)

    def remove_context_injector(self, injector):
        for handler in self.__middle_handlers:
            handler.removeFilter(injector)

    def add_logging_level(self, level_name, level_num, method_name=None):
        # inspired by @Mad Physicist
        # https://stackoverflow.com/a/35804945/3655984
        if not method_name:
            method_name = level_name.lower()

        if hasattr(logging, level_name):
            raise ValueError(f'Re-define level {level_name} in logging module')
        if hasattr(logging, method_name):
            raise ValueError(f'Re-define method {method_name} in logging module')
        if hasattr(logging.getLoggerClass(), method_name):
            raise ValueError(f'Re-define {method_name} in Logger class')

        def logForLevel(self, message, *args, **kwargs):
            if self.isEnabledFor(level_num):
                self._log(level_num, message, args, **kwargs)

        def logToRoot(message, *args, **kwargs):
            logging.log(level_num, message, *args, **kwargs)

        logging.addLevelName(level_num, level_name)
        setattr(logging, level_name, level_num)
        setattr(logging.getLoggerClass(), method_name, logForLevel)
        setattr(logging, method_name, logToRoot)

        self.__added_logging_level[level_name] = (method_name, level_num)

    def remove_logging_level(self, level_name):
        if level_name in self.__added_logging_level:
            method_name, level_num = self.__added_logging_level[level_name]
            delattr(logging, level_name)
            delattr(logging.getLoggerClass(), method_name)
            delattr(logging, method_name)

            del logging._levelToName[level_num]
            del logging._nameToLevel[level_name]
            del self.__added_logging_level[level_name]

    def __enter__(self):
        """This is to simplify pytest test case"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """This is to simplify pytest test case"""
        # self.queue.join()
        while self.q_listeners:
            ql = self.q_listeners.pop()
            ql.stop()
            atexit.unregister(ql.stop)

            # py3.10 re-opens the log file after logging.shutdown() to workaround `open` NameError
            # https://github.com/python/cpython/commit/45df61fd2d58e8db33179f3b5d00e53fe6a7e592
            # We have to close it back
            for handler in ql.handlers:
                if isinstance(handler, logging.FileHandler):
                    handler.close()

        for custom_level in list(self.__added_logging_level):
            self.remove_logging_level(custom_level)

        self.__initialized = False


class LogRecordStreamHandler(socketserver.StreamRequestHandler):
    """Handler for a streaming logging request.

    This basically logs the record using whatever logging policy is
    configured locally.
    """
    # log record handlers
    handlers = []
    timeout = 5     # socket timeout when reading

    def receive_meta(self):
        """Get the byte length of incoming log record"""
        chunk = bytearray()

        while len(chunk) < 4:
            try:
                b = self.connection.recv(1)
                if not b:
                    # client disconnected
                    return ''
                else:
                    chunk.extend(b)
            except socket.timeout:
                if main_thread().is_alive():
                    continue
                else:
                    # Main thread exited but
                    # the client of from main thread hasn't disconnected yet.
                    # We break the loop to avoid dead-lock
                    return b''
            except ConnectionResetError as e:
                # connection was forcibly closed by client
                return b''

        return chunk

    def handle(self):
        """
        Handle multiple requests - each expected to be a 4-byte length,
        followed by the LogRecord in pickle format. Logs the record
        according to whatever policy is configured locally.
        """
        while True:
            chunk = self.receive_meta()
            if not chunk:
                break

            record_len = struct.unpack('>L', chunk)[0]
            chunk = self.connection.recv(record_len)
            while len(chunk) < record_len:
                chunk = chunk + self.connection.recv(record_len - len(chunk))

            # unpickle data
            obj = pickle.loads(chunk)
            record = logging.makeLogRecord(obj)

            # handle
            self.handle_log_record(record)

    def handle_log_record(self, record):
        """Handle a record.
            This just loops through the handlers offering them the record
            to handle.
        """
        for handler in self.handlers:
            process = record.levelno >= handler.level
            if process:
                handler.handle(record)


class LogRecordSocketReceiver(socketserver.ThreadingTCPServer):
    """
    Simple TCP socket-based logging receiver suitable for testing.
    """

    allow_reuse_address = True
    daemon_threads = True  # Set this to True to immediate exit when main-thread exits.

    # There is a chance that it terminates some log records that are
    # being processed

    def __init__(self, host, port, log_record_handlers, last_log_timeout):
        self.log_handlers = log_record_handlers

        # update handler class
        LogRecordStreamHandler.handlers = log_record_handlers
        LogRecordStreamHandler.timeout = last_log_timeout
        super().__init__((host, port), LogRecordStreamHandler)

        # if there is a socket connection, wait maximum this seconds
        self.last_log_timeout = last_log_timeout

        # timeout for select.select()
        self.select_timeout = 1

    def serve_until_stopped(self):

        main_exited_at = 0
        while True:
            if not main_exited_at and not main_thread().is_alive():
                # record the time that the dead of the main thread is detected
                main_exited_at = time.time()
                with temporary_logger(root_logger, self.log_handlers):
                    root_logger.debug(f'Detected main thread death at timestamp: {main_exited_at}')

            # calculate the uptime
            dt = time.time() - main_exited_at

            # exit if main exited and uptime is too long
            if main_exited_at and dt > self.last_log_timeout:
                self_exit_at = time.time()
                with temporary_logger(root_logger, self.log_handlers):
                    root_logger.debug(f'Logger server exited at timestamp: {self_exit_at}')
                break

            # else serve the request if any
            rd, wr, ex = select.select([self.socket.fileno()],
                                       [], [],
                                       self.select_timeout)
            if rd:
                self.handle_request()


class DefaultFormatter(logging.Formatter):
    """Based on the format string of any handler in root, we make new formatters for
        the default logger - logger_tt. This is a way to inject information but
        using the same handlers as regular logger.
    """
    default_formats = dict(normal=["%(name)s", "%(filename)s"],
                           thread=["%(message)s", "%(threadName)s %(message)s"],
                           multiprocess=["%(message)s", "%(processName)s %(message)s"],
                           both=["%(message)s", "%(processName)s %(threadName)s %(message)s"])

    def __init__(self, fmt: str = '', datefmt: str = '', style: str = '%'):
        super(DefaultFormatter, self).__init__(fmt=fmt, datefmt=datefmt, style=style)

        self._logger_tt_formatters = {}
        for case, fmt in self._standardize(fmt).items():
            self._logger_tt_formatters[case] = logging.Formatter(fmt=fmt, datefmt=datefmt, style=style)

    def _standardize(self, fmt):
        formatters = {'normal': fmt.replace(self.default_formats['normal'][0], self.default_formats['normal'][1])}

        # concurrent format
        concurrent_fmt = formatters['normal'].replace('%(threadName)s', '').replace('%(processName)s', '')
        for _type, replacement in self.default_formats.items():
            if _type == 'normal':
                continue

            old, new = replacement
            formatters[_type] = concurrent_fmt.replace(old, new)

        return formatters

    def format(self, record):
        if record.name == 'logger_tt':
            if record.processName == 'MainProcess' and record.threadName == 'MainThread':
                return self._logger_tt_formatters['normal'].format(record)
            elif record.processName == 'MainProcess' and record.threadName != 'MainThread':
                return self._logger_tt_formatters['thread'].format(record)
            elif record.processName != 'MainProcess' and record.threadName == 'MainThread':
                return self._logger_tt_formatters['multiprocess'].format(record)
            else:
                return self._logger_tt_formatters['both'].format(record)

        return super(DefaultFormatter, self).format(record)
