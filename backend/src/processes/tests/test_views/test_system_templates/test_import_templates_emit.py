import pytest

from src.logs.events.enums import (
    ActorType,
    EventCategory,
    EventName,
    EventObjectType,
)
from src.logs.events.schema import Actor, EventObject
from src.processes.models.templates.system_template import SystemTemplate
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_owner,
)
from src.utils.validation import ErrorCode

pytestmark = pytest.mark.django_db


def test_import_templates__two_templates__emit_template_library_import(
    api_client,
    fake_stream,
):

    # arrange
    account = create_test_account()
    staff = create_test_owner(
        account=account,
        is_staff=True,
    )
    api_client.token_authenticate(
        staff,
        user_agent='Chrome/141',
        user_ip='10.10.0.26',
    )

    # act
    response = api_client.post(
        '/templates/system/import',
        data={
            'info': 'library update',
            'templates': [
                {
                    'title': 'Performance Appraisal',
                    'intro': 'The performance appraisal process',
                    'category': 'Human Resources',
                    'steps': [
                        {
                            'stepName': 'Establish standards',
                            'stepDescription': 'The first step.',
                        },
                    ],
                },
                {
                    'title': 'Vendor Onboarding',
                    'intro': 'The vendor onboarding process',
                    'category': 'Procurement',
                    'steps': [
                        {
                            'stepName': 'Collect documents',
                            'stepDescription': 'The first step.',
                        },
                    ],
                },
            ],
        },
        HTTP_X_REQUEST_ID='audit-template-26',
    )

    # assert
    assert response.status_code == 204
    assert SystemTemplate.objects.count() == 2
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    assert event.type == EventName.TEMPLATE_LIBRARY_IMPORT
    assert event.category == EventCategory.AUDIT
    assert event.account_id == account.id
    assert event.actor == Actor(
        type=ActorType.USER,
        id=staff.id,
        email=staff.email,
    )
    assert event.object == EventObject(
        type=EventObjectType.SYSTEM_TEMPLATE,
        id=None,
    )
    assert event.payload == {'templates_count': 2}
    assert event.ip == '10.10.0.26'
    assert event.user_agent == 'Chrome/141'
    assert event.request_id == 'audit-template-26'
    assert event.pii == ('actor.email', 'ip', 'user_agent')


def test_import_templates__empty_templates__no_event(
    api_client,
    fake_stream,
):

    # arrange
    account = create_test_account()
    staff = create_test_owner(
        account=account,
        is_staff=True,
    )
    api_client.token_authenticate(staff)

    # act
    response = api_client.post(
        '/templates/system/import',
        data={'templates': []},
    )

    # assert
    assert response.status_code == 400
    message = 'This list may not be empty.'
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    assert response.data['details']['name'] == 'templates'
    assert response.data['details']['reason'] == message
    assert fake_stream.events == []


def test_import_templates__not_staff__no_event(
    api_client,
    fake_stream,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(
        account=account,
        is_staff=False,
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.post(
        '/templates/system/import',
        data={
            'templates': [
                {
                    'title': 'Performance Appraisal',
                    'intro': 'The performance appraisal process',
                    'category': 'Human Resources',
                    'steps': [
                        {
                            'stepName': 'Establish standards',
                            'stepDescription': 'The first step.',
                        },
                    ],
                },
            ],
        },
    )

    # assert
    assert response.status_code == 403
    assert SystemTemplate.objects.count() == 0
    assert fake_stream.events == []
