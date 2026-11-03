import json
from decimal import Decimal
from uuid import UUID

import pytest

from src.logs.events.schema import (
    PAYLOAD_MAX_BYTES,
    PAYLOAD_STR_MAX,
    REDACTED_VALUE,
    normalize_payload,
    without_url_secrets,
)
from src.logs.events.tests.fixtures import EVENT_TS
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_group,
    create_test_owner,
)
from src.utils.logging import SentryLogLevel


def test_normalize_payload__none__empty_dict():

    # arrange
    payload = None

    # act
    result = normalize_payload(payload=payload)

    # assert
    assert result == {}


def test_normalize_payload__empty_dict__empty_dict():

    # arrange
    payload = {}

    # act
    result = normalize_payload(payload=payload)

    # assert
    assert result == {}


# One spelling per entry of the secret lists plus the shapes a header
# or a camelCase serializer produces.
@pytest.mark.parametrize(
    'key',
    (
        'password',
        'user_password',
        'passwd',
        'pwd',
        'token',
        'access_token',
        'api_key',
        'api-key',
        'apiKey',
        'X-API-Key',
        'secret',
        'client_secret',
        'Authorization',
        'credentials',
        'private_key',
        'Cookie',
        'session_id',
        'signature',
        'password_salt',
        'bearer',
        'jwt',
        'otp_code',
        'refresh_token',
        'access',
        'refresh',
        'session',
        'private',
        'OTP',
    ),
)
def test_normalize_payload__secret_key__value_redacted(key):

    # arrange
    payload = {key: 'super-secret-value'}

    # act
    result = normalize_payload(payload=payload)

    # assert
    assert result == {key: REDACTED_VALUE}


@pytest.mark.parametrize(
    'key',
    (
        'is_private',
        'session_count',
        'refresh_interval',
        'saltwater',
    ),
)
def test_normalize_payload__lookalike_key__value_kept(key):
    """A secret word inside a longer name is not a secret: a flag
    named is_private and a counter of sessions reach the journal
    as they are."""

    # arrange
    payload = {key: 'plain-value'}

    # act
    result = normalize_payload(payload=payload)

    # assert
    assert result == {key: 'plain-value'}


def test_normalize_payload__harmless_keys__kept():

    # arrange
    payload = {'name': 'Ann', 'template_id': 12, 'with_attachments': True}

    # act
    result = normalize_payload(payload=payload)

    # assert
    assert result == {
        'name': 'Ann',
        'template_id': 12,
        'with_attachments': True,
    }


def test_normalize_payload__secret_in_a_nested_dict__value_redacted():

    # arrange
    payload = {
        'auth': {'headers': {'token': 'super-secret-value', 'id': 1}},
    }

    # act
    result = normalize_payload(payload=payload)

    # assert
    assert result == {
        'auth': {'headers': '{"token": "[redacted]", "id": 1}'},
    }


def test_normalize_payload__url_with_query__query_dropped():
    """An access token or a signature rides in the query string."""

    # arrange
    payload = {'url': 'https://api.test/v1/hook?access_token=abc&x=1'}

    # act
    result = normalize_payload(payload=payload)

    # assert
    assert result == {'url': 'https://api.test/v1/hook'}


def test_normalize_payload__url_with_fragment__fragment_kept():

    # arrange
    payload = {'url': 'https://api.test/v1?token=abc#part'}

    # act
    result = normalize_payload(payload=payload)

    # assert
    assert result == {'url': 'https://api.test/v1#part'}


def test_normalize_payload__url_with_userinfo__credential_dropped():
    """A password rides in the authority of a webhook url as often
    as a token rides in its query."""

    # arrange
    payload = {'url': 'https://user:pass@hooks.test/hook'}

    # act
    result = normalize_payload(payload=payload)

    # assert
    assert result == {'url': 'https://hooks.test/hook'}


def test_normalize_payload__url_with_userinfo_and_port__port_kept():

    # arrange
    payload = {'url': 'https://user:pass@hooks.test:8443/hook'}

    # act
    result = normalize_payload(payload=payload)

    # assert
    assert result == {'url': 'https://hooks.test:8443/hook'}


def test_normalize_payload__url_with_userinfo_and_query__both_dropped():

    # arrange
    payload = {'url': 'https://user:pass@hooks.test/hook?token=abc'}

    # act
    result = normalize_payload(payload=payload)

    # assert
    assert result == {'url': 'https://hooks.test/hook'}


