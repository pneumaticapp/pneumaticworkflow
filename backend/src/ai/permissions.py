from django.conf import settings
from rest_framework.permissions import BasePermission

from src.ai.messages import MSG_AI_0002


class AiPerformersEnabledPermission(BasePermission):

    message = MSG_AI_0002

    def has_permission(self, request, view):
        return bool(
            settings.PROJECT_CONF['AI_PERFORMERS']
            and request.user.account.ai_performers_enabled,
        )
