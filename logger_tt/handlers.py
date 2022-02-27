import logging
import time
from threading import Thread
from datetime import datetime


class StreamHandlerWithBuffer(logging.StreamHandler):
    def __init__(self, stream=None, buffer_time: float = 0.2, buffer_lines: int = 50, debug=False):
        super().__init__(stream)
        assert buffer_time >= 0 or buffer_lines >= 0, "At least one kind of buffer must be set"

        self.buffer_time = buffer_time
        self.buffer_lines = buffer_lines
        self.buffer = []
        self.debug = debug

        if self.buffer_time:
            watcher = Thread(target=self.watcher, daemon=True)
            watcher.start()

    def export(self):
        """Actual writing data out to the stream"""

        if self.debug:
            self.buffer.append(f'StreamHandlerWithBuffer flush: {datetime.now()}')

        msg = self.terminator.join(self.buffer)
        stream = self.stream
        # issue 35046: merged two stream.writes into one.
        stream.write(msg + self.terminator)
        self.flush()

        self.buffer.clear()

    def emit(self, record):
        """
        Emit a record.

        If a formatter is specified, it is used to format the record.
        The record is then written to the stream with a trailing newline.  If
        exception information is present, it is formatted using
        traceback.print_exception and appended to the stream.  If the stream
        has an 'encoding' attribute, it is used to determine how to do the
        output to the stream.
        """
        try:
            msg = self.format(record)
            self.buffer.append(msg)
            if self.buffer_lines and len(self.buffer) >= self.buffer_lines:
                self.export()

        except RecursionError:  # See issue 36272
            raise
        except Exception:
            self.handleError(record)

    def watcher(self):
        """
        If buffer_time is used, this method will flush the buffer
        after every buffer_time seconds has passed.
        """
        if self.debug:
            self.buffer.append(f'StreamHandlerWithBuffer watcher starts: {datetime.now()}')
        while True:
            time.sleep(self.buffer_time)
            if self.buffer:
                self.acquire()
                self.export()
                self.release()


