# pylint:disable=redefined-outer-name
# pylint:disable=unused-argument
import pytest
from pneumatic_backend.processes.messages import workflow as messages
from pneumatic_backend.utils.validation import ErrorCode
from pneumatic_backend.processes.models import (
    Workflow,
    TaskPerformer,
    FieldTemplate,
    FileAttachment,
    ConditionTemplate,
    RuleTemplate,
    PredicateTemplate,
    Template,
    FieldTemplateSelection
)
from pneumatic_backend.processes.services.versioning.schemas import (
    TemplateSchemaV1,
)
from pneumatic_backend.processes.services.versioning.versioning import (
    TemplateVersioningService,
)
from pneumatic_backend.processes.tests.fixtures import (
    create_test_user,
    create_test_guest,
    create_test_workflow,
    create_invited_user,
    create_test_template,
    create_test_account
)
from pneumatic_backend.processes.models import WorkflowEvent
from pneumatic_backend.processes.api_v2.serializers.workflow.events import (
    TaskEventJsonSerializer
)
from pneumatic_backend.processes.enums import (
    WorkflowStatus,
    PerformerType,
    FieldType,
    PredicateOperator,
    WorkflowEventType,
)
from pneumatic_backend.processes.api_v2.services.task.performers import (
    TaskPerformersService
)
from pneumatic_backend.authentication.services import GuestJWTAuthService
from pneumatic_backend.accounts.services import (
    UserInviteService
)
from pneumatic_backend.accounts.enums import (
    SourceType,
    BillingPlanType,
)
from pneumatic_backend.authentication.enums import AuthTokenType
from pneumatic_backend.processes.api_v2.services.workflows\
    .workflow_version import (
        WorkflowUpdateVersionService
    )
from pneumatic_backend.accounts.models import Notification
from pneumatic_backend.accounts.enums import NotificationType
from pneumatic_backend.processes.services.workflow_action import (
    WorkflowActionService
)


pytestmark = pytest.mark.django_db


def test_complete__fields_values__ok(
    mocker,
    api_client
):

    # arrange
    account = create_test_account()
    user = create_test_user(account=account)
    performer = create_test_user(
        account=account,
        email='test@test.test',
        is_account_owner=False
    )
    workflow = create_test_workflow(user, tasks_count=1)
    task = workflow.current_task_instance
    task.performers.add(performer)
    service_init_mock = mocker.patch.object(
        WorkflowActionService,
        attribute='__init__',
        return_value=None
    )
    complete_current_task_by_user_mock = mocker.patch(
        'pneumatic_backend.processes.services.'
        'workflow_action.WorkflowActionService.'
        'complete_current_task_for_user'
    )
    fields_data = {
        'field_1': 'value_1',
        'field_2': 2
    }
    api_client.token_authenticate(performer)

    # act
    response = api_client.post(
        f'/workflows/{workflow.id}/task-complete',
        data={
            'task_id': workflow.current_task_instance.id,
            'output': fields_data
        }
    )

    # assert
    assert response.status_code == 204
    workflow.refresh_from_db()
    service_init_mock.assert_called_once_with(
        user=performer,
        auth_type=AuthTokenType.USER,
        is_superuser=False
    )
    complete_current_task_by_user_mock.assert_called_once_with(
        workflow=workflow,
        fields_values=fields_data
    )


def test_complete__not_fields_values__ok(
    mocker,
    api_client
):

    # arrange
    account = create_test_account()
    user = create_test_user(account=account)
    performer = create_test_user(
        account=account,
        email='test@test.test',
        is_account_owner=False
    )
    workflow = create_test_workflow(user, tasks_count=1)
    task = workflow.current_task_instance
    task.performers.add(performer)
    service_init_mock = mocker.patch.object(
        WorkflowActionService,
        attribute='__init__',
        return_value=None
    )
    complete_current_task_by_user_mock = mocker.patch(
        'pneumatic_backend.processes.services.'
        'workflow_action.WorkflowActionService.'
        'complete_current_task_for_user'
    )
    api_client.token_authenticate(performer)

    # act
    response = api_client.post(
        f'/workflows/{workflow.id}/task-complete',
        data={
            'task_id': workflow.current_task_instance.id
        }
    )

    # assert
    assert response.status_code == 204
    workflow.refresh_from_db()
    service_init_mock.assert_called_once_with(
        user=performer,
        auth_type=AuthTokenType.USER,
        is_superuser=False
    )
    complete_current_task_by_user_mock.assert_called_once_with(
        workflow=workflow,
        fields_values={}
    )


def test_complete__snoozed_workflow__validation_error(
    mocker,
    api_client
):

    # arrange
    account = create_test_account()
    user = create_test_user(account=account)
    workflow = create_test_workflow(
        user=user,
        status=WorkflowStatus.DELAYED,
        tasks_count=1
    )
    service_init_mock = mocker.patch.object(
        WorkflowActionService,
        attribute='__init__',
        return_value=None
    )
    complete_current_task_by_user_mock = mocker.patch(
        'pneumatic_backend.processes.services.'
        'workflow_action.WorkflowActionService.'
        'complete_current_task_for_user'
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        f'/workflows/{workflow.id}/task-complete',
        data={
            'task_id': workflow.current_task_instance.id
        }
    )

    # assert
    assert response.status_code == 400
    message = messages.MSG_PW_0004
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    service_init_mock.assert_not_called()
    complete_current_task_by_user_mock.assert_not_called()


@pytest.mark.parametrize('status', WorkflowStatus.END_STATUSES)
def test_complete__ended_workflow__validation_error(
    status,
    mocker,
    api_client
):

    # arrange
    account = create_test_account()
    user = create_test_user(account=account)
    workflow = create_test_workflow(user, status=status)
    service_init_mock = mocker.patch.object(
        WorkflowActionService,
        attribute='__init__',
        return_value=None
    )
    complete_current_task_by_user_mock = mocker.patch(
        'pneumatic_backend.processes.services.'
        'workflow_action.WorkflowActionService.'
        'complete_current_task_for_user'
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        f'/workflows/{workflow.id}/task-complete',
        data={
            'task_id': workflow.current_task_instance.id
        }
    )

    # assert
    assert response.status_code == 400
    message = messages.MSG_PW_0008
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    service_init_mock.assert_not_called()
    complete_current_task_by_user_mock.assert_not_called()


def test_complete__not_current_task__validation_error(
    mocker,
    api_client
):

    # arrange
    account = create_test_account()
    user = create_test_user(account=account)
    workflow = create_test_workflow(user, tasks_count=2)
    service_init_mock = mocker.patch.object(
        WorkflowActionService,
        attribute='__init__',
        return_value=None
    )
    complete_current_task_by_user_mock = mocker.patch(
        'pneumatic_backend.processes.services.'
        'workflow_action.WorkflowActionService.'
        'complete_current_task_for_user'
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        f'/workflows/{workflow.id}/task-complete',
        data={
            'task_id': workflow.tasks.get(number=2).id
        }
    )

    # assert
    assert response.status_code == 400
    message = messages.MSG_PW_0018
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    service_init_mock.assert_not_called()
    complete_current_task_by_user_mock.assert_not_called()


def test_complete__checklist_incompleted__validation_error(
    mocker,
    api_client
):

    # arrange
    account = create_test_account()
    user = create_test_user(account=account)
    workflow = create_test_workflow(user, tasks_count=1)
    task = workflow.current_task_instance
    task.checklists_marked = 1
    task.checklists_total = 2
    task.save(update_fields=['checklists_marked', 'checklists_total'])

    service_init_mock = mocker.patch.object(
        WorkflowActionService,
        attribute='__init__',
        return_value=None
    )
    complete_current_task_by_user_mock = mocker.patch(
        'pneumatic_backend.processes.services.'
        'workflow_action.WorkflowActionService.'
        'complete_current_task_for_user'
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        f'/workflows/{workflow.id}/task-complete',
        data={
            'task_id': workflow.current_task_instance.id
        }
    )

    # assert
    assert response.status_code == 400
    message = messages.MSG_PW_0006
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    service_init_mock.assert_not_called()
    complete_current_task_by_user_mock.assert_not_called()


