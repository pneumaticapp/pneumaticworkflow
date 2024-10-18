from rest_framework import serializers


class WorkflowDurationByTemplateSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(read_only=True)
    avg_workflow_duration = serializers.DurationField(
        read_only=True,
        allow_null=True,
    )
