import sys
import logging
import json
import threading
from pathlib import Path
from logging.config import dictConfig
from logging import getLogger
from .inspector import analyze_frame, logging_disabled, analyze_exception_recur
from .core import LogConfig, DefaultFormatter
from multiprocessing import current_process

__author__ = "Duc Tin"
__all__ = ['setup_logging', 'logging_disabled', 'getLogger', 'logger', 'add_logging_level']

"""Config log from file and make it also logs uncaught exception"""

internal_config = LogConfig()


def handle_exception(exc_type, exc_value, exc_traceback, thread_name=''):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    full_context = internal_config.full_context
    limit_length = internal_config.limit_line_length
    analyze_raise = internal_config.analyze_raise_statement

    # Root logger will log all other uncaught exceptions
    txt = analyze_exception_recur(exc_value, full_context, limit_length, analyze_raise)

    # Exception in a child thread?
    if thread_name:
        thread_name = ' in ' + thread_name

    logging.error(f"Uncaught exception{thread_name}:\n{txt}")

    if not thread_name:
        # As interpreter is going to shutdown after this function,
        # objects are getting deleted.
        # Disable further logging to prevent NameError exception
        logging.disable(logging.CRITICAL)
        # Don't do this if exception is on child thread


def thread_run_with_exception_logging(self):
    """Do everything the Thread.run() do and add exception handling"""
    try:
        if self._target:
            self._target(*self._args, **self._kwargs)
    except Exception:
        handle_exception(*sys.exc_info(), thread_name=self.name)
    finally:
        # Avoid a refcycle if the thread is running a function with
        # an argument that has a member that points to the thread.
        del self._target, self._args, self._kwargs


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
        try:
            import yaml  # will raise error if pyyaml is not installed
            safe_load = yaml.safe_load
        except ImportError:
            try:
                from ruamel.yaml import YAML
                yaml = YAML(typ='safe')
                safe_load = yaml.load
            except ImportError:
                raise ImportError('Required package not found: "pyyaml" or "ruamel.yaml"')

        dict_cfg = safe_load(f.read_text())

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
                    suppress_level_below=logging.WARNING, use_multiprocessing=False,
                    limit_line_length=1000, analyze_raise_statement=False,
                    host=None, port=None,
                    )
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


def setup_logging(config_path: str = "", log_path: str = "", **logger_tt_config) -> LogConfig:
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
        :key limit_line_length   : int, define how long should one log line be. 0: unlimited; n: n character
        :key analyze_raise_statement: bool, should the variables in `raise` exception line be shown or not.
        :key host: str, default to 'localhost'. Used in multiprocessing logging
        :key port: int, default to logging.handlers.DEFAULT_TCP_LOGGING_PORT. Used in multiprocessing logging
    """
    if internal_config.initialized:
        logger.warning('Re-initializing logger_tt. "setup_logging()" should only be called one.')

    # add NOTICE level for telegram handler
    add_logging_level('NOTICE', logging.INFO + 5)

    if config_path:
        cfgpath = Path(config_path)
        assert cfgpath.is_file(), 'Input config path is not a file!'
        assert cfgpath.suffix in ['.yaml', '.json', '.yml'], 'Config file type must be either yaml, yml or json!'
        assert cfgpath.exists(), f'Config file path not exists! {cfgpath.absolute()}'
    else:
        cfgpath = Path(__file__).parent / 'log_config.json'

    # load config from file
    config = load_from_file(cfgpath)
    logger_tt_cfg = config.pop('logger_tt', {})
    if current_process().name == 'MainProcess':
        ensure_path(config, log_path)   # create log path if not exist
    else:
        # child process of Spawn-method
        del config['loggers']           # remove all loggers as they will not be used
        del config['root']['handlers']  # remove all handlers of the root logger as a socket handler will be added later

    # initialize
    for name in logging.root.manager.loggerDict:
        existing_logger = logging.getLogger(name)
        existing_logger.__class__ = ExceptionLogger
    else:
        logging.config.dictConfig(config)

    if current_process().name == 'MainProcess':
        logging.debug('New log started'.center(50, '_'))
        logging.debug(f'Log config file: {cfgpath}')

    # set internal config
    iconfig = merge_config(logger_tt_cfg, logger_tt_config)
    internal_config.from_dict(iconfig)

    # capture other messages
    sys.excepthook = handle_exception
    threading.Thread.run = thread_run_with_exception_logging
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

    _logger_names = {}

    def exception(self, msg, *args, exc_info=True, **kwargs):
        if exc_info:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            full_context = internal_config.full_context
            limit_length = internal_config.limit_line_length
            analyze_raise = internal_config.analyze_raise_statement
            txt = analyze_exception_recur(exc_value, full_context, limit_length, analyze_raise)
            logging.error(f'{msg}\n{txt}')
        else:
            logging.error(msg, *args, exc_info=exc_info, **kwargs)

    def makeRecord(self, name, level, fn, lno, msg, args, exc_info, func=None, extra=None, sinfo=None):
        record = super().makeRecord(name, level, fn, lno, msg, args, exc_info, func, extra, sinfo)

        if name == 'logger_tt':
            # try to get the __name__ of the module that use the default logger: logger_tt
            pathname = fn.replace('\\', '/')
            qualified_name = self._logger_names.get(pathname)
            if not qualified_name:
                for qualified_name, module in sys.modules.items():
                    file = getattr(module, '__file__', None)
                    if file and file.replace('\\', '/') == pathname:
                        self._logger_names[pathname] = qualified_name
                        break

            if qualified_name == '__main__' and record.processName != 'MainProcess':
                qualified_name = '__mp_main__'

            record.filename = qualified_name or record.filename

        return record


def logger_tt_filter(record):
    if record.filename not in internal_config.suppress_list:
        return True
    if record.levelno > internal_config.suppress_level_below:
        return True


def add_logging_level(level_name, level_num, method_name=None):
    # inspired by @Mad Physicist
    # https://stackoverflow.com/a/35804945/3655984
    if not method_name:
        method_name = level_name.lower()

    if hasattr(logging, level_name):
        logger.warning(f'Re-define level {level_name} in logging module')
    if hasattr(logging, method_name):
        logger.warning(f'Re-define method {method_name} in logging module')
    if hasattr(logging.getLoggerClass(), method_name):
        logger.warning(f'Re-define {method_name} in Logger class')

    def logForLevel(self, message, *args, **kwargs):
        if self.isEnabledFor(level_num):
            self._log(level_num, message, args, **kwargs)

    def logToRoot(message, *args, **kwargs):
        logging.log(level_num, message, *args, **kwargs)

    logging.addLevelName(level_num, level_name)
    setattr(logging, level_name, level_num)
    setattr(logging.getLoggerClass(), method_name, logForLevel)
    setattr(logging, method_name, logToRoot)


logging.setLoggerClass(ExceptionLogger)
logger = getLogger('logger_tt')  # pre-made default logger for all modules
logger.setLevel(logging.DEBUG)
logger.addFilter(logger_tt_filter)
