import time
import sys
from random import randint

from multiprocessing import Process
from logger_tt import setup_logging
from logging import getLogger


__author__ = "Duc Tin"
logger = getLogger(__name__)
setup_logging(use_multiprocessing=True)


def worker(arg):
    logger.info(f'child process {arg}: started')
    time.sleep(randint(1,5)/10)
    logger.info(f'child process {arg}: stopped')


if __name__ == '__main__':
    if len(sys.argv) > 1:
        proc_no = int(sys.argv[1])
    else:
        proc_no = 7

    all_processes = []
    logger.info('Parent process is ready to spawn child')
    for i in range(proc_no):
        p = Process(target=worker, args=(i,))
        all_processes.append(p)
        p.daemon = True
        p.start()

    for p in all_processes:
        p.join()

    print('__finished__')
