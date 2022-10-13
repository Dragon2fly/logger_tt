import time
from logging import getLogger
from logger_tt import setup_logging

__author__ = "ZeroRin"

setup_logging(analyze_raise_statement=True)
logger = getLogger(__name__)

def foo():
    try:
        a,b=1,0
        a/b
    except:
        try:
            c,d=1,0
            c/d
        except:
            e,f=1,0
            e/f

if __name__ == '__main__':
    logger.info('========A Caught Exception===========')
    try:
        foo()
    except:
        logger.exception('Caught exception:')
    logger.info('=======An Uncaught Exception=========')
    foo()
