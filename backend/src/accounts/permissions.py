from django.utils import timezone
from rest_framework.permissions import BasePermission
from src.generics.permissions import BaseAuthPermission
from src.accounts.messages import (
    MSG_A_0035,
    MSG_A_0036,
    MSG_A_0037,
    MSG_A_0041,
)
from src.accounts.enums import BillingPlanType


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


class BillingPlanPermission(BaseAuthPermission):

    message = MSG_A_0041

    def has_permission(self, request, view):
        if request.user:
            return request.user.account.billing_plan is not None
        return True


class AccountOwnerPermission(BaseAuthPermission):

    message = MSG_A_0036

    def has_permission(self, request, view):
        return bool(
            self._user_is_authenticated(request)
            and request.user.is_account_owner,
        )


class UsersOverlimitedPermission(BasePermission):

    message = MSG_A_0037

    def has_permission(self, request, view):
        account = request.user.account
        if account.billing_plan == BillingPlanType.PREMIUM:
            return account.max_users >= account.total_active_users
        return True


class UserIsAdminOrAccountOwner(BasePermission):

    def has_permission(self, request, view):
        return request.user.is_admin or request.user.is_account_owner


class MasterAccountPermission(BasePermission):

    def has_permission(self, request, view):
        return not request.user.account.is_tenant


class MasterAccountAccessPermission(BasePermission):

    def has_permission(self, request, view):
        try:
            tenant_pk = view.kwargs.get('pk')
        except (ValueError, TypeError):
            return False
        else:
            account = request.user.account
            return (
                not account.is_tenant
                and account.tenants.filter(id=tenant_pk).exists()
            )


class DisallowForTenantPermission(BasePermission):

    def has_permission(self, request, view):
        return not request.user.account.is_tenant
