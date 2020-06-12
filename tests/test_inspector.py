from pathlib import Path
from subprocess import run

from logger_tt.inspector import get_recur_attr, get_repr


__author__ = "Duc Tin"
log = Path.cwd() / 'logs/log.txt'


def test_get_recur_attr():
    class A:
        def __init__(self):
            self.other = None

    a = A()
    b = A()
    a.other = b
    b.other = a

    assert get_recur_attr(a, 'other') == b
    assert get_recur_attr(a, 'other.other') == a
    assert get_recur_attr(a, 'other.other.other') == b
    assert get_recur_attr(a, 'other.other.me') == "!!! Not Exists"


def test_get_repr():
    class A:
        def __init__(self):
            self.other = None

        def __str__(self):
            return "A 123"

    class B:
        def __init__(self):
            self.other = None

        def __repr__(self):
            return 'B(arg=arg)'

    assert get_repr(A()) == "A 123"
    assert get_repr(B()) == "B(arg=arg)"


def test_1_scope():
    cmd = ["python", "exception_main.py"]
    run(cmd)

    data = log.read_text()
    assert "a.value = 3" in data
    assert "a.divisor = 0" in data


def test_nested_1():
    cmd = ["python", "exception_nested_1.py"]
    run(cmd)

    data = log.read_text(encoding='utf8')
    assert "var_in = Dummy(my dummy class)" in data
    assert "arg = (456, 789)" in data
    assert "kwargs = {'my_kw': 'hello', 'another_kw': 'world'}" in data
    assert "my_local_var = 345" in data


def test_nested_2():
    cmd = ["python", "exception_nested_2.py"]
    run(cmd)

    data = log.read_text(encoding='utf8')
    assert "self.value = 3" in data
    assert "self.non_exist = '!!! Not Exists'" in data
    assert "self.base.name = 'Nested dot'" in data


def test_full_context():
    cmd = ["python", "exception_full_context.py"]
    run(cmd)

    data = log.read_text(encoding='utf8')
    assert "__name__ = '__main__'" in data
    assert "Base = <class '__main__.Base'>" in data
    assert "arg = (456, 789)" in data
    assert "arg = 345" in data


def test_log_exception():
    cmd = ["python", "exception_log.py"]
    run(cmd)

    data = log.read_text(encoding='utf8')
    assert "-> a = 1" in data
    assert "-> b = 0" in data
