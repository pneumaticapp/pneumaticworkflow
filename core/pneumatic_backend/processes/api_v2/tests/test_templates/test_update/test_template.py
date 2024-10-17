import pytest
from django.conf import settings

from pneumatic_backend.accounts.enums import BillingPlanType
from pneumatic_backend.processes.tests.fixtures import (
    create_test_user,
    create_test_template,
    create_test_workflow,
    create_invited_user,
    create_test_account
)
from pneumatic_backend.processes.models import (
    FieldTemplate,
    Template
)
from pneumatic_backend.accounts.services import AccountService
from pneumatic_backend.utils.validation import ErrorCode
from pneumatic_backend.processes.messages import template as messages
from pneumatic_backend.processes.enums import (
    PerformerType,
    FieldType,
)
from pneumatic_backend.accounts.tokens import (
    TransferToken
)
from pneumatic_backend.accounts.services.user_transfer import (
    UserTransferService
)
from pneumatic_backend.authentication.tokens import (
    PublicToken,
    EmbedToken,
)
from pneumatic_backend.authentication.enums import AuthTokenType
from pneumatic_backend.processes.api_v2.services.templates\
    .integrations import TemplateIntegrationsService


pytestmark = pytest.mark.django_db


class TestUpdateTemplate:

    def test_update__all_fields__ok(
        self,
        api_client,
        mocker,
    ):

        # arrange
        user = create_test_user()
        user2 = create_test_user(
            email='test2@pneumatic.app',
            account=user.account
        )
        api_client.token_authenticate(user)
        template = create_test_template(
            user,
            is_active=True,
            is_public=False,
            tasks_count=1,
            wf_name_template='old wf template',
        )
        task = template.tasks.first()
        FieldTemplate.objects.create(
            name='Name',
            api_name='name',
            type=FieldType.STRING,
            kickoff=template.kickoff_instance,
            template=template,
        )
        account_service = AccountService(
            instance=user.account,
            user=user
        )
        account_service.update_active_templates()
        create_integrations_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.services.templates.'
            'integrations.TemplateIntegrationsService.'
            'create_integrations_for_template'
        )
        template_updated_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.services.templates.'
            'integrations.TemplateIntegrationsService.template_updated'
        )
        api_request_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.services.templates.'
            'integrations.TemplateIntegrationsService.api_request',
        )

        request_data = {
            'id': template.id,
            'is_active': True,
            'is_public': template.is_public,
            'description': '',
            'name': 'Name changed',
            'wf_name_template': 'New wf name',
            'template_owners': [user.id, user2.id],
            'finalizable': True,
            'kickoff': {
                'id': template.kickoff_instance.id
            },
            'tasks': [
                {
                    'id': task.id,
                    'api_name': task.api_name,
                    'number': task.number,
                    'name': task.name,
                    'raw_performers': [
                        {
                            'type': PerformerType.USER,
                            'source_id': user.id
                        }
                    ]
                }
            ]
        }
        template_update_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.views.template.'
            'AnalyticService.templates_updated'
        )
        kickoff_update_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.views.template.'
            'AnalyticService.templates_kickoff_updated'
        )

        # act
        response = api_client.put(
            path=f'/templates/{template.id}',
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
        assert response_data['wf_name_template'] == 'New wf name'
        assert response_data['description'] == request_data['description']
        assert response_data['is_active'] == request_data['is_active']
        assert response_data['is_public'] == request_data['is_public']
        assert response_data['public_url'] is not None
        assert response_data['finalizable'] == request_data['finalizable']
        assert response_data['tasks_count'] == 1
        assert response_data['performers_count'] == 1
        assert response_data['updated_by'] == user.id
        assert response_data.get('date_updated')

        template.refresh_from_db()
        template_owners_ids = list(template.template_owners.order_by(
            'id'
        ).values_list('id', flat=True))
        assert template.kickoff_instance
        assert template_owners_ids == request_data['template_owners']
        assert template.name == request_data['name']
        assert template.description == request_data['description']
        assert template.is_active == request_data['is_active']
        assert template.is_public == request_data['is_public']
        assert template.public_url is not None
        assert template.finalizable == request_data['finalizable']
        assert template.updated_by is not None
        assert template.date_updated.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        assert user.account.active_templates == 1
        template_update_mock.assert_called_once_with(
            user=user,
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
        kickoff_update_mock.assert_called_once_with(
            user=user,
            template=template,
            auth_type=AuthTokenType.USER,
            is_superuser=False,
        )
        create_integrations_mock.assert_not_called()
        template_updated_mock.assert_called_once_with(template=template)
        api_request_mock.assert_not_called()

    def test_update__active_to_draft__ok(
        self,
        mocker,
        api_client,
    ):

        # arrange
        account = create_test_account()
        user = create_test_user(account=account)
        user2 = create_test_user(
            email='test2@pneumatic.app',
            account=account
        )
        api_client.token_authenticate(user)
        template = create_test_template(
            user,
            is_active=True,
            tasks_count=1
        )
        task = template.tasks.first()
        FieldTemplate.objects.create(
            name='Name',
            api_name='name',
            type=FieldType.STRING,
            kickoff=template.kickoff_instance,
            template=template,
        )
        account_service = AccountService(
            instance=account,
            user=user
        )
        account_service.update_active_templates()
        create_integrations_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.services.templates.'
            'integrations.TemplateIntegrationsService.'
            'create_integrations_for_template'
        )
        template_updated_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.services.templates.'
            'integrations.TemplateIntegrationsService.template_updated'
        )
        request_data = {
            'id': template.id,
            'is_active': False,
            'description': 'Desc changed',
            'name': 'Name changed',
            'template_owners': [user.id, user2.id],
            'finalizable': True,
            'kickoff': {
                'id': template.kickoff_instance.id,
                'description': 'Desc changed'
            },
            'tasks': [
                {
                    'id': task.id,
                    'name': 'First step changed',
                    'raw_performers': [
                        {
                            'type': PerformerType.USER,
                            'source_id': user.id
                        }
                    ]
                }
            ]
        }
        template_update_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.views.template.'
            'AnalyticService.templates_updated'
        )
        kickoff_update_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.views.template.'
            'AnalyticService.templates_kickoff_updated'
        )

        # act
        response = api_client.put(
            path=f'/templates/{template.id}',
            data=request_data
        )

        # assert
        assert response.status_code == 200
        response_data = response.json()

        assert response_data.get('id')
        assert set(response_data['template_owners']) == set(
            request_data['template_owners']
        )
        assert response_data['name'] == request_data['name']
        assert response_data['description'] == request_data['description']
        assert response_data['is_active'] == request_data['is_active']
        assert response_data['finalizable'] == request_data['finalizable']
        assert response_data['tasks_count'] == 1
        assert response_data['performers_count'] == 1
        assert response_data['updated_by'] == user.id
        assert response_data.get('date_updated')

        assert response_data['kickoff']['id'] == (
            request_data['kickoff']['id']
        )
        assert response_data['kickoff']['description'] == (
            request_data['kickoff']['description']
        )

        assert response_data['tasks'][0]['id'] == (
            request_data['tasks'][0]['id']
        )
        assert response_data['tasks'][0]['name'] == (
            request_data['tasks'][0]['name']
        )

        template.refresh_from_db()
        assert template.is_active is False
        template_draft = template.draft
        assert template_draft is not None
        assert template_draft.draft is not None
        assert template_draft.draft['is_active'] is False
        assert template.kickoff_instance is not None
        assert template.tasks.exists()
        account.refresh_from_db()
        assert account.active_templates == 0
        template_update_mock.assert_not_called()
        kickoff_update_mock.assert_not_called()
        create_integrations_mock.assert_not_called()
        template_updated_mock.assert_called_once_with(template=template)

    def test_update__draft_to_draft__ok(
        self,
        mocker,
        api_client,
    ):

        # arrange
        user = create_test_user()
        user2 = create_test_user(
            email='test2@pneumatic.app',
            account=user.account
        )
        api_client.token_authenticate(user)

        response = api_client.post(
            path='/templates',
            data={
                'description': 'Desc',
                'name': 'Name',
                'template_owners': [user.id, user2.id],
                'is_active': False,
                'finalizable': True,
                'kickoff': {
                    'description': 'Desc',
                },
                'tasks': [
                    {
                      'number': 1,
                      'name': 'First step'
                    }
                ]
            }
        )
        account_service = AccountService(
            instance=user.account,
            user=user
        )
        account_service.update_active_templates()
        template = Template.objects.get(id=response.data['id'])

        request_data = {
            'id': template.id,
            'is_active': False,
            'description': 'Desc changed',
            'name': 'Name changed',
            'template_owners': [user.id, user2.id],
            'finalizable': True,
            'kickoff': {
                'description': 'Desc changed',
            },
            'tasks': [
                {
                    'name': 'First step changed'
                }
            ]
        }
        create_integrations_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.services.templates.'
            'integrations.TemplateIntegrationsService.'
            'create_integrations_for_template'
        )
        template_updated_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.services.templates.'
            'integrations.TemplateIntegrationsService.template_updated'
        )
        template_update_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.views.template.'
            'AnalyticService.templates_updated'
        )
        kickoff_update_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.views.template.'
            'AnalyticService.templates_kickoff_updated'
        )

        # act
        response = api_client.put(
            path=f'/templates/{template.id}',
            data=request_data
        )

        # assert
        assert response.status_code == 200
        response_data = response.json()

        assert response_data['id'] == request_data['id']
        assert set(response_data['template_owners']) == set(
            request_data['template_owners']
        )
        assert response_data['name'] == request_data['name']
        assert response_data['description'] == request_data['description']
        assert response_data['is_active'] == request_data['is_active']
        assert response_data['finalizable'] == request_data['finalizable']
        assert response_data['tasks_count'] == 1
        assert response_data['performers_count'] == 0
        assert response_data['updated_by'] == user.id
        assert response_data.get('date_updated')

        assert response_data['kickoff']['description'] == (
            request_data['kickoff']['description']
        )
        assert response_data['tasks'][0]['name'] == (
            request_data['tasks'][0]['name']
        )

        template.refresh_from_db()
        assert template.is_active is False
        assert not template.tasks.exists()
        template_draft = template.draft
        assert template_draft is not None
        assert template_draft.draft is not None
        assert template_draft.draft['is_active'] is False
        assert user.account.active_templates == 0

        template_update_mock.assert_not_called()
        kickoff_update_mock.assert_not_called()
        create_integrations_mock.assert_not_called()
        template_updated_mock.assert_called_once_with(template=template)

    def test_update_draft_to_active__ok(
        self,
        mocker,
        api_client,
    ):

        # arrange
        account = create_test_account()
        user = create_test_user(account=account)
        api_client.token_authenticate(user)

        response = api_client.post(
            path='/templates',
            data={
                'description': 'Desc',
                'name': 'Name',
                'template_owners': [user.id],
                'is_active': False,
                'finalizable': True,
                'kickoff': {
                    'description': 'Desc',
                },
                'tasks': [
                    {
                      'number': 1,
                      'name': 'First step'
                    }
                ]
            }
        )
        template = Template.objects.get(id=response.data['id'])
        kickoff = template.kickoff_instance
        create_integrations_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.services.templates.'
            'integrations.TemplateIntegrationsService.'
            'create_integrations_for_template'
        )
        template_updated_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.services.templates.'
            'integrations.TemplateIntegrationsService.template_updated'
        )
        template_update_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.views.template.'
            'AnalyticService.templates_updated'
        )
        kickoff_update_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.views.template.'
            'AnalyticService.templates_kickoff_updated'
        )

        request_data = {
            'id': template.id,
            'is_active': True,
            'description': '',
            'name': 'Name changed',
            'template_owners': [user.id],
            'finalizable': True,
            'kickoff': {
                'id': kickoff.id,
                'description': 'Desc changed',
            },
            'tasks': [
                {
                    'number': 1,
                    'name': 'First step changed',
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
        response = api_client.put(
            path=f'/templates/{template.id}',
            data=request_data
        )

        # assert
        assert response.status_code == 200
        response_data = response.json()

        assert response_data['id'] == request_data['id']
        assert response_data['template_owners'] == (
            request_data['template_owners']
        )
        assert response_data['name'] == request_data['name']
        assert response_data['description'] == request_data['description']
        assert response_data['is_active'] == request_data['is_active']
        assert response_data['finalizable'] == request_data['finalizable']
        assert response_data['tasks_count'] == 1
        assert response_data['performers_count'] == 1
        assert response_data['updated_by'] == user.id
        assert response_data.get('date_updated')

        assert response_data['kickoff'].get('id')
        assert response_data['kickoff']['description'] == (
            request_data['kickoff']['description']
        )
        response_task_data = response_data['tasks'][0]
        request_task_data = request_data['tasks'][0]
        assert response_task_data['name'] == request_task_data['name']
        assert response_task_data['number'] == request_task_data['number']
        raw_performers = response_task_data['raw_performers']
        assert len(raw_performers) == 1
        assert raw_performers[0]['type'] == PerformerType.USER
        assert raw_performers[0]['source_id'] == str(user.id)

        template.refresh_from_db()
        assert template.is_active is True
        assert template.kickoff_instance is not None
        assert template.tasks.exists()
        assert template.name == request_data['name']

        draft = template.get_draft()
        assert draft['is_active'] == request_data['is_active']
        assert draft['name'] == request_data['name']
        assert draft['tasks_count'] == 1
        assert draft['performers_count'] == 1

        account.refresh_from_db()
        assert account.active_templates == 1
        template_update_mock.assert_called_once()
        kickoff_update_mock.assert_called_once()
        create_integrations_mock.assert_not_called()
        template_updated_mock.assert_called_once_with(template=template)

    def test_update__user_are_not_template_owner__permission_denied(
        self,
        mocker,
        api_client,
    ):

        # arrange
        user = create_test_user()
        user.account.billing_plan = BillingPlanType.PREMIUM
        user.account.save()
        admin_user = create_test_user(
            account=user.account,
            email='admin@test.test',
            is_account_owner=False
        )
        api_client.token_authenticate(user)

        response = api_client.post(
            path='/templates',
            data={
                'description': 'Desc',
                'name': 'Name',
                'template_owners': [user.id],
                'is_active': False,
                'finalizable': True,
                'kickoff': {
                    'description': 'Desc',
                },
                'tasks': [
                    {
                        'number': 1,
                        'name': 'First step',
                        'raw_performers': [
                            {
                                'type': PerformerType.USER,
                                'source_id': admin_user.id
                            }
                        ]
                    }
                ]
            }
        )
        template = Template.objects.get(id=response.data['id'])
        mocker.patch(
            'pneumatic_backend.processes.api_v2.services.templates.'
            'integrations.TemplateIntegrationsService.template_updated'
        )
        template_update_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.views.template.'
            'AnalyticService.templates_updated'
        )
        kickoff_update_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.views.template.'
            'AnalyticService.templates_kickoff_updated'
        )

        request_data = {
            'id': template.id,
            'is_active': True,
            'description': '',
            'name': 'Name changed',
            'template_owners': [user.id],
            'finalizable': True,
            'kickoff': {
                'description': 'Desc changed',
            },
            'tasks': [
                {
                    'number': 1,
                    'name': 'First step changed',
                    'raw_performers': [
                        {
                            'type': PerformerType.USER,
                            'source_id': admin_user.id
                        }
                    ]
                }
            ]
        }
        api_client.token_authenticate(admin_user)

        # act
        response = api_client.put(
            path=f'/templates/{template.id}',
            data=request_data
        )

        # assert
        assert response.status_code == 403
        assert response.data['detail'] == messages.MSG_PT_0023
        template_update_mock.assert_not_called()
        kickoff_update_mock.assert_not_called()

    def test_update__draft__ok(
        self,
        mocker,
        api_client,
    ):

        # arrange
        template_update_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.views.template.'
            'AnalyticService.templates_updated'
        )
        kickoff_update_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.views.template.'
            'AnalyticService.templates_kickoff_updated'
        )
        user = create_test_user()
        api_client.token_authenticate(user)

        response = api_client.post(
            path='/templates',
            data={
                'name': 'Origin template name',
                'description': 'Desc',
                'template_owners': [user.id],
                'is_active': False,
                'finalizable': True,
                'kickoff': {},
                'tasks': [
                    {
                        'number': 1,
                        'name': 'First step',
                        'raw_performers': [
                            {
                                'type': PerformerType.WORKFLOW_STARTER,
                                'source_id': None
                            }
                        ]
                    },
                    {
                        'number': 1,
                        'name': 'Second step'
                    }
                ]
            }
        )
        template = Template.objects.get(id=response.data['id'])
        mocker.patch(
            'pneumatic_backend.processes.api_v2.services.templates.'
            'integrations.TemplateIntegrationsService.template_updated'
        )
        request_data = {
            'id': template.id,
            'name': 'Template name changed',
            'description': 'Desc changed',
            'template_owners': [user.id],
            'is_active': False,
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

        response_put = api_client.put(
            path=f'/templates/{template.id}',
            data=request_data
        )

        # act
        response = api_client.get('/templates')

        # assert
        assert response_put.status_code == 200
        assert response.status_code == 200
        assert len(response.data) == 1
        response_data = response.data[0]

        # Not draft value
        assert response_data['name'] == 'Origin template name'
        assert response_data['tasks_count'] == 0
        assert response_data['performers_count'] == 0
        assert user.account.active_templates == 0
        template_update_mock.assert_not_called()
        kickoff_update_mock.assert_not_called()

    def test_update__draft__remove_yourself_from_template_owners__ok(
        self,
        mocker,
        api_client,
    ):

        # arrange
        template_update_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.views.template.'
            'AnalyticService.templates_updated'
        )
        kickoff_update_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.views.template.'
            'AnalyticService.templates_kickoff_updated'
        )
        user = create_test_user()
        user_2 = create_test_user(account=user.account, email='t@t.t')
        api_client.token_authenticate(user)

        response_create = api_client.post(
            path='/templates',
            data={
                'name': 'Template',
                'description': 'Desc',
                'template_owners': [user.id],
                'is_active': False,
                'finalizable': True,
                'kickoff': {},
                'tasks': [
                    {
                        'number': 1,
                        'name': 'First step',
                        'raw_performers': [
                            {
                                'type': PerformerType.WORKFLOW_STARTER,
                                'source_id': None
                            }
                        ]
                    },
                    {
                        'number': 1,
                        'name': 'Second step'
                    }
                ]
            }
        )
        template = Template.objects.get(id=response_create.data['id'])
        mocker.patch(
            'pneumatic_backend.processes.api_v2.services.templates.'
            'integrations.TemplateIntegrationsService.template_updated'
        )
        request_data = {
            'id': template.id,
            'name': 'Template changed',
            'description': 'Desc changed',
            'template_owners': [user_2.id],
            'is_active': False,
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

        # act
        response_update = api_client.put(
            path=f'/templates/{template.id}',
            data=request_data
        )

        # assert
        assert response_create.status_code == 200
        assert response_update.status_code == 200

        assert response_update.data['template_owners'] == [user_2.id]
        assert response_update.data['is_active'] is False
        template.refresh_from_db()
        assert template.is_active is False
        assert template.template_owners.count() == 1
        assert template.template_owners.filter(id=user.id).exists()
        template_update_mock.assert_not_called()
        kickoff_update_mock.assert_not_called()

    def test_update__validate_limit_active_templates__validation_error(
        self,
        mocker,
        api_client
    ):

        # arrange
        user = create_test_user()
        api_client.token_authenticate(user)
        for _ in range(settings.PAYWALL_MAX_ACTIVE_TEMPLATES):
            create_test_template(
                user=user,
                is_active=True,
                tasks_count=1
            )
        template = create_test_template(
            user=user,
            is_active=False,
            tasks_count=1
        )
        account_service = AccountService(
            instance=user.account,
            user=user
        )
        account_service.update_active_templates()
        task = template.tasks.first()

        # act
        response = api_client.put(
            path=f'/templates/{template.id}',
            data={
                'id': template.id,
                'is_active': True,
                'description':  template.description,
                'name': template.name,
                'template_owners': [user.id],
                'finalizable': True,
                'kickoff': {
                    'id': template.kickoff_instance.id
                },
                'tasks': [
                    {
                        'id': task.id,
                        'number': task.number,
                        'name': task.name,
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

    def test_update__unlimited_drafts_for_account__ok(
        self,
        mocker,
        api_client
    ):

        # arrange
        user = create_test_user()
        api_client.token_authenticate(user)
        for _ in range(settings.PAYWALL_MAX_ACTIVE_TEMPLATES):
            create_test_template(
                user=user,
                is_active=True,
                tasks_count=1
            )
        template = create_test_template(
            user=user,
            is_active=False,
            tasks_count=1
        )
        account_service = AccountService(
            instance=user.account,
            user=user
        )
        account_service.update_active_templates()
        task = template.tasks.first()
        mocker.patch(
            'pneumatic_backend.processes.api_v2.services.templates.'
            'integrations.TemplateIntegrationsService.template_updated'
        )

        # act
        response = api_client.put(
            path=f'/templates/{template.id}',
            data={
                'id': template.id,
                'is_active': False,
                'description':  template.description,
                'name': template.name,
                'template_owners': [user.id],
                'finalizable': True,
                'kickoff': {
                    'id': template.kickoff_instance.id
                },
                'tasks': [
                    {
                        'id': task.id,
                        'number': task.number,
                        'name': task.name,
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

    def test_update__public__ok(
        self,
        mocker,
        api_client
    ):

        # arrange
        user = create_test_user()
        api_client.token_authenticate(user)
        token = 'a' * PublicToken.token_length
        public_url = f'{settings.PUBLIC_FORMS_ORIGIN}/{token}'
        token_mock = mocker.patch.object(
            PublicToken,
            attribute='__str__',
            return_value=token
        )

        response = api_client.post(
            path='/templates',
            data={
                'description': 'Desc',
                'name': 'Name',
                'template_owners': [user.id],
                'is_active': True,
                'is_public': False,
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
        template = Template.objects.get(id=response.data['id'])
        task = template.tasks.first()
        mocker.patch(
            'pneumatic_backend.processes.api_v2.services.templates.'
            'integrations.TemplateIntegrationsService.template_updated'
        )

        # act
        response = api_client.put(
            path=f'/templates/{template.id}',
            data={
                'id': template.id,
                'is_active': True,
                'is_public': True,
                'description': template.description,
                'name': template.name,
                'template_owners': [user.id],
                'finalizable': template.finalizable,
                'kickoff': {
                    'id': template.kickoff_instance.id
                },
                'tasks': [
                    {
                        'id': task.id,
                        'number': task.number,
                        'name': task.name,
                        'api_name': task.api_name,
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
        template.refresh_from_db()
        assert template.is_public is True
        assert template.public_url == public_url
        token_mock.assert_called_once()

    def test_update__public_success_url__paid_feature__validation_error(
        self,
        mocker,
        api_client
    ):
        # arrange
        user = create_test_user()
        api_client.token_authenticate(user)
        template = create_test_template(
            user=user,
            is_active=True,
            is_public=True
        )
        task = template.tasks.first()
        request_data = {
            'id': template.id,
            'is_active': template.is_active,
            'is_public': template.is_public,
            'public_success_url': 'my.pneumatic.app',
            'description': template.description,
            'name': template.name,
            'template_owners': [user.id],
            'finalizable': template.finalizable,
            'kickoff': {
                'id': template.kickoff_instance.id
            },
            'tasks': [
                {
                    'id': task.id,
                    'number': task.number,
                    'api_name': task.api_name,
                    'name': task.name,
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
        response = api_client.put(
            path=f'/templates/{template.id}',
            data=request_data
        )

        # assert
        assert response.status_code == 400
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['message'] == messages.MSG_PT_0020
        assert response.data['details']['name'] == 'public_success_url'

    def test_update__embed__ok(
        self,
        mocker,
        api_client
    ):

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
        response = api_client.post(
            path='/templates',
            data={
                'description': 'Desc',
                'name': 'Name',
                'template_owners': [user.id],
                'is_active': True,
                'is_embedded': False,
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
        template = Template.objects.get(id=response.data['id'])
        task = template.tasks.first()
        mocker.patch(
            'pneumatic_backend.processes.api_v2.services.templates.'
            'integrations.TemplateIntegrationsService.template_updated'
        )
        request_data = {
            'id': template.id,
            'is_active': True,
            'is_embedded': True,
            'description': template.description,
            'name': template.name,
            'template_owners': [user.id],
            'finalizable': template.finalizable,
            'kickoff': {
                'id': template.kickoff_instance.id
            },
            'tasks': [
                {
                    'id': task.id,
                    'number': task.number,
                    'name': task.name,
                    'api_name': task.api_name,
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
        response = api_client.put(
            path=f'/templates/{template.id}',
            data=request_data
        )

        # assert
        assert response.status_code == 200
        assert response.data['is_embedded'] is True
        assert response.data['embed_url'] == embed_url
        template.refresh_from_db()
        assert template.is_embedded is True
        assert template.embed_url == embed_url
        token_mock.assert_called_once()

    def test_update__workflow_is_external_not_changed__ok(
        self,
        mocker,
        api_client
    ):

        # arrange
        user = create_test_user()
        api_client.token_authenticate(user)
        workflow = create_test_workflow(
            user=user,
            is_external=True,
            tasks_count=1
        )
        template = workflow.template
        task_template = template.tasks.first()
        mocker.patch(
            'pneumatic_backend.processes.api_v2.services.templates.'
            'integrations.TemplateIntegrationsService.template_updated'
        )
        request_data = {
            'id': template.id,
            'is_active': template.is_active,
            'is_public': False,
            'description': template.description,
            'name': template.name,
            'template_owners': [user.id],
            'finalizable': template.finalizable,
            'kickoff': {
                'id': template.kickoff_instance.id
            },
            'tasks': [
                {
                    'id': task_template.id,
                    'number': task_template.number,
                    'name': task_template.name,
                    'api_name': task_template.api_name,
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
        response = api_client.put(
            path=f'/templates/{template.id}',
            data=request_data
        )
        workflow.refresh_from_db()

        # assert
        assert response.status_code == 200
        assert workflow.is_external is True

    def test_update__change_template_owners__ok(
        self,
        mocker,
        api_client,
    ):

        # arrange
        account = create_test_account(plan=BillingPlanType.PREMIUM)
        user = create_test_user(account=account)
        create_test_user(
            email='test2@pneumatic.app',
            account=account
        )
        api_client.token_authenticate(user)
        template = create_test_template(
            user,
            is_active=True,
            is_public=False,
            tasks_count=1
        )
        task = template.tasks.first()
        mocker.patch(
            'pneumatic_backend.processes.api_v2.services.templates.'
            'integrations.TemplateIntegrationsService.template_updated'
        )
        template_update_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.views.template.'
            'AnalyticService.templates_updated'
        )
        kickoff_update_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.views.template.'
            'AnalyticService.templates_kickoff_updated'
        )

        request_data = {
            'id': template.id,
            'is_active': True,
            'is_public': template.is_public,
            'description': '',
            'name': 'Name changed',
            'template_owners': [user.id],
            'finalizable': True,
            'kickoff': {
                'id': template.kickoff_instance.id
            },
            'tasks': [
                {
                    'id': task.id,
                    'api_name': task.api_name,
                    'number': task.number,
                    'name': task.name,
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
        response = api_client.put(
            path=f'/templates/{template.id}',
            data=request_data
        )

        # assert
        assert response.status_code == 200
        response_data = response.json()
        assert len(response_data['template_owners']) == len(
            request_data['template_owners']
        )
        template_update_mock.assert_called_once()
        kickoff_update_mock.assert_called_once()

    def test_update__make_public__ok(
        self,
        mocker,
        api_client
    ):

        # arrange
        user = create_test_user()
        account = user.account
        account.billing_plan = BillingPlanType.PREMIUM
        account.save()
        api_client.token_authenticate(user)
        response = api_client.post(
            path='/templates',
            data={
                'description': 'Desc',
                'name': 'Name',
                'template_owners': [user.id],
                'is_active': True,
                'is_public': False,
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
        template = Template.objects.get(id=response.data['id'])
        task = template.tasks.first()
        mocker.patch(
            'pneumatic_backend.processes.api_v2.services.templates.'
            'integrations.TemplateIntegrationsService.template_updated'
        )
        request_data = {
            'id': template.id,
            'is_active': True,
            'is_public': True,
            'description': template.description,
            'name': template.name,
            'template_owners': [user.id],
            'finalizable': template.finalizable,
            'kickoff': {
                'id': template.kickoff_instance.id
            },
            'tasks': [
                {
                    'id': task.id,
                    'number': task.number,
                    'name': task.name,
                    'api_name': task.api_name,
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
        response = api_client.put(
            path=f'/templates/{template.id}',
            data=request_data
        )

        # assert
        assert response.status_code == 200
        assert response.data['public_url'] is not None
        assert response.data['is_public'] is True

    def test_update__make_not_public__ok(
        self,
        mocker,
        api_client
    ):

        # arrange
        user = create_test_user()
        api_client.token_authenticate(user)
        response = api_client.post(
            path='/templates',
            data={
                'description': 'Desc',
                'name': 'Name',
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
        template = Template.objects.get(id=response.data['id'])
        task = template.tasks.first()
        mocker.patch(
            'pneumatic_backend.processes.api_v2.services.templates.'
            'integrations.TemplateIntegrationsService.template_updated'
        )
        request_data = {
            'id': template.id,
            'is_active': True,
            'is_public': False,
            'description': template.description,
            'name': template.name,
            'template_owners': [user.id],
            'finalizable': template.finalizable,
            'kickoff': {
                'id': template.kickoff_instance.id
            },
            'tasks': [
                {
                    'id': task.id,
                    'number': task.number,
                    'name': task.name,
                    'api_name': task.api_name,
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
        response = api_client.put(
            path=f'/templates/{template.id}',
            data=request_data
        )

        # assert
        assert response.status_code == 200
        assert response.data['public_url'] is not None
        assert response.data['is_public'] is False

    def test_update__checklist_service__called(
        self,
        api_client,
        mocker,
    ):

        # arrange
        account = create_test_account(plan=BillingPlanType.PREMIUM)
        user = create_test_user(account=account)
        user_2 = create_test_user(email='t@t.t', account=account)
        api_client.token_authenticate(user)
        template = create_test_template(
            user,
            is_active=True,
            tasks_count=1
        )
        task = template.tasks.first()
        account_service = AccountService(
            instance=user.account,
            user=user
        )
        account_service.update_active_templates()
        mocker.patch(
            'pneumatic_backend.processes.api_v2.services.templates.'
            'integrations.TemplateIntegrationsService.template_updated'
        )
        request_data = {
            'id': template.id,
            'is_active': True,
            'is_public': template.is_public,
            'description': '',
            'name': 'Name changed',
            'template_owners': [user.id, user_2.id],
            'finalizable': True,
            'kickoff': {
                'id': template.kickoff_instance.id
            },
            'tasks': [
                {
                    'id': task.id,
                    'api_name': task.api_name,
                    'number': task.number,
                    'name': task.name,
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
        response = api_client.put(
            path=f'/templates/{template.id}',
            data=request_data
        )

        # assert
        assert response.status_code == 200

    @pytest.mark.parametrize('is_active', (True, False))
    def test_update__after_template_owner_transfer__ok(
        self,
        mocker,
        is_active,
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

        new_account = create_test_account(name='transfer to')
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
            is_active=is_active,
            tasks_count=1
        )
        task = template.tasks.first()
        task.add_raw_performer(account_1_owner)
        service = UserTransferService()
        service.accept_transfer(
            user_id=new_user.id,
            token_str=str(token)
        )
        api_client.token_authenticate(account_1_owner)
        mocker.patch(
            'pneumatic_backend.processes.api_v2.services.templates.'
            'integrations.TemplateIntegrationsService.template_updated'
        )
        request_data = {
            'id': template.id,
            'is_active': True,
            'is_public': template.is_public,
            'description': '',
            'name': 'Name changed',
            'template_owners': [account_1_owner.id],
            'finalizable': True,
            'kickoff': {
                'id': template.kickoff_instance.id
            },
            'tasks': [
                {
                    'id': task.id,
                    'api_name': task.api_name,
                    'number': task.number,
                    'name': task.name,
                    'raw_performers': [
                        {
                            'type': PerformerType.USER,
                            'source_id': account_1_owner.id
                        }
                    ]
                }
            ]
        }

        # act
        response = api_client.put(
            path=f'/templates/{template.id}',
            data=request_data
        )

        # assert
        assert response.status_code == 200

    @pytest.mark.parametrize('plan', BillingPlanType.PAYMENT_PLANS)
    def test_update__non_admin_in_template_owners_premium__ok(
        self,
        plan,
        mocker,
        api_client,
    ):

        # arrange
        account = create_test_account(plan=plan)
        owner = create_test_user(
            email='owner@test.test',
            is_account_owner=True,
            account=account
        )
        non_admin = create_test_user(is_admin=False, account=account)
        api_client.token_authenticate(owner)

        template = create_test_template(
            owner,
            is_active=True,
            is_public=False,
            tasks_count=1
        )
        task = template.tasks.first()
        mocker.patch(
            'pneumatic_backend.processes.api_v2.services.templates.'
            'integrations.TemplateIntegrationsService.template_updated'
        )

        # act
        response = api_client.put(
            path=f'/templates/{template.id}',
            data={
                'id': template.id,
                'is_active': True,
                'is_public': template.is_public,
                'description': '',
                'name': 'Name changed',
                'template_owners': [non_admin.id, owner.id],
                'finalizable': True,
                'kickoff': {
                    'id': template.kickoff_instance.id
                },
                'tasks': [
                    {
                        'id': task.id,
                        'api_name': task.api_name,
                        'number': task.number,
                        'name': task.name,
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

    def test_update__non_admin_in_template_owners_freemium__ok(
        self,
        mocker,
        api_client,
    ):

        # arrange
        account = create_test_account(plan=BillingPlanType.FREEMIUM)
        owner = create_test_user(
            email='owner@test.test',
            is_account_owner=True,
            account=account
        )
        non_admin = create_test_user(is_admin=False, account=account)
        api_client.token_authenticate(owner)

        template = create_test_template(
            owner,
            is_active=True,
            is_public=False,
            tasks_count=1
        )
        task = template.tasks.first()
        mocker.patch(
            'pneumatic_backend.processes.api_v2.services.templates.'
            'integrations.TemplateIntegrationsService.template_updated'
        )
        template_update_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.views.template.'
            'AnalyticService.templates_updated'
        )
        kickoff_update_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.views.template.'
            'AnalyticService.templates_kickoff_updated'
        )

        # act
        response = api_client.put(
            path=f'/templates/{template.id}',
            data={
                'id': template.id,
                'is_active': True,
                'is_public': template.is_public,
                'description': '',
                'name': 'Name changed',
                'template_owners': [non_admin.id, owner.id],
                'finalizable': True,
                'kickoff': {
                    'id': template.kickoff_instance.id
                },
                'tasks': [
                    {
                        'id': task.id,
                        'api_name': task.api_name,
                        'number': task.number,
                        'name': task.name,
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
        template_update_mock.assert_called_once()
        kickoff_update_mock.assert_called_once()

    def test_update__api_request__ok(
        self,
        api_client,
        mocker,
    ):

        # arrange
        user = create_test_user()
        template = create_test_template(
            user,
            is_active=True,
            is_public=False,
            tasks_count=1
        )
        task = template.tasks.first()

        account_service = AccountService(
            instance=user.account,
            user=user
        )
        account_service.update_active_templates()
        create_integrations_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.services.templates.'
            'integrations.TemplateIntegrationsService.'
            'create_integrations_for_template'
        )
        template_updated_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.services.templates.'
            'integrations.TemplateIntegrationsService.template_updated'
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
        template_update_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.views.template.'
            'AnalyticService.templates_updated'
        )
        kickoff_update_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.views.template.'
            'AnalyticService.templates_kickoff_updated'
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
        response = api_client.put(
            path=f'/templates/{template.id}',
            data={
                'id': template.id,
                'is_active': True,
                'is_public': template.is_public,
                'description': '',
                'name': 'Name changed',
                'template_owners': [user.id],
                'finalizable': True,
                'kickoff': {
                    'id': template.kickoff_instance.id
                },
                'tasks': [
                    {
                        'id': task.id,
                        'api_name': task.api_name,
                        'number': task.number,
                        'name': task.name,
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
        create_integrations_mock.assert_not_called()
        template_updated_mock.assert_called_once_with(template=template)
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
        template_update_mock.assert_called_once()
        kickoff_update_mock.assert_called_once()
