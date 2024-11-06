import pytest
from django.conf import settings
from pneumatic_backend.accounts.enums import BillingPlanType
from pneumatic_backend.processes.tests.fixtures import (
    create_test_user,
    create_test_template,
    create_test_account,
    create_invited_user,
)
from pneumatic_backend.accounts.services import AccountService
from pneumatic_backend.processes.models import (
    Template,
    FieldTemplate,
    PredicateTemplate,
    TaskTemplate,
    ConditionTemplate,
    RuleTemplate,
    FieldTemplateSelection,
)
from pneumatic_backend.utils.validation import ErrorCode
from pneumatic_backend.processes.messages import template as messages
from pneumatic_backend.accounts.models import (
    UserInvite
)
from pneumatic_backend.processes.enums import (
    PerformerType,
    PredicateOperator,
    FieldType
)
from pneumatic_backend.authentication.tokens import (
    PublicToken,
    EmbedToken,
)
from pneumatic_backend.accounts.services.user import UserService
from pneumatic_backend.authentication.enums import AuthTokenType
from pneumatic_backend.processes.api_v2.services.templates\
    .integrations import TemplateIntegrationsService

pytestmark = pytest.mark.django_db


def test_create__only_required_fields__defaults_ok(
    mocker,
    api_client
):

    # arrange
    account = create_test_account()
    user = create_test_user(account=account)
    api_client.token_authenticate(user)
    create_integrations_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'integrations.TemplateIntegrationsService.'
        'create_integrations_for_template'
    )
    api_request_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'integrations.TemplateIntegrationsService.api_request',
    )
    template_create_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.views.template.'
        'AnalyticService.templates_created'
    )
    kickoff_create_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.views.template.'
        'AnalyticService.templates_kickoff_created'
    )
    request_data = {
        'name': 'Template',
        'template_owners': [user.id],
        'is_active': True,
        'kickoff': {},
        'tasks': [
            {
                'number': 1,
                'name': 'First step',
                'raw_performers': [
                    {
                        'type': PerformerType.USER,
                        'source_id': user.id
                    }
                ]
            }
        ]
    }

    # act
    response = api_client.post(
        path='/templates',
        data=request_data
    )

    # assert
    assert response.status_code == 200
    response_data = response.json()

    assert response_data['template_owners'] == (
        request_data['template_owners']
    )
    assert response_data['name'] == request_data['name']
    assert response_data['description'] == ''
    assert response_data['is_active'] is True
    assert response_data['is_public'] is False
    assert response_data['public_url'] is not None
    assert response_data['finalizable'] is False
    assert response_data['tasks_count'] == 1
    assert response_data['performers_count'] == 1
    assert response_data['wf_name_template'] is None
    template = Template.objects.get(id=response_data['id'])
    assert template.tasks.first().account_id == user.account_id
    assert template.template_owners.count() == 1
    assert template.name == request_data['name']
    assert template.description == ''
    assert template.is_active == request_data['is_active']
    assert template.finalizable is False
    assert template.wf_name_template is None
    account.refresh_from_db()
    assert user.account.active_templates == 1
    create_integrations_mock.assert_called_with(
        template=template
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
        email='test2@pneumatic.app'
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
                        }
                    ],
                    'api_name': 'rule-1',
                }
            ],
            'api_name': 'condition-1',
            'order': 1,
            'action': 'skip_task',
        }
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
                }
            ]
        }
    ]
    api_client.token_authenticate(user)
    mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'integrations.TemplateIntegrationsService.'
        'create_integrations_for_template'
    )
    template_create_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.views.template.'
        'AnalyticService.templates_created'
    )
    kickoff_create_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.views.template.'
        'AnalyticService.templates_kickoff_created'
    )
    request_data = {
        'description': 'Desc',
        'name': 'Name',
        'template_owners': [user.id, user2.id],
        'is_active': True,
        'is_public': False,
        'finalizable': True,
        'kickoff': {
            'fields': kickoff_fields,
            'description': ""
        },
        'tasks': [
            {
                'number': 1,
                'name': 'First step',
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
                        'order': 1,
                        'api_name': 'field-2',
                        'selections': [
                            {
                                'value': 'First selection',
                                'api_name': 'selection-2',
                            }
                        ]
                    }
                ],
                'conditions': conditions
            },
            {
                'number': 2,
                'name': 'Second step',
                'api_name': 'task-1',
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
                        'order': 1,
                        'api_name': 'field-3',
                        'selections': [
                            {
                                'value': 'First selection',
                                'api_name': 'selection-3',
                            }
                        ]
                    }
                ],
                'raw_due_date': {
                    'api_name': 'raw-due-date-bwybf0',
                    'rule': 'after task started',
                    'duration_months': 0,
                    'duration': '0 00:05:00',
                    'source_id': 'task-1'
                },
            },
            {
                'number': 3,
                'name': 'Third step',
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
                        'order': 1,
                        'api_name': 'field-4',
                        'selections': [
                            {
                                'value': 'First selection',
                                'api_name': 'selection-4',
                            }
                        ]
                    }
                ],
                'delay': '1 12:00:00',
            }
        ]
    }

    # act
    response = api_client.post(
        path='/templates',
        data=request_data
    )

    # assert
    assert response.status_code == 200
    response_data = response.json()

    assert response_data.get('id')
    assert response_data.get('kickoff')
    assert len(response_data['template_owners']) == len(
        request_data['template_owners']
    )
    assert response_data['name'] == request_data['name']
    assert response_data['description'] == request_data['description']
    assert response_data['is_active'] == request_data['is_active']
    assert response_data['is_public'] == request_data['is_public']
    assert response_data['public_url'] is not None
    assert response_data['embed_url'] is not None
    assert response_data['finalizable'] == request_data['finalizable']
    assert response_data['tasks_count'] == 3
    assert response_data['performers_count'] == 1
    assert response_data['updated_by'] == user.id
    assert response_data.get('date_updated')

    template = Template.objects.get(id=response_data['id'])
    template_owners_ids = list(template.template_owners.order_by(
        'id'
    ).values_list('id', flat=True))
    assert template_owners_ids == request_data['template_owners']
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
    assert account.active_templates == 1

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


