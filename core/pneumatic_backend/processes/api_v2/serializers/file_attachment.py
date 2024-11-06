from django.conf import settings
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from pneumatic_backend.processes.models import FileAttachment
from pneumatic_backend.processes.messages.workflow import (
    MSG_PW_0050,
)
from pneumatic_backend.generics.mixins.serializers import (
    CustomValidationErrorMixin
)


ATTACHMENT_MAX_SIZE_BYTES = settings.ATTACHMENT_MAX_SIZE_BYTES


class FileAttachmentCreateSerializer(
    CustomValidationErrorMixin,
    serializers.Serializer,
):

    content_type = serializers.CharField(max_length=256)
    filename = serializers.CharField(max_length=256)
    size = serializers.IntegerField()
    thumbnail = serializers.BooleanField()

    def validate_size(self, value: int) -> int:
        if value > ATTACHMENT_MAX_SIZE_BYTES:
            raise ValidationError(MSG_PW_0050(ATTACHMENT_MAX_SIZE_BYTES))
        return value


class FileAttachmentSerializer(serializers.ModelSerializer):

    class Meta:
        model = FileAttachment
        fields = (
            'id',
            'name',
            'url',
            'thumbnail_url',
            'size',
        )


class FileAttachmentShortSerializer(serializers.ModelSerializer):

    class Meta:
        model = FileAttachment
        fields = (
            'id',
            'name',
            'url',
        )
