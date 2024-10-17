from django.utils import timezone
from rest_framework.permissions import BasePermission
from pneumatic_backend.generics.permissions import BaseAuthPermission
from pneumatic_backend.accounts.messages import (
    MSG_A_0035,
    MSG_A_0036,
    MSG_A_0037,
    MSG_A_0038,
)
from pneumatic_backend.accounts.enums import BillingPlanType


class SubscriptionPermission(BaseAuthPermission):

    """ Active subscription required """

    def has_permission(self, request, view):
        return bool(
            self._user_is_authenticated(request)
            and request.user.account.is_subscribed
        )


class SubscribedToggleAdminPermission(SubscriptionPermission):

    message = MSG_A_0038


class ExpiredSubscriptionPermission(BaseAuthPermission):

    """ Disallow for expired subscription,
        but allow for free or unauthorized """

    message = MSG_A_0035

    def has_permission(self, request, view):
        user = request.user
        if self._user_is_authenticated(request):
            is_expired_subscription = (
                user.account.billing_plan in BillingPlanType.PAYMENT_PLANS and
                user.account.plan_expiration and
                user.account.plan_expiration < timezone.now()
            )
            return not is_expired_subscription
        return True


class AccountOwnerPermission(BaseAuthPermission):

    message = MSG_A_0036

    def has_permission(self, request, view):
        return bool(
            self._user_is_authenticated(request)
            and request.user.is_account_owner
        )


class UsersOverlimitedPermission(BasePermission):

    message = MSG_A_0037

    def has_permission(self, request, view):
        return not request.user.account.is_blocked


class UserIsAdminOrAccountOwner(BasePermission):

    def has_permission(self, request, view):
        return request.user.is_admin or request.user.is_account_owner


class MasterAccountPermission(BasePermission):

    def has_permission(self, request, view):
        account = request.user.account
        return (
            not account.is_tenant
            and account.is_subscribed
        )


class MasterAccountAccessPermission(BasePermission):

    def has_permission(self, request, view):
        tenant_pk = view.kwargs.get('pk')
        account = request.user.account
        return (
            not account.is_tenant
            and account.is_subscribed
            and account.tenants.filter(id=tenant_pk).exists()
        )


class DisallowForTenantPermission(BasePermission):

    def has_permission(self, request, view):
        return not request.user.account.is_tenant
