from src.logs.events.stream import (
    consumer_name,
    get_stream,
)


def test_get_stream__settings__configured_client(settings):

    # arrange
    settings.LOGS_REDIS_URL = 'redis://localhost:6379/4'
    settings.LOGS_STREAM_KEY = 'pneumatic:events-unit'
    settings.LOGS_CONSUMER_GROUP = 'otlp'
    settings.LOGS_STREAM_MAXLEN = 10

    # act
    stream = get_stream()

    # assert
    assert stream.url == 'redis://localhost:6379/4'
    assert stream.key == 'pneumatic:events-unit'
    assert stream.group == 'otlp'
    assert stream.maxlen == 10
    assert stream.dead_key == 'pneumatic:events-unit:dead'


def test_get_stream__called_twice__same_client(settings):

    """ One connection pool per process: a client rebuilt on every
        emit would open a new connection for every request. """

    # arrange
    settings.LOGS_REDIS_URL = 'redis://localhost:6379/4'
    settings.LOGS_STREAM_KEY = 'pneumatic:events-unit'
    settings.LOGS_CONSUMER_GROUP = 'otlp'
    settings.LOGS_STREAM_MAXLEN = 10
    first = get_stream()

    # act
    second = get_stream()

    # assert
    assert second is first


def test_get_stream__changed_settings__new_client(settings):

    # arrange
    settings.LOGS_REDIS_URL = 'redis://localhost:6379/4'
    settings.LOGS_STREAM_KEY = 'pneumatic:events-unit'
    settings.LOGS_CONSUMER_GROUP = 'otlp'
    settings.LOGS_STREAM_MAXLEN = 10
    first = get_stream()
    settings.LOGS_REDIS_URL = 'redis://localhost:6379/5'

    # act
    second = get_stream()

    # assert
    assert second is not first
    assert second.url == 'redis://localhost:6379/5'


def test_consumer_name__process__host_name_only(mocker):

    """ One name per host, not per process: the next tick may run in
        another worker process and takes over the pending list of the
        previous one right away. """

    # arrange
    gethostname_mock = mocker.patch(
        'src.logs.events.stream.socket.gethostname',
        return_value='worker-1',
    )

    # act
    name = consumer_name()

    # assert
    assert name == 'worker-1'
    gethostname_mock.assert_called_once_with()
