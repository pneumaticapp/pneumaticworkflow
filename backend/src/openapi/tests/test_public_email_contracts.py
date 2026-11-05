"""Signed email callbacks need business assertions to classify HTTP success."""

import pytest

from src.accounts.enums import UserStatus
from src.accounts.messages import MSG_A_0014
from src.accounts.tokens import (
    DigestUnsubscribeToken,
    TransferToken,
    UnsubscribeEmailToken,
)
from src.analysis.enums import MailoutType
from src.processes.tests.fixtures import (
    create_test_not_admin,
    create_test_owner,
)

pytestmark = pytest.mark.django_db


@pytest.mark.contract_success('get', '/accounts/digest/unsubscribe')
def test_digest_unsubscribe__real_signed_token__preference_changes(
    contract_api_client,
) -> None:
    owner = create_test_owner()
    token = str(DigestUnsubscribeToken.for_user(owner))
    assert owner.is_digest_subscriber is True

    response = contract_api_client.get(
        '/accounts/digest/unsubscribe', data={'token': token},
    )

    assert response.status_code == 200
    assert str(MSG_A_0014) in response.content.decode('utf-8')
    owner.refresh_from_db()
    assert owner.is_digest_subscriber is False


@pytest.mark.contract_success('get', '/accounts/emails/unsubscribe')
def test_email_unsubscribe__real_signed_token__preference_changes(
    contract_api_client,
) -> None:
    owner = create_test_owner()
    token = str(UnsubscribeEmailToken.create_token(
        user_id=owner.id, email_type=MailoutType.NEW_TASK,
    ))
    assert owner.is_new_tasks_subscriber is True

    response = contract_api_client.get(
        '/accounts/emails/unsubscribe', data={'token': token},
    )

    assert response.status_code == 200
    assert str(MSG_A_0014) in response.content.decode('utf-8')
    owner.refresh_from_db()
    assert owner.is_new_tasks_subscriber is False


@pytest.mark.contract_success('get', '/accounts/users/{id}/transfer')
def test_transfer__real_signed_token__membership_changes(
    contract_api_client, mocker,
) -> None:
    source_owner = create_test_owner()
    target_owner = create_test_owner(email='target-owner@example.test')
    old_user = create_test_not_admin(
        account=source_owner.account, email='transferred@example.test',
    )
    new_user = create_test_not_admin(
        account=target_owner.account, email=old_user.email,
        status=UserStatus.INVITED,
    )
    token = TransferToken.for_user_id(new_user.id)
    token['new_user_id'] = new_user.id
    token['prev_user_id'] = old_user.id
    # Keep state transitions real; replace only notification queue transport.
    for name in (
        'send_user_updated_notification', 'send_user_deleted_notification',
        'send_user_deactivated_notification',
    ):
        mocker.patch(f'src.notifications.tasks.{name}.delay')

    response = contract_api_client.get(
        f'/accounts/users/{new_user.id}/transfer', data={'token': str(token)},
    )

    assert response.status_code == 200
    assert target_owner.account.name in response.content.decode('utf-8')
    old_user.refresh_from_db()
    new_user.refresh_from_db()
    assert old_user.status == UserStatus.INACTIVE
    assert new_user.status == UserStatus.ACTIVE
    assert new_user.account_id == target_owner.account_id
