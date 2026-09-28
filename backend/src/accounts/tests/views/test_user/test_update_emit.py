import pytest

from src.accounts.messages import MSG_A_0046
from src.authentication.enums import AuthTokenType
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_admin,
    create_test_not_admin,
    create_test_owner,
)
from src.utils.validation import ErrorCode

pytestmark = pytest.mark.django_db


def test_put__name_changed__audit_update_kwargs(
    mocker,
    identify_mock,
    api_client,
):

    # arrange
    account = create_test_account()
    create_test_owner(account=account)
    user = create_test_not_admin(
        account=account,
        last_name='Old',
    )
    send_user_updated_mock = mocker.patch(
        'src.accounts.services.user.send_user_updated_notification.delay',
    )
    user_updated_mock = mocker.patch(
        'src.accounts.services.user.AuditEventService.user_updated',
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.put(
        '/accounts/user',
        data={'first_name': user.first_name, 'last_name': 'New'},
        format='json',
    )

    # assert
    assert response.status_code == 200
    user_updated_mock.assert_called_once_with(
        user=user,
        auth_type=AuthTokenType.USER,
        target=user,
        update_kwargs={'first_name': user.first_name, 'last_name': 'New'},
        user_groups=None,
        subordinates=None,
        is_password_set=False,
    )
    identify_mock.assert_called_once_with(user)
    send_user_updated_mock.assert_called_once_with(
        logging=account.log_api_requests,
        account_id=account.id,
        user_data=mocker.ANY,
    )


def test_put__password_sent__audit_password_set(
    mocker,
    identify_mock,
    api_client,
):

    # arrange
    account = create_test_account()
    create_test_owner(account=account)
    user = create_test_not_admin(account=account)
    send_user_updated_mock = mocker.patch(
        'src.accounts.services.user.send_user_updated_notification.delay',
    )
    user_updated_mock = mocker.patch(
        'src.accounts.services.user.AuditEventService.user_updated',
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.put(
        '/accounts/user',
        data={'password': 'new strong password'},
        format='json',
    )

    # assert
    assert response.status_code == 200
    user_updated_mock.assert_called_once_with(
        user=user,
        auth_type=AuthTokenType.USER,
        target=user,
        update_kwargs={},
        user_groups=None,
        subordinates=None,
        is_password_set=True,
    )
    identify_mock.assert_called_once_with(user)
    send_user_updated_mock.assert_called_once_with(
        logging=account.log_api_requests,
        account_id=account.id,
        user_data=mocker.ANY,
    )


def test_put__admin_revokes_own_admin__audit_is_admin(
    mocker,
    identify_mock,
    api_client,
):

    # arrange
    account = create_test_account()
    create_test_owner(account=account)
    user = create_test_admin(account=account)
    send_user_updated_mock = mocker.patch(
        'src.accounts.services.user.send_user_updated_notification.delay',
    )
    user_updated_mock = mocker.patch(
        'src.accounts.services.user.AuditEventService.user_updated',
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.put(
        '/accounts/user',
        data={'is_admin': False},
        format='json',
    )

    # assert
    assert response.status_code == 200
    user.refresh_from_db()
    assert user.is_admin is False
    user_updated_mock.assert_called_once_with(
        user=user,
        auth_type=AuthTokenType.USER,
        target=user,
        update_kwargs={'is_admin': False},
        user_groups=None,
        subordinates=None,
        is_password_set=False,
    )
    identify_mock.assert_called_once_with(user)
    send_user_updated_mock.assert_called_once_with(
        logging=account.log_api_requests,
        account_id=account.id,
        user_data=mocker.ANY,
    )


def test_put__same_values__audit_update_kwargs(
    mocker,
    identify_mock,
    api_client,
):

    """ A request that arrived is an update, whatever it sent. """

    # arrange
    account = create_test_account()
    create_test_owner(account=account)
    user = create_test_not_admin(account=account)
    send_user_updated_mock = mocker.patch(
        'src.accounts.services.user.send_user_updated_notification.delay',
    )
    user_updated_mock = mocker.patch(
        'src.accounts.services.user.AuditEventService.user_updated',
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.put(
        '/accounts/user',
        data={
            'first_name': user.first_name,
            'last_name': user.last_name,
            'phone': user.phone,
            'language': user.language,
            'timezone': user.timezone,
        },
        format='json',
    )

    # assert
    assert response.status_code == 200
    user_updated_mock.assert_called_once_with(
        user=user,
        auth_type=AuthTokenType.USER,
        target=user,
        update_kwargs={
            'first_name': user.first_name,
            'last_name': user.last_name,
            'phone': user.phone,
            'language': user.language,
            'timezone': user.timezone,
        },
        user_groups=None,
        subordinates=None,
        is_password_set=False,
    )
    identify_mock.assert_called_once_with(user)
    send_user_updated_mock.assert_called_once_with(
        logging=account.log_api_requests,
        account_id=account.id,
        user_data=mocker.ANY,
    )


def test_put__escalate_privileges__audit_not_called(
    mocker,
    identify_mock,
    api_client,
):

    # arrange
    account = create_test_account()
    create_test_owner(account=account)
    user = create_test_not_admin(account=account)
    send_user_updated_mock = mocker.patch(
        'src.accounts.services.user.send_user_updated_notification.delay',
    )
    user_updated_mock = mocker.patch(
        'src.accounts.services.user.AuditEventService.user_updated',
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.put(
        '/accounts/user',
        data={'is_admin': True},
        format='json',
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == str(MSG_A_0046)
    assert response.data['details']['name'] == 'is_admin'
    assert response.data['details']['reason'] == str(MSG_A_0046)
    user_updated_mock.assert_not_called()
    identify_mock.assert_not_called()
    send_user_updated_mock.assert_not_called()
