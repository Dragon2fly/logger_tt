import sys
import logging
import json
from pathlib import Path
from logging.config import dictConfig
from .capture import PrintCapture


__author__ = "Duc Tin"
__all__ = ['setup_logging']


"""Config log from file and make it also logs uncaught exception"""


def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    # Root logger with log all other uncaught exceptions
    logging.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))


def ensure_path(config: dict, override_log_path: str = ""):
    """ensure log path exists"""
    for handler in config['handlers'].values():
        filename = handler.get('filename')
        if not filename:
            continue
        filename = override_log_path or filename
        log_path = Path(filename).parent
        log_path.mkdir(parents=True, exist_ok=True)


def load_from_file(f: Path) -> dict:
    if f.suffix == '.yaml':
        import yaml     # will raise error if pyyaml is not installed
        return yaml.safe_load(f.read_text())
    else:
        with f.open() as fp:
            return json.load(fp)


def setup_logging(config_path="", log_path="", capture_print=False, strict=False, guess_level=False):
    """Setup logging configuration
        config_path: Path to log config file. Use default config if this is not provided
        log_path: Path to store log file. Override 'filename' field of 'handlers' in
            default config.
        capture_print: Log message that is printed out with print() function
        strict: only used when capture_print is True. If strict is True, then log
            everything that use sys.stdout.write().
    """
    if config_path:
        path = Path(config_path)
        assert path.is_file(), 'Input config path is not a file!'
        assert path.suffix in ['.yaml', '.json'], 'Config file type must be either yaml or json!'
        assert path.exists(), f'Config file path not exists! {path.absolute()}'
    else:
        path = Path(__file__).parent / 'log_conf.json'

    # load config from file
    config = load_from_file(path)
    ensure_path(config, log_path)
    logging.config.dictConfig(config)

    # capture other messages
    sys.excepthook = handle_exception
    if capture_print:
        sys.stdout = PrintCapture(sys.stdout, strict=strict, guess_level=guess_level)
    logging.debug('New log started'.center(50, '_'))
