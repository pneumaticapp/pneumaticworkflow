"""Remaining Core 401/403 contracts through actual authentication."""

from typing import Tuple

from django.core.cache import caches
import pytest

from src.accounts.models import User
from src.processes.models.templates.template import Template
from src.processes.tests.fixtures import create_test_owner

pytestmark = pytest.mark.django_db

UNAUTHORIZED_OPERATIONS = (
    ('put', '/accounts/account'),
    ('get', '/accounts/groups/{id}/count-workflows'),
    ('post', '/accounts/invites'),
    ('get', '/accounts/invites/{id}'),
    ('post', '/accounts/invites/{id}/resend'),
    ('post', '/accounts/invites/decline'),
    ('get', '/accounts/invites/token'),
    ('delete', '/accounts/notifications/{id}'),
    ('post', '/accounts/user/activate-vacation'),
    ('post', '/accounts/user/deactivate-vacation'),
    ('get', '/accounts/users'),
    ('patch', '/accounts/users/{id}'),
    ('delete', '/accounts/users/{id}'),
    ('get', '/accounts/users/{id}/count-workflows'),
    ('post', '/accounts/users/{id}/delete'),
    ('post', '/accounts/users/{id}/toggle-admin'),
    ('post', '/accounts/users/{user_id}/api-keys'),
    ('delete', '/accounts/users/{user_id}/api-keys/{id}'),
    ('post', '/accounts/users/reassign'),
    ('get', '/applications/integrations/{id}'),
    ('post', '/datasets/{id}/items'),
    ('post', '/notifications/device'),
    ('delete', '/notifications/device/{token}'),
    ('post', '/notifications/ios/reset-push-counter'),
    ('get', '/payment/card-setup'),
    ('get', '/payment/confirm'),
    ('get', '/payment/customer-portal'),
    ('get', '/payment/default-payment-method'),
    ('post', '/payment/purchase'),
    ('post', '/payment/subscription/cancel'),
    ('get', '/reports/dashboard/workflows/by-tasks'),
    ('get', '/reports/dashboard/workflows/overview'),
    ('get', '/reports/highlights'),
    ('get', '/templates'),
    ('delete', '/templates/{id}'),
    ('get', '/templates/{id}/integrations'),
    ('post', '/templates/{id}/run'),
    ('get', '/templates/integrations'),
    ('post', '/templates/public/run'),
    ('post', '/templates/system/import'),
    ('get', '/v2/tasks/{id}'),
    ('post', '/v2/tasks/{id}/create-group-performer'),
    ('get', '/v2/tasks/{id}/events'),
    ('post', '/v2/tasks/{id}/revert'),
    ('get', '/v2/tasks/checklists/{id}'),
    ('post', '/v2/tasks/checklists/{id}/mark'),
    ('post', '/v2/tasks/checklists/{id}/unmark'),
    ('get', '/v3/tasks'),
    ('patch', '/workflows/comments/{id}'),
    ('delete', '/workflows/comments/{id}'),
    ('get', '/workflows/count/by-current-performer'),
    ('get', '/workflows/count/by-template-task'),
    ('get', '/workflows/count/by-workflow-starter'),
)

