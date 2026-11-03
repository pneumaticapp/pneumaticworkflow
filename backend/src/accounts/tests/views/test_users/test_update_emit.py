import pytest

from src.accounts.messages import MSG_A_0055
from src.authentication.enums import AuthTokenType
from src.payment.stripe.service import StripeService
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_group,
    create_test_not_admin,
    create_test_owner,
)
from src.utils.validation import ErrorCode

pytestmark = pytest.mark.django_db


def test_update__name_changed__audit_update_kwargs(
    mocker,
    identify_mock,
    api_client,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    target = create_test_not_admin(
        account=account,
        first_name='Old',
    )
    send_user_updated_mock = mocker.patch(
        'src.accounts.services.user.send_user_updated_notification.delay',
    )
    user_updated_mock = mocker.patch(
        'src.accounts.services.user.AuditEventService.user_updated',
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.put(
        f'/accounts/users/{target.id}',
        data={'first_name': 'New', 'last_name': target.last_name},
        format='json',
    )

    # assert
    assert response.status_code == 200
    user_updated_mock.assert_called_once_with(
        user=owner,
        auth_type=AuthTokenType.USER,
        target=target,
        update_kwargs={'first_name': 'New', 'last_name': target.last_name},
        user_groups=None,
        subordinates=None,
        is_password_set=False,
    )
    identify_mock.assert_called_once_with(target)
    send_user_updated_mock.assert_called_once_with(
        logging=account.log_api_requests,
        account_id=account.id,
        user_data=mocker.ANY,
    )


def test_update__same_values__audit_update_kwargs(
    mocker,
    identify_mock,
    api_client,
):

    """ A request that arrived is an update, whatever it sent. """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    target = create_test_not_admin(account=account)
    group = create_test_group(
        account=account,
        users=[target],
    )
    send_user_updated_mock = mocker.patch(
        'src.accounts.services.user.send_user_updated_notification.delay',
    )
    user_updated_mock = mocker.patch(
        'src.accounts.services.user.AuditEventService.user_updated',
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.put(
        f'/accounts/users/{target.id}',
        data={
            'first_name': target.first_name,
            'last_name': target.last_name,
            'phone': target.phone,
            'is_admin': False,
            'groups': [group.id],
        },
        format='json',
    )

    # assert
    assert response.status_code == 200
    user_updated_mock.assert_called_once_with(
        user=owner,
        auth_type=AuthTokenType.USER,
        target=target,
        update_kwargs={
            'first_name': target.first_name,
            'last_name': target.last_name,
            'phone': target.phone,
            'is_admin': False,
        },
        user_groups=[group.id],
        subordinates=None,
        is_password_set=False,
    )
    identify_mock.assert_called_once_with(target)
    send_user_updated_mock.assert_called_once_with(
        logging=account.log_api_requests,
        account_id=account.id,
        user_data=mocker.ANY,
    )


def test_update__groups_changed__audit_user_groups(
    mocker,
    identify_mock,
    api_client,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    target = create_test_not_admin(account=account)
    create_test_group(
        account=account,
        name='old',
        users=[target],
    )
    new_group_1 = create_test_group(
        account=account,
        name='new 1',
    )
    new_group_2 = create_test_group(
        account=account,
        name='new 2',
    )
    send_user_updated_mock = mocker.patch(
        'src.accounts.services.user.send_user_updated_notification.delay',
    )
    user_updated_mock = mocker.patch(
        'src.accounts.services.user.AuditEventService.user_updated',
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.put(
        f'/accounts/users/{target.id}',
        data={'groups': [new_group_2.id, new_group_1.id]},
        format='json',
    )

    # assert
    assert response.status_code == 200
    user_updated_mock.assert_called_once_with(
        user=owner,
        auth_type=AuthTokenType.USER,
        target=target,
        update_kwargs={},
        user_groups=[new_group_2.id, new_group_1.id],
        subordinates=None,
        is_password_set=False,
    )
    identify_mock.assert_called_once_with(target)
    send_user_updated_mock.assert_called_once_with(
        logging=account.log_api_requests,
        account_id=account.id,
        user_data=mocker.ANY,
    )


def test_update__manager_changed__audit_manager(
    mocker,
    identify_mock,
    api_client,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    manager = create_test_not_admin(
        account=account,
        email='manager@test.test',
    )
    target = create_test_not_admin(account=account)
    send_user_updated_mock = mocker.patch(
        'src.accounts.services.user.send_user_updated_notification.delay',
    )
    user_updated_mock = mocker.patch(
        'src.accounts.services.user.AuditEventService.user_updated',
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.put(
        f'/accounts/users/{target.id}',
        data={'manager_id': manager.id},
        format='json',
    )

    # assert
    assert response.status_code == 200
    user_updated_mock.assert_called_once_with(
        user=owner,
        auth_type=AuthTokenType.USER,
        target=target,
        update_kwargs={'manager': manager},
        user_groups=None,
        subordinates=None,
        is_password_set=False,
    )
    identify_mock.assert_called_once_with(target)
    assert send_user_updated_mock.call_count == 2
    send_user_updated_mock.assert_has_calls([
        mocker.call(
            logging=False,
            account_id=account.id,
            user_data=mocker.ANY,
        ),
        mocker.call(
            logging=account.log_api_requests,
            account_id=account.id,
            user_data=mocker.ANY,
        ),
    ])


def test_update__subordinates_changed__audit_subordinates(
    mocker,
    identify_mock,
    api_client,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    target = create_test_not_admin(account=account)
    subordinate = create_test_not_admin(
        account=account,
        email='subordinate@test.test',
    )
    send_user_updated_mock = mocker.patch(
        'src.accounts.services.user.send_user_updated_notification.delay',
    )
    user_updated_mock = mocker.patch(
        'src.accounts.services.user.AuditEventService.user_updated',
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.put(
        f'/accounts/users/{target.id}',
        data={'subordinates_ids': [subordinate.id]},
        format='json',
    )

    # assert
    assert response.status_code == 200
    user_updated_mock.assert_called_once_with(
        user=owner,
        auth_type=AuthTokenType.USER,
        target=target,
        update_kwargs={},
        user_groups=None,
        subordinates=[subordinate],
        is_password_set=False,
    )
    identify_mock.assert_called_once_with(target)
    send_user_updated_mock.assert_called_once_with(
        logging=account.log_api_requests,
        account_id=account.id,
        user_data=mocker.ANY,
    )


def test_update__admin_granted__audit_is_admin(
    mocker,
    identify_mock,
    api_client,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    target = create_test_not_admin(account=account)
    send_user_updated_mock = mocker.patch(
        'src.accounts.services.user.send_user_updated_notification.delay',
    )
    user_updated_mock = mocker.patch(
        'src.accounts.services.user.AuditEventService.user_updated',
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.put(
        f'/accounts/users/{target.id}',
        data={'is_admin': True},
        format='json',
    )

    # assert
    assert response.status_code == 200
    target.refresh_from_db()
    assert target.is_admin is True
    user_updated_mock.assert_called_once_with(
        user=owner,
        auth_type=AuthTokenType.USER,
        target=target,
        update_kwargs={'is_admin': True},
        user_groups=None,
        subordinates=None,
        is_password_set=False,
    )
    identify_mock.assert_called_once_with(target)
    send_user_updated_mock.assert_called_once_with(
        logging=account.log_api_requests,
        account_id=account.id,
        user_data=mocker.ANY,
    )


def test_update__password_set_by_admin__audit_password_set(
    mocker,
    identify_mock,
    api_client,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    target = create_test_not_admin(account=account)
    send_user_updated_mock = mocker.patch(
        'src.accounts.services.user.send_user_updated_notification.delay',
    )
    user_updated_mock = mocker.patch(
        'src.accounts.services.user.AuditEventService.user_updated',
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.put(
        f'/accounts/users/{target.id}',
        data={'password': 'new strong password'},
        format='json',
    )

    # assert
    assert response.status_code == 200
    user_updated_mock.assert_called_once_with(
        user=owner,
        auth_type=AuthTokenType.USER,
        target=target,
        update_kwargs={},
        user_groups=None,
        subordinates=None,
        is_password_set=True,
    )
    identify_mock.assert_called_once_with(target)
    send_user_updated_mock.assert_called_once_with(
        logging=account.log_api_requests,
        account_id=account.id,
        user_data=mocker.ANY,
    )


def test_update__owner_sets_own_password__audit_password_set(
    mocker,
    identify_mock,
    api_client,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    stripe_service_init_mock = mocker.patch.object(
        StripeService,
        attribute='__init__',
        return_value=None,
    )
    update_customer_mock = mocker.patch(
        'src.payment.stripe.service.StripeService.update_customer',
    )
    send_user_updated_mock = mocker.patch(
        'src.accounts.services.user.send_user_updated_notification.delay',
    )
    user_updated_mock = mocker.patch(
        'src.accounts.services.user.AuditEventService.user_updated',
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.put(
        f'/accounts/users/{owner.id}',
        data={'password': 'new strong password'},
        format='json',
    )

    # assert
    assert response.status_code == 200
    user_updated_mock.assert_called_once_with(
        user=owner,
        auth_type=AuthTokenType.USER,
        target=owner,
        update_kwargs={},
        user_groups=None,
        subordinates=None,
        is_password_set=True,
    )
    identify_mock.assert_called_once_with(owner)
    stripe_service_init_mock.assert_called_once_with(
        user=owner,
        auth_type=AuthTokenType.USER,
        is_superuser=False,
    )
    update_customer_mock.assert_called_once_with()
    send_user_updated_mock.assert_called_once_with(
        logging=account.log_api_requests,
        account_id=account.id,
        user_data=mocker.ANY,
    )


def test_update__api_key_auth__audit_api_auth_type(
    mocker,
    identify_mock,
    api_client,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    target = create_test_not_admin(
        account=account,
        first_name='Old',
    )
    send_user_updated_mock = mocker.patch(
        'src.accounts.services.user.send_user_updated_notification.delay',
    )
    user_updated_mock = mocker.patch(
        'src.accounts.services.user.AuditEventService.user_updated',
    )
    api_client.token_authenticate(
        owner,
        token_type=AuthTokenType.API,
    )

    # act
    response = api_client.put(
        f'/accounts/users/{target.id}',
        data={'first_name': 'New'},
        format='json',
    )

    # assert
    assert response.status_code == 200
    user_updated_mock.assert_called_once_with(
        user=owner,
        auth_type=AuthTokenType.API,
        target=target,
        update_kwargs={'first_name': 'New'},
        user_groups=None,
        subordinates=None,
        is_password_set=False,
    )
    identify_mock.assert_called_once_with(target)
    send_user_updated_mock.assert_called_once_with(
        logging=account.log_api_requests,
        account_id=account.id,
        user_data=mocker.ANY,
    )


def test_update__service_exception__audit_not_called(
    mocker,
    identify_mock,
    api_client,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    target = create_test_not_admin(account=account)
    send_user_updated_mock = mocker.patch(
        'src.accounts.services.user.send_user_updated_notification.delay',
    )
    user_updated_mock = mocker.patch(
        'src.accounts.services.user.AuditEventService.user_updated',
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.put(
        f'/accounts/users/{target.id}',
        data={'first_name': 'New', 'manager_id': target.id},
        format='json',
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == str(MSG_A_0055)
    assert response.data['details'] == {}
    user_updated_mock.assert_not_called()
    identify_mock.assert_not_called()
    send_user_updated_mock.assert_not_called()


def test_update__validation_error__audit_not_called(
    mocker,
    identify_mock,
    api_client,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    target = create_test_not_admin(account=account)
    send_user_updated_mock = mocker.patch(
        'src.accounts.services.user.send_user_updated_notification.delay',
    )
    user_updated_mock = mocker.patch(
        'src.accounts.services.user.AuditEventService.user_updated',
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.put(
        f'/accounts/users/{target.id}',
        data={'first_name': 'New', 'photo': 'invalid_url'},
        format='json',
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == 'Enter a valid URL.'
    assert response.data['details']['name'] == 'photo'
    assert response.data['details']['reason'] == 'Enter a valid URL.'
    user_updated_mock.assert_not_called()
    identify_mock.assert_not_called()
    send_user_updated_mock.assert_not_called()
