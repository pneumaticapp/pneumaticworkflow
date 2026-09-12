"""Tests for the records of one request."""

import io
from datetime import UTC, datetime
from unittest.mock import AsyncMock, Mock

import pytest

from src.application.dto import UploadFileCommand
from src.domain.entities import FileRecord
from src.shared_kernel.events.request_events import (
    RequestEvents,
    get_request_events,
)
from src.shared_kernel.events.schema import (
    PAYLOAD_STR_MAX,
    SERVICE_NAME,
    Actor,
    ActorType,
    Event,
    EventName,
    RequestContext,
)
from src.shared_kernel.http_context import FALLBACK_IP
from tests.fixtures.unit import CONTRACT_FILE_ID as FILE_ID


@pytest.mark.asyncio
async def test_file_upload__long_filename__payload_string_cut(
    request_events,
    capturing_emitter,
    actor_user,
):
    """The name reaches the record from the request and is unbounded
    there, so the payload has to bound it the way the backend does."""

    # arrange
    command = Mock(
        filename='y' * (PAYLOAD_STR_MAX + 100),
        content_type='text/plain',
        size=3,
    )

    # act
    await request_events.file_upload(
        user=actor_user,
        file_id=FILE_ID,
        file=command,
    )

    # assert
    payload = capturing_emitter.events[0].payload
    assert payload['filename'] == 'y' * PAYLOAD_STR_MAX


async def test_file_download__owner__record_matches_backend_contract(
    request_events,
    capturing_emitter,
    actor_user,
    mock_request_events_now,
    backend_contract_record,
):
    # arrange
    file_record = FileRecord(
        file_id=FILE_ID,
        filename='Contract Ann Smith.pdf',
        content_type='application/pdf',
        size=12345,
        user_id=17,
        account_id=42,
        created_at=datetime(2026, 9, 9, tzinfo=UTC),
    )

    # act
    await request_events.file_download(
        user=actor_user,
        file_record=file_record,
        is_owner=True,
    )

    # assert
    assert len(capturing_emitter.events) == 1
    assert capturing_emitter.events[0].to_dict() == backend_contract_record
    mock_request_events_now.assert_called_once_with()


@pytest.mark.asyncio
async def test_file_download__non_owner__is_owner_false(
    request_events,
    capturing_emitter,
    actor_user,
    mock_request_events_now,
):
    # arrange
    file_record = FileRecord(
        file_id=FILE_ID,
        filename='report.pdf',
        content_type='application/pdf',
        size=10,
        user_id=99,
        account_id=42,
        created_at=datetime(2026, 9, 9, tzinfo=UTC),
    )

    # act
    await request_events.file_download(
        user=actor_user,
        file_record=file_record,
        is_owner=False,
    )

    # assert
    assert capturing_emitter.events[0].payload == {
        'filename': 'report.pdf',
        'size': 10,
        'content_type': 'application/pdf',
        'is_owner': False,
    }
    mock_request_events_now.assert_called_once_with()


@pytest.mark.asyncio
async def test_file_upload__command__upload_record(
    request_events,
    capturing_emitter,
    sample_context,
    actor_user,
    mock_request_events_now,
):
    # arrange
    command = UploadFileCommand(
        file_stream=io.BytesIO(b'abc'),
        filename='notes.txt',
        content_type='text/plain',
        size=3,
        user_id=17,
        account_id=42,
    )

    # act
    await request_events.file_upload(
        user=actor_user,
        file_id=FILE_ID,
        file=command,
    )

    # assert
    assert capturing_emitter.events == [
        Event(
            type=EventName.FILE_UPLOAD,
            service=SERVICE_NAME,
            ts=datetime(2026, 9, 9, 12, 0, 0, 123, tzinfo=UTC),
            account_id=42,
            actor=Actor(type=ActorType.USER, id=17),
            file_id=FILE_ID,
            context=sample_context,
            payload={
                'filename': 'notes.txt',
                'size': 3,
                'content_type': 'text/plain',
            },
        ),
    ]
    mock_request_events_now.assert_called_once_with()


@pytest.mark.asyncio
async def test_file_upload__api_key__actor_api_key(
    request_events,
    capturing_emitter,
    mock_request_events_now,
):
    # arrange
    user = Mock(user_id=17, account_id=42, actor_type=ActorType.API_KEY)
    command = UploadFileCommand(
        file_stream=io.BytesIO(b''),
        filename='a.txt',
        content_type='text/plain',
        size=0,
        user_id=17,
        account_id=42,
    )

    # act
    await request_events.file_upload(
        user=user,
        file_id=FILE_ID,
        file=command,
    )

    # assert
    assert capturing_emitter.events[0].actor == Actor(
        type=ActorType.API_KEY,
        id=17,
    )
    mock_request_events_now.assert_called_once_with()


@pytest.mark.asyncio
async def test_file_upload__public_token__guest_without_user(
    request_events,
    capturing_emitter,
    mock_request_events_now,
):
    # arrange
    user = Mock(user_id=None, account_id=42, actor_type=ActorType.GUEST)
    command = UploadFileCommand(
        file_stream=io.BytesIO(b''),
        filename='a.txt',
        content_type='text/plain',
        size=0,
        user_id=None,
        account_id=42,
    )

    # act
    await request_events.file_upload(
        user=user,
        file_id=FILE_ID,
        file=command,
    )

    # assert
    assert capturing_emitter.events[0].actor == Actor(
        type=ActorType.GUEST,
        id=None,
    )
    assert capturing_emitter.events[0].account_id == 42
    mock_request_events_now.assert_called_once_with()


