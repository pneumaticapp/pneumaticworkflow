import pytest
from datetime import timedelta
from django.contrib.auth import get_user_model
from django.utils import timezone
from pneumatic_backend.accounts.services import AccountService
from pneumatic_backend.reports.tests.fixtures import (
    create_test_user,
    create_invited_user,
    create_test_template,
    create_test_workflow,
    create_test_account,
)
from pneumatic_backend.processes.enums import (
    WorkflowStatus,
)
from pneumatic_backend.accounts.enums import BillingPlanType


UserModel = get_user_model()
pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def replica_mock(mocker):
    mocker.patch('django.conf.settings.REPLICA', 'default')
    yield


class TestDashboardOverview:

    def test_overview__ok(self, api_client):

        # arrange
        account = create_test_account()
        create_test_user(
            email='owner@test.test',
            account=account,
            is_account_owner=True
        )
        user = create_test_user(account=account, is_account_owner=False)
        first_template = create_test_template(user)
        second_template = create_test_template(user, is_active=True)
        create_test_template(user, is_active=True)
        fourth_template = create_test_template(user, is_active=True)
        account_service = AccountService(
            instance=user.account,
            user=user
        )
        account_service.update_active_templates()
        create_test_template(user)

        first_workflow = create_test_workflow(user, first_template)
        first_workflow.status = WorkflowStatus.DONE
        date_created = first_workflow.date_created - timedelta(days=2)
        first_workflow.date_created = date_created
        first_workflow.date_completed = timezone.now()
        first_workflow.save(update_fields=[
            'status',
            'date_completed',
            'date_created',
        ])

        overdue_workflow = create_test_workflow(user, first_template)
        task = overdue_workflow.tasks.get(number=1)
        date_started = timezone.now() - timedelta(seconds=2)
        task.date_started = date_started
        task.date_first_started = date_started
        task.due_date = date_started + timedelta(seconds=1)

        task.save(update_fields=[
            'due_date',
            'date_started',
            'date_first_started',
        ])
        overdue_workflow.status = WorkflowStatus.DONE
        date_created = overdue_workflow.date_created - timedelta(days=2)
        overdue_workflow.date_created = date_created
        overdue_workflow.date_completed = timezone.now()
        overdue_workflow.save(update_fields=[
            'status',
            'date_completed',
            'date_created'
        ])

        second_workflow = create_test_workflow(user, first_template)
        second_workflow.status = WorkflowStatus.RUNNING
        second_workflow.save(update_fields=['status'])

        fourth_workflow = create_test_workflow(user, second_template)
        fourth_workflow.status = WorkflowStatus.DONE
        fourth_workflow.date_completed = timezone.now()
        fourth_workflow.save(update_fields=['status', 'date_completed'])

        uncount_workflow = create_test_workflow(user, fourth_template)
        uncount_workflow.status = WorkflowStatus.DONE
        date_created = uncount_workflow.date_created - timedelta(days=2)
        uncount_workflow.date_created = date_created
        uncount_workflow.date_completed = timezone.now() - timedelta(days=2)
        uncount_workflow.save(update_fields=[
            'status',
            'date_completed',
            'date_created',
        ])

        seventh_workflow = create_test_workflow(user, fourth_template)
        seventh_workflow.status = WorkflowStatus.DELAYED
        seventh_workflow.save(update_fields=['status'])

        api_client.token_authenticate(user)

        # act
        response = api_client.get('/reports/dashboard/workflows/overview')

        # assert
        assert response.status_code == 200
        assert response.data['started'] == 3
        assert response.data['completed'] == 3
        assert response.data['in_progress'] == 5
        assert response.data['overdue'] == 1

    def test_overview__different_user_statistic__correct_count(
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
        user = create_test_user(account=account, is_account_owner=False)
        create_invited_user(user, 'test1@pneumatic.app')

        first_template = create_test_template(user, is_active=True)
        second_template = create_test_template(user)
        fourth_template = create_test_template(user)
        create_test_template(user, is_active=True)
        account_service = AccountService(
            instance=user.account,
            user=user
        )
        account_service.update_active_templates()
        create_test_template(user)

        first_workflow = create_test_workflow(user, first_template)
        first_workflow.status = WorkflowStatus.DONE
        first_workflow.date_completed = timezone.now()
        first_workflow.save(update_fields=['status', 'date_completed'])

        second_workflow = create_test_workflow(user, first_template)
        second_workflow.status = WorkflowStatus.RUNNING
        second_workflow.save(update_fields=['status'])

        fourth_workflow = create_test_workflow(user, second_template)
        fourth_workflow.status = WorkflowStatus.DONE
        fourth_workflow.date_completed = timezone.now()
        fourth_workflow.save(update_fields=['status', 'date_completed'])

        sixth_workflow = create_test_workflow(user, fourth_template)
        sixth_workflow.status = WorkflowStatus.DONE
        sixth_workflow.date_completed = timezone.now()
        sixth_workflow.save(update_fields=['status', 'date_completed'])

        seventh_workflow = create_test_workflow(user, fourth_template)
        seventh_workflow.status = WorkflowStatus.DELAYED
        seventh_workflow.save(update_fields=['status'])

        api_client.token_authenticate(user)

        # act
        response = api_client.get('/reports/dashboard/workflows/overview')

        # assert
        assert response.status_code == 200
        assert response.data['started'] == 5
        assert response.data['completed'] == 3
        assert response.data['in_progress'] == 5
        assert response.data['overdue'] == 0

    def test_overview__legacy_template__count(
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
        user = create_test_user(account=account, is_account_owner=False)
        first_template = create_test_template(user, is_active=True)
        second_template = create_test_template(user, is_active=True)
        fourth_template = create_test_template(user, is_active=True)

        first_workflow = create_test_workflow(user, first_template)
        first_workflow.status = WorkflowStatus.RUNNING
        first_workflow.save(update_fields=['status'])

        second_workflow = create_test_workflow(user, second_template)
        second_workflow.status = WorkflowStatus.DONE
        second_workflow.date_completed = timezone.now()
        second_workflow.save(update_fields=['status', 'date_completed'])

        fourth_workflow = create_test_workflow(user, fourth_template)
        fourth_workflow.status = WorkflowStatus.DONE
        fourth_workflow.date_completed = timezone.now()
        fourth_workflow.save(update_fields=['status', 'date_completed'])

        fifth_workflow = create_test_workflow(user, fourth_template)
        fifth_workflow.status = WorkflowStatus.DELAYED
        fifth_workflow.save(update_fields=['status'])

        api_client.token_authenticate(user)
        api_client.delete(f'/templates/{fourth_template.id}')

        # act
        response = api_client.get('/reports/dashboard/workflows/overview')

        # assert
        assert response.status_code == 200
        assert response.data['started'] == 4
        assert response.data['completed'] == 2
        assert response.data['in_progress'] == 4
        assert response.data['overdue'] == 0

    def test_overview__now__ok(
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
        user = create_test_user(account=account, is_account_owner=False)
        first_template = create_test_template(user)
        second_template = create_test_template(user, is_active=True)
        fourth_template = create_test_template(user, is_active=True)
        account_service = AccountService(
            instance=user.account,
            user=user
        )
        account_service.update_active_templates()
        create_test_template(user)

        first_workflow = create_test_workflow(user, first_template)
        first_workflow.status = WorkflowStatus.DONE
        date_created = first_workflow.date_created - timedelta(days=2)
        first_workflow.date_created = date_created
        first_workflow.date_completed = timezone.now()
        first_workflow.save(update_fields=[
            'status',
            'date_completed',
            'date_created',
        ])

        overdue_workflow = create_test_workflow(user, first_template)
        task = overdue_workflow.tasks.get(number=1)

        date_started = timezone.now() - timedelta(seconds=2)
        task.date_started = date_started
        task.date_first_started = date_started
        task.due_date = date_started + timedelta(seconds=1)
        task.save(update_fields=[
            'due_date',
            'date_started',
            'date_first_started',
        ])
        date_created = overdue_workflow.date_created - timedelta(days=2)
        overdue_workflow.date_created = date_created
        overdue_workflow.save(update_fields=['date_created'])
        api_client.token_authenticate(user)

        second_workflow = create_test_workflow(user, first_template)
        second_workflow.status = WorkflowStatus.RUNNING
        second_workflow.save(update_fields=['status'])

        fourth_workflow = create_test_workflow(user, second_template)
        fourth_workflow.status = WorkflowStatus.DONE
        fourth_workflow.date_completed = timezone.now()
        fourth_workflow.save(update_fields=['status', 'date_completed'])

        uncount_workflow = create_test_workflow(user, fourth_template)
        uncount_workflow.status = WorkflowStatus.DONE
        date_created = uncount_workflow.date_created - timedelta(days=2)
        uncount_workflow.date_created = date_created
        uncount_workflow.date_completed = timezone.now() - timedelta(days=2)
        uncount_workflow.save(update_fields=[
            'status',
            'date_completed',
            'date_created',
        ])

        seventh_workflow = create_test_workflow(user, fourth_template)
        seventh_workflow.status = WorkflowStatus.DELAYED
        seventh_workflow.save(update_fields=['status'])

        # act
        response = api_client.get(
            '/reports/dashboard/workflows/overview',
            data={'now': True},
        )

        # assert
        assert response.status_code == 200
        assert response.data['started'] is None
        assert response.data['completed'] is None
        assert response.data['in_progress'] == 2
        assert response.data['overdue'] == 1

    def test_overview__overdue_task__ok(self, api_client):

        # arrange
        account = create_test_account()
        create_test_user(
            email='owner@test.test',
            account=account,
            is_account_owner=True
        )
        user = create_test_user(account=account, is_account_owner=False)
        overdue_workflow = create_test_workflow(user, tasks_count=1)
        task = overdue_workflow.current_task_instance

        date_started = timezone.now() - timedelta(seconds=2)
        task.date_started = date_started
        task.date_first_started = date_started
        task.due_date = date_started + timedelta(seconds=1)
        task.save(update_fields=[
            'due_date',
            'date_started',
            'date_first_started',
        ])
        api_client.token_authenticate(user)

        # act
        response = api_client.get('/reports/dashboard/workflows/overview')

        # assert
        assert response.status_code == 200
        assert response.data['started'] == 1
        assert response.data['completed'] == 0
        assert response.data['in_progress'] == 1
        assert response.data['overdue'] == 1

    def test_overview__overdue_workflow__ok(self, api_client):

        # arrange
        account = create_test_account()
        create_test_user(
            email='owner@test.test',
            account=account,
            is_account_owner=True
        )
        user = create_test_user(account=account, is_account_owner=False)
        overdue_workflow = create_test_workflow(user, tasks_count=1)
        overdue_workflow.due_date = timezone.now() - timedelta(minutes=1)
        overdue_workflow.save(update_fields=['due_date'])
        api_client.token_authenticate(user)

        # act
        response = api_client.get('/reports/dashboard/workflows/overview')

        # assert
        assert response.status_code == 200
        assert response.data['started'] == 1
        assert response.data['completed'] == 0
        assert response.data['in_progress'] == 1
        assert response.data['overdue'] == 1

    def test_overview__now_overdue_task__ok(
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
        user = create_test_user(account=account, is_account_owner=False)
        overdue_workflow = create_test_workflow(user, tasks_count=1)
        task = overdue_workflow.tasks.get(number=1)
        date_started = timezone.now() - timedelta(seconds=2)
        task.date_started = date_started
        task.date_first_started = date_started
        task.due_date = date_started + timedelta(seconds=1)
        task.save(update_fields=[
            'due_date',
            'date_started',
            'date_first_started',
        ])
        date_created = overdue_workflow.date_created - timedelta(days=2)
        overdue_workflow.date_created = date_created
        overdue_workflow.save(update_fields=['date_created'])
        api_client.token_authenticate(user)

        # act
        response = api_client.get(
            '/reports/dashboard/workflows/overview',
            data={'now': True},
        )

        # assert
        assert response.status_code == 200
        assert response.data['started'] is None
        assert response.data['completed'] is None
        assert response.data['in_progress'] == 1
        assert response.data['overdue'] == 1

    def test_overview__now_overdue_workflow__ok(
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
        user = create_test_user(account=account, is_account_owner=False)
        overdue_workflow = create_test_workflow(user, tasks_count=1)
        overdue_workflow.date_created = timezone.now() - timedelta(minutes=2)
        overdue_workflow.due_date = timezone.now() - timedelta(minutes=1)
        overdue_workflow.save(update_fields=['due_date', 'date_created'])
        api_client.token_authenticate(user)

        # act
        response = api_client.get(
            '/reports/dashboard/workflows/overview',
            data={'now': True},
        )

        # assert
        assert response.status_code == 200
        assert response.data['started'] is None
        assert response.data['completed'] is None
        assert response.data['in_progress'] == 1
        assert response.data['overdue'] == 1

    def test_overview__now__not_overdue_afert_overdue__task_returned__ok(
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
        user = create_test_user(account=account, is_account_owner=False)
        api_client.token_authenticate(user)

        workflow = create_test_workflow(user)
        r1 = api_client.post(
            f'/workflows/{workflow.id}/task-complete',
            data={'task_id': workflow.current_task_instance.id},
        )
        task = workflow.tasks.get(number=2)
        date_started = timezone.now() - timedelta(days=7)
        task.date_started = date_started
        task.date_first_started = date_started
        task.due_date = date_started + timedelta(hours=1)  # overdue
        task.save(update_fields=[
            'due_date',
            'date_started',
            'date_first_started',
        ])
        r2 = api_client.post(
            f'/workflows/{workflow.id}/task-revert',
        )

        # act
        response = api_client.get(
            '/reports/dashboard/workflows/overview',
            data={'now': True},
        )

        # assert
        assert r1.status_code == 204
        assert r2.status_code == 204
        workflow.refresh_from_db()
        assert workflow.current_task == 1
        assert response.status_code == 200
        assert response.data['started'] is None
        assert response.data['completed'] is None
        assert response.data['in_progress'] == 1
        assert response.data['overdue'] == 0


class TestDashboardWorkflowBreakdown:

    def test_workflow_breakdown__ok(
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
        user = create_test_user(account=account, is_account_owner=False)
        first_template = create_test_template(user)
        second_template = create_test_template(user, is_active=True)
        third_template = create_test_template(user, is_active=True)
        fourth_template = create_test_template(user, is_active=True)
        account_service = AccountService(
            instance=user.account,
            user=user
        )
        account_service.update_active_templates()
        draft_template = create_test_template(user)

        first_workflow = create_test_workflow(user, first_template)
        first_workflow.status = WorkflowStatus.DONE
        date_created = first_workflow.date_created - timedelta(days=2)
        first_workflow.date_created = date_created
        first_workflow.date_completed = timezone.now()
        first_workflow.save(update_fields=[
            'status',
            'date_completed',
            'date_created',
        ])

        overdue_workflow = create_test_workflow(user, first_template)
        task = overdue_workflow.tasks.get(number=1)
        date_started = timezone.now() - timedelta(seconds=2)
        task.date_started = date_started
        task.date_first_started = date_started
        task.due_date = date_started + timedelta(seconds=1)
        task.save(update_fields=[
            'due_date',
            'date_started',
            'date_first_started',
        ])
        overdue_workflow.status = WorkflowStatus.DONE
        date_created = overdue_workflow.date_created - timedelta(days=2)
        overdue_workflow.date_created = date_created
        overdue_workflow.date_completed = timezone.now()
        overdue_workflow.save(update_fields=[
            'status',
            'date_completed',
            'date_created'
        ])

        second_workflow = create_test_workflow(user, first_template)
        second_workflow.status = WorkflowStatus.RUNNING
        second_workflow.save(update_fields=['status'])

        not_overdue_workflow = create_test_workflow(
            user=user,
            template=first_template,
        )

        date_started = not_overdue_workflow.date_created - timedelta(days=8)
        task.date_started = date_started
        task.date_first_started = date_started
        task.due_date = date_started + timedelta(seconds=1)
        task.save(update_fields=[
            'due_date',
            'date_started',
            'date_first_started',
        ])

        not_overdue_workflow.status = WorkflowStatus.DONE
        date_completed = date_started + timedelta(minutes=1)
        not_overdue_workflow.date_completed = date_completed
        not_overdue_workflow.date_created = date_started
        not_overdue_workflow.save(
            update_fields=['date_created', 'date_completed', 'status'],
        )

        fourth_workflow = create_test_workflow(user, second_template)
        fourth_workflow.status = WorkflowStatus.DONE
        fourth_workflow.date_completed = timezone.now()
        fourth_workflow.save(update_fields=['status', 'date_completed'])

        uncount_workflow = create_test_workflow(user, fourth_template)
        uncount_workflow.status = WorkflowStatus.DONE
        date_created = uncount_workflow.date_created - timedelta(days=2)
        uncount_workflow.date_created = date_created
        uncount_workflow.date_completed = timezone.now() - timedelta(days=2)
        uncount_workflow.save(update_fields=[
            'status',
            'date_completed',
            'date_created',
        ])

        seventh_workflow = create_test_workflow(user, fourth_template)
        seventh_workflow.status = WorkflowStatus.DELAYED
        seventh_workflow.save(update_fields=['status'])

        api_client.token_authenticate(user)

        # act
        response = api_client.get('/reports/dashboard/workflows/breakdown')

        # assert
        assert response.status_code == 200
        assert len(response.data) == 5
        assert response.data[0]['template_id'] == first_template.id
        assert response.data[0]['template_name'] == first_template.name
        assert response.data[0]['is_active'] == first_template.is_active
        assert response.data[0]['started'] == 1
        assert response.data[0]['completed'] == 2
        assert response.data[0]['in_progress'] == 3
        assert response.data[0]['overdue'] == 1

        assert response.data[1]['template_id'] == second_template.id
        assert response.data[1]['template_name'] == second_template.name
        assert response.data[1]['is_active'] == second_template.is_active
        assert response.data[1]['started'] == 1
        assert response.data[1]['completed'] == 1
        assert response.data[1]['in_progress'] == 1
        assert response.data[1]['overdue'] == 0

        assert response.data[2]['template_id'] == fourth_template.id
        assert response.data[2]['template_name'] == fourth_template.name
        assert response.data[2]['is_active'] == fourth_template.is_active
        assert response.data[2]['started'] == 1
        assert response.data[2]['completed'] == 0
        assert response.data[2]['in_progress'] == 1
        assert response.data[2]['overdue'] == 0

        assert response.data[3]['template_id'] == third_template.id
        assert response.data[3]['template_name'] == third_template.name
        assert response.data[3]['is_active'] == third_template.is_active
        assert response.data[3]['started'] == 0
        assert response.data[3]['completed'] == 0
        assert response.data[3]['in_progress'] == 0
        assert response.data[3]['overdue'] == 0

        assert response.data[4]['template_id'] == draft_template.id
        assert response.data[4]['template_name'] == draft_template.name
        assert response.data[4]['is_active'] is False
        assert response.data[4]['started'] == 0
        assert response.data[4]['completed'] == 0
        assert response.data[4]['in_progress'] == 0
        assert response.data[4]['overdue'] == 0

    def test_workflow_breakdown__legacy_template__not_count(
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
        user = create_test_user(account=account, is_account_owner=False)
        first_template = create_test_template(user)
        second_template = create_test_template(user, is_active=True)
        account_service = AccountService(
            instance=user.account,
            user=user
        )
        account_service.update_active_templates()

        first_workflow = create_test_workflow(user, first_template)
        first_workflow.status = WorkflowStatus.DONE
        date_created = first_workflow.date_created - timedelta(days=2)
        first_workflow.date_created = date_created
        first_workflow.date_completed = timezone.now()
        first_workflow.save(update_fields=[
            'status',
            'date_completed',
            'date_created',
        ])

        overdue_workflow = create_test_workflow(user, first_template)
        task = overdue_workflow.tasks.get(number=1)
        date_started = timezone.now() - timedelta(seconds=2)
        task.date_started = date_started
        task.date_first_started = date_started
        task.due_date = date_started + timedelta(seconds=1)
        task.save(update_fields=[
            'due_date',
            'date_started',
            'date_first_started',
        ])
        overdue_workflow.status = WorkflowStatus.DONE
        date_created = overdue_workflow.date_created - timedelta(days=2)
        overdue_workflow.date_created = date_created
        overdue_workflow.date_completed = timezone.now()
        overdue_workflow.save(update_fields=[
            'status',
            'date_completed',
            'date_created'
        ])

        second_workflow = create_test_workflow(user, first_template)
        second_workflow.status = WorkflowStatus.RUNNING
        second_workflow.save(update_fields=['status'])

        fourth_workflow = create_test_workflow(user, second_template)
        fourth_workflow.status = WorkflowStatus.DONE
        fourth_workflow.date_completed = timezone.now()
        fourth_workflow.save(update_fields=['status', 'date_completed'])
        api_client.token_authenticate(user)
        api_client.delete(f'/templates/{second_template.id}')

        # act
        response = api_client.get('/reports/dashboard/workflows/breakdown')

        # assert
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]['template_id'] == first_template.id
        assert response.data[0]['template_name'] == first_template.name
        assert response.data[0]['is_active'] == first_template.is_active
        assert response.data[0]['started'] == 1
        assert response.data[0]['completed'] == 2
        assert response.data[0]['in_progress'] == 3
        assert response.data[0]['overdue'] == 1

    def test_workflow_breakdown__now__ok(
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
        user = create_test_user(account=account, is_account_owner=False)
        first_template = create_test_template(user, name='first')
        second_template = create_test_template(
            user,
            is_active=True,
            name='second'
        )
        third_template = create_test_template(
            user,
            is_active=True,
            name='third'
        )
        fourth_template = create_test_template(
            user,
            is_active=True,
            name='fourth'
        )
        account_service = AccountService(
            instance=user.account,
            user=user
        )
        account_service.update_active_templates()
        draft_template = create_test_template(
            user,
            is_active=False,
            name='draft'
        )

        first_workflow = create_test_workflow(user, first_template)
        first_workflow.status = WorkflowStatus.DONE
        date_created = first_workflow.date_created - timedelta(days=2)
        first_workflow.date_created = date_created
        first_workflow.date_completed = timezone.now()
        first_workflow.save(update_fields=[
            'status',
            'date_completed',
            'date_created',
        ])

        overdue_workflow = create_test_workflow(user, first_template)
        task = overdue_workflow.tasks.get(number=1)
        date_started = timezone.now() - timedelta(seconds=2)
        task.date_started = date_started
        task.date_first_started = date_started
        task.due_date = date_started + timedelta(seconds=1)
        task.save(update_fields=[
            'due_date',
            'date_started',
            'date_first_started',
        ])
        date_created = overdue_workflow.date_created - timedelta(days=2)
        overdue_workflow.date_created = date_created
        overdue_workflow.save(update_fields=[
            'status',
            'date_created'
        ])

        second_workflow = create_test_workflow(user, first_template)
        second_workflow.status = WorkflowStatus.RUNNING
        second_workflow.save(update_fields=['status'])

        not_overdue_workflow = create_test_workflow(
            user=user,
            template=first_template,
        )
        task = not_overdue_workflow.tasks.get(number=1)
        date_started = not_overdue_workflow.date_created - timedelta(days=8)
        task.date_started = date_started
        task.date_first_started = date_started
        task.due_date = date_started + timedelta(seconds=1)
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

        fourth_workflow = create_test_workflow(user, second_template)
        fourth_workflow.status = WorkflowStatus.DONE
        fourth_workflow.date_completed = timezone.now()
        fourth_workflow.save(update_fields=['status', 'date_completed'])

        uncount_workflow = create_test_workflow(user, fourth_template)
        uncount_workflow.status = WorkflowStatus.DONE
        date_created = uncount_workflow.date_created - timedelta(days=2)
        uncount_workflow.date_created = date_created
        uncount_workflow.date_completed = timezone.now() - timedelta(days=2)
        uncount_workflow.save(update_fields=[
            'status',
            'date_completed',
            'date_created',
        ])

        # not count
        seventh_workflow = create_test_workflow(user, fourth_template)
        seventh_workflow.status = WorkflowStatus.DELAYED
        seventh_workflow.save(update_fields=['status'])

        api_client.token_authenticate(user)

        # act
        response = api_client.get(
            '/reports/dashboard/workflows/breakdown',
            data={'now': True}
        )

        # assert
        assert response.status_code == 200
        assert len(response.data) == 5
        assert response.data[0]['is_active'] == first_template.is_active
        assert response.data[0]['in_progress'] == 2
        assert response.data[0]['started'] is None
        assert response.data[0]['completed'] is None
        assert response.data[0]['overdue'] == 1
        assert response.data[0]['template_name'] == first_template.name
        assert response.data[0]['template_id'] == first_template.id

        assert response.data[1]['is_active'] == second_template.is_active
        assert response.data[1]['started'] is None
        assert response.data[1]['completed'] is None
        assert response.data[1]['in_progress'] == 0
        assert response.data[1]['overdue'] == 0
        assert response.data[1]['template_name'] == second_template.name
        assert response.data[1]['template_id'] == second_template.id

        assert response.data[2]['is_active'] == third_template.is_active
        assert response.data[2]['started'] is None
        assert response.data[2]['completed'] is None
        assert response.data[2]['in_progress'] == 0
        assert response.data[2]['overdue'] == 0
        assert response.data[2]['template_name'] == third_template.name
        assert response.data[2]['template_id'] == third_template.id

        assert response.data[3]['is_active'] == fourth_template.is_active
        assert response.data[3]['in_progress'] == 0
        assert response.data[3]['started'] is None
        assert response.data[3]['completed'] is None
        assert response.data[3]['overdue'] == 0
        assert response.data[3]['template_name'] == fourth_template.name
        assert response.data[3]['template_id'] == fourth_template.id

        assert response.data[4]['is_active'] is False
        assert response.data[4]['started'] is None
        assert response.data[4]['completed'] is None
        assert response.data[4]['in_progress'] == 0
        assert response.data[4]['overdue'] == 0
        assert response.data[4]['template_name'] == draft_template.name
        assert response.data[4]['template_id'] == draft_template.id

    def test_workflow_breakdown__draft_template_with_zero_workflows__ok(
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
        user = create_test_user(account=account, is_account_owner=False)
        template = create_test_template(user, is_active=False)
        api_client.token_authenticate(user)

        # act
        response = api_client.get('/reports/dashboard/workflows/breakdown')

        # assert
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]['template_id'] == template.id
        assert response.data[0]['template_name'] == template.name
        assert response.data[0]['is_active'] is False
        assert response.data[0]['started'] == 0
        assert response.data[0]['completed'] == 0
        assert response.data[0]['in_progress'] == 0
        assert response.data[0]['overdue'] == 0

    def test_workflow_breakdown__date_range__ok(
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
        user = create_test_user(account=account, is_account_owner=False)
        api_client.token_authenticate(user)
        date_now = timezone.now()
        date_from = (date_now - timedelta(hours=1))
        date_to = (date_now + timedelta(hours=1))
        draft_template = create_test_template(
            user=user,
            is_active=False,
            tasks_count=1
        )
        active_template = create_test_template(
            user=user,
            is_active=True,
            tasks_count=1
        )
        create_test_workflow(
            user=user,
            template=active_template,
        )
        workflow_out_range = create_test_workflow(
            user=user,
            template=active_template,
        )
        workflow_out_range.date_created = (date_from - timedelta(minutes=1))
        workflow_out_range.date_completed = (date_from - timedelta(minutes=1))
        workflow_out_range.status = WorkflowStatus.DONE
        workflow_out_range.save(
            update_fields=[
                'date_created',
                'date_completed',
                'status'
            ]
        )

        # act
        response = api_client.get(
            path='/reports/dashboard/workflows/breakdown',
            data={
                'date_from': date_from,
                'date_to': date_to,
            }
        )

        # assert
        assert response.status_code == 200
        assert len(response.data) == 2

        assert response.data[0]['template_id'] == active_template.id
        assert response.data[0]['template_name'] == active_template.name
        assert response.data[0]['is_active'] is True
        assert response.data[0]['started'] == 1
        assert response.data[0]['completed'] == 0
        assert response.data[0]['in_progress'] == 1
        assert response.data[0]['overdue'] == 0

        assert response.data[1]['template_id'] == draft_template.id
        assert response.data[1]['template_name'] == draft_template.name
        assert response.data[1]['is_active'] is False
        assert response.data[1]['started'] == 0
        assert response.data[1]['completed'] == 0
        assert response.data[1]['in_progress'] == 0
        assert response.data[1]['overdue'] == 0

    def test_workflow_breakdown__date_range_tsp__ok(
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
        user = create_test_user(account=account, is_account_owner=False)
        api_client.token_authenticate(user)
        date_now = timezone.now()
        date_from = (date_now - timedelta(hours=1))
        date_to = (date_now + timedelta(hours=1))
        draft_template = create_test_template(
            user=user,
            is_active=False,
            tasks_count=1
        )
        active_template = create_test_template(
            user=user,
            is_active=True,
            tasks_count=1
        )
        create_test_workflow(
            user=user,
            template=active_template,
        )
        workflow_out_range = create_test_workflow(
            user=user,
            template=active_template,
        )
        workflow_out_range.date_created = (date_from - timedelta(minutes=1))
        workflow_out_range.date_completed = (date_from - timedelta(minutes=1))
        workflow_out_range.status = WorkflowStatus.DONE
        workflow_out_range.save(
            update_fields=[
                'date_created',
                'date_completed',
                'status'
            ]
        )

        # act
        response = api_client.get(
            path='/reports/dashboard/workflows/breakdown',
            data={
                'date_from_tsp': date_from.timestamp(),
                'date_to_tsp': date_to.timestamp(),
            }
        )

        # assert
        assert response.status_code == 200
        assert len(response.data) == 2

        assert response.data[0]['template_id'] == active_template.id
        assert response.data[0]['template_name'] == active_template.name
        assert response.data[0]['is_active'] is True
        assert response.data[0]['started'] == 1
        assert response.data[0]['completed'] == 0
        assert response.data[0]['in_progress'] == 1
        assert response.data[0]['overdue'] == 0

        assert response.data[1]['template_id'] == draft_template.id
        assert response.data[1]['template_name'] == draft_template.name
        assert response.data[1]['is_active'] is False
        assert response.data[1]['started'] == 0
        assert response.data[1]['completed'] == 0
        assert response.data[1]['in_progress'] == 0
        assert response.data[1]['overdue'] == 0

    def test_workflow_breakdown__overdue_task__ok(
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
        user = create_test_user(account=account, is_account_owner=False)
        overdue_workflow = create_test_workflow(user, tasks_count=1)
        task = overdue_workflow.current_task_instance
        date_started = timezone.now() - timedelta(seconds=2)
        task.date_started = date_started
        task.date_first_started = date_started
        task.due_date = date_started + timedelta(seconds=1)
        task.save(update_fields=[
            'due_date',
            'date_started',
            'date_first_started',
        ])
        template = overdue_workflow.template
        api_client.token_authenticate(user)

        # act
        response = api_client.get('/reports/dashboard/workflows/breakdown')

        # assert
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]['template_id'] == template.id
        assert response.data[0]['template_name'] == template.name
        assert response.data[0]['is_active'] == template.is_active
        assert response.data[0]['started'] == 1
        assert response.data[0]['completed'] == 0
        assert response.data[0]['in_progress'] == 1
        assert response.data[0]['overdue'] == 1

    def test_workflow_breakdown__overdue_workflow__ok(
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
        user = create_test_user(account=account, is_account_owner=False)
        overdue_workflow = create_test_workflow(user, tasks_count=1)
        overdue_workflow.date_created = timezone.now() - timedelta(minutes=5)
        overdue_workflow.due_date = timezone.now() - timedelta(minutes=1)
        overdue_workflow.save(update_fields=[
            'due_date',
            'date_created'
        ])
        template = overdue_workflow.template
        api_client.token_authenticate(user)

        # act
        response = api_client.get('/reports/dashboard/workflows/breakdown')

        # assert
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]['template_id'] == template.id
        assert response.data[0]['template_name'] == template.name
        assert response.data[0]['is_active'] == template.is_active
        assert response.data[0]['started'] == 1
        assert response.data[0]['completed'] == 0
        assert response.data[0]['in_progress'] == 1
        assert response.data[0]['overdue'] == 1

    def test_workflow_breakdown__now__overdue_task__ok(
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
        user = create_test_user(account=account, is_account_owner=False)
        overdue_workflow = create_test_workflow(user, tasks_count=1)
        task = overdue_workflow.current_task_instance
        date_started = timezone.now() - timedelta(seconds=2)
        task.date_started = date_started
        task.date_first_started = date_started
        task.due_date = date_started + timedelta(seconds=1)
        task.save(update_fields=[
            'due_date',
            'date_started',
            'date_first_started',
        ])
        template = overdue_workflow.template
        api_client.token_authenticate(user)

        # act
        response = api_client.get(
            '/reports/dashboard/workflows/breakdown',
            data={'now': True}
        )

        # assert
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]['is_active'] == template.is_active
        assert response.data[0]['template_id'] == template.id
        assert response.data[0]['template_name'] == template.name
        assert response.data[0]['started'] is None
        assert response.data[0]['completed'] is None
        assert response.data[0]['in_progress'] == 1
        assert response.data[0]['overdue'] == 1

    def test_workflow_breakdown__now__overdue_workflow__ok(
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
        user = create_test_user(account=account, is_account_owner=False)
        overdue_workflow = create_test_workflow(user, tasks_count=1)
        overdue_workflow.date_created = timezone.now() - timedelta(minutes=5)
        overdue_workflow.due_date = timezone.now() - timedelta(minutes=1)
        overdue_workflow.save(update_fields=[
            'due_date',
            'date_created'
        ])
        template = overdue_workflow.template
        api_client.token_authenticate(user)
        api_client.token_authenticate(user)

        # act
        response = api_client.get(
            '/reports/dashboard/workflows/breakdown',
            data={'now': True}
        )

        # assert
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]['is_active'] == template.is_active
        assert response.data[0]['template_id'] == template.id
        assert response.data[0]['template_name'] == template.name
        assert response.data[0]['started'] is None
        assert response.data[0]['completed'] is None
        assert response.data[0]['in_progress'] == 1
        assert response.data[0]['overdue'] == 1


class TestWorkflowBreakdownByTasks:

    def test_workflow_breakdown__ok(
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
        user = create_test_user(account=account, is_account_owner=False)
        first_template = create_test_template(user)
        second_template = create_test_template(user, is_active=True)
        account_service = AccountService(
            instance=user.account,
            user=user
        )
        account_service.update_active_templates()

        first_workflow = create_test_workflow(user, first_template)
        api_client.token_authenticate(user)
        api_client.post(
            f'/workflows/{first_workflow.id}/task-complete',
            data={'task_id': first_workflow.current_task_instance.id},
        )

        overdue_workflow = create_test_workflow(user, first_template)
        task = overdue_workflow.tasks.get(number=1)
        date_started = overdue_workflow.date_created - timedelta(days=2)
        task.date_started = date_started
        task.date_first_started = date_started
        task.due_date = date_started + timedelta(seconds=1)
        task.save(update_fields=[
            'due_date',
            'date_started',
            'date_first_started',
        ])
        overdue_workflow.date_created = date_started
        overdue_workflow.save(update_fields=['date_created'])
        api_client.post(
            f'/workflows/{overdue_workflow.id}/task-complete',
            data={'task_id': overdue_workflow.current_task_instance.id},
        )
        api_client.post(
            f'/workflows/{overdue_workflow.id}/task-complete',
            data={'task_id': overdue_workflow.tasks.get(number=2).id},
        )

        second_workflow = create_test_workflow(user, first_template)
        second_workflow.status = WorkflowStatus.RUNNING
        second_workflow.save(update_fields=['status'])

        fourth_workflow = create_test_workflow(user, second_template)
        fourth_workflow.status = WorkflowStatus.DONE
        fourth_workflow.date_completed = timezone.now()
        fourth_workflow.save(update_fields=['status', 'date_completed'])

        # act
        response = api_client.get(
            '/reports/dashboard/workflows/by-tasks',
            data={'template_id': first_template.id},
        )

        # assert
        assert response.status_code == 200
        assert len(response.data) == 3
        assert response.data[0]['id']
        assert response.data[0]['name']
        assert response.data[0]['number'] == 1
        assert response.data[0]['started'] == 2
        assert response.data[0]['completed'] == 2
        assert response.data[0]['in_progress'] == 3
        assert response.data[0]['overdue'] == 1
        assert response.data[1]['id']
        assert response.data[1]['name']
        assert response.data[1]['number'] == 2
        assert response.data[1]['started'] == 2
        assert response.data[1]['completed'] == 1
        assert response.data[1]['in_progress'] == 2
        assert response.data[1]['overdue'] == 0
        assert response.data[2]['id']
        assert response.data[2]['name']
        assert response.data[2]['number'] == 3
        assert response.data[2]['started'] == 1
        assert response.data[2]['completed'] == 0
        assert response.data[2]['in_progress'] == 1
        assert response.data[2]['overdue'] == 0

    def test_workflow_breakdown__user_is_not_template_owner__not_found(
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
        user = create_test_user(account=account, is_account_owner=False)
        first_template = create_test_template(user, is_active=True)
        create_test_workflow(user, first_template)
        another_user = create_test_user(
            account=user.account,
            email='test@test.test'
        )
        api_client.token_authenticate(another_user)

        # act
        response = api_client.get(
            '/reports/dashboard/workflows/by-tasks',
            data={'template_id': first_template.id},
        )

        # assert
        assert response.status_code == 404

    def test_workflow_breakdown__now__ok(
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
        user = create_test_user(account=account, is_account_owner=False)
        first_template = create_test_template(user)
        second_template = create_test_template(user, is_active=True)
        account_service = AccountService(
            instance=user.account,
            user=user
        )
        account_service.update_active_templates()

        first_workflow = create_test_workflow(user, first_template)
        api_client.token_authenticate(user)
        api_client.post(
            f'/workflows/{first_workflow.id}/task-complete',
            data={'task_id': first_workflow.current_task_instance.id},
        )

        second_workflow = create_test_workflow(user, first_template)
        api_client.post(
            f'/workflows/{second_workflow.id}/task-complete',
            data={'task_id': second_workflow.current_task_instance.id},
        )
        api_client.post(
            f'/workflows/{second_workflow.id}/task-complete',
            data={'task_id': second_workflow.tasks.get(number=2).id},
        )

        third_workflow = create_test_workflow(user, first_template)
        third_workflow.status = WorkflowStatus.RUNNING
        third_workflow.save(update_fields=['status'])

        fifth_workflow = create_test_workflow(user, second_template)
        fifth_workflow.status = WorkflowStatus.DONE
        fifth_workflow.date_completed = timezone.now()
        fifth_workflow.save(update_fields=['status', 'date_completed'])

        # act
        response = api_client.get(
            '/reports/dashboard/workflows/by-tasks',
            data={'template_id': first_template.id, 'now': True},
        )

        # assert
        assert response.status_code == 200
        assert len(response.data) == 3
        assert response.data[0]['id']
        assert response.data[0]['name']
        assert response.data[0]['number'] == 1
        assert response.data[0]['in_progress'] == 1
        assert response.data[0]['started'] is None
        assert response.data[0]['completed'] is None
        assert response.data[0]['overdue'] == 0
        assert response.data[1]['id']
        assert response.data[1]['name']
        assert response.data[1]['number'] == 2
        assert response.data[1]['in_progress'] == 1
        assert response.data[1]['started'] is None
        assert response.data[1]['completed'] is None
        assert response.data[1]['overdue'] == 0
        assert response.data[2]['id']
        assert response.data[2]['name']
        assert response.data[2]['number'] == 3
        assert response.data[2]['in_progress'] == 1
        assert response.data[2]['started'] is None
        assert response.data[2]['completed'] is None
        assert response.data[2]['overdue'] == 0

    @pytest.mark.parametrize('is_active', (True, False))
    def test_workflow_breakdown__without_workflows__ok(
        self,
        is_active,
        api_client
    ):

        # arrange
        account = create_test_account()
        create_test_user(
            email='owner@test.test',
            account=account,
            is_account_owner=True
        )
        user = create_test_user(account=account, is_account_owner=False)
        api_client.token_authenticate(user)
        template = create_test_template(
            user=user,
            is_active=is_active,
            tasks_count=1
        )
        template_task = template.tasks.get()

        # act
        response = api_client.get(
            '/reports/dashboard/workflows/by-tasks',
            data={'template_id': template.id},
        )

        # assert
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]['id'] == template_task.id
        assert response.data[0]['name'] == template_task.name
        assert response.data[0]['number'] == 1
        assert response.data[0]['started'] == 0
        assert response.data[0]['completed'] == 0
        assert response.data[0]['in_progress'] == 0
        assert response.data[0]['overdue'] == 0

    @pytest.mark.parametrize('is_active', (True, False))
    def test_workflow_breakdown__terminated_workflow__ok(
        self,
        mocker,
        is_active,
        api_client
    ):

        # arrange
        account = create_test_account()
        create_test_user(
            email='owner@test.test',
            account=account,
            is_account_owner=True
        )
        user = create_test_user(account=account, is_account_owner=False)
        api_client.token_authenticate(user)
        template = create_test_template(
            user=user,
            is_active=is_active,
            tasks_count=1
        )
        workflow = create_test_workflow(
            template=template,
            user=user,
            tasks_count=1
        )

        template_task = template.tasks.get()
        mocker.patch(
            'pneumatic_backend.analytics.services.AnalyticService.'
            'workflows_terminated'
        )

        # act
        response_close = api_client.delete(f'/workflows/{workflow.id}')

        # act
        response = api_client.get(
            '/reports/dashboard/workflows/by-tasks',
            data={'template_id': template.id},
        )

        # assert
        assert response_close.status_code == 204
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]['id'] == template_task.id
        assert response.data[0]['name'] == template_task.name
        assert response.data[0]['number'] == 1
        assert response.data[0]['started'] == 0
        assert response.data[0]['completed'] == 0
        assert response.data[0]['in_progress'] == 0
        assert response.data[0]['overdue'] == 0

    def test_workflow_breakdown__overdue_task__ok(
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
        user = create_test_user(account=account, is_account_owner=False)
        overdue_workflow = create_test_workflow(user, tasks_count=1)
        task = overdue_workflow.tasks.get(number=1)
        date_started = timezone.now() - timedelta(minutes=2)
        task.date_started = date_started
        task.date_first_started = date_started
        task.due_date = date_started + timedelta(minutes=1)
        task.save(update_fields=[
            'due_date',
            'date_started',
            'date_first_started',
        ])
        template = overdue_workflow.template
        template_task = template.tasks.first()
        api_client.token_authenticate(user)

        # act
        response = api_client.get(
            '/reports/dashboard/workflows/by-tasks',
            data={'template_id': template.id},
        )

        # assert
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]['id'] == template_task.id
        assert response.data[0]['name'] == template_task.name
        assert response.data[0]['number'] == 1
        assert response.data[0]['started'] == 1
        assert response.data[0]['completed'] == 0
        assert response.data[0]['in_progress'] == 1
        assert response.data[0]['overdue'] == 1

    def test_workflow_breakdown__overdue_workflow__ok(
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
        user = create_test_user(account=account, is_account_owner=False)
        overdue_workflow = create_test_workflow(user, tasks_count=1)
        overdue_workflow.date_created = timezone.now() - timedelta(minutes=5)
        overdue_workflow.due_date = timezone.now() - timedelta(minutes=1)
        overdue_workflow.save(update_fields=[
            'due_date',
            'date_created'
        ])
        template = overdue_workflow.template
        template_task = template.tasks.first()
        api_client.token_authenticate(user)

        # act
        response = api_client.get(
            '/reports/dashboard/workflows/by-tasks',
            data={'template_id': template.id},
        )

        # assert
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]['id'] == template_task.id
        assert response.data[0]['name'] == template_task.name
        assert response.data[0]['number'] == 1
        assert response.data[0]['started'] == 1
        assert response.data[0]['completed'] == 0
        assert response.data[0]['in_progress'] == 1
        assert response.data[0]['overdue'] == 1

    def test_workflow_breakdown__now__overdue_task__ok(
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
        user = create_test_user(account=account, is_account_owner=False)
        overdue_workflow = create_test_workflow(user, tasks_count=1)
        task = overdue_workflow.current_task_instance
        date_started = timezone.now() - timedelta(seconds=2)
        task.date_started = date_started
        task.date_first_started = date_started
        task.due_date = date_started + timedelta(seconds=1)
        task.save(update_fields=[
            'due_date',
            'date_started',
            'date_first_started',
        ])
        template = overdue_workflow.template
        template_task = template.tasks.first()
        api_client.token_authenticate(user)

        # act
        response = api_client.get(
            '/reports/dashboard/workflows/by-tasks',
            data={
                'template_id': template.id,
                'now': True
            },
        )

        # assert
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]['id'] == template_task.id
        assert response.data[0]['name'] == template_task.name
        assert response.data[0]['number'] == 1
        assert response.data[0]['in_progress'] == 1
        assert response.data[0]['started'] is None
        assert response.data[0]['completed'] is None
        assert response.data[0]['overdue'] == 1

    def test_workflow_breakdown__now__overdue_workflow__ok(
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
        user = create_test_user(account=account, is_account_owner=False)
        overdue_workflow = create_test_workflow(user, tasks_count=1)
        overdue_workflow.date_created = timezone.now() - timedelta(minutes=5)
        overdue_workflow.due_date = timezone.now() - timedelta(minutes=1)
        overdue_workflow.save(update_fields=[
            'due_date',
            'date_created'
        ])
        template = overdue_workflow.template
        template_task = template.tasks.first()
        api_client.token_authenticate(user)

        # act
        response = api_client.get(
            '/reports/dashboard/workflows/by-tasks',
            data={
                'template_id': template.id,
                'now': True
            },
        )

        # assert
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]['id'] == template_task.id
        assert response.data[0]['name'] == template_task.name
        assert response.data[0]['number'] == 1
        assert response.data[0]['in_progress'] == 1
        assert response.data[0]['started'] is None
        assert response.data[0]['completed'] is None
        assert response.data[0]['overdue'] == 1
