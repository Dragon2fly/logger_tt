import time
import sys
from multiprocessing import Process

from logger_tt import setup_logging, logger


__author__ = "Duc Tin"
setup_logging(config_path="multiprocessing_issue21.yaml")


def worker(arg):
    logger.info(f'{arg} worker is doing stuff')
    time.sleep(3)
    logger.info(f'{arg} worker completed')
    logger.info(f'{arg} worker completed again x1')
    logger.info(f'{arg} worker completed again x2')

    time.sleep(5)
    print('haha')


if __name__ == '__main__':
    if len(sys.argv) > 1:
        proc_no = int(sys.argv[1])
    else:
        proc_no = 2

    all_processes = []
    logger.info('Parent process is ready to spawn child')
    logger.info('Test for issue 21')

    for i in range(proc_no):
        p = Process(target=worker, args=(i,))
        all_processes.append(p)
        p.daemon = True        # simulate an independent 2nd process
        p.start()

    # No join() to simulate the first app exit
    # for p in all_processes:
    #     p.join()
    logger.info('Parent process die')
    print('__finished__')
