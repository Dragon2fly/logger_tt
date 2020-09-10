import time
import sys
from random import randint

from multiprocessing import Pool
from logger_tt import setup_logging
from logging import getLogger


__author__ = "Duc Tin"
logger = getLogger(__name__)
setup_logging(use_multiprocessing=True)


def worker(arg):
    logger.info(f'child process {arg}: started')
    time.sleep(randint(1,10)/10)
    logger.info(f'child process {arg}: stopped')


if __name__ == '__main__':
    if len(sys.argv) > 1:
        proc_no = int(sys.argv[1])
    else:
        proc_no = 7

    logger.info('Parent process pool is ready to spawn child')

    with Pool(4) as p:
        p.map(worker, range(proc_no))

    print('__finished__')
