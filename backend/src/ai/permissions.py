from django.conf import settings
from rest_framework.permissions import BasePermission

from src.ai.messages import MSG_AI_0002
from src.ai.providers import ai_performers_active


class AiPerformersEnabledPermission(BasePermission):

    message = MSG_AI_0002

    def has_permission(self, request, view):
        return ai_performers_active(request.user.account)


class AiPerformersDeployedPermission(BasePermission):

    """ Only the deployment-level flag: lets an account manage its
        provider connection (the thing that enables the feature)
        before the feature is enabled. """

    message = MSG_AI_0002

    def has_permission(self, request, view):
        return bool(settings.PROJECT_CONF['AI_PERFORMERS'])
