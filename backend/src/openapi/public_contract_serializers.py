"""OpenAPI request projections for public endpoints, never runtime input."""

from rest_framework import serializers

from src.processes.serializers.workflows.external.workflow import (
    SecuredExternalWorkflowCreateSerializer,
)


class PublicTemplateRunRequestSerializer(
    SecuredExternalWorkflowCreateSerializer,
):
    captcha = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        write_only=True,
        help_text=(
            'reCAPTCHA response. Required only when GET /templates/public '
            'returns show_captcha=true for this visitor. Otherwise ignored '
            'and may be omitted, empty or null.'
        ),
    )
