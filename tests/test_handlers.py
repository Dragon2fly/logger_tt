import time

from io import StringIO
from logging import getLogger, DEBUG, Formatter

import pytest
from logger_tt.handlers import StreamHandlerWithBuffer


@pytest.mark.parametrize('threshold', [0.2, 0.4])
def test_handler_with_buffer_time(caplog, threshold):
    logger = getLogger('Test buffer time')
    my_stream = StringIO()
    handler = StreamHandlerWithBuffer(stream=my_stream, buffer_time=threshold, buffer_lines=0)
    formatter = Formatter(fmt="[%(asctime)s.%(msecs)03d] %(levelname)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.propagate = False

    # only one timestamp when not exceeding time threshold
    lengths1 = []
    with caplog.at_level(DEBUG):
        t0 = time.time()
        while True:
            logger.info('This is my log message')
            dt = time.time() - t0
            my_stream.seek(0)
            logs = my_stream.read()

            if dt < threshold:
                assert not logs, "No logs while threshold is not exceeded"
            elif threshold <= dt < threshold + 0.016:
                time.sleep(0.02)
            elif threshold + 0.016 <= dt < 2*threshold:
                assert logs, "logs appear after threshold is exceeded"
                lengths1.append(len(logs))
            elif 2*threshold <= dt < 2*threshold + 0.016:
                time.sleep(0.02)
            elif dt >= 2*threshold + 0.016:
                assert len(set(lengths1)) == 1, "During the interval of threshold, no new log should appear"
                assert len(logs) != lengths1[0], "After threshold, new log should appear"
                break


@pytest.mark.parametrize('threshold', [10, 20])
def test_handler_with_buffer_lines(caplog, threshold):
    logger = getLogger('Test buffer time')
    my_stream = StringIO()
    handler = StreamHandlerWithBuffer(stream=my_stream, buffer_time=0, buffer_lines=threshold)
    formatter = Formatter(fmt="[%(asctime)s.%(msecs)03d] %(levelname)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.propagate = False

    with caplog.at_level(DEBUG):
        for i in range(50):
            logger.info('This is my log line')
            if i == threshold - 2:
                my_stream.seek(0)
                logs = my_stream.read()
                assert not logs, "Right before threshold exceeding, no log should appear"
            if i == threshold - 1:
                my_stream.seek(0)
                logs = my_stream.read()
                assert logs, "Right after threshold exceeding, the log should appear"
            if i == threshold*2-1:
                my_stream.seek(0)
                logs = my_stream.read().splitlines()
                assert len(logs) == 2*threshold, "Total log lines should equal threshold * 2"
