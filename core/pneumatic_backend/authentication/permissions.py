from django.conf import settings
from rest_framework.permissions import BasePermission
from pneumatic_backend.generics.permissions import BaseAuthPermission
from pneumatic_backend.authentication.enums import AuthTokenType


class NoAuthApiPermission(BasePermission):

    def has_permission(self, request, view):
        if not settings.PRIVATE_API_CHECK_IP:
            return True

        remote_addr = request.META['HTTP_REMOTE_ADDR']
        return remote_addr in settings.PRIVATE_API_IP_WHITELIST


class PrivateApiPermission(BasePermission):
    def has_permission(self, request, view):
        if not settings.PRIVATE_API_CHECK_IP:
            return True

        if request.token_type == AuthTokenType.API:
            return False

        remote_addr = request.META['HTTP_REMOTE_ADDR']
        return remote_addr in settings.PRIVATE_API_IP_WHITELIST


class IsSuperuserPermission(BaseAuthPermission):

    def has_permission(self, request, view):
        return bool(
            self._user_is_authenticated(request)
            and request.user.is_superuser
        )


class StaffPermission(BaseAuthPermission):

    def has_permission(self, request, view):
        return bool(
            self._user_is_authenticated(request)
            and request.user.is_staff
        )


class GoogleAuthPermission(BasePermission):

    def has_permission(self, request, view):
        return settings.PROJECT_CONF['GOOGLE_AUTH']


class MSAuthPermission(BasePermission):

    def has_permission(self, request, view):
        return settings.PROJECT_CONF['MS_AUTH']


class Auth0Permission(BasePermission):

    def has_permission(self, request, view):
        return settings.PROJECT_CONF['SSO_AUTH']


class SignupPermission(BasePermission):

    def has_permission(self, request, view):
        return settings.PROJECT_CONF['SIGNUP']
