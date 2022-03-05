import socket
import sys
import logging
import atexit
import platform
from logging import handlers
from multiprocessing import Queue as mpQueue, current_process
from queue import Queue as thQueue
from threading import Thread, main_thread

import pickle
import socketserver
import struct
import select

from .capture import PrintCapture

__author__ = "Duc Tin"
root_logger = logging.getLogger()


class LogConfig:
    def __init__(self):
        self.qclass = None
        self.root_handlers = []
        self.q_listeners = []

        # tcp port for socket handler
        self.host = 'localhost'
        self.port = handlers.DEFAULT_TCP_LOGGING_PORT
        self.tcp_server = None

        # other settings
        self.full_context = False
        self.__capture_print = False
        self.strict = False
        self.guess_level = False
        self.suppress_level_below = logging.WARNING
        self.limit_line_length = 1000
        self.analyze_raise_statement = False

        self.original_stdout = sys.stdout

        # suppress logger list for usage in filter
        self.suppress_list = set()

        # initialized counter
        self.__initialized = 0

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
            if level.upper() not in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
                raise ValueError(f'"level" string is incorrect: {level}')
            level = getattr(logging, level.upper())
        self.suppress_level_below = level
        self.suppress_loggers(odict.get("suppress"))

        # backup root handler:
        self.root_handlers = root_logger.handlers

        # set logging mode accordingly
        self._set_mode(odict['use_multiprocessing'])

        self.__initialized += 1

    def _set_mode(self, use_multiprocessing):
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
                self._replace_with_socket_handler()

    def _replace_with_queue_handler(self):
        """ setup a central queue handler and start a listener thread """
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

            ql = handlers.QueueListener(queue, *all_handlers, respect_handler_level=True)
            self.q_listeners.append(ql)

            # start listening
            atexit.register(ql.stop)
            ql.start()

        root_logger.debug('Logging queue listener started!')

    def _replace_with_socket_handler(self):
        """ setup a central socket handler and start a listener server """
        logger = logging.getLogger()

        # backup current handlers
        all_handlers = logger.handlers

        # clear all handlers
        logger.handlers = []

        # add socket handler
        socket_handler = logging.handlers.SocketHandler(self.host, self.port)
        atexit.register(socket_handler.close)
        logger.addHandler(socket_handler)

        # initiate server
        if current_process().name == 'MainProcess':
            self.tcp_server = LogRecordSocketReceiver(self.host, self.port, all_handlers)
            serving = Thread(target=self.tcp_server.serve_until_stopped)
            serving.start()
            root_logger.debug('Logging server started!')

    def replace_handler_stream(self, index: int, stream):
        """Replace a stream of the root logger's handler
            This is mainly for GUI app to redirect the log to a widget
        """
        if current_process().name != 'MainProcess':
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


class LogRecordStreamHandler(socketserver.StreamRequestHandler):
    """Handler for a streaming logging request.

    This basically logs the record using whatever logging policy is
    configured locally.
    """
    # log record handlers
    handlers = []

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
        self.connection.settimeout(5)
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
    daemon_threads = False  # Set this to True to immediate exit when main-thread exits.

    # There is a chance that it terminates some log records that are
    # being processed

    def __init__(self, host, port, log_record_handlers):
        LogRecordStreamHandler.handlers = log_record_handlers
        super().__init__((host, port), LogRecordStreamHandler)
        self.abort = False
        self.timeout = 1

    def serve_until_stopped(self):
        while main_thread().is_alive():
            rd, wr, ex = select.select([self.socket.fileno()],
                                       [], [],
                                       self.timeout)
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

    def __init__(self, fmt: str = '', datefmt: str = '', style: str = ''):
        super(DefaultFormatter, self).__init__(fmt=fmt, datefmt=datefmt)

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
