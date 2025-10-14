# ruff: noqa: UP031
import pytest
from django.conf import settings

from src.accounts.enums import BillingPlanType
from src.accounts.models import (
    UserInvite,
)
from src.accounts.services.user import UserService
from src.authentication.enums import AuthTokenType
from src.authentication.tokens import (
    EmbedToken,
    PublicToken,
)
from src.processes.enums import (
    FieldType,
    OwnerType,
    PerformerType,
    PredicateOperator,
)
from src.processes.messages import template as messages
from src.processes.models.templates.conditions import (
    ConditionTemplate,
    PredicateTemplate,
    RuleTemplate,
)
from src.processes.models.templates.fields import (
    FieldTemplate,
    FieldTemplateSelection,
)
from src.processes.models.templates.raw_performer import RawPerformerTemplate
from src.processes.models.templates.task import TaskTemplate
from src.processes.models.templates.template import Template
from src.processes.services.templates.integrations import (
    TemplateIntegrationsService,
)
from src.processes.tests.fixtures import (
    create_invited_user,
    create_test_account,
    create_test_group,
    create_test_owner,
    create_test_template,
    create_test_user,
)
from src.utils.validation import ErrorCode

pytestmark = pytest.mark.django_db


def test_create__only_required_fields__defaults_ok(
    mocker,
    api_client,
):

    # arrange
    account = create_test_account()
    user = create_test_user(account=account)
    api_client.token_authenticate(user)
    create_integrations_mock = mocker.patch(
        'src.processes.services.templates.'
        'integrations.TemplateIntegrationsService.'
        'create_integrations_for_template',
    )
    api_request_mock = mocker.patch(
        'src.processes.services.templates.'
        'integrations.TemplateIntegrationsService.api_request',
    )
    template_create_mock = mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_created',
    )
    kickoff_create_mock = mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_kickoff_created',
    )
    request_data = {
        'name': 'Template',
        'owners': [
            {
                'type': OwnerType.USER,
                'source_id': user.id,
            },
        ],
        'is_active': True,
        'kickoff': {},
        'tasks': [
            {
                'number': 1,
                'name': 'First step',
                'raw_performers': [
                    {
                        'type': PerformerType.USER,
                        'source_id': user.id,
                    },
                ],
            },
        ],
    }

    # act
    response = api_client.post(
        path='/templates',
        data=request_data,
    )

    # assert
    assert response.status_code == 200
    response_data = response.json()

    assert response.data['owners'][0].get('api_name')
    assert response.data['owners'][0]['source_id'] == str(user.id)
    assert response.data['owners'][0]['type'] == OwnerType.USER
    assert response_data['name'] == request_data['name']
    assert response_data['description'] == ''
    assert response_data['is_active'] is True
    assert response_data['is_public'] is False
    assert response_data['public_url'] is not None
    assert response_data['finalizable'] is False
    assert response_data['wf_name_template'] is None
    template = Template.objects.get(id=response_data['id'])
    assert template.tasks.first().account_id == user.account_id
    assert template.owners.count() == 1
    assert template.name == request_data['name']
    assert template.description == ''
    assert template.is_active == request_data['is_active']
    assert template.finalizable is False
    assert template.wf_name_template is None
    account.refresh_from_db()
    create_integrations_mock.assert_called_with(
        template=template,
    )
    api_request_mock.assert_not_called()
    template_create_mock.assert_called_once()
    kickoff_create_mock.assert_called_once()


def test_create__only_required_fields_with_group__defaults_ok(
    mocker,
    api_client,
):

    # arrange
    account = create_test_account()
    user = create_test_user(account=account)
    user_in_group = create_test_user(
        account=account,
        email='test2@pneumatic.app',
    )
    group = create_test_group(account, users=[user_in_group])
    api_client.token_authenticate(user)
    create_integrations_mock = mocker.patch(
        'src.processes.services.templates.'
        'integrations.TemplateIntegrationsService.'
        'create_integrations_for_template',
    )
    api_request_mock = mocker.patch(
        'src.processes.services.templates.'
        'integrations.TemplateIntegrationsService.api_request',
    )
    template_create_mock = mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_created',
    )
    kickoff_create_mock = mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_kickoff_created',
    )
    request_data = {
        'name': 'Template',
        'owners': [
            {
                'api_name': 'owner-gft3g3625',
                'type': OwnerType.USER,
                'source_id': user.id,
            },
            {
                'api_name': 'owner-gf216g1625',
                'type': OwnerType.GROUP,
                'source_id': group.id,
            },
        ],
        'is_active': True,
        'kickoff': {},
        'tasks': [
            {
                'number': 1,
                'name': 'First step',
                'raw_performers': [
                    {
                        'type': PerformerType.USER,
                        'source_id': user.id,
                    },
                ],
            },
        ],
    }

    # act
    response = api_client.post(
        path='/templates',
        data=request_data,
    )

    # assert
    assert response.status_code == 200
    response_data = response.json()

    assert response.data['owners'][0]['api_name'] == 'owner-gf216g1625'
    assert response.data['owners'][0]['source_id'] == str(group.id)
    assert response.data['owners'][0]['type'] == OwnerType.GROUP
    assert response.data['owners'][1]['api_name'] == 'owner-gft3g3625'
    assert response.data['owners'][1]['source_id'] == str(user.id)
    assert response.data['owners'][1]['type'] == OwnerType.USER
    assert response_data['name'] == request_data['name']
    assert response_data['description'] == ''
    assert response_data['is_active'] is True
    assert response_data['is_public'] is False
    assert response_data['public_url'] is not None
    assert response_data['finalizable'] is False
    assert response_data['wf_name_template'] is None
    template = Template.objects.get(id=response_data['id'])
    assert template.tasks.first().account_id == user.account_id
    assert template.owners.count() == 2
    assert template.name == request_data['name']
    assert template.description == ''
    assert template.is_active == request_data['is_active']
    assert template.finalizable is False
    assert template.wf_name_template is None
    account.refresh_from_db()
    create_integrations_mock.assert_called_with(
        template=template,
    )
    api_request_mock.assert_not_called()
    template_create_mock.assert_called_once()
    kickoff_create_mock.assert_called_once()


