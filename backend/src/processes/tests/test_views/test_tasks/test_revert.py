import pytest

from src.authentication.enums import AuthTokenType
from src.authentication.services.guest_auth import GuestJWTAuthService
from src.processes.enums import (
    ConditionAction,
    DirectlyStatus,
    FieldType,
    PredicateOperator,
    PredicateType,
    TaskStatus,
    WorkflowStatus,
)
from src.processes.messages import workflow as messages
from src.processes.models.workflows.conditions import (
    Condition,
    Predicate,
    Rule,
)
from src.processes.models.workflows.fields import TaskField
from src.processes.models.workflows.task import TaskPerformer
from src.processes.services.exceptions import (
    WorkflowActionServiceException,
)
from src.processes.services.workflow_action import (
    WorkflowActionService,
)
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_guest,
    create_test_not_admin,
    create_test_owner,
    create_test_workflow,
)
from src.utils.validation import ErrorCode

pytestmark = pytest.mark.django_db


def test_revert__account_owner__ok(
    api_client,
    mocker,
):
    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(
        user=owner,
        tasks_count=2,
        active_task_number=2,
    )
    task_2 = workflow.tasks.get(number=2)
    service_init_mock = mocker.patch.object(
        WorkflowActionService,
        attribute='__init__',
        return_value=None,
    )
    service_revert_mock = mocker.patch(
        'src.processes.services.workflow_action.'
        'WorkflowActionService.revert',
    )
    api_client.token_authenticate(owner)
    text_comment = 'text_comment'

    # act
    response = api_client.post(
        f'/v2/tasks/{task_2.id}/revert',
        data={
            'comment': text_comment,
        },
    )

    # assert
    assert response.status_code == 204
    service_init_mock.assert_called_once_with(
        workflow=workflow,
        user=owner,
        auth_type=AuthTokenType.USER,
        is_superuser=False,
    )
    service_revert_mock.assert_called_once_with(
        revert_from_task=task_2,
        comment=text_comment,
    )


def test_revert__user_performer__ok(
    api_client,
    mocker,
):
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(
        user=owner,
        tasks_count=2,
        active_task_number=2,
    )
    task_2 = workflow.tasks.get(number=2)
    performer = create_test_not_admin(account=account)
    TaskPerformer.objects.create(
        task_id=task_2.id,
        user_id=performer.id,
    )
    service_init_mock = mocker.patch.object(
        WorkflowActionService,
        attribute='__init__',
        return_value=None,
    )
    service_revert_mock = mocker.patch(
        'src.processes.services.workflow_action.'
        'WorkflowActionService.revert',
    )
    api_client.token_authenticate(performer)
    text_comment = 'text_comment'

    # act
    response = api_client.post(
        f'/v2/tasks/{task_2.id}/revert',
        data={
            'comment': text_comment,
        },
    )

    # assert
    assert response.status_code == 204
    service_init_mock.assert_called_once_with(
        workflow=workflow,
        user=performer,
        auth_type=AuthTokenType.USER,
        is_superuser=False,
    )
    service_revert_mock.assert_called_once_with(
        revert_from_task=task_2,
        comment=text_comment,
    )


def test_revert__deleted_performer__permission_denied(
    api_client,
    mocker,
):
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(
        user=owner,
        tasks_count=2,
        active_task_number=2,
    )
    task_2 = workflow.tasks.get(number=2)
    performer = create_test_not_admin(account=account)
    TaskPerformer.objects.create(
        task_id=task_2.id,
        user_id=performer.id,
        directly_status=DirectlyStatus.DELETED,
    )
    service_init_mock = mocker.patch.object(
        WorkflowActionService,
        attribute='__init__',
        return_value=None,
    )
    service_revert_mock = mocker.patch(
        'src.processes.services.workflow_action.'
        'WorkflowActionService.revert',
    )
    api_client.token_authenticate(performer)
    text_comment = 'text_comment'

    # act
    response = api_client.post(
        f'/v2/tasks/{task_2.id}/revert',
        data={
            'comment': text_comment,
        },
    )

    # assert
    assert response.status_code == 403
    service_init_mock.assert_not_called()
    service_revert_mock.assert_not_called()


