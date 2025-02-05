from logger_tt import setup_logging, logger


setup_logging(config_path='style_brace_config.yaml')


if __name__ == '__main__':
    logger.critical("hello1 {}", "world")
    logger.critical("hello2 {name}", name="world")
    logger.critical('hello3 {} {name}', 'beautiful', name='world')