def test_create__all_fields__ok(
    api_client,
    mocker,
):

    # arrange
    account = create_test_account(plan=BillingPlanType.PREMIUM)
    user = create_test_user(account=account)
    user2 = create_test_user(
        account=account,
        email='test2@pneumatic.app',
    )
    conditions = [
        {
            'rules': [
                {
                    'predicates': [
                        {
                            'field': 'field-1',
                            'field_type': FieldType.RADIO,
                            'operator': PredicateOperator.EQUAL,
                            'value': 'selection-1',
                            'api_name': 'predicate-1',
                        },
                    ],
                    'api_name': 'rule-1',
                },
            ],
            'api_name': 'condition-1',
            'order': 1,
            'action': 'skip_task',
        },
    ]
    kickoff_fields = [
        {
            'type': FieldType.RADIO,
            'name': 'Radio field',
            'order': 1,
            'api_name': 'field-1',
            'selections': [
                {
                    'value': 'First selection',
                    'api_name': 'selection-1',
                },
            ],
        },
    ]
    api_client.token_authenticate(user)
    mocker.patch(
        'src.processes.services.templates.'
        'integrations.TemplateIntegrationsService.'
        'create_integrations_for_template',
    )
    template_create_mock = mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_created',
    )
    kickoff_create_mock = mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_kickoff_created',
    )
    request_data = {
        'description': 'Desc',
        'name': 'Name',
        'owners': [
            {
                'type': OwnerType.USER,
                'source_id': user.id,
            },
            {
                'type': OwnerType.USER,
                'source_id': user2.id,
            },
        ],
        'is_active': True,
        'is_public': False,
        'finalizable': True,
        'kickoff': {
            'fields': kickoff_fields,
        },
        'tasks': [
            {
                'number': 1,
                'name': 'First step',
                'raw_performers': [
                    {
                        'type': PerformerType.USER,
                        'source_id': user.id,
                    },
                ],
                'fields': [
                    {
                        'type': FieldType.RADIO,
                        'name': 'Radio field',
                        'order': 1,
                        'api_name': 'field-2',
                        'selections': [
                            {
                                'value': 'First selection',
                                'api_name': 'selection-2',
                            },
                        ],
                    },
                ],
                'conditions': conditions,
            },
            {
                'number': 2,
                'name': 'Second step',
                'api_name': 'task-1',
                'raw_performers': [
                    {
                        'type': PerformerType.USER,
                        'source_id': user.id,
                    },
                ],
                'fields': [
                    {
                        'type': FieldType.RADIO,
                        'name': 'Radio field',
                        'order': 1,
                        'api_name': 'field-3',
                        'selections': [
                            {
                                'value': 'First selection',
                                'api_name': 'selection-3',
                            },
                        ],
                    },
                ],
                'raw_due_date': {
                    'api_name': 'raw-due-date-bwybf0',
                    'rule': 'after task started',
                    'duration_months': 0,
                    'duration': '0 00:05:00',
                    'source_id': 'task-1',
                },
            },
            {
                'number': 3,
                'name': 'Third step',
                'raw_performers': [
                    {
                        'type': PerformerType.USER,
                        'source_id': user.id,
                    },
                ],
                'fields': [
                    {
                        'type': FieldType.RADIO,
                        'name': 'Radio field',
                        'order': 1,
                        'api_name': 'field-4',
                        'selections': [
                            {
                                'value': 'First selection',
                                'api_name': 'selection-4',
                            },
                        ],
                    },
                ],
                'delay': '1 12:00:00',
            },
        ],
    }

    # act
    response = api_client.post(
        path='/templates',
        data=request_data,
    )

    # assert
    assert response.status_code == 200
    response_data = response.json()

    assert response_data.get('id')
    assert response_data.get('kickoff')
    assert len(response_data['owners']) == len(request_data['owners'])
    assert response_data['name'] == request_data['name']
    assert response_data['description'] == request_data['description']
    assert response_data['is_active'] == request_data['is_active']
    assert response_data['is_public'] == request_data['is_public']
    assert response_data['public_url'] is not None
    assert response_data['embed_url'] is not None
    assert response_data['finalizable'] == request_data['finalizable']
    assert response_data['updated_by'] == user.id
    assert response_data.get('date_updated')

    template = Template.objects.get(id=response_data['id'])
    template_owners = list(template.owners.order_by(
        'id',
    ).values_list('user_id', 'type'))
    assert template_owners[0][0] == user.id
    assert template_owners[0][1] == OwnerType.USER
    assert template_owners[1][0] == user2.id
    assert template_owners[1][1] == OwnerType.USER
    assert template.name == request_data['name']
    assert template.description == request_data['description']
    assert template.is_active == request_data['is_active']
    assert template.is_public == request_data['is_public']
    assert template.public_url is not None
    assert template.embed_url is not None
    assert template.finalizable == request_data['finalizable']
    assert template.updated_by is not None
    assert template.date_updated.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    assert template.kickoff_instance is not None
    assert template.tasks.exists()
    account.refresh_from_db()

    template_create_mock.assert_called_once_with(
        user=user,
        template=template,
        auth_type=AuthTokenType.USER,
        is_superuser=False,
        kickoff_fields_count=1,
        tasks_count=3,
        tasks_fields_count=3,
        due_in_count=1,
        delays_count=1,
        conditions_count=1,
    )
    kickoff_create_mock.assert_called_once_with(
        user=user,
        template=template,
        auth_type=AuthTokenType.USER,
        is_superuser=False,
    )


def test_create__current_user_in_group__ok(
    mocker,
    api_client,
):

    # arrange
    account = create_test_account(plan=BillingPlanType.PREMIUM)
    user = create_test_user(is_account_owner=False, account=account)
    another_user = create_test_user(
        account=account,
        email='another@pneumatic.app',
    )
    api_client.token_authenticate(another_user)
    group = create_test_group(account, users=[another_user])
    mocker.patch(
        'src.processes.services.templates.'
        'integrations.TemplateIntegrationsService.'
        'create_integrations_for_template',
    )
    template_create_mock = mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_created',
    )
    kickoff_create_mock = mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_kickoff_created',
    )

    # act
    response = api_client.post(
        '/templates',
        data={
            'name': 'Template',
            'owners': [
                {
                    'api_name': 'owner-gft3g3625',
                    'type': OwnerType.GROUP,
                    'source_id': group.id,
                },
            ],
            'is_active': True,
            'description': '',
            'kickoff': {},
            'tasks': [
                {
                    'name': 'First step',
                    'number': 1,
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

    # assert
    assert response.status_code == 200
    response_data = response.json()

    # assert response.data['owners'][0]['api_name'] == 'owner-gf216g1625'
    assert response.data['owners'][0]['source_id'] == str(group.id)
    assert response.data['owners'][0]['type'] == OwnerType.GROUP
    template = Template.objects.get(id=response_data['id'])

    template_create_mock.assert_called_once_with(
        user=another_user,
        template=template,
        auth_type=AuthTokenType.USER,
        is_superuser=False,
        kickoff_fields_count=0,
        tasks_count=1,
        tasks_fields_count=0,
        due_in_count=0,
        delays_count=0,
        conditions_count=0,
    )
    kickoff_create_mock.assert_called_once_with(
        user=another_user,
        template=template,
        auth_type=AuthTokenType.USER,
        is_superuser=False,
    )


def test_create__draft__ok(
    mocker,
    api_client,
):
    # arrange
    template_create_mock = mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_created',
    )
    kickoff_create_mock = mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_kickoff_created',
    )
    user = create_test_user()
    user_2 = create_test_user(
        is_account_owner=False,
        email='test@test.test',
        account=user.account,
    )
    api_client.token_authenticate(user)
    create_integrations_mock = mocker.patch(
        'src.processes.services.templates.'
        'integrations.TemplateIntegrationsService.'
        'create_integrations_for_template',
    )
    request_data = {
        'owners': [
            {
                'type': OwnerType.USER,
                'source_id': user.id,
            },
            {
                'type': OwnerType.USER,
                'source_id': user_2.id,
            },
        ],
        'is_active': False,
        'kickoff': {
            'fields': [],
            'description': "",
        },
        'tasks': [],
    }

    # act
    response = api_client.post(
        path='/templates',
        data=request_data,
    )

    # assert
    assert response.status_code == 200
    response_data = response.json()

    assert response_data.get('id')
    assert response_data['owners'][0]['source_id'] == str(user.id)
    assert response_data['owners'][0]['type'] == OwnerType.USER
    assert response_data['owners'][1]['source_id'] == str(user_2.id)
    assert response_data['owners'][1]['type'] == OwnerType.USER
    assert response_data['name'] == ''
    assert not response_data.get('description')
    assert response_data['is_active'] is False
    assert response_data['is_public'] is False
    assert response_data['is_embedded'] is False
    assert response_data['public_url'] is not None
    assert response_data['embed_url'] is not None
    assert response_data['updated_by'] == user.id
    assert response_data.get('date_updated')
    assert response_data['tasks'] == request_data['tasks']

    template = Template.objects.get(id=response_data['id'])
    assert template.owners.count() == 1
    assert template.owners.first().user_id == user.id
    assert template.name == 'New template'
    assert template.is_active is False
    assert template.is_public is False
    assert template.public_url is not None
    assert template.embed_url is not None
    assert not template.tasks.exists()

    template_draft = template.draft
    assert template_draft is not None
    assert template_draft.draft is not None
    assert template_draft.draft['is_active'] is False
    assert template_draft.draft['name'] == ''
    assert template_draft.draft['owners'][0]['source_id'] == str(user.id)
    assert template_draft.draft['owners'][0]['type'] == OwnerType.USER
    assert template_draft.draft['owners'][1]['source_id'] == str(user_2.id)
    assert template_draft.draft['owners'][1]['type'] == OwnerType.USER
    assert template_draft.draft['is_public'] is False
    assert template_draft.draft['is_embedded'] is False
    assert template_draft.draft['public_url'] is not None
    assert template_draft.draft['embed_url'] is not None

    template_create_mock.assert_called_once_with(
        user=user,
        template=template,
        auth_type=AuthTokenType.USER,
        is_superuser=False,
        kickoff_fields_count=0,
        tasks_count=0,
        tasks_fields_count=0,
        due_in_count=0,
        delays_count=0,
        conditions_count=0,
    )
    kickoff_create_mock.assert_called_once_with(
        user=user,
        template=template,
        auth_type=AuthTokenType.USER,
        is_superuser=False,
    )
    create_integrations_mock.assert_called_with(
        template=template,
    )


def test_create__draft_null_tasks__create_empty_tasks(
    mocker,
    api_client,
):
    # arrange
    user = create_test_owner()
    api_client.token_authenticate(user)
    mocker.patch(
        'src.processes.services.templates.'
        'integrations.TemplateIntegrationsService.'
        'create_integrations_for_template',
    )
    mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_created',
    )
    mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_kickoff_created',
    )
    request_data = {
        'owners': [
            {
                'type': OwnerType.USER,
                'source_id': user.id,
            },
        ],
        'is_active': False,
        'kickoff': {},
        'tasks': None,
    }

    # act
    response = api_client.post(
        path='/templates',
        data=request_data,
    )

    # assert
    assert response.status_code == 200
    assert response.data['tasks'] == []


