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
    create_test_template,
)

pytestmark = pytest.mark.django_db


def test_update__published_template__emit_template_publish(
    mocker,
    api_client,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    template = create_test_template(
        user=owner,
        is_active=True,
        tasks_count=1,
    )
    task = template.tasks.get(number=1)
    api_client.token_authenticate(owner)
    update_workflows_mock = mocker.patch(
        'src.processes.views.template.update_workflows.delay',
    )
    template_updated_mock = mocker.patch(
        'src.processes.services.templates.integrations'
        '.TemplateIntegrationsService.template_updated',
    )
    templates_updated_mock = mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_updated',
    )
    kickoff_updated_mock = mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_kickoff_updated',
    )
    emit_mock = mocker.patch('src.logs.events.services.emit')

    # act
    response = api_client.put(
        path=f'/templates/{template.id}',
        data={
            'id': template.id,
            'name': 'Onboarding changed',
            'is_active': True,
            'owners': [
                {
                    'type': OwnerType.USER,
                    'source_id': owner.id,
                    'role': OwnerRole.OWNER,
                },
            ],
            'kickoff': {
                'id': template.kickoff_instance.id,
                'fields': [],
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
                            'source_id': owner.id,
                        },
                    ],
                },
            ],
        },
    )

    # assert
    assert response.status_code == 200
    template.refresh_from_db()
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
            'name': 'Onboarding changed',
            'version': template.version,
            'is_active': True,
        },
        request=mocker.ANY,
    )
    update_workflows_mock.assert_called_once_with(
        template_id=template.id,
        version=template.version,
        updated_by=owner.id,
        auth_type=AuthTokenType.USER,
        is_superuser=False,
    )
    template_updated_mock.assert_called_once_with(template=template)
    templates_updated_mock.assert_called_once_with(
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
    kickoff_updated_mock.assert_called_once_with(
        user=owner,
        template=template,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )


def test_update__draft__emit_template_draft_save_with_draft_name(
    mocker,
    api_client,
):

    """ A draft save of an existing template writes only is_active
        to the template row, the edited name stays in the draft. The
        event names what the person saved, not the last published
        name of the row. """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    template = create_test_template(
        user=owner,
        name='Published name',
        is_active=True,
        tasks_count=1,
    )
    api_client.token_authenticate(owner)
    update_workflows_mock = mocker.patch(
        'src.processes.views.template.update_workflows.delay',
    )
    template_updated_mock = mocker.patch(
        'src.processes.services.templates.integrations'
        '.TemplateIntegrationsService.template_updated',
    )
    emit_mock = mocker.patch('src.logs.events.services.emit')

    # act
    response = api_client.put(
        path=f'/templates/{template.id}',
        data={
            'id': template.id,
            'name': 'Draft again',
            'is_active': False,
            'kickoff': {
                'id': template.kickoff_instance.id,
                'fields': [],
            },
            'tasks': [],
        },
    )

    # assert
    assert response.status_code == 200
    template.refresh_from_db()
    assert template.name == 'Published name'
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
            'name': 'Draft again',
            'version': template.version,
            'is_active': False,
        },
        request=mocker.ANY,
    )
    update_workflows_mock.assert_not_called()
    template_updated_mock.assert_called_once_with(template=template)


def test_update__draft__event_keeps_request_context(
    mocker,
    api_client,
    events_enabled,
    run_on_commit,
    fake_stream,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    template = create_test_template(
        user=owner,
        name='Published name',
        is_active=True,
        tasks_count=1,
    )
    api_client.token_authenticate(
        owner,
        user_agent='Chrome/141',
        user_ip='10.10.0.14',
    )
    update_workflows_mock = mocker.patch(
        'src.processes.views.template.update_workflows.delay',
    )
    template_updated_mock = mocker.patch(
        'src.processes.services.templates.integrations'
        '.TemplateIntegrationsService.template_updated',
    )

    # act
    response = api_client.put(
        path=f'/templates/{template.id}',
        data={
            'id': template.id,
            'name': 'Draft again',
            'is_active': False,
            'kickoff': {
                'id': template.kickoff_instance.id,
                'fields': [],
            },
            'tasks': [],
        },
        HTTP_X_REQUEST_ID='audit-template-2',
    )

    # assert
    assert response.status_code == 200
    saved = Template.objects.get(id=template.id)
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
        id=saved.id,
    )
    assert event.payload == {
        'name': 'Draft again',
        'version': saved.version,
        'is_active': False,
    }
    assert event.ip == '10.10.0.14'
    assert event.user_agent == 'Chrome/141'
    assert event.request_id == 'audit-template-2'
    update_workflows_mock.assert_not_called()
    template_updated_mock.assert_called_once_with(template=saved)
