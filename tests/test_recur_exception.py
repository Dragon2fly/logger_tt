import re
import sys
from pathlib import Path
from subprocess import run

__author__ = "ZeroRin"
log = Path(__file__).parent / 'logs/log.txt'

TRACE = r'''Traceback \(most recent call last\):
  File ".+?", line \d+?, in foo
    raise RuntimeError\(a\)
     |-> a = 1
RuntimeError: 1

During handling of the above exception, another exception occurred:

Traceback \(most recent call last\):
  File ".+?", line \d+, in foo
    raise RuntimeError\(b\)
     |-> b = 2
RuntimeError: 2

During handling of the above exception, another exception occurred:

Traceback \(most recent call last\):
  File ".+", line \d+, in <module>
    foo\(\)

  File ".+", line \d+, in foo
    raise RuntimeError\(c\)
     |-> c = 3
RuntimeError: 3'''


def test_recur_exception_caught():
    cmd = [sys.executable, "exception_on_exception.py", "caught"]
    run(cmd)
    data = log.read_text()
    pattern = rf'Caught exception\n{TRACE}'
    assert re.search(pattern, data, re.DOTALL)


def test_recur_exception_uncaught():
    cmd = [sys.executable, "exception_on_exception.py", "uncaught"]
    run(cmd)
    data = log.read_text()
    pattern = rf'Uncaught exception\n{TRACE}'
    assert re.search(pattern, data, re.DOTALL)