def test_create__draft_skip_tasks__create_empty_tasks(
    mocker,
    api_client,
):
    # arrange
    user = create_test_owner()
    api_client.token_authenticate(user)
    mocker.patch(
        'src.processes.services.templates.'
        'integrations.TemplateIntegrationsService.'
        'create_integrations_for_template',
    )
    mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_created',
    )
    mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_kickoff_created',
    )
    request_data = {
        'owners': [
            {
                'type': OwnerType.USER,
                'source_id': user.id,
            },
        ],
        'is_active': False,
        'kickoff': {},
    }

    # act
    response = api_client.post(
        path='/templates',
        data=request_data,
    )

    # assert
    assert response.status_code == 200
    assert response.data['tasks'] == []


def test_create__draft_null_owners__create_default_owner(
    mocker,
    api_client,
):
    # arrange
    user = create_test_owner()
    api_client.token_authenticate(user)
    mocker.patch(
        'src.processes.services.templates.'
        'integrations.TemplateIntegrationsService.'
        'create_integrations_for_template',
    )
    mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_created',
    )
    mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_kickoff_created',
    )
    request_data = {
        'owners': None,
        'is_active': False,
        'kickoff': {},
        'tasks': None,
    }

    # act
    response = api_client.post(
        path='/templates',
        data=request_data,
    )

    # assert
    assert response.status_code == 200
    assert len(response.data['owners']) == 1
    assert response.data['owners'][0]['type'] == OwnerType.USER
    assert response.data['owners'][0]['source_id'] == str(user.id)
    assert response.data['owners'][0]['api_name']


@pytest.mark.parametrize(
    'owner', (
        {
            'type': None,
            'source_id': '1',
            'api_name': 'some',
        },
        {
            'source_id': '1',
            'api_name': 'some',
        },
        1,
        {
            'type': OwnerType.USER,
            'api_name': 'some',
        },
    ),
)
def test_create__draft_invalid_owners__create_default_owner(
    mocker,
    owner,
    api_client,
):
    # arrange
    user = create_test_owner()
    api_client.token_authenticate(user)
    mocker.patch(
        'src.processes.services.templates.'
        'integrations.TemplateIntegrationsService.'
        'create_integrations_for_template',
    )
    mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_created',
    )
    mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_kickoff_created',
    )
    request_data = {
        'owners': [owner],
        'is_active': False,
        'kickoff': {},
        'tasks': None,
    }

    # act
    response = api_client.post(
        path='/templates',
        data=request_data,
    )

    # assert
    assert response.status_code == 200
    assert len(response.data['owners']) == 1
    assert response.data['owners'][0]['type'] == OwnerType.USER
    assert response.data['owners'][0]['source_id'] == str(user.id)
    assert response.data['owners'][0]['api_name']


