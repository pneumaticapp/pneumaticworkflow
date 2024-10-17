from rest_framework import serializers
from pneumatic_backend.accounts.serializers.user import (
    UserNameSerializer,
)
from pneumatic_backend.processes.models import (
    Task,
    Workflow,
    Template,
)
from pneumatic_backend.processes.serializers.kickoff_value import (
    KickoffValueInfoSerializer,
)
from pneumatic_backend.processes.serializers.task_field import (
    TaskFieldListSerializer,
)
from pneumatic_backend.processes.serializers.template import (
    TemplateDetailsSerializer,
)


class TemplateTaskListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Template
        fields = (
            'id',
            'name',
        )


class WorkflowTaskListSerializer(serializers.ModelSerializer):
    template = TemplateTaskListSerializer(allow_null=True)

    class Meta:
        model = Workflow
        fields = (
            'id',
            'workflow',
            'name',
            'is_legacy_template',
            'legacy_template_name',
            'tasks_count',
            'current_task',
            'finalizable',
        )


class RecentCurrentTaskSerializer(serializers.ModelSerializer):
    performers = UserNameSerializer(
        many=True,
        read_only=True
    )

    class Meta:
        model = Task
        fields = (
            'id',
            'name',
            'number',
            'description',
            'performers',
            'date_started',
            'date_completed',
        )


class RecentWorkflowSerializer(serializers.ModelSerializer):

    class Meta:
        model = Workflow
        fields = (
            'id',
            'name',
            'status',
            'date_created',
            'template',
            'current_task',
            'kickoff',
        )

    kickoff = serializers.SerializerMethodField()
    current_task = serializers.SerializerMethodField(read_only=True)
    template = TemplateDetailsSerializer(read_only=True)

    def get_current_task(self, instance):
        task = instance.current_task_instance
        return RecentCurrentTaskSerializer(task).data

    def get_kickoff(self, instance: Workflow):
        kickoff = instance.kickoff_instance
        if kickoff:
            return KickoffValueInfoSerializer(kickoff).data
        return None


class RecentTaskSerializer(serializers.ModelSerializer):
    performers = UserNameSerializer(
        many=True,
        read_only=True
    )
    workflow = RecentWorkflowSerializer(read_only=True)
    output = TaskFieldListSerializer(many=True)

    class Meta:
        model = Task
        fields = (
            'id',
            'name',
            'number',
            'description',
            'workflow',
            'output',
            'performers',
            'date_started',
            'date_completed',
        )
