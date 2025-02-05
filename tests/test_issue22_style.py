import sys
from pathlib import Path
from subprocess import run, PIPE
from tests.utils import config_modified

__author__ = "Duc Tin"
log = Path.cwd() / 'logs/log.txt'


def test_style_brace():
    with config_modified(
            'style_brace_config.yaml',
            [('formatters/simple/style', '{'),
             ('formatters/simple/format', '[{asctime}] {name}:{lineno} {levelname} {message}'),
             ('formatters/brief/style', '{'),
             ('formatters/brief/format', '[{asctime}] {levelname} {message}')
             ]):
        cmd = [sys.executable, 'format_style_issue22.py']
        result = run(cmd, stdout=PIPE, stderr=PIPE, universal_newlines=True)
        assert result.returncode == 0, f'subprocess crashed with error: {result.stderr}'

        data = log.read_text(encoding='utf8')

        # {} replaced correctly
        assert 'CRITICAL hello1 world' in data

        # {name} replaced correctly
        assert 'CRITICAL hello2 world' in data

        # {} {name} replaced correctly
        assert 'CRITICAL hello3 beautiful world' in data
