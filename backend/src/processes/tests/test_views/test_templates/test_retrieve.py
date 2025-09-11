import pytest

from src.accounts.enums import BillingPlanType
from src.processes.tests.fixtures import (
    create_test_user,
    create_test_template,
    create_test_account,
    create_invited_user,
    create_test_group,
)

from src.processes.models import (
    Template
)
from src.processes.enums import (
    PerformerType,
    FieldType,
    DueDateRule,
    OwnerType,
)
from src.accounts.services.user_transfer import (
    UserTransferService
)
from src.accounts.tokens import (
    TransferToken
)
from src.authentication.enums import AuthTokenType
from src.processes.services.templates.integrations import (
    TemplateIntegrationsService
)
from src.processes.messages import template as messages
from src.utils.dates import date_format


pytestmark = pytest.mark.django_db


class TestRetrieveTemplate:

    def test_retrieve__active__ok(self, api_client, mocker):

        # arrange
        user = create_test_user()
        user2 = create_test_user(
            email='user2@pneumaticapp',
            account=user.account
        )
        api_client.token_authenticate(user)
        owners = [
            {
                'type': OwnerType.USER,
                'source_id': str(user.id)
            },
            {
                'type': OwnerType.USER,
                'source_id': str(user2.id)
            },
        ]
        request_data = {
            'name': 'Template',
            'description': 'Desc',
            'owners': owners,
            'is_active': True,
            'finalizable': True,
            'kickoff': {
                'fields': [
                    {
                        'type': FieldType.USER,
                        'name': 'Field performer',
                        'description': 'desc',
                        'order': 1,
                        'is_required': True,
                        'api_name': 'user-field-1',
                        'default': 'default value'
                    }
                ]
            },
            'tasks': [
                {
                    'number': 1,
                    'api_name': 'task-1',
                    'name': 'First step',
                    'delay': None,
                    'description': 'Task desc',
                    'require_completion_by_all': True,
                    'raw_performers': [
                        {
                            'type': PerformerType.USER,
                            'source_id': user.id
                        }
                    ],
                    'fields': [
                        {
                            'type': FieldType.RADIO,
                            'name': 'Radio field',
                            'description': 'desc',
                            'order': 1,
                            'is_required': True,
                            'api_name': 'text-field-1',
                            'default': 'default value',
                            'selections': [
                                {'value': 'First selection'}
                            ]
                        }
                    ],
                    'checklists': [
                        {
                            'api_name': 'checklist-1',
                            'selections': [
                                {
                                    'api_name': 'cl-selection-1',
                                    'value': 'some value 1'
                                }
                            ]
                        }
                    ],
                    'raw_due_date': {
                        'api_name': 'raw-due-date-1',
                        'duration': '01:00:00',
                        'duration_months': 1,
                        'rule': DueDateRule.AFTER_WORKFLOW_STARTED,
                    },
                }
            ]
        }
        response = api_client.post(
            path='/templates',
            data=request_data
        )
        template = Template.objects.get(id=response.data['id'])
        api_request_mock = mocker.patch(
            'src.processes.services.templates.'
            'integrations.TemplateIntegrationsService.api_request',
        )

        # act
        response = api_client.get(f'/templates/{template.id}')

        # assert
        assert response.status_code == 200
        response_data = response.json()

        assert response_data.get('id')
        assert response_data['name'] == request_data['name']
        assert response_data['description'] == request_data['description']
        assert (
            response_data['owners'][0]['source_id'] == owners[0]['source_id']
        )
        assert response_data['owners'][0]['type'] == owners[0]['type']
        assert (
            response_data['owners'][1]['source_id'] == owners[1]['source_id']
        )
        assert response_data['owners'][1]['type'] == owners[1]['type']
        assert response_data['is_active'] == request_data['is_active']
        assert response_data['is_public'] is False
        assert response_data['public_url'] is not None
        assert response_data['finalizable'] == request_data['finalizable']
        assert response_data['updated_by'] == user.id
        assert response_data['tasks'][0]['api_name'] == 'task-1'
        assert response_data['date_updated'] == (
            template.date_updated.strftime(date_format)
        )
        assert response_data['date_updated_tsp'] == (
            template.date_updated.timestamp()
        )
        request_kickoff = request_data['kickoff']
        response_kickoff = response_data['kickoff']

        assert len(response_kickoff['fields']) == len(
            request_kickoff['fields'])
        request_kickoff_field = request_kickoff['fields'][0]
        response_kickoff_field = response_kickoff['fields'][0]
        assert response_kickoff_field['type'] == (
            request_kickoff_field['type']
        )
        assert response_kickoff_field['name'] == (
            request_kickoff_field['name']
        )
        assert response_kickoff_field['description'] == (
            request_kickoff_field['description']
        )
        assert response_kickoff_field['order'] == (
            request_kickoff_field['order']
        )
        assert response_kickoff_field['is_required'] == (
            request_kickoff_field['is_required']
        )
        assert response_kickoff_field['api_name'] == (
            request_kickoff_field['api_name']
        )
        assert response_kickoff_field['default'] == (
            request_kickoff_field['default']
        )

        assert len(response_data['tasks']) == len(
            request_data['tasks'])
        request_task = request_data['tasks'][0]
        response_task = response_data['tasks'][0]
        assert response_task.get('api_name')
        assert response_task['number'] == request_task['number']
        assert response_task['name'] == request_task['name']
        assert response_task['description'] == request_task['description']
        assert response_task['delay'] is None
        assert response_task['revert_task'] is None
        assert response_task['parents'] == []
        assert response_task['ancestors'] == []
        assert response_task['require_completion_by_all'] == (
            request_task['require_completion_by_all']
        )
        performers = response_task['raw_performers']
        assert len(performers) == 1
        assert performers[0]['type'] == PerformerType.USER
        assert performers[0]['source_id'] == str(user.id)

        assert len(response_task['fields']) == len(request_task['fields'])
        response_task_field = response_task['fields'][0]
        request_task_field = request_task['fields'][0]
        assert response_task_field['type'] == request_task_field['type']
        assert response_task_field['name'] == request_task_field['name']
        assert response_task_field['description'] == (
            request_task_field['description']
        )
        assert response_task_field['order'] == request_task_field['order']
        assert response_task_field['is_required'] == (
            request_task_field['is_required']
        )
        assert response_task_field['api_name'] == (
            request_task_field['api_name']
        )
        assert response_task_field['default'] == (
            request_task_field['default']
        )

        assert len(response_task_field['selections']) == len(
            request_task_field['selections']
        )
        response_selection = response_task_field['selections'][0]
        request_selection = request_task_field['selections'][0]
        assert response_selection.get('api_name')
        assert response_selection['value'] == request_selection['value']

        assert len(response_task['checklists'][0]['selections']) == 1
        checklist_data = response_task['checklists'][0]
        assert checklist_data.get('id') is None
        assert checklist_data['api_name'] == 'checklist-1'

        selection_data = checklist_data['selections'][0]
        assert selection_data['api_name'] == 'cl-selection-1'
        assert selection_data['value'] == 'some value 1'

        raw_due_date_data = response_task['raw_due_date']
        assert raw_due_date_data['api_name'] == 'raw-due-date-1'
        assert raw_due_date_data['duration'] == '01:00:00'
        assert raw_due_date_data['duration_months'] == 1
        assert raw_due_date_data['rule'] == DueDateRule.AFTER_WORKFLOW_STARTED
        assert raw_due_date_data['source_id'] is None

        api_request_mock.assert_not_called()

    def test_retrieve__draft__ok(self, api_client):

        # arrange
        user = create_test_user()
        api_client.token_authenticate(user)
        request_template_owners = [
            {
                'type': OwnerType.USER,
                'source_id': str(user.id),
                'api_name': 'owner-xcbjag'
            }
        ]
        request_data = {
            'is_active': False,
            'owners': request_template_owners,
            'kickoff': {},
            'tasks': [
                {
                    'number': 1,
                    'api_name': 'task-1',
                    'name': 'First step',
                    'raw_performers': [
                        {
                            'type': PerformerType.USER,
                            'source_id': user.id
                        }
                    ],
                    'checklists': [
                        {
                            'api_name': 'checklist-1',
                            'selections': [
                                {
                                    'api_name': 'cl-selection-1',
                                    'value': 'some value 1'
                                }
                            ]
                        }
                    ],
                    'raw_due_date': {
                        'api_name': 'raw-due-date-1',
                        'duration': '01:00:00',
                        'duration_months': 1,
                        'source_id': None,
                        'rule': DueDateRule.AFTER_WORKFLOW_STARTED,
                    }
                }
            ]
        }
        response = api_client.post(
            path='/templates',
            data=request_data
        )
        template = Template.objects.get(id=response.data['id'])

        # act
        response = api_client.get(f'/templates/{template.id}')

        # assert
        assert response.status_code == 200
        response_data = response.json()

        assert response_data.get('id')
        assert response_data['kickoff']
        assert response_data.get('tasks')
        assert response_data['name'] == ''
        assert response_data['is_active'] == request_data['is_active']
        assert response_data['updated_by'] == user.id
        assert response_data['date_updated'] == (
            template.get_draft()['date_updated']
        )
        assert response_data['date_updated_tsp'] == (
            template.get_draft()['date_updated_tsp']
        )
        assert response_data['owners'] == request_template_owners

        response_task = response_data['tasks'][0]
        assert response_task['parents'] == []
        assert response_task['ancestors'] == []
        assert response_task['api_name'] == 'task-1'
        assert len(response_task['checklists'][0]['selections']) == 1
        checklist_data = response_task['checklists'][0]
        assert checklist_data.get('id') is None
        assert checklist_data['api_name'] == 'checklist-1'

        selection_data = checklist_data['selections'][0]
        assert selection_data.get('id') is None
        assert selection_data['api_name'] == 'cl-selection-1'
        assert selection_data['value'] == 'some value 1'

        raw_due_date_data = response_task['raw_due_date']
        assert raw_due_date_data['api_name'] == 'raw-due-date-1'
        assert raw_due_date_data['duration'] == '01:00:00'
        assert raw_due_date_data['duration_months'] == 1
        assert raw_due_date_data['rule'] == DueDateRule.AFTER_WORKFLOW_STARTED
        assert raw_due_date_data['source_id'] is None

        template.refresh_from_db()
        assert template.is_active is False

    def test_retrieve__public_embed__ok(self, api_client):

        # arrange
        account = create_test_account(plan=BillingPlanType.PREMIUM)
        user = create_test_user(account=account)
        api_client.token_authenticate(user)

        template = create_test_template(
            user=user,
            is_active=True,
            is_public=True,
            is_embedded=True,
        )

        # act
        response = api_client.get(f'/templates/{template.id}')

        # assert
        assert response.status_code == 200
        assert response.data['id'] == template.id
        assert response.data['is_public'] is True
        assert response.data['public_url'] is not None
        assert response.data['is_embedded'] is True
        assert response.data['embed_url'] is not None

    def test_retrieve_active__after_template_owner_transfer__ok(
        self,
        api_client
    ):

        # arrange
        account_1 = create_test_account(
            name='transfer from',
            plan=BillingPlanType.FREEMIUM
        )
        account_1_owner = create_test_user(
            account=account_1,
            email='owner@test.test',
            is_account_owner=True
        )
        user_to_transfer = create_test_user(
            account=account_1,
            email='transfer@test.test',
            is_account_owner=False
        )

        new_account = create_test_account(name='new')
        new_account_owner = create_test_user(account=new_account)
        new_user = create_invited_user(
            user=new_account_owner,
            email='transfer@test.test',
        )
        token = TransferToken()
        token['prev_user_id'] = user_to_transfer.id
        token['new_user_id'] = new_user.id
        template = create_test_template(
            user=user_to_transfer,
            is_active=True,
            tasks_count=1
        )
        service = UserTransferService()
        service.accept_transfer(
            user_id=new_user.id,
            token_str=str(token)
        )
        api_client.token_authenticate(account_1_owner)

        # act
        response = api_client.get(f'/templates/{template.id}')

        # assert
        assert response.status_code == 200
        assert response.data['is_active'] is True
        assert len(response.data['owners']) == 1
        assert (
            response.data['owners'][0]['source_id'] == str(account_1_owner.id)
        )
        assert len(response.data['tasks'][0]['raw_performers']) == 1
        assert response.data['tasks'][0]['raw_performers'][0]['type'] == (
            PerformerType.USER
        )
        assert response.data['tasks'][0]['raw_performers'][0]['source_id'] == (
            str(account_1_owner.id)
        )

    def test_retrieve_draft__after_template_owner_transfer__changed(
        self,
        api_client
    ):
        # arrange
        account_1 = create_test_account(name='transfer from')
        account_1_owner = create_test_user(
            account=account_1,
            email='owner@test.test',
            is_account_owner=True
        )
        user_to_transfer = create_test_user(
            account=account_1,
            email='transfer@test.test',
            is_account_owner=False
        )
        api_client.token_authenticate(user_to_transfer)

        # act
        response = api_client.post(
            path='/templates',
            data={
                'name': 'Template',
                'owners': [
                    {
                        'type': OwnerType.USER,
                        'source_id': account_1_owner.id,
                        'api_name': 'user-1'
                    },
                    {
                        'type': OwnerType.USER,
                        'source_id': user_to_transfer.id,
                        'api_name': 'user-2'
                    }
                ],
                'is_active': False,
                'kickoff': {},
                'tasks': [
                    {
                        'number': 1,
                        'name': 'First step',
                        'raw_performers': [
                            {
                                'type': PerformerType.USER,
                                'source_id': user_to_transfer.id
                            }
                        ]
                    }
                ]
            }
        )
        template_id = response.data['id']
        new_account = create_test_account(name='new')
        new_account_owner = create_test_user(account=new_account)
        new_user = create_invited_user(
            user=new_account_owner,
            email='transfer@test.test',
        )
        token = TransferToken()
        token['prev_user_id'] = user_to_transfer.id
        token['new_user_id'] = new_user.id
        service = UserTransferService()
        service.accept_transfer(
            user_id=new_user.id,
            token_str=str(token)
        )
        api_client.token_authenticate(account_1_owner)

        # act
        response = api_client.get(f'/templates/{template_id}')

        # assert
        assert response.status_code == 200
        assert response.data['is_active'] is False
        assert len(response.data['owners']) == 1
        assert int(
            response.data['owners'][0]['source_id']
        ) == account_1_owner.id
        raw_performers = response.data['tasks'][0]['raw_performers']
        assert len(raw_performers) == 0

    def test_retrieve__api_request__ok(self, api_client, mocker):

        # arrange
        user = create_test_user()
        template = create_test_template(user=user)
        user_agent = 'Mozilla'
        get_user_agent_mock = mocker.patch(
            'src.processes.views.template.get_user_agent',
            return_value=user_agent
        )
        service_init_mock = mocker.patch.object(
            TemplateIntegrationsService,
            attribute='__init__',
            return_value=None
        )
        api_request_mock = mocker.patch(
            'src.processes.services.templates.'
            'integrations.TemplateIntegrationsService.api_request',
        )
        api_client.token_authenticate(
            user=user,
            token_type=AuthTokenType.API
        )

        # act
        response = api_client.get(f'/templates/{template.id}')

        # assert
        assert response.status_code == 200
        get_user_agent_mock.assert_called_once()
        api_request_mock.assert_called_once_with(
            template=template,
            user_agent=user_agent
        )
        service_init_mock.assert_called_once_with(
            account=user.account,
            is_superuser=False,
            user=user
        )

    def test_retrieve__not_template_owner__permission_denied(
        self,
        api_client
    ):

        # arrange
        user = create_test_user()
        template = create_test_template(user=user, tasks_count=1)
        user2 = create_test_user(
            email='user2@pneumaticapp',
            account=user.account,
            is_admin=True,
            is_account_owner=False
        )
        api_client.token_authenticate(user2)

        # act
        response = api_client.get(f'/templates/{template.id}')

        # assert
        assert response.status_code == 403
        assert response.data['detail'] == messages.MSG_PT_0023

    def test_retrieve__raw_performers_group__ok(self, api_client, mocker):

        # arrange
        user = create_test_user()
        user2 = create_test_user(
            email='user2@pneumaticapp',
            account=user.account
        )
        group = create_test_group(user.account, users=[user, user2])
        api_client.token_authenticate(user)
        owners = [
            {
                'type': OwnerType.USER,
                'source_id': str(user.id)
            },
            {
                'type': OwnerType.USER,
                'source_id': str(user2.id)
            },
        ]
        request_data = {
            'name': 'Template',
            'owners': owners,
            'is_active': True,
            'kickoff': {},
            'tasks': [
                {
                    'number': 1,
                    'name': 'First step',
                    'raw_performers': [
                        {
                            'type': PerformerType.GROUP,
                            'source_id': group.id
                        }
                    ],
                }
            ]
        }
        response = api_client.post(
            path='/templates',
            data=request_data
        )
        template = Template.objects.get(id=response.data['id'])
        mocker.patch(
            'src.processes.services.templates.'
            'integrations.TemplateIntegrationsService.api_request',
        )

        # act
        response = api_client.get(f'/templates/{template.id}')

        # assert
        assert response.status_code == 200
        raw_performers_data = response.json()['tasks'][0]['raw_performers']
        assert len(raw_performers_data) == 1
        assert raw_performers_data[0]['type'] == PerformerType.GROUP
        assert raw_performers_data[0]['source_id'] == str(group.id)
