# pylint:disable=redefined-outer-name
from datetime import timedelta

import pytest
from django.db.models import Q
from django.utils import timezone
from pneumatic_backend.processes.models import (
    Workflow,
    Delay,
    FieldTemplate,
    ConditionTemplate,
    RuleTemplate,
    PredicateTemplate,
    FieldTemplateSelection,
)
from pneumatic_backend.processes.services.exceptions import \
    WorkflowActionServiceException
from pneumatic_backend.processes.services.workflow_action import \
    WorkflowActionService
from pneumatic_backend.processes.tests.fixtures import (
    create_test_workflow,
    create_test_user,
    create_test_template,
    create_test_account,
    create_task_returned_webhook,
)
from pneumatic_backend.processes.messages import workflow as messages
from pneumatic_backend.utils.validation import ErrorCode
from pneumatic_backend.processes.enums import (
    PredicateOperator,
    FieldType,
    WorkflowStatus,
)
from pneumatic_backend.authentication.enums import AuthTokenType

pytestmark = pytest.mark.django_db


def test_return_to__by_task_id__ok(
    api_client,
    mocker,
):
    # arrange
    user = create_test_user(is_account_owner=True)
    workflow = create_test_workflow(
        user=user,
        tasks_count=3
    )
    workflow.current_task = 3
    workflow.save()
    task_1 = workflow.tasks.get(number=1)
    service_init_mock = mocker.patch.object(
        WorkflowActionService,
        attribute='__init__',
        return_value=None
    )
    service_revert_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action.'
        'WorkflowActionService.return_to'
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        f'/workflows/{workflow.id}/return-to',
        data={'task': task_1.id}
    )

    # assert
    assert response.status_code == 204
    service_init_mock.assert_called_once_with(
        user=user,
        auth_type=AuthTokenType.USER,
        is_superuser=False
    )
    service_revert_mock.assert_called_once_with(
        workflow=workflow,
        revert_to_task=task_1,
    )


def test_return_to__by_task_api_name__ok(
    api_client,
    mocker,
):
    # arrange
    user = create_test_user(is_account_owner=True)
    workflow = create_test_workflow(
        user=user,
        tasks_count=3
    )
    workflow.current_task = 3
    workflow.save()
    task_1 = workflow.tasks.get(number=1)
    service_init_mock = mocker.patch.object(
        WorkflowActionService,
        attribute='__init__',
        return_value=None
    )
    service_revert_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action.'
        'WorkflowActionService.return_to'
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        f'/workflows/{workflow.id}/return-to',
        data={'task_api_name': task_1.api_name}
    )

    # assert
    assert response.status_code == 204
    service_init_mock.assert_called_once_with(
        user=user,
        auth_type=AuthTokenType.USER,
        is_superuser=False
    )
    service_revert_mock.assert_called_once_with(
        workflow=workflow,
        revert_to_task=task_1,
    )


def test_return_to__skip_task_key__validation_error(
    api_client,
    mocker,
):
    # arrange
    user = create_test_user(is_account_owner=True)
    workflow = create_test_workflow(
        user=user,
        tasks_count=3
    )
    service_init_mock = mocker.patch.object(
        WorkflowActionService,
        attribute='__init__',
        return_value=None
    )
    service_revert_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action.'
        'WorkflowActionService.return_to'
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        f'/workflows/{workflow.id}/return-to',
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == messages.MSG_PW_0076
    service_init_mock.assert_not_called()
    service_revert_mock.assert_not_called()


def test_return_to__another_workflow_task__validation_error(
    api_client,
    mocker,
):
    # arrange
    user = create_test_user(is_account_owner=True)
    workflow = create_test_workflow(user=user, tasks_count=1)
    another_workflow = create_test_workflow(user=user, tasks_count=1)
    another_task = another_workflow.tasks.get(number=1)
    service_init_mock = mocker.patch.object(
        WorkflowActionService,
        attribute='__init__',
        return_value=None
    )
    service_revert_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action.'
        'WorkflowActionService.return_to'
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        f'/workflows/{workflow.id}/return-to',
        data={'task_api_name': another_task.api_name}
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == messages.MSG_PW_0077
    service_init_mock.assert_not_called()
    service_revert_mock.assert_not_called()


