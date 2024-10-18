import pytest
from django.utils import timezone
from pneumatic_backend.utils.validation import ErrorCode
from pneumatic_backend.authentication.enums import AuthTokenType
from pneumatic_backend.accounts.enums import BillingPlanType
from pneumatic_backend.processes.tests.fixtures import (
    create_test_user,
    create_test_template,
    create_invited_user,
    create_test_workflow, create_test_account,
)
from pneumatic_backend.processes.models import (
    Template,
)
from pneumatic_backend.processes.enums import (
    PerformerType,
    FieldType
)
from pneumatic_backend.processes.enums import TemplateType
from pneumatic_backend.accounts.messages import (
    MSG_A_0035
)


pytestmark = pytest.mark.django_db


class TestListTemplate:

    def test_list__ok(self, api_client):

        # arrange
        user = create_test_user()
        api_client.token_authenticate(user)
        response_1 = api_client.post(
            path='/templates',
            data={
                'name': 'Template 1',
                'is_active': True,
                'template_owners': [user.id],
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
        active_template = Template.objects.get(id=response_1.data['id'])

        wf_name_template = '{{date}} Template 1'
        response_2 = api_client.post(
            path='/templates',
            data={
                'name': 'Template 1',
                'wf_name_template': wf_name_template,
                'is_active': False,
                'template_owners': [user.id],
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
        draft_template = Template.objects.get(id=response_2.data['id'])

        # act
        response = api_client.get('/templates')

        # assert
        assert response.status_code == 200
        assert len(response.data) == 2

        assert response.data[0]['id'] == active_template.id
        assert response.data[0]['template_owners'][0] == user.id
        assert response.data[0]['tasks_count'] == 1
        assert response.data[0]['wf_name_template'] is None

        assert response.data[1]['id'] == draft_template.id
        assert response.data[1]['template_owners'][0] == user.id
        assert response.data[1]['tasks_count'] == 0
        assert response.data[1]['wf_name_template'] is None

    def test_list__wf_name_template__ok(self, api_client):

        # arrange
        user = create_test_user()
        api_client.token_authenticate(user)
        wf_name_template = '{{date}} Template 1'
        api_client.post(
            path='/templates',
            data={
                'name': 'Template 1',
                'wf_name_template': wf_name_template,
                'is_active': True,
                'template_owners': [user.id],
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

        # act
        response = api_client.get('/templates')

        # assert
        assert response.status_code == 200
        assert response.data[0]['wf_name_template'] == wf_name_template

    def test_list__template_owners__ok(self, api_client):

        # arrange
        account = create_test_account(plan=BillingPlanType.FREEMIUM)
        user = create_test_user(account=account)
        user2 = create_test_user(
            account=account,
            email='t@t.t'
        )
        api_client.token_authenticate(user2)
        create_test_template(
            user=user,
            tasks_count=1,
            is_active=True
        )
        create_test_template(
            user=user2,
            tasks_count=1,
            is_active=True
        )

        # act
        response = api_client.get('/templates')

        # assert
        assert response.status_code == 200
        assert len(response.data) == 2
        template_owners = set(response.data[0]['template_owners'])
        assert template_owners == {user.id, user2.id}
        template_owners2 = set(response.data[1]['template_owners'])
        assert template_owners2 == {user.id, user2.id}

    def test_list__subscription_expired__forbidden(self, api_client):

        # arrange
        account = create_test_account(plan=BillingPlanType.PREMIUM)
        user = create_test_user(account=account)
        account.plan_expiration = timezone.now()
        account.save()
        api_client.token_authenticate(user)
        create_test_template(user, is_active=True)
        create_test_template(user, is_active=True)

        # act
        response = api_client.get('/templates')

        # assert
        assert response.status_code == 403
        assert response.data['detail'] == MSG_A_0035

    def test_list_ordering_name(self, api_client):

        user = create_test_user()
        template_one = create_test_template(user)
        template_two = create_test_template(user)
        template_one.name = 'Aa1'
        template_one.save()
        template_two.name = 'Bb2'
        template_two.save()

        api_client.token_authenticate(user)
        response = api_client.get('/templates?ordering=name')

        assert response.status_code == 200

        assert response.data[0]['id'] == template_one.id
        assert response.data[1]['id'] == template_two.id

    def test_list_ordering_invert_name(self, api_client):

        # arrange
        user = create_test_user()
        template_one = create_test_template(user, name='Aa1')
        template_two = create_test_template(user, name='Bb2')
        api_client.token_authenticate(user)

        # act
        response = api_client.get('/templates?ordering=-name')

        # assert
        assert response.status_code == 200
        assert response.data[0]['id'] == template_two.id
        assert response.data[1]['id'] == template_one.id

    def test_list_invalid_ordering__validation_error(self, api_client):

        # arrange
        user = create_test_user()
        api_client.token_authenticate(user=user)
        create_test_template(user)

        # act
        response = api_client.get(
            path='/templates?ordering=DROP OWNED BY CURRENT_USER'
        )

        # assert
        assert response.status_code == 400
        assert response.data['code'] == (
            ErrorCode.VALIDATION_ERROR
        )

    def test_list_ordering_date(self, api_client):
        user = create_test_user()
        template_one = create_test_template(user)
        template_two = create_test_template(user)

        api_client.token_authenticate(user)
        response = api_client.get('/templates?ordering=date')

        assert response.status_code == 200

        assert response.data[0]['id'] == template_one.id
        assert response.data[1]['id'] == template_two.id
        assert template_two.date_created > template_one.date_created

    def test_list_ordering_invert_date(self, api_client):

        user = create_test_user()
        template_one = create_test_template(
            user=user,
            is_active=True
        )
        template_two = create_test_template(user)
        template_three = create_test_template(user)
        api_client.token_authenticate(user)

        response = api_client.get('/templates?ordering=-date')

        assert response.status_code == 200
        assert response.data[0]['id'] == template_one.id
        assert response.data[1]['id'] == template_three.id
        assert response.data[2]['id'] == template_two.id
        assert template_two.date_created > template_one.date_created
        assert template_three.date_created > template_two.date_created

    def test_list__performers_count__draft__ok(
        self,
        api_client,
    ):

        # arrange
        user = create_test_user()
        api_client.token_authenticate(user)
        invited = create_invited_user(user)

        response_post = api_client.post(
            path='/templates',
            data={
                'name': 'Template 1',
                'is_active': False,
                'template_owners': [user.id, invited.id],
                'kickoff': {
                    'fields': [
                        {
                            'order': 1,
                            'name': 'First step performer',
                            'type': FieldType.USER,
                            'is_required': True,
                            'api_name': 'user-field-1'
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
                            },
                            {
                                'type': PerformerType.USER,
                                'source_id': invited.id
                            }
                        ]
                    },
                    {
                        'number': 2,
                        'name': 'Second step',
                        'raw_performers': [
                            {
                                'type': PerformerType.USER,
                                'source_id': invited.id
                            },
                            {
                                'type': PerformerType.WORKFLOW_STARTER,
                                'source_id': None
                            },
                            {
                                'type': PerformerType.FIELD,
                                'source_id': 'user-field-1'
                            }
                        ]
                    }
                ]
            }
        )

        # act
        response = api_client.get('/templates')

        # assert
        assert response_post.status_code == 200
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]['performers_count'] == 0
        template = Template.objects.get(id=response_post.data['id'])
        assert template.performers_count == 0
        template_owners = response.data[0]['template_owners']
        assert len(template_owners) == 1
        assert template_owners[0] == user.id

    def test_list__performers_count__is_active__ok(self,  api_client):

        # arrange
        user = create_test_user()
        api_client.token_authenticate(user)
        invited = create_invited_user(user)

        response_post = api_client.post(
            path='/templates',
            data={
                'name': 'Template 1',
                'is_active': True,
                'template_owners': [user.id, invited.id],
                'kickoff': {
                    'fields': [
                        {
                            'order': 1,
                            'name': 'First step performer',
                            'type': FieldType.USER,
                            'is_required': True,
                            'api_name': 'user-field-1'
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
                            },
                            {
                                'type': PerformerType.USER,
                                'source_id': invited.id
                            }
                        ]
                    },
                    {
                        'number': 2,
                        'name': 'Second step',
                        'raw_performers': [
                            {
                                'type': PerformerType.USER,
                                'source_id': invited.id
                            },
                            {
                                'type': PerformerType.WORKFLOW_STARTER,
                                'source_id': None
                            },
                            {
                                'type': PerformerType.FIELD,
                                'source_id': 'user-field-1'
                            }
                        ]
                    }
                ]
            }
        )

        # act
        response = api_client.get('/templates')

        # assert
        assert response_post.status_code == 200
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]['performers_count'] == 2
        template = Template.objects.get(id=response_post.data['id'])
        assert template.performers_count == 2
        template_owners = response.data[0]['template_owners']
        assert len(template_owners) == 2
        assert {user.id, invited.id} == set(template_owners)

    def test_list__is_template_owner__ok(self, api_client):

        # arrange
        user = create_test_user(is_admin=False)
        another_user = create_test_user(email='another@pneumatic.app')
        template = create_test_template(
            user=user,
            is_active=True
        )
        create_test_template(
            user=user,
            is_active=False
        )
        create_test_template(
            user=another_user,
            is_active=True
        )
        api_client.token_authenticate(user)

        # act
        response = api_client.get(
            '/templates?is_active=true&is_template_owner=true',
        )

        # assert
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]['id'] == template.id

    def test_list__search(self, api_client):
        user = create_test_user()
        template = create_test_template(user)
        another_template = create_test_template(user)
        another_template.name = 'Not search name'
        another_template.save()
        search_text = template.name

        api_client.token_authenticate(user)
        response = api_client.get(f'/templates?search={search_text}')

        assert response.status_code == 200
        assert response.data[0]['id'] == template.id

    def test_list__search_by_taskname(self, api_client):
        user = create_test_user()
        template = create_test_template(user)
        another_template = create_test_template(user)
        another_template.tasks.update(name='Not search name')
        search_text = template.tasks.filter(number=1).first().name

        api_client.token_authenticate(user)
        response = api_client.get(f'/templates?search={search_text}')

        assert response.status_code == 200
        assert response.data[0]['id'] == template.id

    def test_list__search_by_performer__ok(self, api_client):
        user = create_test_user()
        invited = create_invited_user(user)
        template = create_test_template(user)
        create_test_template(invited)
        search_text = user.email

        api_client.token_authenticate(user)
        response = api_client.get(f'/templates?search={search_text}')

        assert response.status_code == 200
        assert response.data[0]['id'] == template.id

    def test_list__track_analytics(self, api_client, mocker):

        # arrange
        user = create_test_user()
        create_test_template(user)
        search_text = 'some text'

        analytics_mock = mocker.patch(
            'pneumatic_backend.analytics.services.AnalyticService.'
            'search_search'
        )
        api_client.token_authenticate(user)

        # act
        response = api_client.get(f'/templates?search={search_text}')

        # assert
        assert response.status_code == 200
        analytics_mock.assert_called_once_with(
            user_id=user.id,
            page='templates',
            search_text=search_text,
            is_superuser=False,
            auth_type=AuthTokenType.USER,
        )

    def test_list__ordering_usage(self, api_client):

        # arrange
        user = create_test_user()

        template_one = create_test_template(user)
        create_test_workflow(user, template=template_one)
        create_test_workflow(user, template=template_one)
        template_two = create_test_template(user)
        template_three = create_test_template(user)
        create_test_workflow(user, template=template_three)
        create_test_workflow(user, template=template_three)
        create_test_workflow(user, template=template_three)

        api_client.token_authenticate(user=user)

        # act
        response = api_client.get('/templates?ordering=-usage')

        # assert
        assert response.status_code == 200

        assert response.data[0]['id'] == template_three.id
        assert response.data[1]['id'] == template_one.id
        assert response.data[2]['id'] == template_two.id

    def test_list__filter_is_not_public__ok(
        self,
        api_client
    ):

        # arrange
        user = create_test_user()
        api_client.token_authenticate(user)
        template = create_test_template(
            user=user,
            is_active=True,
            is_public=False
        )
        create_test_template(
            user=user,
            is_active=True,
            is_public=True
        )

        # act
        response = api_client.get(f'/templates?is_public=false')

        # assert
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]['id'] == template.id
        assert response.data[0]['is_public'] is False

    def test_list__filter_is_public_is_embedded__ok(
        self,
        api_client
    ):

        # arrange
        account = create_test_account(plan=BillingPlanType.PREMIUM)
        user = create_test_user(account=account)
        api_client.token_authenticate(user)
        template = create_test_template(
            user=user,
            is_active=True,
            is_embedded=True,
            is_public=True
        )
        create_test_template(
            user=user,
            is_active=True,
            is_public=False
        )

        # act
        response = api_client.get(f'/templates?is_public=true')

        # assert
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]['id'] == template.id
        assert response.data[0]['is_public'] is True
        assert response.data[0]['is_embedded'] is True

    def test_list__default_filter_is_public__ok(self, api_client):

        # arrange
        user = create_test_user()
        api_client.token_authenticate(user)
        create_test_template(
            user=user,
            is_active=True,
            is_public=True
        )
        create_test_template(
            user=user,
            is_active=True,
            is_public=False
        )

        # act
        response = api_client.get('/templates')

        # assert
        assert response.status_code == 200
        assert len(response.data) == 2

    def test_list__invalid_filter_is_public__validation_error(
        self,
        api_client
    ):
        # arrange
        user = create_test_user()
        api_client.token_authenticate(user)
        create_test_template(
            user=user,
            is_active=True,
            is_public=True
        )

        # act
        response = api_client.get(
            path='/templates?is_public=DROP OWNED BY CURRENT_USER'
        )

        # assert
        assert response.status_code == 400
        assert response.data['code'] == (
            ErrorCode.VALIDATION_ERROR
        )

    def test_list__user_is_performer_in_draft__empty_list(
        self,
        mocker,
        api_client
    ):

        # arrange
        user = create_test_user()
        api_client.token_authenticate(user)
        admin_user = create_test_user(
            account=user.account,
            email='admin@test.test',
            is_account_owner=False
        )
        user.account.billing_plan = BillingPlanType.PREMIUM
        user.account.save()
        request_data_1 = {
            'name': 'Template 1',
            'is_active': True,
            'template_owners': [user.id],
            'kickoff': {},
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
                },
                {
                    'number': 2,
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
        request_data_2 = {
            'is_active': True,
            'name': 'Template 2',
            'template_owners': [user.id],
            'kickoff': {},
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
                },
                {
                    'number': 2,
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

        response = api_client.post(
            path=f'/templates',
            data=request_data_1
        )
        template_1_id = response.data['id']
        response.data['is_active'] = False
        response.data['tasks'][0]['raw_performers'].append({
            'type': PerformerType.USER,
            'source_id': admin_user.id
        })
        mocker.patch(
            'pneumatic_backend.processes.api_v2.services.templates.'
            'integrations.TemplateIntegrationsService.template_updated'
        )
        api_client.put(
            path=f'/templates/{template_1_id}',
            data=response.data
        )
        response = api_client.post(
            path=f'/templates',
            data=request_data_2
        )
        template_2_id = response.data['id']
        response.data['is_active'] = False
        response.data['tasks'][1]['raw_performers'] = [{
            'type': PerformerType.USER,
            'source_id': admin_user.id
        }]
        api_client.put(
            path=f'/templates/{template_2_id}',
            data=response.data
        )
        api_client.token_authenticate(admin_user)

        # act
        response = api_client.get('/templates')

        # assert
        assert response.status_code == 200
        assert len(response.data) == 0

    def test_list__exclude_onboarding__ok(self, api_client):

        # arrange
        user = create_test_user()
        api_client.token_authenticate(user)
        create_test_template(
            user,
            type_=TemplateType.ONBOARDING_NON_ADMIN
        )
        create_test_template(
            user,
            type_=TemplateType.ONBOARDING_ADMIN
        )
        create_test_template(
            user,
            type_=TemplateType.ONBOARDING_ACCOUNT_OWNER
        )

        # act
        response = api_client.get('/templates')

        # assert
        assert response.status_code == 200
        assert len(response.data) == 0

    def test_list__pagination__ok(self, api_client):

        # arrange
        user = create_test_user()
        api_client.token_authenticate(user)
        create_test_template(user, is_active=True)
        create_test_template(user, is_active=True)
        template = create_test_template(user, is_active=True)
        create_test_template(user, is_active=True)

        # act
        response = api_client.get(
            path='/templates',
            data={
                'limit': 1,
                'offset': 2,
                'ordering': 'date'
            }
        )

        # assert
        assert response.status_code == 200
        assert response.data['count'] == 4
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['id'] == template.id
