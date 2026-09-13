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
)
from src.utils.validation import ErrorCode

pytestmark = pytest.mark.django_db


def test_create__shared_fieldset__emit_fieldset_create(
    api_client,
    fake_stream,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    api_client.token_authenticate(owner)

    # act
    response = api_client.post('/fieldsets', data={'name': 'Contacts'})

    # assert
    assert response.status_code == 201
    fieldset = FieldsetTemplate.objects.get(id=response.data['id'])
    assert fieldset.name == 'Contacts'
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    assert event.type == EventName.FIELDSET_CREATE
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
    assert event.payload == {'name': 'Contacts'}
    assert event.workflow_id is None
    assert event.task_id is None


def test_create__blank_name__no_event(
    api_client,
    fake_stream,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    api_client.token_authenticate(owner)

    # act
    response = api_client.post('/fieldsets', data={})

    # assert
    assert response.status_code == 400
    message = 'This field is required.'
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    assert response.data['details']['name'] == 'name'
    assert response.data['details']['reason'] == message
    assert fake_stream.events == []


def test_create__service_exception__no_event(
    mocker,
    api_client,
    fake_stream,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    message = 'Service error occurred'
    create_shared_fieldset_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.'
        'create_shared_fieldset',
        side_effect=BaseServiceException(message=message),
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.post('/fieldsets', data={'name': 'Contacts'})

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    assert response.data['details'] == {}
    assert fake_stream.events == []
    create_shared_fieldset_mock.assert_called_once_with(
        name='Contacts',
        rules=[],
        fields=[],
    )
