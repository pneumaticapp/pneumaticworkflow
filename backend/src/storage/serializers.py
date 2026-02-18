from typing import Optional

from rest_framework import serializers
from rest_framework.serializers import ValidationError

from src.generics.mixins.serializers import CustomValidationErrorMixin
from src.storage.messages import MSG_FS_0011
from src.storage.models import Attachment
from src.storage.paginations import AttachmentListPagination
from src.storage.utils import get_file_service_file_url


class AttachmentSerializer(serializers.ModelSerializer):
    """Serializer for Attachment model."""

    class Meta:
        model = Attachment
        fields = [
            'id',
            'file_id',
            'access_type',
            'source_type',
            'account',
            'task',
            'template',
            'workflow',
        ]
        read_only_fields = [
            'id',
        ]


class AttachmentCheckPermissionSerializer(
    CustomValidationErrorMixin,
    serializers.Serializer,
):
    """Serializer for checking file access permissions."""

    file_id = serializers.CharField(
        max_length=64,
        required=True,
        help_text='Unique file identifier',
    )

    def validate_file_id(self, value):
        if not value.strip():
            raise ValidationError(MSG_FS_0011)
        return value.strip()


class AttachmentListSerializer(serializers.ModelSerializer):
    """Serializer for attachment list."""

    url = serializers.SerializerMethodField()

    class Meta:
        model = Attachment
        fields = [
            'id',
            'file_id',
            'url',
            'access_type',
            'source_type',
        ]

    def get_url(self, obj: Attachment) -> Optional[str]:
        """Return ready-made link to file in file service."""
        return get_file_service_file_url(obj.file_id)


class AttachmentListFilterSerializer(
    CustomValidationErrorMixin,
    serializers.Serializer,
):
    """Serializer for filtering attachment list."""

    limit = serializers.IntegerField(
        required=False,
        min_value=0,
        max_value=AttachmentListPagination.max_limit,
        default=AttachmentListPagination.default_limit,
    )
    offset = serializers.IntegerField(
        required=False,
        min_value=0,
    )
