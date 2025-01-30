# pylint:disable=redefined-outer-name
import pytest
from django.utils import timezone

from pneumatic_backend.authentication.enums import AuthTokenType
from pneumatic_backend.processes.models import (
    Workflow,
    FieldTemplate,
    ConditionTemplate,
    RuleTemplate,
    PredicateTemplate,
    FileAttachment,
    Template,
)
from pneumatic_backend.accounts.enums import (
    BillingPlanType
)
from pneumatic_backend.processes.services.exceptions import \
    WorkflowActionServiceException
from pneumatic_backend.processes.services.workflow_action import (
    WorkflowActionService
)
from pneumatic_backend.processes.tests.fixtures import (
    create_test_workflow,
    create_test_user,
    create_test_template,
    create_test_account,
)
from pneumatic_backend.processes.messages import workflow as messages
from pneumatic_backend.utils.validation import ErrorCode
from pneumatic_backend.processes.api_v2.services.task.performers import (
    TaskPerformersService
)
from pneumatic_backend.processes.enums import (
    PerformerType,
    PredicateOperator,
    FieldType,
    WorkflowStatus,
)


pytestmark = pytest.mark.django_db


def test_revert__ok(
    api_client,
    mocker,
):
    # arrange
    user = create_test_user(is_account_owner=True)
    workflow = create_test_workflow(
        user=user,
        tasks_count=2
    )
    workflow.current_task = 2
    workflow.save()
    service_init_mock = mocker.patch.object(
        WorkflowActionService,
        attribute='__init__',
        return_value=None
    )
    service_revert_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action.'
        'WorkflowActionService.revert'
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        f'/workflows/{workflow.id}/task-revert',
    )

    # assert
    assert response.status_code == 204
    service_init_mock.assert_called_once_with(
        user=user,
        auth_type=AuthTokenType.USER,
        is_superuser=False
    )
    service_revert_mock.assert_called_once_with(workflow)


def test_revert_service_exception__validation_error(
    api_client,
    mocker,
):
    # arrange
    user = create_test_user(is_account_owner=True)
    workflow = create_test_workflow(
        user=user,
        tasks_count=2
    )
    workflow.current_task = 2
    workflow.save()
    service_init_mock = mocker.patch.object(
        WorkflowActionService,
        attribute='__init__',
        return_value=None
    )
    message = 'Some message'
    ex = WorkflowActionServiceException(message)
    service_revert_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action.'
        'WorkflowActionService.revert',
        side_effect=ex,
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        f'/workflows/{workflow.id}/task-revert',
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
    service_revert_mock.assert_called_once_with(workflow)


# TODO Deprecated old style tests


def test_revert__skip_task_condition_true__before_previous_task(
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
        'send_task_completed_webhook.delay',
    )
    mocker.patch(
        'pneumatic_backend.processes.tasks.webhooks.'
        'send_task_returned_webhook.delay',
    )
    user = create_test_user()
    template = create_test_template(
        user=user,
        is_active=True
    )
    task = template.tasks.order_by('number').first()
    output_field = FieldTemplate.objects.create(
        type=FieldType.TEXT,
        name='Past name',
        description='Last description',
        task=task,
        template=template,
    )
    output_file = FieldTemplate.objects.create(
        type=FieldType.FILE,
        name='File field',
        task=task,
        template=template,
    )
    task.save()
    second_task = template.tasks.order_by('number')[1]
    condition_template = ConditionTemplate.objects.create(
        task=second_task,
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
        field_type=FieldType.TEXT,
        field=output_field.api_name,
        value='JOHN CENA',
        template=template,
    )
    PredicateTemplate.objects.create(
        rule=rule_1,
        operator=PredicateOperator.EXIST,
        field_type=FieldType.FILE,
        field=output_file.api_name,
        value='456',
        template=template,
    )
    third_task = template.tasks.order_by('number')[2]
    third_task.description = (
        'His name is... {{ %s }}!!! Third link {{ %s }}'
        % (output_field.api_name, output_file.api_name)
    )
    third_task.save()

    api_client.token_authenticate(user=user)
    response = api_client.post(
        f'/templates/{template.id}/run',
    )
    workflow = Workflow.objects.get(id=response.data['id'])

    first_file = FileAttachment.objects.create(
        name='john.cena',
        url='https://john.cena/john.cena',
        size=1488,
        account_id=user.account_id
    )
    second_file = FileAttachment.objects.create(
        name='john1.cena',
        url='https://john.cena/john1.cena',
        size=1337,
        account_id=user.account_id,
    )

    data = {
        'task_id': workflow.current_task_instance.id,
        'output': {
            output_field.api_name: 'JOHN CENA',
            output_file.api_name: [first_file.id, second_file.id]
        }
    }
    api_client.post(
        f'/workflows/{workflow.id}/task-complete',
        data=data,
    )
    workflow.refresh_from_db()
    third_description = workflow.current_task_instance.description
    third_name = workflow.current_task_instance.name

    # act
    response = api_client.post(
        f'/workflows/{workflow.id}/task-revert',
    )

    # assert
    assert response.status_code == 204
    workflow.refresh_from_db()
    assert workflow.current_task == 1
    third_task = workflow.tasks.get(number=3)
    assert third_task.description == third_description
    assert third_task.name == third_name


