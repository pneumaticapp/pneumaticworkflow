from django.contrib.auth import get_user_model
from rest_framework import serializers
from pneumatic_backend.generics.mixins.serializers import (
    CustomValidationErrorMixin,
)
from pneumatic_backend.processes.models import (
    TaskField
)
from pneumatic_backend.processes.serializers.selections import (
    FieldSelectionSerializer
)

UserModel = get_user_model()


class TaskFieldSerializer(
    CustomValidationErrorMixin,
    serializers.ModelSerializer
):

    class Meta:
        model = TaskField
        fields = (
            'id',
            'task_id',
            'kickoff_id',
            'type',
            'api_name',
            'name',
            'value',
            'attachments',
            'selections',
        )

    selections = FieldSelectionSerializer(many=True)
