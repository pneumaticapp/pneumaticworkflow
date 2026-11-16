import pytest

from src.accounts.messages import (
    MSG_A_0008,
    MSG_A_0014,
)
from src.accounts.tokens import UnsubscribeEmailToken
from src.analysis.enums import MailoutType
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_not_admin,
    create_test_owner,
)

pytestmark = pytest.mark.django_db


def test_unsubscribe__valid_token__audit_user_unsubscribed(
    mocker,
    api_client,
):

    # arrange
    account = create_test_account()
    create_test_owner(account=account)
    user = create_test_not_admin(account=account)
    token = str(
        UnsubscribeEmailToken.create_token(
            user_id=user.id,
            email_type=MailoutType.TASKS_DIGEST,
        ),
    )
    user_unsubscribed_mock = mocker.patch(
        'src.accounts.views.unsubscribes.AuditEventService.'
        'user_unsubscribed',
    )

    # act
    response = api_client.get(f'/accounts/emails/unsubscribe?token={token}')

    # assert
    assert response.status_code == 200
    assert str(MSG_A_0014) in response.content.decode()
    user.refresh_from_db()
    assert user.is_tasks_digest_subscriber is False
    user_unsubscribed_mock.assert_called_once_with(
        user=user,
        email_type=MailoutType.MAP[MailoutType.TASKS_DIGEST],
    )


def test_unsubscribe__already_unsubscribed__audit_user_unsubscribed(
    mocker,
    api_client,
):

    # arrange
    account = create_test_account()
    create_test_owner(account=account)
    user = create_test_not_admin(account=account)
    user.is_tasks_digest_subscriber = False
    user.save(update_fields=['is_tasks_digest_subscriber'])
    token = str(
        UnsubscribeEmailToken.create_token(
            user_id=user.id,
            email_type=MailoutType.TASKS_DIGEST,
        ),
    )
    user_unsubscribed_mock = mocker.patch(
        'src.accounts.views.unsubscribes.AuditEventService.'
        'user_unsubscribed',
    )

    # act
    response = api_client.get(f'/accounts/emails/unsubscribe?token={token}')

    # assert
    assert response.status_code == 200
    assert str(MSG_A_0014) in response.content.decode()
    user.refresh_from_db()
    assert user.is_tasks_digest_subscriber is False
    user_unsubscribed_mock.assert_called_once_with(
        user=user,
        email_type=MailoutType.MAP[MailoutType.TASKS_DIGEST],
    )


def test_unsubscribe__incorrect_token__audit_not_called(
    mocker,
    api_client,
):

    # arrange
    user = create_test_owner()
    user_unsubscribed_mock = mocker.patch(
        'src.accounts.views.unsubscribes.AuditEventService.'
        'user_unsubscribed',
    )

    # act
    response = api_client.get('/accounts/emails/unsubscribe?token=12345')

    # assert
    assert response.status_code == 200
    assert str(MSG_A_0008) in response.content.decode()
    user.refresh_from_db()
    assert user.is_tasks_digest_subscriber is True
    user_unsubscribed_mock.assert_not_called()


def test_unsubscribe__no_token__audit_not_called(
    mocker,
    api_client,
):

    # arrange
    user = create_test_owner()
    user_unsubscribed_mock = mocker.patch(
        'src.accounts.views.unsubscribes.AuditEventService.'
        'user_unsubscribed',
    )

    # act
    response = api_client.get('/accounts/emails/unsubscribe')

    # assert
    assert response.status_code == 200
    assert str(MSG_A_0008) in response.content.decode()
    user.refresh_from_db()
    assert user.is_tasks_digest_subscriber is True
    user_unsubscribed_mock.assert_not_called()
