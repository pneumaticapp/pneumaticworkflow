"""Unit-tests for PneumaticTokenAuthentication."""
import pytest

from src.authentication.services.user_auth import PneumaticTokenAuthentication
from src.authentication.tokens import PneumaticToken
from src.processes.tests.fixtures import create_test_owner

pytestmark = pytest.mark.django_db


def test_authenticate__cache_hit__ok():

    # arrange
    user = create_test_owner()
    raw_key = PneumaticToken.create(user, for_api_key=False)
    auth_service = PneumaticTokenAuthentication()

    # act
    result = auth_service.authenticate_credentials(raw_key)

    # assert
    assert result is not None
    assert result[0].id == user.id


def test_authenticate__cache_miss__none(mocker):

    # arrange
    token_data_mock = mocker.patch(
        'src.authentication.tokens.PneumaticToken.data',
        return_value=None,
    )
    auth_service = PneumaticTokenAuthentication()

    # act
    result = auth_service.authenticate_credentials('no_such_token')

    # assert
    assert result is None
    token_data_mock.assert_called_once_with('no_such_token')
