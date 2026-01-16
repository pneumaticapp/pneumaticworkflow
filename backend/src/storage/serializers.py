from rest_framework import serializers

from src.generics.mixins.serializers import CustomValidationErrorMixin
from src.storage.models import Attachment


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
        """Validate file_id."""
        if not value or not value.strip():
            raise serializers.ValidationError(
                'file_id cannot be empty',
            )
        return value.strip()


class AttachmentListSerializer(serializers.ModelSerializer):
    """Serializer for attachment list."""

    class Meta:
        model = Attachment
        fields = [
            'id',
            'file_id',
            'access_type',
            'source_type',
        ]
