from datetime import timedelta

import pytest
from django.utils import timezone

from pneumatic_backend.accounts.enums import (
    BillingPlanType,
)
from pneumatic_backend.accounts.permissions import (
    ExpiredSubscriptionPermission,
    UsersOverlimitedPermission,
)
from pneumatic_backend.processes.tests.fixtures import (
    create_test_user,
    create_test_account
)

pytestmark = pytest.mark.django_db


class TestExpiredSubscriptionPermission:

    @pytest.mark.parametrize('plan', BillingPlanType.PAYMENT_PLANS)
    def test__expired_subscription__return_false(
        self,
        plan,
        mocker,
    ):
        # arrange
        user = create_test_user()
        user.account.billing_plan = plan
        user.account.plan_expiration = timezone.now() - timedelta(seconds=1)
        user.account.save()

        permission = ExpiredSubscriptionPermission()

        request = mocker.Mock(user=user)
        view = mocker.Mock()

        # act & assert
        assert permission.has_permission(request, view) is False

    @pytest.mark.parametrize('plan', BillingPlanType.PAYMENT_PLANS)
    def test__has_not_expired_subscription__return_true(
        self,
        plan,
        mocker,
    ):
        # arrange

        user = create_test_user()
        user.account.billing_plan = plan
        user.account.plan_expiration = timezone.now() + timedelta(days=1)
        user.account.save()

        permission = ExpiredSubscriptionPermission()

        request = mocker.Mock(user=user)
        view = mocker.Mock()

        # act & assert
        assert permission.has_permission(request, view) is True

    def test__free_plan__return_true(
        self,
        mocker,
    ):
        # arrange

        user = create_test_user()
        user.account.billing_plan = BillingPlanType.FREEMIUM
        user.account.plan_expiration = None
        user.account.save()

        permission = ExpiredSubscriptionPermission()

        request = mocker.Mock(user=user)
        view = mocker.Mock()

        # act & assert
        assert permission.has_permission(request, view) is True


class TestUsersOverlimitedPermission:

    def test__overlimit__permission_denied(self, mocker):

        # arrange
        account = create_test_account()
        mocker.patch(
            'pneumatic_backend.accounts.models.Account.is_blocked',
            True
        )
        user = create_test_user(account=account)
        request = mocker.Mock(user=user)
        view = mocker.Mock()
        permission = UsersOverlimitedPermission()

        # act
        result = permission.has_permission(request, view)

        # assert
        assert result is False

    def test__limit_not_reached__ok(self, mocker):

        # arrange
        account = create_test_account()
        mocker.patch(
            'pneumatic_backend.accounts.models.Account.is_blocked',
            False
        )
        user = create_test_user(account=account)

        request = mocker.Mock(user=user)
        view = mocker.Mock()
        permission = UsersOverlimitedPermission()

        # act
        result = permission.has_permission(request, view)

        # assert
        assert result is True
