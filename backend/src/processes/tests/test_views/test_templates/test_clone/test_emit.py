import pytest

from src.accounts.enums import UserType
from src.authentication.enums import AuthTokenType
from src.logs.events.enums import (
    EventObjectType,
    TemplateEvents,
)
from src.logs.events.schema import Actor, EventObject
from src.processes.models.templates.template import Template
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_owner,
    create_test_template,
)

pytestmark = pytest.mark.django_db


def test_clone__template__emit_template_clone(
    mocker,
    api_client,
):

    """ The event is about the copy, not the original: the object is
        the new draft and the name is the one the draft got. """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    template = create_test_template(
        user=owner,
        name='Onboarding',
        is_active=True,
        tasks_count=1,
    )
    api_client.token_authenticate(owner)
    create_integrations_mock = mocker.patch(
        'src.processes.services.templates.integrations.'
        'TemplateIntegrationsService.create_integrations_for_template',
    )
    emit_mock = mocker.patch('src.logs.events.services.emit')

    # act
    response = api_client.post(f'/templates/{template.id}/clone')

    # assert
    assert response.status_code == 200
    clone = Template.objects.get(id=response.data['id'])
    assert clone.id != template.id
    emit_mock.assert_called_once_with(
        TemplateEvents.CLONE,
        account_id=account.id,
        actor=Actor(
            id=owner.id,
            email=owner.email,
            user_type=UserType.USER,
        ),
        auth_type=AuthTokenType.USER,
        event_object=EventObject(
            type=EventObjectType.TEMPLATE,
            id=clone.id,
        ),
        payload={
            'name': 'Onboarding - clone',
            'version': clone.version,
            'is_active': False,
        },
        workflow_id=None,
        task_id=None,
    )
    create_integrations_mock.assert_called_once_with(template=clone)


def test_clone__template__event_keeps_request_context(
    mocker,
    api_client,
    fake_stream,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    template = create_test_template(
        user=owner,
        name='Onboarding',
        is_active=True,
        tasks_count=1,
    )
    api_client.token_authenticate(
        owner,
        user_agent='Chrome/141',
        user_ip='10.10.0.17',
    )
    create_integrations_mock = mocker.patch(
        'src.processes.services.templates.integrations.'
        'TemplateIntegrationsService.create_integrations_for_template',
    )

    # act
    response = api_client.post(
        f'/templates/{template.id}/clone',
        HTTP_X_REQUEST_ID='audit-template-5',
    )

    # assert
    assert response.status_code == 200
    clone = Template.objects.get(id=response.data['id'])
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    assert event.type == TemplateEvents.CLONE
    assert event.category == TemplateEvents.CATEGORY
    assert event.account_id == account.id
    assert event.actor == Actor(
        id=owner.id,
        email=owner.email,
        user_type=UserType.USER,
    )
    assert event.auth_type == AuthTokenType.USER
    assert event.object == EventObject(
        type=EventObjectType.TEMPLATE,
        id=clone.id,
    )
    assert event.payload == {
        'name': 'Onboarding - clone',
        'version': clone.version,
        'is_active': False,
    }
    assert event.ip == '10.10.0.17'
    assert event.user_agent == 'Chrome/141'
    assert event.request_id == 'audit-template-5'
    create_integrations_mock.assert_called_once_with(template=clone)


def test_clone__template_of_another_account__no_event(
    mocker,
    api_client,
    fake_stream,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    template = create_test_template(
        user=owner,
        is_active=True,
        tasks_count=1,
    )
    another_account = create_test_account(name='Another Company')
    another_owner = create_test_owner(
        account=another_account,
        email='another_owner@pneumatic.app',
    )
    api_client.token_authenticate(another_owner)
    create_integrations_mock = mocker.patch(
        'src.processes.services.templates.integrations.'
        'TemplateIntegrationsService.create_integrations_for_template',
    )

    # act
    response = api_client.post(f'/templates/{template.id}/clone')

    # assert
    assert response.status_code == 404
    assert Template.objects.count() == 1
    assert fake_stream.events == []
    create_integrations_mock.assert_not_called()
