from typing import Optional
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from pneumatic_backend.authentication.enums import AuthTokenType
from pneumatic_backend.accounts.models import APIKey
from pneumatic_backend.authentication.tokens import PneumaticToken


UserModel = get_user_model()


class PneumaticApiClient(APIClient):

    """ Allow use token auth for requests """

    def token_authenticate(
        self,
        user: UserModel,
        token_type: AuthTokenType = AuthTokenType.USER,
        user_agent: str = 'Firefox',
        user_ip: str = '192.168.0.1',
        token: Optional[str] = None
    ):

        if not token:
            if token_type == AuthTokenType.API:
                token = PneumaticToken.create(
                    user=user,
                    for_api_key=True
                )
                APIKey.objects.create(
                    user=user,
                    account=user.account,
                    name='Token for API',
                    key=token,
                )
            elif token_type == AuthTokenType.USER:
                token = PneumaticToken.create(
                    user=user,
                    for_api_key=False,
                    user_agent=user_agent,
                    user_ip=user_ip
                )
            else:
                raise Exception('Unsupported token type.')
        self.credentials(
            HTTP_AUTHORIZATION=f'Bearer {token}',
            HTTP_USER_AGENT=user_agent,
            HTTP_X_REAL_IP=user_ip,
            REMOTE_ADDR=user_ip,
        )
        return token
