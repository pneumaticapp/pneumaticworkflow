from src.storage import messages as fs_messages
from rest_framework import serializers

from src.storage.constants import (
    CONTENT_TYPE_PATTERN,
    FILE_ID_PATTERN,
)
from src.storage.constants import (
    MAX_FILE_ID_LENGTH,
)
from src.storage.enums import (
    FileOperation,
)
from src.storage.file_metadata import valid_file_id
from src.mcp.models import FileAuthorization, UploadCapability
from src.generics.serializers import BaseInputSerializer
from src.storage.models import Attachment


class FileValidationSerializer(BaseInputSerializer):
    credential = serializers.CharField(max_length=4096, required=False)
    operation = serializers.ChoiceField(choices=FileOperation.CHOICES)
    upload_session_id = serializers.UUIDField(required=False)
    file_id = serializers.CharField(
        max_length=MAX_FILE_ID_LENGTH,
        required=False,
        trim_whitespace=False,
    )
    connection_id = serializers.UUIDField(required=False)
    authorization_id = serializers.UUIDField(required=False)

    def validate_file_id(self, value: str) -> str:
        if not valid_file_id(value=value):
            raise serializers.ValidationError(fs_messages.MSG_FS_0012)
        return value


class UploadCompletionSerializer(BaseInputSerializer):
    credential = serializers.CharField(max_length=4096)
    upload_session_id = serializers.UUIDField()
    file_id = serializers.RegexField(regex=FILE_ID_PATTERN)
    name = serializers.CharField(max_length=255)
    size = serializers.IntegerField(min_value=1)
    content_type = serializers.RegexField(
        regex=CONTENT_TYPE_PATTERN,
        max_length=255,
    )


class CleanupSerializer(BaseInputSerializer):
    upload_session_id = serializers.UUIDField()
    file_id = serializers.RegexField(regex=FILE_ID_PATTERN)
    account_id = serializers.IntegerField(min_value=1)
    user_id = serializers.IntegerField(min_value=1)


class AttachmentResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attachment
        fields = ('id', 'file_id')


class UploadGrantSerializer(serializers.ModelSerializer):
    class Meta:
        model = UploadCapability
        fields = (
            'active',
            'user_id',
            'account_id',
            'connection_id',
            'operation',
            'upload_session_id',
        )

    active = serializers.SerializerMethodField()
    user_id = serializers.IntegerField(source='session.connection.user_id')
    account_id = serializers.IntegerField(
        source='session.connection.account_id',
    )
    connection_id = serializers.CharField(source='session.connection_id')
    operation = serializers.SerializerMethodField()
    upload_session_id = serializers.CharField(source='session_id')

    def get_active(self, instance: UploadCapability) -> bool:
        return True

    def get_operation(self, instance: UploadCapability) -> str:
        return self.context['operation']


class FileGrantSerializer(serializers.ModelSerializer):
    class Meta:
        model = FileAuthorization
        fields = (
            'active',
            'user_id',
            'account_id',
            'connection_id',
            'operation',
            'authorization_id',
            'expires_at',
        )

    active = serializers.SerializerMethodField()
    user_id = serializers.IntegerField(source='connection.user_id')
    account_id = serializers.IntegerField(source='connection.account_id')
    connection_id = serializers.CharField()
    operation = serializers.SerializerMethodField()
    authorization_id = serializers.CharField(source='pk')
    expires_at = serializers.SerializerMethodField()

    def get_active(self, instance: FileAuthorization) -> bool:
        return True

    def get_operation(self, instance: FileAuthorization) -> str:
        return self.context['operation']

    def get_expires_at(self, instance: FileAuthorization) -> int:
        return int(instance.expires_at.timestamp())