def test_revert__user_not_performer__permission_denied(
    api_client,
    mocker,
):
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(
        user=owner,
        tasks_count=2,
        active_task_number=2,
    )
    task_2 = workflow.tasks.get(number=2)
    performer = create_test_not_admin(account=account)
    service_init_mock = mocker.patch.object(
        WorkflowActionService,
        attribute='__init__',
        return_value=None,
    )
    service_revert_mock = mocker.patch(
        'src.processes.services.workflow_action.'
        'WorkflowActionService.revert',
    )
    api_client.token_authenticate(performer)
    text_comment = 'text_comment'

    # act
    response = api_client.post(
        f'/v2/tasks/{task_2.id}/revert',
        data={
            'comment': text_comment,
        },
    )

    # assert
    assert response.status_code == 403
    service_init_mock.assert_not_called()
    service_revert_mock.assert_not_called()


def test_revert__guest_performer__permission_denied(
    mocker,
    api_client,
):
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(
        owner,
        tasks_count=2,
        active_task_number=2,
    )
    task_2 = workflow.tasks.get(number=2)

    guest = create_test_guest(account=account)
    TaskPerformer.objects.create(
        task_id=task_2.id,
        user_id=guest.id,
    )
    str_token = GuestJWTAuthService.get_str_token(
        task_id=task_2.id,
        user_id=guest.id,
        account_id=account.id,
    )
    service_revert_mock = mocker.patch(
        'src.processes.services.workflow_action.'
        'WorkflowActionService.revert',
    )
    text_comment = 'text_comment'

    # act
    response = api_client.post(
        path=f'/v2/tasks/{task_2.id}/revert',
        data={
            'comment': text_comment,
        },
        **{'X-Guest-Authorization': str_token},
    )

    # assert
    assert response.status_code == 403
    service_revert_mock.assert_not_called()


