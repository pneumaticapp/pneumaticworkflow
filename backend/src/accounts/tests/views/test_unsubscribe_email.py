import pytest
from django.conf import settings

from src.accounts.messages import MSG_A_0008, MSG_A_0014
from src.accounts.tokens import UnsubscribeEmailToken
from src.analysis.enums import MailoutType
from src.processes.tests.fixtures import create_test_owner

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    'email_type', [
        MailoutType.TASKS_DIGEST,
        MailoutType.WF_DIGEST,
        MailoutType.COMMENTS,
        MailoutType.NEW_TASK,
    ],
)
def test_unsubscribe__ok(api_client, email_type):

    # arrange
    user = create_test_owner()
    token = str(UnsubscribeEmailToken.create_token(
        user_id=user.id,
        email_type=email_type,
    ))
    expected = f"""
        <script>
            setTimeout("location.href = '{settings.FRONTEND_URL}';",3000);
        </script>
        {MSG_A_0014}
        """

    # act
    response = api_client.get(
        '/accounts/emails/unsubscribe'
        f'?token={token}',
    )

    # assert
    assert response.status_code == 200
    assert response.content.decode('utf-8') == expected
    user.refresh_from_db()
    attribute = MailoutType.MAP[email_type]
    assert getattr(user, attribute, None) is False


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
        '/accounts/emails/unsubscribe?token=12345',
    )

    # assert
    assert response.status_code == 200
    assert response.content.decode('utf-8') == expected
    user.refresh_from_db()
    assert user.is_digest_subscriber is True
    assert user.is_tasks_digest_subscriber is True
    assert user.is_comments_mentions_subscriber is True
    assert user.is_new_tasks_subscriber is True
    assert user.is_complete_tasks_subscriber is True
    assert user.is_newsletters_subscriber is True
    assert user.is_special_offers_subscriber is True


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
        '/accounts/emails/unsubscribe',
    )

    # assert
    assert response.status_code == 200
    assert response.content.decode('utf-8') == expected
    user.refresh_from_db()
    assert user.is_digest_subscriber is True
    assert user.is_tasks_digest_subscriber is True
    assert user.is_comments_mentions_subscriber is True
    assert user.is_new_tasks_subscriber is True
    assert user.is_complete_tasks_subscriber is True
    assert user.is_newsletters_subscriber is True
    assert user.is_special_offers_subscriber is True
