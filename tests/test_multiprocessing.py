from subprocess import run
from logging import getLogger
from pathlib import Path

from logger_tt import setup_logging

__author__ = "Duc Tin"

logger = getLogger(__name__)
log = Path.cwd() / 'logs/log.txt'


def test_multiprocessing_normal():
    with setup_logging(use_multiprocessing=True):
        cmd = ["python", "multiprocessing_normal.py", "3"]
        run(cmd)

    data = log.read_text(encoding='utf8')
    assert 'Parent process is ready to spawn child' in data
    assert 'child process 0' in data
    assert 'child process 1' in data
    assert 'child process 2' in data


def test_multiprocessing_pool():
    setup_logging(use_multiprocessing=True)
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
