from django.contrib.auth import get_user_model
from rest_framework import serializers
from pneumatic_backend.processes.models import Delay
from pneumatic_backend.accounts.models import Notification
from pneumatic_backend.accounts.enums import NotificationType
from pneumatic_backend.generics.fields import TimeStampField


UserModel = get_user_model()
datetime_format = '%Y-%m-%dT%H:%M:%S.%fZ'


class DelaySerializer(serializers.ModelSerializer):

    class Meta:
        model = Delay
        fields = (
            'estimated_end_date',
            'estimated_end_date_tsp',
            'duration',
        )

    estimated_end_date_tsp = TimeStampField(
        source='estimated_end_date',
        read_only=True
    )


class NotificationsSerializer(serializers.ModelSerializer):

    class Meta:
        model = Notification
        fields = (
            'id',
            'text',
            'type',
            'task',
            'datetime',
            'datetime_tsp',
            'status',
            'author',
            'workflow'
        )

    workflow = serializers.SerializerMethodField()
    task = serializers.SerializerMethodField()
    datetime_tsp = TimeStampField(source='datetime', read_only=True)

    def get_workflow(self, instance):
        if instance.type == NotificationType.SYSTEM:
            return None
        elif instance.task.workflow:  # TODO fix in 2962
            return {
                'id': instance.task.workflow.id,
                'name': instance.task.workflow.name
            }

    def get_task(self, instance):
        if instance.type == NotificationType.SYSTEM:
            return None
        elif instance.task:  # TODO fix in 2962
            result = {
                'id': instance.task.id,
                'name': instance.task.name
            }
            if instance.type == NotificationType.DELAY_WORKFLOW:
                delay = (
                    instance.task.delay_set.active().first()
                    or instance.task.delay_set.order_by('-id').first()
                )
                result['delay'] = DelaySerializer(instance=delay).data
            elif instance.type == NotificationType.DUE_DATE_CHANGED:
                if instance.task.due_date:
                    result['due_date'] = instance.task.due_date.strftime(
                        datetime_format
                    )
                else:
                    result['due_date'] = None
        return result
