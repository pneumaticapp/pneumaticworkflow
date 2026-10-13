import uuid

from django.conf import settings
from django.db import models
from oauth2_provider.models import AbstractApplication

from src.storage.enums import (
    ImportJobState,
    UploadStatus,
    UploadTargetType,
)
from src.generics.querysets import (
    ExpiringQuerySet,
)
from src.storage.querysets import (
    ImportJobQuerySet,
    UploadSessionQuerySet,
)


class MCPModel(models.Model):
    """Base for MCP records.

    MCP records are short-lived credentials, bindings and transfer state
    that expire by TTL and are pruned physically by
    `src.mcp.tasks.prune_expired_state`. They hold no business data:
    workflows, tasks and attachments created through MCP live in their
    own soft-deleted models.
    """

    class Meta:
        abstract = True

    def __str__(self):
        return f'{type(self).__name__} {self.pk}'


class ClientPolicy(MCPModel):
    application = models.OneToOneField(
        'oauth2_provider.Application',
        on_delete=models.CASCADE,
        related_name='mcp_policy',
    )
    can_introspect = models.BooleanField(default=False, editable=False)
    is_active = models.BooleanField(default=True)
    registration_type = models.CharField(
        max_length=20,
        choices=AbstractApplication.RegistrationSource.choices,
        default=AbstractApplication.RegistrationSource.MANUAL,
    )


class Connection(MCPModel):
    """User consent for an MCP client; revoked, never deleted by users."""

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    account = models.ForeignKey('accounts.Account', on_delete=models.CASCADE)
    application = models.ForeignKey(
        'oauth2_provider.Application',
        on_delete=models.CASCADE,
    )
    scopes = models.JSONField(default=list)
    resource = models.URLField(max_length=2048)
    created_at = models.DateTimeField(auto_now_add=True)
    revoked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ('-created_at', 'pk')
        indexes = [
            models.Index(
                fields=['user', 'account', 'application', 'resource'],
                name='mcp_connection_identity_idx',
            ),
        ]


class AuthorizationRequest(MCPModel):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    parameters = models.JSONField()
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
    )
    account = models.ForeignKey(
        'accounts.Account',
        on_delete=models.CASCADE,
        null=True,
    )
    expires_at = models.DateTimeField(db_index=True)
    consumed_at = models.DateTimeField(null=True)
    login_completed_at = models.DateTimeField(null=True)

    objects = ExpiringQuerySet.as_manager()


class LoginCode(MCPModel):
    digest = models.CharField(max_length=64, unique=True)
    authorization_request = models.ForeignKey(
        AuthorizationRequest,
        on_delete=models.CASCADE,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    account = models.ForeignKey('accounts.Account', on_delete=models.CASCADE)
    expires_at = models.DateTimeField(db_index=True)
    consumed_at = models.DateTimeField(null=True)
    redirect_url = models.TextField(blank=True)

    objects = ExpiringQuerySet.as_manager()


class CodeBinding(MCPModel):
    digest = models.CharField(max_length=64, unique=True)
    connection = models.ForeignKey(Connection, on_delete=models.CASCADE)
    expires_at = models.DateTimeField(db_index=True)

    objects = ExpiringQuerySet.as_manager()


class AccessBinding(MCPModel):
    access_token = models.OneToOneField(
        'oauth2_provider.AccessToken',
        on_delete=models.CASCADE,
        related_name='mcp_binding',
    )
    connection = models.ForeignKey(Connection, on_delete=models.CASCADE)


class RefreshBinding(MCPModel):
    refresh_token = models.OneToOneField(
        'oauth2_provider.RefreshToken',
        on_delete=models.CASCADE,
        related_name='mcp_binding',
    )
    connection = models.ForeignKey(Connection, on_delete=models.CASCADE)


class Delegation(MCPModel):
    digest = models.CharField(max_length=64, unique=True)
    connection = models.ForeignKey(Connection, on_delete=models.CASCADE)
    source_token = models.ForeignKey(
        'oauth2_provider.AccessToken',
        on_delete=models.CASCADE,
    )
    audience = models.CharField(max_length=40)
    operation = models.CharField(max_length=80)
    method = models.CharField(max_length=8)
    path = models.CharField(max_length=8192)
    scopes = models.JSONField(default=list)
    expires_at = models.DateTimeField(db_index=True)

    objects = ExpiringQuerySet.as_manager()


class UploadSession(MCPModel):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    connection = models.ForeignKey(Connection, on_delete=models.CASCADE)
    target_type = models.CharField(
        max_length=10,
        choices=UploadTargetType.CHOICES,
        default=UploadTargetType.TASK,
    )
    task = models.ForeignKey(
        'processes.Task',
        on_delete=models.CASCADE,
        null=True,
    )
    template = models.ForeignKey(
        'processes.Template',
        on_delete=models.CASCADE,
        null=True,
    )
    field = models.ForeignKey(
        'processes.TaskField',
        on_delete=models.CASCADE,
        null=True,
    )
    field_template = models.ForeignKey(
        'processes.FieldTemplate',
        on_delete=models.CASCADE,
        null=True,
    )
    filename = models.CharField(max_length=255)
    content_type = models.CharField(max_length=255)
    size = models.PositiveBigIntegerField()
    status = models.CharField(
        max_length=20,
        choices=UploadStatus.CHOICES,
        default=UploadStatus.PENDING,
    )
    file_id = models.CharField(max_length=512, blank=True)
    source_url = models.URLField(max_length=2048, blank=True)
    error = models.CharField(max_length=255, blank=True)
    expires_at = models.DateTimeField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = UploadSessionQuerySet.as_manager()

    class Meta:
        indexes = [
            models.Index(fields=['status'], name='mcp_upload_status_idx'),
        ]

    @property
    def field_api_name(self) -> str:
        if self.target_type == UploadTargetType.TASK:
            return self.field.api_name
        return self.field_template.api_name


class UploadCapability(MCPModel):
    digest = models.CharField(max_length=64, unique=True)
    session = models.ForeignKey(UploadSession, on_delete=models.CASCADE)
    expires_at = models.DateTimeField(db_index=True)

    objects = ExpiringQuerySet.as_manager()


class ImportJob(MCPModel):
    session = models.OneToOneField(UploadSession, on_delete=models.CASCADE)
    state = models.CharField(
        max_length=20,
        choices=ImportJobState.CHOICES,
        default=ImportJobState.QUEUED,
    )
    attempts = models.PositiveIntegerField(default=0)
    lease_until = models.DateTimeField(null=True)
    next_attempt_at = models.DateTimeField()

    objects = ImportJobQuerySet.as_manager()

    class Meta:
        indexes = [
            models.Index(
                fields=['state', 'next_attempt_at'],
                name='mcp_import_due_idx',
            ),
            models.Index(
                fields=['state', 'lease_until'],
                name='mcp_import_lease_idx',
            ),
        ]


class FileAuthorization(MCPModel):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    connection = models.ForeignKey(Connection, on_delete=models.CASCADE)
    source_token = models.ForeignKey(
        'oauth2_provider.AccessToken',
        on_delete=models.CASCADE,
    )
    file_id = models.CharField(max_length=512)
    expires_at = models.DateTimeField(db_index=True)

    objects = ExpiringQuerySet.as_manager()
