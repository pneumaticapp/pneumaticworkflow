from datetime import timedelta

import pytest
from django.utils import timezone

from src.accounts.enums import (
    BillingPlanType,
    Language,
    LeaseLevel,
    UserDateFormat,
    UserFirstDayWeek,
)
from src.authentication.enums import AuthTokenType
from src.authentication.services.guest_auth import GuestJWTAuthService
from src.payment.stripe.exceptions import StripeServiceException
from src.payment.stripe.service import StripeService
from src.processes.enums import FieldType
from src.processes.models.workflows.task import TaskPerformer
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_admin,
    create_test_guest,
    create_test_owner,
    create_test_workflow,
)
from src.utils.dates import date_format
from src.utils.validation import ErrorCode

pytestmark = pytest.mark.django_db


def test_update__all_fields__ok(mocker, api_client):

    # arrange
    analysis_mock = mocker.patch(
        'src.accounts.views.user.AnalyticService.'
        'users_digest',
    )
    identify_mock = mocker.patch(
        'src.accounts.views.user'
        '.UserViewSet.identify',
    )
    user = create_test_owner()
    request_data = {
        'first_name': 'First',
        'last_name': 'Last',
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
    }
    stripe_service_init_mock = mocker.patch.object(
        StripeService,
        attribute='__init__',
        return_value=None,
    )
    update_customer_mock = mocker.patch(
        'src.payment.stripe.service.StripeService.'
        'update_customer',
    )
    task_field_filter_mock = mocker.patch(
        'src.processes.models.workflows.fields.TaskField.objects.filter',
        return_value=mocker.Mock(update=mocker.Mock(return_value=None)),
    )
    send_user_updated_mock = mocker.patch(
        'src.notifications.tasks.'
        'send_user_updated_notification.delay',
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.put(
        path='/accounts/user',
        data=request_data,
    )

    # assert
    assert response.status_code == 200
    data = response.data
    assert data['id'] == user.id
    assert data['email'] == user.email
    assert data['phone'] == request_data['phone']
    assert data['photo'] == request_data['photo']
    assert data['first_name'] == request_data['first_name']
    assert data['last_name'] == request_data['last_name']
    assert data['type'] == user.type
    assert data['date_joined'] == user.date_joined.strftime(date_format)
    assert data['date_joined_tsp'] == user.date_joined.timestamp()
    assert data['is_admin'] == user.is_admin
    assert data['is_account_owner'] == user.is_account_owner
    assert data['language'] == request_data['language']
    assert data['timezone'] == request_data['timezone']
    assert data['is_tasks_digest_subscriber'] == (
        request_data['is_tasks_digest_subscriber']
    )
    assert data['is_digest_subscriber'] == (
        request_data['is_digest_subscriber']
    )
    assert data['is_newsletters_subscriber'] == (
        request_data['is_newsletters_subscriber']
    )
    assert data['is_special_offers_subscriber'] == (
        request_data['is_special_offers_subscriber']
    )
    assert data['is_new_tasks_subscriber'] == (
        request_data['is_new_tasks_subscriber']
    )
    assert data['is_complete_tasks_subscriber'] == (
        request_data['is_complete_tasks_subscriber']
    )
    assert data['is_comments_mentions_subscriber'] == (
        request_data['is_comments_mentions_subscriber']
    )

    user.refresh_from_db()
    assert user.language == request_data['language']
    assert user.timezone == request_data['timezone']
    assert user.date_fmt == UserDateFormat.PY_USA_24
    assert user.date_fdw == request_data['date_fdw']
    assert user.first_name == request_data['first_name']
    assert user.last_name == request_data['last_name']
    assert user.photo == request_data['photo']
    assert user.phone == request_data['phone']
    assert user.is_tasks_digest_subscriber == (
        request_data['is_tasks_digest_subscriber']
    )
    assert user.is_digest_subscriber == (
        request_data['is_digest_subscriber']
    )
    assert user.is_comments_mentions_subscriber == (
        request_data['is_comments_mentions_subscriber']
    )
    assert user.is_new_tasks_subscriber == (
        request_data['is_new_tasks_subscriber']
    )
    assert user.is_complete_tasks_subscriber == (
        request_data['is_complete_tasks_subscriber']
    )
    assert user.is_newsletters_subscriber == (
        request_data['is_newsletters_subscriber']
    )
    assert user.is_special_offers_subscriber == (
        request_data['is_special_offers_subscriber']
    )
    identify_mock.assert_called_once_with(user)
    analysis_mock.assert_called_once_with(
        user=user,
        auth_type=AuthTokenType.USER,
        is_superuser=False,
    )
    stripe_service_init_mock.assert_called_once_with(
        user=user,
        auth_type=AuthTokenType.USER,
        is_superuser=False,
    )
    update_customer_mock.assert_called_once()
    send_user_updated_mock.assert_called_once_with(
        logging=user.account.log_api_requests,
        account_id=user.account_id,
        user_data={
            'id': user.id,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'photo': user.photo,
            'is_admin': user.is_admin,
            'is_account_owner': user.is_account_owner,
        },
    )
    task_field_filter_mock.assert_called_once_with(
        type=FieldType.USER,
        user_id=user.id,
    )
    task_field_filter_mock.return_value.update.assert_called_once_with(
        value=user.name,
    )


def test_update__partial__update_request_fields(mocker, api_client):

    # arrange
    tz = 'America/Anchorage'
    first_name = 'Old first name'
    last_name = 'Old last name'
    photo = 'https://my.lovely.photo.jpg'
    phone = '79999999990'
    is_tasks_digest_subscriber = False
    is_digest_subscriber = False
    is_comments_mentions_subscriber = False
    is_new_tasks_subscriber = False
    is_complete_tasks_subscriber = False
    is_newsletters_subscriber = False
    is_special_offers_subscriber = False

    analysis_mock = mocker.patch(
        'src.accounts.views.user.AnalyticService.'
        'users_digest',
    )
    identify_mock = mocker.patch(
        'src.accounts.views.user'
        '.UserViewSet.identify',
    )
    user = create_test_owner(
        tz=tz,
        language='en',
        first_name=first_name,
        last_name=last_name,
        photo=photo,
        phone=phone,
    )
    user.is_tasks_digest_subscriber = is_tasks_digest_subscriber
    user.is_digest_subscriber = is_digest_subscriber
    user.is_comments_mentions_subscriber = is_comments_mentions_subscriber
    user.is_new_tasks_subscriber = is_new_tasks_subscriber
    user.is_complete_tasks_subscriber = is_complete_tasks_subscriber
    user.is_newsletters_subscriber = is_newsletters_subscriber
    user.is_special_offers_subscriber = is_special_offers_subscriber
    user.save()

    new_language = Language.fr
    stripe_service_init_mock = mocker.patch.object(
        StripeService,
        attribute='__init__',
        return_value=None,
    )
    update_customer_mock = mocker.patch(
        'src.payment.stripe.service.StripeService.'
        'update_customer',
    )
    task_field_filter_mock = mocker.patch(
        'src.processes.models.workflows.fields.TaskField.objects.filter',
        return_value=mocker.Mock(update=mocker.Mock(return_value=None)),
    )
    send_user_updated_mock = mocker.patch(
        'src.notifications.tasks.'
        'send_user_updated_notification.delay',
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.put(
        path='/accounts/user',
        data={
            'language': new_language,
        },
    )

    # assert
    assert response.status_code == 200
    data = response.data
    assert data['language'] == new_language
    assert data['timezone'] == tz
    assert data['first_name'] == first_name
    assert data['last_name'] == last_name
    assert data['photo'] == photo
    assert data['phone'] == phone
    assert data['is_tasks_digest_subscriber'] == is_tasks_digest_subscriber
    assert data['is_digest_subscriber'] == is_digest_subscriber
    assert data['is_comments_mentions_subscriber'] == (
        is_comments_mentions_subscriber
    )
    assert data['is_new_tasks_subscriber'] == is_new_tasks_subscriber
    assert data['is_complete_tasks_subscriber'] == is_complete_tasks_subscriber
    assert data['is_newsletters_subscriber'] == is_newsletters_subscriber
    assert data['is_special_offers_subscriber'] == (
        is_special_offers_subscriber
    )

    user.refresh_from_db()
    assert user.language == new_language
    assert user.date_fmt == UserDateFormat.PY_USA_12
    assert user.timezone == tz
    assert user.date_fdw == UserFirstDayWeek.SUNDAY
    assert user.first_name == first_name
    assert user.last_name == last_name
    assert user.last_name == last_name
    assert user.photo == photo
    assert user.phone == phone
    assert user.is_tasks_digest_subscriber == is_tasks_digest_subscriber
    assert user.is_digest_subscriber == is_digest_subscriber
    assert user.is_comments_mentions_subscriber == (
        is_comments_mentions_subscriber
    )
    assert user.is_new_tasks_subscriber == is_new_tasks_subscriber
    assert user.is_complete_tasks_subscriber == is_complete_tasks_subscriber
    assert user.is_newsletters_subscriber == is_newsletters_subscriber
    assert user.is_special_offers_subscriber == (
        is_special_offers_subscriber
    )
    identify_mock.assert_called_once_with(user)
    analysis_mock.assert_called_once_with(
        user=user,
        auth_type=AuthTokenType.USER,
        is_superuser=False,
    )
    stripe_service_init_mock.assert_called_once_with(
        user=user,
        auth_type=AuthTokenType.USER,
        is_superuser=False,
    )
    update_customer_mock.assert_called_once()
    send_user_updated_mock.assert_called_once_with(
        logging=user.account.log_api_requests,
        account_id=user.account_id,
        user_data={
            'id': user.id,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'photo': user.photo,
            'is_admin': user.is_admin,
            'is_account_owner': user.is_account_owner,
        },
    )
    task_field_filter_mock.assert_not_called()


def test_update__no_call_analysis__ok(mocker, api_client):

    # arrange
    analysis_mock = mocker.patch(
        'src.accounts.views.user.AnalyticService'
        '.users_digest',
    )
    identify_mock = mocker.patch(
        'src.accounts.views.user'
        '.UserViewSet.identify',
    )
    user = create_test_owner()
    api_client.token_authenticate(user)
    mocker.patch.object(
        StripeService,
        attribute='__init__',
        return_value=None,
    )
    mocker.patch(
        'src.payment.stripe.service.StripeService.'
        'update_customer',
    )
    task_field_filter_mock = mocker.patch(
        'src.processes.models.workflows.fields.TaskField.objects.filter',
        return_value=mocker.Mock(update=mocker.Mock(return_value=None)),
    )
    send_user_updated_mock = mocker.patch(
        'src.notifications.tasks.'
        'send_user_updated_notification.delay',
    )

    # act
    response = api_client.put(
        path='/accounts/user',
        data={
            'is_digest_subscriber': True,
        },
    )

    # assert
    assert response.status_code == 200
    user.refresh_from_db()
    assert user.is_digest_subscriber is True
    identify_mock.assert_called_once_with(user)
    analysis_mock.assert_not_called()
    send_user_updated_mock.assert_called_once_with(
        logging=user.account.log_api_requests,
        account_id=user.account_id,
        user_data={
            'id': user.id,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'photo': user.photo,
            'is_admin': user.is_admin,
            'is_account_owner': user.is_account_owner,
        },
    )
    task_field_filter_mock.assert_not_called()


def test_update__only_first_name__ok(mocker, api_client):
    # arrange
    analytics_mock = mocker.patch(
        'src.accounts.views.user.AnalyticService'
        '.users_digest',
    )
    identify_mock = mocker.patch(
        'src.accounts.views.user'
        '.UserViewSet.identify',
    )
    user = create_test_owner(
        first_name='OldFirst',
        last_name='Last',
    )
    data = {
        'first_name': 'NewFirst',
        'last_name': 'Last',
    }
    stripe_service_init_mock = mocker.patch.object(
        StripeService,
        attribute='__init__',
        return_value=None,
    )
    update_customer_mock = mocker.patch(
        'src.payment.stripe.service.StripeService.'
        'update_customer',
    )
    task_field_filter_mock = mocker.patch(
        'src.processes.models.workflows.fields.TaskField.objects.filter',
        return_value=mocker.Mock(update=mocker.Mock(return_value=None)),
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.put(
        path='/accounts/user',
        data=data,
    )

    # assert
    assert response.status_code == 200
    user.refresh_from_db()
    assert user.first_name == data['first_name']
    assert user.last_name == data['last_name']
    identify_mock.assert_called_once_with(user)
    analytics_mock.assert_not_called()
    stripe_service_init_mock.assert_called_once_with(
        user=user,
        auth_type=AuthTokenType.USER,
        is_superuser=False,
    )
    update_customer_mock.assert_called_once()
    task_field_filter_mock.assert_called_once_with(
        type=FieldType.USER,
        user_id=user.id,
    )
    task_field_filter_mock.return_value.update.assert_called_once_with(
        value=user.name,
    )


def test_update__only_last_name__ok(mocker, api_client):
    # arrange
    analytics_mock = mocker.patch(
        'src.accounts.views.user.AnalyticService'
        '.users_digest',
    )
    identify_mock = mocker.patch(
        'src.accounts.views.user'
        '.UserViewSet.identify',
    )
    user = create_test_owner(
        first_name='First',
        last_name='OldLast',
    )
    data = {
        'first_name': 'First',
        'last_name': 'NewLast',
    }
    stripe_service_init_mock = mocker.patch.object(
        StripeService,
        attribute='__init__',
        return_value=None,
    )
    update_customer_mock = mocker.patch(
        'src.payment.stripe.service.StripeService.'
        'update_customer',
    )
    task_field_filter_mock = mocker.patch(
        'src.processes.models.workflows.fields.TaskField.objects.filter',
        return_value=mocker.Mock(update=mocker.Mock(return_value=None)),
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.put(
        path='/accounts/user',
        data=data,
    )

    # assert
    assert response.status_code == 200
    user.refresh_from_db()
    assert user.first_name == data['first_name']
    assert user.last_name == data['last_name']
    identify_mock.assert_called_once_with(user)
    analytics_mock.assert_not_called()
    stripe_service_init_mock.assert_called_once_with(
        user=user,
        auth_type=AuthTokenType.USER,
        is_superuser=False,
    )
    update_customer_mock.assert_called_once()
    task_field_filter_mock.assert_called_once_with(
        type=FieldType.USER,
        user_id=user.id,
    )
    task_field_filter_mock.return_value.update.assert_called_once_with(
        value=user.name,
    )


def test_update__both_first_and_last_name__ok(mocker, api_client):
    # arrange
    analytics_mock = mocker.patch(
        'src.accounts.views.user.AnalyticService'
        '.users_digest',
    )
    identify_mock = mocker.patch(
        'src.accounts.views.user'
        '.UserViewSet.identify',
    )
    user = create_test_owner(
        first_name='OldFirst',
        last_name='OldLast',
    )
    data = {
        'first_name': 'NewFirst',
        'last_name': 'NewLast',
    }
    stripe_service_init_mock = mocker.patch.object(
        StripeService,
        attribute='__init__',
        return_value=None,
    )
    update_customer_mock = mocker.patch(
        'src.payment.stripe.service.StripeService.'
        'update_customer',
    )
    task_field_filter_mock = mocker.patch(
        'src.processes.models.workflows.fields.TaskField.objects.filter',
        return_value=mocker.Mock(update=mocker.Mock(return_value=None)),
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.put(
        path='/accounts/user',
        data=data,
    )

    # assert
    assert response.status_code == 200
    user.refresh_from_db()
    assert user.first_name == data['first_name']
    assert user.last_name == data['last_name']
    identify_mock.assert_called_once_with(user)
    analytics_mock.assert_not_called()
    stripe_service_init_mock.assert_called_once_with(
        user=user,
        auth_type=AuthTokenType.USER,
        is_superuser=False,
    )
    update_customer_mock.assert_called_once()
    task_field_filter_mock.assert_called_once_with(
        type=FieldType.USER,
        user_id=user.id,
    )
    task_field_filter_mock.return_value.update.assert_called_once_with(
        value=user.name,
    )


def test_update__only_date_fmt__ok(mocker, api_client):

    # arrange
    analysis_mock = mocker.patch(
        'src.accounts.views.user.AnalyticService.'
        'users_digest',
    )
    identify_mock = mocker.patch(
        'src.accounts.views.user'
        '.UserViewSet.identify',
    )
    user = create_test_owner(date_fmt=UserDateFormat.API_USA_24)
    data = {
        'date_fmt': UserDateFormat.API_EUROPE_24,
    }
    stripe_service_init_mock = mocker.patch.object(
        StripeService,
        attribute='__init__',
        return_value=None,
    )
    update_customer_mock = mocker.patch(
        'src.payment.stripe.service.StripeService.'
        'update_customer',
    )
    send_user_updated_mock = mocker.patch(
        'src.notifications.tasks.'
        'send_user_updated_notification.delay',
    )
    task_field_filter_mock = mocker.patch(
        'src.processes.models.workflows.fields.TaskField.objects.filter',
        return_value=mocker.Mock(update=mocker.Mock(return_value=None)),
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.put(
        path='/accounts/user',
        data=data,
    )

    # assert
    assert response.status_code == 200
    user.refresh_from_db()
    assert user.date_fmt == UserDateFormat.PY_EUROPE_24
    identify_mock.assert_called_once_with(user)
    analysis_mock.assert_not_called()
    stripe_service_init_mock.assert_called_once_with(
        user=user,
        auth_type=AuthTokenType.USER,
        is_superuser=False,
    )
    update_customer_mock.assert_called_once()
    task_field_filter_mock.assert_not_called()
    send_user_updated_mock.assert_called_once_with(
        logging=user.account.log_api_requests,
        account_id=user.account_id,
        user_data={
            'id': user.id,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'photo': user.photo,
            'is_admin': user.is_admin,
            'is_account_owner': user.is_account_owner,
        },
    )


def test_update__only_date_fdw__ok(mocker, api_client):

    # arrange
    analysis_mock = mocker.patch(
        'src.accounts.views.user.AnalyticService.'
        'users_digest',
    )
    identify_mock = mocker.patch(
        'src.accounts.views.user'
        '.UserViewSet.identify',
    )
    user = create_test_owner(date_fdw=UserFirstDayWeek.FRIDAY)
    data = {
        'date_fdw': UserFirstDayWeek.THURSDAY,
    }
    stripe_service_init_mock = mocker.patch.object(
        StripeService,
        attribute='__init__',
        return_value=None,
    )
    update_customer_mock = mocker.patch(
        'src.payment.stripe.service.StripeService.'
        'update_customer',
    )
    task_field_filter_mock = mocker.patch(
        'src.processes.models.workflows.fields.TaskField.objects.filter',
        return_value=mocker.Mock(update=mocker.Mock(return_value=None)),
    )
    send_user_updated_mock = mocker.patch(
        'src.notifications.tasks.'
        'send_user_updated_notification.delay',
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.put(
        path='/accounts/user',
        data=data,
    )

    # assert
    assert response.status_code == 200
    user.refresh_from_db()
    assert user.date_fdw == UserFirstDayWeek.THURSDAY
    identify_mock.assert_called_once_with(user)
    analysis_mock.assert_not_called()
    stripe_service_init_mock.assert_called_once_with(
        user=user,
        auth_type=AuthTokenType.USER,
        is_superuser=False,
    )
    update_customer_mock.assert_called_once()
    task_field_filter_mock.assert_not_called()
    send_user_updated_mock.assert_called_once_with(
        logging=user.account.log_api_requests,
        account_id=user.account_id,
        user_data={
            'id': user.id,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'photo': user.photo,
            'is_admin': user.is_admin,
            'is_account_owner': user.is_account_owner,
        },
    )


@pytest.mark.parametrize(
    'date_fmt', [
        ' ',
        '',
        'Bad Format',
        '%B %d, %Y, %I:%M%p',
    ])
def test_update__invalid_date_fmt__validation_error(
    mocker,
    api_client,
    date_fmt,
):

    # arrange
    analysis_mock = mocker.patch(
        'src.accounts.views.user.AnalyticService.'
        'users_digest',
    )
    identify_mock = mocker.patch(
        'src.accounts.views.user'
        '.UserViewSet.identify',
    )
    user = create_test_owner()
    data = {
        'date_fmt': date_fmt,
    }
    stripe_service_init_mock = mocker.patch.object(
        StripeService,
        attribute='__init__',
        return_value=None,
    )
    update_customer_mock = mocker.patch(
        'src.payment.stripe.service.StripeService.'
        'update_customer',
    )
    task_field_filter_mock = mocker.patch(
        'src.processes.models.workflows.fields.TaskField.objects.filter',
        return_value=mocker.Mock(update=mocker.Mock(return_value=None)),
    )
    send_user_updated_mock = mocker.patch(
        'src.notifications.tasks.'
        'send_user_updated_notification.delay',
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.put(
        path='/accounts/user',
        data=data,
    )

    # assert
    assert response.status_code == 400
    message = 'is not a valid choice.'
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'].endswith(message)
    assert response.data['details']['name'] == 'date_fmt'
    assert response.data['details']['reason'].endswith(message)
    identify_mock.assert_not_called()
    analysis_mock.assert_not_called()
    stripe_service_init_mock.assert_not_called()
    update_customer_mock.assert_not_called()
    task_field_filter_mock.assert_not_called()
    send_user_updated_mock.assert_not_called()


@pytest.mark.parametrize(
    'date_fdw', [
        ' ',
        '',
        'Bad Format',
    ])
def test_update__invalid_date_fdw__validation_error(
    mocker,
    api_client,
    date_fdw,
):

    # arrange
    analysis_mock = mocker.patch(
        'src.accounts.views.user.AnalyticService.'
        'users_digest',
    )
    identify_mock = mocker.patch(
        'src.accounts.views.user'
        '.UserViewSet.identify',
    )
    user = create_test_owner()
    data = {
        'date_fdw': date_fdw,
    }
    stripe_service_init_mock = mocker.patch.object(
        StripeService,
        attribute='__init__',
        return_value=None,
    )
    update_customer_mock = mocker.patch(
        'src.payment.stripe.service.StripeService.'
        'update_customer',
    )
    task_field_filter_mock = mocker.patch(
        'src.processes.models.workflows.fields.TaskField.objects.filter',
        return_value=mocker.Mock(update=mocker.Mock(return_value=None)),
    )
    send_user_updated_mock = mocker.patch(
        'src.notifications.tasks.'
        'send_user_updated_notification.delay',
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.put(
        path='/accounts/user',
        data=data,
    )

    # assert
    assert response.status_code == 400
    message = 'is not a valid choice.'
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'].endswith(message)
    assert response.data['details']['name'] == 'date_fdw'
    assert response.data['details']['reason'].endswith(message)
    identify_mock.assert_not_called()
    analysis_mock.assert_not_called()
    stripe_service_init_mock.assert_not_called()
    update_customer_mock.assert_not_called()
    task_field_filter_mock.assert_not_called()
    send_user_updated_mock.assert_not_called()


def test_update__invalid_photo__validation_error(
    mocker,
    api_client,
):

    # arrange
    analysis_mock = mocker.patch(
        'src.accounts.views.user.AnalyticService'
        '.users_digest',
    )
    identify_mock = mocker.patch(
        'src.accounts.views.user'
        '.UserViewSet.identify',
    )
    user = create_test_owner()
    data = {
        'photo': 'invalid_url',
    }
    api_client.token_authenticate(user)
    stripe_service_init_mock = mocker.patch.object(
        StripeService,
        attribute='__init__',
        return_value=None,
    )
    update_customer_mock = mocker.patch(
        'src.payment.stripe.service.StripeService.'
        'update_customer',
    )
    task_field_filter_mock = mocker.patch(
        'src.processes.models.workflows.fields.TaskField.objects.filter',
        return_value=mocker.Mock(update=mocker.Mock(return_value=None)),
    )
    send_user_updated_mock = mocker.patch(
        'src.notifications.tasks.'
        'send_user_updated_notification.delay',
    )

    # act
    response = api_client.put(
        path='/accounts/user',
        data=data,
    )

    # assert
    message = 'Enter a valid URL.'
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    assert response.data['details']['name'] == 'photo'
    assert response.data['details']['reason'] == message
    identify_mock.assert_not_called()
    analysis_mock.assert_not_called()
    stripe_service_init_mock.assert_not_called()
    update_customer_mock.assert_not_called()
    task_field_filter_mock.assert_not_called()
    send_user_updated_mock.assert_not_called()


def test_update__not_account_owner__not_update_customer(
    mocker,
    api_client,
):

    # arrange
    mocker.patch(
        'src.accounts.views.user.AnalyticService'
        '.users_digest',
    )
    mocker.patch(
        'src.accounts.views.user'
        '.UserViewSet.identify',
    )
    account = create_test_account(lease_level=LeaseLevel.STANDARD)
    create_test_owner(
        account=account,
        email='owner@test.test',
    )
    user = create_test_admin(account=account)
    stripe_service_init_mock = mocker.patch.object(
        StripeService,
        attribute='__init__',
        return_value=None,
    )
    update_customer_mock = mocker.patch(
        'src.payment.stripe.service.StripeService.'
        'update_customer',
    )
    send_user_updated_mock = mocker.patch(
        'src.notifications.tasks.'
        'send_user_updated_notification.delay',
    )
    task_field_filter_mock = mocker.patch(
        'src.processes.models.workflows.fields.TaskField.objects.filter',
        return_value=mocker.Mock(update=mocker.Mock(return_value=None)),
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.put(
        path='/accounts/user',
        data={'first_name': 'New name'},
    )

    # assert
    assert response.status_code == 200
    user.refresh_from_db()
    stripe_service_init_mock.assert_not_called()
    update_customer_mock.assert_not_called()
    task_field_filter_mock.assert_called_once_with(
        type=FieldType.USER,
        user_id=user.id,
    )
    task_field_filter_mock.return_value.update.assert_called_once_with(
        value=user.name,
    )
    send_user_updated_mock.assert_called_once_with(
        logging=user.account.log_api_requests,
        account_id=user.account_id,
        user_data={
            'id': user.id,
            'first_name': 'New name',
            'last_name': user.last_name,
            'email': user.email,
            'photo': user.photo,
            'is_admin': user.is_admin,
            'is_account_owner': user.is_account_owner,
        },
    )


def test_update__tenant_account__not_update_customer(
    mocker,
    api_client,
):

    # arrange
    mocker.patch(
        'src.accounts.views.user.AnalyticService'
        '.users_digest',
    )
    mocker.patch(
        'src.accounts.views.user'
        '.UserViewSet.identify',
    )
    account = create_test_account(lease_level=LeaseLevel.TENANT)
    user = create_test_owner(account=account)
    stripe_service_init_mock = mocker.patch.object(
        StripeService,
        attribute='__init__',
        return_value=None,
    )
    update_customer_mock = mocker.patch(
        'src.payment.stripe.service.StripeService.'
        'update_customer',
    )
    task_field_filter_mock = mocker.patch(
        'src.processes.models.workflows.fields.TaskField.objects.filter',
        return_value=mocker.Mock(update=mocker.Mock(return_value=None)),
    )
    send_user_updated_mock = mocker.patch(
        'src.notifications.tasks.'
        'send_user_updated_notification.delay',
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.put(
        path='/accounts/user',
        data={'first_name': 'New name'},
    )

    # assert
    assert response.status_code == 200
    user.refresh_from_db()
    stripe_service_init_mock.assert_not_called()
    update_customer_mock.assert_not_called()
    task_field_filter_mock.assert_called_once_with(
        type=FieldType.USER,
        user_id=user.id,
    )
    task_field_filter_mock.return_value.update.assert_called_once_with(
        value=user.name,
    )
    send_user_updated_mock.assert_called_once_with(
        logging=user.account.log_api_requests,
        account_id=user.account_id,
        user_data={
            'id': user.id,
            'first_name': 'New name',
            'last_name': user.last_name,
            'email': user.email,
            'photo': user.photo,
            'is_admin': user.is_admin,
            'is_account_owner': user.is_account_owner,
        },
    )


def test_update__stripe_exception__validation_error(
    mocker,
    api_client,
):

    # arrange
    mocker.patch(
        'src.accounts.views.user.AnalyticService'
        '.users_digest',
    )
    mocker.patch(
        'src.accounts.views.user'
        '.UserViewSet.identify',
    )
    user = create_test_owner()
    stripe_service_init_mock = mocker.patch.object(
        StripeService,
        attribute='__init__',
        return_value=None,
    )
    message = 'Some error'
    update_customer_mock = mocker.patch(
        'src.payment.stripe.service.StripeService.'
        'update_customer',
        side_effect=StripeServiceException(message),
    )
    task_field_filter_mock = mocker.patch(
        'src.processes.models.workflows.fields.TaskField.objects.filter',
        return_value=mocker.Mock(update=mocker.Mock(return_value=None)),
    )
    send_user_updated_mock = mocker.patch(
        'src.notifications.tasks.'
        'send_user_updated_notification.delay',
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.put(
        path='/accounts/user',
        data={'first_name': 'First'},
    )

    # assert
    assert response.status_code == 400
    assert response.data['message'] == message
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    stripe_service_init_mock.assert_called_once_with(
        user=user,
        auth_type=AuthTokenType.USER,
        is_superuser=False,
    )
    user.refresh_from_db()
    update_customer_mock.assert_called_once()
    send_user_updated_mock.assert_not_called()
    task_field_filter_mock.assert_called_once_with(
        type=FieldType.USER,
        user_id=user.id,
    )
    task_field_filter_mock.return_value.update.assert_called_once_with(
        value=user.name,
    )


def test_update__is_digest_subscriber__anaytics_call(
    mocker,
    api_client,
):

    # arrange
    analysis_mock = mocker.patch(
        'src.accounts.views.user.AnalyticService'
        '.users_digest',
    )
    identify_mock = mocker.patch(
        'src.accounts.views.user'
        '.UserViewSet.identify',
    )
    user = create_test_owner()
    data = {
        'is_digest_subscriber': False,
    }
    mocker.patch.object(
        StripeService,
        attribute='__init__',
        return_value=None,
    )
    mocker.patch(
        'src.payment.stripe.service.StripeService.'
        'update_customer',
    )
    task_field_filter_mock = mocker.patch(
        'src.processes.models.workflows.fields.TaskField.objects.filter',
        return_value=mocker.Mock(update=mocker.Mock(return_value=None)),
    )
    send_user_updated_mock = mocker.patch(
        'src.notifications.tasks.'
        'send_user_updated_notification.delay',
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.put(
        path='/accounts/user',
        data=data,
    )

    # assert
    assert response.status_code == 200
    assert response.data['is_digest_subscriber'] == (
        data['is_digest_subscriber']
    )
    user.refresh_from_db()
    assert user.is_digest_subscriber == data['is_digest_subscriber']
    identify_mock.assert_called_once_with(user)
    analysis_mock.assert_called_once_with(
        user=user,
        auth_type=AuthTokenType.USER,
        is_superuser=False,
    )
    task_field_filter_mock.assert_not_called()
    send_user_updated_mock.assert_called_once_with(
        logging=user.account.log_api_requests,
        account_id=user.account_id,
        user_data={
            'id': user.id,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'photo': user.photo,
            'is_admin': user.is_admin,
            'is_account_owner': user.is_account_owner,
        },
    )


@pytest.mark.parametrize('language', Language.EURO_VALUES)
def test_update__euro_languages__ok(
    mocker,
    language,
    api_client,
):

    # arrange
    mocker.patch(
        'src.accounts.views.user.AnalyticService'
        '.users_digest',
    )
    mocker.patch(
        'src.accounts.views.user'
        '.UserViewSet.identify',
    )
    user = create_test_owner()
    mocker.patch.object(
        StripeService,
        attribute='__init__',
        return_value=None,
    )
    mocker.patch(
        'src.payment.stripe.service.StripeService.'
        'update_customer',
    )
    task_field_filter_mock = mocker.patch(
        'src.processes.models.workflows.fields.TaskField.objects.filter',
        return_value=mocker.Mock(update=mocker.Mock(return_value=None)),
    )
    settings_mock = mocker.patch(
        'src.accounts.serializers.user.settings',
    )
    settings_mock.LANGUAGE_CODE = Language.en

    data = {
        'language': language,
    }
    send_user_updated_mock = mocker.patch(
        'src.notifications.tasks.'
        'send_user_updated_notification.delay',
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.put(
        path='/accounts/user',
        data=data,
    )

    # assert
    assert response.status_code == 200
    assert response.data['language'] == language
    user.refresh_from_db()
    assert user.language == language
    task_field_filter_mock.assert_not_called()
    send_user_updated_mock.assert_called_once_with(
        logging=user.account.log_api_requests,
        account_id=user.account_id,
        user_data={
            'id': user.id,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'photo': user.photo,
            'is_admin': user.is_admin,
            'is_account_owner': user.is_account_owner,
        },
    )


@pytest.mark.parametrize('language', Language.EURO_VALUES)
def test_update__system_euro_language_not_allow_ru__validation_error(
    mocker,
    language,
    api_client,
):

    # arrange
    analysis_mock = mocker.patch(
        'src.accounts.views.user.AnalyticService'
        '.users_digest',
    )
    identify_mock = mocker.patch(
        'src.accounts.views.user'
        '.UserViewSet.identify',
    )
    settings_mock = mocker.patch(
        'src.accounts.serializers.user.settings',
    )
    settings_mock.LANGUAGE_CODE = language

    user = create_test_owner()
    stripe_service_init_mock = mocker.patch.object(
        StripeService,
        attribute='__init__',
        return_value=None,
    )
    update_customer_mock = mocker.patch(
        'src.payment.stripe.service.StripeService.'
        'update_customer',
    )
    task_field_filter_mock = mocker.patch(
        'src.processes.models.workflows.fields.TaskField.objects.filter',
        return_value=mocker.Mock(update=mocker.Mock(return_value=None)),
    )
    send_user_updated_mock = mocker.patch(
        'src.notifications.tasks.'
        'send_user_updated_notification.delay',
    )
    data = {
        'language': Language.ru,
    }
    api_client.token_authenticate(user)

    # act
    response = api_client.put(
        path='/accounts/user',
        data=data,
    )

    # assert
    assert response.status_code == 400
    assert response.data['message'] == (
        f'"{Language.ru}" is not a valid choice.'
    )
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['details']['name'] == 'language'
    identify_mock.assert_not_called()
    analysis_mock.assert_not_called()
    stripe_service_init_mock.assert_not_called()
    update_customer_mock.assert_not_called()
    task_field_filter_mock.assert_not_called()
    send_user_updated_mock.assert_not_called()


@pytest.mark.parametrize('language', Language.VALUES)
def test_update__system_ru_language_allow_all__ok(
    mocker,
    language,
    api_client,
):

    # arrange
    mocker.patch(
        'src.accounts.views.user.AnalyticService'
        '.users_digest',
    )
    mocker.patch(
        'src.accounts.views.user'
        '.UserViewSet.identify',
    )
    user = create_test_owner()
    mocker.patch.object(
        StripeService,
        attribute='__init__',
        return_value=None,
    )
    mocker.patch(
        'src.payment.stripe.service.StripeService.'
        'update_customer',
    )
    task_field_filter_mock = mocker.patch(
        'src.processes.models.workflows.fields.TaskField.objects.filter',
        return_value=mocker.Mock(update=mocker.Mock(return_value=None)),
    )
    settings_mock = mocker.patch(
        'src.accounts.serializers.user.settings',
    )
    send_user_updated_mock = mocker.patch(
        'src.notifications.tasks.'
        'send_user_updated_notification.delay',
    )
    settings_mock.LANGUAGE_CODE = Language.ru

    data = {
        'language': language,
    }
    api_client.token_authenticate(user)

    # act
    response = api_client.put(
        path='/accounts/user',
        data=data,
    )

    # assert
    assert response.status_code == 200
    assert response.data['language'] == language
    user.refresh_from_db()
    assert user.language == language
    task_field_filter_mock.assert_not_called()
    send_user_updated_mock.assert_called_once_with(
        logging=user.account.log_api_requests,
        account_id=user.account_id,
        user_data={
            'id': user.id,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'photo': user.photo,
            'is_admin': user.is_admin,
            'is_account_owner': user.is_account_owner,
        },
    )


def test_update__unsupported_language__validation_error(
    mocker,
    api_client,
):

    # arrange
    analysis_mock = mocker.patch(
        'src.accounts.views.user.AnalyticService'
        '.users_digest',
    )
    identify_mock = mocker.patch(
        'src.accounts.views.user'
        '.UserViewSet.identify',
    )
    send_user_updated_mock = mocker.patch(
        'src.notifications.tasks.'
        'send_user_updated_notification.delay',
    )
    language = 'po'
    user = create_test_owner()
    stripe_service_init_mock = mocker.patch.object(
        StripeService,
        attribute='__init__',
        return_value=None,
    )
    update_customer_mock = mocker.patch(
        'src.payment.stripe.service.StripeService.'
        'update_customer',
    )
    task_field_filter_mock = mocker.patch(
        'src.processes.models.workflows.fields.TaskField.objects.filter',
        return_value=mocker.Mock(update=mocker.Mock(return_value=None)),
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.put(
        path='/accounts/user',
        data={'language': language},
    )

    # assert
    assert response.status_code == 400
    assert response.data['message'] == (
        f'"{language}" is not a valid choice.'
    )
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['details']['name'] == 'language'
    identify_mock.assert_not_called()
    analysis_mock.assert_not_called()
    stripe_service_init_mock.assert_not_called()
    update_customer_mock.assert_not_called()
    task_field_filter_mock.assert_not_called()
    send_user_updated_mock.assert_not_called()


def test_update__timezone__ok(
    mocker,
    api_client,
):

    # arrange
    mocker.patch(
        'src.accounts.views.user.AnalyticService'
        '.users_digest',
    )
    mocker.patch(
        'src.accounts.views.user'
        '.UserViewSet.identify',
    )
    task_field_filter_mock = mocker.patch(
        'src.processes.models.workflows.fields.TaskField.objects.filter',
        return_value=mocker.Mock(update=mocker.Mock(return_value=None)),
    )
    user = create_test_owner()
    mocker.patch.object(
        StripeService,
        attribute='__init__',
        return_value=None,
    )
    mocker.patch(
        'src.payment.stripe.service.StripeService.'
        'update_customer',
    )
    send_user_updated_mock = mocker.patch(
        'src.notifications.tasks.'
        'send_user_updated_notification.delay',
    )
    tz = 'America/Anchorage'
    data = {
        'timezone': tz,
    }
    api_client.token_authenticate(user)

    # act
    response = api_client.put(
        path='/accounts/user',
        data=data,
    )

    # assert
    assert response.status_code == 200
    assert response.data['timezone'] == tz
    user.refresh_from_db()
    assert user.timezone == tz
    task_field_filter_mock.assert_not_called()
    send_user_updated_mock.assert_called_once_with(
        logging=user.account.log_api_requests,
        account_id=user.account_id,
        user_data={
            'id': user.id,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'photo': user.photo,
            'is_admin': user.is_admin,
            'is_account_owner': user.is_account_owner,
        },
    )


def test_update__invalid_timezone__validation_error(
    mocker,
    api_client,
):

    # arrange
    analysis_mock = mocker.patch(
        'src.accounts.views.user.AnalyticService'
        '.users_digest',
    )
    identify_mock = mocker.patch(
        'src.accounts.views.user'
        '.UserViewSet.identify',
    )
    task_field_filter_mock = mocker.patch(
        'src.processes.models.workflows.fields.TaskField.objects.filter',
        return_value=mocker.Mock(update=mocker.Mock(return_value=None)),
    )
    user = create_test_owner()
    stripe_service_init_mock = mocker.patch.object(
        StripeService,
        attribute='__init__',
        return_value=None,
    )
    update_customer_mock = mocker.patch(
        'src.payment.stripe.service.StripeService.'
        'update_customer',
    )
    send_user_updated_mock = mocker.patch(
        'src.notifications.tasks.'
        'send_user_updated_notification.delay',
    )
    tz = 'What/Ever'
    data = {
        'timezone': tz,
    }
    api_client.token_authenticate(user)

    # act
    response = api_client.put(
        path='/accounts/user',
        data=data,
    )

    # assert
    assert response.status_code == 400
    assert response.data['message'] == f'"{tz}" is not a valid choice.'
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['details']['name'] == 'timezone'
    identify_mock.assert_not_called()
    analysis_mock.assert_not_called()
    stripe_service_init_mock.assert_not_called()
    update_customer_mock.assert_not_called()
    task_field_filter_mock.assert_not_called()
    send_user_updated_mock.assert_not_called()


def test_update__not_authenticated__unauthorized(mocker, api_client):

    # arrange
    analysis_mock = mocker.patch(
        'src.accounts.views.user.AnalyticService.'
        'users_digest',
    )
    identify_mock = mocker.patch(
        'src.accounts.views.user'
        '.UserViewSet.identify',
    )
    task_field_filter_mock = mocker.patch(
        'src.processes.models.workflows.fields.TaskField.objects.filter',
        return_value=mocker.Mock(update=mocker.Mock(return_value=None)),
    )
    stripe_service_init_mock = mocker.patch.object(
        StripeService,
        attribute='__init__',
        return_value=None,
    )
    update_customer_mock = mocker.patch(
        'src.payment.stripe.service.StripeService.'
        'update_customer',
    )
    send_user_updated_mock = mocker.patch(
        'src.notifications.tasks.'
        'send_user_updated_notification.delay',
    )

    # act
    response = api_client.put(
        path='/accounts/user',
        data={'phone': '79999999990'},
    )

    # assert
    assert response.status_code == 401
    identify_mock.assert_not_called()
    analysis_mock.assert_not_called()
    stripe_service_init_mock.assert_not_called()
    update_customer_mock.assert_not_called()
    task_field_filter_mock.assert_not_called()
    send_user_updated_mock.assert_not_called()


def test_update__guest__permission_denied(mocker, api_client):

    # arrange
    analysis_mock = mocker.patch(
        'src.accounts.views.user.AnalyticService.'
        'users_digest',
    )
    identify_mock = mocker.patch(
        'src.accounts.views.user'
        '.UserViewSet.identify',
    )
    task_field_filter_mock = mocker.patch(
        'src.processes.models.workflows.fields.TaskField.objects.filter',
        return_value=mocker.Mock(update=mocker.Mock(return_value=None)),
    )
    account = create_test_account()
    owner = create_test_owner(account=account)
    guest = create_test_guest(account=account)
    workflow = create_test_workflow(owner, tasks_count=1)
    task = workflow.tasks.first()
    TaskPerformer.objects.create(
        task_id=task.id,
        user_id=guest.id,
    )
    stripe_service_init_mock = mocker.patch.object(
        StripeService,
        attribute='__init__',
        return_value=None,
    )
    update_customer_mock = mocker.patch(
        'src.payment.stripe.service.StripeService.'
        'update_customer',
    )
    send_user_updated_mock = mocker.patch(
        'src.notifications.tasks.'
        'send_user_updated_notification.delay',
    )
    str_token = GuestJWTAuthService.get_str_token(
        task_id=task.id,
        user_id=guest.id,
        account_id=account.id,
    )

    # act
    response = api_client.put(
        path='/accounts/user',
        data={'date_fdw': UserFirstDayWeek.THURSDAY},
        **{'X-Guest-Authorization': str_token},
    )

    # assert
    assert response.status_code == 403
    identify_mock.assert_not_called()
    analysis_mock.assert_not_called()
    stripe_service_init_mock.assert_not_called()
    update_customer_mock.assert_not_called()
    task_field_filter_mock.assert_not_called()
    send_user_updated_mock.assert_not_called()


def test_update__expired_subscription__permission_denied(
    mocker,
    api_client,
):

    # arrange
    analysis_mock = mocker.patch(
        'src.accounts.views.user.AnalyticService.'
        'users_digest',
    )
    identify_mock = mocker.patch(
        'src.accounts.views.user'
        '.UserViewSet.identify',
    )
    task_field_filter_mock = mocker.patch(
        'src.processes.models.workflows.fields.TaskField.objects.filter',
        return_value=mocker.Mock(update=mocker.Mock(return_value=None)),
    )
    account = create_test_account(
        plan=BillingPlanType.UNLIMITED,
        plan_expiration=timezone.now() - timedelta(days=1),
    )
    user = create_test_owner(account=account)
    stripe_service_init_mock = mocker.patch.object(
        StripeService,
        attribute='__init__',
        return_value=None,
    )
    update_customer_mock = mocker.patch(
        'src.payment.stripe.service.StripeService.'
        'update_customer',
    )
    send_user_updated_mock = mocker.patch(
        'src.notifications.tasks.'
        'send_user_updated_notification.delay',
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.put(
        path='/accounts/user',
        data={'date_fdw': UserFirstDayWeek.THURSDAY},
    )

    # assert
    assert response.status_code == 403
    identify_mock.assert_not_called()
    analysis_mock.assert_not_called()
    stripe_service_init_mock.assert_not_called()
    update_customer_mock.assert_not_called()
    task_field_filter_mock.assert_not_called()
    send_user_updated_mock.assert_not_called()
