import json
import re
import sys
from pathlib import Path
from subprocess import run

__author__ = "ZeroRin"
log = Path.cwd()/'logs/log.txt'
modified_log =  Path.cwd()/'logs/log.log'

def test_edit_log_path():
    '''
    passing a log_path in string to setup_logging
    all file handlers should be redirected to that file
    '''
    # create config file with multiple file handlers 
    config_file = Path("../logger_tt/log_config.json")
    config = json.loads(config_file.read_text())
    config['handlers']['urllib_file_handler'] = config['handlers']['error_file_handler']
    config['loggers']['urllib3']['handlers'] = ['urllib_file_handler']

    test_config = Path("edit_log_path.json")
    test_config.write_text(json.dumps(config))

    # run test and check outputs
    cmd = [sys.executable, "edit_log_path.py", repr(str(modified_log))]
    run(cmd)
    data = modified_log.read_text()
    assert re.search('A log from default logger', data)
    assert re.search('A log from urllib logger', data)
    test_config.unlink()

def test_edit_log_path_partial():
    '''
    passing a log_path in dict to setup_logging
    only selected file handler should be redirected to that file
    '''
    # create config file with multiple file handlers 
    config_file = Path("../logger_tt/log_config.json")
    config = json.loads(config_file.read_text())
    config['handlers']['urllib_file_handler'] = config['handlers']['error_file_handler']
    config['loggers']['urllib3']['handlers'] = ['urllib_file_handler']
    
    test_config = Path("edit_log_path.json")
    test_config.write_text(json.dumps(config))

    # run test and check outputs
    cmd = [sys.executable, "edit_log_path.py", repr(dict(urllib_file_handler=str(modified_log)))]
    run(cmd)
    data = log.read_text()
    assert re.search('A log from default logger', data)
    data = modified_log.read_text()
    assert re.search('A log from urllib logger', data)
    test_config.unlink()