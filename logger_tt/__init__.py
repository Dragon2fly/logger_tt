import sys
import logging
import json
from pathlib import Path
from logging.config import dictConfig
from logging import getLogger
from .inspector import analyze_frame, logging_disabled
from .core import LogConfig, DefaultFormatter
from multiprocessing import current_process

__author__ = "Duc Tin"
__all__ = ['setup_logging', 'logging_disabled', 'getLogger', 'logger']

"""Config log from file and make it also logs uncaught exception"""

internal_config = LogConfig()
logger = getLogger('logger_tt')  # pre-made default logger for all modules
logger.setLevel(logging.DEBUG)


def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    full_context = internal_config.full_context

    # Root logger will log all other uncaught exceptions
    txt = analyze_frame(exc_traceback, full_context)
    logging.error(f"Uncaught exception:\n"
                  f"Traceback (most recent call last):\n"
                  f"{txt}",
                  exc_info=(exc_type, exc_value, None))

    # As interpreter is going to shutdown after this function,
    # objects are getting deleted.
    # Disable further logging to prevent NameError exception
    logging.disable(logging.CRITICAL)


def ensure_path(config: dict, override_log_path: str = ""):
    """ensure log path exists"""
    for handler in config['handlers'].values():
        filename = handler.get('filename')
        if not filename:
            continue
        filename = override_log_path or filename
        handler['filename'] = filename
        log_path = Path(filename).parent
        log_path.mkdir(parents=True, exist_ok=True)


def load_from_file(f: Path) -> dict:
    if f.suffix in ['.yaml', '.yml']:
        import yaml  # will raise error if pyyaml is not installed
        dict_cfg = yaml.safe_load(f.read_text())
    else:
        with f.open() as fp:
            dict_cfg = json.load(fp)

    # add default formatters to use logger_tt logger right on spot
    try:
        dlf = dict_cfg['logger_tt'].pop('default_logger_formats', {})
    except KeyError:
        dlf = {}
    DefaultFormatter.default_formats.update(dlf)
    for formatter in dict_cfg['formatters'].values():
        if not formatter.get('class'):
            formatter['class'] = 'logger_tt.core.DefaultFormatter'

    return dict_cfg


def merge_config(from_file: dict, from_func: dict) -> dict:
    """Override logger_tt config of from_file by
        the argument passed to the setup_logging function
    """
    defaults = dict(capture_print=False, strict=False, guess_level=False,
                    full_context=0, suppress=None,
                    suppress_level_below=logging.WARNING, use_multiprocessing=False)
    merged = {}
    for key, val in defaults.items():
        merged[key] = from_func.get(key, from_file.get(key, val))

    # check for unknown key
    uff1 = set(from_file) - set(defaults)
    uff2 = set(from_func) - set(defaults)

    if uff1:
        raise TypeError(f'setup_logging() got an unexpected keyword argument(s): {uff1}')
    if uff2:
        raise ValueError(f'logger_tt unknown fields: {uff2}')

    return merged


def setup_logging(config_path="", log_path="", **logger_tt_config) -> LogConfig:
    """Setup logging configuration
    :param config_path: Path to log config file. Use default config if this is not provided
    :param log_path: Path to store log file. Override 'filename' field of 'handlers' in
        default config.
    :param logger_tt_config: keyword only arguments to config the logger. Fields in this dictionary
        will override the same field in the config file.
        :key capture_print: bool, log message that is printed out with print() function
        :key strict       : bool, only used when capture_print is True.
                            If strict is True, then log everything that use sys.stdout.write().
        :key guess_level  : bool, auto guess logging level of captured message
        :key full_context : int, whether to log full local scope on exception or not and up to what level
        :key suppress     : list[str], name of loggers to be suppressed.
        :key suppress_level_below: int, for logger in the suppress list,
                                    any message below this level is not processed, not printed out nor logged to file
        :key use_multiprocessing : bool or str, set this to True if your code use multiprocessing.
                                    This flag switches the queue used for logging from
                                    queue.Queue to multiprocessing.Queue . This option can only be used here.
    """
    if config_path:
        cfgpath = Path(config_path)
        assert cfgpath.is_file(), 'Input config path is not a file!'
        assert cfgpath.suffix in ['.yaml', '.json', '.yml'], 'Config file type must be either yaml, yml or json!'
        assert cfgpath.exists(), f'Config file path not exists! {cfgpath.absolute()}'
    else:
        cfgpath = Path(__file__).parent / 'log_config.yaml'

    # load config from file
    config = load_from_file(cfgpath)
    ensure_path(config, log_path)
    logger_tt_cfg = config.pop('logger_tt', {})

    # initialize
    logging.config.dictConfig(config)

    if current_process().name == 'MainProcess':
        logging.debug('New log started'.center(50, '_'))
        logging.debug(f'Log config file: {cfgpath}')

    # set internal config
    iconfig = merge_config(logger_tt_cfg, logger_tt_config)
    internal_config.from_dict(iconfig)

    # capture other messages
    sys.excepthook = handle_exception
    return internal_config


class ExceptionLogger(logging.Logger):
    """Modify the `exception` func so that it print out context too
        This allow user do a try-except in outer code but still has the full log
        of nested code's error
        Example:
            try:
                a, b = 1, 0
            except Exception as e:
                logger.exception(e)
            # then move on
    """

    def exception(self, msg, *args, exc_info=True, **kwargs):
        if exc_info:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            full_context = internal_config.full_context
            txt = analyze_frame(exc_traceback, full_context)
            logging.error(f'{msg}\n'
                          f"Traceback (most recent call last):\n"
                          f"{txt}",
                          exc_info=(exc_type, exc_value, None))
        else:
            logging.error(msg, *args, exc_info=exc_info, **kwargs)


logging.setLoggerClass(ExceptionLogger)
