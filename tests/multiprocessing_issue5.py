import os
import time
import sys
from random import randint
from multiprocessing import Process
from logger_tt import setup_logging, logger
from datetime import datetime

__author__ = "Duc Tin"
checkpoint_time = datetime.now().strftime("%Y%m%d-%H%M%S")
setup_logging(use_multiprocessing=True, log_path=os.path.join('logs', checkpoint_time, 'info.log'))


def worker(arg):
    logger.info(f'child process {arg}: started')
    time.sleep(randint(1, 3)/10)
    logger.info(f'child process {arg}: stopped')


if __name__ == '__main__':
    if len(sys.argv) > 1:
        proc_no = int(sys.argv[1])
    else:
        proc_no = 7

    all_processes = []
    logger.info('Parent process is ready to spawn child')
    logger.info('Test for issue 5')
    time.sleep(2)
    for i in range(proc_no):
        p = Process(target=worker, args=(i,))
        all_processes.append(p)
        p.daemon = True
        p.start()

    for p in all_processes:
        p.join()

    print('__finished__')