def test_revert__skipped_task__not_completed(
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
        'send_task_completed_webhook.delay',
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

    value = 'Skip second task'
    field_template = FieldTemplate.objects.create(
        name='Skip second task',
        is_required=True,
        type=FieldType.TEXT,
        description='Last description',
        kickoff=template.kickoff_instance,
        template=template,
    )
    condition_template = ConditionTemplate.objects.create(
        task=task_template_2,
        action=ConditionTemplate.SKIP_TASK,
        order=0,
        template=template,
    )
    rule = RuleTemplate.objects.create(
        condition=condition_template,
        template=template,
    )
    PredicateTemplate.objects.create(
        rule=rule,
        operator=PredicateOperator.EQUAL,
        field_type=FieldType.TEXT,
        field=field_template.api_name,
        value=value,
        template=template,
    )

    api_client.token_authenticate(user=user)

    # Run with flag for skip second task
    response_run = api_client.post(
        f'/templates/{template.id}/run',
        data={
            'name': 'Test name',
            'kickoff': {
                field_template.api_name: value
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
    response_revert = api_client.post(
        f'/workflows/{workflow.id}/task-revert',
    )

    # assert
    assert response_run.status_code == 200
    assert response_complete.status_code == 204
    assert response_revert.status_code == 204
    workflow.refresh_from_db()
    assert workflow.current_task == 1
    task_2 = workflow.tasks.get(number=2)
    assert task_2.is_skipped is False
    assert task_2.is_completed is False
    assert task_2.date_completed is None
    assert task_2.taskperformer_set.count() == 0


def test_revert__skip_first_task_condition_true__raise(
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

    # act
    response = api_client.post(
        f'/workflows/{workflow.id}/task-revert',
    )

    # assert
    assert response.status_code == 400
    workflow.refresh_from_db()
    assert workflow.current_task == 2


def test_revert__skip_two_task_to_first_task_by_condition__raise(
    api_client,
    mocker,
):
    """ cause by bug https://my.pneumatic.app/workflows/10397 """
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

    assert response.status_code == 200
    assert workflow.current_task == 3

    # act
    response = api_client.post(
        f'/workflows/{workflow.id}/task-revert',
    )

    # assert
    assert response.status_code == 400
    workflow.refresh_from_db()
    assert workflow.current_task == 3


def test_revert__deleted_performer_recreated__ok(
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
        'send_task_completed_webhook.delay'
    )
    mocker.patch(
        'pneumatic_backend.processes.tasks.webhooks.'
        'send_task_returned_webhook.delay',
    )
    user = create_test_user()
    user_performer = create_test_user(
        email='t@t.t',
        account=user.account
    )
    api_client.token_authenticate(user)
    response1 = api_client.post(
        path='/templates',
        data={
            'name': 'Template',
            'template_owners': [user.id, user_performer.id],
            'is_active': True,
            'kickoff': {},
            'tasks': [
                {
                    'number': 1,
                    'name': 'First step',
                    'fields': [
                        {
                            'type': FieldType.USER,
                            'name': 'Performer',
                            'order': 1,
                            'is_required': True,
                            'api_name': 'user-field-1'
                        }
                    ],
                    'raw_performers': [
                        {
                            'type': PerformerType.USER,
                            'source_id': str(user.id)
                        }
                    ]
                },
                {
                    'number': 2,
                    'name': 'Second step',
                    'raw_performers': [
                        {
                            'type': PerformerType.FIELD,
                            'source_id': 'user-field-1'
                        },
                        {
                            'type': PerformerType.USER,
                            'source_id': str(user.id)
                        }
                    ]
                }
            ]
        }
    )
    template = Template.objects.get(id=response1.data['id'])
    response = api_client.post(
        f'/templates/{template.id}/run',
    )
    workflow = Workflow.objects.get(id=response.data['id'])

    mocker.patch(
        'pneumatic_backend.processes.services.websocket.WSSender.'
        '_send_task_notification'
    )

    # Go on second step
    task1 = workflow.current_task_instance
    api_client.post(
        f'/workflows/{workflow.id}/task-complete',
        data={
            'task_id': task1.id,
            'output': {'user-field-1': user_performer.id}
        }
    )
    workflow.refresh_from_db()
    task2 = workflow.current_task_instance

    # Remove performer and go to the first step
    TaskPerformersService.delete_performer(
        task=task2,
        request_user=user,
        user_key=user_performer.id
    )
    api_client.post(
        f'/workflows/{workflow.id}/task-revert',
    )

    # act
    response = api_client.post(
        f'/workflows/{workflow.id}/task-complete',
        data={
            'task_id': task1.id,
            'output': {'user-field-1': user_performer.id}
        }
    )

    # assert
    workflow.refresh_from_db()
    assert response.status_code == 204
    assert workflow.current_task == 2
    task2 = workflow.current_task_instance
    assert task2.is_completed is False
    performers = task2.performers.exclude_directly_deleted()
    assert performers.count() == 2
    assert performers.filter(id=user_performer.id).exists()


def test_revert__deleted_performer__permission_denied(
    mocker,
    api_client
):
    # arrange
    template_owner = create_test_user()
    deleted_performer = create_test_user(
        email='t@t.t',
        account=template_owner.account,
        is_account_owner=False
    )
    api_client.token_authenticate(template_owner)
    workflow = create_test_workflow(
        tasks_count=2,
        user=template_owner
    )

    mocker.patch(
        'pneumatic_backend.processes.services.websocket.WSSender.'
        '_send_task_notification'
    )

    # Go on second step
    task1 = workflow.current_task_instance
    api_client.post(
        f'/workflows/{workflow.id}/task-complete',
        data={'task_id': task1.id}
    )
    workflow.refresh_from_db()
    task2 = workflow.current_task_instance

    # Remove performer and go to the first step
    TaskPerformersService.delete_performer(
        task=task2,
        request_user=template_owner,
        user_key=deleted_performer.id
    )
    api_client.token_authenticate(deleted_performer)
    response = api_client.post(
        f'/workflows/{workflow.id}/task-revert',
    )

    # assert
    workflow.refresh_from_db()
    assert response.status_code == 403


def test_revert__activate_skipped_task__ok(
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
    account = create_test_account(plan=BillingPlanType.PREMIUM)
    user = create_test_user(account=account)
    template = create_test_template(
        user=user,
        is_active=True,
        tasks_count=2
    )

    kickoff_field = FieldTemplate.objects.create(
        type=FieldType.TEXT,
        name='Skip first task',
        kickoff=template.kickoff_instance,
        template=template,
    )
    template_task_1 = template.tasks.get(number=1)
    condition_template = ConditionTemplate.objects.create(
        task=template_task_1,
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
        field_type=FieldType.TEXT,
        field=kickoff_field.api_name,
        value='ok',
        template=template,
    )

    api_client.token_authenticate(user=user)
    # skip first task
    response_run = api_client.post(
        f'/templates/{template.id}/run',
        data={
            'kickoff': {
                kickoff_field.api_name: 'ok'
            }
        }
    )
    workflow_id = response_run.data['id']

    # cancel skip condition for first task
    response_update = api_client.patch(
        f'/workflows/{workflow_id}',
        data={
            'kickoff': {
                kickoff_field.api_name: 'no',
            }
        }
    )

    # act
    response_revert = api_client.post(
        f'/workflows/{workflow_id}/task-revert',
    )

    # assert
    assert response_run.status_code == 200
    assert response_update.status_code == 200
    assert response_revert.status_code == 204
    workflow = Workflow.objects.get(id=workflow_id)
    assert workflow.current_task == 1
    task = workflow.current_task_instance
    assert task.is_skipped is False


@pytest.mark.parametrize('status', WorkflowStatus.RUNNING_STATUSES)
def test_revert__sub_workflow_incompleted__validation_error(
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
        f'/workflows/{workflow.id}/task-revert',
    )

    # assert
    assert response.status_code == 400
    assert response.data['message'] == messages.MSG_PW_0071
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    workflow.refresh_from_db()
    assert workflow.current_task == 2


def test_revert__sub_workflow_completed__ok(
    mocker,
    api_client,
):

    # arrange
    mocker.patch(
        'pneumatic_backend.processes.tasks.webhooks.'
        'send_task_returned_webhook.delay',
    )
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
        f'/workflows/{workflow.id}/task-revert',
    )

    # assert
    assert response.status_code == 204
    workflow.refresh_from_db()
    assert workflow.current_task == 1
