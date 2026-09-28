import pytest

from src.processes.enums import (
    OwnerRole,
    ConditionAction,
    FieldType,
    OwnerType,
    PerformerType,
    PredicateOperator,
    PredicateType,
)
from src.processes.models.templates.task import TaskTemplate
from src.processes.models.templates.template import Template
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_owner,
    create_test_user,
)

pytestmark = pytest.mark.django_db


def test_clone__preserves_task_api_name__ok(mocker, api_client):

    # arrange
    task_api_name = 'task-699a25'
    account = create_test_account()
    user = create_test_owner(account=account)
    api_client.token_authenticate(user)
    create_response = api_client.post(
        path='/templates',
        data={
            'name': 'Template',
            'is_active': True,
            'owners': [
                {
                    'type': OwnerType.USER,
                    'source_id': user.id,
                    'role': OwnerRole.OWNER,
                },
            ],
            'kickoff': {},
            'tasks': [
                {
                    'number': 1,
                    'name': 'First step',
                    'api_name': task_api_name,
                    'raw_performers': [
                        {
                            'type': PerformerType.USER,
                            'source_id': user.id,
                        },
                    ],
                },
            ],
        },
    )
    assert create_response.status_code == 200
    origin_template = Template.objects.get(
        id=create_response.data['id'],
    )
    create_integrations_mock = mocker.patch(
        'src.processes.services.templates.'
        'integrations.TemplateIntegrationsService.'
        'create_integrations_for_template',
    )

    # act
    clone_response = api_client.post(
        f'/templates/{origin_template.id}/clone',
    )

    # assert
    assert clone_response.status_code == 200
    assert create_response.data['tasks'][0]['api_name'] == task_api_name
    assert clone_response.data['tasks'][0]['api_name'] == task_api_name
    create_integrations_mock.assert_called_once_with(
        template=Template.objects.get(id=clone_response.data['id']),
    )


def test_clone__activate_with_same_api_name__ok(mocker, api_client):

    # arrange
    task_api_name = 'task-699a25'
    account = create_test_account()
    user = create_test_owner(account=account)
    api_client.token_authenticate(user)
    create_response = api_client.post(
        path='/templates',
        data={
            'name': 'Template',
            'is_active': True,
            'owners': [
                {
                    'type': OwnerType.USER,
                    'source_id': user.id,
                    'role': OwnerRole.OWNER,
                },
            ],
            'kickoff': {},
            'tasks': [
                {
                    'number': 1,
                    'name': 'First step',
                    'api_name': task_api_name,
                    'raw_performers': [
                        {
                            'type': PerformerType.USER,
                            'source_id': user.id,
                        },
                    ],
                },
            ],
        },
    )
    assert create_response.status_code == 200
    origin_template = Template.objects.get(
        id=create_response.data['id'],
    )
    create_integrations_mock = mocker.patch(
        'src.processes.services.templates.'
        'integrations.TemplateIntegrationsService.'
        'create_integrations_for_template',
    )
    clone_response = api_client.post(
        f'/templates/{origin_template.id}/clone',
    )
    assert clone_response.status_code == 200
    clone_data = clone_response.data
    clone_data['is_active'] = True
    template_updated_mock = mocker.patch(
        'src.processes.services.templates.'
        'integrations.TemplateIntegrationsService.template_updated',
    )

    # act
    activate_response = api_client.put(
        f'/templates/{clone_data["id"]}',
        data=clone_data,
    )

    # assert
    assert activate_response.status_code == 200
    assert origin_template.tasks.get().api_name == task_api_name
    assert TaskTemplate.objects.get(
        template_id=clone_data['id'],
    ).api_name == task_api_name
    create_integrations_mock.assert_called_once_with(
        template=Template.objects.get(id=clone_data['id']),
    )
    template_updated_mock.assert_called_once_with(
        template=Template.objects.get(id=clone_data['id']),
    )