def test_create__public__ok(mocker, api_client):

    # arrange
    template_create_mock = mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_created',
    )
    kickoff_create_mock = mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_kickoff_created',
    )
    user = create_test_user()
    api_client.token_authenticate(user)
    token = 'a' * PublicToken.token_length
    public_url = f'{settings.FORMS_URL}/{token}'
    token_mock = mocker.patch.object(
        PublicToken,
        attribute='__str__',
        return_value=token,
    )
    mocker.patch(
        'src.processes.services.templates.'
        'integrations.TemplateIntegrationsService.'
        'create_integrations_for_template',
    )

    # act
    response = api_client.post(
        path='/templates',
        data={
            'name': 'Template',
            'owners': [
                {
                    'type': OwnerType.USER,
                    'source_id': user.id,
                },
            ],
            'is_active': True,
            'is_public': True,
            'kickoff': {},
            'tasks': [
                {
                    'number': 1,
                    'name': 'First step',
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

    # assert
    assert response.status_code == 200
    assert response.data['is_public'] is True
    assert response.data['public_url'] == public_url
    template = Template.objects.get(id=response.data['id'])
    assert template.is_public is True
    assert template.public_url == public_url
    token_mock.assert_called_once()
    template_create_mock.assert_called_once()
    kickoff_create_mock.assert_called_once()


def test_create__embed__ok(api_client, mocker):

    # arrange
    account = create_test_account(plan=BillingPlanType.PREMIUM)
    user = create_test_user(account=account)
    api_client.token_authenticate(user)
    token = 'a' * EmbedToken.token_length
    embed_url = f'{settings.FORMS_URL}/embed/{token}'
    token_mock = mocker.patch.object(
        EmbedToken,
        attribute='__str__',
        return_value=token,
    )
    mocker.patch(
        'src.processes.services.templates.'
        'integrations.TemplateIntegrationsService.'
        'create_integrations_for_template',
    )

    # act
    response = api_client.post(
        path='/templates',
        data={
            'name': 'Template',
            'owners': [
                {
                    'type': OwnerType.USER,
                    'source_id': user.id,
                },
            ],
            'is_active': True,
            'is_embedded': True,
            'kickoff': {},
            'tasks': [
                {
                    'number': 1,
                    'name': 'First step',
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

    # assert
    assert response.status_code == 200
    assert response.data['is_embedded'] is True
    assert response.data['embed_url'] == embed_url
    template = Template.objects.get(id=response.data['id'])
    assert template.is_embedded is True
    assert template.embed_url == embed_url
    token_mock.assert_called_once()


@pytest.mark.parametrize(
    'value',
    [
        '192.168.0.1',
        'https://192.168.0.1',
        'https://192.168.0.1/templates?param=12;param2=',
        'https://my.pneumatic.app',
        'https://my.pneumatic.app/templates?param=12;param2=',
        'http://my.pneumatic.app',
        'my.pneumatic.app',
        'my.pneumatic.app/templates?param=12;param2=',
    ],
)
def test_create__public_success_url__ok(value, api_client, mocker):

    # arrange
    account = create_test_account(plan=BillingPlanType.PREMIUM)
    user = create_test_user(account=account)
    api_client.token_authenticate(user)
    mocker.patch(
        'src.processes.services.templates.'
        'integrations.TemplateIntegrationsService.'
        'create_integrations_for_template',
    )
    template_create_mock = mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_created',
    )
    kickoff_create_mock = mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_kickoff_created',
    )

    # act
    response = api_client.post(
        path='/templates',
        data={
            'name': 'Template',
            'owners': [
                {
                    'type': OwnerType.USER,
                    'source_id': user.id,
                },
            ],
            'is_active': True,
            'is_public': True,
            'public_success_url': value,
            'kickoff': {},
            'tasks': [
                {
                    'number': 1,
                    'name': 'First step',
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

    # assert
    assert response.status_code == 200
    assert response.data['public_success_url'] == value
    template = Template.objects.get(id=response.data['id'])
    assert template.public_success_url == value
    template_create_mock.assert_called_once()
    kickoff_create_mock.assert_called_once()


@pytest.mark.parametrize(
    'value',
    [
        'https://my.pneumatic.app/broken space/here',
        'my.pneumatic.app/broken space/here',
        'ssh://my.pneumatic.app',
        'my.pneumatic.app http://my.pneumatic.app',
        'relative/path/to',
        'relative/path',
        '/relative/path/',
        '://my.pneumatic.app',
    ],
)
def test_create__public_success_url_invalid__validation_error(
    value,
    mocker,
    api_client,
):

    # arrange
    template_create_mock = mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_created',
    )
    kickoff_create_mock = mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_kickoff_created',
    )
    account = create_test_account(plan=BillingPlanType.PREMIUM)
    user = create_test_user(account=account)
    api_client.token_authenticate(user)
    request_data = {
        'name': 'Template',
        'owners': [
            {
                'type': OwnerType.USER,
                'source_id': user.id,
            },
        ],
        'is_active': True,
        'is_public': True,
        'public_success_url': value,
        'kickoff': {},
        'tasks': [
            {
                'number': 1,
                'name': 'First step',
                'raw_performers': [
                    {
                        'type': PerformerType.USER,
                        'source_id': user.id,
                    },
                ],
            },
        ],
    }

    # act
    response = api_client.post(
        path='/templates',
        data=request_data,
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == messages.MSG_PT_0021
    assert response.data['details']['name'] == 'public_success_url'
    template_create_mock.assert_not_called()
    kickoff_create_mock.assert_not_called()


def test_create__name_is_required__validation_error(
    mocker,
    api_client,
):

    # arrange
    template_create_mock = mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_created',
    )
    kickoff_create_mock = mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_kickoff_created',
    )
    user = create_test_user()
    api_client.token_authenticate(user)
    request_data = {
        'name': None,
        'owners': [
            {
                'type': OwnerType.USER,
                'source_id': user.id,
            },
        ],
        'is_active': True,
        'kickoff': {},
        'tasks': [
            {
                'number': 1,
                'name': 'First step',
                'raw_performers': [
                    {
                        'type': PerformerType.USER,
                        'source_id': user.id,
                    },
                ],
            },
        ],
    }

    # act
    response = api_client.post(
        path='/templates',
        data=request_data,
    )

    # assert
    message = 'This field may not be null.'
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    assert response.data['details']['name'] == 'name'
    assert response.data['details']['reason'] == message
    assert 'api_name' not in response.data['details']
    template_create_mock.assert_not_called()
    kickoff_create_mock.assert_not_called()


def test_create__not_name_in_draft__ok(
    mocker,
    api_client,
):
    # arrange
    template_create_mock = mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_created',
    )
    kickoff_create_mock = mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_kickoff_created',
    )
    user = create_test_user()
    api_client.token_authenticate(user)
    mocker.patch(
        'src.processes.services.templates.'
        'integrations.TemplateIntegrationsService.'
        'create_integrations_for_template',
    )
    request_data = {
        'owners': [
            {
                'type': OwnerType.USER,
                'source_id': user.id,
            },
        ],
        'is_active': False,
        'is_public': True,
        'kickoff': {},
        'tasks': [],
    }

    # act
    response = api_client.post(
        path='/templates',
        data=request_data,
    )

    # assert
    assert response.status_code == 200
    response_data = response.json()

    assert response_data['name'] == ''
    assert response_data['is_public'] is True
    assert response.data['public_url'] is not None

    template = Template.objects.get(id=response_data['id'])
    assert template.name == 'New template'
    assert template.is_public is False
    assert template.public_url is not None
    template_create_mock.assert_called_once()
    kickoff_create_mock.assert_called_once()


def test_create__name_is_required_two_errors__validation_error(
    mocker,
    api_client,
):
    # arrange
    template_create_mock = mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_created',
    )
    kickoff_create_mock = mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_kickoff_created',
    )

    user = create_test_user()
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        path='/templates',
        data={
            'name': None,
            'owners': [
                {
                    'type': OwnerType.USER,
                    'source_id': user.id,
                },
            ],
            'is_active': True,
            'kickoff': {},
            'tasks': [
                {
                    'number': 1,
                    'name': 'First step',
                    'api_name': 'task-55',
                    'performers': None,
                },
            ],
        },
    )

    # assert
    message = 'This field may not be null.'
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    assert response.data['details']['name'] == 'name'
    assert response.data['details']['reason'] == message
    assert 'api_name' not in response.data['details']
    template_create_mock.assert_not_called()
    kickoff_create_mock.assert_not_called()


def test_create__user_field_in_public_task__ok(
    mocker,
    api_client,
):

    # arrange
    template_create_mock = mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_created',
    )
    kickoff_create_mock = mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_kickoff_created',
    )
    user = create_test_user()
    api_client.token_authenticate(user)
    mocker.patch(
        'src.processes.services.templates.'
        'integrations.TemplateIntegrationsService.'
        'create_integrations_for_template',
    )
    request_data = {
        'description': 'Desc',
        'name': 'Name',
        'owners': [
            {
                'type': OwnerType.USER,
                'source_id': user.id,
            },
        ],
        'is_active': True,
        'is_public': True,
        'finalizable': True,
        'kickoff': {},
        'tasks': [
            {
                'number': 1,
                'name': 'Second step',
                'raw_performers': [
                    {
                        'type': PerformerType.USER,
                        'source_id': user.id,
                    },
                ],
                'fields': [
                    {
                        'type': FieldType.USER,
                        'name': 'User field',
                        'description': 'desc',
                        'order': 1,
                        'is_required': True,
                        'api_name': 'user-field-1',
                    },
                ],
            },
        ],
    }

    # act
    response = api_client.post(
        path='/templates',
        data=request_data,
    )

    # assert
    assert response.status_code == 200
    template_create_mock.assert_called_once()
    kickoff_create_mock.assert_called_once()


def test_create__public_url__ok(mocker):
    mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_created',
    )
    mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_kickoff_created',
    )
    user = create_test_user()
    template = create_test_template(
        user=user,
        is_active=True,
        is_public=True,
        tasks_count=1,
    )
    host = settings.FORMS_URL
    assert len(template.public_id) == 8
    assert template.public_url == f'{host}/{template.public_id}'


