import logging

from typing import Union
from logging import getLogger
from .inspector import logging_disabled
from .core import LogConfig


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
                  use_multiprocessing: Union[bool,int, str] = False,
                  limit_line_length: int = 1000,
                  analyze_raise_statement: bool = False,
                  host: str = None,
                  port: int = None,
                  server_timeout: float = 5,
                  client_only: bool = False) -> LogConfig: ...
