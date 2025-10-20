from django.conf import settings
from rest_framework.permissions import BasePermission
from rest_framework.request import Request

from src.accounts.enums import UserType


class BaseAuthPermission(BasePermission):

    def _is_authenticated(self, request: Request) -> bool:
        return bool(
            request.user
            and request.user.is_authenticated,
        )

    def _user_is_authenticated(self, request: Request) -> bool:
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.type == UserType.USER,
        )


class IsAuthenticated(BaseAuthPermission):

    def has_permission(self, request, view):
        return self._is_authenticated(request)


class UserIsAuthenticated(BaseAuthPermission):

    def has_permission(self, request, view):
        return self._user_is_authenticated(request)


class StagingPermission(BasePermission):

    def has_permission(self, request, view):
        return settings.CONFIGURATION_CURRENT in {
            settings.CONFIGURATION_DEV,
            settings.CONFIGURATION_TESTING,
            settings.CONFIGURATION_STAGING,
        }
