import datetime
import os
import re
import time

from io import StringIO, BytesIO
from logging import getLogger, DEBUG, Formatter
from urllib import request, error as request_error

import pytest
from logger_tt.handlers import StreamHandlerWithBuffer, TelegramHandler, parse


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

        for i in range(2):
            time.sleep(0.2)
            my_stream.seek(0)
            logs = my_stream.read()
            data = re.findall(r'StreamHandlerWithBuffer.*\n', logs)
            try:
                start_time = datetime.datetime.strptime(data[0].strip().split(': ')[1], '%Y-%m-%d %H:%M:%S.%f')
                flush1_time = datetime.datetime.strptime(data[1].strip().split(': ')[1], '%Y-%m-%d %H:%M:%S.%f')
                flush2_time = datetime.datetime.strptime(data[2].strip().split(': ')[1], '%Y-%m-%d %H:%M:%S.%f')
                break
            except IndexError:
                continue
        else:
            raise IndexError

        dt1 = (flush1_time - start_time).microseconds/1e6
        dt2 = (flush2_time - flush1_time).microseconds/1e6
        assert threshold < dt1 < threshold + 0.2*threshold, "It shouldn't flush too soon or too late"
        assert threshold < dt2 < threshold + 0.2*threshold, "It shouldn't flush too soon or too late"

        lines = logs.splitlines()
        msg_count = lines.index(data[2].strip()) - lines.index(data[1].strip()) - 1
        assert msg_count, "Some messages must be logged between 2 flushing"


@pytest.mark.parametrize('threshold', [10, 20])
def test_handler_with_buffer_lines(caplog, threshold):
    logger = getLogger('Test buffer lines')
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


@pytest.mark.skip('comment this line. Add your bot token and chat_id/(group_id, topic) to test. Already tested!')
@pytest.mark.parametrize('unique_id', ['123456789',
                                       '-1234567890123@2',
                                       '-1234567890123@2; -1234567890123@4'
                                       ])
def test_telegram_handler_basic(unique_id):
    bot_token = 'your bot token here'
    os.environ['TELEGRAM_BOT_LOG_TOKEN'] = bot_token
    os.environ['TELEGRAM_BOT_LOG_DEST'] = unique_id
    logger = getLogger('test telegram')
    handler = TelegramHandler(env_token_key='TELEGRAM_BOT_LOG_TOKEN', env_unique_ids_key='TELEGRAM_BOT_LOG_DEST')
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
        # remove handler to test a second params set
        logger.removeHandler(handler)
        handler.close()


