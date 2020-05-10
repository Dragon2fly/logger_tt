import re
import sys
from logging import getLogger
from pathlib import Path
from io import StringIO

from logger_tt import setup_logging

__author__ = "Duc Tin"

logger = getLogger(__name__)
log = Path.cwd() / 'logs/log.txt'


def test_basic_function():
    stdout = StringIO()
    sys.stdout = stdout
    setup_logging()

    logger.debug('my debug')
    logger.info('my info')
    logger.warning('my warning')
    logger.error('my error')
    logger.critical('the market crashed')

    # check stdout
    stdout_data = sys.stdout.getvalue()
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


def test_capture_print_not_strict():
    stdout = StringIO()
    sys.stdout = stdout
    setup_logging(capture_print=True)

    print('This is my print')
    sys.stdout.write('This should be printed normally')

    stdout_data = stdout.getvalue()
    log_data = log.read_text()

    assert re.search('.*INFO.*This is my print', stdout_data)
    assert re.search('.*INFO.*This is my print', log_data)

    assert 'This should be printed normally' in stdout_data
    assert not re.search('.*INFO.*This should be printed normally', stdout_data)
    assert 'This should be printed normally' not in log_data


def test_capture_print_strict():
    stdout = StringIO()
    sys.stdout = stdout
    setup_logging(capture_print=True, strict=True)

    print('This is my print')
    sys.stdout.write('This should be printed normally')

    stdout_data = stdout.getvalue()
    log_data = log.read_text()

    assert re.search('.*INFO.*This is my print', stdout_data)
    assert re.search('.*INFO.*This is my print', log_data)

    assert re.search('.*INFO.*This should be printed normally', stdout_data)
    assert re.search('.*INFO.*This should be printed normally', log_data)
