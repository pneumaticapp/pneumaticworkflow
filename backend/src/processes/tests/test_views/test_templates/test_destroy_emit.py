import pytest

from src.authentication.enums import AuthTokenType
from src.logs.events.enums import (
    ActorType,
    EventCategory,
    EventName,
    EventObjectType,
)
from src.logs.events.schema import Actor, EventObject
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_owner,
    create_test_template,
)

pytestmark = pytest.mark.django_db


def test_destroy__template__emit_template_delete(
    mocker,
    api_client,
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
    api_client.token_authenticate(owner)
    templates_deleted_mock = mocker.patch(
        'src.analysis.services.AnalyticService.templates_deleted',
    )
    emit_mock = mocker.patch('src.logs.events.services.emit')

    # act
    response = api_client.delete(f'/templates/{template.id}')

    # assert
    assert response.status_code == 204
    emit_mock.assert_called_once_with(
        EventName.TEMPLATE_DELETE,
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
    templates_deleted_mock.assert_called_once_with(
        user=owner,
        template=template,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )


def test_destroy__template__event_keeps_request_context(
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
        user_ip='10.10.0.15',
    )
    templates_deleted_mock = mocker.patch(
        'src.analysis.services.AnalyticService.templates_deleted',
    )

    # act
    response = api_client.delete(
        f'/templates/{template.id}',
        HTTP_X_REQUEST_ID='audit-template-3',
    )

    # assert
    assert response.status_code == 204
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    assert event.type == EventName.TEMPLATE_DELETE
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
    assert event.ip == '10.10.0.15'
    assert event.user_agent == 'Chrome/141'
    assert event.request_id == 'audit-template-3'
    templates_deleted_mock.assert_called_once_with(
        user=owner,
        template=template,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