def test_complete__sub_workflows_incompleted__validation_error(
    mocker,
    api_client
):

    # arrange
    account = create_test_account()
    user = create_test_user(account=account)
    workflow = create_test_workflow(user, tasks_count=1)
    task = workflow.current_task_instance
    create_test_workflow(
        user=user,
        tasks_count=1,
        ancestor_task=task
    )
    service_init_mock = mocker.patch.object(
        WorkflowActionService,
        attribute='__init__',
        return_value=None
    )
    complete_current_task_by_user_mock = mocker.patch(
        'pneumatic_backend.processes.services.'
        'workflow_action.WorkflowActionService.'
        'complete_current_task_for_user'
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        f'/workflows/{workflow.id}/task-complete',
        data={
            'task_id': workflow.current_task_instance.id
        }
    )

    # assert
    assert response.status_code == 400
    message = messages.MSG_PW_0070
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    service_init_mock.assert_not_called()
    complete_current_task_by_user_mock.assert_not_called()


def test_complete__not_performer__validation_error(
    mocker,
    api_client
):

    # arrange
    account = create_test_account()
    user = create_test_user(
        account=account,
        is_account_owner=True
    )
    workflow = create_test_workflow(user, tasks_count=1)
    not_performer = create_test_user(
        account=account,
        email='test@test.test',
        is_account_owner=False
    )
    service_init_mock = mocker.patch.object(
        WorkflowActionService,
        attribute='__init__',
        return_value=None
    )
    complete_current_task_by_user_mock = mocker.patch(
        'pneumatic_backend.processes.services.'
        'workflow_action.WorkflowActionService.'
        'complete_current_task_for_user'
    )
    api_client.token_authenticate(not_performer)

    # act
    response = api_client.post(
        f'/workflows/{workflow.id}/task-complete',
        data={
            'task_id': workflow.current_task_instance.id
        }
    )

    # assert
    assert response.status_code == 403
    service_init_mock.assert_not_called()
    complete_current_task_by_user_mock.assert_not_called()


def test_complete__performer_already_complete__validation_error(
    mocker,
    api_client
):

    # arrange
    account = create_test_account()
    user = create_test_user(
        account=account,
        is_account_owner=True
    )
    performer = create_test_user(
        account=account,
        email='test@test.test',
        is_account_owner=False
    )
    workflow = create_test_workflow(user, tasks_count=1)
    task = workflow.current_task_instance
    task.taskperformer_set.filter(user=performer).update(is_completed=True)

    service_init_mock = mocker.patch.object(
        WorkflowActionService,
        attribute='__init__',
        return_value=None
    )
    complete_current_task_by_user_mock = mocker.patch(
        'pneumatic_backend.processes.services.'
        'workflow_action.WorkflowActionService.'
        'complete_current_task_for_user'
    )
    api_client.token_authenticate(performer)

    # act
    response = api_client.post(
        f'/workflows/{workflow.id}/task-complete',
        data={
            'task_id': workflow.current_task_instance.id
        }
    )

    # assert
    assert response.status_code == 403
    service_init_mock.assert_not_called()
    complete_current_task_by_user_mock.assert_not_called()


