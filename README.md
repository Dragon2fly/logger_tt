# Logger_tt
Make configuring logging simpler and log even exceptions that you forgot to catch. <br>
Even multiprocessing logging becomes a breeze.

[![Downloads](https://pepy.tech/badge/logger-tt)](https://pepy.tech/project/logger-tt)
[![PyPI version](https://badge.fury.io/py/logger-tt.svg)](https://pypi.org/project/logger-tt/)
[![GitHub license](https://img.shields.io/github/license/Dragon2fly/logger_tt)](https://github.com/Dragon2fly/logger_tt/blob/master/LICENSE)

## Table of contents

* [Install](#install)
* [Overview](#overview)
* [Usage](#usage)
  * [Overwrite the default log path](#1-overwrite-the-default-log-path)
  * [Provide your config file](#2-provide-your-config-file)
  * [Capture stdout](#3-capture-stdout)
  * [Exception logging](#4-exception-logging)
  * [try-except exception logging](#5-try-except-exception-logging)
  * [Silent unwanted loggers](#6-silent-unwanted-loggers)
  * [Logging in multiprocessing](#7-logging-in-multiprocessing)
  * [Temporary disable logging](#8-temporary-disable-logging)
  * [Limit traceback line length](#9-limit-traceback-lines-length)
  * [Analyze `raise` exception line](#10-analyze-raise-exception-line)
  * [StreamHandler with buffer](#11-streamhandler-with-buffer)
    
* [Sample config](#sample-config)
  * [YAML format](#1-yaml-format)
  * [JSON format](#2-json-format)
* [Changelog](#changelog)

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
There are two ways that you could obtain a logger.

* **Conventional way**: as you have always done it that way

  ```python
  from logging import getLogger
  
  logger = getLogger(__name__)
  ```

* **Convenient way**: use a pre-made logger named `logger_tt` from this package.

  ```python
  from logger_tt import logger
  ```

After that, you start logging as usual:

```python
logger.debug('Module is initialized')
logger.info('Making connection ...')

# output
[2020-07-21 11:24:19] [__main__:5 DEBUG] Module is initialized
[2020-07-21 11:24:19] [__main__:6 INFO] Making connection ...
```
  
Both ways give you the same output except the line number, obviously.<br>
The pre-made logger also has an advantage that it will automatically inject 
`threadName` and `processName` to the output in case of multithreading or multiprocessing. 

Both ways will provide your project with the following **default** log behaviors:

* **log file**: Assume that your `working directory` is `project_root`,
 log.txt is stored at your `project_root/logs/` folder. <br>
If the log path doesn't exist, it will be created. <br>
The log file is time rotated at midnight. A maximum of 15 dates of logs will be kept.
This log file's `level` is `DEBUG`.<br>
The log format is `[%(asctime)s] [%(name)s:%(lineno)d %(levelname)s] %(message)s`, <br> 
where the time format is `%Y-%m-%d %H:%M:%S`.<br>
*Example*: `[2020-05-09 00:31:33] [myproject.mymodule:26 DEBUG] Module is initialized`

* **console**: log records with level `INFO` and above will be printed to `stdout` of the console. <br>
The format for console log is simpler: `[%(asctime)s] %(levelname)s: %(message)s`. <br>
*Example*: `[2020-05-09 00:31:34] INFO: Making connection ...`

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
              use_multiprocessing=False,
              limit_line_length=1000, 
              analyze_raise_statement=False,
              host="",
              port=0,
              )
```

This function also return a `LogConfig` object. 
Except `config_path`, `log_path`, `use_multiprocessing`, `host` and `port`, 
other parameters are attributes of this object and can be changed on the fly.

Except `config_path`, `log_path`, all other parameters can be defined in `logger_tt` section in the config file
(see `Sample config` chapter below). 
Parameter with the same name passed in `setup_logging` function will override the one in the config file. 



### 1. Overwrite the default log path:
   Instead of `./logs/logs.txt`, you can overwrite with your own as follows
    
   ```python
   setup_logging(log_path='new/path/to/your_log.txt')
   ```

### 2. Provide your config file:
   You can config your own logger and handler by providing either `yaml` or `json` config file as follows:
    
   ```python
   setup_logging(config_path='path/to/.yaml_or_.json')
   ```

   Without providing a config file, the default config file with the above **default** log behavior is used.
   You could copy `log_conf.yaml` or `log_conf.json` shipped with this package to start making your version.

   **Warning**: To process `.yaml` config file, you either need `pyyaml` or `ruamel.yaml` package installed. 

### 3. Capture stdout:

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

### 4. Exception logging:
   
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
   With `logger-tt`, a full statement is grabbed for you.
   
   For each level in the stack, any object that appears in the error line is shown with its `readable representation`.
   This representation may not necessarily be `__repr__`. The choice between `__str__` and `__repr__` are as follows:
   * `__str__` : `__str__` is present, and the object class's `__repr__` is default with `<class name at Address>`.
   * `__repr__`: `__str__` is present, but the object class's `__repr__` is anything else, such as `ClassName(var=value)`.<br>
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

   **Note**: from version 1.6, uncaught exception happened in child thread of a multithreading 
    program will also be caught by `logger-tt` and logged normally. 
   If you are using python 3.8+, the new `threading.excepthook` won't be called as the uncaught exception
    has been handled by `logger-tt`. 
   
### 5. `try-except` exception logging:
   
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

### 6. Silent unwanted loggers:
   
   Third party modules also have loggers, and their messages are usually not related to your code.
   A bunch of unwanted messages may hide the one that come from your own module. 
   To prevent that and also reduce log file size, we need to silent unwanted loggers.
   
   By config file, there are two ways to silent a logger:
   
   * Create a new logger: in `logger` section of the config file, 
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
   
   You could also suppress loggers directly by `setup_logging`:
   
   ```python
   from logger_tt import setup_logging    

   setup_logging(suppress=['urllib3', 'exchangelib'])
   ```
   
### 7. Logging in multiprocessing:
    
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

from logger_tt import setup_logging, logger


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
[2020-10-28 20:39:14] [root:129 DEBUG] _________________New log started__________________
[2020-10-28 20:39:17] [root:130 DEBUG] Log config file: D:\my_project\log_config.json
[2020-10-28 20:39:17] [root:131 DEBUG] Logging server started!
[2020-10-28 20:39:22] [__main__:28 INFO] Parent process is ready to spawn child
[2020-10-28 20:39:22] [__mp_main__:16 INFO] Process-3 child process 2: started
[2020-10-28 20:39:22] [__mp_main__:16 INFO] Process-2 child process 1: started
[2020-10-28 20:39:22] [__mp_main__:16 INFO] Process-1 child process 0: started
[2020-10-28 20:39:23] [__mp_main__:18 INFO] Process-2 child process 1: stopped
[2020-10-28 20:39:23] [__mp_main__:18 INFO] Process-3 child process 2: stopped
[2020-10-28 20:39:24] [__mp_main__:18 INFO] Process-1 child process 0: stopped
```

   **Note**: Under linux, to use `queueHandler`, you must pass `use_multiprocessing="fork"` to `setup_logging`.<br>
   Other options `True`, `spawn`, `forkserver` will use `socketHandler` by default.<br> 
   This is to prevent you `set_start_method` as `spawn` under linux and thus `queueHandler` won't work.


   **Socket Address**: `socketHandler` will use tcp `localhost` and port `9020` by default. 
   In the rare cases where you run multiple multiprocessing applications with `logger_tt`, 
   the `Address already in use` error will be raised. In such cases, you have to set the address manually.

```python
setup_logging(host='localhost', port=6789)
```
   You can omit the `host` if you use `"localhost"`. 
   You can also set this in the log config file for each application. 

   
### 8. Temporary disable logging:

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

### 9. Limit traceback line's length:
   Sometimes the variable on the exception line can hold enormous amount of data, 
   such as content of some huge json file or html. In this case, printing out the whole content
   of the variable is quite point less and hinders debugging process as it hides away exception line.
    
   So we should limit the character to be printed out in each line of the traceback.
   And we can do it as simple as follow:

    setup_logging(limit_line_length=1000)

   The default limit is 1000 characters. All left characters will be replaced with `...`. 
   `limit_line_length=0` means no limit at all, prints the content of variable as is.  

   **Note**: if you input a `float`, it will be round down to nearest `int`. 
   A negative input is treated as inputting `0`.

   For demonstration purpose, the example below will limit to `100` characters:
   ```python
from logger_tt import setup_logging

setup_logging(limit_line_length=100)

def will_fail():
    loren_ipsum = "On the other hand, we denounce with righteous indignation and dislike men who are so beguiled and " \
                  "demoralized by the charms of pleasure of the moment, so blinded by desire, that they cannot " \
                  "foresee the pain and trouble that are bound to ensue; and equal blame belongs to those who fail in " \
                  "their duty through weakness of will, which is the same as saying through shrinking from toil and " \
                  "pain. These cases are perfectly simple and easy to distinguish. In a free hour, when our power of " \
                  "choice is untrammelled and when nothing prevents our being able to do what we like best, " \
                  "every pleasure is to be welcomed and every pain avoided. But in certain circumstances and owing to " \
                  "the claims of duty or the obligations of business it will frequently occur that pleasures have to " \
                  "be repudiated and annoyances accepted. The wise man therefore always holds in these matters to " \
                  "this principle of selection: he rejects pleasures to secure other greater pleasures, or else he " \
                  "endures pains to avoid worse pains. "

    print(f'Below is the {random} text used as a standard to test font: \n{loren_ipsum}')

if __name__ == '__main__':
    will_fail()
   ```

It will output the follow traceback. Pay attention to the `loren_ipsum` variable.
```python
[2021-06-19 17:40:39] ERROR: Uncaught exception:
Traceback (most recent call last):
  File "D:\my_project\long_line.py", line 21, in <module>
    will_fail()

  File "D:\my_project\long_line.py", line 18, in will_fail
    print(f'Below is the {random} text used as a standard to test font: \n{loren_ipsum}')
     |-> loren_ipsum = 'On the other hand, we denounce with righteous indignation and dislike men wh... (922 characters more)
NameError: name 'random' is not defined
```

### 10. Analyze `raise` exception line:
   If the code explicitly `raise` an exception, in most cases, 
   the variables on the line are substituted and printed out at the end of traceback.
   With `logger-tt` analyzing the `raise` statement, these variables are printed again too.

```python
[2021-06-19 18:15:01] ERROR: Uncaught exception:
Traceback (most recent call last):
  File "D:\my_project\module.py", line 9, in <module>
    raise RuntimeError(f'Too much laughing with a={a} and b={b}')
     |-> a = 'haha'
     |-> b = 'hihi'
RuntimeError: Too much laughing with a=haha and b=hihi
```

   The duplication is unnecessary, so from version `1.6.1`, `raise` exception line will not be analyzed as default.
   This resulted in a much cleaner log:

```python
[2021-06-19 18:15:30] ERROR: Uncaught exception:
Traceback (most recent call last):
  File "D:\my_project\module.py", line 9, in <module>
    raise RuntimeError(f'Too much laughing with a={a} and b={b}')
RuntimeError: Too much laughing with a=haha and b=hihi
```

   If the `raise` exception line in turn, raise another exception, and you want to analyze it,
   you could turn it back on as below:

    setup_logging(analyze_raise_statement=True)


### 11. StreamHandler with buffer:
   This handler is mainly to solve the problem of outputting a tremendous amount of logs to GUI applications in real-time.
   
   GUI applications use threading to display content while listening for user input (button click, key pressing, mouse scroll).
   But since cpython actually running only one thread at a time due to the GIL (global interpreter lock), 
   processing to display a tremendous amount of logs to the GUI widget will lock a thread for quite a long time. 
   During this time, no user input will be handled and the app seems unresponsive.

   The answer to this problem is to cache the log and output them at once after some interval or a number of cached lines reached a threshold.
   This significantly reduces the overhead on the widget side and makes the app responsive. 
   The solution is implemented in the new `StreamHandlerWithBuffer` which is inside `logger_tt.handlers`. 
   There are 2 steps to use this handler.
     
   * config the handler in the `log_config` file.

     ```yaml
     handlers:
       buffer_stream_handler:
         class: logger_tt.handlers.StreamHandlerWithBuffer
         level: DEBUG
         formatter: brief
         stream: ext://sys.stdout
         buffer_time: 0.5
         buffer_lines: 0
         debug: False
     
     root:
       level: DEBUG
       handlers: [console, error_file_handler, buffer_stream_handler]
     ```
     
     Its parameters look exactly like the `console` handler except the last 3 ones.
     * `buffer_time`: the cache time interval in **seconds** before it flush the log out 
     * `buffer_line`: the **number of line** to cache before it flush the log out
     * `debug`: log the time that it flush the log out or not<br>
     
     For `buffer_line`, to avoid the last lines of log not printed out as the number of line is below threshold, 
     you should set `buffer_time` to a certain number too.  

     Then, you need to add this handler to the `root` logger's `handlers` list.


   * replace the `stream`:
     you need to replace the `stdout` with your GUI widget stream.
     You cannot do this in the config file since your widget is only appear during runtime. 
     You have to do this in the code.

     ```python
     config = setup_logging(config_path='log_config.json')
     config.replace_handler_stream(index=HANDLER_INDEX, stream=WIDGET_STREAM)
     ```
     Setup your logging as usual with your config file, 
     then call `replace_handler_stream` to replace the with your widget's stream.
     * `index`: the index of the handler, in the root logger' `handlers` list, that you want to replace the stream
     * `stream`: the stream that you want to put into this handler.
   

   Below is the example with `PySimpleGUI v4.57.0` with the above config.
   ```python
import time
from threading import Thread

import PySimpleGUI as sg
from logger_tt import setup_logging, logger

stop_flag = False

# GUI config
sg.theme('DarkAmber')
layout = [
    [[sg.Button("Show Log", key="-show_log-"),
     sg.Button("stop", key="-stop-", button_color='red')],
     sg.Multiline(size=(80, 30), font='Courier 10', key='log', autoscroll=True)]
]
window = sg.Window('Logging tool', layout, finalize=True)

# logging config
config = setup_logging(config_path='log_config.json')
config.replace_handler_stream(index=2, stream=window["log"])


def my_func():
    """long running task in the background"""
    while not stop_flag:
        for i in range(1000):
            logger.warning(f" {i} Function is empty")
        time.sleep(1)


while True:
    event, values = window.read()
    if event == sg.WINDOW_CLOSED:
        break
    if event == "-show_log-":
        logger.info(__name__)
        Thread(target=my_func).start()
    if event == "-stop-":
        stop_flag = True
        logger.info(f"stop button pressed")

window.close()
```
You could set `index=0` to use the normal `StreamHandler` and 
see the difference while clicking the `stop` button for yourself.


# Sample config:
Below are default config files that used by `logger-tt`. You can copy and modify them as needed. 
## 1. Yaml format:
   
   log_config.yaml:
   
```yaml
# This is an example of config file
# In case of no config provided, log_config.json file will be loaded
# If you need a yaml file, install pyyaml or ruamel.yaml package and copy this file
version: 1
disable_existing_loggers: False
formatters:
  simple:
    format: "[%(asctime)s] [%(name)s:%(lineno)d %(levelname)s] %(message)s"
    datefmt: "%Y-%m-%d %H:%M:%S"
  brief:
    format: "[%(asctime)s] %(levelname)s: %(message)s"
    datefmt: "%Y-%m-%d %H:%M:%S"

handlers:
  console:
    class: logging.StreamHandler
    level: INFO
    formatter: brief
    stream: ext://sys.stdout

  error_file_handler:
    class: logging.handlers.TimedRotatingFileHandler
    level: DEBUG
    formatter: simple
    filename: logs/log.txt
    backupCount: 15
    encoding: utf8
    when: midnight
  
  buffer_stream_handler:
    class: logger_tt.handlers.StreamHandlerWithBuffer
    level: DEBUG
    formatter: brief
    stream: ext://sys.stdout
    buffer_time: 0.5
    buffer_lines: 0
    debug: False

loggers:
  urllib3:
    level: WARNING
    handlers: [console, error_file_handler]
    propagate: no

root:
  level: DEBUG
  handlers: [console, error_file_handler]

logger_tt:
  suppress: ["exchangelib"]
  suppress_level_below: "WARNING"
  capture_print: False
  strict: False
  guess_level: False
  full_context: 0
  use_multiprocessing: False
  limit_line_length: 1000
  analyze_raise_statement: False
  default_logger_formats:
    normal: ["%(name)s", "%(filename)s"]
    thread: ["%(message)s", "%(threadName)s %(message)s"]
    multiprocess: ["%(message)s", "%(processName)s %(message)s"]
    both: ["%(message)s", "%(processName)s %(threadName)s %(message)s"]
```

## 2. Json format:

   log_config.json:
   
```json
{
 "version": 1,
 "disable_existing_loggers": false,
 "formatters": {
   "simple": {
     "format": "[%(asctime)s] [%(name)s:%(lineno)d %(levelname)s] %(message)s",
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
   },

   "buffer_stream_handler": {
     "class": "logger_tt.handlers.StreamHandlerWithBuffer",
     "level": "INFO",
     "formatter": "simple",
     "stream": "ext://sys.stdout",
     "buffer_time": 0.5,
     "buffer_lines": 0,
     "debug": false
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
   "suppress": ["exchangelib"],
   "suppress_level_below": "WARNING",
   "capture_print": false,
   "strict": false,
   "guess_level": false,
   "full_context": 0,
   "use_multiprocessing": false,
   "limit_line_length": 1000,
   "analyze_raise_statement": false,
   "default_logger_formats": {
      "normal": ["%(name)s", "%(filename)s"],
      "thread": ["%(message)s", "%(threadName)s %(message)s"],
      "multiprocess": ["%(message)s", "%(processName)s %(message)s"],
      "both": ["%(message)s", "%(processName)s %(threadName)s %(message)s"]
   }
 }
}
```

# Changelog
## 1.7.0
* Fixed: 
  * multiprocessing: log file rollover fails as child process keep opening the file.
  * multiprocessing: if the log path is set by a variable with time, 
    child process creates a new redundant log path.
  
* New functionality: Added `StreamHandlerWithBuffer`. Buffer the log output by time or by line number.
    GUI app could use this handler to keep the app responsive while having a tremendous log output.

* Usability: In multiprocessing logging, 
  users can set the log server address themselves through `setup_logging` or log config file.

## 1.6.1
* Added `limit_line_length` parameter: log only maximum `n` characters for each traceback line. 
  This prevents dumping the whole huge content of the variable into the log. `n=1000` by default.
  
* Added `analyze_raise_statement` parameter: 
  `logger-tt` no longer analyze the `raise` statement by default. 
  This avoids logging value of variables on the `raise` statement two time, especially when the content 
  of these variables are huge.

## 1.6.0
* Fixed: If an exception happened on the multiline statement,
 py3.6 and py3.7 return the last line while py3.9 returns the first line. 
  Plus the `tokenize` module's behavior has changed, so it made grabbing the 
  all the lines of the statement inconsistent and sometime buggy.
  Now `logger-tt` only grabs maximum of 10 lines and grabs more accurately, 
  more consistent between different python version.
  
* Added support for `ruamel.yaml` package. If you already have it installed, 
  you don't need to install `pyyaml` to use `config.yaml` file 
  
* New feature: Uncaught exception happened in child thread of multi-threading 
 program will also be logged. For python 3.8+, `threading.excepthook` will not run
  as the exception is already caught by `logger-tt`.


## 1.5.2
**Improved the pre-made logger named `logger_tt`** 

* `logger_tt` now can detect the qualified `__name__` of the module that calls it.
 Instead of `filename`, output log line will have the `__name__` as regular logger.
 
  For example:
 
      [2020-07-21 11:24:19] [my_module.py:5 DEBUG] Module is initialized
      [2020-07-21 11:24:19] [sub_module.py:15 DEBUG] Entering sub module
    
  Now becomes
 
      [2020-07-21 11:24:19] [__main__:5 DEBUG] Module is initialized
      [2020-07-21 11:24:19] [my_module.submodule:15 DEBUG] Entering sub module
 
* Suppressing loggers also works with log records output by `logger_tt` by using the qualified `__name__` too.
 For example, suppressing `my_module.submodule` will tell `logger_tt` not to output the second line.
 
  This is much better than suppressing `logger_tt` if you use this same logger in other modules too. 

* You now can define fields of log record for `logger_tt` in the log config file too. 
 Just looks for `default_logger_formats` section. 
 It works by replacing the field in the formatters that are used by any handler of the root logger.

**Pre-existing loggers:**<br> 
Before this version, if you import submodules before importing `logger_tt` and 
there are loggers in submodules, these loggers do not inspect exception when you call `logger.exception()`. 
That is because there class was different from the loggers created after importing `logger_tt`.
Now all loggers have the same new class regardless the point of importing `logger_tt`.

**setup_logging()**: This function should only be called once. 
Add a warning if it is called more than one time.

## 1.5.1
* Use `socketHandler` as default for multiprocessing.
 Under linux, to use `queueHandler`, user must pass `use_multiprocessing="fork"` to `setup_logging` 
* Expose `logging_disabled` function to user: `from logger_tt import logging_disabled`. 
Then this function can be used as a context with `with` statement. 
* For convenient, user can import a pre-made `logger` from `logger_tt` to use right away in sub modules.
The built-in `getLogger` function can be imported from `logger_tt`, too.
* Added line number to a default `simple` log record formatter in the config file.
* Most parameters of `setup_logging()` function can be specified in the config file, too.
If the same parameter is specified in both `setup_logging()` function and in the config file,
the parameter passed in `setup_logging()` will be used.

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