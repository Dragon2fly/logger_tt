import sys
from logging import getLogger
from typing import *

from logger_tt import logger, setup_logging

__author__ = "ZeroRin"

def modify_log_files(log_path: Union[str,dict]=''):
    print(log_path)
    setup_logging(config_path='edit_log_path.json',log_path=log_path)

    urllib_logger = getLogger('urllib3')
    logger.info('A log from default logger')
    urllib_logger.error('A log from urllib logger')


if __name__=='__main__':
    try:
        log_path = eval(sys.argv[-1])
    except:
        raise ValueError('Usage [PROG] log_path_repr')
    modify_log_files(log_path)