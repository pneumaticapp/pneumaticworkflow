"""Exercise every paginated Core operation with nonempty real records."""

import pytest

from src.accounts.enums import (
    BillingPlanType,
    LeaseLevel,
    NotificationType,
    SourceType as ContactSource,
)
from src.accounts.models import APIKey, Contact, Notification
from src.accounts.serializers.notifications import (
    NotificationTaskSerializer,
    NotificationWorkflowSerializer,
)
from src.ai.enums import AIVendor
from src.ai.models import AIProvider
from src.ai.tests.fixtures import create_test_agent
from src.applications.models import Integration
from src.authentication.tokens import PneumaticToken
from src.faq.models import FaqItem
from src.pages.enums import PageType
from src.pages.models import Page
from src.processes.enums import SysTemplateType, WorkflowStatus
from src.processes.models.templates.system_template import (
    SystemTemplate,
    SystemTemplateCategory,
)
from src.processes.services.events import WorkflowEventService
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_dataset,
    create_test_owner,
    create_test_shared_fieldset,
    create_test_template,
    create_test_user,
    create_test_workflow,
    create_test_attachment,
)
from src.storage.enums import AccessType, SourceType as AttachmentSource

pytestmark = pytest.mark.django_db

PAGINATED_OPERATIONS = (
    '/accounts/api-keys',
    '/accounts/notifications',
    '/accounts/public/users',
    '/accounts/user/contacts',
    '/accounts/users',
    '/accounts/users/{user_id}/api-keys',
    '/accounts/users/privileges',
    '/ai/agents',
    '/ai/providers',
    '/applications/integrations',
    '/attachments',
    '/datasets',
    '/faq',
    '/fieldsets',
    '/pages/public',
    '/reports/highlights',
    '/templates',
    '/templates/export',
    '/templates/system',
    '/templates/titles-by-owners',
    '/tenants',
    '/v2/tasks/{id}/events',
    '/v3/tasks',
    '/workflows',
    '/workflows/{id}/events',
    '/workflows/fields',
)

ENVELOPE_DEFAULTS = frozenset({
    '/attachments', '/workflows', '/workflows/fields',
})


def test_pagination_matrix__covers_all_documented_paginators(
    http_contract,
) -> None:
    discovered = {
        path for path, item in http_contract.document['paths'].items()
        if 'get' in item and http_contract.is_paginated(item['get'])
    }
    assert discovered == set(PAGINATED_OPERATIONS)
    for path in discovered:
        parameters = http_contract.document['paths'][path]['get'].get(
            'parameters', [],
        )
        assert any(
            value['in'] == 'query' and value['name'] == 'limit'
            for value in parameters
        ), path


