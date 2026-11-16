import pytest
from django.utils import timezone

from src.authentication.enums import AuthTokenType
from src.processes.enums import WorkflowEventType
from src.processes.models.workflows.event import WorkflowEvent
from src.processes.services.events import WorkflowEventService
from src.processes.services.urgent import UrgentService
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_owner,
    create_test_workflow,
)

pytestmark = pytest.mark.django_db


def test__create_urgent_actions__urgent__emit_workflow_urgent(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(
        user=owner,
        is_urgent=True,
    )
    task = workflow.tasks.get(number=1)
    send_urgent_notification_mock = mocker.patch(
        'src.processes.services.urgent.send_urgent_notification.delay',
    )
    send_not_urgent_notification_mock = mocker.patch(
        'src.processes.services.urgent.send_not_urgent_notification.delay',
    )
    workflow_urgent_event_mock = mocker.patch(
        'src.processes.services.urgent.WorkflowEventService'
        '.workflow_urgent_event',
    )
    workflow_urgent_mock = mocker.patch(
        'src.processes.services.urgent.AuditEventService.workflow_urgent',
    )

    # act
    UrgentService._create_urgent_actions(
        workflow=workflow,
        user=owner,
        auth_type=AuthTokenType.USER,
    )

    # assert
    send_urgent_notification_mock.assert_called_once_with(
        logging=account.log_api_requests,
        logo_lg=account.logo_lg,
        author_id=owner.id,
        task_ids=[task.id],
        account_id=account.id,
    )
    send_not_urgent_notification_mock.assert_not_called()
    workflow_urgent_event_mock.assert_called_once_with(
        event_type=WorkflowEventType.URGENT,
        workflow=workflow,
        user=owner,
    )
    workflow_urgent_mock.assert_called_once_with(
        user=owner,
        auth_type=AuthTokenType.USER,
        workflow=workflow,
    )


def test__create_urgent_actions__not_urgent__emit_workflow_urgent(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    task = workflow.tasks.get(number=1)
    send_urgent_notification_mock = mocker.patch(
        'src.processes.services.urgent.send_urgent_notification.delay',
    )
    send_not_urgent_notification_mock = mocker.patch(
        'src.processes.services.urgent.send_not_urgent_notification.delay',
    )
    workflow_urgent_event_mock = mocker.patch(
        'src.processes.services.urgent.WorkflowEventService'
        '.workflow_urgent_event',
    )
    workflow_urgent_mock = mocker.patch(
        'src.processes.services.urgent.AuditEventService.workflow_urgent',
    )

    # act
    UrgentService._create_urgent_actions(
        workflow=workflow,
        user=owner,
        auth_type=AuthTokenType.USER,
    )

    # assert
    send_urgent_notification_mock.assert_not_called()
    send_not_urgent_notification_mock.assert_called_once_with(
        author_id=owner.id,
        logging=account.log_api_requests,
        logo_lg=account.logo_lg,
        task_ids=[task.id],
        account_id=account.id,
    )
    workflow_urgent_event_mock.assert_called_once_with(
        event_type=WorkflowEventType.NOT_URGENT,
        workflow=workflow,
        user=owner,
    )
    workflow_urgent_mock.assert_called_once_with(
        user=owner,
        auth_type=AuthTokenType.USER,
        workflow=workflow,
    )


def test_resolve__same_type__audit_not_called(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(
        user=owner,
        is_urgent=True,
    )
    prev_urgent_event = WorkflowEventService.workflow_urgent_event(
        user=owner,
        event_type=WorkflowEventType.URGENT,
        workflow=workflow,
        after_create_actions=False,
    )
    send_urgent_notification_mock = mocker.patch(
        'src.processes.services.urgent.send_urgent_notification.delay',
    )
    send_not_urgent_notification_mock = mocker.patch(
        'src.processes.services.urgent.send_not_urgent_notification.delay',
    )
    workflow_urgent_event_mock = mocker.patch(
        'src.processes.services.urgent.WorkflowEventService'
        '.workflow_urgent_event',
    )
    workflow_urgent_mock = mocker.patch(
        'src.processes.services.urgent.AuditEventService.workflow_urgent',
    )

    # act
    UrgentService.resolve(
        workflow=workflow,
        user=owner,
        auth_type=AuthTokenType.USER,
    )

    # assert
    prev_urgent_event.refresh_from_db()
    assert prev_urgent_event.is_deleted is False
    send_urgent_notification_mock.assert_not_called()
    send_not_urgent_notification_mock.assert_not_called()
    workflow_urgent_event_mock.assert_not_called()
    workflow_urgent_mock.assert_not_called()


def test_resolve__reverse_type_less_minute__audit_not_called(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    prev_urgent_event = WorkflowEventService.workflow_urgent_event(
        user=owner,
        event_type=WorkflowEventType.URGENT,
        workflow=workflow,
        after_create_actions=False,
    )
    send_urgent_notification_mock = mocker.patch(
        'src.processes.services.urgent.send_urgent_notification.delay',
    )
    send_not_urgent_notification_mock = mocker.patch(
        'src.processes.services.urgent.send_not_urgent_notification.delay',
    )
    workflow_urgent_event_mock = mocker.patch(
        'src.processes.services.urgent.WorkflowEventService'
        '.workflow_urgent_event',
    )
    workflow_urgent_mock = mocker.patch(
        'src.processes.services.urgent.AuditEventService.workflow_urgent',
    )

    # act
    UrgentService.resolve(
        workflow=workflow,
        user=owner,
        auth_type=AuthTokenType.USER,
    )

    # assert
    prev_urgent_event.refresh_from_db()
    assert prev_urgent_event.is_deleted is True
    send_urgent_notification_mock.assert_not_called()
    send_not_urgent_notification_mock.assert_not_called()
    workflow_urgent_event_mock.assert_not_called()
    workflow_urgent_mock.assert_not_called()


def test_resolve__no_prev_event__audit_called(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(
        user=owner,
        is_urgent=True,
    )
    task = workflow.tasks.get(number=1)
    send_urgent_notification_mock = mocker.patch(
        'src.processes.services.urgent.send_urgent_notification.delay',
    )
    send_not_urgent_notification_mock = mocker.patch(
        'src.processes.services.urgent.send_not_urgent_notification.delay',
    )
    workflow_urgent_event_mock = mocker.patch(
        'src.processes.services.urgent.WorkflowEventService'
        '.workflow_urgent_event',
    )
    workflow_urgent_mock = mocker.patch(
        'src.processes.services.urgent.AuditEventService.workflow_urgent',
    )

    # act
    UrgentService.resolve(
        workflow=workflow,
        user=owner,
        auth_type=AuthTokenType.API,
    )

    # assert
    send_urgent_notification_mock.assert_called_once_with(
        logging=account.log_api_requests,
        logo_lg=account.logo_lg,
        author_id=owner.id,
        task_ids=[task.id],
        account_id=account.id,
    )
    send_not_urgent_notification_mock.assert_not_called()
    workflow_urgent_event_mock.assert_called_once_with(
        event_type=WorkflowEventType.URGENT,
        workflow=workflow,
        user=owner,
    )
    workflow_urgent_mock.assert_called_once_with(
        user=owner,
        auth_type=AuthTokenType.API,
        workflow=workflow,
    )


def test_resolve__reverse_type_more_minute__audit_called(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    task = workflow.tasks.get(number=1)
    prev_urgent_event = WorkflowEventService.workflow_urgent_event(
        user=owner,
        event_type=WorkflowEventType.URGENT,
        workflow=workflow,
        after_create_actions=False,
    )
    WorkflowEvent.objects.filter(id=prev_urgent_event.id).update(
        created=timezone.now() - timezone.timedelta(minutes=2),
    )
    send_urgent_notification_mock = mocker.patch(
        'src.processes.services.urgent.send_urgent_notification.delay',
    )
    send_not_urgent_notification_mock = mocker.patch(
        'src.processes.services.urgent.send_not_urgent_notification.delay',
    )
    workflow_urgent_event_mock = mocker.patch(
        'src.processes.services.urgent.WorkflowEventService'
        '.workflow_urgent_event',
    )
    workflow_urgent_mock = mocker.patch(
        'src.processes.services.urgent.AuditEventService.workflow_urgent',
    )

    # act
    UrgentService.resolve(
        workflow=workflow,
        user=owner,
        auth_type=AuthTokenType.API,
    )

    # assert
    prev_urgent_event.refresh_from_db()
    assert prev_urgent_event.is_deleted is False
    send_urgent_notification_mock.assert_not_called()
    send_not_urgent_notification_mock.assert_called_once_with(
        author_id=owner.id,
        logging=account.log_api_requests,
        logo_lg=account.logo_lg,
        task_ids=[task.id],
        account_id=account.id,
    )
    workflow_urgent_event_mock.assert_called_once_with(
        event_type=WorkflowEventType.NOT_URGENT,
        workflow=workflow,
        user=owner,
    )
    workflow_urgent_mock.assert_called_once_with(
        user=owner,
        auth_type=AuthTokenType.API,
        workflow=workflow,
    )
