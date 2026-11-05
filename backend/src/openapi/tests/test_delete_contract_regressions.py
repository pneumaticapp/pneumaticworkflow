"""Deletion contracts use real services, not injected service exceptions."""

from typing import Any

from django.core.cache import caches
import pytest

from src.accounts.enums import BillingPlanType
from src.accounts.models import User
from src.ai.tests.fixtures import create_test_agent
from src.datasets.models import Dataset, DatasetItem
from src.generics.tests.clients import PneumaticApiClient
from src.openapi.tests.http_contracts import HttpContract
from src.processes.tests.fixtures import create_test_account, create_test_owner


OPERATIONS = (
    ('agent', '/ai/agents/{id}'),
    ('dataset', '/datasets/{id}'),
)
MOCKED_DELETE_CASES = (
    'src/ai/tests/test_views/test_agents/test_destroy.py'
    '::test_destroy__by_owner__ok',
    'src/ai/tests/test_views/test_agents/test_destroy.py'
    '::test_destroy__service_exception__validation_error',
    'src/datasets/tests/test_views/test_datasets/test_destroy.py'
    '::test_destroy__ok',
    'src/datasets/tests/test_views/test_datasets/test_destroy.py'
    '::test_destroy__service_exception__validation_error',
)


@pytest.fixture
def deletion_owner(
    contract_api_client: PneumaticApiClient, settings: Any, db: None,
) -> User:
    settings.PRIVATE_API_CHECK_IP = False
    settings.PROJECT_CONF = {**settings.PROJECT_CONF, 'AI': True}
    for alias in ('default', 'auth', 'session'):
        caches[alias].clear()
    account = create_test_account(
        plan=BillingPlanType.UNLIMITED, billing_sync=False,
    )
    owner = create_test_owner(account=account)
    contract_api_client.token_authenticate(owner)
    return owner


@pytest.mark.parametrize('body', [
    b'', b'{invalid JSON', b'null', b'{"unused": true}',
])
@pytest.mark.parametrize('kind,path', OPERATIONS)
def test_delete__real_service__soft_deletes_resource_and_related_record(
    contract_api_client: PneumaticApiClient,
    deletion_owner: User,
    mocker: Any,
    kind: str,
    path: str,
    body: bytes,
) -> None:
    # Only dispatch to the external notification worker is replaced.
    notification = mocker.patch(
        'src.datasets.services.dataset.'
        'send_dataset_deleted_notification.delay',
    )
    if kind == 'agent':
        resource = create_test_agent(account=deletion_owner.account)
        related = resource.user
    else:
        resource = Dataset.objects.create(
            account=deletion_owner.account, name='Deletion contract dataset',
        )
        related = DatasetItem.objects.create(
            account=deletion_owner.account, dataset=resource, value='Item',
        )
    url = path.format(id=resource.id)

    response = contract_api_client.delete(
        f'{url}?ordering=invalid&limit=-1', data=body,
        content_type='application/json',
    )

    assert response.status_code == 204
    assert not response.content
    resource.refresh_from_db()
    related.refresh_from_db()
    assert resource.is_deleted is True
    assert related.is_deleted is True
    assert not type(resource).objects.filter(id=resource.id).exists()
    deletion_owner.refresh_from_db()
    assert deletion_owner.is_deleted is False
    deletion_owner.account.refresh_from_db()
    assert deletion_owner.account.is_deleted is False
    if kind == 'dataset':
        notification.assert_called_once()
        assert notification.call_args.kwargs['account_id'] == (
            deletion_owner.account_id
        )
    else:
        notification.assert_not_called()
        resource.provider.refresh_from_db()
        assert resource.provider.is_deleted is False


@pytest.mark.parametrize('kind,path', OPERATIONS)
def test_delete__missing_resource__real_not_found(
    contract_api_client: PneumaticApiClient,
    deletion_owner: User,
    path: str,
    kind: str,
) -> None:
    response = contract_api_client.delete(path.format(id=2147483647))

    assert response.status_code == 404
    assert isinstance(response.json()['detail'], str)


@pytest.mark.parametrize('kind,path', OPERATIONS)
def test_delete__schema__does_not_advertise_unreachable_bad_request(
    http_contract: HttpContract, kind: str, path: str,
) -> None:
    operation = http_contract.document['paths'][path]['delete']

    assert set(operation['responses']) == {'204', '401', '403', '404'}
    assert 'requestBody' not in operation


@pytest.mark.parametrize('case', MOCKED_DELETE_CASES)
def test_delete__mocked_service_case__excluded_from_contract_registry(
    pytestconfig: Any, case: str,
) -> None:
    assert case not in pytestconfig._api_contract_cases
