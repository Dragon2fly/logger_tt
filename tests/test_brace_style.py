from logging import getLogger
from pathlib import Path

import pytest
from logger_tt import setup_logging

__author__ = "nonnull"

logger = getLogger(__name__)
log = Path.cwd() / 'logs/log.txt'

def test_basic_brace_style(capsys):
    with setup_logging(config_path="test_brace_style.yaml"):
        logger.debug('my %s', 'debug')
        logger.info('my %s', 'info')
        logger.warning('my %s', 'warning')
        logger.error('my %s', 'error')
        logger.critical('the market %s', 'crashed')

    # check stdout
    captured = capsys.readouterr()
    stdout_data = captured.out
    stderr_data = captured.err
    assert '--- Logging error ---' not in stderr_data, stderr_data
    assert 'my debug' not in stdout_data, stdout_data
    assert 'INFO: my info' in stdout_data, stdout_data
    assert 'WARNING: my warning' in stdout_data, stdout_data
    assert 'ERROR: my error' in stdout_data, stdout_data
    assert 'CRITICAL: the market crashed' in stdout_data, stdout_data

    # check log.txt
    log_data = log.read_text()
    assert 'DEBUG] my debug' in log_data
    assert 'INFO] my info' in log_data
    assert 'WARNING] my warning' in log_data
    assert 'ERROR] my error' in log_data
    assert 'CRITICAL] the market crashed' in log_data
