from threading import Thread
from logger_tt import setup_logging, getLogger

setup_logging()
logger = getLogger(__name__)


def faulty_func(a=1, b=0):
    c = a/b
    return c


if __name__ == '__main__':
    # create an error in another thread and try to log it
    t = Thread(target=faulty_func)
    t.start()
    t.join()

    # can we continue the logging ?
    logger.debug('The thread has finished')
