from src.logs.events.stream import get_stream


def test_get_stream__settings__configured_client(settings):
    """The key and the group are constants of the code: the file
    service writes into the same key. The length comes from the
    settings, which read it from .env as a number."""

    # arrange
    settings.LOGS_REDIS_URL = 'redis://localhost:6379/4'
    settings.LOGS_STREAM_MAXLEN = 10

    # act
    stream = get_stream()

    # assert
    assert stream.url == 'redis://localhost:6379/4'
    assert stream.key == 'pneumatic:events'
    assert stream.group == 'otlp'
    assert stream.maxlen == 10


def test_get_stream__called_twice__same_client(settings):
    """One connection pool per process: a client rebuilt on every
    emit would open a new connection for every request."""

    # arrange
    settings.LOGS_REDIS_URL = 'redis://localhost:6379/4'
    settings.LOGS_STREAM_MAXLEN = 10
    first = get_stream()

    # act
    second = get_stream()

    # assert
    assert second is first


def test_get_stream__changed_settings__new_client(settings):

    # arrange
    settings.LOGS_REDIS_URL = 'redis://localhost:6379/4'
    settings.LOGS_STREAM_MAXLEN = 10
    first = get_stream()
    settings.LOGS_REDIS_URL = 'redis://localhost:6379/5'

    # act
    second = get_stream()

    # assert
    assert second is not first
    assert second.url == 'redis://localhost:6379/5'


def test_get_stream__changed_maxlen__new_client(settings):

    # arrange
    settings.LOGS_REDIS_URL = 'redis://localhost:6379/4'
    settings.LOGS_STREAM_MAXLEN = 10
    first = get_stream()
    settings.LOGS_STREAM_MAXLEN = 20

    # act
    second = get_stream()

    # assert
    assert second is not first
    assert second.maxlen == 20
