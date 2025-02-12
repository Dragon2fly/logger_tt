import re
import sys

import pytest
from subprocess import run, PIPE
from pathlib import Path
from logger_tt import setup_logging
from tests.utils import config_modified


__author__ = "Duc Tin"

log = Path.cwd() / 'logs/log.txt'


def test_multiprocessing_normal():
    cmd = [sys.executable, "multiprocessing_normal.py", "3"]
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
    cmd = [sys.executable, "multiprocessing_pool.py", "10"]
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
    cmd = [sys.executable, "multiprocessing_threading.py", "10"]
    result = run(cmd, stdout=PIPE, universal_newlines=True)
    assert 'Parent process is ready to spawn child' in result.stdout
    expect = re.findall(r'Process-\d+ Thread-\d+.*? thread running from process', result.stdout)
    assert len(expect) == 10

    data = log.read_text(encoding='utf8')
    assert 'Parent process is ready to spawn child' in data
    expect = re.findall(r'Process-\d+ Thread-\d+.*? thread running from process', data)
    assert len(expect) == 10


def test_multiprocessing_rollover():
    # reduce the rollover interval to 5 seconds
    with config_modified(
            "multiprocessing_issue3_config.yaml",
            [
                ('handlers/error_file_handler/when', 's'),
                ('handlers/error_file_handler/interval', 5)]):
        # test it
        cmd = [sys.executable, "multiprocessing_issue3.py", "3"]
        result = run(cmd, stderr=PIPE, universal_newlines=True)
        assert "PermissionError: [WinError 32] The process cannot access the file" not in result.stderr


def test_multiprocessing_issue5():
    """child processes also create a log path which is unnecessary"""

    # test it
    cmd = [sys.executable, "multiprocessing_issue5.py", "3"]
    result = run(cmd, stdout=PIPE, universal_newlines=True)
    log_parent = log.parent
    sub_folders = [x for x in log_parent.iterdir() if x.is_dir()]
    number_of_path = len(sub_folders)

    # issue 5
    assert number_of_path == 1, sub_folders

    # to be sure
    logfile = sub_folders[0] / 'info.log'
    assert logfile.exists()
    assert 'Test for issue 5' in logfile.read_text()


def test_multiprocessing_port_change():
    """Change the tcp server's port to a user selected one"""

    with config_modified(
            "multiprocessing_change_port.yaml",
            [('logger_tt/use_multiprocessing', True),
             ('logger_tt/port', 6789)]):
        cmd = [sys.executable, "multiprocessing_change_port.py", "3"]
        result = run(cmd, stdout=PIPE, stderr=PIPE, universal_newlines=True)
        assert result.returncode == 0, f'subprocess crashed with error: {result.stderr}'

        assert '6789' in result.stdout, "Port failed to change"
        assert result.stdout.count("stopped") == 3, "Child process failed to log"


def test_multiprocessing_automatic_port():
    # write the config out
    with config_modified(
            "multiprocessing_change_port.yaml",
            [('logger_tt/use_multiprocessing', True),
             ('logger_tt/port', 0)]):
        cmd = [sys.executable, "multiprocessing_change_port.py", "4"]
        result = run(cmd, stdout=PIPE, stderr=PIPE, universal_newlines=True)
        assert result.returncode == 0, f'subprocess crashed with error: {result.stderr}'

        data = log.read_text(encoding='utf8')
        assert not result.stderr
        assert 'Server port' in data, "Port failed to change"
        assert 'Child picked up' in data, "Port failed to change"
        assert result.stdout.count("stopped") == 4, "Child process failed to log"


def test_multiprocessing_issue21_timeout1sec():
    # continue logging for 1 sec after main thread of main process exited

    # set server_timeout to 1 second is set in the target py file below
    timeout = 1
    with config_modified(
            'multiprocessing_issue21.yaml',
            [('logger_tt/use_multiprocessing', True),
             ('logger_tt/server_timeout', timeout)]):
        cmd = [sys.executable, "multiprocessing_issue21.py", "3"]
        result = run(cmd, stdout=PIPE, stderr=PIPE, universal_newlines=True)
        assert result.returncode == 0, f'subprocess crashed with error: {result.stderr}'

        data = log.read_text()
        main_thread_died_at, server_exit_at = map(float, re.findall(f'timestamp: ([0-9.]+)', data))
        dt = server_exit_at - main_thread_died_at
        assert timeout < dt < timeout + 1    # plus one second from socket timeout


def test_multiprocessing_issue21_timeout3sec():
    # continue logging for 3 sec after main thread of main process exited

    # set server_timeout to 3 second is set in the target py file below
    timeout = 3
    with config_modified(
            'multiprocessing_issue21.yaml',
            [('logger_tt/use_multiprocessing', True),
             ('logger_tt/server_timeout', timeout)]):
        cmd = [sys.executable, "multiprocessing_issue21.py", "3"]
        result = run(cmd, stdout=PIPE, stderr=PIPE, universal_newlines=True)
        assert result.returncode == 0, f'subprocess crashed with error: {result.stderr}'

        data = log.read_text()
        main_thread_died_at, server_exit_at = map(float, re.findall(f'timestamp: ([0-9.]+)', data))
        dt = server_exit_at - main_thread_died_at
        assert timeout < dt < timeout + 1       # plus one second from socket timeout


def test_multiprocessing_issue21_timeout5sec():
    # continue logging for 5 sec after main thread of main process exited

    timeout = 5
    with config_modified(
            'multiprocessing_issue21.yaml',
            [('logger_tt/use_multiprocessing', True),
             ('logger_tt/server_timeout', timeout)]):
        cmd = [sys.executable, "multiprocessing_issue21.py", "3"]
        result = run(cmd, stdout=PIPE, stderr=PIPE, universal_newlines=True)
        assert result.returncode == 0, f'subprocess crashed with error: {result.stderr}'

        data = log.read_text()
        main_thread_died_at, server_exit_at = map(float, re.findall(f'timestamp: ([0-9.]+)', data))
        dt = server_exit_at - main_thread_died_at
        assert timeout < dt < timeout + 1       # plus one second from socket timeout

        # this time there are some more log from the other processes
        assert 'worker complete' in data
