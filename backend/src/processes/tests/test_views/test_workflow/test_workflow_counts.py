import pytest

from src.accounts.enums import BillingPlanType
from src.processes.tests.fixtures import (
    create_test_user,
    create_test_workflow,
    create_test_template,
    create_test_account,
    create_test_group
)
from src.processes.enums import (
    PerformerType,
)
from src.processes.enums import (
    WorkflowStatus,
    WorkflowApiStatus
)
from src.utils.validation import ErrorCode
from src.processes.messages import workflow as messages
from src.processes.models import (
    TaskPerformer,
    TemplateOwner
)
from src.processes.enums import OwnerType

pytestmark = pytest.mark.django_db


class TestWorkflowCountsByWorkflowStarter:

    def test__no_filters__ok(self, api_client):

        # arrange
        account = create_test_account()
        user_1 = create_test_user(account=account, email='user1@test.test')
        user_2 = create_test_user(account=account, email='user2@test.test')
        create_test_workflow(user_1, is_external=True)
        create_test_workflow(user_1)
        workflow_3 = create_test_workflow(user_2)
        workflow_3.owners.add(user_1)
        workflow_4 = create_test_workflow(user_2)
        workflow_4.owners.add(user_1)
        api_client.token_authenticate(user_1)

        # act
        response = api_client.get('/workflows/count/by-workflow-starter')

        # assert
        assert response.status_code == 200
        assert len(response.data) == 3
        assert response.data[0]['type'] == 'user'
        assert response.data[0]['source_id'] == -1
        assert response.data[0]['workflows_count'] == 1
        assert response.data[1]['type'] == 'user'
        assert response.data[1]['source_id'] == user_1.id
        assert response.data[1]['workflows_count'] == 1
        assert response.data[2]['type'] == 'user'
        assert response.data[2]['source_id'] == user_2.id
        assert response.data[2]['workflows_count'] == 2

    def test__filter__all_status___ok(self, api_client):

        # arrange
        user = create_test_user()

        workflow_done = create_test_workflow(user)
        workflow_done.status = WorkflowStatus.DONE
        workflow_done.save()

        create_test_workflow(user)

        workflow_delayed = create_test_workflow(user)
        workflow_delayed.status = WorkflowStatus.DELAYED
        workflow_delayed.save()

        api_client.token_authenticate(user)

        # act
        response = api_client.get('/workflows/count/by-workflow-starter')

        # assert
        assert response.status_code == 200
        assert len(response.data) == 2
        assert response.data[0]['type'] == 'user'
        assert response.data[0]['source_id'] == -1
        assert response.data[0]['workflows_count'] == 0
        assert response.data[1]['type'] == 'user'
        assert response.data[1]['source_id'] == user.id
        assert response.data[1]['workflows_count'] == 3

    def test__filter__status_done__ok(self, api_client):

        # arrange
        account = create_test_account()
        user_1 = create_test_user(account=account, email='user1@test.test')
        user_2 = create_test_user(account=account, email='user2@test.test')
        external_workflow_done = create_test_workflow(user_1, is_external=True)
        external_workflow_done.status = WorkflowStatus.DONE
        external_workflow_done.save()
        create_test_workflow(user_1)
        workflow_3 = create_test_workflow(user_2)
        workflow_3.owners.add(user_1)
        workflow_done = create_test_workflow(user_2)
        workflow_done.status = WorkflowStatus.DONE
        workflow_done.save()
        workflow_done.owners.add(user_1)
        api_client.token_authenticate(user_1)

        # act
        response = api_client.get(
            f'/workflows/count/by-workflow-starter',
            data={
                'status': WorkflowApiStatus.DONE
            }
        )

        # assert
        assert response.status_code == 200
        assert len(response.data) == 2
        assert response.data[0]['type'] == 'user'
        assert response.data[0]['source_id'] == -1
        assert response.data[0]['workflows_count'] == 1
        assert response.data[1]['type'] == 'user'
        assert response.data[1]['source_id'] == user_2.id
        assert response.data[1]['workflows_count'] == 1

    def test__filter__status_running__ok(self, api_client):

        # arrange
        account = create_test_account()
        user_1 = create_test_user(account=account, email='user1@test.test')
        workflow_done = create_test_workflow(user_1)
        workflow_done.status = WorkflowStatus.DONE
        workflow_done.save()

        workflow_delay = create_test_workflow(user_1)
        workflow_delay.status = WorkflowStatus.DELAYED
        workflow_delay.save()

        create_test_workflow(user_1)
        api_client.token_authenticate(user_1)

        # act
        response = api_client.get(
            f'/workflows/count/by-workflow-starter',
            data={
                'status': WorkflowApiStatus.RUNNING
            }
        )

        # assert
        assert response.status_code == 200
        assert len(response.data) == 2
        assert response.data[0]['type'] == 'user'
        assert response.data[0]['source_id'] == -1
        assert response.data[0]['workflows_count'] == 0
        assert response.data[1]['type'] == 'user'
        assert response.data[1]['source_id'] == user_1.id
        assert response.data[1]['workflows_count'] == 1

    def test__filter__status_delayed__ok(self, api_client):

        # arrange
        account = create_test_account()
        user_1 = create_test_user(account=account, email='user1@test.test')

        workflow_delay = create_test_workflow(user_1)
        workflow_delay.status = WorkflowStatus.DELAYED
        workflow_delay.save()

        api_client.token_authenticate(user_1)

        # act
        response = api_client.get(
            f'/workflows/count/by-workflow-starter',
            data={
                'status': WorkflowApiStatus.DELAYED
            }
        )

        # assert
        assert response.status_code == 200
        assert len(response.data) == 2
        assert response.data[0]['type'] == 'user'
        assert response.data[0]['source_id'] == -1
        assert response.data[0]['workflows_count'] == 0
        assert response.data[1]['type'] == 'user'
        assert response.data[1]['source_id'] == user_1.id
        assert response.data[1]['workflows_count'] == 1

    def test__filter__status_invalid__validation_error(self, api_client):

        # arrange
        account = create_test_account()
        user_1 = create_test_user(account=account, email='user1@test.test')
        workflow_delay = create_test_workflow(user_1, is_external=True)
        workflow_delay.status = WorkflowStatus.DELAYED
        workflow_delay.save()
        create_test_workflow(user_1)
        api_client.token_authenticate(user_1)

        # act
        response = api_client.get(
            f'/workflows/count/by-workflow-starter',
            data={'status': 'delayed'}
        )

        # assert
        assert response.status_code == 400
        message = '"delayed" is not a valid choice.'
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['message'] == message
        assert response.data['details']['name'] == 'status'
        assert response.data['details']['reason'] == message

    def test__filter__template_ids__ok(self, api_client):

        # arrange
        account = create_test_account()
        user = create_test_user(account=account, email='user1@test.test')
        template_1 = create_test_template(user, tasks_count=1)
        template_2 = create_test_template(user, tasks_count=1)
        template_3 = create_test_template(user, tasks_count=1)
        create_test_workflow(user, template=template_1, is_external=True)
        create_test_workflow(user, template=template_2)
        create_test_workflow(user, template=template_3)
        api_client.token_authenticate(user)

        # act
        response = api_client.get(
            '/workflows/count/by-workflow-starter',
            data={
                'template_ids': f'{template_1.id},{template_3.id}'
            }
        )

        # assert
        assert response.status_code == 200
        assert len(response.data) == 2
        assert response.data[0]['type'] == 'user'
        assert response.data[0]['source_id'] == -1
        assert response.data[0]['workflows_count'] == 1
        assert response.data[1]['type'] == 'user'
        assert response.data[1]['source_id'] == user.id
        assert response.data[1]['workflows_count'] == 1

    def test__filter__template_ids_invalid__validation_error(
        self,
        api_client
    ):

        # arrange
        account = create_test_account()
        user = create_test_user(account=account, email='user1@test.test')
        api_client.token_authenticate(user)

        # act
        response = api_client.get(
            '/workflows/count/by-workflow-starter',
            data={'template_ids': 'null'}
        )

        # assert
        assert response.status_code == 400
        message = 'Value should be a list of integers.'
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['message'] == message
        assert response.data['details']['name'] == 'template_ids'
        assert response.data['details']['reason'] == message

    def test__filter__current_performer_ids__ok(self, api_client):

        # arrange
        account = create_test_account()
        workflow_starter = create_test_user(account=account)
        workflow = create_test_workflow(user=workflow_starter, tasks_count=1)
        request_user = create_test_user(
            account=account,
            email='user3@test.test',
            is_account_owner=False
        )
        workflow.owners.add(request_user)
        task = workflow.tasks.get(number=1)
        task.taskperformer_set.all().delete()
        performer_1 = create_test_user(
            account=account,
            email='performer_1@test.test',
            is_account_owner=False
        )
        TaskPerformer.objects.create(
            task=task,
            user=performer_1,
        )
        api_client.token_authenticate(request_user)

        # act
        response = api_client.get(
            '/workflows/count/by-workflow-starter',
            data={
                'current_performer_ids': f'{performer_1.id}'
            }
        )

        # assert
        assert response.status_code == 200
        assert len(response.data) == 2
        assert response.data[1]['type'] == 'user'
        assert response.data[1]['source_id'] == workflow_starter.id
        assert response.data[1]['workflows_count'] == 1

    def test__filter__current_performer_ids_multiple__ok(self, api_client):

        # arrange
        account = create_test_account()
        workflow_starter = create_test_user(account=account)
        workflow_1 = create_test_workflow(user=workflow_starter, tasks_count=1)
        workflow_2 = create_test_workflow(user=workflow_starter, tasks_count=1)
        request_user = create_test_user(
            account=account,
            email='request_user@test.test',
            is_account_owner=False
        )

        performer_1 = create_test_user(
            account=account,
            email='performer_1@test.test',
            is_account_owner=False
        )
        workflow_1.owners.add(request_user)
        task_1 = workflow_1.tasks.get(number=1)
        task_1.taskperformer_set.all().delete()
        TaskPerformer.objects.create(
            task=task_1,
            user=performer_1,
        )

        performer_2 = create_test_user(
            account=account,
            email='performer_2@test.test',
            is_account_owner=False
        )
        workflow_2.owners.add(request_user)
        task_2 = workflow_2.tasks.get(number=1)
        task_2.taskperformer_set.all().delete()
        TaskPerformer.objects.create(
            task=task_2,
            user=performer_2,
        )

        api_client.token_authenticate(request_user)

        # act
        response = api_client.get(
            '/workflows/count/by-workflow-starter',
            data={
                'current_performer_ids': f'{performer_1.id}, {performer_2.id}'
            }
        )

        # assert
        assert response.status_code == 200
        assert len(response.data) == 2
        assert response.data[1]['type'] == 'user'
        assert response.data[1]['source_id'] == workflow_starter.id
        assert response.data[1]['workflows_count'] == 2

    def test__filter__current_performer_ids_invalid__validation_error(
        self,
        api_client
    ):

        # arrange
        account = create_test_account()
        user = create_test_user(account=account, email='user1@test.test')
        api_client.token_authenticate(user)

        # act
        response = api_client.get(
            '/workflows/count/by-workflow-starter',
            data={'current_performer_ids': 'None'}
        )

        # assert
        assert response.status_code == 400
        message = 'Value should be a list of integers.'
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['message'] == message
        assert response.data['details']['name'] == 'current_performer_ids'
        assert response.data['details']['reason'] == message

    def test__filter__inconsistent_filters__validation_error(
        self,
        api_client
    ):

        # arrange
        account = create_test_account()
        user = create_test_user(account=account, email='user1@test.test')
        api_client.token_authenticate(user)

        # act
        response = api_client.get(
            '/workflows/count/by-workflow-starter',
            data={
                'status': WorkflowApiStatus.DONE,
                'current_performer_ids': user.id
            }
        )

        # assert
        assert response.status_code == 400
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['message'] == messages.MSG_PW_0067

    def test__filter__current_performer_group_ids__ok(self, api_client):

        # arrange
        account = create_test_account()
        workflow_starter = create_test_user(account=account)
        workflow = create_test_workflow(user=workflow_starter, tasks_count=1)
        request_user = create_test_user(
            account=account,
            email='request_user@test.test',
            is_account_owner=False
        )

        workflow.owners.add(request_user)
        task = workflow.tasks.get(number=1)
        task.taskperformer_set.all().delete()
        group_user = create_test_user(
            account=account,
            email='user2@test.test',
            is_account_owner=False
        )
        group = create_test_group(account, users=[group_user])
        TaskPerformer.objects.create(
            task_id=task.id,
            type=PerformerType.GROUP,
            group_id=group.id,
        )
        api_client.token_authenticate(request_user)

        # act
        response = api_client.get(
            '/workflows/count/by-workflow-starter',
            data={
                'current_performer_group_ids': f'{group.id}'
            }
        )

        # assert
        assert response.status_code == 200
        assert len(response.data) == 2
        assert response.data[1]['type'] == 'user'
        assert response.data[1]['source_id'] == workflow_starter.id
        assert response.data[1]['workflows_count'] == 1

    def test__filter__current_performer_group_ids_multiple__ok(
        self,
        api_client
    ):

        # arrange
        account = create_test_account()
        workflow_starter = create_test_user(account=account)
        workflow_1 = create_test_workflow(user=workflow_starter, tasks_count=1)
        workflow_2 = create_test_workflow(user=workflow_starter, tasks_count=1)
        request_user = create_test_user(
            account=account,
            email='request_user@test.test',
            is_account_owner=False
        )

        group_user_1 = create_test_user(
            account=account,
            email='group_user_1@test.test',
            is_account_owner=False
        )
        workflow_1.owners.add(request_user)
        task_1 = workflow_1.tasks.get(number=1)
        task_1.taskperformer_set.all().delete()
        group_1 = create_test_group(
            account,
            users=[group_user_1]
        )
        TaskPerformer.objects.create(
            task_id=task_1.id,
            type=PerformerType.GROUP,
            group_id=group_1.id,
        )

        group_user_2 = create_test_user(
            account=account,
            email='group_user_2@test.test',
            is_account_owner=False
        )
        workflow_2.owners.add(request_user)
        task_2 = workflow_2.tasks.get(number=1)
        task_2.taskperformer_set.all().delete()
        group_2 = create_test_group(
            account,
            users=[group_user_2]
        )
        TaskPerformer.objects.create(
            task_id=task_2.id,
            type=PerformerType.GROUP,
            group_id=group_2.id,
        )
        api_client.token_authenticate(request_user)

        # act
        response = api_client.get(
            '/workflows/count/by-workflow-starter',
            data={
                'current_performer_group_ids': f'{group_1.id},{group_2.id}'
            }
        )

        # assert
        assert response.status_code == 200
        assert len(response.data) == 2
        assert response.data[1]['type'] == 'user'
        assert response.data[1]['source_id'] == workflow_starter.id
        assert response.data[1]['workflows_count'] == 2

    def test__filter__current_performer_user_and_group__ok(self, api_client):

        # arrange
        account = create_test_account()
        workflow_starter = create_test_user(account=account)
        workflow_1 = create_test_workflow(user=workflow_starter, tasks_count=1)
        workflow_2 = create_test_workflow(user=workflow_starter, tasks_count=1)
        request_user = create_test_user(
            account=account,
            email='user3@test.test',
            is_account_owner=False
        )
        workflow_1.owners.add(request_user)
        task_1 = workflow_1.tasks.get(number=1)
        task_1.taskperformer_set.all().delete()
        performer = create_test_user(
            account=account,
            email='performer_1@test.test',
            is_account_owner=False
        )
        TaskPerformer.objects.create(
            task=task_1,
            user=performer,
        )

        group_user = create_test_user(
            account=account,
            email='group_user_2@test.test',
            is_account_owner=False
        )
        workflow_2.owners.add(request_user)
        task_2 = workflow_2.tasks.get(number=1)
        task_2.taskperformer_set.all().delete()
        group = create_test_group(
            account,
            users=[group_user]
        )
        TaskPerformer.objects.create(
            task_id=task_2.id,
            type=PerformerType.GROUP,
            group_id=group.id,
        )

        api_client.token_authenticate(request_user)

        # act
        response = api_client.get(
            '/workflows/count/by-workflow-starter',
            data={
                'current_performer_ids': f'{performer.id}',
                'current_performer_group_ids': f'{group.id}'
            }
        )

        # assert
        assert response.status_code == 200
        assert len(response.data) == 2
        assert response.data[1]['type'] == 'user'
        assert response.data[1]['source_id'] == workflow_starter .id
        assert response.data[1]['workflows_count'] == 2

    def test__not_template_owner__not_found(self, api_client):

        # arrange
        account = create_test_account(
            'plan kapkan',
            plan=BillingPlanType.PREMIUM
        )
        user_1 = create_test_user(account=account, email='user1@test.test')
        user_2 = create_test_user(account=account, email='user2@test.test')
        create_test_workflow(user_1)
        create_test_workflow(user_1, is_external=True)

        api_client.token_authenticate(user_2)

        # act
        response = api_client.get('/workflows/count/by-workflow-starter')

        # assert
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]['type'] == 'user'
        assert response.data[0]['source_id'] == -1
        assert response.data[0]['workflows_count'] == 0


