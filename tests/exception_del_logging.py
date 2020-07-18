import time
from logging import getLogger
from logger_tt import setup_logging

__author__ = "Duc Tin"

setup_logging(full_context=True)
logger = getLogger(__name__)


class MyClass:
    def __init__(self):
        self.a = "aloha"

    def __del__(self):
        time.sleep(1)
        logger.info(f"delete objects")


if __name__ == '__main__':
    c = MyClass()
    d = 5 / 0
