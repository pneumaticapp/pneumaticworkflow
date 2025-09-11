from django.conf import settings
from rest_framework.permissions import BasePermission
from src.services.messages import MSG_SV_0001


class AIPermission(BasePermission):

    message = MSG_SV_0001

    def has_permission(self, request, view):
        return settings.PROJECT_CONF['AI']