def test_revert_service_exception__validation_error(
    api_client,
    mocker,
):
    # arrange
    user = create_test_user(is_account_owner=True)
    workflow = create_test_workflow(
        user=user,
        tasks_count=3
    )
    workflow.current_task = 3
    workflow.save()
    task_1 = workflow.tasks.get(number=1)
    service_init_mock = mocker.patch.object(
        WorkflowActionService,
        attribute='__init__',
        return_value=None
    )
    message = 'Some message'
    ex = WorkflowActionServiceException(message)
    service_revert_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action.'
        'WorkflowActionService.return_to',
        side_effect=ex,
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        f'/workflows/{workflow.id}/return-to',
        data={'task': task_1.id}
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    service_init_mock.assert_called_once_with(
        user=user,
        auth_type=AuthTokenType.USER,
        is_superuser=False
    )
    service_revert_mock.assert_called_once_with(
        workflow=workflow,
        revert_to_task=task_1,
    )


# TODO Deprecated old style tests


def test_return_to__ok(mocker, api_client):

    # arrange
    user = create_test_user()
    create_task_returned_webhook(user)
    workflow = create_test_workflow(user, tasks_count=3)
    api_client.token_authenticate(user)

    response_complete_1 = api_client.post(
        f'/workflows/{workflow.id}/task-complete',
        data={'task_id': workflow.current_task_instance.id}
    )
    workflow.refresh_from_db()
    response_complete_2 = api_client.post(
        f'/workflows/{workflow.id}/task-complete',
        data={'task_id': workflow.current_task_instance.id}
    )
    workflow.refresh_from_db()

    send_new_task_notification_ws_mock = mocker.patch(
        'pneumatic_backend.processes.services.websocket.WSSender.'
        'send_new_task_notification'
    )
    send_removed_task_notification_mock = mocker.patch(
        'pneumatic_backend.processes.services.websocket.WSSender.'
        'send_removed_task_notification'
    )
    delete_task_guest_cache_mock = mocker.patch(
        'pneumatic_backend.authentication.services.'
        'GuestJWTAuthService.delete_task_guest_cache'
    )
    send_new_task_notification_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action.'
        'send_new_task_notification.delay'
    )
    mocker.patch(
        'pneumatic_backend.processes.tasks.webhooks.'
        'send_workflow_started_webhook.delay',
    )
    mocker.patch(
        'pneumatic_backend.processes.tasks.webhooks.'
        'send_task_completed_webhook.delay'
    )
    webhook_payload = mocker.Mock()
    mocker.patch(
        'pneumatic_backend.processes.models.workflows.task.Task'
        '.webhook_payload',
        return_value=webhook_payload
    )
    revert_task_webhook_mock = mocker.patch(
        'pneumatic_backend.processes.tasks.webhooks.'
        'send_task_returned_webhook.delay',
    )
    revert_workflow_event_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action.'
        'WorkflowEventService.workflow_revert_event'
    )
    start_workflow_event_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action.'
        'WorkflowEventService.task_started_event'
    )
    analytics_return_workflow_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action.'
        'AnalyticService.workflow_returned'
    )

    task_1 = workflow.tasks.get(number=1)

    # act
    response = api_client.post(
        path=f'/workflows/{workflow.id}/return-to',
        data={
            'task': task_1.id
        }
    )

    # assert
    assert response_complete_1.status_code == 204
    assert response_complete_2.status_code == 204
    workflow.refresh_from_db()
    assert response.status_code == 204
    assert workflow.current_task == 1
    assert workflow.tasks.filter(
        Q(date_started__isnull=False) |
        Q(date_completed__isnull=False) |
        Q(is_completed=True),
        number__gt=1
    ).count() == 0
    send_new_task_notification_ws_mock.assert_called_once_with(
        task=task_1,
        sync=False
    )
    send_removed_task_notification_mock.assert_called_once()
    send_new_task_notification_mock.assert_called_once()
    analytics_return_workflow_mock.assert_called_once_with(
        user=user,
        task=task_1,
        workflow=workflow,
        is_superuser=False,
        auth_type=AuthTokenType.USER
    )
    delete_task_guest_cache_mock.assert_called_once_with(
        task_id=task_1.id
    )
    revert_task_webhook_mock.assert_called_once_with(
        user_id=user.id,
        account_id=user.account_id,
        payload=webhook_payload
    )
    task_3 = workflow.tasks.get(number=3)
    revert_workflow_event_mock.assert_called_once_with(
        task=task_3,
        user=user
    )
    start_workflow_event_mock.assert_called_once_with(task_1)