def test_create__draft__ok(
    mocker,
    api_client,
):
    # arrange
    template_create_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.views.template.'
        'AnalyticService.templates_created'
    )
    kickoff_create_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.views.template.'
        'AnalyticService.templates_kickoff_created'
    )
    user = create_test_user()
    user_2 = create_test_user(
        is_account_owner=False,
        email='test@test.test',
        account=user.account
    )
    api_client.token_authenticate(user)
    create_integrations_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'integrations.TemplateIntegrationsService.'
        'create_integrations_for_template'
    )
    request_data = {
        'template_owners': [user.id, user_2.id],
        'is_active': False,
        'kickoff': {
            'fields': [],
            'description': ""
        },
        'tasks': []
    }

    # act
    response = api_client.post(
        path='/templates',
        data=request_data
    )

    # assert
    assert response.status_code == 200
    response_data = response.json()

    assert response_data.get('id')
    assert response_data['template_owners'] == [user.id, user_2.id]
    assert response_data['name'] == ''
    assert not response_data.get('description')
    assert response_data['is_active'] is False
    assert response_data['is_public'] is False
    assert response_data['is_embedded'] is False
    assert response_data['public_url'] is not None
    assert response_data['embed_url'] is not None
    assert response_data['updated_by'] == user.id
    assert response_data.get('date_updated')
    assert response_data['tasks_count'] == 0
    assert response_data['performers_count'] == 0
    assert response_data['tasks'] == request_data['tasks']

    template = Template.objects.get(id=response_data['id'])
    assert template.template_owners.count() == 1
    assert template.template_owners.first().id == user.id
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
    assert template_draft.draft['template_owners'] == [user.id, user_2.id]
    assert template_draft.draft['is_public'] is False
    assert template_draft.draft['is_embedded'] is False
    assert template_draft.draft['public_url'] is not None
    assert template_draft.draft['embed_url'] is not None
    assert user.account.active_templates == 0

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
        template=template
    )


def test_create__public__ok(mocker, api_client):

    # arrange
    template_create_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.views.template.'
        'AnalyticService.templates_created'
    )
    kickoff_create_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.views.template.'
        'AnalyticService.templates_kickoff_created'
    )
    user = create_test_user()
    api_client.token_authenticate(user)
    token = 'a' * PublicToken.token_length
    public_url = f'{settings.PUBLIC_FORMS_ORIGIN}/{token}'
    token_mock = mocker.patch.object(
        PublicToken,
        attribute='__str__',
        return_value=token
    )
    mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'integrations.TemplateIntegrationsService.'
        'create_integrations_for_template'
    )

    # act
    response = api_client.post(
        path='/templates',
        data={
            'name': 'Template',
            'template_owners': [user.id],
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
                            'source_id': user.id
                        }
                    ]
                }
            ]
        }
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
    embed_url = f'{settings.PUBLIC_FORMS_ORIGIN}/embed/{token}'
    token_mock = mocker.patch.object(
        EmbedToken,
        attribute='__str__',
        return_value=token
    )
    mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'integrations.TemplateIntegrationsService.'
        'create_integrations_for_template'
    )

    # act
    response = api_client.post(
        path='/templates',
        data={
            'name': 'Template',
            'template_owners': [user.id],
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
                            'source_id': user.id
                        }
                    ]
                }
            ]
        }
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
    ]
)
def test_create__public_success_url__ok(value, api_client, mocker):

    # arrange
    account = create_test_account(plan=BillingPlanType.PREMIUM)
    user = create_test_user(account=account)
    api_client.token_authenticate(user)
    mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'integrations.TemplateIntegrationsService.'
        'create_integrations_for_template'
    )
    template_create_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.views.template.'
        'AnalyticService.templates_created'
    )
    kickoff_create_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.views.template.'
        'AnalyticService.templates_kickoff_created'
    )

    # act
    response = api_client.post(
        path='/templates',
        data={
            'name': 'Template',
            'template_owners': [user.id],
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
                            'source_id': user.id
                        }
                    ]
                }
            ]
        }
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
        '://my.pneumatic.app'
    ]
)
def test_create__public_success_url_invalid__validation_error(
    value,
    mocker,
    api_client
):

    # arrange
    template_create_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.views.template.'
        'AnalyticService.templates_created'
    )
    kickoff_create_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.views.template.'
        'AnalyticService.templates_kickoff_created'
    )
    account = create_test_account(plan=BillingPlanType.PREMIUM)
    user = create_test_user(account=account)
    api_client.token_authenticate(user)
    request_data = {
        'name': 'Template',
        'template_owners': [user.id],
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
                        'source_id': user.id
                    }
                ]
            }
        ]
    }

    # act
    response = api_client.post(
        path='/templates',
        data=request_data
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == messages.MSG_PT_0021
    assert response.data['details']['name'] == 'public_success_url'
    template_create_mock.assert_not_called()
    kickoff_create_mock.assert_not_called()


def test_create__public_success_url__paid_feature__validation_error(
    mocker,
    api_client
):

    # arrange
    template_create_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.views.template.'
        'AnalyticService.templates_created'
    )
    kickoff_create_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.views.template.'
        'AnalyticService.templates_kickoff_created'
    )
    user = create_test_user()
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        path='/templates',
        data={
            'name': 'Template',
            'template_owners': [user.id],
            'is_active': True,
            'is_public': True,
            'public_success_url': 'my.pneumatic.app',
            'kickoff': {},
            'tasks': [
                {
                    'number': 1,
                    'name': 'First step',
                    'raw_performers': [
                        {
                            'type': PerformerType.USER,
                            'source_id': user.id
                        }
                    ]
                }
            ]
        }
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == messages.MSG_PT_0020
    assert response.data['details']['name'] == 'public_success_url'
    template_create_mock.assert_not_called()
    kickoff_create_mock.assert_not_called()


