import sys
import logging
import atexit
from logging import handlers
from multiprocessing import Queue as mpQueue
from queue import Queue as thQueue

from .capture import PrintCapture


__author__ = "Duc Tin"
root = logging.getLogger()


class LogConfig:
    def __init__(self):
        self.queue = None
        self.q_listener = None
        self.converted_handlers = set()

        # other settings
        self.full_context = False
        self.__capture_print = False
        self.strict = False
        self.guess_level = False
        self.suppress_level_below = logging.WARNING

        self.original_stdout = sys.stdout

    def init_queue(self, use_multiprocessing):
        if use_multiprocessing:
            self.queue = mpQueue()
        else:
            self.queue = thQueue()

    def replace_with_queue_handler(self, logger:logging.Logger):
        """ call this method after setting up dictConfig """
        # backup current handlers
        all_handlers = logger.handlers

        # clear all handlers
        logger.handlers = []

        # add queue handler
        q_handler = handlers.QueueHandler(self.queue)
        logger.addHandler(q_handler)

        new_handler = set(all_handlers) - self.converted_handlers
        self.q_listener = handlers.QueueListener(self.queue,*new_handler, respect_handler_level=True)
        self.converted_handlers.update(new_handler)

        # todo: what if child logger has it own handlers ?

        # start listening
        atexit.register(self.q_listener.stop)
        self.q_listener.start()

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
        self.q_listener.stop()
        atexit.unregister(self.q_listener.stop)