def test_return_to__task_with_delay__reset_delay(
    mocker,
    api_client,
):
    """ https://trello.com/c/8rbbGOcp """

    # arrange
    mocker.patch(
        'pneumatic_backend.processes.tasks.webhooks.'
        'send_workflow_started_webhook.delay',
    )
    mocker.patch(
        'pneumatic_backend.processes.tasks.webhooks.'
        'send_task_completed_webhook.delay'
    )
    mocker.patch(
        'pneumatic_backend.processes.tasks.webhooks.'
        'send_task_returned_webhook.delay',
    )
    user = create_test_user()
    workflow = create_test_workflow(user)
    task_1 = workflow.tasks.get(number=1)
    task_2 = workflow.tasks.get(number=2)
    delay = Delay.objects.create(
        task=task_2,
        duration=timedelta(seconds=10),
    )

    api_client.token_authenticate(user)
    api_client.post(
        f'/workflows/{workflow.id}/task-complete',
        data={'task_id': task_1.id}
    )
    api_client.post(f'/workflows/{workflow.id}/resume')

    # act
    response = api_client.post(
        f'/workflows/{workflow.id}/return-to',
        data={'task': task_1.id}
    )

    # assert
    assert response.status_code == 204
    workflow.refresh_from_db()
    task_1.refresh_from_db()
    delay.refresh_from_db()

    assert delay.end_date is None
    assert delay.start_date is None
    assert delay.estimated_end_date is None
    assert workflow.current_task == 1
    assert task_1.is_completed is False
    assert task_1.date_completed is None
    assert task_1.date_first_started


def test_return_to__skip_condition__validation_error(
    api_client,
    mocker,
):
    # arrange
    mocker.patch(
        'pneumatic_backend.processes.tasks.webhooks.'
        'send_workflow_started_webhook.delay',
    )
    mocker.patch(
        'pneumatic_backend.processes.tasks.webhooks.'
        'send_task_returned_webhook.delay',
    )
    user = create_test_user()
    template = create_test_template(user, is_active=True)
    field_template = FieldTemplate.objects.create(
        name='Performer',
        is_required=True,
        type=FieldType.USER,
        kickoff=template.kickoff_instance,
        template=template,
    )
    first_task = template.tasks.order_by('number').first()
    second_task = template.tasks.get(number=2)
    condition_template = ConditionTemplate.objects.create(
        task=first_task,
        action=ConditionTemplate.SKIP_TASK,
        order=0,
        template=template,
    )
    rule_1 = RuleTemplate.objects.create(
        condition=condition_template,
        template=template,
    )
    PredicateTemplate.objects.create(
        rule=rule_1,
        operator=PredicateOperator.EQUAL,
        field_type=FieldType.USER,
        field=field_template.api_name,
        value=user.id,
        template=template,
    )
    second_condition_template = ConditionTemplate.objects.create(
        task=second_task,
        action=ConditionTemplate.SKIP_TASK,
        order=0,
        template=template,
    )
    rule_2 = RuleTemplate.objects.create(
        condition=second_condition_template,
        template=template,
    )
    PredicateTemplate.objects.create(
        rule=rule_2,
        operator=PredicateOperator.EQUAL,
        field_type=FieldType.USER,
        field=field_template.api_name,
        value=user.id,
        template=template,
    )

    api_client.token_authenticate(user=user)
    response = api_client.post(
        f'/templates/{template.id}/run',
        data={
            'name': 'Test name',
            'kickoff': {
                field_template.api_name: user.id
            }
        }
    )
    workflow = Workflow.objects.get(id=response.data['id'])
    data = {
        'task': workflow.tasks.get(number=1).id
    }

    # act
    response = api_client.post(
        f'/workflows/{workflow.id}/return-to',
        data=data
    )

    # assert
    assert response.status_code == 400
    workflow.refresh_from_db()
    assert workflow.current_task == 3


