import sys
from logging import getLogger

from logger_tt import setup_logging

__author__ = "ZeroRin"

setup_logging(analyze_raise_statement=True)
logger = getLogger(__name__)

def foo():
    try:
        a=1
        raise RuntimeError(a)
    except:
        try:
            b=2
            raise RuntimeError(b)
        except:
            c=3
            raise RuntimeError(c)

if __name__ == '__main__':
    match sys.argv[-1]:
        case 'caught':
            try:
                foo()
            except:
                logger.exception('Caught exception:')
        case 'uncaught':
            foo()
        case _:
            raise ValueError('Usage [PROG] {caught,uncaught}')