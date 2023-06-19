import shutil
import os, sys
from pathlib import Path


__author__ = "Duc Tin"

# extract needed paths
original_cwd = Path.cwd()
tests_folder = Path(__file__).parent
tests_path = tests_folder.absolute().as_posix()
lib_path = tests_folder.parent.absolute().as_posix()

# set environment variable PYTHONPATH with correct paths
# so that any subprocess can file the logger-tt while still giving the log file at the correct location
python_path = os.environ.get("PYTHONPATH", "") + os.pathsep
python_path += os.pathsep.join([lib_path, tests_path])
os.environ["PYTHONPATH"] = python_path.strip(os.pathsep)
if sys.version.startswith('3.6'):
    # don't know why but python 3.6 need this
    sys.path.insert(0, lib_path)

# set working directory to the "tests" folder
os.chdir(tests_folder)
log = tests_folder / 'logs/log.txt'


def remove_log():
    log_folder = log.parent
    if log_folder.exists():
        shutil.rmtree(log_folder)


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
    os.chdir(original_cwd)


def pytest_unconfigure(config):
    """
    called before test process is exited.
    """
    pass