def test_return_to__force_snooze_and_return_to__snooze_not_running_again(
    mocker,
    api_client
):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user, tasks_count=2)
    api_client.token_authenticate(user)
    first_task = workflow.tasks.get(number=1)

    mocker.patch(
        'pneumatic_backend.processes.tasks.webhooks.'
        'send_task_returned_webhook.delay',
    )
    mocker.patch(
        'pneumatic_backend.processes.tasks.webhooks.'
        'send_task_completed_webhook.delay',
    )

    response_complete = api_client.post(
        f'/workflows/{workflow.id}/task-complete',
        data={'task_id': first_task.id}
    )
    workflow.refresh_from_db()

    mocker.patch(
        'pneumatic_backend.processes.services.websocket.WSSender.'
        'send_removed_task_notification'
    )
    mocker.patch(
        'pneumatic_backend.processes.services.workflow_action.'
        'send_new_task_notification.delay'
    )
    mocker.patch(
        'pneumatic_backend.authentication.services.'
        'GuestJWTAuthService.delete_task_guest_cache'
    )
    date = timezone.now() + timedelta(days=1)

    response_snooze = api_client.post(
        f'/workflows/{workflow.id}/snooze',
        data={'date': str(date)}
    )
    workflow.refresh_from_db()

    response_return_to = api_client.post(
        f'/workflows/{workflow.id}/return-to',
        data={'task': first_task.id}
    )
    workflow.refresh_from_db()

    # act
    response_complete_2 = api_client.post(
        f'/workflows/{workflow.id}/task-complete',
        data={'task_id': workflow.current_task_instance.id}
    )

    # assert
    assert response_complete.status_code == 204
    assert response_snooze.status_code == 200
    assert response_return_to.status_code == 204
    assert response_complete_2.status_code == 204
    workflow.refresh_from_db()
    assert workflow.status == WorkflowStatus.RUNNING


def test_return_to__force_snooze_and_resume__snooze_not_running_again(
    mocker,
    api_client
):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user, tasks_count=2)
    api_client.token_authenticate(user)
    first_task = workflow.tasks.get(number=1)
    mocker.patch(
        'pneumatic_backend.processes.tasks.webhooks.'
        'send_task_returned_webhook.delay',
    )
    mocker.patch(
        'pneumatic_backend.processes.tasks.webhooks.'
        'send_task_completed_webhook.delay',
    )
    response_complete = api_client.post(
        f'/workflows/{workflow.id}/task-complete',
        data={'task_id': first_task.id}
    )
    workflow.refresh_from_db()

    mocker.patch(
        'pneumatic_backend.processes.services.websocket.WSSender.'
        'send_removed_task_notification'
    )
    mocker.patch(
        'pneumatic_backend.processes.services.workflow_action.'
        'send_new_task_notification.delay'
    )
    mocker.patch(
        'pneumatic_backend.authentication.services.'
        'GuestJWTAuthService.delete_task_guest_cache'
    )
    date = timezone.now() + timedelta(days=1)

    response_snooze = api_client.post(
        f'/workflows/{workflow.id}/snooze',
        data={'date': str(date)}
    )
    workflow.refresh_from_db()
    response_resume = api_client.post(f'/workflows/{workflow.id}/resume')

    response_return_to = api_client.post(
        f'/workflows/{workflow.id}/return-to',
        data={'task': first_task.id}
    )
    workflow.refresh_from_db()

    # act
    response_complete_2 = api_client.post(
        f'/workflows/{workflow.id}/task-complete',
        data={'task_id': first_task.id}
    )

    # assert
    assert response_complete.status_code == 204
    assert response_snooze.status_code == 200
    assert response_resume.status_code == 204
    assert response_return_to.status_code == 204
    assert response_complete_2.status_code == 204
    workflow.refresh_from_db()
    assert workflow.status == WorkflowStatus.RUNNING


