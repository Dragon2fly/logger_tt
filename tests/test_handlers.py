import datetime
import re
import time

from io import StringIO, BytesIO
from logging import getLogger, DEBUG, Formatter

import pytest
from logger_tt.handlers import StreamHandlerWithBuffer, TelegramHandler


@pytest.mark.parametrize('threshold', [0.2, 0.4])
def test_handler_with_buffer_time(caplog, threshold):
    logger = getLogger('Test buffer time')
    my_stream = StringIO()
    handler = StreamHandlerWithBuffer(stream=my_stream, buffer_time=threshold, buffer_lines=0, debug=True)
    formatter = Formatter(fmt="[%(asctime)s.%(msecs)03d] %(levelname)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.propagate = False

    with caplog.at_level(DEBUG):
        t0 = time.time()
        dt = 0
        while dt < 2*threshold + 2*0.016:
            logger.info('This is my log message')
            time.sleep(0.01)
            dt = time.time() - t0

        my_stream.seek(0)
        logs = my_stream.read()

        time.sleep(0.2)
        data = re.findall(r'StreamHandlerWithBuffer.*\n', logs)
        start_time = datetime.datetime.strptime(data[0].strip().split(': ')[1], '%Y-%m-%d %H:%M:%S.%f')
        flush1_time = datetime.datetime.strptime(data[1].strip().split(': ')[1], '%Y-%m-%d %H:%M:%S.%f')
        flush2_time = datetime.datetime.strptime(data[2].strip().split(': ')[1], '%Y-%m-%d %H:%M:%S.%f')

        dt1 = (flush1_time - start_time).microseconds/1e6
        dt2 = (flush2_time - flush1_time).microseconds/1e6
        assert threshold < dt1 < threshold + 0.2*threshold, "It shouldn't flush too soon or too late"
        assert threshold < dt2 < threshold + 0.2*threshold, "It shouldn't flush too soon or too late"

        lines = logs.splitlines()
        msg_count = lines.index(data[2].strip()) - lines.index(data[1].strip()) - 1
        assert msg_count, "Some messages must be logged between 2 flushing"


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


@pytest.mark.skip('Uncomment this line. Add your bot token and chat_id/(group_id, topic) to test. Already tested!')
@pytest.mark.parametrize('unique_id', [123456789,
                                       (-1234567890123, 2),
                                       (-1234567890123, 4)])
def test_telegram_handler_basic(unique_id):
    bot_token = 'your bot token here'
    logger = getLogger('test telegram')
    handler = TelegramHandler(token=bot_token, unique_ids=[unique_id])
    formatter = Formatter(fmt="[%(asctime)s.%(msecs)03d] %(levelname)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.propagate = False

    try:
        logger.warning('this is my warning')
        feedback = handler.feedback[unique_id]
        assert feedback.get('ok')

        logger.error('this is my error \n this is the next line')
        feedback = handler.feedback[unique_id]
        assert feedback.get('ok')
    finally:
        logger.removeHandler(handler)


def test_telegram_handler_error(caplog):
    bot_token = ''
    user_id = 123456789
    logger = getLogger('test telegram')
    handler = TelegramHandler(token=bot_token, unique_ids=[user_id], debug=True)
    formatter = Formatter(fmt="[%(asctime)s.%(msecs)03d] %(levelname)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.propagate = False
    getLogger().setLevel(0)

    # setup stub function
    from urllib import request, error

    def fake_urlopen(*arg, **kwargs):
        if code != 200:
            raise error.HTTPError('fake_url', code=code, msg='fake_url raised error', hdrs={}, fp=None)
        else:
            my_stream = BytesIO()
            my_stream.write(b'{"ok": "true"}')
            my_stream.seek(0)
            return my_stream

    request.urlopen = fake_urlopen
    # stub done

    code = 403
    logger.warning('user blocked this bot')
    assert 'HTTP Error 403' in caplog.text
    assert not handler.cache[user_id]
    assert not handler.is_watching

    code = 500
    handler.check_interval = 0.5
    logger.error('server error')
    assert handler.cache[user_id]
    assert handler.is_watching
    code = 200
    time.sleep(1.5)
    assert not handler.cache[user_id]
    assert 'HTTP Error 500' in caplog.text
    assert 'watcher starts' in caplog.text
    assert 'found unsent messages' in caplog.text
    assert 'watcher finished' in caplog.text
