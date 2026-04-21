"""Tests for PUT /accounts/user (UserViewSet.put)."""

from datetime import timedelta

import pytest
from django.utils import timezone

from src.accounts.enums import (
    BillingPlanType,
    Language,
    UserDateFormat,
    UserFirstDayWeek,
)
from src.accounts.services.exceptions import UserServiceException
from src.accounts.services.user import UserService
from src.accounts.serializers.user import UserWebsocketSerializer
from src.accounts import messages
from src.authentication.enums import AuthTokenType
from src.authentication.services.guest_auth import GuestJWTAuthService
from src.processes.models.workflows.task import TaskPerformer
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_guest,
    create_test_group,
    create_test_owner,
    create_test_workflow,
    create_test_not_admin,
)
from src.utils.validation import ErrorCode

pytestmark = pytest.mark.django_db


def test_put__all_fields__ok(api_client, mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    group = create_test_group(account=account, users=[owner])
    first_name = 'First'
    last_name = 'Last'
    password = 'some password'
    is_admin = True
    photo = 'https://my.lovely.photo.jpg'
    phone = '79999999990'
    is_tasks_digest_subscriber = False
    is_digest_subscriber = False
    is_comments_mentions_subscriber = False
    is_new_tasks_subscriber = False
    is_complete_tasks_subscriber = False
    is_newsletters_subscriber = False
    is_special_offers_subscriber = False
    language = 'en'
    timezone_val = 'America/Anchorage'
    date_fmt = UserDateFormat.API_USA_24
    date_fdw = UserFirstDayWeek.THURSDAY
    groups = [group.id]
    request_data = {
        'first_name': first_name,
        'last_name': last_name,
        'password': password,
        'is_admin': is_admin,
        'photo': photo,
        'phone': phone,
        'is_tasks_digest_subscriber': is_tasks_digest_subscriber,
        'is_digest_subscriber': is_digest_subscriber,
        'is_comments_mentions_subscriber': is_comments_mentions_subscriber,
        'is_new_tasks_subscriber': is_new_tasks_subscriber,
        'is_complete_tasks_subscriber': is_complete_tasks_subscriber,
        'is_newsletters_subscriber': is_newsletters_subscriber,
        'is_special_offers_subscriber': is_special_offers_subscriber,
        'language': language,
        'timezone': timezone_val,
        'date_fmt': date_fmt,
        'date_fdw': date_fdw,
        'groups': groups,
    }
    user_service_init_mock = mocker.patch.object(
        UserService,
        attribute='__init__',
        return_value=None,
    )
    partial_update_mock = mocker.patch(
        'src.accounts.views.user.UserService.partial_update',
        return_value=owner,
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.put('/accounts/user', request_data)

    # assert
    assert response.status_code == 200
    user_service_init_mock.assert_called_once_with(
        user=owner,
        instance=owner,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    partial_update_mock.assert_called_once_with(
        first_name=first_name,
        last_name=last_name,
        raw_password=password,
        is_admin=is_admin,
        photo=photo,
        phone=phone,
        is_tasks_digest_subscriber=is_tasks_digest_subscriber,
        is_digest_subscriber=is_digest_subscriber,
        is_comments_mentions_subscriber=is_comments_mentions_subscriber,
        is_new_tasks_subscriber=is_new_tasks_subscriber,
        is_complete_tasks_subscriber=is_complete_tasks_subscriber,
        is_newsletters_subscriber=is_newsletters_subscriber,
        is_special_offers_subscriber=is_special_offers_subscriber,
        language=language,
        timezone=timezone_val,
        date_fmt=UserDateFormat.PY_USA_24,
        date_fdw=date_fdw,
        user_groups=groups,
        force_save=True,
    )
    data = response.data
    assert data['id'] == owner.id
    assert data['email'] == owner.email
    assert data['phone'] == owner.phone
    assert data['photo'] == owner.photo
    assert data['first_name'] == owner.first_name
    assert data['last_name'] == owner.last_name
    assert 'password' not in data
    assert 'raw_password' not in data
    assert data['type'] == owner.type
    assert data['date_joined_tsp'] == owner.date_joined.timestamp()
    assert data['is_admin'] == owner.is_admin
    assert data['is_account_owner'] == owner.is_account_owner
    assert data['language'] == owner.language
    assert data['timezone'] == owner.timezone
    assert data['date_fmt'] == UserDateFormat.API_USA_12
    assert data['date_fdw'] == owner.date_fdw
    assert data['invite'] is None
    assert data['groups'] == groups
    assert data['is_tasks_digest_subscriber'] == (
        owner.is_tasks_digest_subscriber
    )
    assert data['is_digest_subscriber'] == owner.is_digest_subscriber
    assert data['is_newsletters_subscriber'] == (
        owner.is_newsletters_subscriber
    )
    assert data['is_special_offers_subscriber'] == (
        owner.is_special_offers_subscriber
    )
    assert data['is_new_tasks_subscriber'] == owner.is_new_tasks_subscriber
    assert data['is_complete_tasks_subscriber'] == (
        owner.is_complete_tasks_subscriber
    )
    assert data['is_comments_mentions_subscriber'] == (
        owner.is_comments_mentions_subscriber
    )


def test_put__escalate_privileges__validation_error(api_client, mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    user = create_test_not_admin(account=account)
    user_service_init_mock = mocker.patch.object(
        UserService,
        attribute='__init__',
        return_value=None,
    )
    partial_update_mock = mocker.patch(
        'src.accounts.views.user.UserService.partial_update',
        return_value=owner,
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.put(
        path='/accounts/user',
        data={'is_admin': True},
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == str(messages.MSG_A_0046)
    user_service_init_mock.assert_not_called()
    partial_update_mock.assert_not_called()


def test_put__only_required_fields__ok(api_client, mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    first_name = 'Updated'
    request_data = {'first_name': first_name}
    user_service_init_mock = mocker.patch.object(
        UserService,
        attribute='__init__',
        return_value=None,
    )
    partial_update_mock = mocker.patch(
        'src.accounts.views.user.UserService.partial_update',
        return_value=owner,
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.put('/accounts/user', request_data)

    # assert
    assert response.status_code == 200
    user_service_init_mock.assert_called_once_with(
        user=owner,
        instance=owner,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    partial_update_mock.assert_called_once_with(
        first_name=first_name,
        force_save=True,
    )
    assert response.data['id'] == owner.id
    assert response.data['email'] == owner.email


def test_put__owner_updates_self_password__ok(api_client, mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    password = 'some password'
    request_data = {'password': password}
    user_service_init_mock = mocker.patch.object(
        UserService,
        attribute='__init__',
        return_value=None,
    )
    partial_update_mock = mocker.patch(
        'src.accounts.views.user.UserService.partial_update',
        return_value=owner,
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.put('/accounts/user', request_data)

    # assert
    assert response.status_code == 200
    user_service_init_mock.assert_called_once_with(
        user=owner,
        instance=owner,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    partial_update_mock.assert_called_once_with(
        raw_password=password,
        force_save=True,
    )
    assert response.data['id'] == owner.id
    assert response.data['email'] == owner.email


@pytest.mark.parametrize('date_fmt', [
    ' ',
    '',
    'Bad Format',
    '%B %d, %Y, %I:%M%p',
])
def test_put__invalid_date_fmt__validation_error(
    api_client,
    mocker,
    date_fmt,
):
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    partial_update_mock = mocker.patch(
        'src.accounts.views.user.UserService.partial_update',
    )
    api_client.token_authenticate(owner)
    request_data = {'date_fmt': date_fmt}

    # act
    response = api_client.put('/accounts/user', request_data)

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    msg = f'"{date_fmt}" is not a valid choice.'
    assert response.data['message'] == msg
    assert response.data['details']['name'] == 'date_fmt'
    partial_update_mock.assert_not_called()


@pytest.mark.parametrize('date_fdw', [
    ' ',
    '',
    'Bad Format',
])
def test_put__invalid_date_fdw__validation_error(
    api_client,
    mocker,
    date_fdw,
):
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    partial_update_mock = mocker.patch(
        'src.accounts.views.user.UserService.partial_update',
    )
    api_client.token_authenticate(owner)
    request_data = {'date_fdw': date_fdw}

    # act
    response = api_client.put('/accounts/user', request_data)

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    msg = f'"{date_fdw}" is not a valid choice.'
    assert response.data['message'] == msg
    assert response.data['details']['name'] == 'date_fdw'
    partial_update_mock.assert_not_called()


def test_put__invalid_photo__validation_error(api_client, mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    invalid_url = 'invalid_url'
    request_data = {'photo': invalid_url}
    partial_update_mock = mocker.patch(
        'src.accounts.views.user.UserService.partial_update',
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.put('/accounts/user', request_data)

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    url_msg = 'Enter a valid URL.'
    assert response.data['message'] == url_msg
    assert response.data['details']['name'] == 'photo'
    assert response.data['details']['reason'] == url_msg
    partial_update_mock.assert_not_called()


def test_put__not_authenticated__unauthorized(api_client, mocker):

    # arrange
    account = create_test_account()
    create_test_owner(account=account)
    partial_update_mock = mocker.patch(
        'src.accounts.views.user.UserService.partial_update',
    )
    first_name = 'Updated'
    request_data = {'first_name': first_name}

    # act
    response = api_client.put('/accounts/user', request_data)

    # assert
    assert response.status_code == 401
    partial_update_mock.assert_not_called()


def test_put__guest__permission_denied(api_client, mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    guest = create_test_guest(account=account)
    workflow = create_test_workflow(owner, tasks_count=1)
    task = workflow.tasks.first()
    TaskPerformer.objects.create(
        task_id=task.id,
        user_id=guest.id,
    )
    str_token = GuestJWTAuthService.get_str_token(
        task_id=task.id,
        user_id=guest.id,
        account_id=account.id,
    )
    partial_update_mock = mocker.patch(
        'src.accounts.views.user.UserService.partial_update',
    )
    first_name = 'Updated'
    request_data = {'first_name': first_name}

    # act
    response = api_client.put(
        '/accounts/user',
        request_data,
        **{'X-Guest-Authorization': str_token},
    )

    # assert
    assert response.status_code == 403
    partial_update_mock.assert_not_called()


def test_put__expired_subscription__permission_denied(
    api_client,
    mocker,
):

    # arrange
    account = create_test_account(
        plan=BillingPlanType.UNLIMITED,
        plan_expiration=timezone.now() - timedelta(days=1),
    )
    owner = create_test_owner(account=account)
    partial_update_mock = mocker.patch(
        'src.accounts.views.user.UserService.partial_update',
    )
    api_client.token_authenticate(owner)
    first_name = 'Updated'
    request_data = {'first_name': first_name}

    # act
    response = api_client.put('/accounts/user', request_data)

    # assert
    assert response.status_code == 403
    partial_update_mock.assert_not_called()


def test_put__no_billing_plan__permission_denied(api_client, mocker):

    # arrange
    account = create_test_account(plan=None)
    owner = create_test_owner(account=account)
    partial_update_mock = mocker.patch(
        'src.accounts.views.user.UserService.partial_update',
    )
    api_client.token_authenticate(owner)
    first_name = 'Updated'
    request_data = {'first_name': first_name}

    # act
    response = api_client.put('/accounts/user', request_data)

    # assert
    assert response.status_code == 403
    partial_update_mock.assert_not_called()


def test_put__service_raise_exception__validation_error(
    api_client,
    mocker,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    error_message = 'Service error'
    partial_update_mock = mocker.patch(
        'src.accounts.views.user.UserService.partial_update',
        side_effect=UserServiceException(message=error_message),
    )
    user_service_init_mock = mocker.patch.object(
        UserService,
        attribute='__init__',
        return_value=None,
    )
    api_client.token_authenticate(owner)
    first_name = 'Updated'
    request_data = {'first_name': first_name}

    # act
    response = api_client.put('/accounts/user', request_data)

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == error_message
    user_service_init_mock.assert_called_once_with(
        user=owner,
        instance=owner,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    partial_update_mock.assert_called_once_with(
        first_name=first_name,
        force_save=True,
    )


def test_put__unsupported_language__validation_error(api_client, mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    language = 'po'
    request_data = {'language': language}
    partial_update_mock = mocker.patch(
        'src.accounts.views.user.UserService.partial_update',
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.put('/accounts/user', request_data)

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    msg = f'"{language}" is not a valid choice.'
    assert response.data['message'] == msg
    assert response.data['details']['name'] == 'language'
    partial_update_mock.assert_not_called()


def test_put__invalid_timezone__validation_error(api_client, mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    invalid_tz = 'Invalid/Zone'
    request_data = {'timezone': invalid_tz}
    partial_update_mock = mocker.patch(
        'src.accounts.views.user.UserService.partial_update',
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.put('/accounts/user', request_data)

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    msg = f'"{invalid_tz}" is not a valid choice.'
    assert response.data['message'] == msg
    assert response.data['details']['name'] == 'timezone'
    partial_update_mock.assert_not_called()


@pytest.mark.parametrize('language', Language.EURO_VALUES)
def test_put__euro_languages__ok(
    api_client,
    mocker,
    language,
):

    # arrange
    settings_mock = mocker.patch(
        'src.accounts.serializers.user.settings',
    )
    settings_mock.LANGUAGE_CODE = language
    account = create_test_account()
    owner = create_test_owner(account=account)
    user_service_init_mock = mocker.patch.object(
        UserService,
        attribute='__init__',
        return_value=None,
    )
    partial_update_mock = mocker.patch(
        'src.accounts.views.user.UserService.partial_update',
        return_value=owner,
    )
    api_client.token_authenticate(owner)
    request_data = {'language': language}

    # act
    response = api_client.put('/accounts/user', request_data)

    # assert
    assert response.status_code == 200
    assert response.data['language'] == owner.language
    user_service_init_mock.assert_called_once_with(
        user=owner,
        instance=owner,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    partial_update_mock.assert_called_once_with(
        language=language,
        force_save=True,
    )


@pytest.mark.parametrize('language', Language.EURO_VALUES)
def test_put__system_euro_language_not_allow_ru__validation_error(
    api_client,
    mocker,
    language,
):

    # arrange
    settings_mock = mocker.patch(
        'src.accounts.serializers.user.settings',
    )
    settings_mock.LANGUAGE_CODE = language
    account = create_test_account()
    owner = create_test_owner(account=account)
    partial_update_mock = mocker.patch(
        'src.accounts.views.user.UserService.partial_update',
    )
    api_client.token_authenticate(owner)
    request_data = {'language': Language.ru}

    # act
    response = api_client.put('/accounts/user', request_data)

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    msg = f'"{Language.ru}" is not a valid choice.'
    assert response.data['message'] == msg
    assert response.data['details']['name'] == 'language'
    partial_update_mock.assert_not_called()


@pytest.mark.parametrize('language', Language.VALUES)
def test_put__system_ru_language_allow_all__ok(
    api_client,
    mocker,
    language,
):

    # arrange
    settings_mock = mocker.patch(
        'src.accounts.serializers.user.settings',
    )
    settings_mock.LANGUAGE_CODE = Language.ru
    account = create_test_account()
    owner = create_test_owner(account=account)
    user_service_init_mock = mocker.patch.object(
        UserService,
        attribute='__init__',
        return_value=None,
    )
    partial_update_mock = mocker.patch(
        'src.accounts.views.user.UserService.partial_update',
        return_value=owner,
    )
    api_client.token_authenticate(owner)
    request_data = {'language': language}

    # act
    response = api_client.put('/accounts/user', request_data)

    # assert
    assert response.status_code == 200
    assert response.data['language'] == owner.language
    user_service_init_mock.assert_called_once_with(
        user=owner,
        instance=owner,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    partial_update_mock.assert_called_once_with(
        language=language,
        force_save=True,
    )


def test_put__email_integer_type__validation_error(api_client, mocker):
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    partial_update_mock = mocker.patch(
        'src.accounts.views.user.UserService.partial_update',
    )
    api_client.token_authenticate(owner)
    request_data = {'email': 123}

    # act
    response = api_client.put('/accounts/user', request_data)

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    partial_update_mock.assert_not_called()


def test_put__is_admin_non_boolean_type__validation_error(
    api_client,
    mocker,
):
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    partial_update_mock = mocker.patch(
        'src.accounts.views.user.UserService.partial_update',
    )
    api_client.token_authenticate(owner)
    request_data = {'is_admin': [1]}

    # act
    response = api_client.put('/accounts/user', request_data)

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    partial_update_mock.assert_not_called()


def test_put__first_name_integer_type__ok(
    api_client,
    mocker,
):
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    first_name = 123
    request_data = {'first_name': first_name}
    user_service_init_mock = mocker.patch.object(
        UserService,
        attribute='__init__',
        return_value=None,
    )
    partial_update_mock = mocker.patch(
        'src.accounts.views.user.UserService.partial_update',
        return_value=owner,
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.put('/accounts/user', request_data)

    # assert
    assert response.status_code == 200
    user_service_init_mock.assert_called_once_with(
        user=owner,
        instance=owner,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    partial_update_mock.assert_called_once_with(
        first_name=str(first_name),
        force_save=True,
    )


def test_put__last_name_integer_type__ok(
    api_client,
    mocker,
):
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    last_name = 123
    request_data = {'last_name': last_name}
    user_service_init_mock = mocker.patch.object(
        UserService,
        attribute='__init__',
        return_value=None,
    )
    partial_update_mock = mocker.patch(
        'src.accounts.views.user.UserService.partial_update',
        return_value=owner,
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.put('/accounts/user', request_data)

    # assert
    assert response.status_code == 200
    user_service_init_mock.assert_called_once_with(
        user=owner,
        instance=owner,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    partial_update_mock.assert_called_once_with(
        last_name=str(last_name),
        force_save=True,
    )


def test_put__phone_integer_type__ok(api_client, mocker):
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    phone = 123
    request_data = {'phone': phone}
    user_service_init_mock = mocker.patch.object(
        UserService,
        attribute='__init__',
        return_value=None,
    )
    partial_update_mock = mocker.patch(
        'src.accounts.views.user.UserService.partial_update',
        return_value=owner,
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.put('/accounts/user', request_data)

    # assert
    assert response.status_code == 200
    user_service_init_mock.assert_called_once_with(
        user=owner,
        instance=owner,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    partial_update_mock.assert_called_once_with(
        phone=str(phone),
        force_save=True,
    )


def test_put__photo_integer_type__validation_error(api_client, mocker):
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    partial_update_mock = mocker.patch(
        'src.accounts.views.user.UserService.partial_update',
    )
    api_client.token_authenticate(owner)
    request_data = {'photo': 123}

    # act
    response = api_client.put('/accounts/user', request_data)

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    partial_update_mock.assert_not_called()


def test_put__groups_non_list_type__validation_error(api_client, mocker):
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    partial_update_mock = mocker.patch(
        'src.accounts.views.user.UserService.partial_update',
    )
    api_client.token_authenticate(owner)
    request_data = {'groups': 'not_a_list'}

    # act
    response = api_client.put('/accounts/user', request_data)

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    partial_update_mock.assert_not_called()


def test_put__first_name_exceeds_max__validation_error(
    api_client,
    mocker,
):
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    long_name = 'x' * 151
    request_data = {'first_name': long_name}
    partial_update_mock = mocker.patch(
        'src.accounts.views.user.UserService.partial_update',
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.put('/accounts/user', request_data)

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    partial_update_mock.assert_not_called()


def test_put__last_name_exceeds_max__validation_error(
    api_client,
    mocker,
):
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    long_name = 'y' * 151
    request_data = {'last_name': long_name}
    partial_update_mock = mocker.patch(
        'src.accounts.views.user.UserService.partial_update',
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.put('/accounts/user', request_data)

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    partial_update_mock.assert_not_called()


def test_put__phone_exceeds_max__validation_error(api_client, mocker):
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    long_phone = '1' * 33
    request_data = {'phone': long_phone}
    partial_update_mock = mocker.patch(
        'src.accounts.views.user.UserService.partial_update',
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.put('/accounts/user', request_data)

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    partial_update_mock.assert_not_called()


def test_put__photo_exceeds_max__validation_error(api_client, mocker):
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    long_photo = 'https://x.co/' + 'a' * 2040
    request_data = {'photo': long_photo}
    partial_update_mock = mocker.patch(
        'src.accounts.views.user.UserService.partial_update',
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.put('/accounts/user', request_data)

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    partial_update_mock.assert_not_called()


def test_put__harmful_chars_in_name__ok(api_client, mocker):
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    first_name = '<script>alert(1)</script>'
    request_data = {'first_name': first_name}
    user_service_init_mock = mocker.patch.object(
        UserService,
        attribute='__init__',
        return_value=None,
    )
    partial_update_mock = mocker.patch(
        'src.accounts.views.user.UserService.partial_update',
        return_value=owner,
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.put('/accounts/user', request_data)

    # assert
    assert response.status_code == 200
    user_service_init_mock.assert_called_once_with(
        user=owner,
        instance=owner,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    partial_update_mock.assert_called_once_with(
        first_name=first_name,
        force_save=True,
    )


def test_put__sql_like_input_in_field__no_execution(api_client, mocker):
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    sql_like = "' OR 1=1--"
    request_data = {'first_name': sql_like}
    user_service_init_mock = mocker.patch.object(
        UserService,
        attribute='__init__',
        return_value=None,
    )
    partial_update_mock = mocker.patch(
        'src.accounts.views.user.UserService.partial_update',
        return_value=owner,
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.put('/accounts/user', request_data)

    # assert
    assert response.status_code == 200
    user_service_init_mock.assert_called_once_with(
        user=owner,
        instance=owner,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    partial_update_mock.assert_called_once_with(
        first_name=sql_like,
        force_save=True,
    )


def test_put__manager_id_circular__validation_error(api_client):
    """PUT /accounts/user with manager_id that creates a cycle → 400.

    Scenario: manager.manager = user → setting user.manager = manager
    would create: user → manager → user (circular).
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    manager = create_test_not_admin(account=account)
    manager.manager = user
    manager.save(update_fields=('manager',))
    api_client.token_authenticate(user)

    # act
    response = api_client.put(
        '/accounts/user',
        {'manager_id': manager.id},
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == str(messages.MSG_A_0050)


def test_put__manager_id_self__validation_error(api_client):
    """PUT /accounts/user with manager_id pointing to self → 400."""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    api_client.token_authenticate(user)

    # act
    response = api_client.put(
        '/accounts/user',
        {'manager_id': user.id},
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == str(messages.MSG_A_0049)


def test_put__subordinates_circular__validation_error(api_client):
    """PUT /accounts/user with a subordinate that is an ancestor → 400.

    Scenario: user.manager = ancestor → assigning ancestor as
    subordinate of user would create a cycle.
    """

    # arrange
    account = create_test_account()
    ancestor = create_test_not_admin(account=account, email='anc@test.test')
    user = create_test_owner(account=account)
    user.manager = ancestor
    user.save(update_fields=('manager',))
    api_client.token_authenticate(user)

    # act
    response = api_client.put(
        '/accounts/user',
        {'subordinates_ids': [ancestor.id]},
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == str(messages.MSG_A_0050)


def test_put__manager_id_valid__ok(api_client, mocker):
    """PUT /accounts/user with a valid (non-circular) manager_id → 200."""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    manager = create_test_not_admin(account=account)
    user_service_init_mock = mocker.patch.object(
        UserService,
        attribute='__init__',
        return_value=None,
    )
    partial_update_mock = mocker.patch(
        'src.accounts.views.user.UserService.partial_update',
        return_value=user,
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.put(
        '/accounts/user',
        {'manager_id': manager.id},
    )

    # assert
    assert response.status_code == 200
    user_service_init_mock.assert_called_once_with(
        user=user,
        instance=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    partial_update_mock.assert_called_once_with(
        manager=manager,
        force_save=True,
    )


def test_put__remove_manager_id__ok(api_client, mocker):
    """PUT /accounts/user with manager_id: null removes the manager."""

    # arrange
    account = create_test_account()
    manager = create_test_not_admin(account=account)
    user = create_test_not_admin(
        account=account,
        email='target_to_remove@test.test',
    )
    user.manager = manager
    user.save(update_fields=('manager',))

    ws_mock = mocker.patch(
        'src.accounts.services.user.send_user_updated_notification.delay',
    )

    api_client.token_authenticate(user)

    # act
    response = api_client.put(
        '/accounts/user',
        {'manager_id': None},
    )

    # assert
    assert response.status_code == 200
    user.refresh_from_db()
    manager.refresh_from_db()
    assert user.manager is None

    assert ws_mock.call_count == 2
    ws_mock.assert_any_call(
        logging=False,
        account_id=account.id,
        user_data=UserWebsocketSerializer(manager).data,
    )
    ws_mock.assert_any_call(
        logging=account.log_api_requests,
        account_id=account.id,
        user_data=UserWebsocketSerializer(user).data,
    )


def test_put__without_manager_id_preserves_manager__ok(api_client, mocker):
    """PUT /accounts/user without manager_id preserves the manager."""

    # arrange
    account = create_test_account()
    manager = create_test_not_admin(account=account)
    user = create_test_not_admin(
        account=account,
        email='target_to_preserve@test.test',
    )
    user.manager = manager
    user.save(update_fields=('manager',))

    ws_mock = mocker.patch(
        'src.accounts.services.user.send_user_updated_notification.delay',
    )

    api_client.token_authenticate(user)

    # act
    response = api_client.put(
        '/accounts/user',
        {'first_name': 'NewName'},
    )

    # assert
    assert response.status_code == 200
    user.refresh_from_db()
    assert user.manager == manager
    assert user.first_name == 'NewName'
    ws_mock.assert_called_once_with(
        logging=account.log_api_requests,
        account_id=account.id,
        user_data=UserWebsocketSerializer(user).data,
    )