def test_create__name_is_required__validation_error(
    mocker,
    api_client
):

    # arrange
    template_create_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.views.template.'
        'AnalyticService.templates_created'
    )
    kickoff_create_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.views.template.'
        'AnalyticService.templates_kickoff_created'
    )
    user = create_test_user()
    api_client.token_authenticate(user)
    request_data = {
        'name': None,
        'template_owners': [user.id],
        'is_active': True,
        'kickoff': {},
        'tasks': [
            {
                'number': 1,
                'name': 'First step',
                'raw_performers': [
                    {
                        'type': PerformerType.USER,
                        'source_id': user.id
                    }
                ]
            }
        ]
    }

    # act
    response = api_client.post(
        path='/templates',
        data=request_data
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
        'pneumatic_backend.processes.api_v2.views.template.'
        'AnalyticService.templates_created'
    )
    kickoff_create_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.views.template.'
        'AnalyticService.templates_kickoff_created'
    )
    user = create_test_user()
    api_client.token_authenticate(user)
    mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'integrations.TemplateIntegrationsService.'
        'create_integrations_for_template'
    )
    request_data = {
        'template_owners': [user.id],
        'is_active': False,
        'is_public': True,
        'kickoff': {},
        'tasks': []
    }

    # act
    response = api_client.post(
        path='/templates',
        data=request_data
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
        'pneumatic_backend.processes.api_v2.views.template.'
        'AnalyticService.templates_created'
    )
    kickoff_create_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.views.template.'
        'AnalyticService.templates_kickoff_created'
    )

    user = create_test_user()
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        path='/templates',
        data={
            'name': None,
            'template_owners': [user.id],
            'is_active': True,
            'kickoff': {},
            'tasks': [
                {
                    'number': 1,
                    'name': 'First step',
                    'api_name': 'task-55',
                    'performers': None
                }
            ]
        }
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


def test_create__validate_limit_active_templates__validation_error(
    mocker,
    api_client
):

    # arrange
    template_create_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.views.template.'
        'AnalyticService.templates_created'
    )
    kickoff_create_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.views.template.'
        'AnalyticService.templates_kickoff_created'
    )
    user = create_test_user()
    api_client.token_authenticate(user)
    for _ in range(settings.PAYWALL_MAX_ACTIVE_TEMPLATES):
        create_test_template(
            user=user,
            is_active=True,
            tasks_count=1
        )
    account_service = AccountService(
        instance=user.account,
        user=user
    )
    account_service.update_active_templates()

    request_data = {
        'name': 'Template',
        'template_owners': [user.id],
        'is_active': True,
        'kickoff': {},
        'tasks': [
            {
                'number': 1,
                'name': 'First step',
                'raw_performers': [
                    {
                        'type': PerformerType.USER,
                        'source_id': user.id
                    }
                ]
            }
        ]
    }

    # act
    response = api_client.post(
        path='/templates',
        data=request_data
    )

    # assert
    assert response.status_code == 400
    template_create_mock.assert_not_called()
    kickoff_create_mock.assert_not_called()


def test_create__unlimited_drafts_for_account__ok(
    mocker,
    api_client
):

    # arrange
    template_create_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.views.template.'
        'AnalyticService.templates_created'
    )
    kickoff_create_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.views.template.'
        'AnalyticService.templates_kickoff_created'
    )
    user = create_test_user()
    api_client.token_authenticate(user)
    for _ in range(settings.PAYWALL_MAX_ACTIVE_TEMPLATES):
        create_test_template(
            user=user,
            is_active=True,
            tasks_count=1
        )
    account_service = AccountService(
        instance=user.account,
        user=user
    )
    account_service.update_active_templates()
    mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'integrations.TemplateIntegrationsService.'
        'create_integrations_for_template'
    )
    request_data = {
        'name': 'Template',
        'template_owners': [user.id],
        'is_active': False,
        'kickoff': {},
        'tasks': [
            {
                'number': 1,
                'name': 'First step',
                'raw_performers': [
                    {
                        'type': PerformerType.USER,
                        'source_id': user.id
                    }
                ]
            }
        ]
    }

    # act
    response = api_client.post(
        path='/templates',
        data=request_data
    )

    # assert
    assert response.status_code == 200
    template_create_mock.assert_called_once()
    kickoff_create_mock.assert_called_once()


