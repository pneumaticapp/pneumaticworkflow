from src.storage.validators import validate_import_url
import src.storage.messages as fs_messages

from django.conf import settings
from rest_framework import serializers

from src.mcp import messages
from src.storage.constants import (
    CONTENT_TYPE_PATTERN,
    FILENAME_PATTERN,
)
from src.mcp.constants import (
    FRONTEND_FILE_UPLOAD_PATH,
    FRONTEND_UPLOADS_PATH,
)
from src.authentication.constants import (
    UPLOAD_CAPABILITY_TTL,
)
from src.storage.enums import (
    UploadTargetType,
)
from src.storage.file_metadata import (
    canonical_content_type,
    canonical_filename,
)
from src.mcp.models import UploadSession
from src.generics.serializers import BaseInputSerializer
from src.storage.services.upload_sessions import UploadSessionService
from src.authentication.tokens import get_expires_in

BEARER = 'Bearer'


class UploadSerializer(BaseInputSerializer):
    target_type = serializers.ChoiceField(
        choices=UploadTargetType.CHOICES,
        default=UploadTargetType.TASK,
    )
    task_id = serializers.IntegerField(min_value=1, required=False)
    template_id = serializers.IntegerField(min_value=1, required=False)
    field_api_name = serializers.CharField(max_length=255)
    filename = serializers.RegexField(
        regex=FILENAME_PATTERN,
        trim_whitespace=False,
    )
    content_type = serializers.RegexField(
        regex=CONTENT_TYPE_PATTERN,
        max_length=255,
    )
    size = serializers.IntegerField(min_value=1)

    def validate_filename(self, value: str) -> str:
        return canonical_filename(value=value)

    def validate_content_type(self, value: str) -> str:
        return canonical_content_type(value=value)

    def validate_size(self, value: int) -> int:
        if value > settings.MCP_MAX_IMPORT_BYTES:
            raise serializers.ValidationError(fs_messages.MSG_FS_0014)
        return value

    def validate(self, attrs: dict) -> dict:
        is_task = attrs['target_type'] == UploadTargetType.TASK
        has_task = 'task_id' in attrs
        has_template = 'template_id' in attrs
        if is_task != has_task or is_task == has_template:
            raise serializers.ValidationError(messages.MSG_MCP_0002)
        return attrs


class ImportSerializer(BaseInputSerializer):
    url = serializers.CharField(max_length=2048)

    def validate_url(self, value: str) -> str:
        """Storage downloads only public HTTPS URLs without credentials."""
        return validate_import_url(value=value)


class AttachSerializer(BaseInputSerializer):
    task_id = serializers.IntegerField(min_value=1)


class UploadSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = UploadSession
        fields = (
            'id',
            'status',
            'user_id',
            'account_id',
            'connection_id',
            'target_type',
            'task_id',
            'template_id',
            'field_api_name',
            'filename',
            'content_type',
            'size',
            'max_size',
            'expires_at',
            'upload_url',
            'file_id',
            'error',
        )

    status = serializers.SerializerMethodField()
    user_id = serializers.IntegerField(source='connection.user_id')
    account_id = serializers.IntegerField(source='connection.account_id')
    connection_id = serializers.CharField()
    task_id = serializers.IntegerField(allow_null=True)
    template_id = serializers.IntegerField(allow_null=True)
    field_api_name = serializers.CharField()
    max_size = serializers.SerializerMethodField()
    expires_at = serializers.SerializerMethodField()
    upload_url = serializers.SerializerMethodField()
    file_id = serializers.SerializerMethodField()
    error = serializers.SerializerMethodField()

    def get_status(self, instance: UploadSession) -> str:
        return UploadSessionService.get_status(session=instance)

    def get_max_size(self, instance: UploadSession) -> int:
        return settings.MCP_MAX_IMPORT_BYTES

    def get_expires_at(self, instance: UploadSession) -> str:
        return instance.expires_at.isoformat()

    def get_upload_url(self, instance: UploadSession) -> str:
        return f'{settings.FRONTEND_URL}{FRONTEND_UPLOADS_PATH}/{instance.pk}'

    def get_file_id(self, instance: UploadSession) -> str | None:
        return instance.file_id or None

    def get_error(self, instance: UploadSession) -> str | None:
        return instance.error or None


class UploadCreateResponseSerializer(UploadSessionSerializer):
    class Meta(UploadSessionSerializer.Meta):
        fields = (*UploadSessionSerializer.Meta.fields, 'credential')

    credential = serializers.SerializerMethodField()

    def get_credential(self, instance: UploadSession) -> str:
        return self.context['credential']


class UploadTokenResponseSerializer(serializers.Serializer):
    access_token = serializers.CharField(source='credential')
    token_type = serializers.SerializerMethodField()
    expires_in = serializers.SerializerMethodField()
    upload_session_id = serializers.CharField(source='session.pk')
    file_upload_url = serializers.SerializerMethodField()

    def get_token_type(self, instance) -> str:
        return BEARER

    def get_expires_in(self, instance) -> int:
        return get_expires_in(
            expires_at=instance.session.expires_at,
            ttl=UPLOAD_CAPABILITY_TTL,
        )

    def get_file_upload_url(self, instance) -> str:
        return f'{settings.FRONTEND_URL}{FRONTEND_FILE_UPLOAD_PATH}'


class UploadStateResponseSerializer(serializers.ModelSerializer):
    """Short result of import, completion and attach."""

    class Meta:
        model = UploadSession
        fields = ('id', 'status')

    id = serializers.CharField()


class UploadCompletedResponseSerializer(UploadStateResponseSerializer):
    class Meta(UploadStateResponseSerializer.Meta):
        fields = ('id', 'status', 'file_id')


class UploadAttachedResponseSerializer(UploadStateResponseSerializer):
    class Meta(UploadStateResponseSerializer.Meta):
        fields = ('id', 'status', 'task_id', 'field_api_name', 'file_id')

    task_id = serializers.IntegerField()
    field_api_name = serializers.CharField()
