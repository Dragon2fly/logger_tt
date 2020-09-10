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
        self.queues = []
        self.q_listeners = []
        self.converted_handlers = set()

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

        self.original_stdout = sys.stdout

    def set_mode(self, use_multiprocessing):
        """Select logging method according to platform and multiprocessing"""
        os_name = platform.system()

        if os_name == 'Linux' or not use_multiprocessing:
            # for normal usage, thread queue is more than enough
            self.qclass = thQueue
            self.replace_with_queue_handler()
        else:
            # multiprocessing
            if os_name == 'Linux':
                # because of copy on write while forking, multiprocessing queue can be used
                self.qclass = mpQueue
                self.replace_with_queue_handler()
            else:
                # __main__ is imported from crash for each child process
                # so we must use socket to communicate between processes
                self.replace_with_socket_handler()

    def replace_with_queue_handler(self):
        """ call this method after setting up dictConfig """
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

            ql = handlers.QueueListener(queue,*all_handlers, respect_handler_level=True)
            self.q_listeners.append(ql)

            # start listening
            atexit.register(ql.stop)
            ql.start()

    def clean_up(self, sh):
        # print('close it'.center(40, '-'))
        sh.close()

    def replace_with_socket_handler(self):
        logger = logging.getLogger()

        # backup current handlers
        all_handlers = logger.handlers

        # clear all handlers
        logger.handlers = []

        # add socket handler
        socket_handler = logging.handlers.SocketHandler(self.host, self.port)
        atexit.register(self.clean_up, socket_handler)
        logger.addHandler(socket_handler)

        # initiate server
        if current_process().name == 'MainProcess':
            self.tcp_server = LogRecordSocketReceiver(self.host, self.port, all_handlers)
            serving = Thread(target=self.tcp_server.serve_until_stopped)
            serving.start()
            root_logger.debug('Start logging server ...')

    def suppress_logger(self, loggers):
        if not loggers:
            return

        for name in loggers:
            logger = logging.getLogger(name)
            logger.level = self.suppress_level_below

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
    daemon_threads = False         # Set this to True to immediate exit when main-thread exits.
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