def test_create__user_field_in_public_task__ok(
    mocker,
    api_client
):

    # arrange
    template_create_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.views.template.'
        'AnalyticService.templates_created'
    )
    kickoff_create_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.views.template.'
        'AnalyticService.templates_kickoff_created'
    )
    user = create_test_user()
    api_client.token_authenticate(user)
    mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'integrations.TemplateIntegrationsService.'
        'create_integrations_for_template'
    )
    request_data = {
        'description': 'Desc',
        'name': 'Name',
        'template_owners': [user.id],
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
                        'source_id': user.id
                    }
                ],
                'fields': [
                    {
                        'type': FieldType.USER,
                        'name': 'User field',
                        'description': 'desc',
                        'order': 1,
                        'is_required': True,
                        'api_name': 'user-field-1',
                    }
                ]
            },
        ]
    }

    # act
    response = api_client.post(
        path='/templates',
        data=request_data
    )

    # assert
    assert response.status_code == 200
    template_create_mock.assert_called_once()
    kickoff_create_mock.assert_called_once()


def test_create__public_url__ok(mocker):
    mocker.patch(
        'pneumatic_backend.processes.api_v2.views.template.'
        'AnalyticService.templates_created'
    )
    mocker.patch(
        'pneumatic_backend.processes.api_v2.views.template.'
        'AnalyticService.templates_kickoff_created'
    )
    user = create_test_user()
    template = create_test_template(
        user=user,
        is_active=True,
        is_public=True,
        tasks_count=1
    )
    host = settings.PUBLIC_FORMS_ORIGIN
    assert len(template.public_id) == 8
    assert template.public_url == f'{host}/{template.public_id}'


def test_create__public_url_limit_is_reached__validation_error(
    mocker,
    api_client
):
    # assert
    template_create_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.views.template.'
        'AnalyticService.templates_created'
    )
    kickoff_create_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.views.template.'
        'AnalyticService.templates_kickoff_created'
    )
    user = create_test_user()
    api_client.token_authenticate(user)
    token = 'a' * PublicToken.token_length
    template = create_test_template(
        user=user,
        is_active=True,
        is_public=True
    )
    template.public_id = token
    template.save(update_fields=('public_id',))
    token_mock = mocker.patch.object(
        PublicToken,
        attribute='__str__',
        return_value=token
    )
    mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'integrations.TemplateIntegrationsService.'
        'create_integrations_for_template'
    )

    # act
    response = api_client.post(
        path='/templates',
        data={
            'description': 'Desc',
            'name': 'Name',
            'template_owners': [user.id],
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
                            'source_id': user.id
                        }
                    ]
                }
            ]
        }
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
    api_client
):
    # assert
    template_create_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.views.template.'
        'AnalyticService.templates_created'
    )
    kickoff_create_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.views.template.'
        'AnalyticService.templates_kickoff_created'
    )
    user = create_test_user()
    api_client.token_authenticate(user)
    token = 'a' * EmbedToken.token_length
    template = create_test_template(
        user=user,
        is_active=True,
        is_embedded=True
    )
    template.embed_id = token
    template.save(update_fields=('embed_id',))
    token_mock = mocker.patch.object(
        EmbedToken,
        attribute='__str__',
        return_value=token
    )

    # act
    response = api_client.post(
        path='/templates',
        data={
            'description': 'Desc',
            'name': 'Name',
            'template_owners': [user.id],
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
                            'source_id': user.id
                        }
                    ]
                }
            ]
        }
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
        'pneumatic_backend.processes.api_v2.views.template.'
        'AnalyticService.templates_created'
    )
    mocker.patch(
        'pneumatic_backend.processes.api_v2.views.template.'
        'AnalyticService.templates_kickoff_created'
    )
    account = create_test_account(plan=BillingPlanType.PREMIUM)
    user = create_test_user(account=account)
    user2 = create_test_user(
        account=account,
        email='test2@pneumatic.app'
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
                        }
                    ],
                    'api_name': 'rule-1',
                }
            ],
            'api_name': 'condition-1',
            'order': 1,
            'action': 'skip_task',
        }
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
                }
            ]
        }
    ]
    api_client.token_authenticate(user)
    request_data = {
        'description': 'Desc',
        'name': 'Name',
        'template_owners': [user.id, user2.id],
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
                        'source_id': user.id
                    }
                ],
                'conditions': conditions,
            }
        ]
    }
    mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'integrations.TemplateIntegrationsService.'
        'create_integrations_for_template'
    )

    # act
    api_client.post(
        path='/templates',
        data=request_data
    )
    api_client.post(
        path='/templates',
        data=request_data
    )

    # assert
    assert Template.objects.count() == 2
    assert TaskTemplate.objects.filter(api_name='task-1').count() == 2
    assert FieldTemplate.objects.filter(api_name='field-1').count() == 2
    assert FieldTemplateSelection.objects.filter(
        api_name='selection-1'
    ).count() == 2
    assert ConditionTemplate.objects.filter(
        api_name='condition-1'
    ).count() == 2
    assert RuleTemplate.objects.filter(api_name='rule-1').count() == 2
    assert PredicateTemplate.objects.filter(
        api_name='predicate-1'
    ).count() == 2