def test_return_to__skipped_task__not_completed(
    mocker,
    api_client
):

    # arrange
    mocker.patch(
        'pneumatic_backend.processes.tasks.webhooks.'
        'send_workflow_started_webhook.delay',
    )
    mocker.patch(
        'pneumatic_backend.processes.tasks.webhooks.'
        'send_task_returned_webhook.delay',
    )
    mocker.patch(
        'pneumatic_backend.processes.services.websocket.WSSender.'
        'send_new_task_notification'
    )
    mocker.patch(
        'pneumatic_backend.processes.services.websocket.WSSender.'
        'send_removed_task_notification'
    )
    mocker.patch(
        'pneumatic_backend.authentication.services.'
        'GuestJWTAuthService.delete_task_guest_cache'
    )
    mocker.patch(
        'pneumatic_backend.processes.services.workflow_action.'
        'send_new_task_notification.delay'
    )
    account = create_test_account()
    create_test_user(
        is_account_owner=True,
        email='owner@test.test',
        account=account
    )
    user = create_test_user(
        is_account_owner=False,
        email='user@test.test',
        account=account
    )
    # Specific performer for second step
    user_2 = create_test_user(
        is_account_owner=False,
        email='performer_2_task@test.test',
        account=account
    )
    template = create_test_template(
        user=user,
        is_active=True,
        tasks_count=3
    )
    task_template_2 = template.tasks.get(number=2)
    task_template_2.add_raw_performer(user_2)
    task_template_2.delete_raw_performer(user)

    # Condition for skip second step
    field_template = FieldTemplate.objects.create(
        name='Skip second task',
        is_required=True,
        type=FieldType.CHECKBOX,
        kickoff=template.kickoff_instance,
        template=template,
    )
    selection_template = FieldTemplateSelection.objects.create(
        field_template=field_template,
        value='Skip second task',
        template=template,
    )
    condition_template = ConditionTemplate.objects.create(
        task=task_template_2,
        action=ConditionTemplate.SKIP_TASK,
        order=0,
        template=template,
    )
    rule_1 = RuleTemplate.objects.create(
        condition=condition_template,
        template=template,
    )
    PredicateTemplate.objects.create(
        rule=rule_1,
        operator=PredicateOperator.EQUAL,
        field_type=field_template.type,
        field=field_template.api_name,
        value=selection_template.api_name,
        template=template,
    )

    api_client.token_authenticate(user)

    # Run with flag for skip second task
    response_run = api_client.post(
        f'/templates/{template.id}/run',
        data={
            'name': 'Test name',
            'kickoff': {
                field_template.api_name: [selection_template.api_name]
            }
        }
    )

    workflow = Workflow.objects.get(id=response_run.data['id'])

    task_1 = workflow.tasks.get(number=1)
    response_complete = api_client.post(
        f'/workflows/{workflow.id}/task-complete',
        data={'task_id': task_1.id}
    )

    # now third task is current

    # act
    response_return = api_client.post(
        path=f'/workflows/{workflow.id}/return-to',
        data={'task': task_1.id}
    )

    # assert
    assert response_complete.status_code == 204
    assert response_run.status_code == 200
    assert response_return.status_code == 204

    workflow.refresh_from_db()
    assert workflow.current_task == 1
    task_2 = workflow.tasks.get(number=2)
    assert task_2.is_skipped is False
    assert task_2.is_completed is False
    assert task_2.date_completed is None
    assert task_2.taskperformer_set.count() == 0