def test_normalize_payload__url_without_userinfo__kept_as_is():

    # arrange
    payload = {'url': 'https://hooks.test:8443/hook'}

    # act
    result = normalize_payload(payload=payload)

    # assert
    assert result == {'url': 'https://hooks.test:8443/hook'}


def test_normalize_payload__at_sign_in_url_path__kept_as_is():

    # arrange
    payload = {'url': 'https://blog.test/@ann'}

    # act
    result = normalize_payload(payload=payload)

    # assert
    assert result == {'url': 'https://blog.test/@ann'}


def test_normalize_payload__email_address__kept_as_is():
    """An address is not a url: its at sign is no credential."""

    # arrange
    payload = {'email': 'ann@test.test'}

    # act
    result = normalize_payload(payload=payload)

    # assert
    assert result == {'email': 'ann@test.test'}


def test_normalize_payload__question_mark_in_plain_text__kept():

    # arrange
    payload = {'name': 'Is it done?'}

    # act
    result = normalize_payload(payload=payload)

    # assert
    assert result == {'name': 'Is it done?'}


def test_normalize_payload__unparsable_url__kept_as_is():
    """urlsplit raises for a broken IPv6 host: a value that cannot be
    parsed is left alone instead of breaking the whole event."""

    # arrange
    payload = {'url': 'http://[oops?token=abc'}

    # act
    result = normalize_payload(payload=payload)

    # assert
    assert result == {'url': 'http://[oops?token=abc'}


def test_normalize_payload__secret_in_a_too_deep_url__query_dropped():

    # arrange
    payload = {'a': {'b': {'url': 'https://api.test/v1?token=abc'}}}

    # act
    result = normalize_payload(payload=payload)

    # assert
    assert result == {'a': {'b': '{"url": "https://api.test/v1"}'}}


def test_normalize_payload__django_types__serialized():

    # arrange
    key = UUID('12345678-1234-5678-1234-567812345678')
    payload = {
        'created': EVENT_TS,
        'amount': Decimal('10.50'),
        'key': key,
        'items': [EVENT_TS, Decimal('1.10')],
    }

    # act
    result = normalize_payload(payload=payload)

    # assert
    assert result == {
        'created': '2026-09-08T10:15:30.123Z',
        'amount': '10.50',
        'key': '12345678-1234-5678-1234-567812345678',
        'items': ['2026-09-08T10:15:30.123Z', '1.10'],
    }


def test_normalize_payload__long_string__trimmed():

    # arrange
    payload = {'name': 'x' * (PAYLOAD_STR_MAX + 100)}

    # act
    result = normalize_payload(payload=payload)

    # assert
    assert result == {'name': 'x' * PAYLOAD_STR_MAX}


def test_normalize_payload__too_deep_value__json_string():

    # arrange
    payload = {'a': {'b': {'c': 1}}, 'list': [[1, 2]]}

    # act
    result = normalize_payload(payload=payload)

    # assert
    assert result == {'a': {'b': '{"c": 1}'}, 'list': ['[1, 2]']}


def test_normalize_payload__unknown_type__string():
    """A range is neither a JSON type nor one of the Django ones the
    encoder knows: it is stored as its text."""

    # arrange
    payload = {'obj': range(3)}

    # act
    result = normalize_payload(payload=payload)

    # assert
    assert result == {'obj': 'range(0, 3)'}


def test_normalize_payload__unencodable_value_too_deep__string():
    """A value the encoder cannot handle becomes its text, so one
    odd value never breaks the whole batch of the sink. The
    container around it keeps its shape: the collapsed string is
    built from the normalized value, not from the raw one."""

    # arrange
    payload = {'a': {'b': {'obj': range(3)}}}

    # act
    result = normalize_payload(payload=payload)

    # assert
    assert result == {'a': {'b': '{"obj": "range(0, 3)"}'}}


def test_normalize_payload__nesting_below_the_limit__collapsed_whole():
    """The subtree of a collapsed container goes into that one
    string however deep it is: the collapse is where the depth
    limit stops mattering."""

    # arrange
    payload = {'a': {'b': {'c': {'d': 1}}}, 'list': {'x': [[1, 2]]}}

    # act
    result = normalize_payload(payload=payload)

    # assert
    assert result == {
        'a': {'b': '{"c": {"d": 1}}'},
        'list': {'x': '[[1, 2]]'},
    }