FORBIDDEN_OPERATIONS = (
    ('get', '/accounts/account'),
    ('get', '/accounts/api-keys'),
    ('delete', '/accounts/api-keys/{id}'),
    ('get', '/accounts/groups'),
    ('get', '/accounts/groups/{id}/count-workflows'),
    ('get', '/accounts/invites'),
    ('post', '/accounts/invites'),
    ('get', '/accounts/invites/{id}'),
    ('post', '/accounts/invites/{id}/resend'),
    ('get', '/accounts/invites/token'),
    ('get', '/accounts/notifications'),
    ('delete', '/accounts/notifications/{id}'),
    ('get', '/accounts/notifications/count'),
    ('post', '/accounts/notifications/read'),
    ('get', '/accounts/public/account'),
    ('get', '/accounts/public/users'),
    ('get', '/accounts/user'),
    ('post', '/accounts/user/activate-vacation'),
    ('get', '/accounts/user/contacts'),
    ('get', '/accounts/user/counters'),
    ('post', '/accounts/user/deactivate-vacation'),
    ('get', '/accounts/users'),
    ('get', '/accounts/users/{id}'),
    ('patch', '/accounts/users/{id}'),
    ('post', '/accounts/users/{id}/activate-vacation'),
    ('get', '/accounts/users/{id}/count-workflows'),
    ('post', '/accounts/users/{id}/deactivate-vacation'),
    ('get', '/accounts/users/{user_id}/api-keys'),
    ('get', '/accounts/users/active-count'),
    ('get', '/accounts/users/privileges'),
    ('get', '/applications/integrations'),
    ('get', '/applications/integrations/{id}'),
    ('post', '/datasets/{id}/item'),
    ('post', '/datasets/{id}/items'),
    ('put', '/datasets/{id}/items'),
    ('patch', '/datasets/items/{id}'),
    ('delete', '/datasets/items/{id}'),
    ('get', '/faq'),
    ('get', '/navigation/menu/{slug}'),
    ('get', '/payment/card-setup'),
    ('get', '/payment/default-payment-method'),
    ('post', '/payment/purchase'),
    ('get', '/reports/dashboard/tasks/breakdown'),
    ('get', '/reports/dashboard/tasks/by-steps'),
    ('get', '/reports/dashboard/tasks/overview'),
    ('get', '/reports/dashboard/workflows/breakdown'),
    ('get', '/reports/dashboard/workflows/by-tasks'),
    ('get', '/reports/dashboard/workflows/overview'),
    ('get', '/reports/highlights'),
    ('get', '/services/steps-by-description'),
    ('post', '/templates/by-name'),
    ('post', '/templates/by-steps'),
    ('get', '/templates/public'),
    ('post', '/templates/public/run'),
    ('get', '/templates/system'),
    ('post', '/templates/system/{id}/fill'),
    ('get', '/templates/system/categories'),
    ('post', '/templates/system/import'),
    ('get', '/templates/titles-by-events'),
    ('get', '/templates/titles-by-owners'),
    ('delete', '/v2/tasks/{id}/due-date'),
    ('get', '/v2/tasks/checklists/{id}'),
    ('post', '/v2/tasks/checklists/{id}/mark'),
    ('post', '/v2/tasks/checklists/{id}/unmark'),
    ('get', '/v3/tasks'),
    ('put', '/workflows/{id}'),
    ('get', '/workflows/count/by-current-performer'),
    ('get', '/workflows/count/by-template-task'),
    ('get', '/workflows/count/by-workflow-starter'),
)

PUBLIC_TEMPLATE_OPERATIONS = frozenset({
    '/accounts/public/account', '/accounts/public/users',
    '/templates/public', '/templates/public/run',
})
PRIVATE_INVITE_OPERATIONS = frozenset({
    '/accounts/invites/{id}', '/accounts/invites/token',
})


@pytest.fixture(autouse=True)
def authentication_error_environment(settings) -> None:
    settings.PRIVATE_API_CHECK_IP = False
    settings.PROJECT_CONF = {**settings.PROJECT_CONF, 'AI': False}
    for alias in ('default', 'auth', 'session'):
        caches[alias].clear()


@pytest.fixture
def public_auth_context() -> Tuple[User, Template]:
    owner = create_test_owner()
    template = Template.objects.create(
        account=owner.account, name='Authentication contract context',
        is_active=True, is_public=True,
    )
    return owner, template


def concrete_url(path: str) -> str:
    if path == '/accounts/invites/{id}':
        return path.format(id='00000000-0000-4000-8000-000000000001')
    return path.format(id=2147483647, user_id=2147483647,
                       slug='main', token='contract-device-token')


@pytest.mark.parametrize('method,path', UNAUTHORIZED_OPERATIONS)
def test_core_authentication__invalid_bearer__401_contract(
    contract_api_client, method, path,
) -> None:
    contract_api_client.credentials(
        HTTP_AUTHORIZATION='Bearer invalid-contract-session-token',
    )

    response = getattr(contract_api_client, method)(
        concrete_url(path), data={}, format='json',
    )

    assert response.status_code == 401


@pytest.mark.parametrize('method,path', FORBIDDEN_OPERATIONS)
def test_core_authorization__real_wrong_context__403_contract(
    contract_api_client, public_auth_context, settings, method, path,
) -> None:
    owner, template = public_auth_context
    if path in PUBLIC_TEMPLATE_OPERATIONS:
        # A genuine user session has no public-template authorization context.
        contract_api_client.token_authenticate(owner)
    else:
        # Public authentication succeeds but deliberately yields AnonymousUser;
        # account/user permissions then reject this real public credential.
        contract_api_client.credentials(
            HTTP_X_PUBLIC_AUTHORIZATION=f'Token {template.public_id}',
        )
    if path in PRIVATE_INVITE_OPERATIONS:
        settings.PRIVATE_API_CHECK_IP = True
        settings.PRIVATE_API_IP_WHITELIST = ['192.0.2.1']

    response = getattr(contract_api_client, method)(
        concrete_url(path), data={}, format='json',
        HTTP_REMOTE_ADDR='192.0.2.2',
    )

    assert response.status_code == 403