class TestWorkflowCountsByCPerformer:

    def test__user_performer__ok(self, api_client):

        # arrange
        account = create_test_account()
        user_1 = create_test_user(account=account, email='user1@test.test')
        user_2 = create_test_user(
            account=account,
            email='user2@test.test',
            is_account_owner=False
        )
        create_test_workflow(user_1, is_external=True)
        create_test_workflow(user_1)
        workflow_3 = create_test_workflow(user_2)
        workflow_3.owners.add(user_1)
        api_client.token_authenticate(user_1)

        # act
        response = api_client.get('/workflows/count/by-current-performer')

        # assert
        assert response.status_code == 200
        assert len(response.data) == 2
        assert response.data[0]['type'] == 'user'
        assert response.data[0]['source_id'] == user_1.id
        assert response.data[0]['workflows_count'] == 2
        assert response.data[1]['type'] == 'user'
        assert response.data[1]['source_id'] == user_2.id
        assert response.data[1]['workflows_count'] == 1

    def test__group_performer__ok(self, api_client):

        # arrange
        account = create_test_account()
        owner = create_test_user(account=account, is_account_owner=True)
        workflow = create_test_workflow(owner)
        user_1 = create_test_user(
            account=account,
            email='user1@test.test',
            is_account_owner=False
        )
        workflow.owners.add(user_1)
        group = create_test_group(account, users=[user_1])
        task = workflow.tasks.get(number=1)
        TaskPerformer.objects.create(
            task_id=task.id,
            type=PerformerType.GROUP,
            group_id=group.id,
        )
        api_client.token_authenticate(user_1)

        # act
        response = api_client.get('/workflows/count/by-current-performer')

        # assert
        assert response.status_code == 200
        assert len(response.data) == 3
        assert response.data[0]['type'] == 'group'
        assert response.data[0]['source_id'] == group.id
        assert response.data[0]['workflows_count'] == 1

    def test__filter__all_status___ok(self, api_client):

        # arrange
        user = create_test_user()

        workflow_done = create_test_workflow(user)
        workflow_done.status = WorkflowStatus.DONE
        workflow_done.save()

        create_test_workflow(user)

        workflow_delayed = create_test_workflow(user)
        workflow_delayed.status = WorkflowStatus.DELAYED
        workflow_delayed.save()

        api_client.token_authenticate(user)

        # act
        response = api_client.get('/workflows/count/by-current-performer')

        # assert
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]['type'] == 'user'
        assert response.data[0]['source_id'] == user.id
        assert response.data[0]['workflows_count'] == 1

    def test__filter__template_ids__ok(self, api_client):

        # arrange
        account = create_test_account()
        user = create_test_user(account=account, email='user1@test.test')
        template_1 = create_test_template(user, tasks_count=1)
        template_2 = create_test_template(user, tasks_count=1)
        template_3 = create_test_template(user, tasks_count=1)
        create_test_workflow(user, template=template_1, is_external=True)
        create_test_workflow(user, template=template_2)
        create_test_workflow(user, template=template_3)
        api_client.token_authenticate(user)

        # act
        response = api_client.get(
            '/workflows/count/by-current-performer',
            data={
                'template_ids': f'{template_1.id},{template_3.id}'
            }
        )

        # assert
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]['type'] == 'user'
        assert response.data[0]['source_id'] == user.id
        assert response.data[0]['workflows_count'] == 2

    def test__filter__template_ids_invalid__validation_error(
        self,
        api_client
    ):

        # arrange
        account = create_test_account()
        user = create_test_user(account=account, email='user1@test.test')
        api_client.token_authenticate(user)

        # act
        response = api_client.get(
            '/workflows/count/by-current-performer',
            data={'template_ids': 'null'}
        )

        # assert
        assert response.status_code == 400
        message = 'Value should be a list of integers.'
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['message'] == message
        assert response.data['details']['name'] == 'template_ids'
        assert response.data['details']['reason'] == message

    def test__filter__template_task_api_names__ok(self, api_client):

        # arrange
        account = create_test_account()
        user_1 = create_test_user(account=account, email='user1@test.test')
        user_2 = create_test_user(account=account, email='user2@test.test')
        template_1 = create_test_template(user_1, tasks_count=1)
        template_task_1_1 = template_1.tasks.get(number=1)

        template_2 = create_test_template(user_1, tasks_count=1)
        template_3 = create_test_template(user_1, tasks_count=2)
        template_task_3_1 = template_3.tasks.get(number=1)
        template_task_3_1.add_raw_performer(user_2)
        template_task_3_2 = template_3.tasks.get(number=2)

        workflow_1 = create_test_workflow(
            user_1,
            template=template_1,
            is_external=True
        )
        workflow_1.owners.add(user_2)
        workflow_2 = create_test_workflow(user_1, template=template_2)
        workflow_2.owners.add(user_2)
        workflow_3 = create_test_workflow(user_1, template=template_3)
        workflow_3.owners.add(user_2)

        api_client.token_authenticate(user_2)

        template_task_api_names = (
            f'{template_task_1_1.api_name},'
            f'{template_task_3_1.api_name},'
            f'{template_task_3_2.api_name}'
        )

        # act
        response = api_client.get(
            '/workflows/count/by-current-performer',
            data={'template_task_api_names': template_task_api_names}
        )

        # assert
        assert response.status_code == 200
        assert len(response.data) == 2
        assert response.data[0]['type'] == 'user'
        assert response.data[0]['source_id'] == user_1.id
        assert response.data[0]['workflows_count'] == 2
        assert response.data[1]['type'] == 'user'
        assert response.data[1]['source_id'] == user_2.id
        assert response.data[1]['workflows_count'] == 1

    def test__filter__template_task_ids__ok(self, api_client):

        # arrange
        account = create_test_account()
        user_1 = create_test_user(account=account, email='user1@test.test')
        user_2 = create_test_user(account=account, email='user2@test.test')
        template_1 = create_test_template(user_1, tasks_count=1)
        template_task_1_1 = template_1.tasks.get(number=1)

        template_2 = create_test_template(user_1, tasks_count=1)
        template_3 = create_test_template(user_1, tasks_count=2)
        template_task_3_1 = template_3.tasks.get(number=1)
        template_task_3_1.add_raw_performer(user_2)
        template_task_3_2 = template_3.tasks.get(number=2)

        workflow_1 = create_test_workflow(
            user_1,
            template=template_1,
            is_external=True
        )
        workflow_1.owners.add(user_2)
        workflow_2 = create_test_workflow(user_1, template=template_2)
        workflow_2.owners.add(user_2)
        workflow_3 = create_test_workflow(user_1, template=template_3)
        workflow_3.owners.add(user_2)
        api_client.token_authenticate(user_2)

        template_task_api_names = (
            f'{template_task_1_1.id},'
            f'{template_task_3_1.id},'
            f'{template_task_3_2.id}'
        )

        # act
        response = api_client.get(
            '/workflows/count/by-current-performer',
            data={'template_task_ids': template_task_api_names}
        )

        # assert
        assert response.status_code == 200
        assert len(response.data) == 2
        assert response.data[0]['type'] == 'user'
        assert response.data[0]['source_id'] == user_1.id
        assert response.data[0]['workflows_count'] == 2
        assert response.data[1]['type'] == 'user'
        assert response.data[1]['source_id'] == user_2.id
        assert response.data[1]['workflows_count'] == 1

    def test__filter__workflow_starter_ids__ok(self, api_client):

        # arrange
        account = create_test_account(plan=BillingPlanType.PREMIUM)
        user_1 = create_test_user(account=account, email='user1@test.test')
        user_2 = create_test_user(account=account, email='user2@test.test')
        create_test_group(account, users=[user_1, user_2])
        create_test_user(account=account, email='user3@test.test')
        template_1 = create_test_template(user_1, is_active=True)
        template_2 = create_test_template(user_2, is_active=True)
        TemplateOwner.objects.create(
            template=template_2,
            account=account,
            type=OwnerType.USER,
            user_id=user_1.id,
        )

        create_test_workflow(user_1, template=template_1)
        create_test_workflow(user_2, template=template_2)
        api_client.token_authenticate(user_1)

        # act
        response = api_client.get(
            '/workflows/count/by-current-performer',
            data={'workflow_starter_ids': f'{user_1.id},{user_2.id}'}
        )

        # assert
        assert response.status_code == 200
        assert len(response.data) == 2
        assert response.data[0]['type'] == 'user'
        assert response.data[0]['source_id'] == user_1.id
        assert response.data[0]['workflows_count'] == 1
        assert response.data[1]['type'] == 'user'
        assert response.data[1]['source_id'] == user_2.id
        assert response.data[1]['workflows_count'] == 1

    def test__filter__workflow_starter_ids_and_external_workflows__ok(
        self,
        api_client
    ):

        # arrange
        account = create_test_account(plan=BillingPlanType.PREMIUM)
        user_1 = create_test_user(account=account, email='user1@test.test')
        user_2 = create_test_user(account=account, email='user2@test.test')
        create_test_user(account=account, email='user3@test.test')
        template_1 = create_test_template(user_1, is_active=True)
        template_2 = create_test_template(
            user_2,
            is_active=True,
            is_public=True
        )
        TemplateOwner.objects.create(
            template=template_2,
            account=account,
            type=OwnerType.USER,
            user_id=user_1.id,
        )

        create_test_workflow(user_1, template=template_1)
        create_test_workflow(user_2, template=template_2, is_external=True)
        api_client.token_authenticate(user_1)

        # act
        response = api_client.get(
            '/workflows/count/by-current-performer',
            data={
                'workflow_starter_ids': f'{user_1.id}',
                'is_external': True
            }
        )

        # assert
        assert response.status_code == 200
        assert len(response.data) == 2
        assert response.data[0]['type'] == 'user'
        assert response.data[0]['source_id'] == user_1.id
        assert response.data[0]['workflows_count'] == 1
        assert response.data[1]['type'] == 'user'
        assert response.data[1]['source_id'] == user_2.id
        assert response.data[1]['workflows_count'] == 1

    def test__filter__external_workflows__ok(
        self,
        api_client
    ):

        # arrange
        account = create_test_account(plan=BillingPlanType.PREMIUM)
        user_1 = create_test_user(account=account, email='user1@test.test')
        user_2 = create_test_user(account=account, email='user2@test.test')
        create_test_user(account=account, email='user3@test.test')
        template_1 = create_test_template(user_1, is_active=True)
        template_2 = create_test_template(
            user_2,
            is_active=True,
            is_public=True
        )
        TemplateOwner.objects.create(
            template=template_2,
            account=account,
            type=OwnerType.USER,
            user_id=user_1.id,
        )

        create_test_workflow(user_1, template=template_1)
        create_test_workflow(user_2, template=template_2, is_external=True)
        api_client.token_authenticate(user_1)

        # act
        response = api_client.get(
            '/workflows/count/by-current-performer',
            data={'is_external': True}
        )

        # assert
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]['type'] == 'user'
        assert response.data[0]['source_id'] == user_2.id
        assert response.data[0]['workflows_count'] == 1

    def test__not_template_owner__not_found(self, api_client):

        # arrange
        account = create_test_account(
            'plan kapkan',
            plan=BillingPlanType.PREMIUM
        )
        user_1 = create_test_user(account=account, email='user1@test.test')
        user_2 = create_test_user(account=account, email='user2@test.test')
        create_test_workflow(user_1)
        create_test_workflow(user_1)

        api_client.token_authenticate(user_2)

        # act
        response = api_client.get('/workflows/count/by-current-performer')

        # assert
        assert response.status_code == 200
        assert len(response.data) == 0


