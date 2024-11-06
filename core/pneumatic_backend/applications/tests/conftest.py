import pytest
from django.contrib.auth import get_user_model
from pneumatic_backend.generics.tests.clients import PneumaticApiClient
from pneumatic_backend.accounts.models import Account


UserModel = get_user_model()


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


@pytest.fixture(autouse=True)
def session_mock(mocker):
    session = mocker.patch(
        'django.contrib.sessions.backends.cache.SessionStore',
    )
    session.return_value.session_key = 'test'