def test_create__public_url_limit_is_reached__validation_error(
    mocker,
    api_client,
):
    # assert
    template_create_mock = mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_created',
    )
    kickoff_create_mock = mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_kickoff_created',
    )
    user = create_test_user()
    api_client.token_authenticate(user)
    token = 'a' * PublicToken.token_length
    template = create_test_template(
        user=user,
        is_active=True,
        is_public=True,
    )
    template.public_id = token
    template.save(update_fields=('public_id',))
    token_mock = mocker.patch.object(
        PublicToken,
        attribute='__str__',
        return_value=token,
    )
    mocker.patch(
        'src.processes.services.templates.'
        'integrations.TemplateIntegrationsService.'
        'create_integrations_for_template',
    )

    # act
    response = api_client.post(
        path='/templates',
        data={
            'description': 'Desc',
            'name': 'Name',
            'owners': [
                {
                    'type': OwnerType.USER,
                    'source_id': user.id,
                },
            ],
            'is_active': True,
            'is_public': True,
            'finalizable': True,
            'kickoff': {},
            'tasks': [
                {
                    'number': 1,
                    'name': 'First step',
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

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == messages.MSG_PT_0025
    assert token_mock.call_count == 3
    template_create_mock.assert_not_called()
    kickoff_create_mock.assert_not_called()


def test_create__embed_url_limit_is_reached__validation_error(
    mocker,
    api_client,
):
    # assert
    template_create_mock = mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_created',
    )
    kickoff_create_mock = mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_kickoff_created',
    )
    user = create_test_user()
    api_client.token_authenticate(user)
    token = 'a' * EmbedToken.token_length
    template = create_test_template(
        user=user,
        is_active=True,
        is_embedded=True,
    )
    template.embed_id = token
    template.save(update_fields=('embed_id',))
    token_mock = mocker.patch.object(
        EmbedToken,
        attribute='__str__',
        return_value=token,
    )

    # act
    response = api_client.post(
        path='/templates',
        data={
            'description': 'Desc',
            'name': 'Name',
            'owners': [
                {
                    'type': OwnerType.USER,
                    'source_id': user.id,
                },
            ],
            'is_active': True,
            'is_embedded': True,
            'finalizable': True,
            'kickoff': {},
            'tasks': [
                {
                    'number': 1,
                    'name': 'First step',
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

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == messages.MSG_PT_0026
    assert token_mock.call_count == 3
    template_create_mock.assert_not_called()
    kickoff_create_mock.assert_not_called()


def test_create__create_with_equal_api_names__ok(api_client, mocker):
    """ Test entities with equal api names
    do not update previous template and create the new one.
    """
    # arrange
    mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_created',
    )
    mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_kickoff_created',
    )
    account = create_test_account(plan=BillingPlanType.PREMIUM)
    user = create_test_user(account=account)
    user2 = create_test_user(
        account=account,
        email='test2@pneumatic.app',
    )
    conditions = [
        {
            'rules': [
                {
                    'predicates': [
                        {
                            'field': 'field-1',
                            'field_type': FieldType.RADIO,
                            'operator': PredicateOperator.EQUAL,
                            'value': 'selection-1',
                            'api_name': 'predicate-1',
                        },
                    ],
                    'api_name': 'rule-1',
                },
            ],
            'api_name': 'condition-1',
            'order': 1,
            'action': 'skip_task',
        },
    ]
    fields = [
        {
            'type': FieldType.RADIO,
            'name': 'Radio field',
            'order': 1,
            'api_name': 'field-1',
            'selections': [
                {
                    'value': 'First selection',
                    'api_name': 'selection-1',
                },
            ],
        },
    ]
    api_client.token_authenticate(user)
    request_data = {
        'description': 'Desc',
        'name': 'Name',
        'owners': [
            {
                'type': OwnerType.USER,
                'source_id': user.id,
            },
            {
                'type': OwnerType.USER,
                'source_id': user2.id,
            },
        ],
        'is_active': True,
        'is_public': False,
        'finalizable': True,
        'kickoff': {
            'fields': fields,
        },
        'tasks': [
            {
                'number': 1,
                'name': 'First step',
                'api_name': 'task-1',
                'fields': [],
                'raw_performers': [
                    {
                        'type': PerformerType.USER,
                        'source_id': user.id,
                    },
                ],
                'conditions': conditions,
            },
        ],
    }
    mocker.patch(
        'src.processes.services.templates.'
        'integrations.TemplateIntegrationsService.'
        'create_integrations_for_template',
    )

    # act
    api_client.post(
        path='/templates',
        data=request_data,
    )
    api_client.post(
        path='/templates',
        data=request_data,
    )

    # assert
    assert Template.objects.count() == 2
    assert TaskTemplate.objects.filter(api_name='task-1').count() == 2
    assert FieldTemplate.objects.filter(api_name='field-1').count() == 2
    assert FieldTemplateSelection.objects.filter(
        api_name='selection-1',
    ).count() == 2
    assert ConditionTemplate.objects.filter(
        api_name='condition-1',
    ).count() == 2
    assert RuleTemplate.objects.filter(api_name='rule-1').count() == 2
    assert PredicateTemplate.objects.filter(
        api_name='predicate-1',
    ).count() == 2


def test_create__template_owners_from_another_account__validation_error(
    mocker,
    api_client,
):

    # arrange
    template_create_mock = mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_created',
    )
    kickoff_create_mock = mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_kickoff_created',
    )
    user = create_test_user()
    api_client.token_authenticate(user)
    another_user = create_test_user(email='another@pneumatic.app')
    user.account.billing_plan = BillingPlanType.PREMIUM
    user.account.save()

    # act
    response = api_client.post(
        '/templates',
        data={
            'name': 'Template',
            'owners': [
                {
                    'type': OwnerType.USER,
                    'source_id': user.id,
                },
                {
                    'type': OwnerType.USER,
                    'source_id': another_user.id,
                },
            ],
            'is_active': True,
            'description': '',
            'kickoff': {},
            'tasks': [
                {
                    'name': 'First step',
                    'number': 1,
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

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == messages.MSG_PT_0019
    assert response.data['details']['reason'] == messages.MSG_PT_0019
    assert response.data['details']['name'] == 'owners'
    template_create_mock.assert_not_called()
    kickoff_create_mock.assert_not_called()


def test_create__template_owners_without_current_user__validation_error(
    mocker,
    api_client,
):

    # arrange
    template_create_mock = mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_created',
    )
    kickoff_create_mock = mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_kickoff_created',
    )
    account = create_test_account(plan=BillingPlanType.PREMIUM)
    user = create_test_user(is_account_owner=False, account=account)
    api_client.token_authenticate(user)
    invited_user = create_invited_user(user)

    # act
    response = api_client.post(
        '/templates',
        data={
            'name': 'Template',
            'owners': [
                {
                    'type': OwnerType.USER,
                    'source_id': invited_user.id,
                },
            ],
            'is_active': True,
            'description': '',
            'kickoff': {},
            'tasks': [
                {
                    'name': 'First step',
                    'number': 1,
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

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == messages.MSG_PT_0018
    assert response.data['details']['reason'] == messages.MSG_PT_0018
    assert response.data['details']['name'] == 'owners'
    template_create_mock.assert_not_called()
    kickoff_create_mock.assert_not_called()


def test_create__template_owners_user_source_id_none__validation_error(
    mocker,
    api_client,
):

    # arrange
    template_create_mock = mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_created',
    )
    kickoff_create_mock = mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_kickoff_created',
    )
    account = create_test_account(plan=BillingPlanType.PREMIUM)
    user = create_test_user(is_account_owner=False, account=account)
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        '/templates',
        data={
            'name': 'Template',
            'owners': [
                {
                    'type': OwnerType.USER,
                    'source_id': user.id,
                },
                {
                    'type': OwnerType.USER,
                    'source_id': None,
                },
            ],
            'is_active': True,
            'description': '',
            'kickoff': {},
            'tasks': [
                {
                    'name': 'First step',
                    'number': 1,
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

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == messages.MSG_PT_0057
    assert response.data['details']['reason'] == messages.MSG_PT_0057
    assert response.data['details']['name'] == 'owners'
    template_create_mock.assert_not_called()
    kickoff_create_mock.assert_not_called()


def test_create__template_owners_group_source_id_none__validation_error(
    mocker,
    api_client,
):

    # arrange
    template_create_mock = mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_created',
    )
    kickoff_create_mock = mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_kickoff_created',
    )
    account = create_test_account(plan=BillingPlanType.PREMIUM)
    user = create_test_user(is_account_owner=False, account=account)
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        '/templates',
        data={
            'name': 'Template',
            'owners': [
                {
                    'type': OwnerType.USER,
                    'source_id': user.id,
                },
                {
                    'type': OwnerType.GROUP,
                    'source_id': None,
                },
            ],
            'is_active': True,
            'description': '',
            'kickoff': {},
            'tasks': [
                {
                    'name': 'First step',
                    'number': 1,
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

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == messages.MSG_PT_0057
    assert response.data['details']['reason'] == messages.MSG_PT_0057
    assert response.data['details']['name'] == 'owners'
    template_create_mock.assert_not_called()
    kickoff_create_mock.assert_not_called()


def test_create__template_owners_pending_transfer__ok(
    mocker,
    api_client,
):

    # arrange
    template_create_mock = mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_created',
    )
    kickoff_create_mock = mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_kickoff_created',
    )
    user = create_test_user()
    invited_user = create_test_user(email='another@pneumatic.app')
    UserInvite.objects.create(
        email=invited_user.email,
        account=user.account,
        invited_by=user,
        invited_user=invited_user,
    )
    api_client.token_authenticate(user)
    mocker.patch(
        'src.processes.services.templates.'
        'integrations.TemplateIntegrationsService.'
        'create_integrations_for_template',
    )

    # act
    response = api_client.post(
        '/templates',
        data={
            'name': 'Template',
            'owners': [
                {
                    'type': OwnerType.USER,
                    'source_id': user.id,
                },
                {
                    'type': OwnerType.USER,
                    'source_id': invited_user.id,
                },
            ],
            'is_active': True,
            'description': '',
            'kickoff': {},
            'tasks': [
                {
                    'name': 'First step',
                    'number': 1,
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

    # assert
    assert response.status_code == 200
    template_create_mock.assert_called_once()
    kickoff_create_mock.assert_called_once()


def test_create__template_owners_inactive_user__validation_error(
    mocker,
    api_client,
):

    # arrange
    template_create_mock = mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_created',
    )
    kickoff_create_mock = mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_kickoff_created',
    )
    user = create_test_user()
    inactive_user = create_test_user(
        email='inactive@pneumatic.app',
        account=user.account,
    )
    UserService.deactivate(inactive_user)
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        path='/templates',
        data={
            'name': 'Template',
            'owners': [
                {
                    'type': OwnerType.USER,
                    'source_id': inactive_user.id,
                },
            ],
            'kickoff': {},
            'is_active': True,
            'tasks': [
                {
                    'number': 1,
                    'name': 'First step',
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

    # assert
    assert response.status_code == 400
    template_create_mock.assert_not_called()
    kickoff_create_mock.assert_not_called()


def test_create__change_template_owners__ok(
    mocker,
    api_client,
):

    # arrange
    template_create_mock = mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_created',
    )
    kickoff_create_mock = mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_kickoff_created',
    )
    account = create_test_account(plan=BillingPlanType.PREMIUM)
    user = create_test_user(account=account)
    create_test_user(account=account, email='t@t.t')
    api_client.token_authenticate(user)
    request_data = {
        'name': 'Template',
        'owners': [
            {
                'type': OwnerType.USER,
                'source_id': user.id,
            },
        ],
        'is_active': True,
        'kickoff': {},
        'tasks': [
            {
                'number': 1,
                'name': 'First step',
                'raw_performers': [
                    {
                        'type': PerformerType.USER,
                        'source_id': user.id,
                    },
                ],
            },
        ],
    }
    mocker.patch(
        'src.processes.services.templates.'
        'integrations.TemplateIntegrationsService.'
        'create_integrations_for_template',
    )

    # act
    response = api_client.post(
        path='/templates',
        data=request_data,
    )

    # assert
    assert response.status_code == 200
    response_data = response.json()
    assert response_data['owners'][0].get('api_name')
    assert response_data['owners'][0]['source_id'] == str(user.id)
    assert response_data['owners'][0]['type'] == OwnerType.USER
    template_create_mock.assert_called_once()
    kickoff_create_mock.assert_called_once()


def test_create_draft__skip_template_owners__set_default(
    mocker,
    api_client,
):

    # arrange
    template_create_mock = mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_created',
    )
    kickoff_create_mock = mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_kickoff_created',
    )
    account = create_test_account(plan=BillingPlanType.PREMIUM)
    user = create_test_user(account=account)
    api_client.token_authenticate(user)
    mocker.patch(
        'src.processes.services.templates.'
        'integrations.TemplateIntegrationsService.'
        'create_integrations_for_template',
    )

    # act
    response = api_client.post(
        path='/templates',
        data={
            'name': 'New Template',
            'public_success_url': None,
            'kickoff': {
                'fields': [],
            },
            'tasks': [],
        },
    )

    # assert
    assert response.status_code == 200
    assert len(response.data['owners']) == 1
    assert response.data['owners'][0].get('api_name')
    assert response.data['owners'][0]['source_id'] == str(user.id)
    assert response.data['owners'][0]['type'] == OwnerType.USER
    template_create_mock.assert_called_once()
    kickoff_create_mock.assert_called_once()


@pytest.mark.parametrize('plan', BillingPlanType.PAYMENT_PLANS)
def test_create__non_admin_in_template_owners_premium__ok(
    plan,
    mocker,
    api_client,
):
    # arrange
    template_create_mock = mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_created',
    )
    kickoff_create_mock = mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_kickoff_created',
    )
    account = create_test_account(plan=plan)
    owner = create_test_user(
        email='owner@test.test',
        is_account_owner=True,
        account=account,
    )
    non_admin = create_test_user(is_admin=False, account=account)
    mocker.patch(
        'src.processes.services.templates.'
        'integrations.TemplateIntegrationsService.'
        'create_integrations_for_template',
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.post(
        path='/templates',
        data={
            'name': 'Template',
            'owners': [
                {
                    'type': OwnerType.USER,
                    'source_id': owner.id,
                },
                {
                    'type': OwnerType.USER,
                    'source_id': non_admin.id,
                },
            ],
            'is_active': True,
            'kickoff': {},
            'tasks': [
                {
                    'number': 1,
                    'name': 'First step',
                    'raw_performers': [
                        {
                            'type': PerformerType.USER,
                            'source_id': non_admin.id,
                        },
                    ],
                },
            ],
        },
    )

    # assert
    assert response.status_code == 200
    response_data = response.json()

    assert response_data['owners'][0].get('api_name')
    assert response_data['owners'][0]['source_id'] == str(owner.id)
    assert response_data['owners'][0]['type'] == OwnerType.USER
    assert response_data['owners'][1].get('api_name')
    assert response_data['owners'][1]['source_id'] == str(non_admin.id)
    assert response_data['owners'][1]['type'] == OwnerType.USER
    template = Template.objects.get(id=response_data['id'])
    assert template.owners.count() == 2
    assert template.owners.filter(user_id=non_admin.id).exists()
    template_create_mock.assert_called_once()
    kickoff_create_mock.assert_called_once()


def test_create__non_admin_in_template_owners_freemium__ok(
    mocker,
    api_client,
):
    # arrange
    template_create_mock = mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_created',
    )
    kickoff_create_mock = mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_kickoff_created',
    )
    account = create_test_account(plan=BillingPlanType.FREEMIUM)
    owner = create_test_user(
        email='owner@test.test',
        is_account_owner=True,
        account=account,
    )
    non_admin = create_test_user(is_admin=False, account=account)
    mocker.patch(
        'src.processes.services.templates.'
        'integrations.TemplateIntegrationsService.'
        'create_integrations_for_template',
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.post(
        path='/templates',
        data={
            'name': 'Template',
            'owners': [
                {
                    'type': OwnerType.USER,
                    'source_id': non_admin.id,
                },
                {
                    'type': OwnerType.USER,
                    'source_id': owner.id,
                },
            ],
            'is_active': True,
            'kickoff': {},
            'tasks': [
                {
                    'number': 1,
                    'name': 'First step',
                    'raw_performers': [
                        {
                            'type': PerformerType.USER,
                            'source_id': non_admin.id,
                        },
                    ],
                },
            ],
        },
    )

    # assert
    assert response.status_code == 200
    response_data = response.json()

    assert response_data['owners'][0].get('api_name')
    assert response_data['owners'][0]['source_id'] == str(non_admin.id)
    assert response_data['owners'][0]['type'] == OwnerType.USER
    assert response_data['owners'][1].get('api_name')
    assert response_data['owners'][1]['source_id'] == str(owner.id)
    assert response_data['owners'][1]['type'] == OwnerType.USER
    template = Template.objects.get(id=response_data['id'])
    assert template.owners.count() == 2
    assert template.owners.filter(
        type=OwnerType.USER, user_id=non_admin.id,
    ).exists()
    template_create_mock.assert_called_once()
    kickoff_create_mock.assert_called_once()


def test_create__api_request__ok(
    mocker,
    api_client,
):

    # arrange
    account = create_test_account()
    user = create_test_user(account=account)
    create_integrations_mock = mocker.patch(
        'src.processes.services.templates.'
        'integrations.TemplateIntegrationsService.'
        'create_integrations_for_template',
    )
    template_create_mock = mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_created',
    )
    kickoff_create_mock = mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_kickoff_created',
    )
    user_agent = 'Mozilla'
    get_user_agent_mock = mocker.patch(
        'src.processes.views.template.get_user_agent',
        return_value=user_agent,
    )
    api_request_mock = mocker.patch(
        'src.processes.services.templates.'
        'integrations.TemplateIntegrationsService.api_request',
    )
    api_client.token_authenticate(
        user=user,
        token_type=AuthTokenType.API,
    )
    service_init_mock = mocker.patch.object(
        TemplateIntegrationsService,
        attribute='__init__',
        return_value=None,
    )

    # act
    response = api_client.post(
        path='/templates',
        data={
            'name': 'Template',
            'owners': [
                {
                    'type': OwnerType.USER,
                    'source_id': user.id,
                },
            ],
            'is_active': True,
            'kickoff': {},
            'tasks': [
                {
                    'number': 1,
                    'name': 'First step',
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

    # assert
    assert response.status_code == 200
    template = Template.objects.get(id=response.data['id'])
    create_integrations_mock.assert_called_with(
        template=template,
    )
    get_user_agent_mock.assert_called_once()
    assert service_init_mock.call_count == 2
    service_init_mock.has_calls([
        mocker.call(account=user.account, is_superuser=False, user=user),
        mocker.call(account=user.account, is_superuser=False, user=user),
    ])
    api_request_mock.assert_called_once_with(
        template=template,
        user_agent=user_agent,
    )
    template_create_mock.assert_called_once()
    kickoff_create_mock.assert_called_once()


def test_create__draft_invalid_template_owners_format__set_default(
    mocker,
    api_client,
):

    # arrange
    template_create_mock = mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_created',
    )
    kickoff_create_mock = mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_kickoff_created',
    )
    account = create_test_account()
    user = create_test_user(account=account)
    user_2 = create_test_user(account=account, email='t@t.t')
    api_client.token_authenticate(user)
    request_data = {
        'name': 'Template',
        'owners': [
            {
                'type': OwnerType.USER,
                'source_id': user.id,
            },
            {
                'type': OwnerType.USER,
                'source_id': {'user_id': user_2.id},
            },
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
                        'source_id': user.id,
                    },
                ],
            },
        ],
    }

    # act
    response = api_client.post(
        path='/templates',
        data=request_data,
    )

    # assert
    assert response.status_code == 200
    template = Template.objects.get(id=response.data['id'])
    assert template.owners.count() == 1
    assert template.owners.first().user_id == user.id
    template_create_mock.assert_called_once()
    kickoff_create_mock.assert_called_once()


def test_create__draft_another_acc_users_in_template_owners__set_default(
    mocker,
    api_client,
):

    # arrange
    template_create_mock = mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_created',
    )
    kickoff_create_mock = mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_kickoff_created',
    )
    user = create_test_user()
    another_user = create_test_user(email='another@t.t')
    api_client.token_authenticate(user)
    request_data = {
        'name': 'Template',
        'owners': [
            {
                'type': OwnerType.USER,
                'source_id': user.id,
            },
            {
                'type': OwnerType.USER,
                'source_id': another_user.id,
            },
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
                        'source_id': user.id,
                    },
                ],
            },
        ],
    }

    # act
    response = api_client.post(
        path='/templates',
        data=request_data,
    )

    # assert
    assert response.status_code == 200
    assert response.data['owners'][0]['source_id'] == str(user.id)
    assert response.data['owners'][0]['type'] == OwnerType.USER
    template = Template.objects.get(id=response.data['id'])
    assert template.owners.count() == 1
    assert template.owners.first().user_id == user.id
    template_create_mock.assert_called_once()
    kickoff_create_mock.assert_called_once()


