from logger_tt import logger, getLogger

__author__ = "Duc Tin"

normal_logger = getLogger(__name__)


def run():
    logger.info('Logging by a default logger')
    normal_logger.info('Logging by the normal logger')
