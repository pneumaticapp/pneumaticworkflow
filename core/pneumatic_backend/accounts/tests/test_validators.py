import pytest
from django.conf import settings
from django.contrib.auth import get_user_model

from pneumatic_backend.accounts.enums import BillingPlanType
from pneumatic_backend.accounts.tests.fixtures import (
    create_test_account,
    create_test_user,
    create_test_workflow,
    create_invited_user,
)
from pneumatic_backend.accounts.validators import (
    PayWallValidator,
    user_is_performer,
)


UserModel = get_user_model()


class TestPayWallValidators:

    @pytest.mark.django_db
    def test_active_templates_limit_not_reached(self):
        account = create_test_account()
        result = PayWallValidator.is_active_templates_limit_reached(account)

        assert result is False

    @pytest.mark.django_db
    def test_active_templates_limit_reached(self):
        account = create_test_account()
        account.active_templates = settings.PAYWALL_MAX_ACTIVE_TEMPLATES
        account.save()
        result = PayWallValidator.is_active_templates_limit_reached(account)

        assert result is True

    @pytest.mark.django_db
    def test_active_templates_account_subscsribed(self):
        account = create_test_account()
        account.billing_plan = BillingPlanType.PREMIUM
        account.active_templates = settings.PAYWALL_MAX_ACTIVE_TEMPLATES
        account.save()
        result = PayWallValidator.is_active_templates_limit_reached(account)

        assert result is False


class TestCheckPerformer:

    @pytest.mark.django_db
    def test_user_performer_not_empty(self):
        user = create_test_user()
        create_test_workflow(user.account, user)
        result = user_is_performer(user)
        assert result is True

    @pytest.mark.django_db
    def test_user_performer_empty(self):
        user = create_test_user(is_account_owner=True)
        create_test_workflow(user.account)
        result = user_is_performer(user)
        assert result is False

    @pytest.mark.django_db
    def test_user_performer_other_user(self):
        user = create_test_user()
        invited = create_invited_user(user)
        create_test_workflow(account=user.account, user=user)
        result = user_is_performer(invited)
        assert result is False
