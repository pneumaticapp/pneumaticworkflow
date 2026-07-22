"""Reusable OpenAPI response serializers (docs only)."""

from rest_framework import serializers

from src.authentication.enums import ResetPasswordStatus

from src.processes.serializers.workflows.task import (
    TaskSerializer,
)
from src.processes.serializers.workflows.workflow import (
    WorkflowDetailsSerializer,
)


class CountResponseSerializer(serializers.Serializer):
    count = serializers.IntegerField()


class AuthTokenResponseSerializer(serializers.Serializer):
    token = serializers.CharField()


class CaptchaResponseSerializer(serializers.Serializer):
    show_captcha = serializers.BooleanField()


class UserCountersSerializer(serializers.Serializer):
    tasks_count = serializers.IntegerField()


class ResetPasswordStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=ResetPasswordStatus.CHOICES)


class WebHookEventSerializer(serializers.Serializer):
    url = serializers.CharField(allow_null=True)
    event = serializers.CharField()


class WebHookEventUrlSerializer(serializers.Serializer):
    url = serializers.CharField(allow_null=True)


class WebhookHookSerializer(serializers.Serializer):
    event = serializers.CharField()
    id = serializers.IntegerField()
    target = serializers.URLField()


class TaskWebhookExampleSerializer(serializers.Serializer):
    hook = WebhookHookSerializer()
    task = TaskSerializer()


class WorkflowWebhookExampleSerializer(serializers.Serializer):
    hook = WebhookHookSerializer()
    workflow = WorkflowDetailsSerializer()