def set_telegram_handler(log_name, bot_token='', user_id='123456789', **kwargs):
    logger = getLogger(log_name)
    handler = TelegramHandler(token=bot_token, unique_ids=user_id, debug=True, **kwargs)
    formatter = Formatter(fmt="[%(asctime)s.%(msecs)03d] %(levelname)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.propagate = False
    getLogger().setLevel(0)
    return logger, handler


def mock_urlopen(status_code, url_snipping: StringIO):
    # setup stub function

    def fake_urlopen(url: str, *arg, **kwargs):
        url_snipping.write(url + '\n\n')

        if status_code != 200:
            raise request_error.HTTPError('fake_url', code=status_code,
                                          msg='fake_url raised error', hdrs={}, fp=None)
        else:
            my_stream = BytesIO()
            my_stream.write(b'{"ok": "true"}')
            my_stream.seek(0)
            return my_stream

    request.urlopen = fake_urlopen
    # stub done


def test_telegram_handler_error(caplog):
    # setup handler
    user_id = '123456789'
    logger, handler = set_telegram_handler('test telegram 0', user_id=user_id, check_interval=0.5)

    mock_urlopen(status_code=403, url_snipping=StringIO())
    logger.warning('user blocked this bot')
    assert 'HTTP Error 403' in caplog.text
    assert not handler.message_queue[user_id]
    assert not handler.failed_messages[user_id]

    mock_urlopen(status_code=500, url_snipping=StringIO())
    logger.error('server error')
    assert not handler.message_queue[user_id]
    assert handler.failed_messages[user_id]

    mock_urlopen(status_code=200, url_snipping=StringIO())
    for retry in range(2):
        try:
            time.sleep(1.5)
            assert not handler.message_queue[user_id]
            break
        except AssertionError:
            continue
    else:
        assert not handler.message_queue[user_id]
    assert 'HTTP Error 500' in caplog.text
    assert 'found unsent messages' in caplog.text


def test_telegram_handler_repeated_msg_continuous(caplog):
    # setup handler
    logger, handler = set_telegram_handler('test telegram 1', check_interval=1)

    # setup
    log_sent = StringIO()
    mock_urlopen(status_code=200, url_snipping=log_sent)

    # run repeat the same message continuously
    for i in range(1000):
        logger.warning(f'Connection error: server 500. Retry')
    time.sleep(2)   # let watcher run

    # check result
    log_sent.seek(0)
    data = log_sent.read()
    count = data.count('Connection+error')
    assert count < 500
    res = re.findall(r'Message\+repeated\+(\d+)\+times', data)
    assert sum(int(x) for x in res) == 1000 - 1, data + '\n\n' + caplog.text


def test_telegram_handler_repeated_msg_then_change(caplog):
    # setup handler
    logger, handler = set_telegram_handler('test telegram 2', check_interval=1)

    # setup
    log_sent = StringIO()
    mock_urlopen(status_code=200, url_snipping=log_sent)

    # run repeat the same message for a while then different message
    for i in range(10):
        logger.warning(f'Connection error: server 500. Retry')
    else:
        logger.error(f'Failure. Memory overflow')
    time.sleep(2)   # let watcher run

    # check result, watcher should have nothing to do
    log_sent.seek(0)
    data = log_sent.read()
    count = data.count('Connection+error')
    assert 1 < count < 6, data + '\n\n' + caplog.text
    res = re.findall(r'Message\+repeated\+(\d+)\+times', data)
    assert 'Message+repeated+9+times' in data
    assert sum(int(x) for x in res) == 10 - len(res), data + '\n\n' + caplog.text
    assert 'Memory+overflow' in data
    assert 'watcher emit duplicated' not in caplog.text


def test_telegram_handler_grouping_msg_normal(caplog):
    # setup handler
    logger, handler = set_telegram_handler('test telegram 3', check_interval=10, grouping_interval=1)

    # setup
    log_sent = StringIO()
    mock_urlopen(status_code=200, url_snipping=log_sent)

    # run repeat the same message for a while then different message
    for i in range(10):
        # first group
        logger.warning(f'Connection error: server 500. Retry {i+1} time')
    else:
        # second group
        time.sleep(1)
        logger.error(f'Failure. Memory overflow')

        # third group
        time.sleep(1)
        logger.error(f'Failure. Hard disk is at capacity')
        
    time.sleep(4)   # let watcher run

    log_sent.seek(0)
    data = log_sent.read()
    count = data.count('https')
    assert count == 3, 'There should be 3 groups of http request'


def test_telegram_handler_grouping_msg_resend(caplog):
    # setup handler
    logger, handler = set_telegram_handler('test telegram 4', check_interval=10, grouping_interval=1)

    # setup
    log_sent = StringIO()
    mock_urlopen(status_code=200, url_snipping=log_sent)

    # run repeat the same message for a while then different message
    for i in range(100):
        logger.warning(f'Connection error: server 500. Retry {i} time')

    # first sent
    time.sleep(6)  # let watcher run

    # second sent
    time.sleep(6)  # let watcher run

    log_sent.seek(0)
    data = log_sent.read()
    count = data.count('%0A')
    assert count == 98, 'Grouped message should not be regrouped again'
    assert data.count('https:') > 1, 'long message should be divided'
