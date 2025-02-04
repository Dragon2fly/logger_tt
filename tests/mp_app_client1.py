import time
from logger_tt import setup_logging, getLogger

config = setup_logging(log_path='logs/log_app1.txt',
                       use_multiprocessing=True, port=7891, client_only=True)
logger = getLogger('App1')


if __name__ == '__main__':
    for i in range(10):
        logger.info(f'Doing task {i}')
        time.sleep(1)
