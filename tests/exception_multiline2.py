from logging import getLogger
from logger_tt import setup_logging

__author__ = "Duc Tin"

setup_logging(capture_print=True)
logger = getLogger(__name__)


class Dummy:
    def __str__(self):
          return f"Ahahaha\n ehehe \n lalala"


class Tummy:
    def __init__(self):
        self.dummy = Dummy()


a = Tummy()


def aloha():
    b = Dummy()
    c = b / a.dummy

aloha()
