import re
import inspect
import logging


__author__ = "Duc Tin"


print_logger = logging.getLogger('PrintCapture')
print_level = {'debug': print_logger.debug,
               'info': print_logger.info,
               'warning': print_logger.warning,
               'warn': print_logger.warning,
               'critical': print_logger.critical,
               'error': print_logger.error,
               'err': print_logger.error,
               }


def log_level(message):
    """ guess level of msg and log it """
    msg = message.lower()[:100]     # search within the first few character only
    for keyword in print_level:
        pattern = fr'\b{keyword}\b'
        if re.search(pattern, msg):
            level = keyword
            break
    else:
        level = 'info'

    print_level[level](message)


def is_print_called():
    for frame in inspect.stack():
        context = frame.code_context[0].strip()
        if re.match(r'print\(.*\)', context):
            return True
    return False


class PrintCapture(object):
    """Man in the middle of the stream"""
    def __init__(self, original, strict: bool, guess_level=False):
        self.terminal = original        # original stream
        self.strict = strict            # True: log full stream, False: log print() message only
        self.guess_level = guess_level
        self.log = log_level if guess_level else print_logger.info

    def write(self, message):
        message = message.strip()
        if not message:
            return

        if not self.strict and is_print_called():
            # capture print() function only
            self.log(message)
        elif self.strict:
            # capture anything that use sys.stdout.write()
            self.log(message)
        else:
            # leave sys.stdout.write() alone
            self.terminal.write(message)

    def flush(self):
        pass
