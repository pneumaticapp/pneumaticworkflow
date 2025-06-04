from django.contrib.auth import get_user_model
from rest_framework import serializers
from pneumatic_backend.processes.models import Delay, Task, Workflow
from pneumatic_backend.accounts.models import Notification
from pneumatic_backend.accounts.enums import NotificationType
from pneumatic_backend.generics.fields import TimeStampField


UserModel = get_user_model()


class DelaySerializer(serializers.ModelSerializer):

    class Meta:
        model = Delay
        fields = (
            'estimated_end_date_tsp',
            'duration',
        )

    estimated_end_date_tsp = TimeStampField(
        source='estimated_end_date',
        read_only=True
    )


class NotificationTaskSerializer(serializers.ModelSerializer):
    due_date_tsp = TimeStampField(source='due_date', read_only=True)
    delay = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = (
            'id',
            'name',
            'due_date_tsp',
            'delay'
        )

    def __init__(self, *args, **kwargs):
        self.notification_type = kwargs.pop('notification_type', None)
        super().__init__(*args, **kwargs)
        if self.notification_type != NotificationType.DELAY_WORKFLOW:
            self.fields.pop('delay', None)
        if self.notification_type != NotificationType.DUE_DATE_CHANGED:
            if not self.instance.due_date:
                self.fields.pop('due_date_tsp', None)

    def get_delay(self, instance):
        delay = instance.get_active_delay()
        if not delay:
            return None
        return DelaySerializer(delay).data


class NotificationWorkflowSerializer(serializers.ModelSerializer):
    class Meta:
        model = Workflow
        fields = (
            'id',
            'name'
        )


class NotificationsSerializer(serializers.ModelSerializer):

    class Meta:
        model = Notification
        fields = (
            'id',
            'text',
            'type',
            'datetime',
            'datetime_tsp',
            'status',
            'author',
            'task',
            'workflow',
        )

    task = serializers.JSONField(source='task_json', read_only=True)
    workflow = serializers.JSONField(source='workflow_json', read_only=True)
    datetime_tsp = TimeStampField(source='datetime', read_only=True)