def test_create__template_owners_from_another_account__validation_error(
    mocker,
    api_client
):

    # arrange
    template_create_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.views.template.'
        'AnalyticService.templates_created'
    )
    kickoff_create_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.views.template.'
        'AnalyticService.templates_kickoff_created'
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
            'template_owners': [user.id, another_user.id],
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
                            'source_id': user.id
                        }
                    ]
                }
            ]
        }
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == messages.MSG_PT_0019
    assert response.data['details']['reason'] == messages.MSG_PT_0019
    assert response.data['details']['name'] == 'template_owners'
    template_create_mock.assert_not_called()
    kickoff_create_mock.assert_not_called()


def test_create__template_owners_without_current_user__validation_error(
    mocker,
    api_client
):

    # arrange
    template_create_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.views.template.'
        'AnalyticService.templates_created'
    )
    kickoff_create_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.views.template.'
        'AnalyticService.templates_kickoff_created'
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
            'template_owners': [invited_user.id],
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
                            'source_id': user.id
                        }
                    ]
                }
            ]
        }
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == messages.MSG_PT_0018
    assert response.data['details']['reason'] == messages.MSG_PT_0018
    assert response.data['details']['name'] == 'template_owners'
    template_create_mock.assert_not_called()
    kickoff_create_mock.assert_not_called()


def test_create__template_owners_not_all_user_unsub_acc__validation_error(
    mocker,
    api_client
):

    # arrange
    template_create_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.views.template.'
        'AnalyticService.templates_created'
    )
    kickoff_create_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.views.template.'
        'AnalyticService.templates_kickoff_created'
    )
    user = create_test_user()
    create_test_user(
        is_admin=False,
        email='not_admin@test.test'
    )
    api_client.token_authenticate(user)
    create_invited_user(user)

    # act
    response = api_client.post(
        '/templates',
        data={
            'name': 'Template',
            'template_owners': [user.id],
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
                            'source_id': user.id
                        }
                    ]
                }
            ]
        }
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == messages.MSG_PT_0017
    assert response.data['details']['reason'] == messages.MSG_PT_0017
    assert response.data['details']['name'] == 'template_owners'
    template_create_mock.assert_not_called()
    kickoff_create_mock.assert_not_called()


def test_create__template_owners_pending_transfer__ok(
    mocker,
    api_client
):

    # arrange
    template_create_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.views.template.'
        'AnalyticService.templates_created'
    )
    kickoff_create_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.views.template.'
        'AnalyticService.templates_kickoff_created'
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
        'pneumatic_backend.processes.api_v2.services.templates.'
        'integrations.TemplateIntegrationsService.'
        'create_integrations_for_template'
    )

    # act
    response = api_client.post(
        '/templates',
        data={
            'name': 'Template',
            'template_owners': [user.id, invited_user.id],
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
                            'source_id': user.id
                        }
                    ]
                }
            ]
        }
    )

    # assert
    assert response.status_code == 200
    template_create_mock.assert_called_once()
    kickoff_create_mock.assert_called_once()


def test_create__template_owners_inactive_user__validation_error(
    mocker,
    api_client
):

    # arrange
    template_create_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.views.template.'
        'AnalyticService.templates_created'
    )
    kickoff_create_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.views.template.'
        'AnalyticService.templates_kickoff_created'
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
            'template_owners': [inactive_user.id],
            'kickoff': {},
            'is_active': True,
            'tasks': [
                {
                    'number': 1,
                    'name': 'First step',
                    'raw_performers': [
                        {
                            'type': PerformerType.USER,
                            'source_id': user.id
                        }
                    ]
                }
            ]
        }
    )

    # assert
    assert response.status_code == 400
    template_create_mock.assert_not_called()
    kickoff_create_mock.assert_not_called()


def test_create__change_template_owners__ok(
    mocker,
    api_client
):

    # arrange
    template_create_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.views.template.'
        'AnalyticService.templates_created'
    )
    kickoff_create_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.views.template.'
        'AnalyticService.templates_kickoff_created'
    )
    account = create_test_account(plan=BillingPlanType.PREMIUM)
    user = create_test_user(account=account)
    create_test_user(account=account, email='t@t.t')
    api_client.token_authenticate(user)
    request_data = {
        'name': 'Template',
        'template_owners': [user.id],
        'is_active': True,
        'kickoff': {},
        'tasks': [
            {
                'number': 1,
                'name': 'First step',
                'raw_performers': [
                    {
                        'type': PerformerType.USER,
                        'source_id': user.id
                    }
                ]
            }
        ]
    }
    mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'integrations.TemplateIntegrationsService.'
        'create_integrations_for_template'
    )

    # act
    response = api_client.post(
        path='/templates',
        data=request_data
    )

    # assert
    assert response.status_code == 200
    response_data = response.json()

    assert response_data['template_owners'] == (
        request_data['template_owners']
    )
    template_create_mock.assert_called_once()
    kickoff_create_mock.assert_called_once()


