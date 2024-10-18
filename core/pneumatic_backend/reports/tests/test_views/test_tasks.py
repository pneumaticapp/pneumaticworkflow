from datetime import timedelta
import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from pneumatic_backend.accounts.services import AccountService
from pneumatic_backend.accounts.enums import BillingPlanType
from pneumatic_backend.processes.models import (
    TaskPerformer
)
from pneumatic_backend.reports.tests.fixtures import (
    create_test_user,
    create_test_template,
    create_test_workflow,
    create_test_account,
)
from pneumatic_backend.processes.enums import (
    WorkflowStatus,
    PerformerType,
    PredicateOperator
)
from pneumatic_backend.processes.enums import (
    FieldType,
    DirectlyStatus
)

UserModel = get_user_model()
pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def replica_mock(mocker):
    mocker.patch('django.conf.settings.REPLICA', 'default')
    yield


class TestDashboardMyTasksOverview:

    def test_my_tasks__ok(
        self,
        api_client
    ):
        # arrange
        account = create_test_account()
        create_test_user(
            email='owner@test.test',
            account=account,
            is_account_owner=True
        )
        template_owner = create_test_user(
            account=account,
            is_account_owner=False
        )
        template_owner.account.billing_plan = BillingPlanType.PREMIUM
        template_owner.account.save()
        user = create_test_user(
            email='testinguser@pneumatic.app',
            account=template_owner.account,
        )
        first_template = create_test_template(template_owner)
        second_template = create_test_template(template_owner, is_active=True)
        account_service = AccountService(
            instance=template_owner.account,
            user=template_owner
        )
        account_service.update_active_templates()
        first_task = first_template.tasks.get(number=1)
        first_task.add_raw_performer(user)

        first_task = second_template.tasks.get(number=1)
        first_task.add_raw_performer(user)

        first_workflow = create_test_workflow(template_owner, first_template)
        api_client.token_authenticate(user)
        api_client.post(
            f'/workflows/{first_workflow.id}/task-complete',
            data={'task_id': first_workflow.current_task_instance.id},
        )

        overdue_workflow = create_test_workflow(template_owner, first_template)
        task = overdue_workflow.tasks.get(number=1)
        date_created = overdue_workflow.date_created - timedelta(days=7)
        task.due_date = date_created + timedelta(seconds=1)
        task.date_started = date_created
        task.date_first_started = date_created
        task.save(update_fields=[
            'due_date',
            'date_started',
            'date_first_started',
        ])
        overdue_workflow.date_created = date_created
        overdue_workflow.save(update_fields=['date_created'])
        api_client.post(
            f'/workflows/{overdue_workflow.id}/task-complete',
            data={'task_id': overdue_workflow.current_task_instance.id},
        )

        api_client.token_authenticate(template_owner)
        api_client.post(
            f'/workflows/{overdue_workflow.id}/task-complete',
            data={'task_id': overdue_workflow.tasks.get(number=2).id},
        )

        second_workflow = create_test_workflow(template_owner, first_template)
        second_workflow.status = WorkflowStatus.RUNNING
        second_workflow.save(update_fields=['status'])

        fourth_workflow = create_test_workflow(template_owner, second_template)
        fourth_workflow.status = WorkflowStatus.DONE
        fourth_workflow.date_completed = timezone.now()
        fourth_workflow.save(update_fields=['status', 'date_completed'])

        api_client.token_authenticate(user)

        # act
        response = api_client.get('/reports/dashboard/tasks/overview')

        # assert
        assert response.status_code == 200
        assert response.data['started'] == 3
        assert response.data['completed'] == 2
        assert response.data['in_progress'] == 4
        assert response.data['overdue'] == 1

    def test__my_tasks__deleted_performer__ok(
        self,
        api_client
    ):

        # arrange
        account = create_test_account()
        create_test_user(
            email='owner@test.test',
            account=account,
            is_account_owner=True
        )
        user = create_test_user(
            account=account,
            is_account_owner=False
        )
        workflow = create_test_workflow(user, tasks_count=1)
        task = workflow.current_task_instance
        TaskPerformer.objects.filter(
            task=task
        ).update(directly_status=DirectlyStatus.DELETED)
        api_client.token_authenticate(user)

        # act
        response = api_client.get('/reports/dashboard/tasks/overview')

        # assert
        assert response.status_code == 200
        assert response.data['started'] == 0
        assert response.data['completed'] == 0
        assert response.data['in_progress'] == 0
        assert response.data['overdue'] == 0

    def test_my_tasks__legacy_template__count_tasks(
        self,
        api_client
    ):
        # arrange
        account = create_test_account(plan=BillingPlanType.PREMIUM)
        create_test_user(
            email='owner@test.test',
            account=account,
            is_account_owner=True
        )
        template_owner = create_test_user(
            account=account,
            is_account_owner=False
        )
        user = create_test_user(
            email='testinguser@pneumatic.app',
            account=template_owner.account,
        )
        first_template = create_test_template(template_owner)
        second_template = create_test_template(template_owner, is_active=True)
        account_service = AccountService(
            instance=template_owner.account,
            user=template_owner
        )
        account_service.update_active_templates()
        first_task = first_template.tasks.get(number=1)
        first_task.add_raw_performer(user)

        first_task = second_template.tasks.get(number=1)
        first_task.add_raw_performer(user)

        first_workflow = create_test_workflow(template_owner, first_template)
        api_client.token_authenticate(user)
        api_client.post(
            f'/workflows/{first_workflow.id}/task-complete',
            data={'task_id': first_workflow.current_task_instance.id},
        )

        overdue_workflow = create_test_workflow(template_owner, first_template)
        task = overdue_workflow.tasks.get(number=1)
        date_created = overdue_workflow.date_created - timedelta(days=7)
        task.due_date = date_created + timedelta(seconds=1)
        task.date_started = date_created
        task.date_first_started = date_created
        task.save(update_fields=[
            'due_date',
            'date_started',
            'date_first_started',
        ])
        overdue_workflow.date_created = date_created
        overdue_workflow.save(update_fields=['date_created'])
        api_client.post(
            f'/workflows/{overdue_workflow.id}/task-complete',
            data={'task_id': overdue_workflow.current_task_instance.id},
        )

        api_client.delete(f'/templates/{first_template.id}')

        fourth_workflow = create_test_workflow(template_owner, second_template)
        fourth_workflow.status = WorkflowStatus.DONE
        fourth_workflow.date_completed = timezone.now()
        fourth_workflow.save(update_fields=['status', 'date_completed'])

        # act
        response = api_client.get('/reports/dashboard/tasks/overview')

        # assert
        assert response.status_code == 200
        assert response.data['started'] == 2
        assert response.data['completed'] == 2
        assert response.data['in_progress'] == 3
        assert response.data['overdue'] == 1

    def test_my_tasks__regular_user__ok(
        self,
        api_client
    ):
        # arrange
        account = create_test_account(plan=BillingPlanType.PREMIUM)
        create_test_user(
            email='owner@test.test',
            account=account,
            is_account_owner=True
        )
        create_test_user(
            account=account,
            is_account_owner=False
        )
        user = create_test_user(
            email='testinguser@pneumatic.app',
            is_admin=False,
            account=account,
        )

        api_client.token_authenticate(user)

        # act
        response = api_client.get('/reports/dashboard/tasks/overview')

        # assert
        assert response.status_code == 200
        assert response.data['started'] == 0
        assert response.data['completed'] == 0
        assert response.data['in_progress'] == 0
        assert response.data['overdue'] == 0

    def test_my_tasks__require_completion_by_all__partly_completed(
        self,
        api_client,
    ):
        """ caused by: https://my.pneumatic.app/workflows/12359 """
        # arrange
        account = create_test_account(plan=BillingPlanType.PREMIUM)
        create_test_user(
            email='owner@test.test',
            account=account,
            is_account_owner=True
        )
        template_owner = create_test_user(
            account=account,
            is_account_owner=False
        )
        user = create_test_user(
            email='testinguser@pneumatic.app',
            account=template_owner.account,
        )
        first_template = create_test_template(template_owner, is_active=True)
        account_service = AccountService(
            instance=template_owner.account,
            user=template_owner
        )
        account_service.update_active_templates()

        first_task = first_template.tasks.get(number=1)
        first_task.require_completion_by_all = True
        first_task.save()
        first_task.add_raw_performer(user)

        first_workflow = create_test_workflow(template_owner, first_template)
        api_client.token_authenticate(user)
        api_client.post(
            f'/workflows/{first_workflow.id}/task-complete',
            data={'task_id': first_workflow.current_task_instance.id},
        )

        overdue_workflow = create_test_workflow(template_owner, first_template)
        task = overdue_workflow.tasks.get(number=1)
        date_created = overdue_workflow.date_created - timedelta(days=7)
        task.due_date = date_created + timedelta(seconds=1)
        task.date_started = date_created
        task.date_first_started = date_created
        task.save(update_fields=[
            'due_date',
            'date_started',
            'date_first_started',
        ])
        overdue_workflow.date_created = date_created
        overdue_workflow.save(update_fields=['date_created'])
        api_client.token_authenticate(template_owner)
        api_client.post(
            f'/workflows/{overdue_workflow.id}/task-complete',
            data={'task_id': overdue_workflow.current_task_instance.id},
        )

        # act
        template_owner_response = api_client.get(
            '/reports/dashboard/tasks/overview',
            data={'now': True},
        )
        api_client.token_authenticate(user)
        regular_user_response = api_client.get(
            '/reports/dashboard/tasks/overview',
            data={'now': True},
        )

        # assert
        assert template_owner_response.status_code == 200
        assert template_owner_response.data['in_progress'] == 1
        assert template_owner_response.data['overdue'] == 0
        assert regular_user_response.status_code == 200
        assert regular_user_response.data['in_progress'] == 1
        assert regular_user_response.data['overdue'] == 1

    def test_my_tasks__now__ok(
        self,
        api_client
    ):
        # arrange
        account = create_test_account(plan=BillingPlanType.PREMIUM)
        create_test_user(
            email='owner@test.test',
            account=account,
            is_account_owner=True
        )
        template_owner = create_test_user(
            account=account,
            is_account_owner=False
        )
        user = create_test_user(
            email='testinguser@pneumatic.app',
            account=template_owner.account,
        )
        first_template = create_test_template(template_owner)
        second_template = create_test_template(template_owner, is_active=True)
        account_service = AccountService(
            instance=template_owner.account,
            user=template_owner
        )
        account_service.update_active_templates()

        first_task = first_template.tasks.get(number=1)
        first_task.add_raw_performer(user)

        first_task = second_template.tasks.get(number=1)
        first_task.add_raw_performer(user)

        first_workflow = create_test_workflow(template_owner, first_template)
        api_client.token_authenticate(user)
        api_client.post(
            f'/workflows/{first_workflow.id}/task-complete',
            data={'task_id': first_workflow.current_task_instance.id},
        )

        overdue_workflow = create_test_workflow(template_owner, first_template)
        task = overdue_workflow.tasks.get(number=1)
        date_created = overdue_workflow.date_created - timedelta(days=7)
        task.due_date = date_created + timedelta(seconds=1)
        task.date_started = date_created
        task.date_first_started = date_created
        task.save(update_fields=[
            'due_date',
            'date_started',
            'date_first_started',
        ])
        overdue_workflow.date_created = date_created
        overdue_workflow.save(update_fields=['date_created'])

        second_workflow = create_test_workflow(template_owner, first_template)
        second_workflow.status = WorkflowStatus.RUNNING
        second_workflow.save(update_fields=['status'])

        fourth_workflow = create_test_workflow(template_owner, second_template)
        fourth_workflow.status = WorkflowStatus.DONE
        fourth_workflow.date_completed = timezone.now()
        fourth_workflow.save(update_fields=['status', 'date_completed'])

        api_client.token_authenticate(user)

        # act
        response = api_client.get(
            '/reports/dashboard/tasks/overview',
            data={'now': True}
        )

        # assert
        assert response.status_code == 200
        assert response.data['in_progress'] == 2
        assert response.data['started'] is None
        assert response.data['completed'] is None
        assert response.data['overdue'] == 1

    def test_my_tasks__deleted_performer__ok(
        self,
        api_client
    ):

        # arrange
        account = create_test_account()
        create_test_user(
            email='owner@test.test',
            account=account,
            is_account_owner=True
        )
        user = create_test_user(
            account=account,
            is_account_owner=False
        )
        workflow = create_test_workflow(user, tasks_count=1)
        task = workflow.current_task_instance
        TaskPerformer.objects.filter(
            task=task
        ).update(directly_status=DirectlyStatus.DELETED)
        api_client.token_authenticate(user)

        # act
        response = api_client.get(
            '/reports/dashboard/tasks/overview',
            data={'now': True}
        )

        # assert
        assert response.status_code == 200
        assert response.data['started'] is None
        assert response.data['completed'] is None
        assert response.data['in_progress'] == 0
        assert response.data['overdue'] == 0


