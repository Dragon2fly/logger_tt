__author__ = "Duc Tin"

from logging import getLogger

logger = getLogger('exchangelib')


def fox_run():
    logger.debug('Exchangelib module started')
    logger.info('A quick brown fox jumps over a flower fence')
    logger.warning('A fence is too high')
    logger.error("A fox's rear legs stuck in the fence")
    logger.critical("A fox is bleeding")
