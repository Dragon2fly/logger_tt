from logging import getLogger

__author__ = "Duc Tin"
logger = getLogger(__name__)


def error_func():
    # create an exception
    a = 3
    b = 0
    try:
        res = a / b
        return res
    except Exception as e:
        logger.exception(e)
