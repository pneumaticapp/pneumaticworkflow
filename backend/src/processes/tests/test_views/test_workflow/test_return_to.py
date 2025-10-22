from datetime import timedelta

import pytest
from django.utils import timezone

from src.authentication.enums import AuthTokenType
from src.processes.enums import (
    ConditionAction,
    FieldType,
    PredicateOperator,
    WorkflowStatus,
)
from src.processes.messages import workflow as messages
from src.processes.models.templates.conditions import (
    ConditionTemplate,
    PredicateTemplate,
    RuleTemplate,
)
from src.processes.models.templates.fields import (
    FieldTemplate,
    FieldTemplateSelection,
)
from src.processes.models.workflows.task import Delay
from src.processes.models.workflows.workflow import Workflow
from src.processes.services.exceptions import (
    WorkflowActionServiceException,
)
from src.processes.services.workflow_action import (
    WorkflowActionService,
)
from src.processes.tests.fixtures import (
    create_task_returned_webhook,
    create_test_account,
    create_test_admin,
    create_test_owner,
    create_test_template,
    create_test_user,
    create_test_workflow,
)
from src.utils.validation import ErrorCode

pytestmark = pytest.mark.django_db


def test_return_to__by_task_id__ok(
    api_client,
    mocker,
):
    # arrange
    user = create_test_user(is_account_owner=True)
    workflow = create_test_workflow(
        user=user,
        tasks_count=3,
        active_task_number=3,
    )
    task_1 = workflow.tasks.get(number=1)
    service_init_mock = mocker.patch.object(
        WorkflowActionService,
        attribute='__init__',
        return_value=None,
    )
    service_revert_mock = mocker.patch(
        'src.processes.services.workflow_action.'
        'WorkflowActionService.return_to',
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        f'/workflows/{workflow.id}/return-to',
        data={'task_api_name': task_1.api_name},
    )

    # assert
    assert response.status_code == 204
    service_init_mock.assert_called_once_with(
        workflow=workflow,
        user=user,
        auth_type=AuthTokenType.USER,
        is_superuser=False,
    )
    service_revert_mock.assert_called_once_with(
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
        tasks_count=3,
        active_task_number=3,
    )
    workflow.save()
    task_1 = workflow.tasks.get(number=1)
    service_init_mock = mocker.patch.object(
        WorkflowActionService,
        attribute='__init__',
        return_value=None,
    )
    service_revert_mock = mocker.patch(
        'src.processes.services.workflow_action.'
        'WorkflowActionService.return_to',
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        f'/workflows/{workflow.id}/return-to',
        data={'task_api_name': task_1.api_name},
    )

    # assert
    assert response.status_code == 204
    service_init_mock.assert_called_once_with(
        workflow=workflow,
        user=user,
        auth_type=AuthTokenType.USER,
        is_superuser=False,
    )
    service_revert_mock.assert_called_once_with(
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
        tasks_count=3,
    )
    service_init_mock = mocker.patch.object(
        WorkflowActionService,
        attribute='__init__',
        return_value=None,
    )
    service_revert_mock = mocker.patch(
        'src.processes.services.workflow_action.'
        'WorkflowActionService.return_to',
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
        return_value=None,
    )
    service_revert_mock = mocker.patch(
        'src.processes.services.workflow_action.'
        'WorkflowActionService.return_to',
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        f'/workflows/{workflow.id}/return-to',
        data={'task_api_name': another_task.api_name},
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
        tasks_count=3,
        active_task_number=3,
    )
    task_1 = workflow.tasks.get(number=1)
    service_init_mock = mocker.patch.object(
        WorkflowActionService,
        attribute='__init__',
        return_value=None,
    )
    message = 'Some message'
    ex = WorkflowActionServiceException(message)
    service_revert_mock = mocker.patch(
        'src.processes.services.workflow_action.'
        'WorkflowActionService.return_to',
        side_effect=ex,
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        f'/workflows/{workflow.id}/return-to',
        data={'task_api_name': task_1.api_name},
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    service_init_mock.assert_called_once_with(
        workflow=workflow,
        user=user,
        auth_type=AuthTokenType.USER,
        is_superuser=False,
    )
    service_revert_mock.assert_called_once_with(
        revert_to_task=task_1,
    )


# TODO Deprecated old style tests


def test_return_to__ok(mocker, api_client):

    # arrange
    user = create_test_user()
    create_task_returned_webhook(user)
    workflow = create_test_workflow(user, tasks_count=3)
    task_1 = workflow.tasks.get(number=1)
    api_client.token_authenticate(user)

    response_complete_1 = api_client.post(f'/v2/tasks/{task_1.id}/complete')
    task_2 = workflow.tasks.get(number=2)
    response_complete_2 = api_client.post(f'/v2/tasks/{task_2.id}/complete')

    workflow.refresh_from_db()

    send_removed_task_notification_mock = mocker.patch(
        'src.notifications.tasks'
        '.send_removed_task_notification.delay',
    )
    delete_task_guest_cache_mock = mocker.patch(
        'src.authentication.services.guest_auth.'
        'GuestJWTAuthService.delete_task_guest_cache',
    )
    send_new_task_notification_mock = mocker.patch(
        'src.processes.services.workflow_action.'
        'send_new_task_notification.delay',
    )
    mocker.patch(
        'src.processes.tasks.webhooks.'
        'send_workflow_started_webhook.delay',
    )
    mocker.patch(
        'src.processes.tasks.webhooks.'
        'send_task_completed_webhook.delay',
    )
    webhook_payload = mocker.Mock()
    mocker.patch(
        'src.processes.models.workflows.task.Task'
        '.webhook_payload',
        return_value=webhook_payload,
    )
    revert_task_webhook_mock = mocker.patch(
        'src.processes.tasks.webhooks.'
        'send_task_returned_webhook.delay',
    )
    revert_workflow_event_mock = mocker.patch(
        'src.processes.services.workflow_action.'
        'WorkflowEventService.workflow_revert_event',
    )
    start_workflow_event_mock = mocker.patch(
        'src.processes.services.workflow_action.'
        'WorkflowEventService.task_started_event',
    )
    analysis_return_workflow_mock = mocker.patch(
        'src.processes.services.workflow_action.'
        'AnalyticService.workflow_returned',
    )

    # act
    response = api_client.post(
        path=f'/workflows/{workflow.id}/return-to',
        data={'task_api_name': task_1.api_name},
    )

    # assert
    assert response_complete_1.status_code == 200
    assert response_complete_2.status_code == 200
    assert response.status_code == 204
    task_1.refresh_from_db()
    assert task_1.is_active
    task_2.refresh_from_db()
    assert task_2.is_pending
    send_removed_task_notification_mock.assert_called_once()
    send_new_task_notification_mock.assert_called_once()
    analysis_return_workflow_mock.assert_called_once_with(
        user=user,
        task=task_1,
        workflow=workflow,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    delete_task_guest_cache_mock.assert_called_once_with(
        task_id=task_2.id,
    )
    revert_task_webhook_mock.assert_called_once_with(
        user_id=user.id,
        account_id=user.account_id,
        payload=webhook_payload,
    )
    task_3 = workflow.tasks.get(number=3)
    assert task_3.is_pending
    revert_workflow_event_mock.assert_called_once_with(
        task=task_3,
        user=user,
    )
    start_workflow_event_mock.assert_called_once_with(task_1)


def test_return_to__task_with_delay__reset_delay(
    mocker,
    api_client,
):
    """ https://trello.com/c/8rbbGOcp """

    # arrange
    mocker.patch(
        'src.processes.tasks.webhooks.'
        'send_workflow_started_webhook.delay',
    )
    mocker.patch(
        'src.processes.tasks.webhooks.'
        'send_task_completed_webhook.delay',
    )
    mocker.patch(
        'src.processes.tasks.webhooks.'
        'send_task_returned_webhook.delay',
    )
    user = create_test_owner()
    workflow = create_test_workflow(user)
    task_1 = workflow.tasks.get(number=1)
    task_2 = workflow.tasks.get(number=2)
    delay = Delay.objects.create(
        task=task_2,
        duration=timedelta(seconds=10),
        workflow=workflow,
    )

    api_client.token_authenticate(user)
    response_complete = api_client.post(f'/v2/tasks/{task_1.id}/complete')
    response_resume = api_client.post(f'/workflows/{workflow.id}/resume')

    # act
    response = api_client.post(
        f'/workflows/{workflow.id}/return-to',
        data={'task_api_name': task_1.api_name},
    )

    # assert
    assert response_complete.status_code == 200
    assert response_resume.status_code == 200
    assert response.status_code == 204

    task_1.refresh_from_db()
    assert task_1.is_active
    assert task_1.date_completed is None
    assert task_1.date_first_started

    task_2.refresh_from_db()
    assert task_2.is_pending
    delay.refresh_from_db()
    assert delay.end_date is None
    assert delay.start_date is None
    assert delay.estimated_end_date is None

    task_3 = workflow.tasks.get(number=3)
    assert task_3.is_pending


def test_return_to__skip_condition__validation_error(
    api_client,
    mocker,
):
    # arrange
    mocker.patch(
        'src.processes.tasks.webhooks.'
        'send_workflow_started_webhook.delay',
    )
    mocker.patch(
        'src.processes.tasks.webhooks.'
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
    template_task_1 = template.tasks.get(number=1)
    template_task_2 = template.tasks.get(number=2)
    condition_template = ConditionTemplate.objects.create(
        task=template_task_1,
        action=ConditionAction.SKIP_TASK,
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
        task=template_task_2,
        action=ConditionAction.SKIP_TASK,
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
            'kickoff': {
                field_template.api_name: user.id,
            },
        },
    )
    workflow = Workflow.objects.get(id=response.data['id'])
    task_1 = workflow.tasks.get(number=1)

    # act
    response = api_client.post(
        f'/workflows/{workflow.id}/return-to',
        data={'task_api_name': task_1.api_name},
    )

    # assert
    assert response.status_code == 400
    assert response.data['message'] == messages.MSG_PW_0079(task_1.name)
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    workflow.refresh_from_db()
    assert workflow.status == WorkflowStatus.RUNNING
    task_1.refresh_from_db()
    assert task_1.is_skipped
    task_2 = workflow.tasks.get(number=2)
    assert task_2.is_skipped
    task_3 = workflow.tasks.get(number=3)
    assert task_3.is_active


def test_return_to__force_snooze_and_return_to__snooze_not_running_again(
    mocker,
    api_client,
):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user, tasks_count=2)
    api_client.token_authenticate(user)
    task_1 = workflow.tasks.get(number=1)

    mocker.patch(
        'src.processes.tasks.webhooks.'
        'send_task_returned_webhook.delay',
    )
    mocker.patch(
        'src.processes.tasks.webhooks.'
        'send_task_completed_webhook.delay',
    )

    response_complete = api_client.post(f'/v2/tasks/{task_1.id}/complete')
    workflow.refresh_from_db()

    mocker.patch(
        'src.notifications.tasks'
        '.send_removed_task_notification.delay',
    )
    mocker.patch(
        'src.processes.services.workflow_action.'
        'send_new_task_notification.delay',
    )
    mocker.patch(
        'src.authentication.services.guest_auth.'
        'GuestJWTAuthService.delete_task_guest_cache',
    )
    date = timezone.now() + timedelta(days=1)

    response_snooze = api_client.post(
        f'/workflows/{workflow.id}/snooze',
        data={'date': date.timestamp()},
    )
    workflow.refresh_from_db()

    response_return_to = api_client.post(
        f'/workflows/{workflow.id}/return-to',
        data={'task_api_name': task_1.api_name},
    )
    workflow.refresh_from_db()
    task_1 = workflow.tasks.get(number=1)

    # act
    response_complete_2 = api_client.post(f'/v2/tasks/{task_1.id}/complete')

    # assert
    assert response_complete.status_code == 200
    assert response_snooze.status_code == 200
    assert response_return_to.status_code == 204
    assert response_complete_2.status_code == 200
    workflow.refresh_from_db()
    assert workflow.status == WorkflowStatus.RUNNING


def test_return_to__force_snooze_and_resume__snooze_not_running_again(
    mocker,
    api_client,
):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user, tasks_count=2)
    api_client.token_authenticate(user)
    task_1 = workflow.tasks.get(number=1)
    mocker.patch(
        'src.processes.tasks.webhooks.'
        'send_task_returned_webhook.delay',
    )
    mocker.patch(
        'src.processes.tasks.webhooks.'
        'send_task_completed_webhook.delay',
    )
    response_complete = api_client.post(f'/v2/tasks/{task_1.id}/complete')
    workflow.refresh_from_db()

    mocker.patch(
        'src.notifications.tasks'
        '.send_removed_task_notification.delay',
    )
    mocker.patch(
        'src.processes.services.workflow_action.'
        'send_new_task_notification.delay',
    )
    mocker.patch(
        'src.authentication.services.guest_auth.'
        'GuestJWTAuthService.delete_task_guest_cache',
    )
    date = timezone.now() + timedelta(days=1)

    response_snooze = api_client.post(
        f'/workflows/{workflow.id}/snooze',
        data={'date': date.timestamp()},
    )
    workflow.refresh_from_db()
    response_resume = api_client.post(f'/workflows/{workflow.id}/resume')

    response_return_to = api_client.post(
        f'/workflows/{workflow.id}/return-to',
        data={'task_api_name': task_1.api_name},
    )
    workflow.refresh_from_db()

    # act
    response_complete_2 = api_client.post(f'/v2/tasks/{task_1.id}/complete')

    # assert
    assert response_complete.status_code == 200
    assert response_snooze.status_code == 200
    assert response_resume.status_code == 200
    assert response_return_to.status_code == 204
    assert response_complete_2.status_code == 200
    workflow.refresh_from_db()
    assert workflow.status == WorkflowStatus.RUNNING


