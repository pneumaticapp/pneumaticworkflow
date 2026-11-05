"""Real regressions for nullable workflows and conditional/event responses."""

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone
import pytest

from src.accounts.enums import BillingPlanType
from src.openapi.workflow_enums import WORKFLOW_EVENT_TYPE_CHOICES
from src.processes.enums import FieldType, WorkflowEventType, WorkflowStatus
from src.processes.models.templates.fields import (
    FieldTemplate,
    FieldTemplateSelection,
)
from src.processes.serializers.templates.field import (
    FieldTemplateListSerializer,
)
from src.processes.serializers.workflows.events import WorkflowEventSerializer
from src.processes.serializers.workflows.workflow import (
    WorkflowDetailsSerializer,
    WorkflowListSerializer,
)
from src.processes.services.events import WorkflowEventService
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_owner,
    create_test_template,
    create_test_workflow,
)
from src.reports.serializers import EventHighlightsSerializer

pytestmark = pytest.mark.django_db
UserModel = get_user_model()


@pytest.fixture
def remaining_owner(contract_api_client) -> UserModel:
    owner = create_test_owner(account=create_test_account(
        plan=BillingPlanType.UNLIMITED, billing_sync=False,
    ))
    contract_api_client.token_authenticate(owner)
    return owner


@pytest.mark.parametrize('limit', [None, 1], ids=['default', 'limit=1'])
def test_workflow_list__deleted_template__nullable_contract(
    contract_api_client, remaining_owner, limit,
) -> None:
    workflow = create_test_workflow(remaining_owner, tasks_count=1)
    workflow.template.delete()

    response = contract_api_client.get(
        '/workflows', data={} if limit is None else {'limit': limit},
    )

    assert response.status_code == 200
    row = response.json()['results'][0]
    assert row['id'] == workflow.id
    assert row['template'] is None


def test_workflow_detail__deleted_template__nullable_contract(
    contract_api_client, remaining_owner,
) -> None:
    workflow = create_test_workflow(remaining_owner, tasks_count=1)
    workflow.template.delete()

    response = contract_api_client.get(f'/workflows/{workflow.id}')

    assert response.status_code == 200
    assert response.json()['template'] is None


@pytest.mark.parametrize('limit', [None, 1], ids=['default', 'limit=1'])
def test_workflow_list__external_starter__nullable_contract(
    contract_api_client, remaining_owner, limit,
) -> None:
    workflow = create_test_workflow(
        remaining_owner, tasks_count=1, is_external=True,
    )

    response = contract_api_client.get(
        '/workflows', data={} if limit is None else {'limit': limit},
    )

    assert response.status_code == 200
    row = response.json()['results'][0]
    assert row['id'] == workflow.id
    assert row['workflow_starter'] is None


def test_workflow_detail__external_starter__nullable_contract(
    contract_api_client, remaining_owner,
) -> None:
    workflow = create_test_workflow(
        remaining_owner, tasks_count=1, is_external=True,
    )

    response = contract_api_client.get(f'/workflows/{workflow.id}')

    assert response.status_code == 200
    assert response.json()['workflow_starter'] is None


def test_workflow_snooze__deleted_template__nullable_contract(
    contract_api_client, remaining_owner,
) -> None:
    workflow = create_test_workflow(remaining_owner, tasks_count=1)
    workflow.template.delete()

    response = contract_api_client.post(
        f'/workflows/{workflow.id}/snooze',
        data={'date': (timezone.now() + timedelta(days=1)).timestamp()},
        format='json',
    )

    assert response.status_code == 200
    assert response.json()['template'] is None
    workflow.refresh_from_db()
    assert workflow.status == WorkflowStatus.DELAYED


@pytest.mark.parametrize('limit', [None, 1], ids=['default', 'limit=1'])
def test_template_list__conditional_selections__matches_contract(
    contract_api_client, remaining_owner, limit,
) -> None:
    owner = remaining_owner
    template = create_test_template(owner, is_active=True, tasks_count=1)
    for order, field_type in enumerate((FieldType.STRING, FieldType.DROPDOWN)):
        field = FieldTemplate.objects.create(
            name=f'Field {order}', type=field_type,
            kickoff=template.kickoff_instance, template=template,
            order=order, api_name=f'contract-field-{order}',
            account=owner.account,
        )
        if field_type == FieldType.DROPDOWN:
            FieldTemplateSelection.objects.create(
                field_template=field, template=template,
                value='First option', api_name='contract-selection',
            )

    response = contract_api_client.get(
        '/templates', data={} if limit is None else {'limit': limit},
    )

    assert response.status_code == 200
    body = response.json()
    row = (body['results'] if isinstance(body, dict) else body)[0]
    fields = {field['type']: field for field in row['kickoff']['fields']}
    assert 'selections' not in fields[FieldType.STRING]
    assert fields[FieldType.DROPDOWN]['selections'] == ['First option']


@pytest.mark.parametrize('limit', [None, 1], ids=['default', 'limit=1'])
@pytest.mark.parametrize('resource', ['workflow', 'task', 'highlights'])
def test_subworkflow_event__real_service__matches_contract(
    contract_api_client, remaining_owner, resource, limit,
) -> None:
    owner = remaining_owner
    workflow = create_test_workflow(owner, tasks_count=1)
    task = workflow.tasks.first()
    child = create_test_workflow(owner, tasks_count=1, ancestor_task=task)
    event = WorkflowEventService.sub_workflow_run_event(
        workflow=workflow, sub_workflow=child, user=owner,
        after_create_actions=False,
    )
    path = {
        'workflow': f'/workflows/{workflow.id}/events',
        'task': f'/v2/tasks/{task.id}/events',
        'highlights': '/reports/highlights',
    }[resource]

    response = contract_api_client.get(
        path, data={} if limit is None else {'limit': limit},
    )

    assert response.status_code == 200
    body = response.json()
    rows = body['results'] if isinstance(body, dict) else body
    row = next(row for row in rows if row['id'] == event.id)
    assert row['type'] == WorkflowEventType.SUB_WORKFLOW_RUN
    assert row['task']['sub_workflow']['id'] == child.id


def test_response_metadata__runtime_field_options_preserved(
    http_contract,
) -> None:
    components = http_contract.document['components']['schemas']
    for serializer in (WorkflowListSerializer, WorkflowDetailsSerializer):
        for name in ('template', 'workflow_starter'):
            assert serializer().fields[name].allow_null is False
    assert FieldTemplateListSerializer().fields['selections'].read_only
    assert 'selections' not in components['FieldTemplateList']['required']
    for serializer in (WorkflowEventSerializer, EventHighlightsSerializer):
        assert dict(serializer().fields['type'].choices) == dict(
            WorkflowEventType.CHOICES,
        )
        component = components[serializer.__name__.removesuffix('Serializer')]
        field = component['properties']['type']
        references = [field.get('$ref'), *(
            value.get('$ref') for value in field.get('allOf', [])
        )]
        assert '#/components/schemas/WorkflowEventTypeEnum' in references
    assert WorkflowEventType.SUB_WORKFLOW_RUN not in dict(
        WorkflowEventType.CHOICES,
    )
    assert components['WorkflowEventTypeEnum']['enum'] == [
        value for value, _ in WORKFLOW_EVENT_TYPE_CHOICES
    ]
