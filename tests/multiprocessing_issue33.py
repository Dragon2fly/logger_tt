"""Reproduce issue #33: frozen Windows app crashes in child processes.

The config file has a file handler pointing to a non-existent directory
WITHOUT delay=True.  The main process overrides the path via log_path,
but child processes re-read the config and hit the original bad path.

Before the fix, dictConfig() in the child process would try to
instantiate the TimedRotatingFileHandler at the non-existent path,
causing a crash.
"""
import sys
import time
from multiprocessing import Pool
from logger_tt import setup_logging
from logging import getLogger

setup_logging(
    config_path="multiprocessing_issue33_config.json",
    log_path="logs/log.txt",
    use_multiprocessing=True,
)
logger = getLogger(__name__)


def worker(arg):
    logger.info(f'child process {arg}: started')
    time.sleep(0.1)
    logger.info(f'child process {arg}: stopped')
    return arg


if __name__ == '__main__':
    if len(sys.argv) > 1:
        proc_no = int(sys.argv[1])
    else:
        proc_no = 3

    logger.info('Issue 33 test: parent ready')

    with Pool(2) as p:
        results = p.map(worker, range(proc_no))

    print('__finished__')
