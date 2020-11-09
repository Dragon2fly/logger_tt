from tests.subsub_module import error_func
from logger_tt import setup_logging, logger, getLogger

__author__ = "Duc Tin"

normal_logger = getLogger(__name__)


def run():
    logger.info('Logging by a default logger')
    normal_logger.info('Logging by the normal logger')


if __name__ == '__main__':
    setup_logging()
    run()
    error_func()
