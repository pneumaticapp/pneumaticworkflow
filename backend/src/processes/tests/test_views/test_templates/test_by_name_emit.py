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
    create_test_system_template,
)
from src.utils.validation import ErrorCode

pytestmark = pytest.mark.django_db


def test_by_name__library_template__emit_template_publish(
    mocker,
    api_client,
    fake_stream,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    system_template = create_test_system_template(
        name='Onboarding',
        template={
            'name': 'Onboarding',
            'kickoff': {},
            'tasks': [
                {
                    'number': 1,
                    'name': 'First step',
                },
            ],
        },
    )
    api_client.token_authenticate(
        owner,
        user_agent='Chrome/141',
        user_ip='10.10.0.24',
    )
    create_integrations_for_template_mock = mocker.patch(
        'src.processes.services.templates.integrations.'
        'TemplateIntegrationsService.create_integrations_for_template',
    )
    template_created_from_landing_mock = mocker.patch(
        'src.processes.services.templates.template.'
        'AnalyticService.template_created_from_landing_library',
    )

    # act
    response = api_client.post(
        path='/templates/by-name',
        data={'name': system_template.name},
        HTTP_X_REQUEST_ID='audit-template-24',
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
        'source': TemplateSource.LIBRARY,
    }
    assert event.ip == '10.10.0.24'
    assert event.user_agent == 'Chrome/141'
    assert event.request_id == 'audit-template-24'
    create_integrations_for_template_mock.assert_called_once_with(
        template=template,
    )
    template_created_from_landing_mock.assert_called_once_with(
        user=owner,
        template=template,
        auth_type=AuthTokenType.USER,
        is_superuser=False,
    )


def test_by_name__invalid_library_template__emit_template_draft_save(
    mocker,
    api_client,
    fake_stream,
):

    """ A library template that does not pass validation is saved as
        a draft: the event follows the state the template ended up in,
        and still names the library as its source. """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    system_template = create_test_system_template(
        name='Broken library template',
        template={
            'name': 'Broken library template',
            'kickoff': {},
            'tasks': [],
        },
    )
    api_client.token_authenticate(owner)
    create_integrations_for_template_mock = mocker.patch(
        'src.processes.services.templates.integrations.'
        'TemplateIntegrationsService.create_integrations_for_template',
    )
    template_created_from_landing_mock = mocker.patch(
        'src.processes.services.templates.template.'
        'AnalyticService.template_created_from_landing_library',
    )

    # act
    response = api_client.post(
        path='/templates/by-name',
        data={'name': system_template.name},
    )

    # assert
    assert response.status_code == 200
    template = Template.objects.get(id=response.data['id'])
    assert template.is_active is False
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    assert event.type == EventName.TEMPLATE_DRAFT_SAVE
    assert event.category == EventCategory.ACTIVITY
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
        'name': 'Broken library template',
        'version': template.version,
        'is_active': False,
        'source': TemplateSource.LIBRARY,
    }
    create_integrations_for_template_mock.assert_called_once_with(
        template=template,
    )
    template_created_from_landing_mock.assert_called_once_with(
        user=owner,
        template=template,
        auth_type=AuthTokenType.USER,
        is_superuser=False,
    )


def test_by_name__service_exception__no_event(
    mocker,
    api_client,
    fake_stream,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    system_template = create_test_system_template(name='Onboarding')
    template_service_init_mock = mocker.patch.object(
        TemplateService,
        attribute='__init__',
        return_value=None,
    )
    error_message = 'some message'
    create_template_from_library_mock = mocker.patch(
        'src.processes.services.templates.'
        'template.TemplateService.create_template_from_library_template',
        side_effect=TemplateServiceException(message=error_message),
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.post(
        path='/templates/by-name',
        data={'name': system_template.name},
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
    create_template_from_library_mock.assert_called_once_with(
        system_template=system_template,
    )


def test_by_name__name_blank__no_event(
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
    create_template_from_library_mock = mocker.patch(
        'src.processes.services.templates.'
        'template.TemplateService.create_template_from_library_template',
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.post(
        path='/templates/by-name',
        data={'name': ''},
    )

    # assert
    assert response.status_code == 400
    message = 'This field may not be blank.'
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    assert response.data['details']['name'] == 'name'
    assert response.data['details']['reason'] == message
    assert fake_stream.events == []
    template_service_init_mock.assert_not_called()
    create_template_from_library_mock.assert_not_called()
