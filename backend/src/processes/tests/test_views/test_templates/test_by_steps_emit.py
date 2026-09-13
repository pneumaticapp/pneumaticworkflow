import pytest

from src.authentication.enums import AuthTokenType
from src.logs.events.enums import (
    ActorType,
    EventCategory,
    EventName,
    EventObjectType,
    TemplateSource,
)
from src.logs.events.schema import Actor, EventObject
from src.processes.models.templates.template import Template
from src.processes.services.exceptions import TemplateServiceException
from src.processes.services.templates.template import TemplateService
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_owner,
)
from src.utils.validation import ErrorCode

pytestmark = pytest.mark.django_db


def test_by_steps__template_created__emit_template_publish(
    mocker,
    api_client,
    fake_stream,
):

    """ The real service runs: it publishes the template it creates,
        so the type is template.publish and not a draft save. """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    api_client.token_authenticate(
        owner,
        user_agent='Chrome/141',
        user_ip='10.10.0.23',
    )
    create_integrations_for_template_mock = mocker.patch(
        'src.processes.services.templates.integrations.'
        'TemplateIntegrationsService.create_integrations_for_template',
    )
    template_generated_from_landing_mock = mocker.patch(
        'src.processes.services.templates.template.'
        'AnalyticService.template_generated_from_landing',
    )

    # act
    response = api_client.post(
        path='/templates/by-steps',
        data={
            'name': 'Onboarding',
            'tasks': [
                {
                    'number': 1,
                    'name': 'First step',
                    'description': 'Meet the newcomer',
                },
            ],
        },
        HTTP_X_REQUEST_ID='audit-template-23',
    )

    # assert
    assert response.status_code == 200
    template = Template.objects.get(id=response.data['id'])
    assert template.is_active is True
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    assert event.type == EventName.TEMPLATE_PUBLISH
    assert event.category == EventCategory.AUDIT
    assert event.account_id == account.id
    assert event.actor == Actor(
        type=ActorType.USER,
        id=owner.id,
        email=owner.email,
    )
    assert event.object == EventObject(
        type=EventObjectType.TEMPLATE,
        id=template.id,
    )
    assert event.payload == {
        'name': 'Onboarding',
        'version': template.version,
        'is_active': True,
        'source': TemplateSource.BY_STEPS,
    }
    assert event.ip == '10.10.0.23'
    assert event.user_agent == 'Chrome/141'
    assert event.request_id == 'audit-template-23'
    create_integrations_for_template_mock.assert_called_once_with(
        template=template,
    )
    template_generated_from_landing_mock.assert_called_once_with(
        template=template,
        user=owner,
        auth_type=AuthTokenType.USER,
        is_superuser=False,
    )


def test_by_steps__service_exception__no_event(
    mocker,
    api_client,
    fake_stream,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    name = 'Onboarding'
    tasks = [
        {
            'number': 1,
            'name': 'First step',
            'description': 'Meet the newcomer',
        },
    ]
    template_service_init_mock = mocker.patch.object(
        TemplateService,
        attribute='__init__',
        return_value=None,
    )
    error_message = 'some message'
    create_template_by_steps_mock = mocker.patch(
        'src.processes.services.templates.'
        'template.TemplateService.create_template_by_steps',
        side_effect=TemplateServiceException(message=error_message),
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.post(
        path='/templates/by-steps',
        data={
            'name': name,
            'tasks': tasks,
        },
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == error_message
    assert response.data['details'] == {}
    assert fake_stream.events == []
    template_service_init_mock.assert_called_once_with(
        user=owner,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    create_template_by_steps_mock.assert_called_once_with(
        name=name,
        tasks=tasks,
    )


def test_by_steps__name_null__no_event(
    mocker,
    api_client,
    fake_stream,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    template_service_init_mock = mocker.patch.object(
        TemplateService,
        attribute='__init__',
        return_value=None,
    )
    create_template_by_steps_mock = mocker.patch(
        'src.processes.services.templates.'
        'template.TemplateService.create_template_by_steps',
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.post(
        path='/templates/by-steps',
        data={
            'name': None,
            'tasks': [
                {
                    'number': 1,
                    'name': 'First step',
                    'description': 'Meet the newcomer',
                },
            ],
        },
    )

    # assert
    assert response.status_code == 400
    message = 'This field may not be null.'
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    assert response.data['details']['name'] == 'name'
    assert response.data['details']['reason'] == message
    assert fake_stream.events == []
    template_service_init_mock.assert_not_called()
    create_template_by_steps_mock.assert_not_called()
