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
    if sys.argv[-1] == 'caught':
        try:
            foo()
        except:
            logger.exception('Caught exception:')
    elif sys.argv[-1] ==  'uncaught':
        foo()
    else:
        raise ValueError('Usage [PROG] {caught,uncaught}')