def test_create__active_template__wf_name_template__sys_vars__ok(
    mocker,
    api_client,
):

    # arrange
    template_create_mock = mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_created',
    )
    kickoff_create_mock = mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_kickoff_created',
    )
    account = create_test_account()
    user = create_test_user(account=account)
    api_client.token_authenticate(user)
    wf_name_template = 'Workflow {{ date }} {{ template-name }}'
    request_data = {
        'name': 'Template',
        'wf_name_template': wf_name_template,
        'owners': [
            {
                'type': OwnerType.USER,
                'source_id': user.id,
            },
        ],
        'is_active': True,
        'kickoff': {},
        'tasks': [
            {
                'number': 1,
                'name': 'First step',
                'raw_performers': [
                    {
                        'type': PerformerType.USER,
                        'source_id': user.id,
                    },
                ],
            },
        ],
    }

    # act
    response = api_client.post(
        path='/templates',
        data=request_data,
    )

    # assert
    assert response.status_code == 200
    response_data = response.json()

    assert response_data['wf_name_template'] == wf_name_template
    template = Template.objects.get(id=response_data['id'])
    assert template.wf_name_template == wf_name_template
    template_create_mock.assert_called_once()
    kickoff_create_mock.assert_called_once()


def test_create__draft_template__wf_name_template__sys_vars__ok(
    mocker,
    api_client,
):

    # arrange
    template_create_mock = mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_created',
    )
    kickoff_create_mock = mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_kickoff_created',
    )
    account = create_test_account()
    user = create_test_user(account=account)
    api_client.token_authenticate(user)
    wf_name_template = 'Workflow {{ date }} {{ template-name }}'
    request_data = {
        'name': 'Template',
        'wf_name_template': wf_name_template,
        'owners': [
            {
                'type': OwnerType.USER,
                'source_id': user.id,
            },
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
                        'source_id': user.id,
                    },
                ],
            },
        ],
    }

    # act
    response = api_client.post(
        path='/templates',
        data=request_data,
    )

    # assert
    assert response.status_code == 200
    response_data = response.json()

    assert response_data['wf_name_template'] == wf_name_template
    template = Template.objects.get(id=response_data['id'])
    assert template.wf_name_template is None
    template_create_mock.assert_called_once()
    kickoff_create_mock.assert_called_once()


