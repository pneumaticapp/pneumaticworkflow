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
    create_test_template_preset,
)
from src.utils.validation import ErrorCode

pytestmark = pytest.mark.django_db


def test_destroy__preset__emit_template_preset_delete(
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
        name='Sales view',
        is_default=True,
        type=PresetType.PERSONAL,
    )
    api_client.token_authenticate(
        owner,
        user_agent='Chrome/141',
        user_ip='10.10.0.29',
    )

    # act
    response = api_client.delete(
        f'/templates/presets/{preset.id}',
        HTTP_X_REQUEST_ID='audit-template-29',
    )

    # assert
    assert response.status_code == 204
    assert not TemplatePreset.objects.filter(id=preset.id).exists()
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    assert event.type == EventName.TEMPLATE_PRESET_DELETE
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
        'is_default': True,
    }
    assert event.ip == '10.10.0.29'
    assert event.user_agent == 'Chrome/141'
    assert event.request_id == 'audit-template-29'


def test_destroy__service_exception__no_event(
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
    service_delete_mock = mocker.patch(
        'src.processes.services.templates.preset.'
        'TemplatePresetService.delete',
        side_effect=TemplatePresetServiceException(error_message),
    )

    # act
    response = api_client.delete(f'/templates/presets/{preset.id}')

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == error_message
    assert response.data['details'] == {}
    assert TemplatePreset.objects.filter(id=preset.id).exists()
    assert fake_stream.events == []
    service_delete_mock.assert_called_once_with()