def test_return_to__task_skipped_by_kickoff_field__update_status_to_pending(
    mocker,
    api_client,
):

    # arrange
    mocker.patch(
        'src.processes.tasks.webhooks.'
        'send_workflow_started_webhook.delay',
    )
    mocker.patch(
        'src.processes.tasks.webhooks.'
        'send_task_returned_webhook.delay',
    )
    mocker.patch(
        'src.notifications.tasks'
        '.send_new_task_notification.delay',
    )
    mocker.patch(
        'src.notifications.tasks'
        '.send_removed_task_notification.delay',
    )
    mocker.patch(
        'src.authentication.services.guest_auth.'
        'GuestJWTAuthService.delete_task_guest_cache',
    )
    mocker.patch(
        'src.processes.services.workflow_action.'
        'send_new_task_notification.delay',
    )
    account = create_test_account()
    create_test_owner(account=account)
    user = create_test_admin(account=account)
    # Specific performer for second step
    user_2 = create_test_admin(
        email='performer_2_task@test.test',
        account=account,
    )
    template = create_test_template(
        user=user,
        is_active=True,
        tasks_count=3,
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
        action=ConditionAction.SKIP_TASK,
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
                field_template.api_name: [selection_template.api_name],
            },
        },
    )

    workflow = Workflow.objects.get(id=response_run.data['id'])
    task_1 = workflow.tasks.get(number=1)

    response_complete = api_client.post(f'/v2/tasks/{task_1.id}/complete')

    # now third task is current

    # act
    response_return = api_client.post(
        path=f'/workflows/{workflow.id}/return-to',
        data={'task_api_name': task_1.api_name},
    )

    # assert
    assert response_complete.status_code == 200
    assert response_run.status_code == 200
    assert response_return.status_code == 204

    workflow.refresh_from_db()
    task_1.refresh_from_db()
    assert task_1.is_active
    task_2 = workflow.tasks.get(number=2)
    assert task_2.is_pending
    assert task_2.taskperformer_set.count() == 0
    task_3 = workflow.tasks.get(number=3)
    assert task_3.is_pending


