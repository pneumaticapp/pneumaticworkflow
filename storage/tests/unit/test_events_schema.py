"""Tests for the records of the audit journal."""

from dataclasses import replace
from datetime import UTC, datetime, timedelta, timezone

from src.shared_kernel.auth.user_types import (
    JournalAuthType,
    JournalUserType,
)
from src.shared_kernel.events.schema import (
    STREAM_KEY,
    Actor,
    format_ts,
)


def test_format_ts__utc_moment__rfc3339_with_microseconds():
    # arrange
    moment = datetime(2026, 9, 9, 12, 0, 0, 123, tzinfo=UTC)

    # act
    result = format_ts(moment)

    # assert
    assert result == '2026-09-09T12:00:00.000123Z'


def test_format_ts__naive_moment__treated_as_utc():
    # arrange
    moment = datetime(2026, 9, 9, 12, 0, 0, 123)

    # act
    result = format_ts(moment)

    # assert
    assert result == '2026-09-09T12:00:00.000123Z'


def test_format_ts__non_utc_moment__converted_to_utc():
    # arrange
    moment = datetime(
        2026,
        9,
        9,
        15,
        0,
        0,
        123,
        tzinfo=timezone(timedelta(hours=3)),
    )

    # act
    result = format_ts(moment)

    # assert
    assert result == '2026-09-09T12:00:00.000123Z'


def test_to_dict__download_record__matches_backend_contract(
    sample_event,
    backend_contract_record,
):
    # act
    result = sample_event.to_dict()

    # assert
    assert result == backend_contract_record


def test_to_dict__upload_record__matches_backend_contract(
    sample_upload_event,
    backend_upload_contract_record,
):
    # act
    result = sample_upload_event.to_dict()

    # assert
    assert result == backend_upload_contract_record


def test_to_dict__denied_record__matches_backend_contract(
    sample_denied_event,
    backend_denied_contract_record,
):
    """A refusal names the account of the file when it is foreign."""

    # act
    result = sample_denied_event.to_dict()

    # assert
    assert result == backend_denied_contract_record


def test_to_dict__no_actor__actor_null(sample_event):
    """A shared form acts for the account, not for a person."""

    # arrange
    event = replace(
        sample_event,
        actor=None,
        auth_type=JournalAuthType.SHARED.value,
    )

    # act
    result = event.to_dict()

    # assert
    assert result['actor'] is None
    assert result['auth_type'] == 'Shared'


def test_to_dict__any_record__auth_type_after_actor(sample_event):
    """The key order is the one of the backend writer."""

    # act
    result = sample_event.to_dict()

    # assert
    assert list(result)[5:7] == ['actor', 'auth_type']
    assert 'pii' not in result


def test_to_dict__payload__copied_not_shared(sample_event):
    # act
    result = sample_event.to_dict()
    result['payload']['filename'] = 'changed'

    # assert
    assert sample_event.payload['filename'] == 'Contract Ann Smith.pdf'


def test_actor_to_dict__any_actor__email_never_known():
    # arrange
    actor = Actor(id=17, user_type=JournalUserType.USER)

    # act
    result = actor.to_dict()

    # assert
    assert result == {'id': 17, 'email': None, 'user_type': 'user'}


def test_actor_to_dict__guest_token__guest():
    # arrange
    actor = Actor(id=17, user_type=JournalUserType.GUEST)

    # act
    result = actor.to_dict()

    # assert
    assert result == {'id': 17, 'email': None, 'user_type': 'guest'}


def test_stream_key__backend_contract__same_stream(backend_service_contract):
    """A rename here would write records the backend never reads."""

    # act
    result = STREAM_KEY

    # assert
    assert result == backend_service_contract['stream_key']


def test_user_type__backend_contract__same_values(backend_service_contract):
    """A user type the backend does not declare must not reach the
    stream."""

    # act
    result = sorted(member.value for member in JournalUserType)

    # assert
    assert result == sorted(backend_service_contract['user_types'])


def test_auth_type__backend_contract__same_values(backend_service_contract):
    """An auth type the backend does not declare must not reach the
    stream."""

    # act
    result = sorted(member.value for member in JournalAuthType)

    # assert
    assert result == sorted(backend_service_contract['auth_types'])
