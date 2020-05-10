import sys
from io import StringIO
from pathlib import Path

__author__ = "Duc Tin"


log = Path.cwd() / 'logs/log.txt'


def remove_log():
    log_folder = log.parent
    if log_folder.exists():
        for file in log_folder.iterdir():
            file.unlink()
        # else:
        #     log_folder.unlink()


def pytest_runtest_setup(item):
    """call before execute a test of item"""
    remove_log()


def pytest_runtest_teardown(item, nextitem):
    """call after executed a test item"""
    import logging
    logging.shutdown()
    remove_log()


def pytest_configure(config):
    """
    Allows plugins and conftest files to perform initial configuration.
    This hook is called for every plugin and initial conftest
    file after command line options have been parsed.
    """
    pass


def pytest_sessionstart(session):
    """
    Called after the Session object has been created and
    before performing collection and entering the run test loop.
    """
    pass



def pytest_sessionfinish(session, exitstatus):
    """
    Called after whole test run finished, right before
    returning the exit status to the system.
    """
    pass


def pytest_unconfigure(config):
    """
    called before test process is exited.
    """
    pass
