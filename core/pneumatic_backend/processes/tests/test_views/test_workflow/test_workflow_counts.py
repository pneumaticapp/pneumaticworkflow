import pytest

from pneumatic_backend.accounts.enums import BillingPlanType
from pneumatic_backend.processes.tests.fixtures import (
    create_test_user,
    create_test_workflow,
    create_test_template,
    create_test_account,
)
from pneumatic_backend.processes.enums import (
    WorkflowStatus,
    WorkflowApiStatus
)
from pneumatic_backend.utils.validation import ErrorCode
from pneumatic_backend.processes.messages import workflow as messages


pytestmark = pytest.mark.django_db


class TestWorkflowCountsByWorkflowStarter:

    def test__no_filters__ok(self, api_client):

        # arrange
        account = create_test_account()
        user_1 = create_test_user(account=account, email='user1@test.test')
        user_2 = create_test_user(account=account, email='user2@test.test')
        create_test_workflow(user_1, is_external=True)
        create_test_workflow(user_1)
        create_test_workflow(user_2)
        create_test_workflow(user_2)
        api_client.token_authenticate(user_1)

        # act
        response = api_client.get('/workflows/count/by-workflow-starter')

        # assert
        assert response.status_code == 200
        assert len(response.data) == 3
        assert response.data[0]['user_id'] == -1
        assert response.data[0]['workflows_count'] == 1
        assert response.data[1]['user_id'] == user_1.id
        assert response.data[1]['workflows_count'] == 1
        assert response.data[2]['user_id'] == user_2.id
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
        assert response.data[0]['user_id'] == -1
        assert response.data[0]['workflows_count'] == 0
        assert response.data[1]['user_id'] == user.id
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
        create_test_workflow(user_2)
        workflow_done = create_test_workflow(user_2)
        workflow_done.status = WorkflowStatus.DONE
        workflow_done.save()
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
        assert response.data[0]['user_id'] == -1
        assert response.data[0]['workflows_count'] == 1
        assert response.data[1]['user_id'] == user_2.id
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
        assert response.data[0]['user_id'] == -1
        assert response.data[0]['workflows_count'] == 0
        assert response.data[1]['user_id'] == user_1.id
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
        assert response.data[0]['user_id'] == -1
        assert response.data[0]['workflows_count'] == 0
        assert response.data[1]['user_id'] == user_1.id
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
        assert response.data[0]['user_id'] == -1
        assert response.data[0]['workflows_count'] == 1
        assert response.data[1]['user_id'] == user.id
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
        user_1 = create_test_user(account=account, email='user1@test.test')
        user_2 = create_test_user(account=account, email='user2@test.test')
        user_3 = create_test_user(account=account, email='user3@test.test')
        create_test_workflow(user_1)
        create_test_workflow(user_2)
        api_client.token_authenticate(user_3)

        # act
        response = api_client.get(
            '/workflows/count/by-workflow-starter',
            data={
                'current_performer_ids': f'{user_1.id},{user_2.id}'
            }
        )

        # assert
        assert response.status_code == 200
        assert len(response.data) == 3
        assert response.data[0]['user_id'] == -1
        assert response.data[0]['workflows_count'] == 0
        assert response.data[1]['user_id'] == user_1.id
        assert response.data[1]['workflows_count'] == 1
        assert response.data[2]['user_id'] == user_2.id
        assert response.data[2]['workflows_count'] == 1

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
        assert response.data[0]['user_id'] == -1
        assert response.data[0]['workflows_count'] == 0


