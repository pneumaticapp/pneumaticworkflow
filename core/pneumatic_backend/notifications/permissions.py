from django.conf import settings
from rest_framework.permissions import BasePermission


class PushPermission(BasePermission):

    def has_permission(self, request, view):
        return settings.PROJECT_CONF['PUSH']
