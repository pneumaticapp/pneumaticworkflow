import pytest

from src.logs.events.enums import (
    ActorType,
    EventCategory,
    EventName,
    EventObjectType,
)
from src.logs.events.schema import Actor, EventObject
from src.processes.models.templates.template import Template
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_not_admin,
    create_test_owner,
    create_test_template,
)

pytestmark = pytest.mark.django_db


def test_discard_changes__template_with_tasks__emit_draft_discard(
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
        user_ip='10.10.0.21',
    )

    # act
    response = api_client.post(
        f'/templates/{template.id}/discard-changes',
        HTTP_X_REQUEST_ID='audit-template-21',
    )

    # assert
    assert response.status_code == 204
    template.refresh_from_db()
    assert template.is_deleted is False
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    assert event.type == EventName.TEMPLATE_DRAFT_DISCARD
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
        'name': 'Onboarding',
        'version': template.version,
        'is_active': True,
        'template_deleted': False,
    }
    assert event.ip == '10.10.0.21'
    assert event.user_agent == 'Chrome/141'
    assert event.request_id == 'audit-template-21'


def test_discard_changes__template_without_tasks__emit_template_deleted(
    api_client,
    fake_stream,
):

    """ A template with no tasks was never published: discarding its
        draft deletes the template, and the event has to say so. """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    template = create_test_template(
        user=owner,
        name='Onboarding draft',
        is_active=False,
        tasks_count=0,
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.post(f'/templates/{template.id}/discard-changes')

    # assert
    assert response.status_code == 204
    assert not Template.objects.filter(id=template.id).exists()
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    assert event.type == EventName.TEMPLATE_DRAFT_DISCARD
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
        'name': 'Onboarding draft',
        'version': template.version,
        'is_active': False,
        'template_deleted': True,
    }


def test_discard_changes__not_admin__no_event(
    api_client,
    fake_stream,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    not_admin = create_test_not_admin(account=account)
    template = create_test_template(
        user=owner,
        is_active=True,
        tasks_count=1,
    )
    api_client.token_authenticate(not_admin)

    # act
    response = api_client.post(f'/templates/{template.id}/discard-changes')

    # assert
    assert response.status_code == 403
    assert fake_stream.events == []
