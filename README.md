# Logger_tt
Make configuring logging simpler and log even exceptions that you forgot to catch. <br>
Even multiprocessing logging becomes a breeze.

## Install
* From PYPI: `pip install logger_tt`
* From Github: clone or download this repo then `python setup.py install` 
    
## Overview:

In the most simple case, add the following code into your main python script of your project:

```python
from logger_tt import setup_logging    

setup_logging(full_context=1)
```

Then from any of your modules, you just need to get a `logger` and start logging.

```python
from logging import getLogger

logger = getLogger(__name__)

logger.debug('Module is initialized')
logger.info('Making connection ...')
```


This will provide your project with the following **default** log behavior:

* log file: Assume that your `working directory` is `project_root`,
 log.txt is stored at your `project_root/logs/` folder. 
If the log path doesn't exist, it will be created. 
The log file is time rotated at midnight. A maximum of 15 dates of logs will be kept.
This log file's `level` is `DEBUG`.<br>
The log format is `[%(asctime)s] [%(name)s %(levelname)s] %(message)s` where time is `%Y-%m-%d %H:%M:%S`.<br>
Example: `[2020-05-09 00:31:33] [myproject.mymodule DEBUG] Module is initialized`

* console: log with level `INFO` and above will be printed to `stdout` of the console. <br>
The format for console log is simpler: `[%(asctime)s] %(levelname)s: %(message)s`. <br>
Example: `[2020-05-09 00:31:34] INFO: Making connection ...`

* `urllib3` logger: this ready-made logger is to silent unwanted messages from `requests` library.
* suppressed logger: `exchangelib`. This sets logging level of `exchangelib` logger to `WARNING`.<br>
This is another way to silent unwanted messages from other module, read below for details.

* `root` logger: if there is no logger initialized in your module, this logger will be used with the above behaviors.
This logger is also used to log **uncaught exception** in your project. Example:

```python
raise RecursionError
```

```python
# log.txt
[2020-05-31 19:16:01] [root ERROR] Uncaught exception
Traceback (most recent call last):
  File "D:/MyProject/Echelon/eyes.py", line 13, in <module>
    raise RecursionError
    => var_in = Customer(name='John', member_id=123456)
    => arg = (456, 789)
    => kwargs = {'my_kw': 'hello', 'another_kw': 'world'}
RecursionError
```

* context logging: When an exception occur, variables used in the line of error are also logged.<br>
To log full local variables of current function scope, pass `full_context=1` to `setup_logging`.<br>
If you need the outer scope too, set `full_context` to `2`, `3` and so on...


## Usage:
All configs are done through `setup_logging` function:
```python
setup_logging(config_path="", log_path="", 
              capture_print=False, strict=False, guess_level=False,
              full_context=False,
              suppress_level_below=logging.WARNING,
              use_multiprocessing=False)
```

This function also return a `LogConfig` object. 
Except `config_path`, `log_path` and `use_multiprocessing`, 
other parameters are attributes of this object and can be changed on the fly.


1. You can overwrite the default log path with your own as follows:
    
   ```python
   setup_logging(log_path='new/path/to/your_log.txt')
   ```

2. You can config your own logger and handler by providing either `yaml` or `json` config file as follows:
    
   ```python
   setup_logging(config_path='path/to/.yaml_or_.json')
   ```

   Without providing a config file, the default config file with the above **default** log behavior is used.
   You could copy `log_conf.yaml` or `log_conf.json` shipped with this package to start making your version.

   **Warning**: To process `.yaml` config file, you need `pyyaml` package: `pip install pyyaml`