class TestCompleteWorkflow:

    """ Legacy tests """

    def test_complete__by_performer__ok(
        self,
        mocker,
        api_client,
    ):
        # arrange
        account = create_test_account()
        create_test_user(
            email='owner@test.test',
            is_account_owner=True,
            account=account
        )
        user = create_test_user(is_account_owner=False, account=account)
        workflow = create_test_workflow(user, tasks_count=3)
        send_new_task_notification_ws_mock = mocker.patch(
            'pneumatic_backend.processes.services.websocket.WSSender.'
            'send_new_task_notification'
        )
        send_removed_task_notification_mock = mocker.patch(
            'pneumatic_backend.processes.services.websocket.WSSender.'
            'send_removed_task_notification'
        )
        send_new_task_notification_mock = mocker.patch(
            'pneumatic_backend.processes.services.workflow_action.'
            'send_new_task_notification.delay'
        )

        data = {
            'task_id': workflow.current_task_instance.id
        }
        api_client.token_authenticate(user)
        analytics_mock = mocker.patch(
            'pneumatic_backend.processes.services.'
            'workflow_action.AnalyticService.task_completed'
        )

        # act
        response = api_client.post(
            f'/workflows/{workflow.id}/task-complete',
            data=data
        )
        # assert
        assert response.status_code == 204
        workflow.refresh_from_db()
        task_1 = workflow.tasks.get(number=1)
        task_2 = workflow.tasks.get(number=2)

        assert workflow.current_task == 2
        assert workflow.date_completed is None
        assert task_1.is_completed is True
        assert task_1.date_completed
        send_new_task_notification_ws_mock.assert_called_once_with(
            task=task_2,
            sync=False,
        )
        send_removed_task_notification_mock.assert_called_once_with(
            task=task_1,
            user_ids=(user.id,),
            sync=False,
        )
        send_new_task_notification_mock.assert_called_once()
        analytics_mock.assert_called_once_with(
            user=user,
            is_superuser=False,
            auth_type=AuthTokenType.USER,
            workflow=workflow,
            task=task_1
        )

    def test_complete__insert_output_through_task(
        self,
        api_client,
        mocker,
    ):
        # arrange
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
        second_task.description = (
            'His name is... {{ %s }}!!! Second' % output_field.api_name
        )
        second_task.save()
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
        first_task = workflow.current_task

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
            account_id=user.account_id
        )

        data = {
            'task_id': workflow.current_task_instance.id,
            'output': {
                output_field.api_name: 'JOHN CENA',
                output_file.api_name: [first_file.id, second_file.id]
            }
        }

        api_client.token_authenticate(user=user)

        # act
        response = api_client.post(
            f'/workflows/{workflow.id}/task-complete',
            data=data,
        )
        output_file.refresh_from_db()

        assert response.status_code == 204

        workflow.refresh_from_db()
        data = {
            'task_id': workflow.current_task_instance.id,
        }
        response = api_client.post(
            f'/workflows/{workflow.id}/task-complete',
            data=data,
        )
        output_file.refresh_from_db()

        # assert
        assert response.status_code == 204

        workflow.refresh_from_db()
        current_task = workflow.current_task_instance

        assert workflow.current_task == first_task + 2
        assert current_task.description == (
            'His name is... JOHN CENA!!! Third link '
            f'[{output_file.name}](https://john.cena/john.cena)\n'
            f'[{output_file.name}](https://john.cena/john1.cena)'
        )

    def test_complete__last_task__ok(
        self,
        mocker,
        api_client,
    ):
        # arrange
        user = create_test_user()
        template = create_test_template(
            user=user,
            is_active=True,
            tasks_count=1
        )
        workflow = create_test_workflow(
            user=user,
            template=template,
        )
        deactivate_cache_mock = mocker.patch(
            'pneumatic_backend.authentication.services.'
            'GuestJWTAuthService.deactivate_task_guest_cache'
        )
        task_complete_analytics_mock = mocker.patch(
            'pneumatic_backend.processes.services.'
            'workflow_action.AnalyticService.task_completed'
        )
        wf_complete_analytics_mock = mocker.patch(
            'pneumatic_backend.processes.services.'
            'workflow_action.AnalyticService.workflow_completed'
        )

        api_client.token_authenticate(user)

        # act
        response = api_client.post(
            f'/workflows/{workflow.id}/task-complete',
            data={
                'task_id': workflow.current_task_instance.id
            }
        )

        # assert
        workflow.refresh_from_db()
        assert response.status_code == 204
        assert workflow.status == WorkflowStatus.DONE
        assert workflow.date_completed
        task = workflow.current_task_instance
        assert task.is_completed is True
        task_complete_analytics_mock.assert_called_once_with(
            user=user,
            is_superuser=False,
            auth_type=AuthTokenType.USER,
            workflow=workflow,
            task=task
        )
        wf_complete_analytics_mock.assert_called_once_with(
            user=user,
            is_superuser=False,
            auth_type=AuthTokenType.USER,
            workflow=workflow,
        )
        deactivate_cache_mock.assert_called_once_with(task_id=task.id)

    def test_complete__last_task_without_template__ok(
        self,
        mocker,
        api_client,
    ):
        # arrange
        user = create_test_user()
        template = create_test_template(
            user=user,
            is_active=True,
            tasks_count=1
        )
        workflow = create_test_workflow(
            user=user,
            template=template
        )
        api_client.token_authenticate(user)
        api_client.delete(f'/templates/{template.id}')
        task_complete_analytics_mock = mocker.patch(
            'pneumatic_backend.processes.services.'
            'workflow_action.AnalyticService.task_completed'
        )
        wf_complete_analytics_mock = mocker.patch(
            'pneumatic_backend.processes.services.'
            'workflow_action.AnalyticService.workflow_completed'
        )

        # act
        response = api_client.post(
            f'/workflows/{workflow.id}/task-complete',
            data={'task_id': workflow.current_task_instance.id},
        )
        workflow.refresh_from_db()

        # assert
        assert response.status_code == 204
        assert workflow.status == WorkflowStatus.DONE
        task = workflow.current_task_instance
        assert task.is_completed is True
        task_complete_analytics_mock.assert_called_once_with(
            user=user,
            is_superuser=False,
            auth_type=AuthTokenType.USER,
            workflow=workflow,
            task=task
        )
        wf_complete_analytics_mock.assert_called_once_with(
            user=user,
            is_superuser=False,
            auth_type=AuthTokenType.USER,
            workflow=workflow,
        )

    def test_complete__two_performers_and_rcba_first_complete__ok(
        self,
        mocker,
        api_client
    ):

        # arrange
        user = create_test_user()
        invited = create_invited_user(user)
        workflow = create_test_workflow(user)

        task_1 = workflow.current_task_instance
        task_1.performers.add(invited.id)
        task_1.require_completion_by_all = True
        task_1.save(update_fields=['require_completion_by_all'])
        send_removed_task_notification_mock = mocker.patch(
            'pneumatic_backend.processes.services.websocket.WSSender.'
            'send_removed_task_notification'
        )
        task_complete_analytics_mock = mocker.patch(
            'pneumatic_backend.processes.services.'
            'workflow_action.AnalyticService.task_completed'
        )
        api_client.token_authenticate(user)

        # act
        response = api_client.post(
            f'/workflows/{workflow.id}/task-complete',
            data={'task_id': task_1.id}
        )

        # assert
        assert response.status_code == 204

        workflow.refresh_from_db()
        task_1.refresh_from_db()

        assert workflow.current_task == 1
        assert task_1.is_completed is False
        assert task_1.date_completed is None
        assert task_1.taskperformer_set.filter(
            is_completed=False,
            task=task_1,
            user=invited
        ).exists()
        send_removed_task_notification_mock.assert_called_once_with(
            task=task_1,
            user_ids=(user.id,),
            sync=False
        )
        task_complete_analytics_mock.assert_called_once_with(
            user=user,
            is_superuser=False,
            auth_type=AuthTokenType.USER,
            workflow=workflow,
            task=task_1
        )

    def test_complete__two_performers_and_rcba_last_complete__ok(
        self,
        mocker,
        api_client
    ):

        # arrange
        user = create_test_user()
        invited = create_invited_user(user)
        workflow = create_test_workflow(user)

        task_1 = workflow.current_task_instance
        TaskPerformer.objects.create(
            task=task_1,
            user=invited,
            is_completed=True
        )
        task_1.require_completion_by_all = True
        task_1.save(update_fields=['require_completion_by_all'])
        send_ws_new_task_notification_mock = mocker.patch(
            'pneumatic_backend.processes.services.websocket.WSSender.'
            'send_removed_task_notification'
        )
        task_complete_analytics_mock = mocker.patch(
            'pneumatic_backend.processes.services.'
            'workflow_action.AnalyticService.task_completed'
        )
        api_client.token_authenticate(user)

        # act
        response = api_client.post(
            f'/workflows/{workflow.id}/task-complete',
            data={'task_id': task_1.id}
        )

        # assert
        assert response.status_code == 204

        workflow.refresh_from_db()
        task_1.refresh_from_db()

        assert workflow.current_task == 2
        assert task_1.is_completed
        assert task_1.date_completed
        assert not task_1.taskperformer_set.filter(is_completed=False).exists()
        send_ws_new_task_notification_mock.assert_called_once_with(
            task=task_1,
            user_ids=(user.id,),
            sync=False
        )
        task_complete_analytics_mock.assert_called_once_with(
            user=user,
            is_superuser=False,
            auth_type=AuthTokenType.USER,
            workflow=workflow,
            task=task_1
        )

    def test_task_complete_by_account_owner__ok(self, mocker, api_client):

        # arrange
        user = create_test_user(is_account_owner=True)
        invited = create_invited_user(user, email='test0@pneumatic.app')
        workflow = create_test_workflow(invited)
        current_task = workflow.current_task
        api_client.token_authenticate(user)
        analytics_mock = mocker.patch(
            'pneumatic_backend.processes.services.'
            'workflow_action.AnalyticService.task_completed'
        )

        # act
        response = api_client.post(
            path=f'/workflows/{workflow.id}/task-complete',
            data={
                'task_id': workflow.current_task_instance.id
            }
        )

        # assert
        workflow.refresh_from_db()
        task = workflow.tasks.get(number=current_task)
        assert response.status_code == 204
        assert workflow.current_task == current_task + 1
        assert task.is_completed is True
        analytics_mock.assert_called_once_with(
            user=user,
            is_superuser=False,
            auth_type=AuthTokenType.USER,
            workflow=workflow,
            task=task
        )

    def test_task__complete__not_performer__permission_denied(
        self,
        api_client,
    ):
        # arrange
        user = create_test_user(is_account_owner=False)
        api_client.token_authenticate(user)
        invited = create_invited_user(user, email='test0@pneumatic.app')
        workflow = create_test_workflow(invited)

        # act
        response = api_client.post(
            path=f'/workflows/{workflow.id}/task-complete',
            data={
                'user_id': user.id,
                'task_id': workflow.current_task_instance.id
            }
        )

        # assert
        assert response.status_code == 403

    def test_complete__output_type_user__ok(self, mocker, api_client):

        # arrange
        user = create_test_user()
        api_client.token_authenticate(user)
        template = create_test_template(
            user=user,
            tasks_count=2,
            is_active=True
        )
        field_template1 = FieldTemplate.objects.create(
            name='First performer',
            is_required=True,
            type=FieldType.USER,
            kickoff=template.kickoff_instance,
            template=template,
        )
        field_template2 = FieldTemplate.objects.create(
            name='Second performer',
            is_required=True,
            type=FieldType.USER,
            task=template.tasks.first(),
            template=template,
        )

        response = api_client.post(
            f'/templates/{template.id}/run',
            data={
                'name': 'Test name',
                'kickoff': {
                    field_template1.api_name: user.id
                }
            }
        )
        workflow = Workflow.objects.get(id=response.data['id'])

        # act
        current_task = workflow.current_task_instance
        response = api_client.post(
            f'/workflows/{workflow.id}/task-complete',
            data={
                'task_id': current_task.id,
                'user_id': user.id,
                'output': {
                    field_template2.api_name: user.id
                }
            },
        )

        # assert
        assert response.status_code == 204

    def test_complete__update_notifications__do_nothing(
        self,
        mocker,
        api_client
    ):

        # arrange
        user = create_test_user()
        invited = create_invited_user(user, is_admin=True)
        template = create_test_template(invited)
        task_template_1 = template.tasks.order_by('number').first()
        task_template_1.add_raw_performer(user)

        workflow = create_test_workflow(user, template)
        api_client.token_authenticate(user)
        Notification.objects.create(
            task=workflow.current_task_instance,
            user=invited,
            author=user,
            account=user.account,
            type=NotificationType.COMMENT,
            text='I wanna notify'
        )

        response_complete = api_client.post(
            f'/workflows/{workflow.id}/task-complete',
            data={
                'task_id': workflow.current_task_instance.id,
            }
        )
        workflow.refresh_from_db()
        task_templates = template.tasks.order_by('number')
        task_templates[0].delete_raw_performers()
        task_templates[0].add_raw_performer(invited)
        task_templates[1].delete_raw_performers()
        task_templates[1].add_raw_performer(user)
        task_templates[2].delete_raw_performers()
        task_templates[2].add_raw_performer(user)

        template.refresh_from_db()
        template = TemplateVersioningService(TemplateSchemaV1).save(template)
        version_service = WorkflowUpdateVersionService(
            instance=workflow,
            user=user,
            is_superuser=False,
            auth_type=AuthTokenType.USER
        )

        # act
        version_service.update_from_version(
            data=template.data,
            version=template.version
        )

        # assert
        assert response_complete.status_code == 204
        # Two old notification for completed task №1 (not updated)
        # Zero new notifications for updated tasks №2 and №3
        assert invited.notifications.count() == 2
        assert user.notifications.count() == 0

    def test_complete__skip_task_condition_false__stand_by_task(
        self,
        api_client,
        mocker,
    ):
        # arrange
        send_workflow_started_webhook_mock = mocker.patch(
            'pneumatic_backend.processes.tasks.webhooks.'
            'send_workflow_started_webhook.delay',
        )
        send_task_webhook_mock = mocker.patch(
            'pneumatic_backend.processes.tasks.webhooks.'
            'send_task_webhook.delay',
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
            account_id=user.account_id
        )

        data = {
            'task_id': workflow.current_task_instance.id,
            'output': {
                output_field.api_name: 'JOHN PCENA',
                output_file.api_name: [first_file.id, second_file.id]
            }
        }

        # act
        response = api_client.post(
            f'/workflows/{workflow.id}/task-complete',
            data=data,
        )
        output_file.refresh_from_db()

        # assert
        assert response.status_code == 204

        workflow.refresh_from_db()

        assert workflow.current_task == 2
        send_workflow_started_webhook_mock.assert_called_once_with(
            user_id=user.id,
            instance_id=workflow.id
        )
        send_task_webhook_mock.assert_has_calls([
            mocker.call(
                event_name='task_completed_v2',
                user_id=user.id,
                instance_id=workflow.tasks.order_by('number').first().id,
            )
        ])

    def test_complete__skip_task_condition_true__goto_next_task(
        self,
        api_client,
        mocker,
    ):
        # arrange
        send_workflow_started_webhook_mock = mocker.patch(
            'pneumatic_backend.processes.tasks.webhooks.'
            'send_workflow_started_webhook.delay',
        )
        send_task_webhook_mock = mocker.patch(
            'pneumatic_backend.processes.tasks.webhooks.'
            'send_task_webhook.delay',
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
        rule_2 = RuleTemplate.objects.create(
            condition=condition_template,
            template=template,
        )
        PredicateTemplate.objects.create(
            rule=rule_2,
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
            account_id=user.account_id
        )

        data = {
            'task_id': workflow.current_task_instance.id,
            'output': {
                output_field.api_name: 'JOHN CENA',
                output_file.api_name: [first_file.id, second_file.id]
            }
        }

        # act
        response = api_client.post(
            f'/workflows/{workflow.id}/task-complete',
            data=data,
        )
        output_file.refresh_from_db()

        # assert
        assert response.status_code == 204

        workflow.refresh_from_db()
        current_task = workflow.current_task_instance

        assert workflow.current_task == 3
        assert current_task.description == (
            'His name is... JOHN CENA!!! Third link '
            f'[{output_file.name}](https://john.cena/john.cena)\n'
            f'[{output_file.name}](https://john.cena/john1.cena)'
        )
        send_workflow_started_webhook_mock.assert_called_once_with(
            user_id=user.id,
            instance_id=workflow.id
        )
        send_task_webhook_mock.assert_has_calls([
            mocker.call(
                event_name='task_completed_v2',
                user_id=user.id,
                instance_id=workflow.tasks.order_by('number').first().id,
            )
        ])

    def test_complete__skip_task__correct_notifications(
        self,
        api_client,
        mocker,
    ):
        # arrange
        mocker.patch(
            'pneumatic_backend.processes.tasks.webhooks.'
            'send_workflow_webhook.delay',
        )
        mocker.patch(
            'pneumatic_backend.processes.tasks.webhooks.'
            'send_task_webhook.delay',
        )
        account = create_test_account(plan=BillingPlanType.PREMIUM)
        template_owner = create_test_user(account=account)
        user_1 = create_test_user(
            first_name='First',
            last_name='Performer',
            email='performer_1@some.com',
            account=account,
            is_account_owner=False
        )
        user_2 = create_test_user(
            first_name='Second',
            last_name='Performer',
            email='performer_2@some.com',
            account=account,
            is_account_owner=False
        )
        user_3 = create_test_user(
            first_name='Third',
            last_name='Performer',
            email='performer_3@some.com',
            account=account,
            is_account_owner=False
        )
        api_client.token_authenticate(user=template_owner)

        # act
        response_create = api_client.post(
            path='/templates',
            data={
                'name': 'Template',
                'is_active': True,
                'template_owners': [template_owner.id],
                'kickoff': {
                    'fields': [
                        {
                            'order': 1,
                            'name': 'Skip second task',
                            'type': FieldType.TEXT,
                            'api_name': 'skip-field-1',
                            'is_required': True,
                        }
                    ]
                },
                'tasks': [
                    {
                        'number': 1,
                        'name': 'First task',
                        'raw_performers': [
                            {
                                'type': PerformerType.USER,
                                'source_id': user_1.id
                            }
                        ]
                    },
                    {
                        'number': 2,
                        'name': 'Second task',
                        'raw_performers': [
                            {
                                'type': PerformerType.USER,
                                'source_id': user_2.id
                            }
                        ],
                        'conditions': [
                          {
                            'order': 1,
                            'action': 'skip_task',
                            'rules': [
                              {
                                'predicates': [
                                  {
                                    'field': 'skip-field-1',
                                    'field_type': FieldType.TEXT,
                                    'operator': PredicateOperator.EQUAL,
                                    'value': 'skip',
                                  }
                                ]
                              }
                            ]
                          }
                        ]
                    },
                    {
                        'number': 3,
                        'name': 'Third task',
                        'raw_performers': [
                            {
                                'type': PerformerType.USER,
                                'source_id': user_3.id
                            }
                        ]
                    },
                ]
            }
        )
        template = Template.objects.get(id=response_create.data['id'])

        response_run = api_client.post(
            f'/templates/{template.id}/run',
            data={
                'kickoff': {
                    'skip-field-1': 'skip'
                }
            }
        )
        workflow = Workflow.objects.get(id=response_run.data['id'])
        api_client.token_authenticate(user=template_owner)

        send_ws_new_task_notification_mock = mocker.patch(
            'pneumatic_backend.processes.services.websocket.WSSender.'
            'send_new_task_notification'
        )
        send_ws_removed_task_notification_mock = mocker.patch(
            'pneumatic_backend.processes.services.websocket.WSSender.'
            'send_removed_task_notification'
        )
        send_new_task_notification_mock = mocker.patch(
            'pneumatic_backend.processes.services.workflow_action.'
            'send_new_task_notification.delay'
        )

        # act
        response_complete = api_client.post(
            f'/workflows/{workflow.id}/task-complete',
            data={
                'task_id': workflow.current_task_instance.id,
            },
        )

        # assert
        assert response_create.status_code == 200
        assert response_run.status_code == 200
        assert response_complete.status_code == 204
        workflow.refresh_from_db()
        assert workflow.current_task == 3
        task_1 = workflow.tasks.get(number=1)
        task_3 = workflow.tasks.get(number=3)
        send_ws_removed_task_notification_mock.assert_called_once_with(
            task=task_1,
            user_ids=(user_1.id,),
            sync=False
        )
        send_ws_new_task_notification_mock.assert_called_once_with(
            task=task_3,
            sync=False,
        )
        send_new_task_notification_mock.assert_called_once()

    def test_complete__skip_task_event__ok(
        self,
        api_client,
    ):
        # arrange
        user = create_test_user()
        api_client.token_authenticate(user=user)
        template = create_test_template(
            user=user,
            is_active=True
        )
        task_template_1 = template.tasks.get(number=1)
        output_field = FieldTemplate.objects.create(
            type=FieldType.TEXT,
            name='Past name',
            description='Last description',
            task=task_template_1,
            template=template,
        )
        task_template_2 = template.tasks.get(number=2)
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
            field_type=FieldType.TEXT,
            field=output_field.api_name,
            value='JOHN CENA',
            template=template,
        )

        response = api_client.post(
            f'/templates/{template.id}/run',
        )
        workflow = Workflow.objects.get(id=response.data['id'])

        # act
        response = api_client.post(
            f'/workflows/{workflow.id}/task-complete',
            data={
                'task_id': workflow.current_task_instance.id,
                'output': {
                    output_field.api_name: 'JOHN CENA',
                }
            }
        )
        second_task = workflow.tasks.get(number=2)

        # assert
        assert response.status_code == 204
        workflow.refresh_from_db()
        assert workflow.current_task == 3
        assert WorkflowEvent.objects.filter(
            workflow=workflow,
            account=user.account,
            type=WorkflowEventType.TASK_SKIP,
            task_json=TaskEventJsonSerializer(
                instance=second_task,
                context={'event_type': WorkflowEventType.TASK_SKIP}
            ).data
        ).count() == 1

        assert WorkflowEvent.objects.filter(
            workflow=workflow,
            account=user.account,
            type=WorkflowEventType.TASK_START,
            task_json=TaskEventJsonSerializer(
                instance=second_task,
                context={'event_type': WorkflowEventType.TASK_START}
            ).data
        ).count() == 0

    def test_complete__skip_task_end_workflow_event__ok(
        self,
        api_client,
    ):
        # arrange
        user = create_test_user()
        api_client.token_authenticate(user=user)
        template = create_test_template(
            user=user,
            is_active=True,
            tasks_count=2
        )
        task_template_1 = template.tasks.get(number=1)
        output_field = FieldTemplate.objects.create(
            type=FieldType.TEXT,
            name='Past name',
            description='Last description',
            task=task_template_1,
            template=template,
        )
        task_template_2 = template.tasks.get(number=2)
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
            field_type=FieldType.TEXT,
            field=output_field.api_name,
            value='JOHN CENA',
            template=template,
        )

        response = api_client.post(
            f'/templates/{template.id}/run',
        )
        workflow = Workflow.objects.get(id=response.data['id'])

        # act
        response = api_client.post(
            f'/workflows/{workflow.id}/task-complete',
            data={
                'task_id': workflow.current_task_instance.id,
                'output': {
                    output_field.api_name: 'JOHN CENA',
                }
            }
        )

        # assert
        assert response.status_code == 204
        workflow.refresh_from_db()
        assert workflow.current_task == 1
        assert WorkflowEvent.objects.filter(
            workflow=workflow,
            account=user.account,
            type=WorkflowEventType.ENDED,
        ).count() == 1

    def test_complete__skip_task__fields_is_empty(
        self,
        api_client
    ):

        """ More about the case in the https://trello.com/c/LxXWlXWl """

        # arrange
        account = create_test_account(plan=BillingPlanType.PREMIUM)
        user = create_test_user(account=account)
        api_client.token_authenticate(user)

        api_name_skip_field = 'skip-field'
        api_name_skip_selection = 'skip-selection'
        api_name_file = 'file-field-1'
        api_name_url = 'url-field-1'
        api_name_str = 'str-field-1'
        api_name_text = 'text-field-1'
        api_name_checkbox = 'box-field-1'
        api_name_radio = 'radio-field-1'
        api_name_dropdown = 'drop-field-1'

        task_3_name = 'Second {{%s}}step' % api_name_str
        task_3_result_name = 'Second step'
        task_3_description = '{{%s}}{{%s}}{{%s}}{{%s}}{{%s}}{{%s}}{{%s}}' % (
            api_name_file,
            api_name_url,
            api_name_str,
            api_name_text,
            api_name_checkbox,
            api_name_radio,
            api_name_dropdown
        )
        task_3_result_description = ''

        fields_data = [
            {
                'order': 1,
                'name': 'Attached file',
                'type': FieldType.FILE,
                'is_required': False,
                'api_name': api_name_file
            },
            {
                'order': 2,
                'name': 'Attached URL',
                'type': FieldType.URL,
                'is_required': False,
                'api_name': api_name_url
            },
            {
                'order': 3,
                'name': 'String field',
                'type': FieldType.STRING,
                'is_required': False,
                'api_name': api_name_str
            },
            {
                'order': 4,
                'name': 'Text field',
                'type': FieldType.TEXT,
                'is_required': False,
                'api_name': api_name_text
            },
            {
                'order': 5,
                'name': 'Checkbox field',
                'type': FieldType.CHECKBOX,
                'is_required': False,
                'api_name': api_name_checkbox,
                'selections': [
                    {'value': 'First checkbox'},
                    {'value': 'Second checkbox'}
                ]
            },
            {
                'order': 6,
                'name': 'Radio field',
                'type': FieldType.RADIO,
                'is_required': False,
                'api_name': api_name_radio,
                'selections': [
                    {'value': 'First radio'},
                    {'value': 'Second radio'}
                ]
            },
            {
                'order': 7,
                'type': FieldType.DROPDOWN,
                'name': 'Dropdown field',
                'is_required': False,
                'api_name': api_name_dropdown,
                'selections': [
                    {'value': 'First selection'},
                    {'value': 'Second selection'}
                ]
            },

        ]

        conditions_data = [
            {
                'order': 1,
                'action': 'skip_task',
                'api_name': 'condition-1',
                'rules': [
                    {
                        'predicates': [
                            {
                                'field': api_name_skip_field,
                                'field_type': FieldType.CHECKBOX,
                                'operator': PredicateOperator.EQUAL,
                                'value': api_name_skip_selection
                            }
                        ]
                    }
                ]
            }
        ]

        response_create = api_client.post(
            path='/templates',
            data={
                'name': 'Template',
                'is_active': True,
                'template_owners': [user.id],
                'kickoff': {
                    'fields': [
                        {
                            'order': 1,
                            'name': 'Skip first task',
                            'api_name': api_name_skip_field,
                            'type': FieldType.CHECKBOX,
                            'is_required': False,
                            'selections': [
                                {
                                    'api_name': api_name_skip_selection,
                                    'value': 'Click to skip first step'
                                }
                            ]
                        },
                    ]
                },
                'tasks': [
                    {
                        'number': 1,
                        'name': 'Step 1',
                        'raw_performers': [
                            {
                                'type': PerformerType.USER,
                                'source_id': user.id
                            }
                        ]
                    },
                    {
                        'number': 2,
                        'name': 'Skipped step',
                        'api_name': 'task-1',
                        'fields': fields_data,
                        'raw_performers': [
                            {
                                'type': PerformerType.USER,
                                'source_id': user.id
                            }
                        ],
                        'conditions': conditions_data
                    },
                    {
                        'number': 3,
                        'name': task_3_name,
                        'description': task_3_description,
                        'api_name': 'task-3',
                        'raw_performers': [
                            {
                                'type': PerformerType.USER,
                                'source_id': user.id
                            }
                        ]
                    }
                ]
            }
        )
        template = Template.objects.get(id=response_create.data['id'])
        selection = FieldTemplateSelection.objects.get(
            api_name=api_name_skip_selection
        )

        response_run = api_client.post(
            f'/templates/{template.id}/run',
            data={
                'name': 'test workflow',
                'kickoff': {
                    api_name_skip_field: [selection.api_name],
                }
            }
        )
        workflow = Workflow.objects.get(id=response_run.data['id'])

        # act
        response_complete = api_client.post(
            f'/workflows/{workflow.id}/task-complete',
            data={
                'task_id': workflow.current_task_instance.id
            }
        )
        workflow.refresh_from_db()

        # assert
        assert response_create.status_code == 200
        assert response_run.status_code == 200
        assert response_complete.status_code == 204
        task_3 = workflow.tasks.get(number=3)
        assert workflow.current_task == 3
        assert task_3.name == task_3_result_name
        assert task_3.description == task_3_result_description

    def test_complete__end_workflow_by_condition_event__ok(
        self,
        mocker,
        api_client,
    ):
        # arrange
        user = create_test_user()
        api_client.token_authenticate(user=user)
        template = create_test_template(
            user=user,
            is_active=True,
            tasks_count=2
        )
        task_template_1 = template.tasks.get(number=1)
        output_field = FieldTemplate.objects.create(
            type=FieldType.TEXT,
            name='Past name',
            description='Last description',
            task=task_template_1,
            template=template,
        )
        task_template_2 = template.tasks.get(number=2)
        condition_template = ConditionTemplate.objects.create(
            task=task_template_2,
            action=ConditionTemplate.END_WORKFLOW,
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
        deactivate_cache_mock = mocker.patch(
            'pneumatic_backend.authentication.services.'
            'GuestJWTAuthService.deactivate_task_guest_cache'
        )

        response = api_client.post(
            f'/templates/{template.id}/run',
        )
        workflow = Workflow.objects.get(id=response.data['id'])

        # act
        response = api_client.post(
            f'/workflows/{workflow.id}/task-complete',
            data={
                'task_id': workflow.current_task_instance.id,
                'output': {
                    output_field.api_name: 'JOHN CENA',
                }
            }
        )

        # assert
        assert response.status_code == 204
        workflow.refresh_from_db()
        assert workflow.current_task == 1
        assert WorkflowEvent.objects.filter(
            workflow=workflow,
            account=user.account,
            type=WorkflowEventType.ENDED_BY_CONDITION,
        ).count() == 1
        deactivate_cache_mock.assert_has_calls([
            mocker.call(task_id=workflow.tasks.get(number=1).id),
            mocker.call(task_id=workflow.tasks.get(number=2).id)
        ])

    def test_complete__skip_task_no_performers__ok(
        self,
        api_client,
        mocker
    ):
        # arrange
        mocker.patch(
            'pneumatic_backend.processes.services.websocket.WSSender.'
            'send_new_task_notification'
        )
        mocker.patch(
            'pneumatic_backend.processes.services.websocket.WSSender.'
            'send_removed_task_notification'
        )
        mocker.patch(
            'pneumatic_backend.processes.services.workflow_action.'
            'send_new_task_notification.delay'
        )

        user = create_test_user()
        api_client.token_authenticate(user=user)
        template = create_test_template(
            user=user,
            is_active=True,
            tasks_count=4
        )
        # Create condition for skipping second task
        task_template_1 = template.tasks.get(number=1)
        task_template_2 = template.tasks.get(number=2)
        task_field_template = FieldTemplate.objects.create(
            type=FieldType.TEXT,
            name='Skip second task',
            task=task_template_1,
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
            field_type=FieldType.TEXT,
            field=task_field_template.api_name,
            template=template,
            value='skip'
        )

        # Create user-field for second task
        user_field_template = FieldTemplate.objects.create(
            type=FieldType.USER,
            name='Third task performer',
            task=task_template_2,
            template=template,
            is_required=True
        )

        # Set performer for third task
        task_template_3 = template.tasks.get(number=3)
        task_template_3.delete_raw_performers()
        task_template_3.add_raw_performer(
            field=user_field_template,
            performer_type=PerformerType.FIELD
        )

        response = api_client.post(
            f'/templates/{template.id}/run',
            data={'name': 'Workflow'}
        )
        workflow = Workflow.objects.get(id=response.data['id'])

        # act
        response = api_client.post(
            f'/workflows/{workflow.id}/task-complete',
            data={
                'task_id': workflow.current_task_instance.id,
                'output': {
                    task_field_template.api_name: 'skip'
                }

            }
        )
        workflow.refresh_from_db()

        # assert
        task_1 = workflow.tasks.get(number=1)
        task_2 = workflow.tasks.get(number=2)
        task_3 = workflow.tasks.get(number=3)
        task_4 = workflow.tasks.get(number=4)
        assert response.status_code == 204
        assert task_1.is_completed
        assert task_2.is_skipped
        assert task_3.is_skipped
        assert workflow.current_task == 4
        assert WorkflowEvent.objects.filter(
            workflow=workflow,
            account=user.account,
            type=WorkflowEventType.TASK_SKIP,
            task_json=TaskEventJsonSerializer(
                instance=task_2,
                context={'event_type': WorkflowEventType.TASK_SKIP}
            ).data
        ).count() == 1
        assert WorkflowEvent.objects.filter(
            workflow=workflow,
            account=user.account,
            type=WorkflowEventType.TASK_START,
            task_json=TaskEventJsonSerializer(
                instance=task_3,
                context={'event_type': WorkflowEventType.TASK_START}
            ).data
        ).count() == 0
        assert WorkflowEvent.objects.filter(
            workflow=workflow,
            account=user.account,
            type=WorkflowEventType.TASK_SKIP_NO_PERFORMERS,
            task_json=TaskEventJsonSerializer(
                instance=task_3,
                context={
                    'event_type': WorkflowEventType.TASK_SKIP_NO_PERFORMERS
                }
            ).data
        ).count() == 1
        assert WorkflowEvent.objects.filter(
            workflow=workflow,
            account=user.account,
            type=WorkflowEventType.TASK_START,
            task_json=TaskEventJsonSerializer(
                instance=task_4,
                context={'event_type': WorkflowEventType.TASK_START}
            ).data
        ).count() == 1

    def test_complete__deleted_performer__validation_error(
        self,
        api_client,
        mocker
    ):
        # arrange
        mocker.patch(
            'pneumatic_backend.processes.services.websocket.WSSender.'
            'send_new_task_notification'
        )
        mocker.patch(
            'pneumatic_backend.processes.services.websocket.WSSender.'
            'send_removed_task_notification'
        )
        mocker.patch(
            'pneumatic_backend.processes.services.workflow_action.'
            'send_new_task_notification.delay'
        )

        user = create_test_user()
        deleted_user = create_test_user(
            email='t@t.t',
            account=user.account,
            is_account_owner=False
        )
        workflow = create_test_workflow(
            user=user,
            tasks_count=1
        )
        task = workflow.current_task_instance
        TaskPerformersService.create_performer(
            task=task,
            user_key=deleted_user.id,
            request_user=user,
            run_actions=False,
            current_url='/page',
            is_superuser=False
        )
        TaskPerformersService.delete_performer(
            task=task,
            user_key=deleted_user.id,
            request_user=user,
            run_actions=False
        )
        api_client.token_authenticate(user=deleted_user)

        # act
        response = api_client.post(
            f'/workflows/{workflow.id}/task-complete',
            data={
                'task_id': workflow.current_task_instance.id,
            }
        )

        # assert
        workflow.refresh_from_db()
        assert response.status_code == 403

    def test_complete__user_field_invited_transfer__ok(
        self,
        api_client,
    ):

        # arrange
        account_1 = create_test_account(name='transfer from')
        account_2 = create_test_account(name='transfer to')
        user_to_transfer = create_test_user(
            account=account_1,
            email='transfer@test.test',
            is_account_owner=False
        )
        account_2_owner = create_test_user(
            account=account_2,
            is_account_owner=True
        )
        current_url = 'some_url'
        service = UserInviteService(
            request_user=account_2_owner,
            current_url=current_url
        )
        service.invite_user(
            email=user_to_transfer.email,
            invited_from=SourceType.EMAIL
        )
        account_2_new_user = account_2.users.get(email=user_to_transfer.email)
        api_client.token_authenticate(account_2_owner)

        response_template = api_client.post(
            path='/templates',
            data={
                'name': 'Template',
                'is_active': True,
                'template_owners': [
                    account_2_owner.id,
                    account_2_new_user.id
                ],
                'kickoff': {},
                'tasks': [
                    {
                        'number': 1,
                        'name': 'First step',
                        'raw_performers': [
                            {
                                'type': PerformerType.USER,
                                'source_id': str(account_2_owner.id)
                            }
                        ],
                        'fields': [
                            {
                                'type': FieldType.USER,
                                'order': 1,
                                'name': 'Second task performer',
                                'is_required': True,
                                'api_name': 'user-field-1'
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
                            }
                        ]
                    }
                ]
            }
        )
        template_id = response_template.data['id']
        response_run = api_client.post(
            path=f'/templates/{template_id}/run',
            data={
                'name': 'Wf',
                'kickoff': {}
            }
        )
        workflow = Workflow.objects.get(id=response_run.data['id'])

        # act
        response = api_client.post(
            f'/workflows/{workflow.id}/task-complete',
            data={
                'task_id': workflow.current_task_instance.id,
                'output': {
                    'user-field-1': str(account_2_new_user.id),
                }
            }
        )

        # assert
        assert response_template.status_code == 200
        assert response_run.status_code == 200
        assert response.status_code == 204
        workflow.refresh_from_db()
        second_task = workflow.current_task_instance
        assert second_task.number == 2
        assert TaskPerformer.objects.filter(
            user_id=account_2_new_user.id,
            task_id=second_task.id
        ).exclude_directly_deleted().exists()

    def test_complete__guest__ok(
        self,
        mocker,
        api_client,
    ):
        # arrange
        account = create_test_account()
        account_owner = create_test_user(
            account=account,
            email='owner@test.test',
            is_account_owner=True,
        )
        guest = create_test_guest(account=account)
        workflow = create_test_workflow(account_owner, tasks_count=1)
        task = workflow.tasks.first()
        TaskPerformer.objects.create(
            task_id=task.id,
            user_id=guest.id
        )
        str_token = GuestJWTAuthService.get_str_token(
            task_id=task.id,
            user_id=guest.id,
            account_id=account.id
        )

        mocker.patch(
            'pneumatic_backend.processes.services.websocket.WSSender.'
            'send_new_task_notification'
        )
        mocker.patch(
            'pneumatic_backend.processes.services.workflow_action.'
            'send_new_task_notification.delay'
        )

        # act
        response = api_client.post(
            f'/workflows/{workflow.id}/task-complete',
            data={'task_id': task.id},
            **{'X-Guest-Authorization': str_token}

        )
        # assert
        assert response.status_code == 204
        task.refresh_from_db()
        assert task.is_completed is True

    def test_complete__guest_another_workflow__permission_denied(
        self,
        mocker,
        api_client
    ):

        # arrange
        account = create_test_account()
        account_owner = create_test_user(
            account=account,
            email='owner@test.test',
            is_account_owner=True,
        )
        workflow_1 = create_test_workflow(account_owner, tasks_count=1)
        task_1 = workflow_1.tasks.get(number=1)
        guest_1 = create_test_guest(account=account)
        TaskPerformer.objects.create(
            task_id=task_1.id,
            user_id=guest_1.id
        )
        GuestJWTAuthService.get_str_token(
            task_id=task_1.id,
            user_id=guest_1.id,
            account_id=account.id
        )

        workflow_2 = create_test_workflow(account_owner, tasks_count=1)
        task_2 = workflow_2.tasks.get(number=1)
        guest_2 = create_test_guest(
            account=account,
            email='guest2@test.test'
        )
        TaskPerformer.objects.create(
            task_id=task_2.id,
            user_id=guest_2.id
        )
        str_token_2 = GuestJWTAuthService.get_str_token(
            task_id=task_2.id,
            user_id=guest_2.id,
            account_id=account.id
        )
        mocker.patch(
            'pneumatic_backend.processes.services.websocket.WSSender.'
            'send_new_task_notification'
        )
        mocker.patch(
            'pneumatic_backend.processes.services.workflow_action.'
            'send_new_task_notification.delay'
        )

        # act
        response = api_client.post(
            f'/workflows/{workflow_1.id}/task-complete',
            data={'task_id': task_1.id},
            **{'X-Guest-Authorization': str_token_2}
        )

        # assert
        assert response.status_code == 403

    def test_complete__guest_another_workflow_task__permission_denied(
        self,
        mocker,
        api_client
    ):

        # arrange
        account = create_test_account()
        account_owner = create_test_user(
            account=account,
            email='owner@test.test',
            is_account_owner=True,
        )
        workflow = create_test_workflow(account_owner, tasks_count=2)
        workflow.current_task = 2
        workflow.save()
        task_1 = workflow.tasks.get(number=1)
        guest_1 = create_test_guest(account=account)
        TaskPerformer.objects.create(
            task_id=task_1.id,
            user_id=guest_1.id
        )
        GuestJWTAuthService.get_str_token(
            task_id=task_1.id,
            user_id=guest_1.id,
            account_id=account.id
        )

        task_2 = workflow.tasks.get(number=2)
        guest_2 = create_test_guest(
            account=account,
            email='guest2@test.test'
        )
        TaskPerformer.objects.create(
            task_id=task_2.id,
            user_id=guest_2.id
        )
        str_token_2 = GuestJWTAuthService.get_str_token(
            task_id=task_2.id,
            user_id=guest_2.id,
            account_id=account.id
        )
        mocker.patch(
            'pneumatic_backend.processes.services.websocket.WSSender.'
            'send_new_task_notification'
        )
        mocker.patch(
            'pneumatic_backend.processes.services.workflow_action.'
            'send_new_task_notification.delay'
        )

        # act
        response = api_client.post(
            f'/workflows/{workflow.id}/task-complete',
            data={'task_id': task_1.id},
            **{'X-Guest-Authorization': str_token_2}
        )

        # assert
        assert response.status_code == 403

    def test_complete__guest_second_completion__validation_error(
        self,
        mocker,
        api_client
    ):

        # arrange
        account = create_test_account()
        account_owner = create_test_user(
            account=account,
            email='owner@test.test',
            is_account_owner=True,
        )
        workflow = create_test_workflow(account_owner, tasks_count=1)
        task = workflow.tasks.get(number=1)
        task.require_completion_by_all = True
        task.save()
        guest_1 = create_test_guest(account=account)
        guest_2 = create_test_guest(
            account=account,
            email='guest2@test.test'
        )
        TaskPerformer.objects.create(
            task_id=task.id,
            user_id=guest_1.id
        )
        TaskPerformer.objects.create(
            task_id=task.id,
            user_id=guest_2.id
        )
        GuestJWTAuthService.get_str_token(
            task_id=task.id,
            user_id=guest_1.id,
            account_id=account.id
        )
        str_token_2 = GuestJWTAuthService.get_str_token(
            task_id=task.id,
            user_id=guest_2.id,
            account_id=account.id
        )
        mocker.patch(
            'pneumatic_backend.processes.services.websocket.WSSender.'
            'send_new_task_notification'
        )
        mocker.patch(
            'pneumatic_backend.processes.services.workflow_action.'
            'send_new_task_notification.delay'
        )

        response_complete_1 = api_client.post(
            f'/workflows/{workflow.id}/task-complete',
            data={'task_id': task.id},
            **{'X-Guest-Authorization': str_token_2}
        )

        # act
        response_complete_2 = api_client.post(
            f'/workflows/{workflow.id}/task-complete',
            data={'task_id': task.id},
            **{'X-Guest-Authorization': str_token_2}
        )

        # assert
        assert response_complete_1.status_code == 204
        assert response_complete_2.status_code == 400
        assert response_complete_2.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response_complete_2.data['message'] == messages.MSG_PW_0007

    def test_complete__start_is_skipped_after_return_to__ok(
        self,
        mocker,
        api_client
    ):

        """ Bug case: https://my.pneumatic.app/workflows/22291/ """

        # arrange
        mocker.patch(
            'pneumatic_backend.processes.tasks.webhooks.'
            'send_workflow_webhook.delay',
        )
        mocker.patch(
            'pneumatic_backend.processes.tasks.webhooks.'
            'send_task_webhook.delay',
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

        # act
        response_complete_2 = api_client.post(
            f'/workflows/{workflow.id}/task-complete',
            data={'task_id': task_1.id}
        )

        # assert
        assert response_complete_2.status_code == 204
        assert response_complete.status_code == 204
        assert response_run.status_code == 200
        assert response_return.status_code == 204

        workflow.refresh_from_db()
        assert workflow.current_task == 3
        task_2 = workflow.tasks.get(number=2)
        assert task_2.is_skipped is True
        assert task_2.is_completed is False
        assert task_2.date_completed is None
        assert task_2.taskperformer_set.count() == 0

    def test_revert__start_is_skipped_after_revert__ok(
        self,
        api_client,
        mocker,
    ):

        """ Bug case: https://my.pneumatic.app/workflows/22291/ """

        # arrange
        mocker.patch(
            'pneumatic_backend.processes.tasks.webhooks.'
            'send_workflow_webhook.delay',
        )
        mocker.patch(
            'pneumatic_backend.processes.tasks.webhooks.'
            'send_task_webhook.delay',
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

        response_revert = api_client.post(
            f'/workflows/{workflow.id}/task-revert',
        )

        # act
        response_complete_2 = api_client.post(
            f'/workflows/{workflow.id}/task-complete',
            data={'task_id': task_1.id}
        )

        # assert
        assert response_run.status_code == 200
        assert response_complete.status_code == 204
        assert response_complete_2.status_code == 204
        assert response_revert.status_code == 204
        workflow.refresh_from_db()
        assert workflow.current_task == 3
        task_2 = workflow.tasks.get(number=2)
        assert task_2.is_skipped is True
        assert task_2.is_completed is False
        assert task_2.date_completed is None
        assert task_2.taskperformer_set.count() == 0

    def test_complete__clear_attachment_field__delete_attachment(
        self,
        api_client
    ):

        # arrange
        user = create_test_user()
        api_client.token_authenticate(user)
        template = create_test_template(
            user=user,
            is_active=True,
            tasks_count=2
        )
        template_task_1 = template.tasks.first()
        field_template = FieldTemplate.objects.create(
            name='File Field',
            order=1,
            type=FieldType.FILE,
            is_required=False,
            task=template_task_1,
            template=template,
        )

        response_run = api_client.post(
            path=f'/templates/{template.id}/run',
            data={'name': 'Test name'}
        )

        workflow = Workflow.objects.get(id=response_run.data['id'])
        task_1 = workflow.current_task_instance
        attachment = FileAttachment.objects.create(
            name='john.cena',
            url='https://john.cena/john.cena',
            size=1488,
            account_id=user.account_id,
        )

        response_complete = api_client.post(
            f'/workflows/{workflow.id}/task-complete',
            data={
                'task_id': task_1.id,
                "output": {
                    field_template.api_name: [attachment.id]
                }
            }
        )
        workflow.refresh_from_db()

        response_revert = api_client.post(
            f'/workflows/{workflow.id}/task-revert',
        )
        workflow.refresh_from_db()
        WorkflowEvent.objects.all().delete()

        response_complete_2 = api_client.post(
            f'/workflows/{workflow.id}/task-complete',
            data={
                'task_id': task_1.id,
                "output": {
                    field_template.api_name: []
                }
            }
        )

        # act
        response = api_client.get(
            f'/workflows/{workflow.id}/events?ordering=-created'
        )

        # assert
        assert response_run.status_code == 200
        assert response_complete.status_code == 204
        assert response_revert.status_code == 204
        assert response_complete_2.status_code == 204
        assert response.status_code == 200

        assert response.data[0]['type'] == WorkflowEventType.TASK_START
        assert response.data[1]['type'] == WorkflowEventType.TASK_COMPLETE
        field_data = response.data[1]['task']['output'][0]
        assert len(field_data['attachments']) == 0
        assert field_data['value'] == ""
        assert not FileAttachment.objects.filter(
            id=attachment.id,
            output_id=task_1.output.first().id
        ).exists()

    def test_complete__not_clear_attachment_field__save_value(
        self,
        mocker,
        api_client
    ):

        # arrange
        user = create_test_user()
        api_client.token_authenticate(user)
        template = create_test_template(
            user=user,
            is_active=True,
            tasks_count=2
        )
        template_task_1 = template.tasks.first()
        field_template = FieldTemplate.objects.create(
            name='File Field',
            order=1,
            type=FieldType.FILE,
            is_required=False,
            task=template_task_1,
            template=template,
        )

        response_run = api_client.post(
            path=f'/templates/{template.id}/run',
            data={'name': 'Test name'}
        )

        workflow = Workflow.objects.get(id=response_run.data['id'])
        task_1 = workflow.current_task_instance
        attachment = FileAttachment.objects.create(
            name='john.cena',
            url='https://john.cena/john.cena',
            size=1488,
            account_id=user.account_id,
        )

        response_complete = api_client.post(
            f'/workflows/{workflow.id}/task-complete',
            data={
                'task_id': task_1.id,
                "output": {
                    field_template.api_name: [str(attachment.id)]
                }
            }
        )
        workflow.refresh_from_db()

        response_revert = api_client.post(
            f'/workflows/{workflow.id}/task-revert',
        )
        workflow.refresh_from_db()
        WorkflowEvent.objects.all().delete()

        response_complete_2 = api_client.post(
            f'/workflows/{workflow.id}/task-complete',
            data={
                'task_id': task_1.id,
                "output": {
                    field_template.api_name: [str(attachment.id)]
                }
            }
        )

        # act
        response = api_client.get(
            f'/workflows/{workflow.id}/events?ordering=-created'
        )

        # assert
        assert response_run.status_code == 200
        assert response_complete.status_code == 204
        assert response_revert.status_code == 204
        assert response_complete_2.status_code == 204
        assert response.status_code == 200
        assert len(response.data) == 2

        assert response.data[0]['type'] == WorkflowEventType.TASK_START
        assert response.data[1]['type'] == WorkflowEventType.TASK_COMPLETE
        field_data = response.data[1]['task']['output'][0]
        assert len(field_data['attachments']) == 1
        assert field_data['value'] == 'https://john.cena/john.cena'
        assert FileAttachment.objects.filter(
            id=attachment.id,
            output_id=task_1.output.first().id
        ).exists()

    def test_complete__correct_events_order__ok(
        self,
        api_client
    ):

        # arrange
        user = create_test_user()
        api_client.token_authenticate(user)
        workflow = create_test_workflow(user, tasks_count=2)
        WorkflowEvent.objects.all().delete()

        # act
        response = api_client.post(
            f'/workflows/{workflow.id}/task-complete',
            data={
                'task_id': workflow.current_task_instance.id,
            }
        )

        # assert
        assert response.status_code == 204
        events = list(
            WorkflowEvent.objects
            .on_account(user.account_id)
            .order_by('id')
            .values_list('type', flat=True)
        )
        assert events[0] == WorkflowEventType.TASK_COMPLETE
        assert events[1] == WorkflowEventType.TASK_START
