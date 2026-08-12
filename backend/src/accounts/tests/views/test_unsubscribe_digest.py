import pytest
from django.conf import settings

from src.accounts.messages import MSG_A_0008, MSG_A_0014
from src.accounts.tokens import DigestUnsubscribeToken
from src.authentication.enums import AuthTokenType
from src.processes.tests.fixtures import create_test_owner

pytestmark = pytest.mark.django_db


def test_unsubscribe__ok(mocker, api_client):

    # arrange
    user = create_test_owner()
    token = str(DigestUnsubscribeToken.for_user(user))
    analysis_mock = mocker.patch(
        'src.accounts.views.unsubscribes.'
        'AnalyticService.users_digest',
    )

    # act
    response = api_client.get(
        '/accounts/digest/unsubscribe'
        f'?token={token}',
    )

    # assert
    expected = f"""
        <script>
            setTimeout("location.href = '{settings.FRONTEND_URL}';",3000);
        </script>
        {MSG_A_0014}
        """
    assert response.status_code == 200
    assert response.content.decode('utf-8') == expected
    user.refresh_from_db()
    assert user.is_digest_subscriber is False
    analysis_mock.assert_called_once_with(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )


def test_unsubscribe__incorrect_token__ok(api_client):

    # arrange
    user = create_test_owner()
    expected = f"""
        <script>
            setTimeout("location.href = '{settings.FRONTEND_URL}';",3000);
        </script>
        {MSG_A_0008}
        """

    # act
    response = api_client.get(
        '/accounts/digest/unsubscribe?token=12345',
    )

    # assert
    assert response.status_code == 200
    assert response.content.decode('utf-8') == expected
    user.refresh_from_db()
    assert user.is_digest_subscriber is True


def test_unsubscribe__no_token__ok(api_client):

    # arrange
    user = create_test_owner()
    expected = f"""
        <script>
            setTimeout("location.href = '{settings.FRONTEND_URL}';",3000);
        </script>
        {MSG_A_0008}
        """

    # act
    response = api_client.get(
        '/accounts/digest/unsubscribe',
    )

    # assert
    assert response.status_code == 200
    assert response.content.decode('utf-8') == expected
    user.refresh_from_db()
    assert user.is_digest_subscriber is True