class TestCopyTemplateTask:

    @pytest.mark.parametrize('is_active', [True, False])
    def test_clone__ok(self, is_active, api_client):

        user = create_test_user()
        api_client.token_authenticate(user)

        request_data = {
            'number': 1,
            'name': '{{field-2}}',
            'description': '{{field-2}}',
            'delay': None,
            'require_completion_by_all': False,
            'raw_performers': [
                {
                    'type': PerformerType.USER,
                    'source_id': str(user.id),
                },
            ],
        }

        response = api_client.post(
            path='/templates',
            data={
                'name': 'Template',
                'is_active': is_active,
                'owners': [
                    {
                        'type': OwnerType.USER,
                        'source_id': user.id,
                        'role': OwnerRole.OWNER,
                    },
                ],
                'kickoff': {
                    'fields': [
                        {
                            'order': 1,
                            'name': 'Task name',
                            'type': FieldType.STRING,
                            'api_name': 'field-2',
                            'is_required': True,
                        },
                        {
                            'order': 0,
                            'name': 'User name',
                            'type': FieldType.USER,
                            'api_name': 'without_prefix_name',
                            'is_required': True,
                        },
                    ],
                },
                'tasks': [request_data],
            },
        )
        template = Template.objects.get(id=response.data['id'])

        # act
        response = api_client.post(
            f'/templates/{template.id}/clone',
        )

        # assert
        assert response.status_code == 200
        assert len(response.data['tasks']) == 1
        task_data = response.data['tasks'][0]
        assert not task_data.get('id')
        assert task_data['number'] == request_data['number']
        assert task_data['name'] == '{{field-2}}'
        assert task_data['description'] == '{{field-2}}'
        assert task_data['delay'] == request_data['delay']
        assert task_data['require_completion_by_all'] == (
            request_data['require_completion_by_all']
        )
        performers = task_data['raw_performers']
        assert len(performers) == 1
        assert performers[0]['type'] == PerformerType.USER
        assert performers[0]['source_id'] == str(user.id)

    def test_clone__due_date__ok(
        self,
        api_client,
    ):

        # arrange
        user = create_test_user()
        api_client.token_authenticate(user)
        duration = '10:00:00'

        response = api_client.post(
            path='/templates',
            data={
                'name': 'Template',
                'is_active': True,
                'owners': [
                    {
                        'type': OwnerType.USER,
                        'source_id': user.id,
                        'role': OwnerRole.OWNER,
                    },
                ],
                'kickoff': {},
                'tasks': [
                    {
                        'number': 1,
                        'name': 'First Step',
                        'api_name': 'task-1',
                        'raw_performers': [{
                            'type': PerformerType.USER,
                            'source_id': user.id,
                        }],
                        'raw_due_date': {
                            'api_name': 'raw-due-date-bwybf0',
                            'rule': 'after task started',
                            'duration_months': 0,
                            'duration': duration,
                            'source_id': 'task-1',
                        },
                    },
                ],
            },
        )
        template = Template.objects.get(id=response.data['id'])

        # act
        response = api_client.post(
            f'/templates/{template.id}/clone',
        )

        # assert
        assert response.status_code == 200
        task_data = response.data['tasks'][0]
        assert task_data['raw_due_date']['duration'] == duration

    def test_clone__return_task__ok(
        self,
        mocker,
        api_client,
    ):

        # arrange
        task_1_api_name = 'task-1'
        user = create_test_user()
        mocker.patch(
            'src.processes.serializers.templates.task.'
            'AnalyticService.templates_task_due_date_created',
        )
        conditions = [
            {
                'order': 1,
                'action': ConditionAction.START_TASK,
                'rules': [
                    {
                        'predicates': [
                            {
                                'field_type': PredicateType.TASK,
                                'operator': PredicateOperator.COMPLETED,
                                'field': task_1_api_name,
                                'value': None,
                            },
                        ],
                    },
                ],
            },
        ]

        api_client.token_authenticate(user)
        response = api_client.post(
            path='/templates',
            data={
                'name': 'Template',
                'is_active': True,
                'owners': [
                    {
                        'type': OwnerType.USER,
                        'source_id': user.id,
                        'role': OwnerRole.OWNER,
                    },
                ],
                'kickoff': {},
                'tasks': [
                    {
                        'number': 1,
                        'name': 'First Step',
                        'api_name': task_1_api_name,
                        'raw_performers': [{
                            'type': PerformerType.USER,
                            'source_id': user.id,
                        }],
                    },
                    {
                        'number': 2,
                        'name': 'Second Step',
                        'raw_performers': [{
                            'type': PerformerType.USER,
                            'source_id': user.id,
                        }],
                        'conditions': conditions,
                        'revert_task': task_1_api_name,
                    },
                ],
            },
        )
        template = Template.objects.get(id=response.data['id'])

        # act
        response = api_client.post(
            f'/templates/{template.id}/clone',
        )

        # assert
        assert response.status_code == 200
        task_data = response.data['tasks'][1]
        assert task_data['revert_task'] == task_1_api_name
