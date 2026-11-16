import pytest

from src.authentication.enums import AuthTokenType
from src.processes.enums import (
    OwnerRole,
    OwnerType,
    PerformerType,
)
from src.processes.models.templates.template import Template
from src.processes.tests.fixtures import create_test_owner
from src.utils.validation import ErrorCode

pytestmark = pytest.mark.django_db


def test_create__active_template__audit_template_created(
    mocker,
    api_client,
):

    # arrange
    owner = create_test_owner()
    api_client.token_authenticate(owner)
    templates_created_mock = mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_created',
    )
    kickoff_created_mock = mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_kickoff_created',
    )
    template_created_mock = mocker.patch(
        'src.processes.views.template.AuditEventService.template_created',
    )

    # act
    response = api_client.post(
        path='/templates',
        data={
            'name': 'Onboarding',
            'is_active': True,
            'owners': [
                {
                    'type': OwnerType.USER,
                    'source_id': owner.id,
                    'role': OwnerRole.OWNER,
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
                            'source_id': owner.id,
                        },
                    ],
                },
            ],
        },
    )

    # assert
    assert response.status_code == 200
    template = Template.objects.get(id=response.data['id'])
    templates_created_mock.assert_called_once_with(
        user=owner,
        template=template,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        kickoff_fields_count=0,
        tasks_count=1,
        tasks_fields_count=0,
        delays_count=0,
        due_in_count=0,
        conditions_count=0,
    )
    kickoff_created_mock.assert_called_once_with(
        user=owner,
        template=template,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    template_created_mock.assert_called_once_with(
        user=owner,
        auth_type=AuthTokenType.USER,
        template=template,
    )


def test_create__draft__audit_template_created(
    mocker,
    api_client,
):

    # arrange
    owner = create_test_owner()
    api_client.token_authenticate(owner)
    templates_created_mock = mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_created',
    )
    kickoff_created_mock = mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_kickoff_created',
    )
    template_created_mock = mocker.patch(
        'src.processes.views.template.AuditEventService.template_created',
    )

    # act
    response = api_client.post(
        path='/templates',
        data={
            'name': 'Draft template',
            'is_active': False,
            'kickoff': {},
            'tasks': [],
        },
    )

    # assert
    assert response.status_code == 200
    template = Template.objects.get(id=response.data['id'])
    templates_created_mock.assert_called_once_with(
        user=owner,
        template=template,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        kickoff_fields_count=0,
        tasks_count=0,
        tasks_fields_count=0,
        delays_count=0,
        due_in_count=0,
        conditions_count=0,
    )
    kickoff_created_mock.assert_called_once_with(
        user=owner,
        template=template,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    template_created_mock.assert_called_once_with(
        user=owner,
        auth_type=AuthTokenType.USER,
        template=template,
    )


def test_create__name_null__audit_not_called(
    mocker,
    api_client,
):

    # arrange
    owner = create_test_owner()
    api_client.token_authenticate(owner)
    templates_created_mock = mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_created',
    )
    kickoff_created_mock = mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_kickoff_created',
    )
    template_created_mock = mocker.patch(
        'src.processes.views.template.AuditEventService.template_created',
    )

    # act
    response = api_client.post(
        path='/templates',
        data={
            'name': None,
            'is_active': True,
            'kickoff': {},
            'tasks': [],
        },
    )

    # assert
    assert response.status_code == 400
    message = 'This field may not be null.'
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    assert response.data['details']['name'] == 'name'
    assert response.data['details']['reason'] == message
    assert Template.objects.count() == 0
    templates_created_mock.assert_not_called()
    kickoff_created_mock.assert_not_called()
    template_created_mock.assert_not_called()