def test_create_draft__skip_template_owners__set_default(
    mocker,
    api_client
):

    # arrange
    template_create_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.views.template.'
        'AnalyticService.templates_created'
    )
    kickoff_create_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.views.template.'
        'AnalyticService.templates_kickoff_created'
    )
    account = create_test_account(plan=BillingPlanType.PREMIUM)
    user = create_test_user(account=account)
    api_client.token_authenticate(user)
    mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'integrations.TemplateIntegrationsService.'
        'create_integrations_for_template'
    )

    # act
    response = api_client.post(
        path='/templates',
        data={
            'name': 'New Template',
            'public_success_url': None,
            'kickoff': {
                'description': '',
                'fields': [],
            },
            'tasks': []
        }
    )

    # assert
    assert response.status_code == 200
    assert len(response.data['template_owners']) == 1
    assert response.data['template_owners'][0] == user.id
    template_create_mock.assert_called_once()
    kickoff_create_mock.assert_called_once()


@pytest.mark.parametrize('plan', BillingPlanType.PAYMENT_PLANS)
def test_create__non_admin_in_template_owners_premium__ok(
    plan,
    mocker,
    api_client
):
    # arrange
    template_create_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.views.template.'
        'AnalyticService.templates_created'
    )
    kickoff_create_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.views.template.'
        'AnalyticService.templates_kickoff_created'
    )
    account = create_test_account(plan=plan)
    owner = create_test_user(
        email='owner@test.test',
        is_account_owner=True,
        account=account
    )
    non_admin = create_test_user(is_admin=False, account=account)
    mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'integrations.TemplateIntegrationsService.'
        'create_integrations_for_template'
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.post(
        path='/templates',
        data={
            'name': 'Template',
            'template_owners': [owner.id, non_admin.id],
            'is_active': True,
            'kickoff': {},
            'tasks': [
                {
                    'number': 1,
                    'name': 'First step',
                    'raw_performers': [
                        {
                            'type': PerformerType.USER,
                            'source_id': non_admin.id
                        }
                    ]
                }
            ]
        }
    )

    # assert
    assert response.status_code == 200
    response_data = response.json()

    assert set(response_data['template_owners']) == {
        non_admin.id, owner.id
    }
    template = Template.objects.get(id=response_data['id'])
    assert template.template_owners.count() == 2
    assert template.template_owners.filter(id=non_admin.id).exists()
    template_create_mock.assert_called_once()
    kickoff_create_mock.assert_called_once()


def test_create__non_admin_in_template_owners_freemium__ok(
    mocker,
    api_client
):
    # arrange
    template_create_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.views.template.'
        'AnalyticService.templates_created'
    )
    kickoff_create_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.views.template.'
        'AnalyticService.templates_kickoff_created'
    )
    account = create_test_account(plan=BillingPlanType.FREEMIUM)
    owner = create_test_user(
        email='owner@test.test',
        is_account_owner=True,
        account=account
    )
    non_admin = create_test_user(is_admin=False, account=account)
    mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'integrations.TemplateIntegrationsService.'
        'create_integrations_for_template'
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.post(
        path='/templates',
        data={
            'name': 'Template',
            'template_owners': [non_admin.id, owner.id],
            'is_active': True,
            'kickoff': {},
            'tasks': [
                {
                    'number': 1,
                    'name': 'First step',
                    'raw_performers': [
                        {
                            'type': PerformerType.USER,
                            'source_id': non_admin.id
                        }
                    ]
                }
            ]
        }
    )

    # assert
    assert response.status_code == 200
    response_data = response.json()

    assert set(response_data['template_owners']) == {
        non_admin.id, owner.id
    }
    template = Template.objects.get(id=response_data['id'])
    assert template.template_owners.count() == 2
    assert template.template_owners.filter(id=non_admin.id).exists()
    template_create_mock.assert_called_once()
    kickoff_create_mock.assert_called_once()


def test_create__api_request__ok(
    mocker,
    api_client
):

    # arrange
    account = create_test_account()
    user = create_test_user(account=account)
    create_integrations_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'integrations.TemplateIntegrationsService.'
        'create_integrations_for_template'
    )
    template_create_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.views.template.'
        'AnalyticService.templates_created'
    )
    kickoff_create_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.views.template.'
        'AnalyticService.templates_kickoff_created'
    )
    user_agent = 'Mozilla'
    get_user_agent_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.views.template.get_user_agent',
        return_value=user_agent
    )
    api_request_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'integrations.TemplateIntegrationsService.api_request',
    )
    api_client.token_authenticate(
        user=user,
        token_type=AuthTokenType.API
    )
    service_init_mock = mocker.patch.object(
        TemplateIntegrationsService,
        attribute='__init__',
        return_value=None
    )

    # act
    response = api_client.post(
        path='/templates',
        data={
            'name': 'Template',
            'template_owners': [user.id],
            'is_active': True,
            'kickoff': {},
            'tasks': [
                {
                    'number': 1,
                    'name': 'First step',
                    'raw_performers': [
                        {
                            'type': PerformerType.USER,
                            'source_id': user.id
                        }
                    ]
                }
            ]
        }
    )

    # assert
    assert response.status_code == 200
    template = Template.objects.get(id=response.data['id'])
    create_integrations_mock.assert_called_with(
        template=template
    )
    get_user_agent_mock.assert_called_once()
    assert service_init_mock.call_count == 2
    service_init_mock.has_calls([
        mocker.call(account=user.account, is_superuser=False, user=user),
        mocker.call(account=user.account, is_superuser=False, user=user)
    ])
    api_request_mock.assert_called_once_with(
        template=template,
        user_agent=user_agent
    )
    template_create_mock.assert_called_once()
    kickoff_create_mock.assert_called_once()