def test_create__wf_name_template__only_sys_vars__ok(
    mocker,
    api_client,
):

    # arrange
    template_create_mock = mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_created',
    )
    kickoff_create_mock = mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_kickoff_created',
    )
    account = create_test_account()
    user = create_test_user(account=account)
    api_client.token_authenticate(user)
    wf_name_template = '{{ date }}{{ template-name }}'
    request_data = {
        'name': 'Template',
        'wf_name_template': wf_name_template,
        'owners': [
            {
                'type': OwnerType.USER,
                'source_id': user.id,
            },
        ],
        'is_active': True,
        'kickoff': {},
        'tasks': [
            {
                'number': 1,
                'name': 'First step',
                'raw_performers': [
                    {
                        'type': PerformerType.USER,
                        'source_id': user.id,
                    },
                ],
            },
        ],
    }

    # act
    response = api_client.post(
        path='/templates',
        data=request_data,
    )

    # assert
    assert response.status_code == 200
    response_data = response.json()

    assert response_data['wf_name_template'] == wf_name_template
    template = Template.objects.get(id=response_data['id'])
    assert template.wf_name_template == wf_name_template
    template_create_mock.assert_called_once()
    kickoff_create_mock.assert_called_once()


@pytest.mark.parametrize(
    'field_type', (
        FieldType.STRING,
        FieldType.TEXT,
        FieldType.DATE,
        FieldType.URL,
        FieldType.FILE,
        FieldType.USER,
    ),
)
def test_create__wf_name_template__field__ok(
    mocker,
    api_client,
    field_type,
):

    # arrange
    template_create_mock = mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_created',
    )
    kickoff_create_mock = mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_kickoff_created',
    )

    account = create_test_account()
    user = create_test_user(account=account)
    api_client.token_authenticate(user)
    field_api_name = 'field-api-name'
    wf_name_template = '{{ field-api-name }}'
    request_data = {
        'name': 'Template',
        'wf_name_template': wf_name_template,
        'owners': [
            {
                'type': OwnerType.USER,
                'source_id': user.id,
            },
        ],
        'is_active': True,
        'kickoff': {
            'fields': [
                {
                    'type': field_type,
                    'name': 'Field name',
                    'is_required': True,
                    'order': 1,
                    'api_name': field_api_name,
                },
            ],
        },
        'tasks': [
            {
                'number': 1,
                'name': 'First step',
                'raw_performers': [
                    {
                        'type': PerformerType.USER,
                        'source_id': user.id,
                    },
                ],
            },
        ],
    }

    # act
    response = api_client.post(
        path='/templates',
        data=request_data,
    )

    # assert
    assert response.status_code == 200
    response_data = response.json()

    assert response_data['wf_name_template'] == wf_name_template
    template = Template.objects.get(id=response_data['id'])
    assert template.wf_name_template == wf_name_template
    template_create_mock.assert_called_once()
    kickoff_create_mock.assert_called_once()


