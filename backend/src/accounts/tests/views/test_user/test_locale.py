"""Tests for locale activation in user API views."""

from unittest.mock import call

import pytest
from django.utils import translation
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


@pytest.mark.parametrize('lang', [
    Language.ru,
    Language.de,
])
def test_put__locale__token_activates_user_lang(
    api_client,
    mocker,
    lang,
):

    # arrange
    owner = create_test_owner(language=lang)
    partial_update_mock = mocker.patch(
        'src.accounts.views.user.'
        'UserService.partial_update',
    )
    activate_spy = mocker.spy(translation, 'activate')
    api_client.token_authenticate(owner)

    # act
    response = api_client.put(
        path='/accounts/user',
        data={'photo': 'invalid_url'},
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    activate_spy.assert_has_calls([call(lang)])
    partial_update_mock.assert_not_called()


def test_put__locale__user_lang_overrides_header(
    api_client,
    mocker,
):

    # arrange
    owner = create_test_owner(language=Language.ru)
    partial_update_mock = mocker.patch(
        'src.accounts.views.user.'
        'UserService.partial_update',
    )
    activate_spy = mocker.spy(translation, 'activate')
    api_client.token_authenticate(owner)

    # act
    response = api_client.put(
        path='/accounts/user',
        data={'photo': 'invalid_url'},
        HTTP_ACCEPT_LANGUAGE='de',
    )

    # assert
    assert response.status_code == 400
    activate_spy.assert_has_calls(
        [call('de'), call(Language.ru)],
    )
    partial_update_mock.assert_not_called()


def test_put__locale__no_leak_between_requests(
    api_client,
    mocker,
):

    # arrange
    account = create_test_account()
    ru_user = create_test_owner(
        account=account,
        language=Language.ru,
    )
    de_user = create_test_not_admin(
        account=account,
        language=Language.de,
        email='de@test.test',
    )
    partial_update_mock = mocker.patch(
        'src.accounts.views.user.'
        'UserService.partial_update',
    )
    activate_spy = mocker.spy(translation, 'activate')
    deactivate_spy = mocker.spy(translation, 'deactivate')

    # act
    api_client.token_authenticate(ru_user)
    ru_resp = api_client.put(
        path='/accounts/user',
        data={'photo': 'invalid_url'},
    )
    deactivate_count_after_first = deactivate_spy.call_count
    api_client.token_authenticate(de_user)
    de_resp = api_client.put(
        path='/accounts/user',
        data={'photo': 'invalid_url'},
    )

    # assert
    assert ru_resp.status_code == 400
    assert de_resp.status_code == 400
    activate_spy.assert_has_calls(
        [call(Language.ru), call(Language.de)],
        any_order=True,
    )
    assert deactivate_count_after_first >= 1
    assert deactivate_spy.call_count >= 2
    partial_update_mock.assert_not_called()


def test_put__locale__jwt_activates_user_lang(
    api_client,
    mocker,
):

    # arrange
    owner = create_test_owner(language=Language.ru)
    partial_update_mock = mocker.patch(
        'src.accounts.views.user.'
        'UserService.partial_update',
    )
    activate_spy = mocker.spy(translation, 'activate')
    token = str(AccessToken.for_user(owner))

    # act
    response = api_client.put(
        path='/accounts/user',
        data={'photo': 'invalid_url'},
        HTTP_AUTHORIZATION=f'Bearer {token}',
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    activate_spy.assert_has_calls([call(Language.ru)])
    partial_update_mock.assert_not_called()


def test_comment__locale__guest_activates_lang(
    api_client,
    mocker,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account, language=Language.ru)
    guest = create_test_guest(account=account)
    workflow = create_test_workflow(
        user=owner,
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
    activate_spy = mocker.spy(translation, 'activate')

    # act
    response = api_client.post(
        f'/workflows/{workflow.id}/comment',
        data={},
        HTTP_ACCEPT_LANGUAGE='en',
        **{'X-Guest-Authorization': str_token},
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    activate_spy.assert_has_calls([call(Language.ru)])


def test_comment__locale__guest_wins_over_bearer(
    api_client,
    mocker,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(
        account=account,
        language=Language.de,
    )
    guest = create_test_guest(account=account)
    guest.language = Language.ru
    guest.save(update_fields=['language'])
    workflow = create_test_workflow(
        user=owner,
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
    activate_spy = mocker.spy(translation, 'activate')
    api_client.token_authenticate(owner)

    # act
    response = api_client.post(
        f'/workflows/{workflow.id}/comment',
        data={},
        **{'X-Guest-Authorization': str_token},
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    activate_spy.assert_has_calls([call(Language.ru)])


def test_put__locale__unauth_activates_accept_lang(
    api_client,
    mocker,
):

    # arrange
    activate_spy = mocker.spy(translation, 'activate')

    # act
    response = api_client.put(
        path='/accounts/user',
        data={'photo': 'invalid_url'},
        HTTP_ACCEPT_LANGUAGE='de',
    )

    # assert
    assert response.status_code == 401
    activate_spy.assert_has_calls([call('de')])