3. Capture stdout:

   If you have an old code base with a lot of `print(msg)` or `sys.stdout.write(msg)` and 
   don't have access or time to refactor them into something like `logger.info(msg)`, 
   you can capture these `msg` and log them to file, too.
   
   To capture only `msg` that is printed out by `print(msg)`, simply do as follows: 
    
   ```python
   setup_logging(capture_print=True)
   ```
   
   Example:
   ```python
   print('To be or not to be')
   sys.stdout.write('That is the question')
   ```
   
   ```
   # log.txt
   [2020-05-09 11:42:08] [PrintCapture INFO] To be or not to be
   ```
   
   <hr>
   
   Yes, `That is the question` is not captured. 
   Some libraries may directly use `sys.stdout.write` to draw on the screen (eg. progress bar) or do something quirk.
   This kind of information is usually not useful for users. But when you do need it, you can capture it as follows:
   
   ```python
   setup_logging(capture_print=True, strict=True)
   ```
   
   Example:
   ```python
   sys.stdout.write('The plane VJ-723 has been delayed')
   sys.stdout.write('New departure time has not been scheduled')
   ```
   
   ```
   # log.txt
   [2020-05-09 11:42:08] [PrintCapture INFO] The plane VJ-723 has been delayed
   [2020-05-09 11:42:08] [PrintCapture INFO] New departure time has not been scheduled
   ```
  
   <hr>
   
   As you have seen, the log level of the captured message is `INFO` . 
   What if the code base prints something like `An error has occurred. Abort operation.` and you want to log it as `Error`?
   Just add `guess_level=True` to `setup_logging()`.
   
   ```python
   setup_logging(capture_print=True, guess_level=True)
   ```
   
   Example:
   ```python
   print('An error has occurred. Abort operation.')
   print('A critical error has occurred during making request to database')
   ```
   
   ```
   # log.txt
   [2020-05-09 11:42:08] [PrintCapture ERROR] An error has occurred. Abort operation.
   [2020-05-09 11:42:08] [PrintCapture CRITICAL] A critical error has occurred during making request to database
   ```
   
   **Note**: Capturing stdout ignores messages of `blank line`. 
   That means messages like `\n\n` or `  `(spaces) will not appear in the log. 
   But messages that contain blank line(s) and other characters will be fully logged.
   For example, `\nTo day is a beautiful day\n` will be logged as is.  

4. Exception logging:
   
   Consider the following error code snippet:
   
   ```python
   API_KEY = "asdjhfbhbsdf82340hsdf09u3ionf98230234ilsfd"
   TIMEOUT = 60
   
   class MyProfile:
       def __init__(self, name):
           self.my_boss = None
           self.name = name

   def my_faulty_func(my_var, *args, **kwargs):
       new_var = 'local scope variable'
       me = MyProfile('John Wick')
       boss = MyProfile('Winston')
       me.my_boss = boss
       print(f'Information: {var} and {me.my_boss.name}' 
              ' at {me.my_boss.location} with {API_KEY}')
   
   if __name__ == '__main__':
       cpu_no = 4
       max_concurrent_processes = 3
       my_faulty_func(max_concurrent_processes, 'ryzen 7', freq=3.4)
   ```
   
   In our hypothetical code above,`print` function will raise an exception. 
   This exception, by default, will not only be logged but also analyzed with objects that appeared in the line:
   
   ```python
   [2020-06-06 09:36:01] ERROR: Uncaught exception:
   Traceback (most recent call last):
     File "D:/MyProject/AutoBanking/main.py", line 31, in <module>
       my_faulty_func(max_concurrent_processes, 'ryzen 7', freq=3.4)
        |-> my_faulty_func = <function my_faulty_func at 0x0000023770C6A288>
        |-> max_concurrent_processes = 3
   
     File "D:/MyProject/AutoBanking/main.py", line 25, in my_faulty_func
       print(f'Information: {var} and {me.my_boss.name}'
              ' at {me.my_boss.location} with {API_KEY}')
        |-> me.my_boss.name = 'Winston'
        |-> me.my_boss.location = '!!! Not Exists'
        |-> (outer) API_KEY = 'asdjhfbhbsdf82340hsdf09u3ionf98230234ilsfd'
   NameError: name 'var' is not defined
   ```
   
   **Note**: look at the `print(f'Information...` line, 
   `logger-tt` print this error line different from normal python traceback!
   With normal traceback, multi-line python statement has its only first line printed out.
   With `logger-tt`, full statement is grabbed for you.
   
   For each level in the stack, any object that appears in the error line is shown with its `readable representation`.
   This representation may not necessarily be `__repr__`. The choice between `__str__` and `__repr__` are as follows:
   * `__str__` : `__str__` is present and the object class's `__repr__` is default with `<class name at Address>`.
   * `__repr__`: `__str__` is present but the object class's `__repr__` is anything else, such as `ClassName(var=value)`.<br>
   Also, when `__str__` is missing, even if `__repr__` is `<class name at Address>`, it is used.
   
   Currently, if an object doesn't exist and is directly accessed, as `var` in this case, it will not be shown up.
   But if it is attribute accessed with dot `.`, as `location` in `me.my_boss.location`, 
   then its value is an explicit string `'!!! Not Exists'`.
   
   As you may have noticed, a variable `API_KEY` has its name prefixed with `outer`. <br>
   This tells you that the variable is defined in the outer scope, not local. 
   
   More often than not, only objects in the error line are not sufficient to diagnose what has happened.
   You want to know what the inputs of the function were. You want to know what the intermediate 
   calculated results were. You want to know other objects that appeared during runtime,
   not only local but also outer scope. In other words, you want to know the full context of what has happened.
   `logger-tt` is here with you:
   
   ```python
   setup_logging(full_context=2)
   ```
   
   With the above hypothetical code snippet, the error log becomes the following:
   
   ```python
   [2020-06-06 10:35:21] ERROR: Uncaught exception:
   Traceback (most recent call last):
     File "D:/MyProject/AutoBanking/main.py", line 31, in <module>
       my_faulty_func(max_concurrent_processes, 'ryzen 7', freq=3.4)
        |-> my_faulty_func = <function my_faulty_func at 0x0000019E3599A288>
        |-> max_concurrent_processes = 3
        => __name__ = '__main__'
        => __doc__ = None
        => __package__ = None
        => __loader__ = <_frozen_importlib_external.SourceFileLoader object at 0x0000019E35840E48>
        => __spec__ = None
        => __annotations__ = {}
        => __builtins__ = <module 'builtins' (built-in)>
        => __file__ = 'D:/MyProject/AutoBanking/main.py'
        => __cached__ = None
        => setup_logging = <function setup_logging at 0x0000019E35D111F8>
        => getLogger = <function getLogger at 0x0000019E35BC7C18>
        => logger = <Logger __main__ (DEBUG)>
        => API_KEY = 'asdjhfbhbsdf82340hsdf09u3ionf98230234ilsfd'
        => TIMEOUT = 60
        => MyProfile = <class '__main__.MyProfile'>
        => cpu_no = 4
   
     File "D:/MyProject/AutoBanking/main.py", line 25, in my_faulty_func
       print(f'Information: {var} and {me.my_boss.name} at {me.my_boss.location} with {API_KEY}')
        |-> me.my_boss.name = 'Winston'
        |-> me.my_boss.location = '!!! Not Exists'
        |-> (outer) API_KEY = 'asdjhfbhbsdf82340hsdf09u3ionf98230234ilsfd'
        => my_var = 3
        => args = ('ryzen 7',)
        => kwargs = {'freq': 3.4}
        => new_var = 'local scope variable'
        => me = <__main__.MyProfile object at 0x0000019E35D3BA48>
        => boss = <__main__.MyProfile object at 0x0000019E35D3B9C8>
   NameError: name 'var' is not defined
   ```
   
   Additional objects that not appear in the error line are prefixed with `=>`.
   