@pytest.mark.parametrize(
    'field_type', (
        FieldType.DROPDOWN,
        FieldType.CHECKBOX,
        FieldType.RADIO,
    ),
)
def test_create__wf_name_template__field_with_selections__ok(
    mocker,
    api_client,
    field_type,
):

    # arrange
    template_create_mock = mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_created',
    )
    kickoff_create_mock = mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_kickoff_created',
    )
    account = create_test_account()
    user = create_test_user(account=account)
    api_client.token_authenticate(user)
    field_api_name = 'field-api-name'
    wf_name_template = '{{ field-api-name }}'
    request_data = {
        'name': 'Template',
        'wf_name_template': wf_name_template,
        'owners': [
            {
                'type': OwnerType.USER,
                'source_id': user.id,
            },
        ],
        'is_active': True,
        'kickoff': {
            'fields': [
                {
                    'type': field_type,
                    'name': 'Field name',
                    'is_required': True,
                    'order': 1,
                    'api_name': field_api_name,
                    'selections': [
                        {
                            'value': 'First selection',
                            'api_name': 'selection-1',
                        },
                    ],
                },
            ],
        },
        'tasks': [
            {
                'number': 1,
                'name': 'First step',
                'raw_performers': [
                    {
                        'type': PerformerType.USER,
                        'source_id': user.id,
                    },
                ],
            },
        ],
    }

    # act
    response = api_client.post(
        path='/templates',
        data=request_data,
    )

    # assert
    assert response.status_code == 200
    response_data = response.json()

    assert response_data['wf_name_template'] == wf_name_template
    template = Template.objects.get(id=response_data['id'])
    assert template.wf_name_template == wf_name_template
    template_create_mock.assert_called_once()
    kickoff_create_mock.assert_called_once()


def test_create__wf_name_template__only_fields__not_required__validation_error(
    mocker,
    api_client,
):

    # arrange
    template_create_mock = mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_created',
    )
    kickoff_create_mock = mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_kickoff_created',
    )
    account = create_test_account()
    user = create_test_user(account=account)
    api_client.token_authenticate(user)
    field_api_name_1 = 'field-api-name-1'
    field_api_name_2 = 'field-api-name-2'
    wf_name_template = ' {{%s}} {{%s}} ' % (field_api_name_1, field_api_name_2)
    request_data = {
        'name': 'Template',
        'wf_name_template': wf_name_template,
        'owners': [
            {
                'type': OwnerType.USER,
                'source_id': user.id,
            },
        ],
        'is_active': True,
        'kickoff': {
            'fields': [
                {
                    'type': FieldType.STRING,
                    'name': 'Field name 1',
                    'is_required': False,
                    'order': 1,
                    'api_name': field_api_name_1,
                },
                {
                    'type': FieldType.CHECKBOX,
                    'name': 'Field name 2',
                    'is_required': False,
                    'order': 1,
                    'api_name': field_api_name_2,
                    'selections': [
                        {
                            'api_name': 'sl-2',
                            'value': 'value 2',
                        },
                    ],
                },
            ],
        },
        'tasks': [
            {
                'number': 1,
                'name': 'First step',
                'raw_performers': [
                    {
                        'type': PerformerType.USER,
                        'source_id': user.id,
                    },
                ],
            },
        ],
    }

    # act
    response = api_client.post(
        path='/templates',
        data=request_data,
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == messages.MSG_PT_0009
    assert response.data['details']['name'] == 'wf_name_template'
    assert response.data['details']['reason'] == messages.MSG_PT_0009
    template_create_mock.assert_not_called()
    kickoff_create_mock.assert_not_called()


def test_create__wf_name_template__not_existent_field__validation_error(
    mocker,
    api_client,
):

    # arrange
    template_create_mock = mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_created',
    )
    kickoff_create_mock = mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_kickoff_created',
    )
    account = create_test_account()
    user = create_test_user(account=account)
    api_client.token_authenticate(user)
    wf_name_template = 'Workflow {{field-api-name}} {{field-api-name-2}}'
    request_data = {
        'name': 'Template',
        'wf_name_template': wf_name_template,
        'owners': [
            {
                'type': OwnerType.USER,
                'source_id': user.id,
            },
        ],
        'is_active': True,
        'kickoff': {
            'fields': [
                {
                    'type': FieldType.STRING,
                    'name': 'Field name 1',
                    'is_required': True,
                    'order': 1,
                    'api_name': 'some-api-name',
                },
            ],
        },
        'tasks': [
            {
                'number': 1,
                'name': 'First step',
                'raw_performers': [
                    {
                        'type': PerformerType.USER,
                        'source_id': user.id,
                    },
                ],
            },
        ],
    }

    # act
    response = api_client.post(
        path='/templates',
        data=request_data,
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == messages.MSG_PT_0008
    assert response.data['details']['name'] == 'wf_name_template'
    assert response.data['details']['reason'] == messages.MSG_PT_0008
    template_create_mock.assert_not_called()
    kickoff_create_mock.assert_not_called()


@pytest.mark.parametrize('wf_name_template', ('', None))
def test_create__wf_name_template__blank_value__ok(
    mocker,
    api_client,
    wf_name_template,
):

    # arrange
    template_create_mock = mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_created',
    )
    kickoff_create_mock = mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_kickoff_created',
    )
    account = create_test_account()
    user = create_test_user(account=account)
    api_client.token_authenticate(user)
    request_data = {
        'name': 'Template',
        'wf_name_template': wf_name_template,
        'owners': [
            {
                'type': OwnerType.USER,
                'source_id': user.id,
            },
        ],
        'is_active': True,
        'kickoff': {},
        'tasks': [
            {
                'number': 1,
                'name': 'First step',
                'raw_performers': [
                    {
                        'type': PerformerType.USER,
                        'source_id': user.id,
                    },
                ],
            },
        ],
    }

    # act
    response = api_client.post(
        path='/templates',
        data=request_data,
    )

    # assert
    assert response.status_code == 200
    assert response.data['wf_name_template'] == wf_name_template
    template = Template.objects.get(id=response.data['id'])
    assert template.wf_name_template == wf_name_template
    template_create_mock.assert_called_once()
    kickoff_create_mock.assert_called_once()


def test_create__raw_performers_group__ok(
    mocker,
    api_client,
):

    # arrange
    account = create_test_account()
    user = create_test_user(account=account)
    group = create_test_group(account, users=[user])
    api_client.token_authenticate(user)
    mocker.patch(
        'src.processes.services.templates.'
        'integrations.TemplateIntegrationsService.'
        'create_integrations_for_template',
    )
    mocker.patch(
        'src.processes.services.templates.'
        'integrations.TemplateIntegrationsService.api_request',
    )
    mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_created',
    )
    mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_kickoff_created',
    )
    request_data = {
        'name': 'Template',
        'owners': [
            {
                'type': OwnerType.USER,
                'source_id': user.id,
            },
        ],
        'is_active': True,
        'kickoff': {},
        'tasks': [
            {
                'number': 1,
                'name': 'First step',
                'raw_performers': [
                    {
                        'type': PerformerType.GROUP,
                        'source_id': group.id,
                    },
                ],
            },
        ],
    }

    # act
    response = api_client.post(
        path='/templates',
        data=request_data,
    )

    # assert
    assert response.status_code == 200
    task = response.json()['tasks'][0]
    raw_performers_data = task['raw_performers'][0]
    assert raw_performers_data['type'] == PerformerType.GROUP
    assert raw_performers_data['source_id'] == str(group.id)
    assert RawPerformerTemplate.objects.get(
        account=account,
        task=task['id'],
        type=PerformerType.GROUP,
        group=group,
    )
