import re
import sys
import time

from subprocess import Popen
from pathlib import Path


__author__ = "Duc Tin"

log = Path.cwd() / 'logs/log.txt'


def join_popen(apps: list) -> list:
    while True:
        time.sleep(0.1)
        ret_codes = []

        for p in apps:
            ret_code = p.poll()
            if ret_code is not None:
                ret_codes.append(ret_code)

        if len(ret_codes) == len(apps):
            return ret_codes


def test_multiprocessing_one_server_multiple_clients():
    all_apps = []

    # first we start the server
    cmd = [sys.executable, "mp_app_server.py"]
    proc = Popen(cmd, shell=True, stdin=None, stdout=None, stderr=None, close_fds=True)
    all_apps.append(proc)

    # then start the other client apps
    for client in ['mp_app_client1.py', 'mp_app_client2.py']:
        cmd = [sys.executable, client]
        proc = Popen(cmd, shell=True, stdin=None, stdout=None, stderr=None, close_fds=True)
        all_apps.append(proc)

    # wait for all of them to exit
    return_codes = join_popen(all_apps)
    assert not any(return_codes), f'subprocess crashed'

    # only one log file of server is created, no client's log file
    files = list(log.parent.iterdir())
    assert len(files) == 1

    # there are logs of app1 and app2 in the sever log
    data = log.read_text()
    app1_log = re.findall(r'\[App1:\d+ INFO\] Doing task \d+', data)
    app2_log = re.findall(r'\[App2:\d+ INFO\] Doing task \d+', data)
    assert len(app1_log) == 10
    assert len(app2_log) == 10
