import time
from logger_tt import setup_logging, logger

config = setup_logging(use_multiprocessing=True, port=7891)


if __name__ == '__main__':
    server_info = config.tcp_server.socket.getsockname()
    logger.info("Log server serving at {}:{}".format(*server_info))
    t0 = time.time()
    while True:
        dt = time.time() - t0
        if dt > 10:
            break
        time.sleep(1)
