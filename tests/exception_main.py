from logger_tt import setup_logging
from logging import getLogger


__author__ = "Duc Tin"
setup_logging()
logger = getLogger(__name__)


class Dummy:
    def __init__(self):
        self.value = 3
        self.divisor = 0


if __name__ == '__main__':
    a = Dummy()
    res = a.value / a.divisor
    print(res)