class TestWorkflowCountsByCPerformer:

    def test__no_filters__ok(self, api_client):

        # arrange
        account = create_test_account()
        user_1 = create_test_user(account=account, email='user1@test.test')
        user_2 = create_test_user(account=account, email='user2@test.test')
        create_test_workflow(user_1, is_external=True)
        create_test_workflow(user_1)
        create_test_workflow(user_2)
        create_test_workflow(user_2)
        api_client.token_authenticate(user_1)

        # act
        response = api_client.get('/workflows/count/by-current-performer')

        # assert
        assert response.status_code == 200
        assert len(response.data) == 2
        assert response.data[0]['user_id'] == user_1.id
        assert response.data[0]['workflows_count'] == 2
        assert response.data[1]['user_id'] == user_2.id
        assert response.data[1]['workflows_count'] == 2

    def test__filter__status_running__ok(self, api_client):

        # arrange
        account = create_test_account()
        user_1 = create_test_user(account=account, email='user1@test.test')
        user_2 = create_test_user(account=account, email='user2@test.test')
        workflow_done = create_test_workflow(user_1)
        workflow_done.status = WorkflowStatus.DONE
        workflow_done.save()
        create_test_workflow(user_2)
        workflow_delay = create_test_workflow(user_2)
        workflow_delay.status = WorkflowStatus.DELAYED
        workflow_delay.save()
        api_client.token_authenticate(user_1)

        # act
        response = api_client.get(
            '/workflows/count/by-current-performer',
            data={
                'status': WorkflowApiStatus.RUNNING
            }
        )

        # assert
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]['user_id'] == user_2.id
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
        assert response.data[0]['user_id'] == user.id
        assert response.data[0]['workflows_count'] == 1

    @pytest.mark.parametrize('status', WorkflowApiStatus.NOT_RUNNING)
    def test__filter__status_not_running__validation_error(
        self,
        status,
        api_client
    ):

        # arrange
        account = create_test_account()
        user = create_test_user(account=account, email='user1@test.test')
        api_client.token_authenticate(user)

        # act
        response = api_client.get(
            '/workflows/count/by-current-performer',
            data={'status': status}
        )

        # assert
        assert response.status_code == 400
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['message'] == messages.MSG_PW_0067

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
            f'/workflows/count/by-current-performer',
            data={'status': 'invalid'}
        )

        # assert
        assert response.status_code == 400
        message = '"invalid" is not a valid choice.'
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
            '/workflows/count/by-current-performer',
            data={
                'template_ids': f'{template_1.id},{template_3.id}'
            }
        )

        # assert
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]['user_id'] == user.id
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

        create_test_workflow(user_1, template=template_1, is_external=True)
        create_test_workflow(user_1, template=template_2)
        create_test_workflow(user_1, template=template_3)
        api_client.token_authenticate(user_2)

        template_task_ids = (
            f'{template_task_1_1.id},'
            f'{template_task_3_1.id},'
            f'{template_task_3_2.id}'
        )

        # act
        response = api_client.get(
            '/workflows/count/by-current-performer',
            data={'template_task_ids': template_task_ids}
        )

        # assert
        assert response.status_code == 200
        assert len(response.data) == 2
        assert response.data[0]['user_id'] == user_1.id
        assert response.data[0]['workflows_count'] == 2
        assert response.data[1]['user_id'] == user_2.id
        assert response.data[1]['workflows_count'] == 1

    def test__filter__template_task_ids_invalid__validation_error(
        self,
        api_client
    ):

        # arrange
        account = create_test_account()
        user = create_test_user(account=account, email='user1@test.test')
        template = create_test_template(user, tasks_count=1)
        template_task = template.tasks.get(number=1)
        create_test_workflow(user, template=template, is_external=True)
        api_client.token_authenticate(user)

        template_task_ids = (
            f'{template_task.id},invalid'
        )

        # act
        response = api_client.get(
            '/workflows/count/by-current-performer',
            data={'template_task_ids': template_task_ids}
        )

        # assert
        assert response.status_code == 400
        message = 'Value should be a list of integers.'
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['message'] == message
        assert response.data['details']['name'] == 'template_task_ids'
        assert response.data['details']['reason'] == message

    def test__filter__workflow_starter_ids__ok(self, api_client):

        # arrange
        account = create_test_account(plan=BillingPlanType.PREMIUM)
        user_1 = create_test_user(account=account, email='user1@test.test')
        user_2 = create_test_user(account=account, email='user2@test.test')
        create_test_user(account=account, email='user3@test.test')
        template_1 = create_test_template(user_1, is_active=True)
        template_2 = create_test_template(user_2, is_active=True)
        template_2.template_owners.add(user_1)

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
        assert response.data[0]['user_id'] == user_1.id
        assert response.data[0]['workflows_count'] == 1
        assert response.data[1]['user_id'] == user_2.id
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
        template_2.template_owners.add(user_1)

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
        assert response.data[0]['user_id'] == user_1.id
        assert response.data[0]['workflows_count'] == 1
        assert response.data[1]['user_id'] == user_2.id
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
        template_2.template_owners.add(user_1)

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
        assert response.data[0]['user_id'] == user_2.id
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
        first_template_task = template.tasks.get(number=1)
        second_template_task = template.tasks.get(number=2)
        third_template_task = template.tasks.get(number=3)
        create_test_workflow(user=user, template=template)
        create_test_workflow(user=user, template=template)
        workflow_2 = create_test_workflow(user=user, template=template)
        workflow_2.current_task = 2
        workflow_2.save()
        api_client.token_authenticate(user)

        # act
        response = api_client.get('/workflows/count/by-template-task')

        # assert
        assert response.status_code == 200
        assert len(response.data) == 3
        assert response.data[0]['template_task_id'] == first_template_task.id
        assert response.data[0]['workflows_count'] == 2
        assert response.data[1]['template_task_id'] == second_template_task.id
        assert response.data[1]['workflows_count'] == 1
        assert response.data[2]['template_task_id'] == third_template_task.id
        assert response.data[2]['workflows_count'] == 0

    def test__filter__all_status__ok(self, api_client):

        # arrange
        account = create_test_account()
        user = create_test_user(account=account)
        template = create_test_template(user=user, tasks_count=2)
        first_template_task = template.tasks.get(number=1)
        second_template_task = template.tasks.get(number=2)
        workflow = create_test_workflow(
            template=template,
            user=user
        )
        workflow.current_task = 2
        workflow.save()

        workflow_done = create_test_workflow(
            template=template,
            user=user
        )
        workflow_done.status = WorkflowStatus.DONE
        workflow_done.save()

        workflow_delay = create_test_workflow(
            user=user,
            template=template
        )
        workflow_delay.current_task = 2
        workflow_delay.status = WorkflowStatus.DELAYED
        workflow_delay.save()

        api_client.token_authenticate(user)

        # act
        response = api_client.get('/workflows/count/by-template-task')

        # assert
        assert response.status_code == 200
        assert len(response.data) == 2
        assert response.data[0]['template_task_id'] == first_template_task.id
        assert response.data[0]['workflows_count'] == 1
        assert response.data[1]['template_task_id'] == second_template_task.id
        assert response.data[1]['workflows_count'] == 2

    def test__filter__status_done__ok(self, api_client):

        # arrange
        account = create_test_account()
        user = create_test_user(account=account)
        template = create_test_template(user=user, tasks_count=2)
        first_template_task = template.tasks.get(number=1)
        second_template_task = template.tasks.get(number=2)
        create_test_workflow(
            template=template,
            user=user
        )
        workflow_done = create_test_workflow(
            template=template,
            user=user
        )
        workflow_done.status = WorkflowStatus.DONE
        workflow_done.current_task = 2
        workflow_done.save()
        api_client.token_authenticate(user)

        workflow_delay = create_test_workflow(
            user=user,
            template=template
        )
        workflow_delay.status = WorkflowStatus.DELAYED
        workflow_delay.save()

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
        assert response.data[0]['template_task_id'] == first_template_task.id
        assert response.data[0]['workflows_count'] == 0
        assert response.data[1]['template_task_id'] == second_template_task.id
        assert response.data[1]['workflows_count'] == 1

    def test__filter__status_running__ok(self, api_client):

        # arrange
        account = create_test_account()
        user = create_test_user(account=account)
        template = create_test_template(user=user, tasks_count=2)
        first_template_task = template.tasks.get(number=1)
        second_template_task = template.tasks.get(number=2)
        workflow = create_test_workflow(
            template=template,
            user=user
        )
        workflow.current_task = 2
        workflow.save()

        workflow_done = create_test_workflow(
            template=template,
            user=user
        )
        workflow_done.status = WorkflowStatus.DONE
        workflow_done.save()

        workflow_delay = create_test_workflow(
            user=user,
            template=template
        )
        workflow_delay.current_task = 2
        workflow_delay.status = WorkflowStatus.DELAYED
        workflow_delay.save()

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
        assert response.data[0]['template_task_id'] == first_template_task.id
        assert response.data[0]['workflows_count'] == 0
        assert response.data[1]['template_task_id'] == second_template_task.id
        assert response.data[1]['workflows_count'] == 1

    def test__filter__status_delayed__ok(self, api_client):

        # arrange
        account = create_test_account()
        user = create_test_user(account=account)
        template = create_test_template(user=user, tasks_count=2)
        first_template_task = template.tasks.get(number=1)
        second_template_task = template.tasks.get(number=2)

        workflow_delay = create_test_workflow(
            user=user,
            template=template
        )
        workflow_delay.current_task = 2
        workflow_delay.status = WorkflowStatus.DELAYED
        workflow_delay.save()

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
        assert response.data[0]['template_task_id'] == first_template_task.id
        assert response.data[0]['workflows_count'] == 0
        assert response.data[1]['template_task_id'] == second_template_task.id
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
        workflow = create_test_workflow(
            template=template_3,
            user=user
        )
        workflow.current_task = 2
        workflow.save()

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
        assert response.data[0]['workflows_count'] == 1
        assert response.data[1]['template_task_id'] == template_task_31.id
        assert response.data[1]['workflows_count'] == 0
        assert response.data[2]['template_task_id'] == template_task_32.id
        assert response.data[2]['workflows_count'] == 1

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
        template_2.template_owners.add(user_1)
        template_task_21 = template_2.tasks.get(number=1)

        template_3 = create_test_template(user_3, is_active=True)

        workflow = create_test_workflow(user_1, template=template_1)
        workflow.current_task = 2
        workflow.save()

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
        assert response.data[0]['workflows_count'] == 1
        assert response.data[1]['template_task_id'] == template_task_2.id
        assert response.data[1]['workflows_count'] == 1
        assert response.data[3]['template_task_id'] == template_task_21.id
        assert response.data[3]['workflows_count'] == 1

    def test__many_performers__ok(self, api_client):

        # arrange
        account = create_test_account()
        user = create_test_user(account=account)
        user_2 = create_test_user(account=account, email='t@t.t')

        template = create_test_template(user=user, tasks_count=2)
        first_template_task = template.tasks.get(number=1)
        second_template_task = template.tasks.get(number=2)
        first_template_task.add_raw_performer(user_2)
        create_test_workflow(user=user, template=template)
        api_client.token_authenticate(user)

        # act
        response = api_client.get('/workflows/count/by-template-task')

        # assert
        assert response.status_code == 200
        assert len(response.data) == 2
        assert response.data[0]['template_task_id'] == first_template_task.id
        assert response.data[0]['workflows_count'] == 1
        assert response.data[1]['template_task_id'] == second_template_task.id
        assert response.data[1]['workflows_count'] == 0
