import guardian.management
import pytest
from django.contrib.auth import get_user_model
from unittest.mock import Mock

from src.accounts.models import Account
from src.generics.tests.clients import PneumaticApiClient

UserModel = get_user_model()


def pytest_configure(config):
    guardian.management.create_anonymous_user = Mock()


def create_test_user(email='test@pneumatic.app', account=None):
    account = account or Account.objects.create(name='Test Company')
    return UserModel.objects.create(
        account=account,
        email=email,
        first_name='John',
        last_name='Doe',
        phone='79999999999',
        is_admin=True,
    )


@pytest.fixture
def api_client():
    return PneumaticApiClient(HTTP_USER_AGENT='Mozilla/5.0')
