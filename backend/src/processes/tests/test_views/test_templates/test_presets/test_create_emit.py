import pytest

from src.logs.events.enums import (
    ActorType,
    EventCategory,
    EventName,
    EventObjectType,
)
from src.logs.events.schema import Actor, EventObject
from src.processes.enums import PresetType
from src.processes.models.templates.preset import TemplatePreset
from src.processes.services.exceptions import TemplatePresetServiceException
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_owner,
    create_test_template,
)
from src.utils.validation import ErrorCode

pytestmark = pytest.mark.django_db


def test_preset__created__emit_template_preset_create(
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
    api_client.token_authenticate(
        owner,
        user_agent='Chrome/141',
        user_ip='10.10.0.27',
    )

    # act
    response = api_client.post(
        f'/templates/{template.id}/preset',
        data={
            'name': 'Sales view',
            'is_default': True,
            'type': PresetType.ACCOUNT,
            'fields': [
                {
                    'api_name': 'field-1',
                    'order': 1,
                    'width': 200,
                },
            ],
        },
        HTTP_X_REQUEST_ID='audit-template-27',
    )

    # assert
    assert response.status_code == 200
    preset = TemplatePreset.objects.get(id=response.data['id'])
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    assert event.type == EventName.TEMPLATE_PRESET_CREATE
    assert event.category == EventCategory.ACTIVITY
    assert event.account_id == account.id
    assert event.actor == Actor(
        type=ActorType.USER,
        id=owner.id,
        email=owner.email,
    )
    assert event.object == EventObject(
        type=EventObjectType.TEMPLATE_PRESET,
        id=preset.id,
    )
    assert event.payload == {
        'name': 'Sales view',
        'template_id': template.id,
        'type': PresetType.ACCOUNT,
        'is_default': True,
    }
    assert event.ip == '10.10.0.27'
    assert event.user_agent == 'Chrome/141'
    assert event.request_id == 'audit-template-27'
    assert event.pii == (
        'actor.email',
        'ip',
        'user_agent',
        'payload.name',
    )


def test_preset__service_exception__no_event(
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
    api_client.token_authenticate(owner)
    error_message = 'Service error occurred'
    service_create_mock = mocker.patch(
        'src.processes.services.templates.preset.'
        'TemplatePresetService.create',
        side_effect=TemplatePresetServiceException(error_message),
    )

    # act
    response = api_client.post(
        f'/templates/{template.id}/preset',
        data={
            'name': 'Sales view',
            'is_default': False,
            'type': PresetType.PERSONAL,
            'fields': [],
        },
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == error_message
    assert response.data['details'] == {}
    assert fake_stream.events == []
    service_create_mock.assert_called_once_with(
        template=template,
        name='Sales view',
        is_default=False,
        type=PresetType.PERSONAL,
        fields=[],
    )


def test_preset__invalid_type__no_event(
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
    api_client.token_authenticate(owner)

    # act
    response = api_client.post(
        f'/templates/{template.id}/preset',
        data={
            'name': 'Sales view',
            'is_default': False,
            'type': 'invalid_type',
            'fields': [],
        },
    )

    # assert
    assert response.status_code == 400
    message = '"invalid_type" is not a valid choice.'
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    assert response.data['details']['name'] == 'type'
    assert response.data['details']['reason'] == message
    assert TemplatePreset.objects.count() == 0
    assert fake_stream.events == []