5. `try-except` exception logging:
   
   `exception context` logging also applies for `try-except` block.
    This means that if you call `logger.exception()` inside `except` block, 
    you would have all variables' value at the line of exception. For example,
    
   ```python
   def my_faulty_func():
       a = 10
       b = 0
       c = a/b
       return c
   
   def my_main():
       try:
           my_faulty_func()
       except Exception as e:
           logger.exception('some error has occured')
           print('Clean up resource')
   
   my_main()
   ``` 
   
   Then the log will show up as follows:
   
   ```python
   [2020-06-12 21:37:00] ERROR: some error has occured
   Traceback (most recent call last):
     File "D:/MyProject/exception_log.py", line 19, in my_main
       my_faulty_func()
        |-> my_faulty_func = <function my_faulty_func at 0x000001875DD4B168>
   
     File "D:/MyProject/exception_log.py", line 13, in my_faulty_func
       c = a / b
        |-> a = 10
        |-> b = 0
   ZeroDivisionError: division by zero
   Clean up resource
   ```
   
   **Note**: As in python's [logging document](https://docs.python.org/3/library/logging.html#logging.Logger.exception),
    `logger.exception()` should only be called from an exception handler, eg. inside `except` block.
   
   You don't need to pass `exception object` to `logger.exception()`. 
   It already knows how to get a traceback internally. 
   This enable you to pass any string in as a hint or a short description of what may have happened.  
   Otherwise, passing `exception object`, as `logger.exception(e)`, 
   will cause the first line of error report to be the message of exception. 
   In the case of the above example, it would be come `[2020-06-12 21:37:00] ERROR: division by zero`.

6. Silent unwanted logger:
   
   Third party modules also have logger and their messages are usually not related to your code.
   A bunch of unwanted messages may hide the one that come from your own module. 
   To prevent that and also reduce log file size, we need to silent unwanted loggers.
   
   There are two ways to silent a logger with config file:
   
   * Create a new logger: in `logger` section of config file, 
   add a new logger whose name is the same with the one you want to silent. 
   Set it level to `WARNING` or above. If you add `handlers`, you should also set `propagate` to `no` or `False`.
   Otherwise, the same message may be logged multiple times. Ex:
          
         urllib3:
           level: WARNING
           handlers: [console, error_file_handler]
           propagate: no
   
     Above setting only allow messages with level `WARNING` and above to be processed. 
     Usually that is enough to silent most of unwanted messages. If you need to silent more messages,
     try `ERROR` or `CRITICAL`.
   
   * Add logger's name to `suppress list`: Then a new logger with level default to `WARNING` will be 
   automatically created for you. Ex:
   
         suppress: [exchangelib, urllib3]
   
     If you need to suppress at even higher level, use `suppress_level_below` in `setup_logging`.
     For example suppress any message below `ERROR` level that comes from loggers in `suppress list`:
     
         setup_logging(suppress_level_below=logging.ERROR)

