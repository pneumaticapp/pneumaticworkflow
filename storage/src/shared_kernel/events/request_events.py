"""Records of one request: built here, written by the emitter."""

from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import Depends, Request

from src.shared_kernel.events.emitter import EventEmitter, get_event_emitter
from src.shared_kernel.events.schema import (
    SERVICE_NAME,
    Actor,
    ActorSource,
    Event,
    EventName,
    FileFields,
    RequestContext,
    StoredFile,
    cut,
)
from src.shared_kernel.http_context import (
    get_client_ip,
    get_request_id,
    get_user_agent,
)


def _now() -> datetime:
    # Module-level clock: the tests patch it instead of datetime.now.
    return datetime.now(UTC)


def _file_payload(file: FileFields) -> dict[str, Any]:
    """Build what every file record says about the file.

    The content is never in it, nor the bucket or the path in S3.
    """
    return {
        'filename': cut(file.filename),
        'size': file.size,
        'content_type': cut(file.content_type),
    }


class RequestEvents:
    """The three records an endpoint of the file service may write."""

    def __init__(
        self,
        *,
        emitter: EventEmitter,
        context: RequestContext,
    ) -> None:
        """Bind the records of one request.

        The name this service signs its records with is a constant of
        the process (SERVICE_NAME), not something a request carries,
        so it is not threaded through here.

        Args:
            emitter: Writer of the stream.
            context: HTTP context of the request.

        """
        self._emitter = emitter
        self._context = context

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
            service=SERVICE_NAME,
            ts=_now(),
            account_id=user.account_id,
            actor=Actor(type=user.actor_type, id=user.user_id),
            file_id=file_id,
            context=self._context,
            payload=payload,
        )
        await self._emitter.emit(event)


async def get_request_events(request: Request) -> RequestEvents:
    """FastAPI dependency: the records of this request.

    A coroutine on purpose: FastAPI runs a plain function dependency
    in a thread of the pool, a thread hop per request for three
    header reads.
    """
    return RequestEvents(
        emitter=get_event_emitter(),
        context=RequestContext(
            ip=get_client_ip(request),
            user_agent=get_user_agent(request),
            request_id=get_request_id(request),
        ),
    )


RequestEventsDep = Annotated[RequestEvents, Depends(get_request_events)]
