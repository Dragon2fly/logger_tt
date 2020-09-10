import logging
import re
import sys
from logging import getLogger
from pathlib import Path

import pytest
from logger_tt import setup_logging

__author__ = "Duc Tin"

logger = getLogger(__name__)
log = Path.cwd() / 'logs/log.txt'


def test_basic_function(capsys):
    with setup_logging():
        logger.debug('my debug')
        logger.info('my info')
        logger.warning('my warning')
        logger.error('my error')
        logger.critical('the market crashed')

    # check stdout
    captured = capsys.readouterr()
    stdout_data = captured.out
    assert 'my debug' not in stdout_data
    assert 'my info' in stdout_data
    assert 'my warning' in stdout_data
    assert 'my error' in stdout_data
    assert 'the market crashed' in stdout_data

    # check log.txt
    log_data = log.read_text()
    assert 'my debug' in log_data
    assert 'my info' in log_data
    assert 'my warning' in log_data
    assert 'my error' in log_data
    assert 'the market crashed' in log_data


def test_capture_print_not_strict(capsys):
    with setup_logging(capture_print=True):
        print('This is my print')
        sys.stdout.write('\n')
        sys.stdout.write('This should be printed normally')

    stdout_data = capsys.readouterr().out
    log_data = log.read_text()

    assert re.search('.*INFO.*This is my print', stdout_data)
    assert re.search('.*INFO.*This is my print', log_data)

    assert 'This should be printed normally' in stdout_data
    assert not re.search('.*INFO.*This should be printed normally', stdout_data)
    assert 'This should be printed normally' not in log_data


def test_capture_print_strict(capsys):
    with setup_logging(capture_print=True, strict=True):
        print('This is my print')
        sys.stdout.write('This should be printed normally too')

    stdout_data = capsys.readouterr().out
    log_data = log.read_text()

    assert re.search('.*INFO.*This is my print', stdout_data)
    assert re.search('.*INFO.*This is my print', log_data)

    assert re.search('.*INFO.*This should be printed normally too', stdout_data)
    assert re.search('.*INFO.*This should be printed normally too', log_data)


@pytest.mark.parametrize("msg", [('info', 'abc Info: It will rain this afternoon'),
                                 ('warning', 'def Warning: the price is down'),
                                 ('error', 'ghi Error: username incorrect'),
                                 ('critical', 'jkl Critical: system is overheating'),
                                 ('debug', 'mno DEBUG: ha ha ha')])
def test_guess_message_level(msg):
    with setup_logging(capture_print=True, guess_level=True):
        level, msg = msg
        print(msg)

    log_data = log.read_text().splitlines()[-1].lower()
    assert log_data.count(level) == 2


@pytest.mark.parametrize("level", [logging.WARNING, logging.ERROR])
def test_suppress_logger(capsys, level):
    with setup_logging(suppress_level_below=level):
        from tests.exchangelib_logger import fox_run

        fox_run()

    stdout_data = capsys.readouterr().out
    assert 'DEBUG' not in stdout_data
    assert 'INFO' not in stdout_data

    if level == logging.WARNING:
        assert 'WARNING' in stdout_data
    elif level == logging.ERROR:
        assert 'WARNING' not in stdout_data

    assert 'ERROR' in stdout_data
    assert 'CRITICAL' in stdout_data