def test_return_to__completed_workflow__ok(
    mocker,
    api_client,
):

    # arrange
    user = create_test_user()
    create_task_returned_webhook(user)
    workflow = create_test_workflow(user, tasks_count=1)
    first_task = workflow.tasks.get(number=1)

    api_client.token_authenticate(user)

    response_complete = api_client.post(
        f'/workflows/{workflow.id}/task-complete',
        data={
            'task_id': workflow.current_task_instance.id,
        },
    )

    delete_task_guest_cache_mock = mocker.patch(
        'pneumatic_backend.authentication.services.'
        'GuestJWTAuthService.delete_task_guest_cache'
    )
    send_new_task_notification_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action.'
        'send_new_task_notification.delay'
    )
    mocker.patch(
        'pneumatic_backend.processes.tasks.webhooks.'
        'send_workflow_started_webhook.delay',
    )
    webhook_payload = mocker.Mock()
    mocker.patch(
        'pneumatic_backend.processes.models.workflows.task.Task'
        '.webhook_payload',
        return_value=webhook_payload
    )
    revert_task_webhook_mock = mocker.patch(
        'pneumatic_backend.processes.tasks.webhooks.'
        'send_task_returned_webhook.delay',
    )
    send_removed_task_notification_mock = mocker.patch(
        'pneumatic_backend.processes.services.websocket.WSSender.'
        'send_removed_task_notification'
    )
    send_new_task_notification_ws_mock = mocker.patch(
        'pneumatic_backend.processes.services.websocket.WSSender.'
        'send_new_task_notification'
    )

    # act
    response = api_client.post(
        path=f'/workflows/{workflow.id}/return-to',
        data={
            'task': first_task.id
        }
    )

    # assert
    workflow.refresh_from_db()
    assert response_complete.status_code == 204
    assert response.status_code == 204
    assert workflow.current_task == 1
    assert workflow.is_running
    send_new_task_notification_ws_mock.assert_called_once()
    send_removed_task_notification_mock.assert_not_called()
    send_new_task_notification_mock.assert_called_once()
    delete_task_guest_cache_mock.assert_called_once()
    revert_task_webhook_mock.assert_called_once()


@pytest.mark.parametrize('status', WorkflowStatus.RUNNING_STATUSES)
def test_return_to__sub_workflow_incompleted__validation_error(
    status,
    api_client,
):
    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user=user, tasks_count=2)
    workflow.current_task = 2
    workflow.save()
    task_1 = workflow.tasks.get(number=1)
    task_1.is_completed = True
    task_1.date_completed = timezone.now()
    task_1.save()
    task_2 = workflow.tasks.get(number=2)

    create_test_workflow(
        user=user,
        tasks_count=1,
        ancestor_task=task_2,
        status=status
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.post(
        f'/workflows/{workflow.id}/return-to',
        data={
            'task': task_1.id
        }
    )

    # assert
    assert response.status_code == 400
    assert response.data['message'] == messages.MSG_PW_0071
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    workflow.refresh_from_db()
    assert workflow.current_task == 2


def test_return_to__sub_workflow_completed__ok(
    api_client,
):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user=user, tasks_count=2)
    workflow.current_task = 2
    workflow.save()
    task_1 = workflow.tasks.get(number=1)
    task_1.is_completed = True
    task_1.date_completed = timezone.now()
    task_1.save()
    task_2 = workflow.tasks.get(number=2)

    create_test_workflow(
        user=user,
        tasks_count=1,
        ancestor_task=task_2,
        status=WorkflowStatus.DONE
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.post(
        path=f'/workflows/{workflow.id}/return-to',
        data={
            'task': task_1.id
        }
    )

    # assert
    assert response.status_code == 204
    workflow.refresh_from_db()
    assert workflow.current_task == 1
