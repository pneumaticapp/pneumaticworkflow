"""Shape of an audit record: its name, its actor and its context."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Protocol

from src.shared_kernel.auth.user_types import ActorType

TS_FORMAT = '%Y-%m-%dT%H:%M:%S.%f'
TS_SUFFIX = 'Z'
OBJECT_TYPE_FILE = 'file'
FILE_PII = ('ip', 'user_agent', 'payload.filename')

STREAM_KEY = 'pneumatic:events'
PAYLOAD_STR_MAX = 2000
SERVICE_NAME = 'pneumatic-file-service'


class EventName(StrEnum):
    """Types the backend registry declares for the file service."""

    FILE_UPLOAD = 'file.upload'
    FILE_DOWNLOAD = 'file.download'
    FILE_ACCESS_DENIED = 'file.access_denied'


class EventCategory(StrEnum):
    """Category of the backend registry; every file type is audit."""

    AUDIT = 'audit'


class ActorSource(Protocol):
    """What an authenticated request knows about who is acting.

    Read-only on purpose: frozen entities satisfy it.
    """

    @property
    def user_id(self) -> int | None:
        """Id of the user, None for a public token."""

    @property
    def account_id(self) -> int:
        """Tenant of the actor, the journal the record belongs to."""

    @property
    def actor_type(self) -> ActorType:
        """Kind of the credential behind the request."""


class FileFields(Protocol):
    """What goes into the payload of a file record."""

    @property
    def filename(self) -> str | None:
        """Name given at upload, sanitized."""

    @property
    def content_type(self) -> str | None:
        """Content type given at upload, sanitized."""

    @property
    def size(self) -> int:
        """Size in bytes."""


class StoredFile(FileFields, Protocol):
    """A file that has a record already: download and denial."""

    @property
    def file_id(self) -> str:
        """Identifier of the record."""

    @property
    def account_id(self) -> int:
        """Tenant the file belongs to."""


def format_ts(value: datetime) -> str:
    """Serialize a moment the way the backend parses it back."""
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC).strftime(TS_FORMAT) + TS_SUFFIX


def cut(value: str | None) -> str | None:
    """Trim a payload string to the length the backend allows."""
    if value is None:
        return None
    return value[:PAYLOAD_STR_MAX]


@dataclass(frozen=True)
class Actor:
    """Who acted.

    The e-mail is never known here: the token cache holds no address,
    and the backend records of the same actor.id carry it.
    """

    type: ActorType
    id: int | None

    def to_dict(self) -> dict[str, Any]:
        """Actor part of the envelope."""
        return {'type': self.type.value, 'id': self.id, 'email': None}


@dataclass(frozen=True)
class RequestContext:
    """HTTP context of the request that produced the record."""

    ip: str | None
    user_agent: str | None
    request_id: str


@dataclass(frozen=True)
class Event:
    """One record of the journal."""

    type: EventName
    service: str
    ts: datetime
    account_id: int
    actor: Actor
    file_id: str
    context: RequestContext
    payload: dict[str, Any] = field(default_factory=dict)
    category: EventCategory = EventCategory.AUDIT

    def to_dict(self) -> dict[str, Any]:
        """Build the envelope as the backend consumer expects it."""
        return {
            'type': self.type.value,
            'category': self.category.value,
            'service': self.service,
            'ts': format_ts(self.ts),
            'account_id': self.account_id,
            'actor': self.actor.to_dict(),
            'object': {'type': OBJECT_TYPE_FILE, 'id': self.file_id},
            'workflow_id': None,
            'task_id': None,
            'ip': self.context.ip,
            'user_agent': self.context.user_agent,
            'request_id': self.context.request_id,
            'payload': dict(self.payload),
            'pii': list(FILE_PII),
        }