7. Logging in multiprocessing:
    
    This is archived by using multiprocessing queues or a socket server.
    
    For linux, copy-on-write while forking carries over logger's information. 
    So `multiprocess.Queue` is enough in this case. 
    
    For Windows, it is important that `setup_logging()` must be call out side of `if __name__ == '__main__':` guard block.
    Because child processes run from scratch and re-import `__main__`, by re-executing `setup_logging()`, 
    logger `SocketHandler` can be setup automatically. 
    
    This also means that the same config can work with both `multiprocessing.Process` and `multiprocessing.Pool` 
    magically without user doing anything special.
    
    Below is a minimal example:
    
    ```python
    import time
    from random import randint
    from multiprocessing import Process
   
    from logger_tt import setup_logging
    from logging import getLogger
    
    logger = getLogger(__name__)
    setup_logging(use_multiprocessing=True)        # for Windows, this line must be outside of guard block
    
    
    def worker(arg):
        logger.info(f'child process {arg}: started')
        time.sleep(randint(1,10))                  # imitate time consuming process
        logger.info(f'child process {arg}: stopped')
    
    
    if __name__ == '__main__':
        all_processes = []
        logger.info('Parent process is ready to spawn child')
        for i in range(3):
            p = Process(target=worker, args=(i,))
            all_processes.append(p)
            p.daemon = True
            p.start()
    
        for p in all_processes:
            p.join()
    ```
    
    The content of `log.txt` should be similar to below:
    
    ```text
    [2020-09-11 00:06:14] [root DEBUG] _________________New log started__________________
    [2020-09-11 00:06:14] [root DEBUG] Start logging server ...
    [2020-09-11 00:06:15] [__main__ INFO] Parent process is ready to spawn child
    [2020-09-11 00:06:16] [__mp_main__ INFO] child process 1: started
    [2020-09-11 00:06:16] [__mp_main__ INFO] child process 0: started
    [2020-09-11 00:06:16] [__mp_main__ INFO] child process 2: started
    [2020-09-11 00:06:17] [__mp_main__ INFO] child process 1: stopped
    [2020-09-11 00:06:17] [__mp_main__ INFO] child process 2: stopped
    [2020-09-11 00:06:17] [__mp_main__ INFO] child process 0: stopped
    ```

   **Note**: Under linux, to use `queueHandler`, you must pass `use_multiprocessing="fork"` to `setup_logging`.<br>
   Other options `True`, `spawn`, `forkserver` will use `socketHandler` by default.<br> 
   This is to prevent you `set_start_method` as `spawn` under linux and thus `queueHandler` won't work.
   
8. Temporary disable logging:

    Some block of code contain critical information, such as password processing, that should not be logged.
    You can disable logging for that block with a `logging_disabled` context:
  
    ```python
    from logger_tt import logging_disabled, getLogger
    
    logger = getLogger(__name__) 
   
    
    logger.debug('Begin a secret process')
    with logging_disabled():
        logger.info('This will not appear in any log')
    
    logger.debug('Finish')
    ```

# Sample config:

1. Yaml format:
   
   log_config.yaml:
   
   ```yaml
   version: 1
   disable_existing_loggers: False
   formatters:
     simple:
       format: "[%(asctime)s] [%(name)s %(levelname)s] %(message)s"
       datefmt: "%Y-%m-%d %H:%M:%S"
     brief: {
       format: "[%(asctime)s] %(levelname)s: %(message)s"
       datefmt: "%Y-%m-%d %H:%M:%S"
   handlers:
     console:
       class: logging.StreamHandler
       level: INFO
       formatter: simple
       stream: ext://sys.stdout
   
     error_file_handler:
       class: logging.handlers.TimedRotatingFileHandler
       level: DEBUG
       formatter: simple
       filename: logs/log.txt
       backupCount: 15
       encoding: utf8
       when: midnight
   
   loggers:
     urllib3:
       level: WARNING
       handlers: [console, error_file_handler]
       propagate: no
   
   root:
     level: DEBUG
     handlers: [console, error_file_handler]
   
   logger_tt: 
     suppress: [exchangelib]
   ```

