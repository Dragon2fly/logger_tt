import logging

from logging import getLogger
from .inspector import analyze_frame, logging_disabled
from .core import LogConfig, DefaultFormatter


__author__ = "Duc Tin"
__all__ = ['setup_logging', 'logging_disabled', 'getLogger', 'logger']


logger: logging.Logger


def setup_logging(config_path: str = "", log_path: str = "",
                  capture_print: bool = False,
                  strict: bool = False,
                  guess_level: bool = False,
                  full_context: int = 0,
                  suppress: list = None,
                  suppress_level_below: int = logging.WARNING,
                  use_multiprocessing: bool = False,
                  limit_line_length: int = 1000,
                  analyze_raise_statement: bool = False) -> LogConfig: ...