class TestWorkflowCountsByTemplateTask:

    def test__no_filters__ok(self, api_client):

        # arrange
        account = create_test_account()
        user = create_test_user(account=account)
        template = create_test_template(user=user, tasks_count=3)
        template_task_1 = template.tasks.get(number=1)
        template_task_2 = template.tasks.get(number=2)
        template_task_3 = template.tasks.get(number=3)
        create_test_workflow(user=user, template=template)
        create_test_workflow(user=user, template=template)
        create_test_workflow(
            user=user,
            template=template,
            active_task_number=2
        )
        api_client.token_authenticate(user)

        # act
        response = api_client.get('/workflows/count/by-template-task')

        # assert
        assert response.status_code == 200
        assert len(response.data) == 3
        assert response.data[0]['template_task_id'] == template_task_1.id
        assert (
            response.data[0]['template_task_api_name'] ==
            template_task_1.api_name
        )
        assert response.data[0]['workflows_count'] == 2
        assert (
            response.data[1]['template_task_id'] ==
            template_task_2.id
        )
        assert (
            response.data[1]['template_task_api_name'] ==
            template_task_2.api_name
        )
        assert response.data[1]['workflows_count'] == 1
        assert (
            response.data[2]['template_task_id'] ==
            template_task_3.id
        )
        assert (
            response.data[2]['template_task_api_name'] ==
            template_task_3.api_name
        )
        assert response.data[2]['workflows_count'] == 0

    def test__filter__all_status__ok(self, api_client):

        # arrange
        account = create_test_account()
        user = create_test_user(account=account)
        template = create_test_template(user=user, tasks_count=2)
        template_task_1 = template.tasks.get(number=1)
        template_task_2 = template.tasks.get(number=2)
        create_test_workflow(
            template=template,
            user=user,
            active_task_number=2
        )
        create_test_workflow(
            template=template,
            user=user,
            status=WorkflowStatus.DONE
        )
        create_test_workflow(
            user=user,
            template=template,
            active_task_number=2,
            status=WorkflowStatus.DELAYED
        )
        api_client.token_authenticate(user)

        # act
        response = api_client.get('/workflows/count/by-template-task')

        # assert
        assert response.status_code == 200
        assert len(response.data) == 2
        assert response.data[0]['template_task_id'] == template_task_1.id
        assert (
            response.data[0]['template_task_api_name'] ==
            template_task_1.api_name
        )
        assert response.data[0]['workflows_count'] == 1
        assert response.data[1]['template_task_id'] == template_task_2.id
        assert (
            response.data[1]['template_task_api_name'] ==
            template_task_2.api_name
        )
        assert response.data[1]['workflows_count'] == 2

    def test__filter__status_done__ok(self, api_client):

        # arrange
        account = create_test_account()
        user = create_test_user(account=account)
        template = create_test_template(user=user, tasks_count=2)
        template_task_1 = template.tasks.get(number=1)
        template_task_2 = template.tasks.get(number=2)
        create_test_workflow(
            template=template,
            user=user
        )
        create_test_workflow(
            template=template,
            user=user,
            status=WorkflowStatus.DONE,
            active_task_number=2
        )
        create_test_workflow(
            user=user,
            template=template,
            status=WorkflowStatus.DELAYED
        )
        api_client.token_authenticate(user)

        # act
        response = api_client.get(
            f'/workflows/count/by-template-task',
            data={
                'status': WorkflowApiStatus.DONE
            }
        )

        # assert
        assert response.status_code == 200
        assert len(response.data) == 2
        assert response.data[0]['template_task_id'] == template_task_1.id
        assert (
            response.data[0]['template_task_api_name'] ==
            template_task_1.api_name
        )
        assert response.data[0]['workflows_count'] == 0
        assert response.data[1]['template_task_id'] == template_task_2.id
        assert (
            response.data[1]['template_task_api_name'] ==
            template_task_2.api_name
        )
        assert response.data[1]['workflows_count'] == 1

    def test__filter__status_running__ok(self, api_client):

        # arrange
        account = create_test_account()
        user = create_test_user(account=account)
        template = create_test_template(user=user, tasks_count=2)
        template_task_1 = template.tasks.get(number=1)
        template_task_2 = template.tasks.get(number=2)
        create_test_workflow(
            template=template,
            user=user,
            active_task_number=2
        )
        create_test_workflow(
            template=template,
            user=user,
            status=WorkflowStatus.DONE
        )
        create_test_workflow(
            user=user,
            template=template,
            active_task_number=2,
            status=WorkflowStatus.DELAYED
        )
        api_client.token_authenticate(user)

        # act
        response = api_client.get(
            f'/workflows/count/by-template-task',
            data={
                'status': WorkflowApiStatus.RUNNING
            }
        )

        # assert
        assert response.status_code == 200
        assert len(response.data) == 2
        assert response.data[0]['template_task_id'] == template_task_1.id
        assert (
            response.data[0]['template_task_api_name'] ==
            template_task_1.api_name
        )
        assert response.data[0]['workflows_count'] == 0
        assert response.data[1]['template_task_id'] == template_task_2.id
        assert (
            response.data[1]['template_task_api_name'] ==
            template_task_2.api_name
        )
        assert response.data[1]['workflows_count'] == 1

    def test__filter__status_delayed__ok(self, api_client):

        # arrange
        account = create_test_account()
        user = create_test_user(account=account)
        template = create_test_template(user=user, tasks_count=2)
        template_task_1 = template.tasks.get(number=1)
        template_task_2 = template.tasks.get(number=2)
        create_test_workflow(
            user=user,
            template=template,
            active_task_number=2,
            status=WorkflowStatus.DELAYED,
        )
        api_client.token_authenticate(user)

        # act
        response = api_client.get(
            f'/workflows/count/by-template-task',
            data={
                'status': WorkflowApiStatus.DELAYED
            }
        )

        # assert
        assert response.status_code == 200
        assert len(response.data) == 2
        assert response.data[0]['template_task_id'] == template_task_1.id
        assert (
            response.data[0]['template_task_api_name'] ==
            template_task_1.api_name
        )
        assert response.data[0]['workflows_count'] == 0
        assert response.data[1]['template_task_id'] == template_task_2.id
        assert (
            response.data[1]['template_task_api_name'] ==
            template_task_2.api_name
        )
        assert response.data[1]['workflows_count'] == 1

    def test__filter__status_invalid__validation_error(self, api_client):

        # arrange
        account = create_test_account()
        user = create_test_user(account=account)
        template = create_test_template(user=user, tasks_count=2)
        create_test_workflow(
            template=template,
            user=user
        )
        api_client.token_authenticate(user)

        # act
        response = api_client.get(
            f'/workflows/count/by-template-task',
            data={'status': 'delayed'}
        )

        # assert
        assert response.status_code == 400
        message = '"delayed" is not a valid choice.'
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['message'] == message
        assert response.data['details']['name'] == 'status'
        assert response.data['details']['reason'] == message

    def test__filter__template_ids__ok(self, api_client):

        # arrange
        account = create_test_account()
        user = create_test_user(account=account)
        template_1 = create_test_template(user=user, tasks_count=1)
        template_task_1 = template_1.tasks.get(number=1)
        template_2 = create_test_template(user=user, tasks_count=1)
        template_3 = create_test_template(user=user, tasks_count=2)
        template_task_31 = template_3.tasks.get(number=1)
        template_task_32 = template_3.tasks.get(number=2)

        create_test_workflow(
            template=template_1,
            user=user
        )
        create_test_workflow(
            template=template_2,
            user=user
        )
        create_test_workflow(
            template=template_3,
            user=user,
            active_task_number=2
        )

        api_client.token_authenticate(user)

        # act
        response = api_client.get(
            f'/workflows/count/by-template-task',
            data={
                'template_ids': f'{template_1.id},{template_3.id}'
            }
        )

        # assert
        assert response.status_code == 200
        assert len(response.data) == 3
        assert response.data[0]['template_task_id'] == template_task_1.id
        assert (
            response.data[0]['template_task_api_name'] ==
            template_task_1.api_name
        )
        assert response.data[0]['workflows_count'] == 1
        assert response.data[1]['template_task_id'] == template_task_31.id
        assert (
            response.data[1]['template_task_api_name'] ==
            template_task_31.api_name
        )
        assert response.data[1]['workflows_count'] == 0
        assert response.data[2]['template_task_id'] == template_task_32.id
        assert (
            response.data[2]['template_task_api_name'] ==
            template_task_32.api_name
        )
        assert response.data[2]['workflows_count'] == 1

    def test__filter__current_performer_ids__ok(
        self,
        api_client
    ):
        # arrange
        account = create_test_account()
        user = create_test_user(account=account)
        user2 = create_test_user(account=account, email='owner@test.test')
        group = create_test_group(account, users=[user])
        template_1 = create_test_template(user=user, tasks_count=1)
        TemplateOwner.objects.create(
            template=template_1,
            account=account,
            type=OwnerType.USER,
            user_id=user2.id,
        )
        template_2 = create_test_template(user=user2, tasks_count=2)
        template_3 = create_test_template(user=user, tasks_count=1)
        TemplateOwner.objects.create(
            template=template_3,
            account=account,
            type=OwnerType.USER,
            user_id=user2.id,
        )
        template_task_1 = template_1.tasks.get(number=1)
        template_task_2_1 = template_2.tasks.get(number=1)
        template_task_2_2 = template_2.tasks.get(number=2)
        template_task_3 = template_3.tasks.get(number=1)
        template_task_3.delete_raw_performers()
        template_task_3.add_raw_performer(
            performer_type=PerformerType.GROUP,
            group=group
        )

        create_test_workflow(
            template=template_1,
            user=user
        )
        create_test_workflow(
            template=template_2,
            user=user2
        )
        create_test_workflow(
            template=template_3,
            user=user
        )

        api_client.token_authenticate(user2)

        # act
        response = api_client.get(
            f'/workflows/count/by-template-task',
            data={'current_performer_ids': user.id}
        )

        # assert
        assert response.status_code == 200
        assert len(response.data) == 4
        assert response.data[0]['workflows_count'] == 1
        assert response.data[0]['template_task_id'] == template_task_1.id
        assert (
            response.data[0]['template_task_api_name'] ==
            template_task_1.api_name
        )
        assert response.data[1]['workflows_count'] == 0
        assert response.data[1]['template_task_id'] == template_task_2_1.id
        assert (
            response.data[1]['template_task_api_name'] ==
            template_task_2_1.api_name
        )
        assert response.data[2]['workflows_count'] == 0
        assert response.data[2]['template_task_id'] == template_task_2_2.id
        assert (
            response.data[2]['template_task_api_name'] ==
            template_task_2_2.api_name
        )
        assert response.data[3]['workflows_count'] == 1
        assert response.data[3]['template_task_id'] == template_task_3.id
        assert (
            response.data[3]['template_task_api_name'] ==
            template_task_3.api_name
        )

    def test__filter__current_performer_group_ids__ok(
        self,
        api_client
    ):
        # arrange
        account = create_test_account()
        user = create_test_user(account=account)
        user2 = create_test_user(account=account, email='owner@test.test')
        group = create_test_group(account, users=[user])
        template_1 = create_test_template(user=user, tasks_count=1)
        TemplateOwner.objects.create(
            template=template_1,
            account=account,
            type=OwnerType.USER,
            user_id=user2.id,
        )
        template_2 = create_test_template(user=user2, tasks_count=2)
        template_3 = create_test_template(user=user, tasks_count=1)
        TemplateOwner.objects.create(
            template=template_3,
            account=account,
            type=OwnerType.USER,
            user_id=user2.id,
        )
        template_task_1 = template_1.tasks.get(number=1)
        template_task_2_1 = template_2.tasks.get(number=1)
        template_task_2_2 = template_2.tasks.get(number=2)
        template_task_3 = template_3.tasks.get(number=1)
        template_task_1.add_raw_performer(
            performer_type=PerformerType.GROUP,
            group=group
        )

        create_test_workflow(
            template=template_1,
            user=user
        )
        create_test_workflow(
            template=template_2,
            user=user2
        )
        create_test_workflow(
            template=template_3,
            user=user
        )

        api_client.token_authenticate(user2)

        # act
        response = api_client.get(
            f'/workflows/count/by-template-task',
            data={
                'current_performer_group_ids': group.id
            }
        )

        # assert
        assert response.status_code == 200
        assert len(response.data) == 4
        assert response.data[0]['workflows_count'] == 1
        assert response.data[0]['template_task_id'] == template_task_1.id
        assert (
            response.data[0]['template_task_api_name'] ==
            template_task_1.api_name
        )
        assert response.data[1]['workflows_count'] == 0
        assert response.data[1]['template_task_id'] == template_task_2_1.id
        assert (
            response.data[1]['template_task_api_name'] ==
            template_task_2_1.api_name
        )
        assert response.data[2]['workflows_count'] == 0
        assert response.data[2]['template_task_id'] == template_task_2_2.id
        assert (
            response.data[2]['template_task_api_name'] ==
            template_task_2_2.api_name
        )
        assert response.data[3]['workflows_count'] == 0
        assert response.data[3]['template_task_id'] == template_task_3.id
        assert (
            response.data[3]['template_task_api_name'] ==
            template_task_3.api_name
        )

    def test__filter__current_performer_and_performer_group_ids__ok(
        self,
        api_client
    ):
        # arrange
        account = create_test_account()
        user = create_test_user(account=account)
        user2 = create_test_user(account=account, email='owner@test.test')
        group = create_test_group(account, users=[user2])
        template_1 = create_test_template(user=user, tasks_count=1)
        TemplateOwner.objects.create(
            template=template_1,
            account=account,
            type=OwnerType.USER,
            user_id=user2.id,
        )
        template_2 = create_test_template(user=user2, tasks_count=2)
        template_3 = create_test_template(user=user, tasks_count=1)
        TemplateOwner.objects.create(
            template=template_3,
            account=account,
            type=OwnerType.USER,
            user_id=user2.id,
        )
        template_task_1 = template_1.tasks.get(number=1)
        template_task_2_1 = template_2.tasks.get(number=1)
        template_task_2_2 = template_2.tasks.get(number=2)
        template_task_3 = template_3.tasks.get(number=1)
        template_task_1.add_raw_performer(
            performer_type=PerformerType.GROUP,
            group=group
        )

        create_test_workflow(
            template=template_1,
            user=user
        )
        create_test_workflow(
            template=template_2,
            user=user2
        )
        create_test_workflow(
            template=template_3,
            user=user
        )

        api_client.token_authenticate(user2)

        # act
        response = api_client.get(
            f'/workflows/count/by-template-task',
            data={
                'current_performer_ids': user.id,
                'current_performer_group_ids': group.id
            }
        )

        # assert
        assert response.status_code == 200
        assert len(response.data) == 4
        assert response.data[0]['workflows_count'] == 1
        assert response.data[0]['template_task_id'] == template_task_1.id
        assert (
            response.data[0]['template_task_api_name'] ==
            template_task_1.api_name
        )
        assert response.data[1]['workflows_count'] == 0
        assert response.data[1]['template_task_id'] == template_task_2_1.id
        assert (
            response.data[1]['template_task_api_name'] ==
            template_task_2_1.api_name
        )
        assert response.data[2]['workflows_count'] == 0
        assert response.data[2]['template_task_id'] == template_task_2_2.id
        assert (
            response.data[2]['template_task_api_name'] ==
            template_task_2_2.api_name
        )
        assert response.data[3]['workflows_count'] == 1
        assert response.data[3]['template_task_id'] == template_task_3.id
        assert (
            response.data[3]['template_task_api_name'] ==
            template_task_3.api_name
        )

    def test__filter__not_unique_current_performer_and_performer_group_ids__ok(
        self,
        api_client
    ):
        # arrange
        account = create_test_account()
        user = create_test_user(account=account)
        user2 = create_test_user(account=account, email='owner@test.test')
        group = create_test_group(account, users=[user])
        template_1 = create_test_template(user=user, tasks_count=1)
        TemplateOwner.objects.create(
            template=template_1,
            account=account,
            type=OwnerType.USER,
            user_id=user2.id,
        )
        template_2 = create_test_template(user=user2, tasks_count=2)
        template_3 = create_test_template(user=user, tasks_count=1)
        TemplateOwner.objects.create(
            template=template_3,
            account=account,
            type=OwnerType.USER,
            user_id=user2.id,
        )
        template_task_1 = template_1.tasks.get(number=1)
        template_task_2_1 = template_2.tasks.get(number=1)
        template_task_2_2 = template_2.tasks.get(number=2)
        template_task_3 = template_3.tasks.get(number=1)
        template_task_1.add_raw_performer(
            performer_type=PerformerType.GROUP,
            group=group
        )

        create_test_workflow(
            template=template_1,
            user=user
        )
        create_test_workflow(
            template=template_2,
            user=user2
        )
        create_test_workflow(
            template=template_3,
            user=user
        )

        api_client.token_authenticate(user2)

        # act
        response = api_client.get(
            f'/workflows/count/by-template-task',
            data={
                'current_performer_ids': user.id,
                'current_performer_group_ids': group.id
            }
        )

        # assert
        assert response.status_code == 200
        assert len(response.data) == 4
        assert response.data[0]['workflows_count'] == 1
        assert response.data[0]['template_task_id'] == template_task_1.id
        assert (
            response.data[0]['template_task_api_name'] ==
            template_task_1.api_name
        )
        assert response.data[1]['workflows_count'] == 0
        assert response.data[1]['template_task_id'] == template_task_2_1.id
        assert (
            response.data[1]['template_task_api_name'] ==
            template_task_2_1.api_name
        )
        assert response.data[2]['workflows_count'] == 0
        assert response.data[2]['template_task_id'] == template_task_2_2.id
        assert (
            response.data[2]['template_task_api_name'] ==
            template_task_2_2.api_name
        )
        assert response.data[3]['workflows_count'] == 1
        assert response.data[3]['template_task_id'] == template_task_3.id
        assert (
            response.data[3]['template_task_api_name'] ==
            template_task_3.api_name
        )

    def test__filter__current_performer_group_ids_invalid__validation_error(
        self,
        api_client
    ):
        # arrange
        user = create_test_user()
        api_client.token_authenticate(user)

        # act
        response = api_client.get(
            f'/workflows/count/by-template-task',
            data={'current_performer_group_ids': 'None'}
        )

        # assert
        assert response.status_code == 400
        message = 'Value should be a list of integers.'
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['message'] == message
        assert (
            response.data['details']['name'] == 'current_performer_group_ids'
        )
        assert response.data['details']['reason'] == message

    def test__filter__current_performer_ids_invalid__validation_error(
        self,
        api_client
    ):
        # arrange
        user = create_test_user()
        api_client.token_authenticate(user)

        # act
        response = api_client.get(
            f'/workflows/count/by-template-task',
            data={'current_performer_ids': 'None'}
        )

        # assert
        assert response.status_code == 400
        message = 'Value should be a list of integers.'
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['message'] == message
        assert response.data['details']['name'] == 'current_performer_ids'
        assert response.data['details']['reason'] == message

    def test__filter__inconsistent_filters__validation_error(
        self,
        api_client
    ):

        # arrange
        user = create_test_user()
        api_client.token_authenticate(user)

        # act
        response = api_client.get(
            f'/workflows/count/by-template-task',
            data={
                'status': WorkflowApiStatus.DONE,
                'current_performer_ids': user.id
            }
        )

        # assert
        assert response.status_code == 400
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['message'] == messages.MSG_PW_0067

    def test__not_template_owner__not_found(self, api_client):

        # arrange
        account = create_test_account(
            'plan kapkan',
            plan=BillingPlanType.PREMIUM
        )
        user_1 = create_test_user(account=account, email='user1@test.test')
        user_2 = create_test_user(account=account, email='user2@test.test')
        create_test_workflow(user_1)
        create_test_workflow(user_1, is_external=True)

        api_client.token_authenticate(user_2)

        # act
        response = api_client.get(
            f'/workflows/count/by-template-task',
        )

        # assert
        assert response.status_code == 200
        assert len(response.data) == 0

    def test__filter__workflow_starter_ids__ok(self, api_client):

        # arrange
        account = create_test_account()
        user_1 = create_test_user(account=account, email='user1@test.test')
        user_2 = create_test_user(account=account, email='user2@test.test')
        user_3 = create_test_user(account=account, email='user3@test.test')
        template_1 = create_test_template(user_1, is_active=True)
        template_task_1 = template_1.tasks.get(number=1)
        template_task_2 = template_1.tasks.get(number=2)

        template_2 = create_test_template(user_2, is_active=True)
        TemplateOwner.objects.create(
            template=template_2,
            account=account,
            type=OwnerType.USER,
            user_id=user_1.id,
        )
        template_task_21 = template_2.tasks.get(number=1)

        template_3 = create_test_template(user_3, is_active=True)
        TemplateOwner.objects.create(
            template=template_3,
            account=account,
            type=OwnerType.USER,
            user_id=user_1.id,
        )
        create_test_workflow(
            user=user_1,
            template=template_1,
            active_task_number=2
        )
        template_1.is_public = True
        template_1.save()
        create_test_workflow(user_1, template=template_1)

        create_test_workflow(user_2, template=template_2)
        create_test_workflow(user_3, template=template_3)

        api_client.token_authenticate(user_1)

        # act
        response = api_client.get(
            path='/workflows/count/by-template-task',
            data={'workflow_starter_ids': f'{user_1.id},{user_2.id}'}
        )

        # assert
        assert response.status_code == 200
        assert len(response.data) == 9
        assert response.data[0]['template_task_id'] == template_task_1.id
        assert (
            response.data[0]['template_task_api_name'] ==
            template_task_1.api_name
        )
        assert response.data[0]['workflows_count'] == 1
        assert response.data[1]['template_task_id'] == template_task_2.id
        assert (
            response.data[1]['template_task_api_name'] ==
            template_task_2.api_name
        )
        assert response.data[1]['workflows_count'] == 1
        assert response.data[3]['template_task_id'] == template_task_21.id
        assert (
            response.data[3]['template_task_api_name'] ==
            template_task_21.api_name
        )
        assert response.data[3]['workflows_count'] == 1

    def test__many_performers__ok(self, api_client):

        # arrange
        account = create_test_account()
        user = create_test_user(account=account)
        user_2 = create_test_user(account=account, email='t@t.t')

        template = create_test_template(user=user, tasks_count=2)
        template_task_1 = template.tasks.get(number=1)
        template_task_2 = template.tasks.get(number=2)
        template_task_1.add_raw_performer(user_2)
        create_test_workflow(user=user, template=template)
        api_client.token_authenticate(user)

        # act
        response = api_client.get('/workflows/count/by-template-task')

        # assert
        assert response.status_code == 200
        assert len(response.data) == 2
        assert response.data[0]['template_task_id'] == template_task_1.id
        assert (
            response.data[0]['template_task_api_name'] ==
            template_task_1.api_name
        )
        assert response.data[0]['workflows_count'] == 1
        assert response.data[1]['template_task_id'] == template_task_2.id
        assert (
            response.data[1]['template_task_api_name'] ==
            template_task_2.api_name
        )
        assert response.data[1]['workflows_count'] == 0
