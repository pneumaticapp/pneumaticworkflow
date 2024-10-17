# pylint: disable=redefined-outer-name
import pytest
from datetime import timedelta
from django.utils import timezone
from django.conf import settings
from pneumatic_backend.accounts.models import User, Account
from pneumatic_backend.accounts.serializers.accounts import (
    AccountPlanSerializer
)
from pneumatic_backend.accounts.serializers.onboarding import (
    FinishSignUpSerializer,
)
from pneumatic_backend.accounts.enums import (
    BillingPlanType
)
from pneumatic_backend.accounts.tests.fixtures import (
    create_test_owner,
)

pytestmark = pytest.mark.django_db


class TestFinishSignUpSerializer:
    test_serializer = FinishSignUpSerializer

    def test_update_all(self):
        email = 'test@pneumatic.app'
        account = Account.objects.create(name='')
        user = User.objects.create(
            account=account,
            email=email,
        )
        serializer = self.test_serializer()
        data = {
            'company_name': 'Test Company',
            'phone': '88005553535',
        }
        serializer.update(user, data)

        assert account.name == data['company_name']
        assert user.phone == data['phone']

    def test_update_company(self):
        email = 'test@pneumatic.app'
        account = Account.objects.create(name='')
        user = User.objects.create(
            account=account,
            email=email,
        )
        serializer = self.test_serializer()
        data = {
            'company_name': 'Test Company',
            'phone': '',
        }
        serializer.update(user, data)

        assert account.name == data['company_name']
        assert user.phone is None


class TestAccountPlanSerializer:

    def test_unsubscribed(self):
        user = create_test_owner()
        account = user.account
        serializer = AccountPlanSerializer(account)
        data = serializer.data

        assert data['max_templates'] == settings.PAYWALL_MAX_ACTIVE_TEMPLATES

    def test_subscribed(self):
        user = create_test_owner()
        account = user.account
        account.plan_expiration = (timezone.now() + timedelta(days=1))
        account.billing_plan = BillingPlanType.PREMIUM
        account.save()
        serializer = AccountPlanSerializer(account)
        data = serializer.data

        assert data['max_templates'] is None