def test_return_to__completed_workflow__ok(
    mocker,
    api_client,
):

    # arrange
    user = create_test_user()
    create_task_returned_webhook(user)
    workflow = create_test_workflow(user, tasks_count=1)
    task_1 = workflow.tasks.get(number=1)
    api_client.token_authenticate(user)

    response_complete = api_client.post(f'/v2/tasks/{task_1.id}/complete')

    delete_task_guest_cache_mock = mocker.patch(
        'src.authentication.services.guest_auth.'
        'GuestJWTAuthService.delete_task_guest_cache',
    )
    send_new_task_notification_mock = mocker.patch(
        'src.processes.services.workflow_action.'
        'send_new_task_notification.delay',
    )
    mocker.patch(
        'src.processes.tasks.webhooks.'
        'send_workflow_started_webhook.delay',
    )
    webhook_payload = mocker.Mock()
    mocker.patch(
        'src.processes.models.workflows.task.Task'
        '.webhook_payload',
        return_value=webhook_payload,
    )
    revert_task_webhook_mock = mocker.patch(
        'src.processes.tasks.webhooks.'
        'send_task_returned_webhook.delay',
    )
    send_removed_task_notification_mock = mocker.patch(
        'src.notifications.tasks'
        '.send_removed_task_notification.delay',
    )

    # act
    response = api_client.post(
        path=f'/workflows/{workflow.id}/return-to',
        data={'task_api_name': task_1.api_name},
    )

    # assert
    assert response_complete.status_code == 200
    assert response.status_code == 204
    workflow.refresh_from_db()
    assert workflow.is_running
    task_1.refresh_from_db()
    assert task_1.is_active
    send_removed_task_notification_mock.assert_not_called()
    send_new_task_notification_mock.assert_called_once()
    delete_task_guest_cache_mock.assert_not_called()
    revert_task_webhook_mock.assert_called_once()


