from logger_tt import setup_logging
from logging import getLogger

__author__ = "Duc Tin"
setup_logging()
logger = getLogger(__name__)


def foo(*args, **kwargs):
    return 1


def lel(x, e=4):
    a = 1
    b = 2
    for i in range(1):
        return 1 + foo(a, b, c=x['z']['x']['y']['z']['y'], d=e)


def lel2(x):
    return 25 + lel(x) + lel(x)


def lel3(x):
    return lel2(x) / 23


if __name__ == '__main__':
    xx = {'z': {'x': {'y': None}}}
    lel3(xx)