@pytest.fixture
def pagination_records(request, contract_api_client) -> tuple:
    operation = request.param
    account = create_test_account(
        plan=BillingPlanType.UNLIMITED, billing_sync=False,
    )
    owner = create_test_owner(account=account)
    contract_api_client.token_authenticate(owner)
    path, query = operation, {}

    if operation in ('/accounts/users', '/accounts/users/privileges'):
        create_test_user(account=account, email='member@example.com')
    elif operation in (
        '/accounts/api-keys', '/accounts/users/{user_id}/api-keys',
    ):
        for index in range(2):
            APIKey.objects.create(
                account=account, user=owner, name=f'Contract key {index}',
                token=PneumaticToken.create(user=owner, for_api_key=True),
            )
        path = operation.format(user_id=owner.id)
    elif operation == '/accounts/public/users':
        create_test_user(account=account, email='member@example.com')
        template = create_test_template(
            user=owner, is_active=True, is_public=True,
        )
        contract_api_client.credentials(
            HTTP_X_PUBLIC_AUTHORIZATION=f'Token {template.public_id}',
        )
    elif operation == '/accounts/user/contacts':
        for index in range(2):
            Contact.objects.create(
                account=account, user=owner,
                first_name=f'Contact {index}', last_name='Reader',
                source=ContactSource.GOOGLE, source_id=f'contact-{index}',
                email=f'contact-{index}@example.com', job_title='Reviewer',
            )
    elif operation == '/accounts/notifications':
        workflow = create_test_workflow(owner, tasks_count=1)
        task = workflow.tasks.first()
        for index in range(2):
            Notification.objects.create(
                account=account, user=owner, author=owner,
                type=NotificationType.COMMENT, text=f'Comment {index}',
                task_json=NotificationTaskSerializer(
                    instance=task, notification_type=NotificationType.COMMENT,
                ).data,
                workflow_json=NotificationWorkflowSerializer(workflow).data,
            )
    elif operation in ('/ai/agents', '/ai/providers'):
        for index in range(2):
            provider = AIProvider(
                account=account, name=f'Provider {index}',
                base_url='https://example.com/v1', vendor=AIVendor.CUSTOM,
            )
            provider.api_key = 'local-contract-test-key'
            provider.save()
            if operation == '/ai/agents':
                create_test_agent(
                    account=account, provider=provider, name=f'Agent {index}',
                )
    elif operation == '/applications/integrations':
        for index in range(2):
            Integration.objects.create(
                name=f'Integration {index}', short_description='Summary',
                long_description='Description', button_text='Open',
                logo='https://example.com/logo.svg',
                url='https://example.com/integration', is_active=True,
            )
    elif operation == '/attachments':
        for index in range(2):
            create_test_attachment(
                account, file_id=f'pagination-file-{index}',
                access_type=AccessType.ACCOUNT,
                source_type=AttachmentSource.ACCOUNT,
            )
    elif operation == '/datasets':
        for index in range(2):
            create_test_dataset(
                account, name=f'Dataset {index}', items_count=1,
            )
    elif operation == '/faq':
        for index in range(2):
            FaqItem.objects.create(
                order=index, is_active=True,
                question=f'Question {index}', answer='Answer',
            )
    elif operation == '/fieldsets':
        for index in range(2):
            create_test_shared_fieldset(account, name=f'Fieldset {index}')
    elif operation == '/pages/public':
        for slug in (PageType.SIGNIN, PageType.RESET_PASSWORD):
            Page.objects.create(
                title=slug, description='Description', slug=slug,
            )
    elif operation in (
        '/templates', '/templates/export', '/templates/titles-by-owners',
    ):
        for index in range(2):
            create_test_template(
                owner, is_active=True, name=f'Template {index}',
            )
    elif operation == '/templates/system':
        for index in range(2):
            SystemTemplate.objects.create(
                name=f'Library template {index}', is_active=True,
                type=SysTemplateType.LIBRARY,
                template={
                    'name': 'Workflow', 'kickoff': {},
                    'tasks': [{'name': 'Review', 'number': 1}],
                },
            )
    elif operation == '/tenants':
        for index in range(2):
            create_test_account(
                name=f'Tenant {index}', tenant_name=f'Tenant {index}',
                master_account=account, lease_level=LeaseLevel.TENANT,
                plan=BillingPlanType.UNLIMITED, billing_sync=False,
            )
    elif operation in (
        '/reports/highlights', '/v2/tasks/{id}/events',
        '/workflows/{id}/events',
    ):
        workflow = create_test_workflow(owner, tasks_count=1)
        task = workflow.tasks.first()
        for index in range(2):
            if operation == '/reports/highlights' and index:
                workflow = create_test_workflow(owner, tasks_count=1)
                task = workflow.tasks.first()
            WorkflowEventService.comment_created_event(
                text=f'Comment {index}', task=task, user=owner,
                after_create_actions=False,
            )
        if operation.startswith('/v2/tasks/'):
            path = operation.format(id=task.id)
        elif operation.startswith('/workflows/'):
            path = operation.format(id=workflow.id)
    elif operation in ('/v3/tasks', '/workflows', '/workflows/fields'):
        for index in range(2):
            create_test_workflow(
                owner, tasks_count=1, name=f'Workflow {index}',
                status=(WorkflowStatus.DONE if operation == '/workflows/fields'
                        else WorkflowStatus.RUNNING),
            )
    else:
        raise AssertionError(f'No pagination preparation for {operation}')
    return operation, path, query


@pytest.mark.parametrize('pagination_records', PAGINATED_OPERATIONS,
                         indirect=True)
@pytest.mark.parametrize('limit', [None, 1], ids=['default', 'limit=1'])
def test_all_paginated_operations__nonempty_models__both_modes(
    contract_api_client, pagination_records, limit,
) -> None:
    # arrange
    operation, path, query = pagination_records
    if limit is not None:
        query = {**query, 'limit': limit}

    # act
    response = contract_api_client.get(path, data=query)

    # assert
    assert response.status_code == 200
    data = response.json()
    if limit is not None or operation in ENVELOPE_DEFAULTS:
        assert isinstance(data, dict)
        assert {'count', 'next', 'previous', 'results'} <= set(data)
        rows = data['results']
    else:
        assert isinstance(data, list)
        rows = data
    assert rows
    if limit is None:
        assert len(rows) >= 2
    else:
        assert len(rows) == 1


@pytest.mark.parametrize('limit', [None, 1], ids=['default', 'limit=1'])
def test_categories__limit_is_ignored__flat_response(
    contract_api_client, http_contract, limit,
) -> None:
    owner = create_test_owner()
    contract_api_client.token_authenticate(owner)
    for index in range(2):
        SystemTemplateCategory.objects.create(
            name=f'Category {index}', is_active=True, order=index,
            icon='https://example.com/icon.svg', color='#ffffff',
            template_color='#000000',
        )
    response = contract_api_client.get(
        '/templates/system/categories',
        data={} if limit is None else {'limit': limit},
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) == 2
    operation = http_contract.document['paths'][
        '/templates/system/categories'
    ]['get']
    parameters = {item['name'] for item in operation.get('parameters', [])}
    assert not parameters & {'limit', 'offset'}