def test_revert__service_exception__validation_error(
    api_client,
    mocker,
):
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(
        owner,
        tasks_count=2,
        active_task_number=2,
    )
    task_2 = workflow.tasks.get(number=2)

    service_init_mock = mocker.patch.object(
        WorkflowActionService,
        attribute='__init__',
        return_value=None,
    )
    message = 'Some message'
    ex = WorkflowActionServiceException(message)
    service_revert_mock = mocker.patch(
        'src.processes.services.workflow_action.'
        'WorkflowActionService.revert',
        side_effect=ex,
    )
    api_client.token_authenticate(owner)
    text_comment = 'text_comment'

    # act
    response = api_client.post(
        path=f'/v2/tasks/{task_2.id}/revert',
        data={
            'comment': text_comment,
        },
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    service_init_mock.assert_called_once_with(
        workflow=workflow,
        user=owner,
        auth_type=AuthTokenType.USER,
        is_superuser=False,
    )
    service_revert_mock.assert_called_once_with(
        revert_from_task=task_2,
        comment=text_comment,
    )


@pytest.mark.parametrize('text_comment', ('', '   '))
def test_revert__invalid_comment__validation_error(
    api_client,
    mocker,
    text_comment,
):
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(
        owner,
        tasks_count=2,
        active_task_number=2,
    )
    task_2 = workflow.tasks.get(number=2)
    service_init_mock = mocker.patch(
        'src.processes.services.workflow_action.'
        'WorkflowActionService',
    )
    service_revert_mock = mocker.patch(
        'src.processes.services.workflow_action.'
        'WorkflowActionService.revert',
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.post(
        path=f'/v2/tasks/{task_2.id}/revert',
        data={
            'comment': text_comment,
        },
    )

    # assert
    assert response.status_code == 400
    assert response.data['message'] == messages.MSG_PW_0083
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    service_init_mock.assert_not_called()
    service_revert_mock.assert_not_called()


def test_revert__start_multiple_tasks__ok(api_client):
    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(
        user=owner,
        tasks_count=4,
        active_task_number=3,
    )
    task_1 = workflow.tasks.get(number=1)
    task_2 = workflow.tasks.get(number=2)
    task_2.conditions.all().delete()
    task_2.parents = []
    task_2.save()
    task_3 = workflow.tasks.get(number=3)
    task_3.conditions.all().delete()
    condition = Condition.objects.create(
        task=task_3,
        action=ConditionAction.START_TASK,
        order=0,
    )
    rule = Rule.objects.create(
        condition=condition,
    )
    Predicate.objects.create(
        rule=rule,
        operator=PredicateOperator.COMPLETED,
        field_type=PredicateType.TASK,
        field=task_1.api_name,
        value=None,
    )
    Predicate.objects.create(
        rule=rule,
        operator=PredicateOperator.COMPLETED,
        field_type=PredicateType.TASK,
        field=task_2.api_name,
        value=None,
    )
    task_3.parents = [task_1.api_name, task_2.api_name]
    task_3.save()
    api_client.token_authenticate(owner)
    text_comment = 'text_comment'

    # act
    response = api_client.post(
        f'/v2/tasks/{task_3.id}/revert',
        data={
            'comment': text_comment,
        },
    )

    # assert
    assert response.status_code == 204
    workflow.refresh_from_db()
    assert workflow.status == WorkflowStatus.RUNNING
    task_3.refresh_from_db()
    assert task_3.status == TaskStatus.PENDING
    task_2.refresh_from_db()
    assert task_2.status == TaskStatus.ACTIVE
    task_1.refresh_from_db()
    assert task_1.status == TaskStatus.ACTIVE


def test_revert__to_first_skipped_task__validation_error(api_client):

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(
        user=owner,
        tasks_count=2,
        active_task_number=2,
    )
    task_1 = workflow.tasks.get(number=1)
    task_1.status = TaskStatus.SKIPPED
    task_1.save()
    field = TaskField.objects.create(
        kickoff=workflow.kickoff_instance,
        name='Skip task 1',
        api_name='field-1',
        type=FieldType.STRING,
        workflow=workflow,
        value='Yes',
        account=owner.account,
    )
    condition = Condition.objects.create(
        task=task_1,
        action=ConditionAction.SKIP_TASK,
        order=0,
    )
    rule = Rule.objects.create(
        condition=condition,
    )
    Predicate.objects.create(
        rule=rule,
        operator=PredicateOperator.EQUAL,
        field_type=PredicateType.STRING,
        field=field.api_name,
        value='Yes',
    )
    api_client.token_authenticate(owner)
    text_comment = 'text_comment'
    task_2 = workflow.tasks.get(number=2)

    # act
    response = api_client.post(
        f'/v2/tasks/{task_2.id}/revert',
        data={
            'comment': text_comment,
        },
    )

    # assert
    assert response.status_code == 400
    assert response.data['message'] == messages.MSG_PW_0079(task_1.name)
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    workflow.refresh_from_db()
    assert workflow.status == WorkflowStatus.RUNNING
    task_2.refresh_from_db()
    assert task_2.status == TaskStatus.ACTIVE
    task_1.refresh_from_db()
    assert task_1.status == TaskStatus.SKIPPED


def test_revert__all_tasks_skipped__validation_error(api_client):

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(
        user=owner,
        tasks_count=3,
        active_task_number=3,
    )
    # Skip task 1
    task_1 = workflow.tasks.get(number=1)
    task_1.status = TaskStatus.SKIPPED
    task_1.save()
    field = TaskField.objects.create(
        task=task_1,
        name='Skip task 1',
        api_name='field-1',
        type=FieldType.STRING,
        workflow=workflow,
        value='Yes',
        account=owner.account,
    )
    condition = Condition.objects.create(
        task=task_1,
        action=ConditionAction.SKIP_TASK,
        order=0,
    )
    rule = Rule.objects.create(
        condition=condition,
    )
    Predicate.objects.create(
        rule=rule,
        operator=PredicateOperator.EQUAL,
        field_type=PredicateType.STRING,
        field=field.api_name,
        value='Yes',
    )

    # Skip task 2
    task_2 = workflow.tasks.get(number=2)
    task_2.status = TaskStatus.SKIPPED
    task_2.save()
    field_2 = TaskField.objects.create(
        task=task_2,
        name='Skip task 2',
        api_name='field-2',
        type=FieldType.STRING,
        workflow=workflow,
        value='Yes',
        account=owner.account,
    )
    condition_2 = Condition.objects.create(
        task=task_2,
        action=ConditionAction.SKIP_TASK,
        order=0,
    )
    rule_2 = Rule.objects.create(
        condition=condition_2,
    )
    Predicate.objects.create(
        rule=rule_2,
        operator=PredicateOperator.EQUAL,
        field_type=PredicateType.STRING,
        field=field_2.api_name,
        value='Yes',
    )
    task_3 = workflow.tasks.get(number=3)
    api_client.token_authenticate(owner)
    text_comment = 'text_comment'

    # act
    response = api_client.post(
        f'/v2/tasks/{task_3.id}/revert',
        data={
            'comment': text_comment,
        },
    )

    # assert
    assert response.status_code == 400
    assert response.data['message'] == messages.MSG_PW_0080(task_2.name)
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    workflow.refresh_from_db()
    assert workflow.status == WorkflowStatus.RUNNING
    task_3.refresh_from_db()
    assert task_3.status == TaskStatus.ACTIVE
    task_2.refresh_from_db()
    assert task_2.status == TaskStatus.SKIPPED
    task_1.refresh_from_db()
    assert task_1.status == TaskStatus.SKIPPED
