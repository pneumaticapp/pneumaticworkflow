from django.conf import settings
from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from pneumatic_backend.accounts.enums import UserType
from pneumatic_backend.generics.messages import MSG_GE_0006


class BaseAuthPermission(BasePermission):

    def _is_authenticated(self, request: Request) -> bool:
        return bool(
            request.user
            and request.user.is_authenticated
        )

    def _user_is_authenticated(self, request: Request) -> bool:
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.type == UserType.USER
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


class PaymentCardPermission(BasePermission):

    message = MSG_GE_0006

    def has_permission(self, request, view):
        return request.user.account.payment_card_provided
