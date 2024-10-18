from rest_framework.serializers import (
    Serializer,
    IntegerField,
    CharField,
    ChoiceField,
    BooleanField,
    ValidationError
)
from pneumatic_backend.generics.mixins.serializers import (
    CustomValidationErrorMixin,
    ValidationUtilsMixin
)
from pneumatic_backend.processes.enums import (
    WorkflowApiStatus,
)
from pneumatic_backend.processes.messages.workflow import (
    MSG_PW_0067,
)


class WorkflowCountsResponseSerializer(Serializer):

    user_id = IntegerField()
    workflows_count = IntegerField()


class WorkflowCountsByTemplateTaskResponseSerializer(Serializer):

    template_task_id = IntegerField()
    workflows_count = IntegerField()


class WorkflowCountsByWorkflowStarterSerializer(
    CustomValidationErrorMixin,
    ValidationUtilsMixin,
    Serializer
):

    status = ChoiceField(
        required=False,
        choices=WorkflowApiStatus.CHOICES
    )
    template_ids = CharField(required=False)
    current_performer_ids = CharField(required=False)

    def validate_template_ids(self, value):
        return self.get_valid_list_integers(value)

    def validate_current_performer_ids(self, value):
        return self.get_valid_list_integers(value)

    def validate(self, data):
        status = data.get('status')
        current_performer_ids = data.get('current_performer_ids')
        if (
            current_performer_ids
            and status in WorkflowApiStatus.NOT_RUNNING
        ):
            raise ValidationError(MSG_PW_0067)
        return data


class WorkflowCountsByCurrentPerformerSerializer(
    CustomValidationErrorMixin,
    ValidationUtilsMixin,
    Serializer
):

    is_external = BooleanField(
        required=False,
        default=None,
        allow_null=True
    )
    status = ChoiceField(
        required=False,
        choices=WorkflowApiStatus.CHOICES
    )
    template_ids = CharField(required=False)
    template_task_ids = CharField(required=False)
    workflow_starter_ids = CharField(required=False)

    def validate_template_ids(self, value):
        return self.get_valid_list_integers(value)

    def validate_template_task_ids(self, value):
        return self.get_valid_list_integers(value)

    def validate_workflow_starter_ids(self, value):
        return self.get_valid_list_integers(value)

    def validate_status(self, value):
        if value in WorkflowApiStatus.NOT_RUNNING:
            raise ValidationError(MSG_PW_0067)
        return value


class WorkflowCountsByTemplateTaskSerializer(
    CustomValidationErrorMixin,
    ValidationUtilsMixin,
    Serializer
):

    is_external = BooleanField(
        required=False,
        default=None,
        allow_null=True
    )
    status = ChoiceField(
        required=False,
        choices=WorkflowApiStatus.CHOICES
    )
    template_ids = CharField(required=False)
    workflow_starter_ids = CharField(required=False)
    current_performer_ids = CharField(required=False)

    def validate_template_ids(self, value):
        return self.get_valid_list_integers(value)

    def validate_current_performer_ids(self, value):
        return self.get_valid_list_integers(value)

    def validate_workflow_starter_ids(self, value):
        return self.get_valid_list_integers(value)

    def validate(self, data):
        status = data.get('status')
        current_performer_ids = data.get('current_performer_ids')
        if (
            current_performer_ids
            and status in WorkflowApiStatus.NOT_RUNNING
        ):
            raise ValidationError(MSG_PW_0067)
        return data
