import time
import sys
from random import randint

from multiprocessing import Process
from logger_tt import setup_logging
from logging import getLogger


__author__ = "Duc Tin"
logger = getLogger(__name__)
config = setup_logging(config_path="multiprocessing_change_port.yaml")


def worker(arg):
    logger.info(f'child process {arg}: started')
    time.sleep(randint(1, 5))
    logger.info(f'child process {arg}: stopped')


if __name__ == '__main__':
    if len(sys.argv) > 1:
        proc_no = int(sys.argv[1])
    else:
        proc_no = 7

    all_processes = []
    logger.info('Parent process is ready to spawn child')
    logger.info(f'current logging tcp_server is: {config.tcp_server.server_address}')
    for i in range(proc_no):
        p = Process(target=worker, args=(i,))
        all_processes.append(p)
        p.daemon = True
        p.start()

    for p in all_processes:
        p.join()

    print('__finished__')
