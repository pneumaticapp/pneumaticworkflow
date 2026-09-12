import pytest

from src.logs.events.enums import (
    ActorType,
    EventCategory,
    EventName,
    EventObjectType,
)
from src.logs.events.schema import Actor, EventObject
from src.processes.enums import PresetType
from src.processes.services.exceptions import TemplatePresetServiceException
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_owner,
    create_test_template,
    create_test_template_preset,
)
from src.utils.validation import ErrorCode

pytestmark = pytest.mark.django_db


def test_update__preset__emit_template_preset_update(
    api_client,
    fake_stream,
):

    """ The payload carries the values the preset got, not the ones
        it had before the change. """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    template = create_test_template(
        user=owner,
        is_active=True,
        tasks_count=1,
    )
    preset = create_test_template_preset(
        template=template,
        author=owner,
        name='Old view',
        is_default=False,
        type=PresetType.PERSONAL,
    )
    api_client.token_authenticate(
        owner,
        user_agent='Chrome/141',
        user_ip='10.10.0.28',
    )

    # act
    response = api_client.put(
        f'/templates/presets/{preset.id}',
        data={
            'name': 'Sales view',
            'is_default': True,
            'type': PresetType.ACCOUNT,
            'fields': [],
        },
        HTTP_X_REQUEST_ID='audit-template-28',
    )

    # assert
    assert response.status_code == 200
    preset.refresh_from_db()
    assert preset.name == 'Sales view'
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    assert event.type == EventName.TEMPLATE_PRESET_UPDATE
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
    assert event.ip == '10.10.0.28'
    assert event.user_agent == 'Chrome/141'
    assert event.request_id == 'audit-template-28'


def test_partial_update__preset__emit_template_preset_update(
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
    preset = create_test_template_preset(
        template=template,
        author=owner,
        name='Old view',
        is_default=False,
        type=PresetType.PERSONAL,
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.patch(
        f'/templates/presets/{preset.id}',
        data={
            'name': 'Sales view',
            'is_default': False,
            'type': PresetType.PERSONAL,
            'fields': [],
        },
    )

    # assert
    assert response.status_code == 200
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    assert event.type == EventName.TEMPLATE_PRESET_UPDATE
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
        'type': PresetType.PERSONAL,
        'is_default': False,
    }


def test_update__service_exception__no_event(
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
    preset = create_test_template_preset(
        template=template,
        author=owner,
        type=PresetType.PERSONAL,
    )
    api_client.token_authenticate(owner)
    error_message = 'Service error occurred'
    partial_update_mock = mocker.patch(
        'src.processes.services.templates.preset.'
        'TemplatePresetService.partial_update',
        side_effect=TemplatePresetServiceException(error_message),
    )

    # act
    response = api_client.put(
        f'/templates/presets/{preset.id}',
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
    partial_update_mock.assert_called_once_with(
        force_save=True,
        name='Sales view',
        is_default=False,
        type=PresetType.PERSONAL,
        fields=[],
    )


def test_update__invalid_type__no_event(
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
    preset = create_test_template_preset(
        template=template,
        author=owner,
        name='Old view',
        type=PresetType.PERSONAL,
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.put(
        f'/templates/presets/{preset.id}',
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
    preset.refresh_from_db()
    assert preset.name == 'Old view'
    assert fake_stream.events == []
