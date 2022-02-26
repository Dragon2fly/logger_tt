import re
import sys
import time
from pathlib import Path
from subprocess import run, PIPE

import pytest

from logger_tt.inspector import get_recur_attr, get_repr, is_full_statement, get_full_statement, MEM_PATTERN

__author__ = "Duc Tin"
log = Path.cwd() / 'logs/log.txt'


def test_get_recur_attr():
    class A:
        def __init__(self):
            self.other = None

        @property
        def x(self):
            # error while getting attribute
            return 1 / 0

    a = A()
    b = A()
    a.other = b
    b.other = a

    assert get_recur_attr(a, 'other') == b
    assert get_recur_attr(a, 'other.other') == a
    assert get_recur_attr(a, 'other.other.other') == b
    assert get_recur_attr(a, 'other.other.me') == "!!! Not Exists"
    assert "!!! Attribute Error: " in get_recur_attr(a, 'other.x')


def test_get_repr():
    class A:
        def __str__(self):
            return "A 123"

    class B:
        def __repr__(self):
            return 'B(arg=arg)'

    class C:
        def __repr__(self):
            # error while getting representation
            return "123" + 3

    class D:
        def __str__(self):
            # return __repr__ in case of __str__ error
            return "123" + 3

    assert get_repr(A()) == "A 123"
    assert get_repr(B()) == "B(arg=arg)"
    assert "!!! repr error:" in get_repr(C())
    assert MEM_PATTERN.match(get_repr(D()))


def test_is_full_statement():
    pycode = "print(f'{self.value} '"
    assert not is_full_statement(pycode)

    assert is_full_statement(pycode, "      'f{another} line'", "      )")

    pycode = "print(3+4)"
    assert is_full_statement(pycode)


def test_1_scope():
    cmd = [sys.executable, "exception_main.py"]
    run(cmd)

    data = log.read_text()
    assert "a.value = 3" in data
    assert "a.divisor = 0" in data


def test_nested_1():
    cmd = [sys.executable, "exception_nested_1.py"]
    run(cmd)

    data = log.read_text(encoding='utf8')
    assert "var_in = Dummy(my dummy class)" in data
    assert "arg = (456, 789)" in data
    assert "kwargs = {'my_kw': 'hello', 'another_kw': 'world'}" in data
    assert "my_local_var = 345" in data


def test_nested_2():
    cmd = [sys.executable, "exception_nested_2.py"]
    run(cmd)

    data = log.read_text(encoding='utf8')
    assert "self.value = 3" in data
    assert "self.non_exist = '!!! Not Exists'" in data
    assert "self.base.name = 'Nested dot'" in data


def test_full_context_level1():
    cmd = [sys.executable, "exception_full_context.py", "1"]
    run(cmd)

    data = log.read_text(encoding='utf8')
    assert "__name__ = '__main__'" not in data
    assert "Base = <class '__main__.Base'>" not in data
    assert "arg = (456, 789)" not in data
    assert "arg = 345" in data


def test_full_context_level2():
    cmd = [sys.executable, "exception_full_context.py", "2"]
    run(cmd)

    data = log.read_text(encoding='utf8')
    assert "__name__ = '__main__'" not in data
    assert "Base = <class '__main__.Base'>" not in data
    assert "arg = (456, 789)" in data
    assert "arg = 345" in data


def test_full_context_level3():
    cmd = [sys.executable, "exception_full_context.py", "3"]
    run(cmd)

    data = log.read_text(encoding='utf8')
    assert "__name__ = '__main__'" in data
    assert "Base = <class '__main__.Base'>" in data
    assert "arg = (456, 789)" in data
    assert "arg = 345" in data


def test_log_exception():
    cmd = [sys.executable, "exception_log.py"]
    run(cmd)

    data = log.read_text(encoding='utf8')
    assert "-> a = 1" in data
    assert "-> b = 0" in data


@pytest.mark.skipif(sys.version_info >= (3, 7), reason="'tokenize' module changed behavior")
def test_multiline():
    cmd = [sys.executable, "exception_multiline.py"]
    run(cmd)

    data = log.read_text(encoding='utf8')
    assert "self.value = 3" in data
    assert "self.non_exist = '!!! Not Exists'" in data
    assert "self.base.name = 'Nested dot'" in data


def test_multiline2():
    cmd = [sys.executable, "exception_multiline2.py"]
    run(cmd)

    data = log.read_text(encoding='utf8')
    res = re.findall(r'( *ehehe)', data)
    indent_1 = res[0].count(' ')
    indent_2 = res[1].count(' ')

    assert indent_1 == 13
    assert indent_2 == 27


@pytest.mark.skip(reason='No example of deadlock')
def test_deadlock():
    cmd = [sys.executable, "exception_deadlock.py"]
    run(cmd)

    data = log.read_text(encoding='utf8')
    print(data)
    # fix me
    assert 1


def test_del_logging():
    cmd = [sys.executable, "exception_del_logging.py"]
    output = run(cmd, stderr=PIPE, universal_newlines=True)
    assert "Logging error" not in output.stderr


def test_logging_class():
    # pre-existing logger should also have a new exception handler
    cmd = [sys.executable, "sub_module.py"]
    output = run(cmd, stdout=PIPE, universal_newlines=True)
    data = log.read_text()
    assert "a = 3" in data
    assert "b = 0" in data
    assert "a = 3" in output.stdout
    assert "b = 0" in output.stdout


def test_get_full_statement():
    lines = get_full_statement('full_statement.py', 5)
    assert lines == ['print(x,\n', '          y(1,\n', '            z),\n', '          2)']

    lines = get_full_statement('full_statement.py', 6)
    assert lines == ['y(1,\n', '  z),']

    lines = get_full_statement('full_statement.py', 7)
    assert lines == ['y(1,\n', '  z),']

    lines = get_full_statement('full_statement.py', 17)
    assert lines == ['txt = {a: 3,\n', '       b: 4,\n', '       c:5}']

    lines = get_full_statement('full_statement.py', 23)
    assert lines == ['my_list = [a,\n', '           b,\n', '           c]']


@pytest.mark.parametrize('limit, result', [(-1, "or else he endures pains to avoid worse pains. '"),
                                           (0, "or else he endures pains to avoid worse pains. '"),
                                           (100, "|-> loren_ipsum = 'On the other hand, we denounce with righteous "
                                                 "indignation and dislike men wh... (922 characters more)"),
                                           ])
def test_long_line(limit, result):
    cmd = [sys.executable, f"exception_raise_long_line.py", str(limit), "1"]
    run(cmd, stdout=PIPE, universal_newlines=True)
    data = log.read_text()

    assert result in data


@pytest.mark.parametrize('analyze, result', [(False, "|-> loren_ipsum"),
                                             (True, "|-> loren_ipsum"),
                                             ])
def test_analyze_raise_statement(analyze, result):
    cmd = [sys.executable, f"exception_raise_long_line.py", "0", str(int(analyze))]
    run(cmd, stdout=PIPE, universal_newlines=True)
    data = log.read_text()

    if analyze:
        assert result in data
    else:
        assert result not in data
