"""Tests for POST /accounts/users (UsersViewSet.create)."""

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
from src.authentication.enums import AuthTokenType
from src.authentication.services.guest_auth import GuestJWTAuthService
from src.processes.models.workflows.task import TaskPerformer
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_guest,
    create_test_group,
    create_test_not_admin,
    create_test_owner, create_test_workflow,
)
from src.utils.validation import ErrorCode

pytestmark = pytest.mark.django_db


def test_create__all_fields__ok(api_client, mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    user = create_test_not_admin(account=account)
    group = create_test_group(account=account, users=[owner])
    email = 'some@email.com'
    request_data = {
        'email': email,
        'first_name': 'First',
        'last_name': 'Last',
        'password': 'some password',
        'is_admin': False,
        'photo': 'https://my.lovely.photo.jpg',
        'phone': '79999999990',
        'is_tasks_digest_subscriber': False,
        'is_digest_subscriber': False,
        'is_comments_mentions_subscriber': False,
        'is_new_tasks_subscriber': False,
        'is_complete_tasks_subscriber': False,
        'is_newsletters_subscriber': False,
        'is_special_offers_subscriber': False,
        'language': 'en',
        'timezone': 'America/Anchorage',
        'date_fmt': UserDateFormat.API_USA_24,
        'date_fdw': UserFirstDayWeek.THURSDAY,
        'groups': [group.id],
    }
    user_service_init_mock = mocker.patch.object(
        UserService,
        attribute='__init__',
        return_value=None,
    )
    create_mock = mocker.patch(
        'src.accounts.services.user.UserService.create',
        return_value=user,
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.post('/accounts/users', request_data)

    # assert
    assert response.status_code == 200
    user_service_init_mock.assert_called_once_with(
        user=owner,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    create_mock.assert_called_once_with(**{
        'account': account,
        'email': email,
        'first_name': 'First',
        'last_name': 'Last',
        'raw_password': 'some password',
        'is_admin': False,
        'photo': 'https://my.lovely.photo.jpg',
        'phone': '79999999990',
        'is_tasks_digest_subscriber': False,
        'is_digest_subscriber': False,
        'is_comments_mentions_subscriber': False,
        'is_new_tasks_subscriber': False,
        'is_complete_tasks_subscriber': False,
        'is_newsletters_subscriber': False,
        'is_special_offers_subscriber': False,
        'language': 'en',
        'timezone': 'America/Anchorage',
        'date_fmt': UserDateFormat.PY_USA_24,
        'date_fdw': UserFirstDayWeek.THURSDAY,
        'user_groups': [group.id],
    })
    data = response.data
    assert data['id'] == user.id
    assert data['email'] == user.email
    assert data['phone'] == user.phone
    assert data['photo'] == user.photo
    assert data['first_name'] == user.first_name
    assert data['last_name'] == user.last_name
    assert 'password' not in data
    assert 'raw_password' not in data
    assert data['type'] == user.type
    assert data['date_joined_tsp'] == user.date_joined.timestamp()
    assert data['is_admin'] == user.is_admin
    assert data['is_account_owner'] == user.is_account_owner
    assert data['language'] == user.language
    assert data['timezone'] == user.timezone
    assert data['date_fmt'] == UserDateFormat.API_USA_12
    assert data['date_fdw'] == user.date_fdw
    assert data['invite'] is None
    assert data['groups'] == []
    assert data['is_tasks_digest_subscriber'] == (
        user.is_tasks_digest_subscriber
    )
    assert data['is_digest_subscriber'] == (
        user.is_digest_subscriber
    )
    assert data['is_newsletters_subscriber'] == (
        user.is_newsletters_subscriber
    )
    assert data['is_special_offers_subscriber'] == (
        user.is_special_offers_subscriber
    )
    assert data['is_new_tasks_subscriber'] == (
        user.is_new_tasks_subscriber
    )
    assert data['is_complete_tasks_subscriber'] == (
        user.is_complete_tasks_subscriber
    )
    assert data['is_comments_mentions_subscriber'] == (
        user.is_comments_mentions_subscriber
    )


def test_create__only_required_fields__ok(api_client, mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    email = 'minimal@email.com'
    user = create_test_not_admin(account=account, email=email)
    user_service_init_mock = mocker.patch.object(
        UserService,
        attribute='__init__',
        return_value=None,
    )
    create_mock = mocker.patch(
        'src.accounts.services.user.UserService.create',
        return_value=user,
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.post(
        '/accounts/users',
        data={'email': email},
    )

    # assert
    assert response.status_code == 200
    user_service_init_mock.assert_called_once_with(
        user=owner,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    create_mock.assert_called_once_with(
        account=account,
        email=email,
    )
    assert response.data['id'] == user.id
    assert response.data['email'] == user.email


@pytest.mark.parametrize('date_fmt', [
    ' ',
    '',
    'Bad Format',
    '%B %d, %Y, %I:%M%p',
])
def test_create__invalid_date_fmt__validation_error(
    api_client,
    mocker,
    date_fmt,
):

    # arrange
    owner = create_test_owner()
    create_mock = mocker.patch('src.accounts.views.users.UserService.create')
    email = 'some@email.com'
    api_client.token_authenticate(owner)

    # act
    response = api_client.post(
        '/accounts/users',
        data={'email': email, 'date_fmt': date_fmt},
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == f'"{date_fmt}" is not a valid choice.'
    assert response.data['details']['name'] == 'date_fmt'
    create_mock.assert_not_called()


@pytest.mark.parametrize('date_fdw', [
    ' ',
    '',
    'Bad Format',
])
def test_create__invalid_date_fdw__validation_error(
    api_client,
    mocker,
    date_fdw,
):

    # arrange
    owner = create_test_owner()
    email = 'some@email.com'
    create_mock = mocker.patch('src.accounts.views.users.UserService.create')
    api_client.token_authenticate(owner)

    # act
    response = api_client.post(
        '/accounts/users',
        data={'email': email, 'date_fdw': date_fdw},
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == f'"{date_fdw}" is not a valid choice.'
    assert response.data['details']['name'] == 'date_fdw'
    create_mock.assert_not_called()


def test_create__invalid_photo__validation_error(api_client, mocker):

    # arrange
    owner = create_test_owner()
    email = 'some@email.com'
    create_mock = mocker.patch('src.accounts.views.users.UserService.create')
    api_client.token_authenticate(owner)

    # act
    response = api_client.post(
        '/accounts/users',
        data={'email': email, 'photo': 'invalid_url'},
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == 'Enter a valid URL.'
    assert response.data['details']['name'] == 'photo'
    assert response.data['details']['reason'] == 'Enter a valid URL.'
    create_mock.assert_not_called()


@pytest.mark.parametrize('language', Language.EURO_VALUES)
def test_create__euro_languages__ok(
    api_client,
    mocker,
    language,
):

    # arrange
    settings_mock = mocker.patch(
        'src.accounts.serializers.user.settings',
    )
    email = 'some@email.com'
    settings_mock.LANGUAGE_CODE = language
    account = create_test_account()
    owner = create_test_owner(account=account)
    user = create_test_not_admin(account=account)
    user_service_init_mock = mocker.patch.object(
        UserService,
        attribute='__init__',
        return_value=None,
    )
    create_mock = mocker.patch(
        'src.accounts.services.user.UserService.create',
        return_value=user,
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.post(
        '/accounts/users',
        data={'email': email, 'language': language},
    )

    # assert
    assert response.status_code == 200
    user_service_init_mock.assert_called_once_with(
        user=owner,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    create_mock.assert_called_once_with(
        email=email,
        account=account,
        language=language,
    )


@pytest.mark.parametrize('language', Language.EURO_VALUES)
def test_create__system_euro_language_not_allow_ru__validation_error(
    api_client,
    mocker,
    language,
):

    # arrange
    settings_mock = mocker.patch(
        'src.accounts.serializers.user.settings',
    )
    settings_mock.LANGUAGE_CODE = language
    owner = create_test_owner()
    email = 'some@email.com'
    create_mock = mocker.patch('src.accounts.views.users.UserService.create')
    api_client.token_authenticate(owner)

    # act
    response = api_client.post(
        '/accounts/users',
        data={'email': email, 'language': Language.ru},
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == (
        f'"{Language.ru}" is not a valid choice.'
    )
    assert response.data['details']['name'] == 'language'
    create_mock.assert_not_called()


@pytest.mark.parametrize('language', Language.VALUES)
def test_create__system_ru_language_allow_all__ok(
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
    user = create_test_not_admin(account=account)
    email = 'some@email.com'
    user_service_init_mock = mocker.patch.object(
        UserService,
        attribute='__init__',
        return_value=None,
    )
    create_mock = mocker.patch(
        'src.accounts.services.user.UserService.create',
        return_value=user,
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.post(
        '/accounts/users',
        data={'email': email, 'language': language},
    )

    # assert
    assert response.status_code == 200
    user_service_init_mock.assert_called_once_with(
        user=owner,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    create_mock.assert_called_once_with(
        email=email,
        account=account,
        language=language,
    )


def test_create__unsupported_language__validation_error(api_client, mocker):

    # arrange
    owner = create_test_owner()
    create_mock = mocker.patch('src.accounts.views.users.UserService.create')
    api_client.token_authenticate(owner)
    language = 'po'
    email = 'some@email.com'

    # act
    response = api_client.post(
        '/accounts/users',
        data={'email': email, 'language': language},
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == (
        f'"{language}" is not a valid choice.'
    )
    assert response.data['details']['name'] == 'language'
    create_mock.assert_not_called()


def test_create__invalid_timezone__validation_error(api_client, mocker):

    # arrange
    owner = create_test_owner()
    create_mock = mocker.patch('src.accounts.views.users.UserService.create')
    email = 'some@email.com'
    timezone = 'Invalid/Zone'
    api_client.token_authenticate(owner)

    # act
    response = api_client.post(
        '/accounts/users',
        data={'email': email, 'timezone': timezone},
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == f'"{timezone}" is not a valid choice.'
    assert response.data['details']['name'] == 'timezone'
    create_mock.assert_not_called()


def test_create__not_authenticated__unauthorized(api_client, mocker):

    # arrange
    create_mock = mocker.patch('src.accounts.views.users.UserService.create')
    email = 'some@email.com'

    # act
    response = api_client.post(
        '/accounts/users',
        data={'email': email},
    )

    # assert
    assert response.status_code == 401
    create_mock.assert_not_called()


def test_create__guest__permission_denied(api_client, mocker):

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
    create_mock = mocker.patch('src.accounts.views.users.UserService.create')
    email = 'some@email.com'
    api_client.token_authenticate(guest)

    # act
    response = api_client.post(
        '/accounts/users',
        data={'email': email},
        **{'X-Guest-Authorization': str_token},
    )

    # assert
    assert response.status_code == 403
    create_mock.assert_not_called()


def test_create__expired_subscription__permission_denied(
    api_client,
    mocker,
):

    # arrange
    account = create_test_account(
        plan=BillingPlanType.UNLIMITED,
        plan_expiration=timezone.now() - timedelta(days=1),
    )
    owner = create_test_owner(account=account)
    create_mock = mocker.patch('src.accounts.views.users.UserService.create')
    email = 'some@email.com'
    api_client.token_authenticate(owner)

    # act
    response = api_client.post(
        '/accounts/users',
        data={'email': email},
    )

    # assert
    assert response.status_code == 403
    create_mock.assert_not_called()


def test_create__no_billing_plan__permission_denied(api_client, mocker):

    # arrange
    account = create_test_account(plan=None)
    owner = create_test_owner(account=account)
    email = 'some@email.com'
    create_mock = mocker.patch('src.accounts.views.users.UserService.create')
    api_client.token_authenticate(owner)

    # act
    response = api_client.post(
        '/accounts/users',
        data={'email': email},
    )

    # assert
    assert response.status_code == 403
    create_mock.assert_not_called()


def test_create__not_admin_nor_owner__permission_denied(api_client, mocker):

    # arrange
    account = create_test_account()
    create_test_owner(account=account)
    not_admin = create_test_not_admin(account=account)
    create_mock = mocker.patch('src.accounts.views.users.UserService.create')
    email = 'some@email.com'
    api_client.token_authenticate(not_admin)

    # act
    response = api_client.post(
        '/accounts/users',
        data={'email': email},
    )

    # assert
    assert response.status_code == 403
    create_mock.assert_not_called()


def test_create__service_raise_exception__validation_error(
    api_client,
    mocker,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    error_message = 'Service error'
    email = 'some@email.com'
    create_mock = mocker.patch(
        'src.accounts.views.users.UserService.create',
        side_effect=UserServiceException(message=error_message),
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.post(
        '/accounts/users',
        data={'email': email},
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == error_message
    create_mock.assert_called_once_with(
        account=account,
        email=email,
    )


def test_create__email_integer_type__validation_error(api_client, mocker):

    # arrange
    owner = create_test_owner()
    create_mock = mocker.patch('src.accounts.views.users.UserService.create')
    email = 123
    api_client.token_authenticate(owner)

    # act
    response = api_client.post(
        '/accounts/users',
        data={'email': email},
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    create_mock.assert_not_called()


def test_create__is_admin_non_boolean_type__validation_error(
    api_client,
    mocker,
):

    # arrange
    owner = create_test_owner()
    email = 'some@email.com'
    is_admin = [1]
    create_mock = mocker.patch('src.accounts.views.users.UserService.create')
    api_client.token_authenticate(owner)

    # act
    response = api_client.post(
        '/accounts/users',
        data={'email': email, 'is_admin': is_admin},
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    create_mock.assert_not_called()


def test_create__first_name_exceeds_max__validation_error(api_client, mocker):

    # arrange
    owner = create_test_owner()
    create_mock = mocker.patch('src.accounts.views.users.UserService.create')
    email = 'some@email.com'
    first_name = 'x' * 151
    api_client.token_authenticate(owner)

    # act
    response = api_client.post(
        '/accounts/users',
        data={'email': email, 'first_name': first_name},
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    create_mock.assert_not_called()


def test_create__last_name_exceeds_max__validation_error(api_client, mocker):

    # arrange
    owner = create_test_owner()
    create_mock = mocker.patch('src.accounts.views.users.UserService.create')
    email = 'some@email.com'
    last_name = 'y' * 151
    api_client.token_authenticate(owner)

    # act
    response = api_client.post(
        '/accounts/users',
        data={'email': email, 'last_name': last_name},
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    create_mock.assert_not_called()


def test_create__phone_exceeds_max__validation_error(api_client, mocker):

    # arrange
    owner = create_test_owner()
    create_mock = mocker.patch('src.accounts.views.users.UserService.create')
    email = 'some@email.com'
    phone = '1' * 33
    api_client.token_authenticate(owner)

    # act
    response = api_client.post(
        '/accounts/users',
        data={'email': email, 'phone': phone},
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    create_mock.assert_not_called()


def test_create__photo_exceeds_max__validation_error(api_client, mocker):

    # arrange
    owner = create_test_owner()
    create_mock = mocker.patch('src.accounts.views.users.UserService.create')
    email = 'some@email.com'
    photo = 'https://x.co/' + 'a' * 1015
    api_client.token_authenticate(owner)

    # act
    response = api_client.post(
        '/accounts/users',
        data={'email': email, 'photo': photo},
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    create_mock.assert_not_called()


def test_create__harmful_chars_in_name__ok(api_client, mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    user = create_test_not_admin(account=account)
    user_service_init_mock = mocker.patch.object(
        UserService,
        attribute='__init__',
        return_value=None,
    )
    create_mock = mocker.patch(
        'src.accounts.services.user.UserService.create',
        return_value=user,
    )
    api_client.token_authenticate(owner)
    first_name = '<script>alert(1)</script>'
    last_name = 'O\'Brien'
    email = 'some@email.com'

    # act
    response = api_client.post(
        '/accounts/users',
        data={
            'email': email,
            'first_name': first_name,
            'last_name': last_name,
        },
    )

    # assert
    assert response.status_code == 200
    user_service_init_mock.assert_called_once_with(
        user=owner,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    create_mock.assert_called_once_with(
        account=owner.account,
        email=email,
        first_name=first_name,
        last_name=last_name,
    )


def test_create__sql_like_input_in_field__no_execution(api_client, mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    user = create_test_not_admin(account=account)
    user_service_init_mock = mocker.patch.object(
        UserService,
        attribute='__init__',
        return_value=None,
    )
    email = 'some@email.com'
    create_mock = mocker.patch(
        'src.accounts.services.user.UserService.create',
        return_value=user,
    )
    api_client.token_authenticate(owner)
    sql_like = "' OR 1=1--"

    # act
    response = api_client.post(
        '/accounts/users',
        data={'email': email, 'first_name': sql_like},
    )

    # assert
    assert response.status_code == 200
    user_service_init_mock.assert_called_once_with(
        user=owner,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    create_mock.assert_called_once_with(
        account=account,
        email=email,
        first_name=sql_like,
    )
