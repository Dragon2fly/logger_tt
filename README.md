# Logger_tt
Make configuring logging simpler and log even exceptions that you forgot to catch.

## Usage:
**Install**: `pip install logger_tt`

In the most simple case, add the following code into your main python script of your project:

```python
from logger_tt import setup_logging    

setup_logging()
```

Then from any of your modules, you just need to get a `logger` and start logging.

```python
from logging import getLogger

logger = getLogger(__name__)

logger.debug('Module is initialized')
logger.info('Making connection ...')
```


This will provide your project the following **default** log behavior:

* log file: Assume that your `working directory` is `project_root`,
 log.txt is stored at your `project_root/logs/` folder. 
If log path doesn't exist, it will be created. 
The log file is time rotated at midnight. Maximum of 15 dates of log will be kept.
This log file's `level` is `DEBUG`.<br>
The log format is `[%(asctime)s] [%(name)s %(levelname)s] %(message)s` where time is `%Y-%m-%d %H:%M:%S`.<br>
Example: `[2020-05-09 00:31:33] [myproject.mymodule DEBUG] Module is initialized`

* console: log with level `INFO` and above will be printed to `stdout` of console. <br>
The format for console log is simpler: `[%(asctime)s] %(levelname)s: %(message)s`. <br>
Example: `[2020-05-09 00:31:34] INFO: Making connection ...`

* `urllib3` logger: this ready made logger is to silent unwanted messages from `requests` library.

* `root` logger: if there is no logger initialized in your module, this logger will be used with above behaviors.
This logger is also used to log **uncaught exception** in your project. Example:

```python
raise RecursionError
```

```python
# log.txt
[2020-05-09 11:42:08] [root ERROR] Uncaught exception
Traceback (most recent call last):
  File "D:/MyProject/Echelon/eyes.py", line 13, in <module>
    raise RecursionError
RecursionError
```

## Config:

1. You can overwrite the default log path with your own as following:

```python
    setup_logging(log_path='new/path/to/your_log.txt')
```

2. You can config your own logger and handler by providing either `yaml` or `json` config file as following:

```python
    setup_logging(config_path='path/to/.yaml_or_.json')
```

   Without providing a config file, the default config file with above **default** log behavior is used.
You could copy `log_conf.yaml` or `log_conf.json` shipped with this package to start making your version.


**Warning**: To process `.yaml` config file, you need to `pyyaml` package: `pip install pyyaml`

