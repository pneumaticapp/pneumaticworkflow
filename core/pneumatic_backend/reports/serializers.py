from django.contrib.auth import get_user_model
from rest_framework import serializers

from pneumatic_backend.generics.serializers import DateTimeRangeSerializer
from pneumatic_backend.generics.fields import TimeStampField
from pneumatic_backend.generics.mixins.serializers import (
    CustomValidationErrorMixin,
    ValidationUtilsMixin
)
from pneumatic_backend.processes.models import (
    Workflow,
    Template,
    KickoffValue,
    WorkflowEvent,
)
from pneumatic_backend.processes.serializers.field import (
    TaskFieldSerializer
)


UserModel = get_user_model()


class ReportUsersSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserModel
        fields = (
            'id',
            'email',
            'first_name',
            'last_name',
            'photo',
        )


class TaskActivityTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Template
        fields = (
            'id',
            'name',
        )


class ActivityKickoffValueSerializer(serializers.ModelSerializer):

    class Meta:
        model = KickoffValue
        fields = (
            'description',
            'output',
        )

    output = TaskFieldSerializer(many=True)


class ActivityWorkflowSerializer(serializers.ModelSerializer):

    class Meta:
        model = Workflow
        fields = (
            'id',
            'name',
            'current_task',
            'tasks_count',
            'template',
            'is_legacy_template',
            'legacy_template_name',
            'status',
            'kickoff',
            'is_external',
        )

    template = TaskActivityTemplateSerializer()
    kickoff = serializers.SerializerMethodField()

    def get_kickoff(self, instance):
        kickoff = instance.kickoff_instance
        return (
            ActivityKickoffValueSerializer(kickoff).data if kickoff else None
        )


class HighlightsFilterSerializer(
    CustomValidationErrorMixin,
    ValidationUtilsMixin,
    serializers.Serializer
):
    templates = serializers.CharField(required=False)
    current_performer_ids = serializers.CharField(required=False)
    date_before_tsp = TimeStampField(required=False, allow_null=True)
    date_after_tsp = TimeStampField(required=False, allow_null=True)

    def validate_users(self, value):
        return self.get_valid_list_integers(value)

    def validate_current_performer_ids(self, value):
        return self.get_valid_list_integers(value)

    def validate_current_performer_group_ids(self, value):
        return self.get_valid_list_integers(value)


class EventHighlightsSerializer(serializers.ModelSerializer):

    class Meta:
        model = WorkflowEvent
        fields = (
            'id',
            'type',
            'task',
            'text',
            'delay',
            'created',
            'created_tsp',
            'user_id',
            'target_user_id',
            'workflow',
        )

    task = serializers.JSONField(source='task_json')
    delay = serializers.JSONField(source='delay_json')
    workflow = ActivityWorkflowSerializer()
    created_tsp = TimeStampField(source='created')


class AccountDashboardOverviewSerializer(serializers.Serializer):
    launched = serializers.IntegerField(read_only=True)
    completed = serializers.IntegerField(read_only=True)
    ongoing = serializers.IntegerField(read_only=True)
    snoozed = serializers.IntegerField(read_only=True)


class DashboardFilterSerializer(DateTimeRangeSerializer):
    now = serializers.BooleanField()


class BreakdownByStepsFilterSerializer(DashboardFilterSerializer):
    template_id = serializers.IntegerField()
