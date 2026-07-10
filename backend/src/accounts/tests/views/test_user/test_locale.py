import pytest
from rest_framework_simplejwt.tokens import AccessToken

from src.accounts.enums import Language
from src.authentication.services.guest_auth import GuestJWTAuthService
from src.processes.models.workflows.task import TaskPerformer
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_guest,
    create_test_not_admin,
    create_test_owner,
    create_test_workflow,
)
from src.utils.validation import ErrorCode

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize('lang,expected_msg', [
    (Language.en, 'Enter a valid URL.'),
    (Language.ru, 'Введите правильный URL.'),
    (Language.de, 'Gib eine gültige URL ein.'),
])
def test_put__locale__localized_validation_error(
    api_client,
    mocker,
    lang,
    expected_msg,
):

    """ Validation error is returned in user's language. """

    # arrange
    owner = create_test_owner(language=lang)
    request_data = {'photo': 'invalid_url'}
    partial_update_mock = mocker.patch(
        'src.accounts.views.user.'
        'UserService.partial_update',
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.put(
        path='/accounts/user',
        data=request_data,
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == expected_msg
    assert response.data['details']['name'] == 'photo'
    assert response.data['details']['reason'] == expected_msg
    partial_update_mock.assert_not_called()


def test_put__locale__user_lang_overrides_header(
    api_client,
    mocker,
):

    """ User language takes priority over Accept-Language. """

    # arrange
    owner = create_test_owner(language=Language.ru)
    request_data = {'photo': 'invalid_url'}
    partial_update_mock = mocker.patch(
        'src.accounts.views.user.'
        'UserService.partial_update',
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.put(
        path='/accounts/user',
        data=request_data,
        HTTP_ACCEPT_LANGUAGE='de',
    )

    # assert
    expected_msg = 'Введите правильный URL.'
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == expected_msg
    assert response.data['details']['name'] == 'photo'
    assert response.data['details']['reason'] == expected_msg
    partial_update_mock.assert_not_called()


def test_put__locale__no_leak_between_requests(
    api_client,
    mocker,
):

    """ Locale does not leak between requests. """

    # arrange
    account = create_test_account()
    ru_user = create_test_owner(
        account=account,
        language=Language.ru,
    )
    en_user = create_test_not_admin(
        account=account,
        language=Language.en,
        email='en@test.test',
    )
    request_data = {'photo': 'invalid_url'}
    partial_update_mock = mocker.patch(
        'src.accounts.views.user.'
        'UserService.partial_update',
    )

    # act
    api_client.token_authenticate(ru_user)
    ru_resp = api_client.put(
        path='/accounts/user',
        data=request_data,
    )
    api_client.token_authenticate(en_user)
    en_resp = api_client.put(
        path='/accounts/user',
        data=request_data,
    )

    # assert
    assert ru_resp.status_code == 400
    assert ru_resp.data['code'] == ErrorCode.VALIDATION_ERROR
    assert ru_resp.data['message'] == 'Введите правильный URL.'
    assert en_resp.status_code == 400
    assert en_resp.data['code'] == ErrorCode.VALIDATION_ERROR
    assert en_resp.data['message'] == 'Enter a valid URL.'
    partial_update_mock.assert_not_called()


def test_put__locale__jwt_bearer_localized_validation_error(
    api_client,
    mocker,
):

    """ SimpleJWT bearer resolves user language in middleware. """

    # arrange
    owner = create_test_owner(language=Language.ru)
    request_data = {'photo': 'invalid_url'}
    partial_update_mock = mocker.patch(
        'src.accounts.views.user.'
        'UserService.partial_update',
    )
    token = str(AccessToken.for_user(owner))

    # act
    response = api_client.put(
        path='/accounts/user',
        data=request_data,
        HTTP_AUTHORIZATION=f'Bearer {token}',
    )

    # assert
    expected_msg = 'Введите правильный URL.'
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == expected_msg
    assert response.data['details']['name'] == 'photo'
    assert response.data['details']['reason'] == expected_msg
    partial_update_mock.assert_not_called()


def test_comment__locale__guest_localized_validation_error(api_client):

    """ Guest validation error uses X-Guest-Authorization user language. """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account, language=Language.ru)
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

    # act
    response = api_client.post(
        f'/workflows/{workflow.id}/comment',
        data={},
        HTTP_ACCEPT_LANGUAGE='en',
        **{'X-Guest-Authorization': str_token},
    )

    # assert
    expected_msg = 'Поле обязательно.'
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == expected_msg


def test_comment__locale__guest_wins_over_bearer(api_client):

    """ Guest locale takes priority over Bearer (matches DRF auth order). """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account, language=Language.en)
    guest = create_test_guest(account=account)
    guest.language = Language.ru
    guest.save(update_fields=['language'])
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
    api_client.token_authenticate(owner)

    # act
    response = api_client.post(
        f'/workflows/{workflow.id}/comment',
        data={},
        **{'X-Guest-Authorization': str_token},
    )

    # assert
    expected_msg = 'Поле обязательно.'
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == expected_msg


def test_put__locale__unauthenticated_uses_accept_language(api_client):
    """Anonymous requests fall back to Accept-Language."""

    response = api_client.put(
        path='/accounts/user',
        data={'photo': 'invalid_url'},
        HTTP_ACCEPT_LANGUAGE='de',
    )

    assert response.status_code == 401
    # DRF de locale (not Django's gettext for the same msgid)
    assert str(response.data['detail']) == 'Anmeldedaten fehlen.'