@pytest.mark.asyncio
async def test_file_access_denied__same_account__file_account_absent(
    request_events,
    capturing_emitter,
    actor_user,
    mock_request_events_now,
):
    # arrange
    file_record = FileRecord(
        file_id=FILE_ID,
        filename='report.pdf',
        content_type='application/pdf',
        size=10,
        user_id=99,
        account_id=42,
        created_at=datetime(2026, 9, 9, tzinfo=UTC),
    )

    # act
    await request_events.file_access_denied(
        user=actor_user,
        file_record=file_record,
    )

    # assert
    assert capturing_emitter.events[0].type == EventName.FILE_ACCESS_DENIED
    assert capturing_emitter.events[0].account_id == 42
    assert capturing_emitter.events[0].payload == {
        'filename': 'report.pdf',
        'size': 10,
        'content_type': 'application/pdf',
    }
    mock_request_events_now.assert_called_once_with()


@pytest.mark.asyncio
async def test_file_access_denied__foreign_account__file_account_in_payload(
    request_events,
    capturing_emitter,
    actor_user,
    mock_request_events_now,
):
    # arrange
    file_record = FileRecord(
        file_id=FILE_ID,
        filename='report.pdf',
        content_type='application/pdf',
        size=10,
        user_id=99,
        account_id=77,
        created_at=datetime(2026, 9, 9, tzinfo=UTC),
    )

    # act
    await request_events.file_access_denied(
        user=actor_user,
        file_record=file_record,
    )

    # assert
    assert capturing_emitter.events[0].account_id == 42
    assert capturing_emitter.events[0].payload['file_account_id'] == 77
    mock_request_events_now.assert_called_once_with()


@pytest.mark.asyncio
async def test_get_request_events__request__process_emitter(
    mocker,
    make_context_request,
    actor_user,
    mock_request_events_now,
):
    # arrange
    emitter_mock = AsyncMock()
    get_event_emitter_mock = mocker.patch(
        'src.shared_kernel.events.request_events.get_event_emitter',
        return_value=emitter_mock,
    )
    request = make_context_request(
        headers={'x-real-ip': '203.0.113.7', 'user-agent': 'Mozilla/5.0'},
        request_id='req-1',
    )
    command = UploadFileCommand(
        file_stream=io.BytesIO(b''),
        filename='a.txt',
        content_type='text/plain',
        size=0,
        user_id=17,
        account_id=42,
    )

    # act
    events = await get_request_events(request)
    await events.file_upload(user=actor_user, file_id=FILE_ID, file=command)

    # assert
    assert isinstance(events, RequestEvents)
    get_event_emitter_mock.assert_called_once_with()
    emitter_mock.emit.assert_awaited_once_with(
        Event(
            type=EventName.FILE_UPLOAD,
            service=SERVICE_NAME,
            ts=datetime(2026, 9, 9, 12, 0, 0, 123, tzinfo=UTC),
            account_id=42,
            actor=Actor(type=ActorType.USER, id=17),
            file_id=FILE_ID,
            context=RequestContext(
                ip='203.0.113.7',
                user_agent='Mozilla/5.0',
                request_id='req-1',
            ),
            payload={
                'filename': 'a.txt',
                'size': 0,
                'content_type': 'text/plain',
            },
        ),
    )
    mock_request_events_now.assert_called_once_with()


async def test_get_request_events__headers__context_from_the_request(
    mocker,
    make_context_request,
):
    """The dependency is where a request becomes the context of a
    record: address, browser and correlation id come from it."""

    # arrange
    emitter_mock = AsyncMock()
    mocker.patch(
        'src.shared_kernel.events.request_events.get_event_emitter',
        return_value=emitter_mock,
    )
    request = make_context_request(
        headers={'x-real-ip': '203.0.113.7', 'user-agent': 'Mozilla/5.0'},
        request_id='req-1',
    )

    # act
    events = await get_request_events(request)

    # assert
    assert events._context == RequestContext(
        ip='203.0.113.7',
        user_agent='Mozilla/5.0',
        request_id='req-1',
    )


async def test_get_request_events__no_user_agent__none_in_the_context(
    mocker,
    make_context_request,
):
    # arrange
    emitter_mock = AsyncMock()
    mocker.patch(
        'src.shared_kernel.events.request_events.get_event_emitter',
        return_value=emitter_mock,
    )
    request = make_context_request(
        headers={'x-real-ip': '203.0.113.7'},
        request_id='req-1',
    )

    # act
    events = await get_request_events(request)

    # assert
    assert events._context.user_agent is None
    assert events._context.ip == '203.0.113.7'


async def test_get_request_events__no_client__fallback_address(
    mocker,
    make_context_request,
):
    """No header and no socket: the record still carries an address."""

    # arrange
    emitter_mock = AsyncMock()
    mocker.patch(
        'src.shared_kernel.events.request_events.get_event_emitter',
        return_value=emitter_mock,
    )
    request = make_context_request(has_client=False, request_id='req-1')

    # act
    events = await get_request_events(request)

    # assert
    assert events._context.ip == FALLBACK_IP