<br>
2. Json format:

   log_config.json:

   ```json
   {
     "version": 1,
     "disable_existing_loggers": false,
     "formatters": {
       "simple": {
         "format": "[%(asctime)s] [%(name)s %(levelname)s] %(message)s",
         "datefmt": "%Y-%m-%d %H:%M:%S"
       },
       "brief": {
         "format": "[%(asctime)s] %(levelname)s: %(message)s",
         "datefmt": "%Y-%m-%d %H:%M:%S"
       }
     },
   
     "handlers": {
       "console": {
         "class": "logging.StreamHandler",
         "level": "INFO",
         "formatter": "brief",
         "stream": "ext://sys.stdout"
       },
   
       "error_file_handler": {
         "class": "logging.handlers.TimedRotatingFileHandler",
         "level": "DEBUG",
         "formatter": "simple",
         "filename": "logs/log.txt",
         "backupCount": 15,
         "encoding": "utf8",
         "when": "midnight"
       }
     },
   
     "loggers": {
       "urllib3": {
         "level": "ERROR",
         "handlers": ["console", "error_file_handler"],
         "propagate": false
       }
     },
   
     "root": {
       "level": "DEBUG",
       "handlers": ["console", "error_file_handler"]
     },

     "logger_tt": {
        "suppress": ["exchangelib"]
  }
   }
   ```

# changelog
## 1.5.1
* Use `socketHandler` as default for multiprocessing.
 Under linux, to use `queueHandler`, user must pass `use_multiprocessing="fork"` to `setup_logging` 
* Expose `logging_disabled` function to user: `from logger_tt import logging_disabled`. 
Then this function can be used as a context with `with` statement. 
* For convenient, user can import `getLogger` function from `logger_tt`, too.


## 1.5.0
* Logging is off-loaded to another thread and uses Queue to communicate. 
  This allow critical thread can do there job why time-consuming logging can be done later or in parallel. 
* Support for multiprocessing logging. For linux, a multiprocessing queue is used. 
  For Windows and macOS, a socket server is used instead.  
* `setup_logging` now return a `LogConfig` object. 
   You can set/change parameters of this object instead of passing arguments directly to `setup_logging`.<br>
   Only `config_path`, `log_path` and `use_multiprocessing` argument must be set with `setup_logging`.

__Behaviors changed__:

  * `full_context` is now an `int` that indicate the depth level from the bottom,
       where surrounding variables should be parsed. 
  * Turned off parsing full context for `raise` exception since many exception names are enough to understand the problem.
  * `log_config` file: move `suppress` section into `logger_tt` section. 
    Future settings will also be put into this section for the sake of managing. 
    If you need to hanging the logging framework, you just need to delete this section and move on. 

## 1.4.2
To prevent exception during logging, the following actions have been applied:
* Catch exception while parsing for object's value (property of a class)
* Catch exception while evaluating `__repr__` and `__str__` of object
* Disable logging while inspecting objects' value and representation
* Disable logging after an uncaught exception is logged. 
  Because the interpreter is shutting down, objects get deleted. 
  Logging put inside magic function `__del__` will raise error.

## 1.4.1
* Fix `print_capture` ignoring `print()` line in global scope due to lacking `code_context` frame
* If `__str__` of an object has multiple lines, also indent the second line and so on accordingly.
* If there is an exception during getting object's representation, 
return `!!! Attribute error` instead of `Error in sys.excepthook`

## 1.4.0
* Add an extra field `suppress` in config file. 
Any logger's name appeared in this list will have its messages suppressed.

## 1.3.2
* change extended ascii dash ` ─ ` to normal dash `-` 
so that it is displayed consistently in different encoding 

## 1.3.1
* change extended ascii vertical bar ` ├ ` to normal bar `|` 
so that it is displayed consistently in different encoding 

## 1.3.0
* Exception analyzing now fetch full multi-line python statement. 
This means that variables lie at seconds and below of the same statement can also be seen 
without the need of `full_context=True`.

## 1.2.1
* Extend logging context to `logger.exception()` as well. 
Now you can do `try-except` a block of code and still have a full context at error line. 

## 1.2.0
* Add logging context for uncaught exception. Now automatically log variables surrounding the error line, too.
* Add test cases for logging exception

## 1.1.1
* Fixed typos and grammar
* Add config file sample to README
* using full name `log_config.json` instead of `log_conf.json`, the same for yaml file 
* add test cases for `capture print`

## 1.1.0
* Add `capture print` functionality with `guess level` for the message.