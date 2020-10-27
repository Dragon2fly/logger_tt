import re

import pytest
from subprocess import run, PIPE
from logging import getLogger
from pathlib import Path

from logger_tt import setup_logging

__author__ = "Duc Tin"

logger = getLogger(__name__)
log = Path.cwd() / 'logs/log.txt'


def test_multiprocessing_normal():
    cmd = ["python", "multiprocessing_normal.py", "3"]
    run(cmd)

    data = log.read_text(encoding='utf8')
    assert 'Parent process is ready to spawn child' in data
    assert 'child process 0' in data
    assert 'child process 1' in data
    assert 'child process 2' in data


@pytest.mark.parametrize('value', [-1, 2, 'forker', 'spawm'])
def test_multiprocessing_error(value):
    with pytest.raises(ValueError) as e:
        setup_logging(use_multiprocessing=value)

    assert f'Expected a bool or a multiprocessing start_method name, but got: {value}' in str(e)


def test_multiprocessing_pool():
    cmd = ["python", "multiprocessing_pool.py", "10"]
    run(cmd)

    data = log.read_text(encoding='utf8')
    assert 'Parent process pool is ready to spawn child' in data
    assert 'child process 0' in data
    assert 'child process 1' in data
    assert 'child process 2' in data
    assert 'child process 3' in data
    assert 'child process 4' in data
    assert 'child process 5' in data
    assert 'child process 6' in data
    assert 'child process 7' in data
    assert 'child process 8' in data
    assert 'child process 9' in data


def test_multiprocessing_threading():
    """Test a default logger"""
    cmd = ["python", "multiprocessing_threading.py", "10"]
    result = run(cmd, stdout=PIPE, universal_newlines=True)
    assert 'Parent process is ready to spawn child' in result.stdout
    expect = re.findall(r'Process-\d+ Thread-\d+.*? thread running from process', result.stdout)
    assert len(expect) == 10

    data = log.read_text(encoding='utf8')
    assert 'Parent process is ready to spawn child' in data
    expect = re.findall(r'Process-\d+ Thread-\d+.*? thread running from process', data)
    assert len(expect) == 10
