import pytest
from django.contrib.auth import get_user_model
from src.processes.tests.fixtures import (
    create_test_user
)
from src.processes.models import Kickoff
from src.processes.enums import (
    PerformerType,
    OwnerType
)
from src.authentication.enums import AuthTokenType

UserModel = get_user_model()
pytestmark = pytest.mark.django_db


class TestCreateKickoff:

    def test_create__only_required_fields__defaults_ok(
        self,
        mocker,
        api_client
    ):

        # arrange
        kickoff_create_mock = mocker.patch(
            'src.processes.views.template.'
            'AnalyticService.templates_kickoff_created'
        )
        user = create_test_user()
        api_client.token_authenticate(user)

        # act
        response = api_client.post(
            path='/templates',
            data={
                'name': 'Template',
                'owners': [
                    {
                        'type': OwnerType.USER,
                        'source_id': user.id
                    },
                ],
                'is_active': True,
                'kickoff': {
                    'fields': [],
                },
                'tasks': [
                    {
                        'number': 1,
                        'name': 'First step',
                        'raw_performers': [{
                            'type': PerformerType.USER,
                            'source_id': user.id
                        }]
                    }
                ]
            }
        )

        # assert
        assert response.status_code == 200
        response_data = response.json()['kickoff']

        assert response_data['fields'] == []

        kickoff = Kickoff.objects.get(template_id=response.json()['id'])
        assert kickoff.fields.count() == len(response_data['fields'])
        kickoff_create_mock.assert_called_once()

    def test_create__all_fields__ok(
        self,
        mocker,
        api_client,
    ):

        # arrange
        kickoff_create_mock = mocker.patch(
            'src.processes.views.template.'
            'AnalyticService.templates_kickoff_created'
        )
        user = create_test_user()
        api_client.token_authenticate(user)
        request_data = {
            'fields': []
        }

        # act
        response = api_client.post(
            path='/templates',
            data={
                'name': 'Template',
                'is_active': True,
                'owners': [
                    {
                        'type': OwnerType.USER,
                        'source_id': user.id
                    },
                ],
                'kickoff': request_data,
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
        response_data = response.json()['kickoff']

        assert response_data['fields'] == request_data['fields']

        kickoff = Kickoff.objects.get(template_id=response.json()['id'])
        assert kickoff.fields.count() == len(response_data['fields'])
        kickoff_create_mock.assert_called_once_with(
            user=user,
            template=kickoff.template,
            auth_type=AuthTokenType.USER,
            is_superuser=False,
        )

    def test_create__kickoff_not_provided__validation_error(
        self,
        mocker,
        api_client
    ):

        # arrange
        mocker.patch(
            'src.processes.views.template.'
            'AnalyticService.templates_kickoff_created'
        )
        user = create_test_user()
        api_client.token_authenticate(user)

        # act
        response = api_client.post(
            path='/templates',
            data={
                'name': 'Template',
                'is_active': True,
                'owners': [
                    {
                        'type': OwnerType.USER,
                        'source_id': user.id
                    },
                ],
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

    def test_create_draft__not_kickoff__ok(
        self,
        mocker,
        api_client
    ):

        # arrange
        kickoff_create_mock = mocker.patch(
            'src.processes.views.template.'
            'AnalyticService.templates_kickoff_created'
        )
        user = create_test_user()
        api_client.token_authenticate(user)

        # act
        response = api_client.post(
            path='/templates',
            data={
                'name': 'Template',
                'owners': [
                    {
                        'type': OwnerType.USER,
                        'source_id': user.id
                    },
                ],
                'is_active': False,
                'tasks': [
                    {
                        'number': 1,
                        'name': 'First step'
                    }
                ]
            }
        )

        # assert
        assert response.status_code == 200
        assert response.data['kickoff'] == {
            'fields': [],
        }
        assert response.data['is_active'] is False
        kickoff_create_mock.assert_called_once()

    def test_create_draft__kickoff_is_null__ok(
        self,
        mocker,
        api_client
    ):

        # arrange
        kickoff_create_mock = mocker.patch(
            'src.processes.views.template.'
            'AnalyticService.templates_kickoff_created'
        )
        user = create_test_user()
        api_client.token_authenticate(user)

        # act
        response = api_client.post(
            path='/templates',
            data={
                'name': 'Template',
                'owners': [
                    {
                        'type': OwnerType.USER,
                        'source_id': user.id
                    },
                ],
                'is_active': False,
                'kickoff': None,
                'tasks': [
                    {
                        'number': 1,
                        'name': 'First step'
                    }
                ]
            }
        )

        # assert
        assert response.status_code == 200
        assert response.data['kickoff'] == {
            'fields': [],
        }
        assert response.data['is_active'] is False
        kickoff_create_mock.assert_called_once()