def test_normalize_payload__secret_below_the_limit__value_redacted():
    """Depth is no way past the redaction: the keys of the whole
    collapsed subtree are checked, not only its first level."""

    # arrange
    payload = {'a': {'b': {'auth': {'token': 'secret-value'}}}}

    # act
    result = normalize_payload(payload=payload)

    # assert
    assert result == {'a': {'b': '{"auth": {"token": "[redacted]"}}'}}


def test_normalize_payload__too_deep_long_string__string_cut():
    """A long string inside a collapsed container is cut before
    the container is dumped, so the attribute stays valid
    JSON instead of ending mid-escape."""

    # arrange
    payload = {'a': {'b': {'text': 'y' * (PAYLOAD_STR_MAX + 100)}}}

    # act
    result = normalize_payload(payload=payload)

    # assert
    assert json.loads(result['a']['b']) == {
        'text': 'y' * PAYLOAD_STR_MAX,
    }


def test_normalize_payload__oversized__replaced_by_size_marker(mocker):
    """A single event must not be able to fill up the stream: the
    payload is replaced by its size marker, and the loss of an
    audit payload is reported (throttled, a loop of events would
    flood Sentry). 70 keys of 1000 bytes plus the JSON syntax
    make 70970 bytes."""

    # arrange
    payload = {f'key_{num}': 'x' * 1000 for num in range(70)}
    capture_sentry_mock = mocker.patch(
        'src.logs.events.schema.capture_sentry_message_throttled',
    )

    # act
    result = normalize_payload(payload=payload)

    # assert
    assert result == {'_truncated': True, '_size': 70970}
    capture_sentry_mock.assert_called_once_with(
        message='Event payload dropped: over the size limit',
        data={'size': 70970, 'limit': PAYLOAD_MAX_BYTES},
        level=SentryLogLevel.WARNING,
    )


def test_normalize_payload__whole_template_size__kept(mocker):
    """A whole template goes into the record of its save: 40 keys of
    1000 bytes, 40550 bytes with the JSON syntax, are well below
    the limit of 64 KiB."""

    # arrange
    payload = {f'key_{num}': 'x' * 1000 for num in range(40)}
    capture_sentry_mock = mocker.patch(
        'src.logs.events.schema.capture_sentry_message_throttled',
    )

    # act
    result = normalize_payload(payload=payload)

    # assert
    assert result == payload
    capture_sentry_mock.assert_not_called()


def test_normalize_payload__at_the_size_limit__kept(mocker):
    """The limit is the largest payload that is still stored whole:
    the marker replaces only a bigger one. 32 keys of 2000 bytes
    make 64448 bytes with the JSON syntax, the pad key of 1077
    bytes brings the total to exactly PAYLOAD_MAX_BYTES."""

    # arrange
    payload = {f'key_{num:02d}': 'x' * 2000 for num in range(32)}
    payload['pad'] = 'y' * 1077
    capture_sentry_mock = mocker.patch(
        'src.logs.events.schema.capture_sentry_message_throttled',
    )

    # act
    result = normalize_payload(payload=payload)

    # assert
    assert result == payload
    assert result is not payload
    capture_sentry_mock.assert_not_called()


def test_normalize_payload__one_byte_over_the_limit__size_marker(mocker):

    # arrange
    payload = {f'key_{num:02d}': 'x' * 2000 for num in range(32)}
    payload['pad'] = 'y' * 1078
    capture_sentry_mock = mocker.patch(
        'src.logs.events.schema.capture_sentry_message_throttled',
    )

    # act
    result = normalize_payload(payload=payload)

    # assert
    assert result == {'_truncated': True, '_size': 65537}
    capture_sentry_mock.assert_called_once_with(
        message='Event payload dropped: over the size limit',
        data={'size': 65537, 'limit': PAYLOAD_MAX_BYTES},
        level=SentryLogLevel.WARNING,
    )