class TestDashboardMyTasksBreakdown:

    def test_my_tasks_breakdown__ok(
        self,
        api_client
    ):
        # arrange
        account = create_test_account(plan=BillingPlanType.PREMIUM)
        create_test_user(
            email='owner@test.test',
            account=account,
            is_account_owner=True
        )
        template_owner = create_test_user(
            account=account,
            is_account_owner=False
        )
        user = create_test_user(
            email='testinguser@pneumatic.app',
            account=template_owner.account,
        )
        first_template = create_test_template(template_owner)
        second_template = create_test_template(template_owner, is_active=True)
        third_template = create_test_template(template_owner, is_active=True)
        account_service = AccountService(
            instance=template_owner.account,
            user=template_owner
        )
        account_service.update_active_templates()

        first_task = first_template.tasks.get(number=1)
        first_task.add_raw_performer(user)

        first_task = second_template.tasks.get(number=1)
        first_task.add_raw_performer(user)

        second_task = third_template.tasks.get(number=2)
        second_task.add_raw_performer(user)

        first_workflow = create_test_workflow(template_owner, first_template)
        api_client.token_authenticate(user)
        api_client.post(
            f'/workflows/{first_workflow.id}/task-complete',
            data={'task_id': first_workflow.current_task_instance.id},
        )

        overdue_workflow = create_test_workflow(template_owner, first_template)
        task = overdue_workflow.tasks.get(number=1)
        date_created = overdue_workflow.date_created - timedelta(days=7)
        task.due_date = date_created + timedelta(seconds=1)
        task.date_started = date_created
        task.date_first_started = date_created
        task.save(update_fields=[
            'due_date',
            'date_started',
            'date_first_started',
        ])
        overdue_workflow.date_created = date_created
        overdue_workflow.save(update_fields=['date_created'])
        api_client.post(
            f'/workflows/{overdue_workflow.id}/task-complete',
            data={'task_id': overdue_workflow.current_task_instance.id},
        )
        third_workflow = create_test_workflow(template_owner, first_template)
        api_client.post(
            f'/workflows/{third_workflow.id}/task-complete',
            data={'task_id': third_workflow.current_task_instance.id},
        )

        api_client.token_authenticate(template_owner)
        api_client.post(
            f'/workflows/{overdue_workflow.id}/task-complete',
            data={'task_id': overdue_workflow.tasks.get(number=2).id},
        )

        second_workflow = create_test_workflow(template_owner, first_template)
        second_workflow.status = WorkflowStatus.RUNNING
        second_workflow.save(update_fields=['status'])

        fourth_workflow = create_test_workflow(template_owner, second_template)
        fourth_workflow.status = WorkflowStatus.DONE
        fourth_workflow.date_completed = timezone.now()
        fourth_workflow.save(update_fields=['status', 'date_completed'])

        api_client.token_authenticate(user)

        # act
        response = api_client.get('/reports/dashboard/tasks/breakdown')

        # assert
        assert response.status_code == 200
        assert len(response.data) == 2
        assert response.data[0]['template_id'] == first_template.id
        assert response.data[0]['template_name'] == first_template.name
        assert response.data[0]['started'] == 3
        assert response.data[0]['completed'] == 3
        assert response.data[0]['in_progress'] == 4
        assert response.data[0]['overdue'] == 1
        assert response.data[1]['template_id'] == second_template.id
        assert response.data[1]['template_name'] == second_template.name
        assert response.data[1]['started'] == 1
        assert response.data[1]['completed'] == 0
        assert response.data[1]['in_progress'] == 1
        assert response.data[1]['overdue'] == 0

    def test_my_tasks_breakdown__deleted_performer__ok(
        self,
        api_client
    ):

        # arrange
        account = create_test_account(plan=BillingPlanType.PREMIUM)
        create_test_user(
            email='owner@test.test',
            account=account,
            is_account_owner=True
        )
        user = create_test_user(
            account=account,
            is_account_owner=False
        )
        workflow = create_test_workflow(user, tasks_count=1)
        task = workflow.current_task_instance
        TaskPerformer.objects.filter(
            task=task
        ).update(directly_status=DirectlyStatus.DELETED)
        api_client.token_authenticate(user)

        # act
        response = api_client.get('/reports/dashboard/tasks/breakdown')

        # assert
        assert response.status_code == 200
        assert len(response.data) == 0

    def test_my_tasks_breakdown__require_completion_by_all__partly_completed(
        self,
        api_client,
    ):
        """ caused by: https://my.pneumatic.app/workflows/12359 """
        # arrange
        account = create_test_account(plan=BillingPlanType.PREMIUM)
        create_test_user(
            email='owner@test.test',
            account=account,
            is_account_owner=True
        )
        template_owner = create_test_user(
            account=account,
            is_account_owner=False
        )
        user = create_test_user(
            email='testinguser@pneumatic.app',
            account=template_owner.account,
        )
        first_template = create_test_template(template_owner, is_active=True)
        account_service = AccountService(
            instance=template_owner.account,
            user=template_owner
        )
        account_service.update_active_templates()

        first_task = first_template.tasks.get(number=1)
        first_task.require_completion_by_all = True
        first_task.save()
        first_task.add_raw_performer(user)

        first_workflow = create_test_workflow(template_owner, first_template)
        api_client.token_authenticate(user)
        api_client.post(
            f'/workflows/{first_workflow.id}/task-complete',
            data={'task_id': first_workflow.current_task_instance.id},
        )

        overdue_workflow = create_test_workflow(template_owner, first_template)
        task = overdue_workflow.tasks.get(number=1)
        date_created = overdue_workflow.date_created - timedelta(days=7)
        task.due_date = date_created + timedelta(seconds=1)
        task.date_started = date_created
        task.date_first_started = date_created
        task.save(update_fields=[
            'due_date',
            'date_started',
            'date_first_started',
        ])
        overdue_workflow.date_created = date_created
        overdue_workflow.save(update_fields=['date_created'])
        api_client.token_authenticate(template_owner)
        api_client.post(
            f'/workflows/{overdue_workflow.id}/task-complete',
            data={'task_id': overdue_workflow.current_task_instance.id},
        )

        # act
        owner_response = api_client.get(
            '/reports/dashboard/tasks/breakdown',
            data={'now': True},
        )
        api_client.token_authenticate(user)
        user_response = api_client.get(
            '/reports/dashboard/tasks/breakdown',
            data={'now': True},
        )

        # assert
        assert owner_response.status_code == 200
        assert owner_response.data[0]['template_id'] == first_template.id
        assert owner_response.data[0]['in_progress'] == 1
        assert owner_response.data[0]['overdue'] == 0
        assert user_response.status_code == 200
        assert user_response.data[0]['template_id'] == first_template.id
        assert user_response.data[0]['in_progress'] == 1
        assert user_response.data[0]['overdue'] == 1

    def test_my_tasks_breakdown__regular_user__ok(
        self,
        api_client
    ):
        # arrange
        account = create_test_account(plan=BillingPlanType.PREMIUM)
        create_test_user(
            email='owner@test.test',
            account=account,
            is_account_owner=True
        )
        template_owner = create_test_user(
            account=account,
            is_account_owner=False
        )
        user = create_test_user(
            email='testinguser@pneumatic.app',
            is_admin=False,
            account=template_owner.account,
        )

        api_client.token_authenticate(user)

        # act
        response = api_client.get('/reports/dashboard/tasks/breakdown')

        # assert
        assert response.status_code == 200
        assert response.data == []

    def test_my_tasks_breakdown__overdue_tasks(
        self,
        api_client
    ):
        # arrange
        account = create_test_account(plan=BillingPlanType.PREMIUM)
        create_test_user(
            email='owner@test.test',
            account=account,
            is_account_owner=True
        )
        template_owner = create_test_user(
            account=account,
            is_account_owner=False
        )
        user = create_test_user(
            email='testinguser@pneumatic.app',
            account=template_owner.account,
        )
        first_template = create_test_template(template_owner)
        account_service = AccountService(
            instance=template_owner.account,
            user=template_owner
        )
        account_service.update_active_templates()

        first_task = first_template.tasks.get(number=1)
        first_task.add_raw_performer(user)

        api_client.token_authenticate(user)

        overdue_workflow = create_test_workflow(template_owner, first_template)
        task = overdue_workflow.tasks.get(number=1)
        date_created = overdue_workflow.date_created - timedelta(days=7)
        task.due_date = date_created + timedelta(seconds=1)
        task.date_started = date_created
        task.date_first_started = date_created
        task.save(update_fields=[
            'due_date',
            'date_started',
            'date_first_started',
        ])
        overdue_workflow.date_created = date_created
        overdue_workflow.save(update_fields=['date_created'])
        api_client.post(
            f'/workflows/{overdue_workflow.id}/task-complete',
            data={'task_id': overdue_workflow.current_task_instance.id},
        )

        not_overdue_workflow = create_test_workflow(
            user=template_owner,
            template=first_template,
        )
        task = not_overdue_workflow.tasks.get(number=1)
        date_created = overdue_workflow.date_created - timedelta(days=8)
        task.due_date = date_created + timedelta(seconds=1)
        task.date_started = date_created
        task.date_first_started = date_created
        task.save(update_fields=[
            'due_date',
            'date_started',
            'date_first_started',
        ])
        not_overdue_workflow.status = WorkflowStatus.DONE
        date_completed = date_created + timedelta(minutes=1)
        not_overdue_workflow.date_completed = date_completed
        not_overdue_workflow.date_created = date_created
        not_overdue_workflow.save(
            update_fields=['date_created', 'date_completed', 'status'],
        )

        # act
        response = api_client.get('/reports/dashboard/tasks/breakdown')

        # assert
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]['template_id'] == first_template.id
        assert response.data[0]['template_name'] == first_template.name
        assert response.data[0]['started'] == 0
        assert response.data[0]['completed'] == 1
        assert response.data[0]['in_progress'] == 1
        assert response.data[0]['overdue'] == 1

    def test_my_tasks_breakdown_now(
        self,
        api_client
    ):
        # arrange
        account = create_test_account()
        create_test_user(
            email='owner@test.test',
            account=account,
            is_account_owner=True
        )
        template_owner = create_test_user(
            account=account,
            is_account_owner=False
        )
        template_owner.account.billing_plan = BillingPlanType.PREMIUM
        template_owner.account.save()
        user = create_test_user(
            email='testinguser@pneumatic.app',
            account=template_owner.account,
        )
        first_template = create_test_template(template_owner)
        second_template = create_test_template(template_owner, is_active=True)
        third_template = create_test_template(template_owner, is_active=True)
        account_service = AccountService(
            instance=template_owner.account,
            user=template_owner
        )
        account_service.update_active_templates()

        first_task = first_template.tasks.get(number=1)
        first_task.add_raw_performer(user)

        first_task = second_template.tasks.get(number=1)
        first_task.add_raw_performer(user)

        second_task = third_template.tasks.get(number=2)
        second_task.add_raw_performer(user)

        first_workflow = create_test_workflow(template_owner, first_template)
        api_client.token_authenticate(user)
        api_client.post(
            f'/workflows/{first_workflow.id}/task-complete',
            data={'task_id': first_workflow.current_task_instance.id},
        )

        overdue_workflow = create_test_workflow(template_owner, first_template)
        task = overdue_workflow.tasks.get(number=1)
        date_created = overdue_workflow.date_created - timedelta(days=7)
        task.due_date = date_created + timedelta(seconds=1)
        task.date_started = date_created
        task.date_first_started = date_created
        task.save(update_fields=[
            'due_date',
            'date_started',
            'date_first_started',
        ])
        overdue_workflow.date_created = date_created
        overdue_workflow.save(update_fields=['date_created'])
        third_workflow = create_test_workflow(template_owner, first_template)
        api_client.post(
            f'/workflows/{third_workflow.id}/task-complete',
            data={'task_id': third_workflow.current_task_instance.id},
        )

        second_workflow = create_test_workflow(template_owner, first_template)
        second_workflow.status = WorkflowStatus.RUNNING
        second_workflow.save(update_fields=['status'])

        fourth_workflow = create_test_workflow(template_owner, second_template)
        fourth_workflow.status = WorkflowStatus.DONE
        fourth_workflow.date_completed = timezone.now()
        fourth_workflow.save(update_fields=['status', 'date_completed'])

        api_client.token_authenticate(user)

        # act
        response = api_client.get(
            '/reports/dashboard/tasks/breakdown',
            data={'now': True},
        )

        # assert
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]['template_id'] == first_template.id
        assert response.data[0]['template_name'] == first_template.name
        assert response.data[0]['in_progress'] == 2
        assert response.data[0]['started'] is None
        assert response.data[0]['completed'] is None
        assert response.data[0]['overdue'] == 1

    def test_my_tasks_breakdown_now__deleted_performer__ok(
        self,
        api_client
    ):

        # arrange
        account = create_test_account(plan=BillingPlanType.PREMIUM)
        create_test_user(
            email='owner@test.test',
            account=account,
            is_account_owner=True
        )
        user = create_test_user(
            account=account,
            is_account_owner=False
        )
        workflow = create_test_workflow(user, tasks_count=1)
        task = workflow.current_task_instance
        TaskPerformer.objects.filter(
            task=task
        ).update(directly_status=DirectlyStatus.DELETED)
        api_client.token_authenticate(user)

        # act
        response = api_client.get(
            '/reports/dashboard/tasks/breakdown',
            data={'now': True}
        )

        # assert
        assert response.status_code == 200
        assert len(response.data) == 0


