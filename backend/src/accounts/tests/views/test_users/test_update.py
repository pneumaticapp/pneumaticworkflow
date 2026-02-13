"""Tests for PUT /accounts/users/<id> (UsersViewSet.update)."""

from datetime import timedelta

import pytest
from django.utils import timezone

from src.accounts.enums import (
    BillingPlanType,
    Language,
    UserDateFormat,
    UserFirstDayWeek,
)
from src.accounts.messages import MSG_A_0036
from src.accounts.services.exceptions import UserServiceException
from src.accounts.services.user import UserService
from src.authentication.enums import AuthTokenType
from src.authentication.services.guest_auth import GuestJWTAuthService
from src.processes.models.workflows.task import TaskPerformer
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_guest,
    create_test_group,
    create_test_admin,
    create_test_not_admin,
    create_test_owner,
    create_test_workflow,
)
from src.utils.validation import ErrorCode


pytestmark = pytest.mark.django_db


def test_update__all_fields__ok(api_client, mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    target_user = create_test_not_admin(account=account)
    group = create_test_group(account=account, users=[owner])
    first_name = 'First'
    last_name = 'Last'
    password = 'some password'
    is_admin = False
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
        'src.accounts.services.user.UserService.partial_update',
        return_value=target_user,
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.put(
        f'/accounts/users/{target_user.id}',
        request_data,
    )

    # assert
    assert response.status_code == 200
    user_service_init_mock.assert_called_once_with(
        user=owner,
        instance=target_user,
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
    )
    data = response.data
    assert data['id'] == target_user.id
    assert data['email'] == target_user.email
    assert data['phone'] == target_user.phone
    assert data['photo'] == target_user.photo
    assert data['first_name'] == target_user.first_name
    assert data['last_name'] == target_user.last_name
    assert 'password' not in data
    assert 'raw_password' not in data
    assert data['type'] == target_user.type
    assert data['date_joined_tsp'] == target_user.date_joined.timestamp()
    assert data['is_admin'] == target_user.is_admin
    assert data['is_account_owner'] == target_user.is_account_owner
    assert data['language'] == target_user.language
    assert data['timezone'] == target_user.timezone
    assert data['date_fmt'] == UserDateFormat.API_USA_12
    assert data['date_fdw'] == target_user.date_fdw
    assert data['invite'] is None
    assert data['groups'] == []
    assert data['is_tasks_digest_subscriber'] == (
        target_user.is_tasks_digest_subscriber
    )
    assert data['is_digest_subscriber'] == (
        target_user.is_digest_subscriber
    )
    assert data['is_newsletters_subscriber'] == (
        target_user.is_newsletters_subscriber
    )
    assert data['is_special_offers_subscriber'] == (
        target_user.is_special_offers_subscriber
    )
    assert data['is_new_tasks_subscriber'] == (
        target_user.is_new_tasks_subscriber
    )
    assert data['is_complete_tasks_subscriber'] == (
        target_user.is_complete_tasks_subscriber
    )
    assert data['is_comments_mentions_subscriber'] == (
        target_user.is_comments_mentions_subscriber
    )


def test_update__only_required_fields__ok(api_client, mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    target_user = create_test_not_admin(account=account)
    first_name = 'Updated'
    user_service_init_mock = mocker.patch.object(
        UserService,
        attribute='__init__',
        return_value=None,
    )
    partial_update_mock = mocker.patch(
        'src.accounts.services.user.UserService.partial_update',
        return_value=target_user,
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.put(
        f'/accounts/users/{target_user.id}',
        data={'first_name': first_name},
    )

    # assert
    assert response.status_code == 200
    user_service_init_mock.assert_called_once_with(
        user=owner,
        instance=target_user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    partial_update_mock.assert_called_once_with(
        first_name=first_name,
    )
    assert response.data['id'] == target_user.id
    assert response.data['email'] == target_user.email


def test_update__account_owner_update_yourself__ok(api_client, mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    password = 'some password'
    user_service_init_mock = mocker.patch.object(
        UserService,
        attribute='__init__',
        return_value=None,
    )
    partial_update_mock = mocker.patch(
        'src.accounts.services.user.UserService.partial_update',
        return_value=owner,
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.put(
        f'/accounts/users/{owner.id}',
        data={'password': password},
    )

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
    )
    assert response.data['id'] == owner.id
    assert response.data['email'] == owner.email


def test_update__admin_update_account_owner_password__validation_error(
    api_client,
    mocker,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    user = create_test_admin(account=account)
    password = 'Updated'
    partial_update_mock = mocker.patch(
        'src.accounts.services.user.UserService.partial_update',
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.put(
        f'/accounts/users/{owner.id}',
        data={'password': password},
    )

    # assert
    assert response.status_code == 400
    partial_update_mock.assert_not_called()
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == MSG_A_0036


def test_update__admin_update_account_owner_email__validation_error(
    api_client,
    mocker,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    user = create_test_admin(account=account)
    email = 'new@email.com'
    partial_update_mock = mocker.patch(
        'src.accounts.services.user.UserService.partial_update',
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.put(
        f'/accounts/users/{owner.id}',
        data={'email': email},
    )

    # assert
    assert response.status_code == 400
    partial_update_mock.assert_not_called()
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == MSG_A_0036


@pytest.mark.parametrize('date_fmt', [
    ' ',
    '',
    'Bad Format',
    '%B %d, %Y, %I:%M%p',
])
def test_update__invalid_date_fmt__validation_error(
    api_client,
    mocker,
    date_fmt,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    target_user = create_test_not_admin(account=account)
    partial_update_mock = mocker.patch(
        'src.accounts.views.users.UserService.partial_update',
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.put(
        f'/accounts/users/{target_user.id}',
        data={'date_fmt': date_fmt},
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == f'"{date_fmt}" is not a valid choice.'
    assert response.data['details']['name'] == 'date_fmt'
    partial_update_mock.assert_not_called()


@pytest.mark.parametrize('date_fdw', [
    ' ',
    '',
    'Bad Format',
])
def test_update__invalid_date_fdw__validation_error(
    api_client,
    mocker,
    date_fdw,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    target_user = create_test_not_admin(account=account)
    partial_update_mock = mocker.patch(
        'src.accounts.views.users.UserService.partial_update',
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.put(
        f'/accounts/users/{target_user.id}',
        data={'date_fdw': date_fdw},
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == f'"{date_fdw}" is not a valid choice.'
    assert response.data['details']['name'] == 'date_fdw'
    partial_update_mock.assert_not_called()


def test_update__invalid_photo__validation_error(api_client, mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    target_user = create_test_not_admin(account=account)
    invalid_url = 'invalid_url'
    partial_update_mock = mocker.patch(
        'src.accounts.views.users.UserService.partial_update',
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.put(
        f'/accounts/users/{target_user.id}',
        data={'photo': invalid_url},
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == 'Enter a valid URL.'
    assert response.data['details']['name'] == 'photo'
    assert response.data['details']['reason'] == 'Enter a valid URL.'
    partial_update_mock.assert_not_called()


@pytest.mark.parametrize('language', Language.EURO_VALUES)
def test_update__euro_languages__ok(
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
    target_user = create_test_not_admin(account=account)
    user_service_init_mock = mocker.patch.object(
        UserService,
        attribute='__init__',
        return_value=None,
    )
    partial_update_mock = mocker.patch(
        'src.accounts.services.user.UserService.partial_update',
        return_value=target_user,
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.put(
        f'/accounts/users/{target_user.id}',
        data={'language': language},
    )

    # assert
    assert response.status_code == 200
    assert response.data['language'] == target_user.language
    user_service_init_mock.assert_called_once_with(
        user=owner,
        instance=target_user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    partial_update_mock.assert_called_once_with(
        language=language,
    )


@pytest.mark.parametrize('language', Language.EURO_VALUES)
def test_update__system_euro_language_not_allow_ru__validation_error(
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
    target_user = create_test_not_admin(account=account)
    partial_update_mock = mocker.patch(
        'src.accounts.views.users.UserService.partial_update',
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.put(
        f'/accounts/users/{target_user.id}',
        data={'language': Language.ru},
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == (
        f'"{Language.ru}" is not a valid choice.'
    )
    assert response.data['details']['name'] == 'language'
    partial_update_mock.assert_not_called()


@pytest.mark.parametrize('language', Language.VALUES)
def test_update__system_ru_language_allow_all__ok(
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
    target_user = create_test_not_admin(account=account)
    user_service_init_mock = mocker.patch.object(
        UserService,
        attribute='__init__',
        return_value=None,
    )
    partial_update_mock = mocker.patch(
        'src.accounts.services.user.UserService.partial_update',
        return_value=target_user,
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.put(
        f'/accounts/users/{target_user.id}',
        data={'language': language},
    )

    # assert
    assert response.status_code == 200
    assert response.data['language'] == target_user.language
    user_service_init_mock.assert_called_once_with(
        user=owner,
        instance=target_user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    partial_update_mock.assert_called_once_with(
        language=language,
    )


def test_update__unsupported_language__validation_error(api_client, mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    target_user = create_test_not_admin(account=account)
    language = 'po'
    partial_update_mock = mocker.patch(
        'src.accounts.views.users.UserService.partial_update',
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.put(
        f'/accounts/users/{target_user.id}',
        data={'language': language},
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == (
        f'"{language}" is not a valid choice.'
    )
    assert response.data['details']['name'] == 'language'
    partial_update_mock.assert_not_called()


def test_update__invalid_timezone__validation_error(api_client, mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    target_user = create_test_not_admin(account=account)
    invalid_tz = 'Invalid/Zone'
    partial_update_mock = mocker.patch(
        'src.accounts.views.users.UserService.partial_update',
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.put(
        f'/accounts/users/{target_user.id}',
        data={'timezone': invalid_tz},
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == f'"{invalid_tz}" is not a valid choice.'
    assert response.data['details']['name'] == 'timezone'
    partial_update_mock.assert_not_called()


def test_update__not_authenticated__unauthorized(api_client, mocker):

    # arrange
    account = create_test_account()
    target_user = create_test_not_admin(account=account)
    partial_update_mock = mocker.patch(
        'src.accounts.views.users.UserService.partial_update',
    )

    # act
    response = api_client.put(
        f'/accounts/users/{target_user.id}',
        data={'first_name': 'Updated'},
    )

    # assert
    assert response.status_code == 401
    partial_update_mock.assert_not_called()


def test_update__guest__permission_denied(api_client, mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    guest = create_test_guest(account=account)
    workflow = create_test_workflow(
        owner,
        tasks_count=1,
    )
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
    target_user = create_test_not_admin(account=account)
    partial_update_mock = mocker.patch(
        'src.accounts.views.users.UserService.partial_update',
    )

    # act
    response = api_client.put(
        f'/accounts/users/{target_user.id}',
        data={'first_name': 'Updated'},
        **{'X-Guest-Authorization': str_token},
    )

    # assert
    assert response.status_code == 403
    partial_update_mock.assert_not_called()


def test_update__guest_update_yourself__permission_denied(api_client, mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    guest = create_test_guest(account=account)
    workflow = create_test_workflow(
        owner,
        tasks_count=1,
    )
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
        'src.accounts.views.users.UserService.partial_update',
    )
    api_client.token_authenticate(guest)

    # act
    response = api_client.put(
        f'/accounts/users/{guest.id}',
        data={'password': 'new_password'},
        **{'X-Guest-Authorization': str_token},
    )

    # assert
    assert response.status_code == 403
    partial_update_mock.assert_not_called()


def test_update__expired_subscription__permission_denied(
    api_client,
    mocker,
):

    # arrange
    account = create_test_account(
        plan=BillingPlanType.UNLIMITED,
        plan_expiration=timezone.now() - timedelta(days=1),
    )
    owner = create_test_owner(account=account)
    target_user = create_test_not_admin(account=account)
    partial_update_mock = mocker.patch(
        'src.accounts.views.users.UserService.partial_update',
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.put(
        f'/accounts/users/{target_user.id}',
        data={'first_name': 'Updated'},
    )

    # assert
    assert response.status_code == 403
    partial_update_mock.assert_not_called()


def test_update__no_billing_plan__permission_denied(api_client, mocker):

    # arrange
    account = create_test_account(plan=None)
    owner = create_test_owner(account=account)
    target_user = create_test_not_admin(account=account)
    partial_update_mock = mocker.patch(
        'src.accounts.views.users.UserService.partial_update',
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.put(
        f'/accounts/users/{target_user.id}',
        data={'first_name': 'Updated'},
    )

    # assert
    assert response.status_code == 403
    partial_update_mock.assert_not_called()


def test_update__not_admin__permission_denied(
    api_client,
    mocker,
):

    # arrange
    account = create_test_account()
    create_test_owner(account=account)
    not_admin = create_test_not_admin(account=account)
    target_user = create_test_not_admin(
        account=account,
        email='target@example.com',
    )
    partial_update_mock = mocker.patch(
        'src.accounts.views.users.UserService.partial_update',
    )
    api_client.token_authenticate(not_admin)

    # act
    response = api_client.put(
        f'/accounts/users/{target_user.id}',
        data={'first_name': 'Updated'},
    )

    # assert
    assert response.status_code == 403
    partial_update_mock.assert_not_called()


def test_update__service_raise_exception__validation_error(
    api_client,
    mocker,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    target_user = create_test_not_admin(account=account)
    error_message = 'Service error'
    partial_update_mock = mocker.patch(
        'src.accounts.views.users.UserService.partial_update',
        side_effect=UserServiceException(message=error_message),
    )
    user_service_init_mock = mocker.patch.object(
        UserService,
        attribute='__init__',
        return_value=None,
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.put(
        f'/accounts/users/{target_user.id}',
        data={'first_name': 'Updated'},
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == error_message
    user_service_init_mock.assert_called_once_with(
        user=owner,
        instance=target_user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    partial_update_mock.assert_called_once()


def test_update__email_integer_type__validation_error(api_client, mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    target_user = create_test_not_admin(account=account)
    partial_update_mock = mocker.patch(
        'src.accounts.views.users.UserService.partial_update',
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.put(
        f'/accounts/users/{target_user.id}',
        data={'email': 123},
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    partial_update_mock.assert_not_called()


def test_update__is_admin_non_boolean_type__validation_error(
    api_client,
    mocker,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    target_user = create_test_not_admin(account=account)
    partial_update_mock = mocker.patch(
        'src.accounts.views.users.UserService.partial_update',
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.put(
        f'/accounts/users/{target_user.id}',
        data={'is_admin': [1]},
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    partial_update_mock.assert_not_called()


def test_update__first_name_integer_type__ok(
    api_client,
    mocker,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    target_user = create_test_not_admin(account=account)
    first_name = 123
    user_service_init_mock = mocker.patch.object(
        UserService,
        attribute='__init__',
        return_value=None,
    )
    partial_update_mock = mocker.patch(
        'src.accounts.views.users.UserService.partial_update',
        return_value=target_user,
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.put(
        f'/accounts/users/{target_user.id}',
        data={'first_name': first_name},
    )

    # assert
    assert response.status_code == 200
    user_service_init_mock.assert_called_once_with(
        user=owner,
        instance=target_user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    partial_update_mock.assert_called_once_with(
        first_name=str(first_name),
    )


def test_update__last_name_integer_type__ok(
    api_client,
    mocker,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    target_user = create_test_not_admin(account=account)
    last_name = 123
    user_service_init_mock = mocker.patch.object(
        UserService,
        attribute='__init__',
        return_value=None,
    )
    partial_update_mock = mocker.patch(
        'src.accounts.views.users.UserService.partial_update',
        return_value=target_user,
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.put(
        f'/accounts/users/{target_user.id}',
        data={'last_name': 123},
    )

    # assert
    assert response.status_code == 200
    user_service_init_mock.assert_called_once_with(
        user=owner,
        instance=target_user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    partial_update_mock.assert_called_once_with(
        last_name=str(last_name),
    )


def test_update__phone_integer_type__ok(api_client, mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    target_user = create_test_not_admin(account=account)
    phone = 123
    user_service_init_mock = mocker.patch.object(
        UserService,
        attribute='__init__',
        return_value=None,
    )
    partial_update_mock = mocker.patch(
        'src.accounts.views.users.UserService.partial_update',
        return_value=target_user,
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.put(
        f'/accounts/users/{target_user.id}',
        data={'phone': 123},
    )

    # assert
    assert response.status_code == 200
    user_service_init_mock.assert_called_once_with(
        user=owner,
        instance=target_user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    partial_update_mock.assert_called_once_with(
        phone=str(phone),
    )


def test_update__photo_integer_type__validation_error(api_client, mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    target_user = create_test_not_admin(account=account)
    partial_update_mock = mocker.patch(
        'src.accounts.views.users.UserService.partial_update',
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.put(
        f'/accounts/users/{target_user.id}',
        data={'photo': 123},
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    partial_update_mock.assert_not_called()


def test_update__groups_non_list_type__validation_error(api_client, mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    target_user = create_test_not_admin(account=account)
    partial_update_mock = mocker.patch(
        'src.accounts.views.users.UserService.partial_update',
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.put(
        f'/accounts/users/{target_user.id}',
        data={'groups': 'not_a_list'},
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    partial_update_mock.assert_not_called()


def test_update__first_name_exceeds_max__validation_error(
    api_client,
    mocker,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    target_user = create_test_not_admin(account=account)
    long_name = 'x' * 151
    partial_update_mock = mocker.patch(
        'src.accounts.views.users.UserService.partial_update',
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.put(
        f'/accounts/users/{target_user.id}',
        data={'first_name': long_name},
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    partial_update_mock.assert_not_called()


def test_update__last_name_exceeds_max__validation_error(
    api_client,
    mocker,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    target_user = create_test_not_admin(account=account)
    long_name = 'y' * 151
    partial_update_mock = mocker.patch(
        'src.accounts.views.users.UserService.partial_update',
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.put(
        f'/accounts/users/{target_user.id}',
        data={'last_name': long_name},
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    partial_update_mock.assert_not_called()


def test_update__phone_exceeds_max__validation_error(api_client, mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    target_user = create_test_not_admin(account=account)
    long_phone = '1' * 33
    partial_update_mock = mocker.patch(
        'src.accounts.views.users.UserService.partial_update',
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.put(
        f'/accounts/users/{target_user.id}',
        data={'phone': long_phone},
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    partial_update_mock.assert_not_called()


def test_update__photo_exceeds_max__validation_error(api_client, mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    target_user = create_test_not_admin(account=account)
    long_photo = 'https://x.co/' + 'a' * 1015
    partial_update_mock = mocker.patch(
        'src.accounts.views.users.UserService.partial_update',
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.put(
        f'/accounts/users/{target_user.id}',
        data={'photo': long_photo},
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    partial_update_mock.assert_not_called()


def test_update__harmful_chars_in_name__ok(api_client, mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    target_user = create_test_not_admin(account=account)
    first_name = '<script>alert(1)</script>'
    user_service_init_mock = mocker.patch.object(
        UserService,
        attribute='__init__',
        return_value=None,
    )
    partial_update_mock = mocker.patch(
        'src.accounts.services.user.UserService.partial_update',
        return_value=target_user,
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.put(
        f'/accounts/users/{target_user.id}',
        data={
            'first_name': first_name,
        },
    )

    # assert
    assert response.status_code == 200
    user_service_init_mock.assert_called_once_with(
        user=owner,
        instance=target_user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    partial_update_mock.assert_called_once_with(
        first_name=first_name,
    )


def test_update__sql_like_input_in_field__no_execution(api_client, mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    target_user = create_test_not_admin(account=account)
    sql_like = "' OR 1=1--"
    user_service_init_mock = mocker.patch.object(
        UserService,
        attribute='__init__',
        return_value=None,
    )
    partial_update_mock = mocker.patch(
        'src.accounts.services.user.UserService.partial_update',
        return_value=target_user,
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.put(
        f'/accounts/users/{target_user.id}',
        data={'first_name': sql_like},
    )

    # assert
    assert response.status_code == 200
    user_service_init_mock.assert_called_once_with(
        user=owner,
        instance=target_user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    partial_update_mock.assert_called_once_with(
        first_name=sql_like,
    )


def test_update__another_account_user__not_found(api_client, mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)

    another_account = create_test_account()
    another_user = create_test_admin(account=another_account)
    new_password = 'new_password'
    user_service_init_mock = mocker.patch.object(
        UserService,
        attribute='__init__',
        return_value=None,
    )
    partial_update_mock = mocker.patch(
        'src.accounts.services.user.UserService.partial_update',
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.put(
        f'/accounts/users/{another_user.id}',
        data={'password': new_password},
    )

    # assert
    assert response.status_code == 404
    user_service_init_mock.assert_not_called()
    partial_update_mock.assert_not_called()


def test_partial_update__only_required_fields__ok(api_client, mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    target_user = create_test_not_admin(account=account)
    email = 'new@email.com'
    user_service_init_mock = mocker.patch.object(
        UserService,
        attribute='__init__',
        return_value=None,
    )
    partial_update_mock = mocker.patch(
        'src.accounts.services.user.UserService.partial_update',
        return_value=target_user,
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.patch(
        f'/accounts/users/{target_user.id}',
        data={'email': email},
    )

    # assert
    assert response.status_code == 200
    user_service_init_mock.assert_called_once_with(
        user=owner,
        instance=target_user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    partial_update_mock.assert_called_once_with(
        email=email,
    )
    assert response.data['id'] == target_user.id
    assert response.data['email'] == target_user.email
