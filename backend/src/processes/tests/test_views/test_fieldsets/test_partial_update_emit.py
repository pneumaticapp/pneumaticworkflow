import pytest

from src.logs.events.enums import (
    ActorType,
    EventCategory,
    EventName,
    EventObjectType,
)
from src.logs.events.schema import Actor, EventObject
from src.processes.messages import fieldset as messages
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_fieldset_template,
    create_test_owner,
    create_test_shared_fieldset,
    create_test_template,
)
from src.utils.validation import ErrorCode

pytestmark = pytest.mark.django_db


def test_partial_update__name__emit_fieldset_update(
    api_client,
    fake_stream,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    fieldset = create_test_shared_fieldset(account=account, name='Contacts')
    api_client.token_authenticate(owner)

    # act
    response = api_client.patch(
        f'/fieldsets/{fieldset.id}',
        data={'name': 'Clients'},
    )

    # assert
    assert response.status_code == 200
    fieldset.refresh_from_db()
    assert fieldset.name == 'Clients'
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    assert event.type == EventName.FIELDSET_UPDATE
    assert event.category == EventCategory.AUDIT
    assert event.account_id == account.id
    assert event.actor == Actor(
        type=ActorType.USER,
        id=owner.id,
        email=owner.email,
    )
    assert event.object == EventObject(
        type=EventObjectType.FIELDSET,
        id=fieldset.id,
    )
    assert event.payload == {'name': 'Clients'}
    assert event.workflow_id is None
    assert event.task_id is None


def test_partial_update__fieldset_in_use__no_event(
    api_client,
    fake_stream,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    fieldset = create_test_shared_fieldset(account=account, name='Contacts')
    template = create_test_template(user=owner, tasks_count=1)
    create_test_fieldset_template(
        account=account,
        template=template,
        task=template.tasks.get(number=1),
        shared_fieldset=fieldset,
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.patch(
        f'/fieldsets/{fieldset.id}',
        data={'name': 'Clients'},
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == messages.MSG_FS_0009
    assert response.data['details'] == {}
    fieldset.refresh_from_db()
    assert fieldset.name == 'Contacts'
    assert fake_stream.events == []


def test_partial_update__invalid_layout__no_event(
    api_client,
    fake_stream,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    fieldset = create_test_shared_fieldset(account=account)
    api_client.token_authenticate(owner)

    # act
    response = api_client.patch(
        f'/fieldsets/{fieldset.id}',
        data={'layout': 'invalid_layout'},
    )

    # assert
    assert response.status_code == 400
    message = '"invalid_layout" is not a valid choice.'
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    assert response.data['details']['name'] == 'layout'
    assert response.data['details']['reason'] == message
    assert fake_stream.events == []
