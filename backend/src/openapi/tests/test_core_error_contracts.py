"""Real permission and email-link failures for remaining Core operations."""

from django.conf import settings
import pytest

from src.accounts.messages import MSG_A_0008
from src.processes.tests.fixtures import create_test_owner

pytestmark = pytest.mark.django_db

# These operations lacked a validated negative exchange in the legacy tests.
PROTECTED_OPERATIONS = (
    ('get', '/accounts/account'),
    ('get', '/accounts/api-keys'),
    ('get', '/accounts/invites'),
    ('get', '/accounts/notifications/count'),
    ('get', '/accounts/user/counters'),
    ('get', '/accounts/users/active-count'),
    ('get', '/accounts/users/privileges'),
    ('post', '/accounts/users/1/activate-vacation'),
    ('post', '/accounts/users/1/deactivate-vacation'),
    ('get', '/accounts/users/1/api-keys'),
    ('get', '/applications/integrations'),
    ('get', '/reports/dashboard/tasks/breakdown'),
    ('get', '/reports/dashboard/tasks/by-steps'),
    ('get', '/reports/dashboard/tasks/overview'),
    ('get', '/reports/dashboard/workflows/breakdown'),
    ('get', '/templates/system'),
    ('get', '/templates/system/categories'),
    ('post', '/templates/system/1/fill'),
    ('get', '/templates/titles-by-owners'),
    ('delete', '/v2/tasks/1/due-date'),
)


@pytest.mark.parametrize('method,path', PROTECTED_OPERATIONS)
def test_core__missing_auth__matches_error_contract(
    contract_api_client, method, path,
) -> None:
    response = getattr(contract_api_client, method)(
        path, data={}, format='json',
    )

    assert response.status_code == 401


@pytest.mark.parametrize('path', [
    pytest.param(
        '/accounts/digest/unsubscribe',
        marks=pytest.mark.contract_error(
            'get', '/accounts/digest/unsubscribe',
        ),
    ),
    pytest.param(
        '/accounts/emails/unsubscribe',
        marks=pytest.mark.contract_error(
            'get', '/accounts/emails/unsubscribe',
        ),
    ),
])
def test_unsubscribe__invalid_token__html_error_and_unchanged_user(
    contract_api_client, path,
) -> None:
    owner = create_test_owner()
    original = (owner.is_digest_subscriber, owner.is_new_tasks_subscriber)

    response = contract_api_client.get(path, data={'token': 'invalid-token'})

    assert response.status_code == 200
    assert str(MSG_A_0008) in response.content.decode('utf-8')
    owner.refresh_from_db()
    assert (
        owner.is_digest_subscriber, owner.is_new_tasks_subscriber,
    ) == original


@pytest.mark.contract_error('get', '/accounts/users/{id}/transfer')
def test_transfer__invalid_token__redirect_error_and_unchanged_user(
    contract_api_client,
) -> None:
    owner = create_test_owner()
    original_account = owner.account_id

    response = contract_api_client.get(
        f'/accounts/users/{owner.id}/transfer',
        data={'token': 'invalid-token'},
    )

    assert response.status_code == 302
    assert response['Location'] == settings.EXPIRED_INVITE_PAGE
    owner.refresh_from_db()
    assert owner.account_id == original_account


@pytest.mark.parametrize('path', ['/pages/public', '/pages/public/signin'])
def test_public_pages__invalid_bearer__matches_error_contract(
    contract_api_client, path,
) -> None:
    contract_api_client.credentials(HTTP_AUTHORIZATION='Bearer invalid-token')

    response = contract_api_client.get(path)

    assert response.status_code == 401


def test_public_invite__unknown_id__matches_error_contract(
    contract_api_client,
) -> None:
    response = contract_api_client.get('/accounts/invites/2147483647')

    assert response.status_code == 404
