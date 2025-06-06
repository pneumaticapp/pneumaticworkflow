import pytest
from pneumatic_backend.processes.tests.fixtures import (
    create_test_user,
    create_test_account,
    create_test_group
)
from pneumatic_backend.accounts.enums import BillingPlanType
from pneumatic_backend.processes.models import (
    TemplateDraft,
    Template,
)
from pneumatic_backend.processes.enums import (
    PerformerType,
    OwnerType
)


pytestmark = pytest.mark.django_db


class TestCopyTemplate:

    @pytest.mark.parametrize('is_active', [True, False])
    def test_clone__ok(
        self,
        mocker,
        is_active,
        api_client
    ):

        # arrange
        user = create_test_user()
        api_client.token_authenticate(user)

        request_data = {
            'name': 'Template',
            'wf_name_template': 'Wf template name {{ date }}',
            'description': 'Desc',
            'is_active': is_active,
            'is_public': True,
            'finalizable': True,
            'owners': [
                {
                    'type': OwnerType.USER,
                    'source_id': user.id
                },
            ],
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

        response = api_client.post(
            path='/templates',
            data=request_data
        )
        response_1_data = response.json()
        template = Template.objects.get(id=response.data['id'])
        create_integrations_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.services.templates.'
            'integrations.TemplateIntegrationsService.'
            'create_integrations_for_template'
        )

        # act
        response = api_client.post(
            f'/templates/{template.id}/clone'
        )

        # assert
        assert response.status_code == 200
        response_2_data = response.json()
        assert response_2_data['name'] == request_data['name'] + ' - clone'
        assert response_2_data['wf_name_template'] == (
            'Wf template name {{ date }}'
        )
        assert response_2_data['description'] == request_data['description']
        assert response_2_data['is_active'] is False
        assert response_2_data['is_public'] is True
        assert response_2_data['public_url'] is not None
        assert response_2_data['finalizable'] == request_data['finalizable']
        assert (
            response_2_data['owners'][0]['source_id'] ==
            str(request_data['owners'][0]['source_id'])
        )
        assert (
            response_2_data['owners'][0]['type'] ==
            request_data['owners'][0]['type']
        )
        assert response_1_data['id'] != response_2_data['id']

        draft = TemplateDraft.objects.get(template_id=response_2_data['id'])
        assert draft.draft == response_2_data
        create_integrations_mock.assert_called_once_with(
            template=draft.template
        )

    def test_copy__api_names_equal_param_name__ok(
        self,
        mocker,
        api_client
    ):
        """ https://trello.com/c/NKD5YQr6 """
        # arrange
        user = create_test_user()
        data = {
            "name": "Outreach Campaign",
            "tasks": [
                {
                    "name": "Pre-qualification Research 🔬",
                    "fields": [],
                    "number": 1,
                    "description": "{{ name }}",
                    'raw_performers': [
                        {
                            'type': PerformerType.USER,
                            'source_id': user.id
                        }
                    ],
                    "require_completion_by_all": False
                },
            ],
            "kickoff": {
                "fields": [
                    {
                        "name": "Name",
                        "type": "string",
                        "order": 7,
                        "api_name": "name",
                        "description": "",
                        "is_required": False
                    },
                ],
                "description": ""
            },
            "is_active": False,
            "updated_by": None,
            "description": "",
            "finalizable": True,
            "template_owners": [user.id],
            "tasks_count": 7,
            "date_updated": "",
        }
        api_client.token_authenticate(user)

        response = api_client.post('/templates', data=data)
        template_id = response.data['id']

        # act
        response = api_client.post(f'/templates/{template_id}/clone')

        # assert
        data = response.data
        data['is_active'] = True
        template_id = data['id']
        mocker.patch(
            'pneumatic_backend.processes.api_v2.services.templates.'
            'integrations.TemplateIntegrationsService.template_updated'
        )

        response = api_client.put(
            f'/templates/{template_id}',
            data=data
        )

        assert response.status_code == 200

    @pytest.mark.parametrize('is_active', [True, False])
    def test_clone__embed__ok(self, is_active, api_client):

        # arrange
        account = create_test_account(plan=BillingPlanType.PREMIUM)
        user = create_test_user(account=account)
        api_client.token_authenticate(user)
        response = api_client.post(
            path='/templates',
            data={
                'name': 'Template',
                'description': 'Desc',
                'is_active': is_active,
                'is_embedded': True,
                'finalizable': True,
                'owners': [
                    {
                        'type': OwnerType.USER,
                        'source_id': user.id
                    },
                ],
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
        response = api_client.post(
            f'/templates/{response.data["id"]}/clone'
        )

        # assert
        assert response.data['is_active'] is False
        assert response.data['is_embedded'] is True
        assert response.data['embed_url'] is not None

    def test_clone__raw_performers_group__ok(
        self,
        mocker,
        api_client
    ):

        # arrange
        user = create_test_user()
        group = create_test_group(user.account, users=[user])
        api_client.token_authenticate(user)

        request_data = {
            'name': 'Template',
            'is_active': True,
            'owners': [
                {
                    'type': OwnerType.USER,
                    'source_id': user.id
                },
            ],
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
                    ]
                }
            ]
        }

        response = api_client.post(
            path='/templates',
            data=request_data
        )
        template = Template.objects.get(id=response.data['id'])
        mocker.patch(
            'pneumatic_backend.processes.api_v2.services.templates.'
            'integrations.TemplateIntegrationsService.'
            'create_integrations_for_template'
        )

        # act
        response = api_client.post(
            f'/templates/{template.id}/clone'
        )

        # assert
        assert response.status_code == 200
        raw_performers_data = response.json()['tasks'][0]['raw_performers']
        assert len(raw_performers_data) == 1
        assert raw_performers_data[0]['type'] == PerformerType.GROUP
        assert raw_performers_data[0]['source_id'] == str(group.id)
