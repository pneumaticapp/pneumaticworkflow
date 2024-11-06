import pytest

from pneumatic_backend.accounts.models import Account, User
from pneumatic_backend.authentication.services import AuthService


class TestAuthService:

    @pytest.mark.django_db
    def test_get_jwt(self):
        account = Account.objects.create(name='Test Company')
        user = User.objects.create(
            account=account,
            email='test@pneumatic.app',
            phone='79999999999',
        )
        token = AuthService.get_auth_token(
            user=user,
            user_agent='',
            user_ip='0.0.0.0'
        )

        assert token
