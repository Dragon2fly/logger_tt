import re
import pytest
from pathlib import Path
from tests.utils import config_modified
from logger_tt import getLogger, setup_logging, logger as my_logger


__author__ = "Duc Tin"
log = Path.cwd() / 'logs/log.txt'
normal_logger = getLogger(__name__)


@pytest.mark.parametrize("this_logger", [my_logger, normal_logger])
def test_style_brace(capsys, this_logger):
    with config_modified(
            'style_brace_config.yaml',
            [('formatters/simple/style', '{'),
             ('formatters/simple/format', '[{asctime}] {name}:{lineno} {levelname} {message}'),
             ('formatters/brief/style', '{'),
             ('formatters/brief/format', '[{asctime}] {levelname} {message}')
             ]):

        with setup_logging(config_path='style_brace_config.yaml'):
            this_logger.critical("hello1 {}", "world")
            this_logger.critical("hello2 {name}", name="world")
            this_logger.critical('hello3 {} {name}', 'beautiful', name='world')

        # check stdout
        captured = capsys.readouterr()
        stdout_data = captured.out
        assert 'CRITICAL hello1 world' in stdout_data
        assert 'CRITICAL hello2 world' in stdout_data
        assert 'CRITICAL hello3 beautiful world' in stdout_data

        # check log.txt
        log_data = log.read_text()
        assert re.search(r'test_issue22_style:\d+ CRITICAL hello1 world', log_data)
        assert re.search(r'test_issue22_style:\d+ CRITICAL hello2 world', log_data)
        assert re.search(r'test_issue22_style:\d+ CRITICAL hello3 beautiful world', log_data)


@pytest.mark.parametrize("this_logger", [my_logger, normal_logger])
def test_style_dollar(capsys, this_logger):
    with config_modified(
            'style_brace_config.yaml',
            [('formatters/simple/style', '$'),
             ('formatters/simple/format', '[${asctime}] $name:$lineno ${levelname} ${message}'),
             ('formatters/brief/style', '$'),
             ('formatters/brief/format', '[${asctime}] $levelname $message')
             ]):

        with setup_logging(config_path='style_brace_config.yaml'):
            this_logger.critical("hello2 ${name}", name="world")
            this_logger.critical('hello3 ${what} $name', what='beautiful', name='world')

        # check stdout
        captured = capsys.readouterr()
        stdout_data = captured.out
        assert 'CRITICAL hello2 world' in stdout_data
        assert 'CRITICAL hello3 beautiful world' in stdout_data

        # check log.txt
        log_data = log.read_text()
        assert re.search(r'test_issue22_style:\d+ CRITICAL hello2 world', log_data)
        assert re.search(r'test_issue22_style:\d+ CRITICAL hello3 beautiful world', log_data)