@pytest.mark.parametrize('status', WorkflowStatus.RUNNING_STATUSES)
def test_return_to__sub_workflow_incompleted__validation_error(
    status,
    api_client,
):
    # arrange
    user = create_test_user()
    workflow = create_test_workflow(
        user=user,
        tasks_count=2,
        active_task_number=2,
    )
    task_1 = workflow.tasks.get(number=1)
    task_2 = workflow.tasks.get(number=2)
    create_test_workflow(
        user=user,
        tasks_count=1,
        ancestor_task=task_2,
        status=status,
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.post(
        f'/workflows/{workflow.id}/return-to',
        data={'task_api_name': task_1.api_name},
    )

    # assert
    assert response.status_code == 400
    assert response.data['message'] == messages.MSG_PW_0071
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    task_1.refresh_from_db()
    assert task_1.is_completed
    task_2.refresh_from_db()
    assert task_2.is_active


def test_return_to__sub_workflow_completed__ok(api_client):

    # arrange
    user = create_test_owner()
    workflow = create_test_workflow(
        user=user,
        tasks_count=2,
        active_task_number=2,
    )
    task_1 = workflow.tasks.get(number=1)
    task_2 = workflow.tasks.get(number=2)
    create_test_workflow(
        user=user,
        tasks_count=1,
        ancestor_task=task_2,
        status=WorkflowStatus.DONE,
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.post(
        path=f'/workflows/{workflow.id}/return-to',
        data={'task_api_name': task_1.api_name},
    )

    # assert
    assert response.status_code == 204
    task_1.refresh_from_db()
    assert task_1.is_active
    task_2.refresh_from_db()
    assert task_2.is_pending