def test_normalize_payload__oversized_list__top_level_scalars_kept(
    mocker,
):
    """The tasks of a template make its payload big, while the
    dashboards filter the events by its name and is_active: the
    scalars of the top level stay next to the size marker, the
    list goes. 40 tasks of 2000 bytes make 80265 bytes."""

    # arrange
    payload = {
        'name': 'Onboarding',
        'is_active': True,
        'tasks_count': 40,
        'rate': 0.5,
        'description': None,
        'tasks': ['x' * 2000 for _ in range(40)],
    }
    capture_sentry_mock = mocker.patch(
        'src.logs.events.schema.capture_sentry_message_throttled',
    )

    # act
    result = normalize_payload(payload=payload)

    # assert
    assert result == {
        'name': 'Onboarding',
        'is_active': True,
        'tasks_count': 40,
        'rate': 0.5,
        'description': None,
        '_truncated': True,
        '_size': 80265,
    }
    capture_sentry_mock.assert_called_once_with(
        message='Event payload dropped: over the size limit',
        data={'size': 80265, 'limit': PAYLOAD_MAX_BYTES},
        level=SentryLogLevel.WARNING,
    )


def test_normalize_payload__oversized_dict__top_level_scalars_kept(
    mocker,
):
    """A dict of the top level goes the same way as a list. 40 fields
    of 2000 bytes make 80675 bytes."""

    # arrange
    payload = {
        'name': 'Onboarding',
        'kickoff': {f'field_{num:02d}': 'x' * 2000 for num in range(40)},
    }
    capture_sentry_mock = mocker.patch(
        'src.logs.events.schema.capture_sentry_message_throttled',
    )

    # act
    result = normalize_payload(payload=payload)

    # assert
    assert result == {
        'name': 'Onboarding',
        '_truncated': True,
        '_size': 80675,
    }
    capture_sentry_mock.assert_called_once_with(
        message='Event payload dropped: over the size limit',
        data={'size': 80675, 'limit': PAYLOAD_MAX_BYTES},
        level=SentryLogLevel.WARNING,
    )


def test_normalize_payload__oversized_scalars_and_list__marker_only(
    mocker,
):
    """The scalars of the top level are over the limit on their own:
    keeping them would not bound the event, so only the marker is
    left. 33 strings of 2000 bytes and a list make 67477 bytes."""

    # arrange
    payload = {f'key_{num:02d}': 'x' * 2000 for num in range(33)}
    payload['tasks'] = ['y' * 1000]
    capture_sentry_mock = mocker.patch(
        'src.logs.events.schema.capture_sentry_message_throttled',
    )

    # act
    result = normalize_payload(payload=payload)

    # assert
    assert result == {'_truncated': True, '_size': 67477}
    capture_sentry_mock.assert_called_once_with(
        message='Event payload dropped: over the size limit',
        data={'size': 67477, 'limit': PAYLOAD_MAX_BYTES},
        level=SentryLogLevel.WARNING,
    )


@pytest.mark.django_db
def test_normalize_payload__model_instance__primary_key():
    """The kwargs of an update carry the manager of a user as a row
    of the database: the journal gets its id, not its text."""

    # arrange
    manager = create_test_owner()
    payload = {'manager': manager}

    # act
    result = normalize_payload(payload=payload)

    # assert
    assert result == {'manager': {'id': manager.id, 'name': str(manager)}}


@pytest.mark.django_db
def test_normalize_payload__list_of_model_instances__primary_keys():

    # arrange
    account = create_test_account()
    first_group = create_test_group(
        account=account,
        name='Sales',
    )
    second_group = create_test_group(
        account=account,
        name='Support',
    )
    payload = {'user_groups': [first_group, second_group]}

    # act
    result = normalize_payload(payload=payload)

    # assert
    assert result == {
        'user_groups': [
            {'id': first_group.id, 'name': 'Sales'},
            {'id': second_group.id, 'name': 'Support'},
        ],
    }


@pytest.mark.django_db
def test_normalize_payload__model_instance_too_deep__id_in_the_string():

    # arrange
    manager = create_test_owner()
    payload = {'a': {'b': {'manager': manager}}}

    # act
    result = normalize_payload(payload=payload)

    # assert
    assert json.loads(result['a']['b']) == {
        'manager': {'id': manager.id, 'name': str(manager)},
    }


def test_without_url_secrets__relative_url__kept_as_it_is():
    """Only an absolute url is a url: a path with a query string is
    a plain string to the normalizer, and a caller that puts a
    token there has to cut it itself."""

    # arrange
    value = '/hook?token=x'

    # act
    result = without_url_secrets(value=value)

    # assert
    assert result == '/hook?token=x'
