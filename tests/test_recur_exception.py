import re
import sys
import time
from pathlib import Path
from subprocess import run, PIPE
import pytest
import re
from logger_tt.inspector import get_recur_attr, get_repr, is_full_statement, get_full_statement, MEM_PATTERN

__author__ = "ZeroRin"
log = Path.cwd() / 'logs/log.txt'


def test_recur_exception():
    cmd = [sys.executable, "exception_on_exception.py"]
    run(cmd)
    data = log.read_text()
    pattern = (
        r'Caught exception:\n'
        r'Traceback \(most recent call last\):'
        r'[\S\s]*'
        r'raise RuntimeError\(a\)'
        r'[\S\s]*'
        r'RuntimeError: 1\n\n'
        r'During handling of the above exception, another exception occurred:\n\n'
        r'Traceback \(most recent call last\):'
        r'[\S\s]*'
        r'raise RuntimeError\(b\)'
        r'[\S\s]*'
        r'RuntimeError: 2\n\n'
        r'During handling of the above exception, another exception occurred:\n\n'
        r'Traceback \(most recent call last\):'
        r'[\S\s]*'
        r'raise RuntimeError\(c\)'
        r'[\S\s]*'
        r'RuntimeError: 3'
        r'[\S\s]*'
        r'Uncaught exception:\n'
        r'Traceback \(most recent call last\):'
        r'[\S\s]*'
        r'raise RuntimeError\(a\)'
        r'[\S\s]*'
        r'RuntimeError: 1\n\n'
        r'During handling of the above exception, another exception occurred:\n\n'
        r'Traceback \(most recent call last\):'
        r'[\S\s]*'
        r'raise RuntimeError\(b\)'
        r'[\S\s]*'
        r'RuntimeError: 2\n\n'
        r'During handling of the above exception, another exception occurred:\n\n'
        r'Traceback \(most recent call last\):'
        r'[\S\s]*'
        r'raise RuntimeError\(c\)'
        r'[\S\s]*'
        r'RuntimeError: 3'
        r'[\S\s]*'
    )
    assert re.search(pattern,data)

test_recur_exception()