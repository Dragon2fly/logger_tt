from logging import getLogger
from logger_tt import setup_logging

__author__ = "Duc Tin"

setup_logging()
logger = getLogger(__name__)

try:
    a = 1
    b = 0
    c = a / b
except Exception as e:
    logger.exception('some error')
