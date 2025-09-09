from django.contrib.auth import get_user_model
from rest_framework.serializers import ModelSerializer
from pneumatic_backend.generics.serializers import CustomValidationErrorMixin
from pneumatic_backend.processes.models import FieldSelection

UserModel = get_user_model()


class FieldSelectionSerializer(
    CustomValidationErrorMixin,
    ModelSerializer
):
    class Meta:
        model = FieldSelection
        fields = (
            'id',
            'api_name',
            'value',
            'is_selected'
        )
