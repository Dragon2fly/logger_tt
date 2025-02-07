import sys
import logging
from .inspector import analyze_exception_recur
from string import Template

__author__ = "Duc Tin"

PY_VER = sys.version_info.major, sys.version_info.minor


class ExceptionLogger(logging.Logger):
    """Modify the `exception` func so that it print out context too
        This allows user do a try-except in outer code but still has the full log
        of nested code's error
        Example:
            try:
                a, b = 1, 0
            except Exception as e:
                logger.exception(e)
            # then move on
    """

    _logger_names = {}
    config = None

    def exception(self, msg, *args, exc_info=True, **kwargs):
        if exc_info:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            full_context = self.config.full_context
            limit_length = self.config.limit_line_length
            analyze_raise = self.config.analyze_raise_statement
            txt = analyze_exception_recur(exc_value, full_context, limit_length, analyze_raise)
            logging.error(f'{msg}\n{txt}')
        else:
            logging.error(msg, *args, exc_info=exc_info, **kwargs)

    def makeRecord(self, name, level, fn, lno, msg, args, exc_info, func=None, extra=None, sinfo=None):
        record = super().makeRecord(name, level, fn, lno, msg, args, exc_info, func, extra, sinfo)
        record.kwargs = self.msg_kwargs

        if name == 'logger_tt':
            # try to get the __name__ of the module that use the default logger: logger_tt
            pathname = fn.replace('\\', '/')
            qualified_name = self._logger_names.get(pathname)
            if not qualified_name:
                for qualified_name, module in sys.modules.items():
                    file = getattr(module, '__file__', None)
                    if file and file.replace('\\', '/') == pathname:
                        self._logger_names[pathname] = qualified_name
                        break

            if qualified_name == '__main__' and record.processName != 'MainProcess':
                qualified_name = '__mp_main__'

            record.filename = qualified_name or record.filename

        return record

    def _log(self, level, msg, args, exc_info=None, extra=None, stack_info=False,
             stacklevel=2, **kwargs):
        # Here we override the original method to be able to save the kwargs that
        # the original method omits when create a LogRecord.
        # "extra" argument could be updated too but that is for other placeholders in
        # the format string, not specific to the message.
        self.msg_kwargs = kwargs

        # Notice that stacklevel is default to 2 instead of 1
        # This is for self.findCaller to find the true caller of the log
        # instead of this overridden method
        if PY_VER > (3, 7):
            super()._log(level, msg, args, exc_info, extra, stack_info, stacklevel)
        else:
            super()._log(level, msg, args, exc_info, extra, stack_info)


class DefaultLogRecord(logging.LogRecord):
    def __init__(self, name, level, pathname, lineno,
                 msg, args, exc_info, func=None, sinfo=None, **kwargs):
        self.kwargs = kwargs
        super().__init__(name, level, pathname, lineno, msg, args, exc_info, func, sinfo)

    def get_message_brace(self):
        """
        Return the message for this LogRecord.

        Return the message for this LogRecord after merging any user-supplied
        arguments with the message.
        """
        msg = str(self.msg)
        if self.args and self.kwargs:
            msg = msg.format(*self.args, **self.kwargs)
        elif self.kwargs:
            msg = msg.format(**self.kwargs)
        elif self.args:
            msg = msg.format(*self.args)
        return msg

    def get_message_dollar(self):
        """
        Return the message for this LogRecord.

        Return the message for this LogRecord after merging any user-supplied
        arguments with the message.
        """
        msg = str(self.msg)
        if self.kwargs:
            msg = Template(msg).safe_substitute(self.kwargs)

        return msg

    def get_message_percent(self):
        """
        Return the message for this LogRecord.

        Return the message for this LogRecord after merging any user-supplied
        arguments with the message.
        """
        msg = str(self.msg)
        if self.args:
            msg = msg % self.args
        return msg

    @classmethod
    def set_style(cls, style: str):
        if style == '%':
            cls.getMessage = cls.get_message_percent
        elif style == '$':
            cls.getMessage = cls.get_message_dollar
        elif style == '{':
            cls.getMessage = cls.get_message_brace
        else:
            pass


class DefaultFormatter(logging.Formatter):
    """Based on the format string of any handler in root, we make new formatters for
        the default logger - logger_tt. This is a way to inject information but
        using the same handlers as regular logger.
    """
    default_formats = dict(normal=["%(name)s", "%(filename)s"],
                           thread=["%(message)s", "%(threadName)s %(message)s"],
                           multiprocess=["%(message)s", "%(processName)s %(message)s"],
                           both=["%(message)s", "%(processName)s %(threadName)s %(message)s"])

    def __init__(self, fmt: str = '', datefmt: str = '', style: str = '%'):
        self._check_style(style)
        super(DefaultFormatter, self).__init__(fmt=fmt, datefmt=datefmt, style=style)

        self._logger_tt_formatters = {}
        for case, fmt in self._standardize(fmt).items():
            self._logger_tt_formatters[case] = logging.Formatter(fmt=fmt, datefmt=datefmt, style=style)

    def _check_style(self, style):
        DefaultLogRecord.set_style(style)
        if style == '{':
            for key, val in self.default_formats.items():
                brace_fmt = [x.replace('%(', '{').replace(')s', '}') for x in val]
                self.default_formats[key] = brace_fmt
        elif style == '$':
            for key, val in self.default_formats.items():
                dollar_fmt = [x.replace('%(', '${').replace(')s', '}') for x in val]
                self.default_formats[key] = dollar_fmt
        else:
            pass

    def _standardize(self, fmt):
        formatters = {'normal': fmt.replace(self.default_formats['normal'][0], self.default_formats['normal'][1])}

        # concurrent format
        concurrent_fmt = formatters['normal'].replace('%(threadName)s', '').replace('%(processName)s', '')
        for _type, replacement in self.default_formats.items():
            if _type == 'normal':
                continue

            old, new = replacement
            formatters[_type] = concurrent_fmt.replace(old, new)

        return formatters

    def format(self, record):
        if record.name == 'logger_tt':
            if record.processName == 'MainProcess' and record.threadName == 'MainThread':
                return self._logger_tt_formatters['normal'].format(record)
            elif record.processName == 'MainProcess' and record.threadName != 'MainThread':
                return self._logger_tt_formatters['thread'].format(record)
            elif record.processName != 'MainProcess' and record.threadName == 'MainThread':
                return self._logger_tt_formatters['multiprocess'].format(record)
            else:
                return self._logger_tt_formatters['both'].format(record)

        return super(DefaultFormatter, self).format(record)
