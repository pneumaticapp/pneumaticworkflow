from rest_framework.serializers import (
    BooleanField,
    CharField,
    ChoiceField,
    IntegerField,
    Serializer,
    ValidationError,
)

from src.generics.mixins.serializers import (
    CustomValidationErrorMixin,
    ValidationUtilsMixin,
)
from src.processes.enums import (
    PerformerType,
    WorkflowApiStatus,
)
from src.processes.messages.workflow import (
    MSG_PW_0067,
)


class WorkflowCountsResponseSerializer(Serializer):

    type = ChoiceField(choices=PerformerType.filter_choices)
    source_id = IntegerField()
    workflows_count = IntegerField()


class WorkflowCountsByTemplateTaskResponseSerializer(Serializer):

    template_task_api_name = CharField()
    workflows_count = IntegerField()


class WorkflowCountsByWorkflowStarterSerializer(
    CustomValidationErrorMixin,
    ValidationUtilsMixin,
    Serializer,
):

    status = ChoiceField(
        required=False,
        choices=WorkflowApiStatus.CHOICES,
    )
    template_ids = CharField(required=False)
    current_performer_ids = CharField(required=False)
    current_performer_group_ids = CharField(required=False)

    def validate_template_ids(self, value):
        return self.get_valid_list_integers(value)

    def validate_current_performer_ids(self, value):
        return self.get_valid_list_integers(value)

    def validate_current_performer_group_ids(self, value):
        return self.get_valid_list_integers(value)

    def validate(self, data):
        status = data.get('status')
        current_performer_ids = data.get('current_performer_ids')
        current_performer_group_ids = data.get('current_performer_group_ids')
        if (
            (current_performer_ids or current_performer_group_ids)
            and status in WorkflowApiStatus.NOT_RUNNING
        ):
            raise ValidationError(MSG_PW_0067)
        return data


class WorkflowCountsByCurrentPerformerSerializer(
    CustomValidationErrorMixin,
    ValidationUtilsMixin,
    Serializer,
):

    is_external = BooleanField(
        required=False,
        default=None,
        allow_null=True,
    )
    template_ids = CharField(required=False)
    template_task_api_names = CharField(required=False)
    workflow_starter_ids = CharField(required=False)

    def validate(self, attrs):
        return attrs

    def validate_template_ids(self, value):
        return self.get_valid_list_integers(value)

    def validate_template_task_api_names(self, value):
        return self.get_valid_list_strings(value)

    def validate_workflow_starter_ids(self, value):
        return self.get_valid_list_integers(value)


class WorkflowCountsByTemplateTaskSerializer(
    CustomValidationErrorMixin,
    ValidationUtilsMixin,
    Serializer,
):

    is_external = BooleanField(
        required=False,
        default=None,
        allow_null=True,
    )
    status = ChoiceField(
        required=False,
        choices=WorkflowApiStatus.CHOICES,
    )
    template_ids = CharField(required=False)
    workflow_starter_ids = CharField(required=False)
    current_performer_ids = CharField(required=False)
    current_performer_group_ids = CharField(required=False)

    def validate_template_ids(self, value):
        return self.get_valid_list_integers(value)

    def validate_current_performer_ids(self, value):
        return self.get_valid_list_integers(value)

    def validate_current_performer_group_ids(self, value):
        return self.get_valid_list_integers(value)

    def validate_workflow_starter_ids(self, value):
        return self.get_valid_list_integers(value)

    def validate(self, data):
        status = data.get('status')
        current_performer_ids = data.get('current_performer_ids')
        current_performer_group_ids = data.get('current_performer_group_ids')
        if (
            (current_performer_ids or current_performer_group_ids)
            and status in WorkflowApiStatus.NOT_RUNNING
        ):
            raise ValidationError(MSG_PW_0067)
        return data
