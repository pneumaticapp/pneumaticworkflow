import pytest
from pneumatic_backend.authentication.enums import AuthTokenType
from pneumatic_backend.processes.tests.fixtures import (
    create_test_user,
)
from pneumatic_backend.accounts.models import APIKey
from pneumatic_backend.authentication.tokens import PneumaticToken


pytestmark = pytest.mark.django_db


def test_signout__user_token__ok(api_client, mocker):

    # arrange
    user = create_test_user()
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
    expire_token_mock = mocker.patch(
        'pneumatic_backend.authentication.tokens.'
        'PneumaticToken.expire_token'
    )

    api_client.token_authenticate(user)

    # act
    response = api_client.post('/auth/signout')

    # assert
    assert response.status_code == 204
    token = response.request['HTTP_AUTHORIZATION'].split()[1]
    expire_token_mock.assert_called_once_with(token)


def test_signout__api_key__skip(api_client, mocker):

    # arrange
    user = create_test_user()
    expire_token_mock = mocker.patch(
        'pneumatic_backend.authentication.tokens.'
        'PneumaticToken.expire_token'
    )

    api_client.token_authenticate(user, token_type=AuthTokenType.API)

    # act
    response = api_client.post('/auth/signout')

    # assert
    assert response.status_code == 204
    expire_token_mock.assert_not_called()
