import pytest

from src.generics.exceptions import BaseServiceException
from src.logs.events.enums import (
    ActorType,
    EventCategory,
    EventName,
    EventObjectType,
)
from src.logs.events.schema import Actor, EventObject
from src.processes.models.templates.fieldset import FieldsetTemplate
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_owner,
    create_test_shared_fieldset,
)
from src.utils.validation import ErrorCode

pytestmark = pytest.mark.django_db


def test_clone__shared_fieldset__emit_fieldset_clone(
    api_client,
    fake_stream,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    fieldset = create_test_shared_fieldset(account=account, name='Contacts')
    api_client.token_authenticate(owner)

    # act
    response = api_client.post(f'/fieldsets/{fieldset.id}/clone')

    # assert
    assert response.status_code == 201
    clone = FieldsetTemplate.objects.get(id=response.data['id'])
    assert clone.id != fieldset.id
    assert clone.name == 'Contacts - clone'
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    assert event.type == EventName.FIELDSET_CLONE
    assert event.category == EventCategory.ACTIVITY
    assert event.account_id == account.id
    assert event.actor == Actor(
        type=ActorType.USER,
        id=owner.id,
        email=owner.email,
    )
    assert event.object == EventObject(
        type=EventObjectType.FIELDSET,
        id=clone.id,
    )
    assert event.payload == {
        'name': 'Contacts - clone',
        'source_fieldset_id': fieldset.id,
    }
    assert event.workflow_id is None
    assert event.task_id is None


def test_clone__service_exception__no_event(
    mocker,
    api_client,
    fake_stream,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    fieldset = create_test_shared_fieldset(account=account)
    message = 'Service error occurred'
    get_clone_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.get_clone',
        side_effect=BaseServiceException(message=message),
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.post(f'/fieldsets/{fieldset.id}/clone')

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    assert response.data['details'] == {}
    assert fake_stream.events == []
    get_clone_mock.assert_called_once_with()