class TestDashboardMyTasksBreakdownBySteps:

    def test_my_tasks_breakdown_by_steps__ok(
        self,
        api_client
    ):
        # arrange
        account = create_test_account(plan=BillingPlanType.PREMIUM)
        create_test_user(
            email='owner@test.test',
            account=account,
            is_account_owner=True
        )
        template_owner = create_test_user(
            account=account,
            is_account_owner=False
        )
        user = create_test_user(
            email='testinguser@pneumatic.app',
            account=template_owner.account,
        )
        first_template = create_test_template(template_owner)
        second_template = create_test_template(template_owner, is_active=True)
        account_service = AccountService(
            instance=template_owner.account,
            user=template_owner
        )
        account_service.update_active_templates()

        first_task = first_template.tasks.get(number=1)
        first_task.add_raw_performer(user)
        second_task = first_template.tasks.get(number=2)
        second_task.add_raw_performer(user)

        second_template_first_task = second_template.tasks.get(number=1)
        second_template_first_task.add_raw_performer(user)

        first_workflow = create_test_workflow(template_owner, first_template)
        api_client.token_authenticate(user)
        api_client.post(
            f'/workflows/{first_workflow.id}/task-complete',
            data={'task_id': first_workflow.current_task_instance.id},
        )

        overdue_workflow = create_test_workflow(template_owner, first_template)
        task = overdue_workflow.tasks.get(number=1)
        date_created = overdue_workflow.date_created - timedelta(days=7)
        task.due_date = date_created + timedelta(seconds=1)
        task.date_started = date_created
        task.date_first_started = date_created
        task.save(update_fields=[
            'due_date',
            'date_started',
            'date_first_started',
        ])
        overdue_workflow.date_created = date_created
        overdue_workflow.save(update_fields=['date_created'])
        api_client.post(
            f'/workflows/{overdue_workflow.id}/task-complete',
            data={'task_id': overdue_workflow.current_task_instance.id},
        )
        third_workflow = create_test_workflow(template_owner, first_template)
        api_client.post(
            f'/workflows/{third_workflow.id}/task-complete',
            data={'task_id': third_workflow.current_task_instance.id},
        )

        api_client.token_authenticate(template_owner)
        api_client.post(
            f'/workflows/{overdue_workflow.id}/task-complete',
            data={'task_id': overdue_workflow.tasks.get(number=2).id},
        )

        second_workflow = create_test_workflow(template_owner, first_template)
        second_workflow.status = WorkflowStatus.RUNNING
        second_workflow.save(update_fields=['status'])

        fourth_workflow = create_test_workflow(template_owner, second_template)
        fourth_workflow.status = WorkflowStatus.DONE
        fourth_workflow.date_completed = timezone.now()
        fourth_workflow.save(update_fields=['status', 'date_completed'])

        api_client.token_authenticate(user)

        # act
        response = api_client.get(
            '/reports/dashboard/tasks/by-steps',
            data={'template_id': first_template.id},
        )

        # assert
        assert response.status_code == 200
        assert len(response.data) == 2
        assert response.data[0]['id'] == first_task.id
        assert response.data[0]['name'] == first_task.name
        assert response.data[0]['number'] == first_task.number
        assert response.data[0]['started'] == 3
        assert response.data[0]['completed'] == 3
        assert response.data[0]['in_progress'] == 4
        assert response.data[0]['overdue'] == 1
        assert response.data[1]['id'] == second_task.id
        assert response.data[1]['name'] == second_task.name
        assert response.data[1]['number'] == second_task.number
        assert response.data[1]['started'] == 3
        assert response.data[1]['completed'] == 1
        assert response.data[1]['in_progress'] == 3
        assert response.data[1]['overdue'] == 0

    def test_my_tasks_breakdown_by_steps__deleted_performer__ok(
        self,
        api_client
    ):

        # arrange
        account = create_test_account()
        create_test_user(
            email='owner@test.test',
            account=account,
            is_account_owner=True
        )
        user = create_test_user(
            account=account,
            is_account_owner=False
        )
        workflow = create_test_workflow(user, tasks_count=1)
        task = workflow.current_task_instance
        TaskPerformer.objects.filter(
            task=task
        ).update(directly_status=DirectlyStatus.DELETED)
        api_client.token_authenticate(user)

        # act
        response = api_client.get(
            '/reports/dashboard/tasks/by-steps',
            data={'template_id': workflow.template.id},
        )
        # assert
        assert response.status_code == 200
        assert len(response.data) == 0

    def test_my_tasks_breakdown__require_completion_by_all__partly_completed(
        self,
        api_client,
    ):
        """ caused by: https://my.pneumatic.app/workflows/12359 """
        # arrange
        account = create_test_account(plan=BillingPlanType.PREMIUM)
        create_test_user(
            email='owner@test.test',
            account=account,
            is_account_owner=True
        )
        template_owner = create_test_user(
            account=account,
            is_account_owner=False
        )
        user = create_test_user(
            email='testinguser@pneumatic.app',
            account=template_owner.account,
        )
        first_template = create_test_template(template_owner, is_active=True)
        account_service = AccountService(
            instance=template_owner.account,
            user=template_owner
        )
        account_service.update_active_templates()

        first_task = first_template.tasks.get(number=1)
        first_task.require_completion_by_all = True
        first_task.save()
        first_task.add_raw_performer(user)
        first_template.tasks.get(number=2)

        first_workflow = create_test_workflow(template_owner, first_template)
        api_client.token_authenticate(user)
        api_client.post(
            f'/workflows/{first_workflow.id}/task-complete',
            data={'task_id': first_workflow.current_task_instance.id},
        )

        overdue_workflow = create_test_workflow(template_owner, first_template)
        task = overdue_workflow.tasks.get(number=1)
        date_created = overdue_workflow.date_created - timedelta(days=7)
        task.due_date = date_created + timedelta(seconds=1)
        task.date_started = date_created
        task.date_first_started = date_created
        task.save(update_fields=[
            'due_date',
            'date_started',
            'date_first_started',
        ])
        overdue_workflow.date_created = date_created
        overdue_workflow.save(update_fields=['date_created'])
        api_client.token_authenticate(template_owner)
        api_client.post(
            f'/workflows/{overdue_workflow.id}/task-complete',
            data={'task_id': overdue_workflow.current_task_instance.id},
        )

        # act
        template_owner_response = api_client.get(
            '/reports/dashboard/tasks/by-steps',
            data={
                'template_id': first_template.id,
                'now': True,
            },
        )
        api_client.token_authenticate(user)
        regular_user_response = api_client.get(
            '/reports/dashboard/tasks/by-steps',
            data={
                'template_id': first_template.id,
                'now': True,
            },
        )

        # assert
        assert template_owner_response.status_code == 200
        assert len(template_owner_response.data) == 3
        assert template_owner_response.data[0]['id'] == first_task.id
        assert template_owner_response.data[0]['in_progress'] == 1
        assert template_owner_response.data[0]['overdue'] == 0
        assert regular_user_response.status_code == 200
        assert len(regular_user_response.data) == 1
        assert regular_user_response.data[0]['id'] == first_task.id
        assert regular_user_response.data[0]['in_progress'] == 1
        assert regular_user_response.data[0]['overdue'] == 1

    def test_my_tasks_breakdown__skipped_tasks__not_count_in_progress(
        self,
        api_client
    ):
        # arrange
        account = create_test_account(plan=BillingPlanType.PREMIUM)
        create_test_user(
            email='owner@test.test',
            account=account,
            is_account_owner=True
        )
        user = create_test_user(
            account=account,
            is_account_owner=False
        )
        api_client.token_authenticate(user)
        request_data = {
            'rules': [
                {
                    'predicates': [
                        {
                            'field': 'string-field-1',
                            'field_type': FieldType.STRING,
                            'operator': PredicateOperator.EQUAL,
                            'value': 'skip',
                        }
                    ]
                }
            ],
            'order': 1,
            'action': 'skip_task',
        }
        response = api_client.post(
            path='/templates',
            data={
                'name': 'Template',
                'is_active': True,
                'template_owners': [user.id],
                'kickoff': {
                    'fields': [
                        {
                            'order': 1,
                            'name': 'First step performer',
                            'type': FieldType.STRING,
                            'api_name': 'string-field-1',
                            'is_required': True,
                        }
                    ]
                },
                'tasks': [
                    {
                        'number': 1,
                        'name': 'First step',
                        'conditions': [request_data],
                        'raw_performers': [
                            {
                                'type': PerformerType.USER,
                                'source_id': user.id
                            }
                        ],
                    },
                    {
                        'number': 2,
                        'name': 'Second step',
                        'conditions': [],
                        'raw_performers': [
                            {
                                'type': PerformerType.USER,
                                'source_id': user.id
                            }
                        ],
                    },
                ]
            }
        )
        template_id = response.data['id']
        api_client.post(
            f'/templates/{template_id}/run',
            data={
                'name': 'Test',
                'kickoff': {
                    'string-field-1': 'skip',
                },
            },
        )
        api_client.post(
            f'/templates/{template_id}/run',
            data={
                'name': 'Test',
                'kickoff': {
                    'string-field-1': 'notskip',
                },
            },
        )

        # act
        response = api_client.get(
            '/reports/dashboard/tasks/by-steps',
            data={'template_id': template_id},
        )
        # assert
        assert response.status_code == 200
        assert response.data[0]['name'] == 'First step'
        assert response.data[0]['number'] == 1
        assert response.data[0]['started'] == 1
        assert response.data[0]['completed'] == 0
        assert response.data[0]['in_progress'] == 1
        assert response.data[0]['overdue'] == 0
        assert response.data[1]['name'] == 'Second step'
        assert response.data[1]['number'] == 2
        assert response.data[1]['started'] == 1
        assert response.data[1]['completed'] == 0
        assert response.data[1]['in_progress'] == 1
        assert response.data[1]['overdue'] == 0

    def test_my_tasks_breakdown__now__ok(
        self,
        api_client
    ):
        # arrange
        account = create_test_account(plan=BillingPlanType.PREMIUM)
        create_test_user(
            email='owner@test.test',
            account=account,
            is_account_owner=True
        )
        template_owner = create_test_user(
            account=account,
            is_account_owner=False
        )
        user = create_test_user(
            email='testinguser@pneumatic.app',
            account=template_owner.account,
        )
        first_template = create_test_template(template_owner)
        second_template = create_test_template(template_owner, is_active=True)
        account_service = AccountService(
            instance=template_owner.account,
            user=template_owner
        )
        account_service.update_active_templates()

        first_task = first_template.tasks.get(number=1)
        first_task.add_raw_performer(user)
        second_task = first_template.tasks.get(number=2)
        second_task.add_raw_performer(user)

        second_template_first_task = second_template.tasks.get(number=1)
        second_template_first_task.add_raw_performer(user)

        first_workflow = create_test_workflow(template_owner, first_template)
        api_client.token_authenticate(user)
        api_client.post(
            f'/workflows/{first_workflow.id}/task-complete',
            data={'task_id': first_workflow.current_task_instance.id},
        )

        overdue_workflow = create_test_workflow(template_owner, first_template)
        task = overdue_workflow.tasks.get(number=1)
        date_created = overdue_workflow.date_created - timedelta(days=7)
        task.due_date = date_created + timedelta(seconds=1)
        task.date_started = date_created
        task.date_first_started = date_created
        task.save(update_fields=[
            'due_date',
            'date_started',
            'date_first_started',
        ])
        overdue_workflow.date_created = date_created
        overdue_workflow.save(update_fields=['date_created'])
        third_workflow = create_test_workflow(template_owner, first_template)
        api_client.post(
            f'/workflows/{third_workflow.id}/task-complete',
            data={'task_id': third_workflow.current_task_instance.id},
        )

        second_workflow = create_test_workflow(template_owner, first_template)
        second_workflow.status = WorkflowStatus.RUNNING
        second_workflow.save(update_fields=['status'])
        api_client.post(
            f'/workflows/{second_workflow.id}/task-complete',
            data={'task_id': second_workflow.current_task_instance.id},
        )

        fourth_workflow = create_test_workflow(template_owner, second_template)
        fourth_workflow.status = WorkflowStatus.DONE
        fourth_workflow.date_completed = timezone.now()
        fourth_workflow.save(update_fields=['status', 'date_completed'])

        api_client.token_authenticate(user)

        # act
        response = api_client.get(
            '/reports/dashboard/tasks/by-steps',
            data={'template_id': first_template.id, 'now': True},
        )

        # assert
        assert response.status_code == 200
        assert len(response.data) == 2
        assert response.data[0]['id'] == first_task.id
        assert response.data[0]['name'] == first_task.name
        assert response.data[0]['number'] == first_task.number
        assert response.data[0]['in_progress'] == 1
        assert response.data[0]['started'] is None
        assert response.data[0]['completed'] is None
        assert response.data[0]['overdue'] == 1
        assert response.data[1]['id'] == second_task.id
        assert response.data[1]['name'] == second_task.name
        assert response.data[1]['number'] == second_task.number
        assert response.data[1]['in_progress'] == 3
        assert response.data[1]['started'] is None
        assert response.data[1]['completed'] is None
        assert response.data[1]['overdue'] == 0

    def test_my_tasks_breakdown__now__deleted_performer__ok(
        self,
        api_client
    ):

        # arrange
        account = create_test_account()
        create_test_user(
            email='owner@test.test',
            account=account,
            is_account_owner=True
        )
        user = create_test_user(
            account=account,
            is_account_owner=False
        )
        workflow = create_test_workflow(user, tasks_count=1)
        task = workflow.current_task_instance
        TaskPerformer.objects.filter(
            task=task
        ).update(directly_status=DirectlyStatus.DELETED)
        api_client.token_authenticate(user)

        # act
        response = api_client.get(
            '/reports/dashboard/tasks/by-steps',
            data={
                'template_id': workflow.template.id,
                'now': True
            }
        )

        # assert
        assert response.status_code == 200
        assert len(response.data) == 0

    def test_my_tasks_breakdown_by_steps__overdue_task__ok(
        self,
        api_client
    ):
        # arrange
        account = create_test_account()
        create_test_user(
            email='owner@test.test',
            account=account,
            is_account_owner=True
        )
        template_owner = create_test_user(
            account=account,
            is_account_owner=False
        )
        user = create_test_user(
            email='testinguser@pneumatic.app',
            account=template_owner.account,
        )
        template = create_test_template(
            user=template_owner,
            tasks_count=1,
            is_active=True
        )
        task_template = template.tasks.get(number=1)
        task_template.add_raw_performer(user)

        overdue_workflow = create_test_workflow(
            user=template_owner,
            template=template
        )
        overdue_workflow.date_created = timezone.now() - timedelta(minutes=3)
        overdue_workflow.save(update_fields=['date_created'])
        task = overdue_workflow.tasks.get(number=1)
        date_created = overdue_workflow.date_created - timedelta(minutes=2)
        task.due_date = date_created + timedelta(seconds=1)
        task.date_started = date_created
        task.date_first_started = date_created
        task.save(update_fields=[
            'due_date',
            'date_started',
            'date_first_started',
        ])
        api_client.token_authenticate(template_owner)

        # act
        response = api_client.get(
            '/reports/dashboard/tasks/by-steps',
            data={'template_id': template.id},
        )

        # assert
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]['id'] == task_template.id
        assert response.data[0]['name'] == task_template.name
        assert response.data[0]['number'] == 1
        assert response.data[0]['started'] == 1
        assert response.data[0]['completed'] == 0
        assert response.data[0]['in_progress'] == 1
        assert response.data[0]['overdue'] == 1

    def test_my_tasks_breakdown_by_steps__overdue_workflow__not_count(
        self,
        api_client
    ):
        # arrange
        account = create_test_account()
        create_test_user(
            email='owner@test.test',
            account=account,
            is_account_owner=True
        )
        template_owner = create_test_user(
            account=account,
            is_account_owner=False
        )
        template = create_test_template(
            user=template_owner,
            tasks_count=1,
            is_active=True
        )
        task_template = template.tasks.get(number=1)
        overdue_workflow = create_test_workflow(
            user=template_owner,
            template=template
        )
        overdue_workflow.date_created = timezone.now() - timedelta(minutes=3)
        overdue_workflow.due_date = timezone.now() - timedelta(minutes=1)
        overdue_workflow.save(update_fields=['date_created', 'due_date'])
        api_client.token_authenticate(template_owner)

        # act
        response = api_client.get(
            '/reports/dashboard/tasks/by-steps',
            data={'template_id': template.id},
        )

        # assert
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]['id'] == task_template.id
        assert response.data[0]['name'] == task_template.name
        assert response.data[0]['number'] == 1
        assert response.data[0]['started'] == 1
        assert response.data[0]['completed'] == 0
        assert response.data[0]['in_progress'] == 1
        assert response.data[0]['overdue'] == 0

    def test_my_tasks_breakdown_by_steps__now__overdue_task__ok(
        self,
        api_client
    ):
        # arrange
        account = create_test_account()
        create_test_user(
            email='owner@test.test',
            account=account,
            is_account_owner=True
        )
        template_owner = create_test_user(
            account=account,
            is_account_owner=False
        )
        user = create_test_user(
            email='testinguser@pneumatic.app',
            account=template_owner.account,
        )
        template = create_test_template(
            user=template_owner,
            tasks_count=1,
            is_active=True
        )
        task_template = template.tasks.get(number=1)
        task_template.add_raw_performer(user)

        overdue_workflow = create_test_workflow(
            user=template_owner,
            template=template
        )
        overdue_workflow.date_created = timezone.now() - timedelta(minutes=3)
        overdue_workflow.save(update_fields=['date_created'])
        task = overdue_workflow.tasks.get(number=1)
        date_created = timezone.now() - timedelta(minutes=2)
        task.due_date = date_created + timedelta(seconds=1)
        task.date_started = date_created
        task.date_first_started = date_created
        task.save(update_fields=[
            'due_date',
            'date_started',
            'date_first_started',
        ])
        api_client.token_authenticate(template_owner)

        # act
        response = api_client.get(
            '/reports/dashboard/tasks/by-steps',
            data={'template_id': template.id, 'now': True},
        )

        # assert
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]['id'] == task_template.id
        assert response.data[0]['name'] == task_template.name
        assert response.data[0]['number'] == 1
        assert response.data[0]['started'] is None
        assert response.data[0]['completed'] is None
        assert response.data[0]['in_progress'] == 1
        assert response.data[0]['overdue'] == 1

    def test_my_tasks_breakdown_by_steps__now__overdue_workflow__not_count(
        self,
        api_client
    ):
        # arrange
        account = create_test_account()
        create_test_user(
            email='owner@test.test',
            account=account,
            is_account_owner=True
        )
        template_owner = create_test_user(
            account=account,
            is_account_owner=False
        )
        template = create_test_template(
            user=template_owner,
            tasks_count=1,
            is_active=True
        )
        task_template = template.tasks.get(number=1)
        overdue_workflow = create_test_workflow(
            user=template_owner,
            template=template
        )
        overdue_workflow.date_created = timezone.now() - timedelta(minutes=3)
        overdue_workflow.due_date = timezone.now() - timedelta(minutes=1)
        overdue_workflow.save(update_fields=['date_created', 'due_date'])
        api_client.token_authenticate(template_owner)

        # act
        response = api_client.get(
            '/reports/dashboard/tasks/by-steps',
            data={'template_id': template.id, 'now': True},
        )

        # assert
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]['id'] == task_template.id
        assert response.data[0]['name'] == task_template.name
        assert response.data[0]['number'] == 1
        assert response.data[0]['started'] is None
        assert response.data[0]['completed'] is None
        assert response.data[0]['in_progress'] == 1
        assert response.data[0]['overdue'] == 0
