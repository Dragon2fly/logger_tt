import re
import sys

import pytest
from ruamel.yaml import YAML
from subprocess import run, PIPE
from pathlib import Path

from logger_tt import setup_logging

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
    yaml = YAML(typ='safe')
    config_file = Path("../logger_tt/log_config.yaml")
    log_config = yaml.load(config_file.read_text())
    log_config['handlers']['error_file_handler']['when'] = 's'
    log_config['handlers']['error_file_handler']['interval'] = 5

    # write the config out
    test_config = Path("multiprocessing_issue3_config.yaml")
    yaml.dump(data=log_config, stream=test_config)

    # test it
    cmd = [sys.executable, "multiprocessing_issue3.py", "3"]
    result = run(cmd, stderr=PIPE, universal_newlines=True)
    assert "PermissionError: [WinError 32] The process cannot access the file" not in result.stderr
