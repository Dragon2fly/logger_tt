import sys
from subprocess import run
from pathlib import Path


__author__ = "Duc Tin"

log = Path.cwd() / 'logs/log.txt'


def test_log_uncaught_thread_exception():
    cmd = [sys.executable, "exception_thread.py"]
    run(cmd)

    data = log.read_text(encoding='utf8')
    assert 'Uncaught exception' in data
    assert 'The thread has finished' in data
