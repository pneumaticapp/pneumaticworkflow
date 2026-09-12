import pytest

from src.authentication.enums import AuthTokenType
from src.logs.events.enums import (
    ActorType,
    EventCategory,
    EventName,
    EventObjectType,
)
from src.logs.events.schema import Actor, EventObject
from src.processes.enums import (
    OwnerRole,
    OwnerType,
    PerformerType,
)
from src.processes.models.templates.template import Template
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_owner,
)

pytestmark = pytest.mark.django_db


def test_create__published_template__emit_template_publish(
    mocker,
    api_client,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    api_client.token_authenticate(owner)
    templates_created_mock = mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_created',
    )
    kickoff_created_mock = mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_kickoff_created',
    )
    emit_mock = mocker.patch('src.logs.events.services.emit')

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
    emit_mock.assert_called_once_with(
        EventName.TEMPLATE_PUBLISH,
        account_id=account.id,
        actor=Actor(
            type=ActorType.USER,
            id=owner.id,
            email=owner.email,
        ),
        event_object=EventObject(
            type=EventObjectType.TEMPLATE,
            id=template.id,
        ),
        payload={
            'name': 'Onboarding',
            'version': template.version,
            'is_active': True,
        },
        workflow_id=None,
        task_id=None,
        request=mocker.ANY,
    )
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


def test_create__draft__emit_template_draft_save(
    mocker,
    api_client,
):

    """ The row of a new draft says "New template": the event has to
        carry the name the person typed, the one in the draft data. """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    api_client.token_authenticate(owner)
    templates_created_mock = mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_created',
    )
    kickoff_created_mock = mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_kickoff_created',
    )
    emit_mock = mocker.patch('src.logs.events.services.emit')

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
    emit_mock.assert_called_once_with(
        EventName.TEMPLATE_DRAFT_SAVE,
        account_id=account.id,
        actor=Actor(
            type=ActorType.USER,
            id=owner.id,
            email=owner.email,
        ),
        event_object=EventObject(
            type=EventObjectType.TEMPLATE,
            id=template.id,
        ),
        payload={
            'name': 'Draft template',
            'version': template.version,
            'is_active': False,
        },
        workflow_id=None,
        task_id=None,
        request=mocker.ANY,
    )
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


def test_create__published_template__event_keeps_request_context(
    mocker,
    api_client,
    fake_stream,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    api_client.token_authenticate(
        owner,
        user_agent='Chrome/141',
        user_ip='10.10.0.13',
    )
    templates_created_mock = mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_created',
    )
    kickoff_created_mock = mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_kickoff_created',
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
        HTTP_X_REQUEST_ID='audit-template-1',
    )

    # assert
    assert response.status_code == 200
    template = Template.objects.get(id=response.data['id'])
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
    }
    assert event.ip == '10.10.0.13'
    assert event.user_agent == 'Chrome/141'
    assert event.request_id == 'audit-template-1'
    assert event.pii == (
        'actor.email',
        'ip',
        'user_agent',
        'payload.name',
    )
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