def test_create__draft_invalid_template_owners_format__set_default(
    mocker,
    api_client
):

    # arrange
    template_create_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.views.template.'
        'AnalyticService.templates_created'
    )
    kickoff_create_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.views.template.'
        'AnalyticService.templates_kickoff_created'
    )
    account = create_test_account()
    user = create_test_user(account=account)
    user_2 = create_test_user(account=account, email='t@t.t')
    api_client.token_authenticate(user)
    request_data = {
        'name': 'Template',
        'template_owners': [user.id, {'user_id': user_2.id}],
        'is_active': False,
        'kickoff': {},
        'tasks': [
            {
                'number': 1,
                'name': 'First step',
                'raw_performers': [
                    {
                        'type': PerformerType.USER,
                        'source_id': user.id
                    }
                ]
            }
        ]
    }

    # act
    response = api_client.post(
        path='/templates',
        data=request_data
    )

    # assert
    assert response.status_code == 200
    template = Template.objects.get(id=response.data['id'])
    assert template.template_owners.count() == 1
    assert template.template_owners.first().id == user.id
    template_create_mock.assert_called_once()
    kickoff_create_mock.assert_called_once()


def test_create__draft_another_acc_users_in_template_owners__set_default(
    mocker,
    api_client
):

    # arrange
    template_create_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.views.template.'
        'AnalyticService.templates_created'
    )
    kickoff_create_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.views.template.'
        'AnalyticService.templates_kickoff_created'
    )
    user = create_test_user()
    another_user = create_test_user(email='another@t.t')
    api_client.token_authenticate(user)
    request_data = {
        'name': 'Template',
        'template_owners': [user.id, another_user.id],
        'is_active': False,
        'kickoff': {},
        'tasks': [
            {
                'number': 1,
                'name': 'First step',
                'raw_performers': [
                    {
                        'type': PerformerType.USER,
                        'source_id': user.id
                    }
                ]
            }
        ]
    }

    # act
    response = api_client.post(
        path='/templates',
        data=request_data
    )

    # assert
    assert response.status_code == 200
    assert response.data['template_owners'] == [user.id]
    template = Template.objects.get(id=response.data['id'])
    assert template.template_owners.count() == 1
    assert template.template_owners.first().id == user.id
    template_create_mock.assert_called_once()
    kickoff_create_mock.assert_called_once()


