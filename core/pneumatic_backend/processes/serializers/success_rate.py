from rest_framework import serializers
from rest_framework.fields import IntegerField, CharField, FloatField


class WorkflowSuccessRateSerializer(serializers.Serializer):
    id = IntegerField(read_only=True)
    name = CharField(read_only=True)
    success_rate = FloatField(read_only=True, allow_null=True)
