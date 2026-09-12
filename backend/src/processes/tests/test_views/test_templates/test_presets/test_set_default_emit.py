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


def test_set_default__preset__emit_template_preset_set_default(
    api_client,
    fake_stream,
):

    """ The preset was not the default one before the request: the
        payload has to say what it became. """

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
        is_default=False,
        type=PresetType.PERSONAL,
    )
    api_client.token_authenticate(
        owner,
        user_agent='Chrome/141',
        user_ip='10.10.0.30',
    )

    # act
    response = api_client.post(
        f'/templates/presets/{preset.id}/default',
        HTTP_X_REQUEST_ID='audit-template-30',
    )

    # assert
    assert response.status_code == 204
    preset.refresh_from_db()
    assert preset.is_default is True
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    assert event.type == EventName.TEMPLATE_PRESET_SET_DEFAULT
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
    assert event.ip == '10.10.0.30'
    assert event.user_agent == 'Chrome/141'
    assert event.request_id == 'audit-template-30'


def test_set_default__service_exception__no_event(
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
        is_default=False,
        type=PresetType.PERSONAL,
    )
    api_client.token_authenticate(owner)
    error_message = 'Service error occurred'
    set_default_mock = mocker.patch(
        'src.processes.services.templates.preset.'
        'TemplatePresetService.set_default',
        side_effect=TemplatePresetServiceException(error_message),
    )

    # act
    response = api_client.post(f'/templates/presets/{preset.id}/default')

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == error_message
    assert response.data['details'] == {}
    preset.refresh_from_db()
    assert preset.is_default is False
    assert fake_stream.events == []
    set_default_mock.assert_called_once_with()