def test_create__active_template__wf_name_template__sys_vars__ok(
    mocker,
    api_client,
):

    # arrange
    template_create_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.views.template.'
        'AnalyticService.templates_created'
    )
    kickoff_create_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.views.template.'
        'AnalyticService.templates_kickoff_created'
    )
    account = create_test_account()
    user = create_test_user(account=account)
    api_client.token_authenticate(user)
    wf_name_template = 'Workflow {{ date }} {{ template-name }}'
    request_data = {
        'name': 'Template',
        'wf_name_template': wf_name_template,
        'template_owners': [user.id],
        'is_active': True,
        'kickoff': {},
        'tasks': [
            {
                'number': 1,
                'name': 'First step',
                'raw_performers': [
                    {
                        'type': PerformerType.USER,
                        'source_id': user.id
                    }
                ]
            }
        ]
    }

    # act
    response = api_client.post(
        path='/templates',
        data=request_data
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
        'pneumatic_backend.processes.api_v2.views.template.'
        'AnalyticService.templates_created'
    )
    kickoff_create_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.views.template.'
        'AnalyticService.templates_kickoff_created'
    )
    account = create_test_account()
    user = create_test_user(account=account)
    api_client.token_authenticate(user)
    wf_name_template = 'Workflow {{ date }} {{ template-name }}'
    request_data = {
        'name': 'Template',
        'wf_name_template': wf_name_template,
        'template_owners': [user.id],
        'is_active': False,
        'kickoff': {},
        'tasks': [
            {
                'number': 1,
                'name': 'First step',
                'raw_performers': [
                    {
                        'type': PerformerType.USER,
                        'source_id': user.id
                    }
                ]
            }
        ]
    }

    # act
    response = api_client.post(
        path='/templates',
        data=request_data
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
        'pneumatic_backend.processes.api_v2.views.template.'
        'AnalyticService.templates_created'
    )
    kickoff_create_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.views.template.'
        'AnalyticService.templates_kickoff_created'
    )
    account = create_test_account()
    user = create_test_user(account=account)
    api_client.token_authenticate(user)
    wf_name_template = '{{ date }}{{ template-name }}'
    request_data = {
        'name': 'Template',
        'wf_name_template': wf_name_template,
        'template_owners': [user.id],
        'is_active': True,
        'kickoff': {},
        'tasks': [
            {
                'number': 1,
                'name': 'First step',
                'raw_performers': [
                    {
                        'type': PerformerType.USER,
                        'source_id': user.id
                    }
                ]
            }
        ]
    }

    # act
    response = api_client.post(
        path='/templates',
        data=request_data
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
    )
)
def test_create__wf_name_template__field__ok(
    mocker,
    api_client,
    field_type,
):

    # arrange
    template_create_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.views.template.'
        'AnalyticService.templates_created'
    )
    kickoff_create_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.views.template.'
        'AnalyticService.templates_kickoff_created'
    )

    account = create_test_account()
    user = create_test_user(account=account)
    api_client.token_authenticate(user)
    field_api_name = 'field-api-name'
    wf_name_template = '{{ field-api-name }}'
    request_data = {
        'name': 'Template',
        'wf_name_template': wf_name_template,
        'template_owners': [user.id],
        'is_active': True,
        'kickoff': {
            'fields': [
                {
                    'type': field_type,
                    'name': 'Field name',
                    'is_required': True,
                    'order': 1,
                    'api_name': field_api_name
                }
            ]
        },
        'tasks': [
            {
                'number': 1,
                'name': 'First step',
                'raw_performers': [
                    {
                        'type': PerformerType.USER,
                        'source_id': user.id
                    }
                ]
            }
        ]
    }

    # act
    response = api_client.post(
        path='/templates',
        data=request_data
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
    )
)
def test_create__wf_name_template__field_with_selections__ok(
    mocker,
    api_client,
    field_type,
):

    # arrange
    template_create_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.views.template.'
        'AnalyticService.templates_created'
    )
    kickoff_create_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.views.template.'
        'AnalyticService.templates_kickoff_created'
    )
    account = create_test_account()
    user = create_test_user(account=account)
    api_client.token_authenticate(user)
    field_api_name = 'field-api-name'
    wf_name_template = '{{ field-api-name }}'
    request_data = {
        'name': 'Template',
        'wf_name_template': wf_name_template,
        'template_owners': [user.id],
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
                        }
                    ]
                }
            ]
        },
        'tasks': [
            {
                'number': 1,
                'name': 'First step',
                'raw_performers': [
                    {
                        'type': PerformerType.USER,
                        'source_id': user.id
                    }
                ]
            }
        ]
    }

    # act
    response = api_client.post(
        path='/templates',
        data=request_data
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
        'pneumatic_backend.processes.api_v2.views.template.'
        'AnalyticService.templates_created'
    )
    kickoff_create_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.views.template.'
        'AnalyticService.templates_kickoff_created'
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
        'template_owners': [user.id],
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
                            'value': 'value 2'
                        }
                    ]
                }
            ]
        },
        'tasks': [
            {
                'number': 1,
                'name': 'First step',
                'raw_performers': [
                    {
                        'type': PerformerType.USER,
                        'source_id': user.id
                    }
                ]
            }
        ]
    }

    # act
    response = api_client.post(
        path='/templates',
        data=request_data
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
        'pneumatic_backend.processes.api_v2.views.template.'
        'AnalyticService.templates_created'
    )
    kickoff_create_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.views.template.'
        'AnalyticService.templates_kickoff_created'
    )
    account = create_test_account()
    user = create_test_user(account=account)
    api_client.token_authenticate(user)
    wf_name_template = 'Workflow {{field-api-name}} {{field-api-name-2}}'
    request_data = {
        'name': 'Template',
        'wf_name_template': wf_name_template,
        'template_owners': [user.id],
        'is_active': True,
        'kickoff': {
            'fields': [
                {
                    'type': FieldType.STRING,
                    'name': 'Field name 1',
                    'is_required': True,
                    'order': 1,
                    'api_name': 'some-api-name',
                }
            ]
        },
        'tasks': [
            {
                'number': 1,
                'name': 'First step',
                'raw_performers': [
                    {
                        'type': PerformerType.USER,
                        'source_id': user.id
                    }
                ]
            }
        ]
    }

    # act
    response = api_client.post(
        path='/templates',
        data=request_data
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
        'pneumatic_backend.processes.api_v2.views.template.'
        'AnalyticService.templates_created'
    )
    kickoff_create_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.views.template.'
        'AnalyticService.templates_kickoff_created'
    )
    account = create_test_account()
    user = create_test_user(account=account)
    api_client.token_authenticate(user)
    request_data = {
        'name': 'Template',
        'wf_name_template': wf_name_template,
        'template_owners': [user.id],
        'is_active': True,
        'kickoff': {},
        'tasks': [
            {
                'number': 1,
                'name': 'First step',
                'raw_performers': [
                    {
                        'type': PerformerType.USER,
                        'source_id': user.id
                    }
                ]
            }
        ]
    }

    # act
    response = api_client.post(
        path='/templates',
        data=request_data
    )

    # assert
    assert response.status_code == 200
    assert response.data['wf_name_template'] == wf_name_template
    template = Template.objects.get(id=response.data['id'])
    assert template.wf_name_template == wf_name_template
    template_create_mock.assert_called_once()
    kickoff_create_mock.assert_called_once()
