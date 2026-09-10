"""Records of one request: built here, written by the emitter."""

from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import Depends, Request

from src.shared_kernel.config import get_settings
from src.shared_kernel.events.context import get_request_context
from src.shared_kernel.events.emitter import EventEmitter, get_event_emitter
from src.shared_kernel.events.schema import (
    Actor,
    ActorSource,
    Event,
    EventName,
    FileFields,
    RequestContext,
    StoredFile,
)


def _now() -> datetime:
    # Module-level clock: the tests patch it instead of datetime.now.
    return datetime.now(UTC)


def _file_payload(file: FileFields) -> dict[str, Any]:
    """Build what every file record says about the file.

    The content is never in it, nor the bucket or the path in S3.
    """
    return {
        'filename': file.filename,
        'size': file.size,
        'content_type': file.content_type,
    }


class RequestEvents:
    """The three records an endpoint of the file service may write."""

    def __init__(
        self,
        *,
        emitter: EventEmitter,
        context: RequestContext,
        service: str,
    ) -> None:
        """Bind the records of one request.

        Args:
            emitter: Writer of the stream.
            context: HTTP context of the request.
            service: Name this service signs its records with.

        """
        self._emitter = emitter
        self._context = context
        self._service = service

    async def file_upload(
        self,
        *,
        user: ActorSource,
        file_id: str,
        file: FileFields,
    ) -> None:
        """Journal an upload: the record is committed, the file exists."""
        await self._emit(
            EventName.FILE_UPLOAD,
            user=user,
            file_id=file_id,
            payload=_file_payload(file),
        )

    async def file_download(
        self,
        *,
        user: ActorSource,
        file_record: StoredFile,
        is_owner: bool,
    ) -> None:
        """Journal a download: the stream is open, the file is handed out."""
        payload = _file_payload(file_record)
        payload['is_owner'] = is_owner
        await self._emit(
            EventName.FILE_DOWNLOAD,
            user=user,
            file_id=file_record.file_id,
            payload=payload,
        )

    async def file_access_denied(
        self,
        *,
        user: ActorSource,
        file_record: StoredFile,
    ) -> None:
        """Journal a refusal: the permission check of the backend said no.

        The record belongs to the journal of the actor's account; the
        account of the file is added when it is another one, so that
        the tenant sees its user reaching for a foreign file.
        """
        payload = _file_payload(file_record)
        if file_record.account_id != user.account_id:
            payload['file_account_id'] = file_record.account_id
        await self._emit(
            EventName.FILE_ACCESS_DENIED,
            user=user,
            file_id=file_record.file_id,
            payload=payload,
        )

    async def _emit(
        self,
        name: EventName,
        *,
        user: ActorSource,
        file_id: str,
        payload: dict[str, Any],
    ) -> None:
        event = Event(
            type=name,
            service=self._service,
            ts=_now(),
            account_id=user.account_id,
            actor=Actor(type=user.actor_type, id=user.user_id),
            file_id=file_id,
            context=self._context,
            payload=payload,
        )
        await self._emitter.emit(event)


def get_request_events(request: Request) -> RequestEvents:
    """FastAPI dependency: the records of this request."""
    return RequestEvents(
        emitter=get_event_emitter(),
        context=get_request_context(request),
        service=get_settings().LOGS_SERVICE_NAME,
    )


RequestEventsDep = Annotated[RequestEvents, Depends(get_request_events)]
