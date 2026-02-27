from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from src.processes.enums import (
    ViewerType,
    WorkflowStatus,
)
from src.processes.models.templates.owner import TemplateOwner
from src.processes.models.templates.viewer import TemplateViewer
from src.processes.models.workflows.workflow import Workflow
from src.processes.tests.fixtures import (
    create_invited_user,
    create_test_account,
    create_test_admin,
    create_test_owner,
    create_test_template,
    create_test_user,
    create_test_workflow,
)

UserModel = get_user_model()
pytestmark = pytest.mark.django_db


class TestDashboardOverview:

    def test_overview__ok(self, api_client):

        # arrange
        account = create_test_account()
        create_test_user(
            email='owner@test.test',
            account=account,
            is_account_owner=True,
        )
        user = create_test_user(account=account, is_account_owner=False)
        template_1 = create_test_template(user)
        template_2 = create_test_template(user, is_active=True)
        create_test_template(user, is_active=True)
        template_4 = create_test_template(user, is_active=True)
        create_test_template(user)

        workflow_1 = create_test_workflow(
            user=user,
            template=template_1,
            status=WorkflowStatus.DONE,
        )
        date_created = workflow_1.date_created - timedelta(days=2)
        workflow_1.date_created = date_created
        workflow_1.date_completed = timezone.now()
        workflow_1.save(update_fields=[
            'status',
            'date_completed',
            'date_created',
        ])

        overdue_workflow = create_test_workflow(user, template=template_1)
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
            'date_created',
        ])

        workflow_2 = create_test_workflow(user, template=template_1)
        workflow_2.status = WorkflowStatus.RUNNING
        workflow_2.save(update_fields=['status'])

        workflow_4 = create_test_workflow(user, template=template_2)
        workflow_4.status = WorkflowStatus.DONE
        workflow_4.date_completed = timezone.now()
        workflow_4.save(update_fields=['status', 'date_completed'])

        uncount_workflow = create_test_workflow(user, template=template_4)
        uncount_workflow.status = WorkflowStatus.DONE
        date_created = uncount_workflow.date_created - timedelta(days=2)
        uncount_workflow.date_created = date_created
        uncount_workflow.date_completed = timezone.now() - timedelta(days=2)
        uncount_workflow.save(update_fields=[
            'status',
            'date_completed',
            'date_created',
        ])

        seventh_workflow = create_test_workflow(user, template=template_4)
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

    def test_overview__user_is_template_owner_is_deleted__ok(self, api_client):

        # arrange
        user = create_test_user()
        template = create_test_template(user, tasks_count=1)
        TemplateOwner.objects.filter(user_id=user.id).delete()
        workflow_1 = create_test_workflow(user, template=template)
        workflow_1.status = WorkflowStatus.DONE
        date_created = workflow_1.date_created - timedelta(days=2)
        workflow_1.date_created = date_created
        workflow_1.date_completed = timezone.now()
        workflow_1.save(update_fields=[
            'status',
            'date_completed',
            'date_created',
        ])

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
        assert response.data['in_progress'] == 0
        assert response.data['overdue'] == 0

    def test_overview__different_user_statistic__correct_count(
        self,
        api_client,
    ):
        # arrange
        account = create_test_account()
        create_test_user(
            email='owner@test.test',
            account=account,
            is_account_owner=True,
        )
        user = create_test_user(account=account, is_account_owner=False)
        create_invited_user(user, 'test1@pneumatic.app')

        template_1 = create_test_template(user, is_active=True)
        template_2 = create_test_template(user)
        template_4 = create_test_template(user)
        create_test_template(user, is_active=True)
        create_test_template(user)

        workflow_1 = create_test_workflow(user, template=template_1)
        workflow_1.status = WorkflowStatus.DONE
        workflow_1.date_completed = timezone.now()
        workflow_1.save(update_fields=['status', 'date_completed'])

        workflow_2 = create_test_workflow(user, template=template_1)
        workflow_2.status = WorkflowStatus.RUNNING
        workflow_2.save(update_fields=['status'])

        workflow_4 = create_test_workflow(user, template=template_2)
        workflow_4.status = WorkflowStatus.DONE
        workflow_4.date_completed = timezone.now()
        workflow_4.save(update_fields=['status', 'date_completed'])

        sixth_workflow = create_test_workflow(user, template=template_4)
        sixth_workflow.status = WorkflowStatus.DONE
        sixth_workflow.date_completed = timezone.now()
        sixth_workflow.save(update_fields=['status', 'date_completed'])

        seventh_workflow = create_test_workflow(user, template=template_4)
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
        api_client,
    ):
        # arrange
        account = create_test_account()
        create_test_user(
            email='owner@test.test',
            account=account,
            is_account_owner=True,
        )
        user = create_test_user(account=account, is_account_owner=False)
        template_1 = create_test_template(user, is_active=True)
        template_2 = create_test_template(user, is_active=True)
        template_4 = create_test_template(user, is_active=True)

        workflow_1 = create_test_workflow(user, template=template_1)
        workflow_1.status = WorkflowStatus.RUNNING
        workflow_1.save(update_fields=['status'])

        workflow_2 = create_test_workflow(user, template=template_2)
        workflow_2.status = WorkflowStatus.DONE
        workflow_2.date_completed = timezone.now()
        workflow_2.save(update_fields=['status', 'date_completed'])

        workflow_4 = create_test_workflow(user, template=template_4)
        workflow_4.status = WorkflowStatus.DONE
        workflow_4.date_completed = timezone.now()
        workflow_4.save(update_fields=['status', 'date_completed'])

        workflow_5 = create_test_workflow(user, template=template_4)
        workflow_5.status = WorkflowStatus.DELAYED
        workflow_5.save(update_fields=['status'])

        api_client.token_authenticate(user)
        api_client.delete(f'/templates/{template_4.id}')

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
        api_client,
    ):
        # arrange
        account = create_test_account()
        create_test_user(
            email='owner@test.test',
            account=account,
            is_account_owner=True,
        )
        user = create_test_user(account=account, is_account_owner=False)
        template_1 = create_test_template(user)
        template_2 = create_test_template(user, is_active=True)
        template_4 = create_test_template(user, is_active=True)
        create_test_template(user)

        workflow_1 = create_test_workflow(user, template=template_1)
        workflow_1.status = WorkflowStatus.DONE
        date_created = workflow_1.date_created - timedelta(days=2)
        workflow_1.date_created = date_created
        workflow_1.date_completed = timezone.now()
        workflow_1.save(update_fields=[
            'status',
            'date_completed',
            'date_created',
        ])

        overdue_workflow = create_test_workflow(user, template=template_1)
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

        workflow_2 = create_test_workflow(user, template=template_1)
        workflow_2.status = WorkflowStatus.RUNNING
        workflow_2.save(update_fields=['status'])

        workflow_4 = create_test_workflow(user, template=template_2)
        workflow_4.status = WorkflowStatus.DONE
        workflow_4.date_completed = timezone.now()
        workflow_4.save(update_fields=['status', 'date_completed'])

        uncount_workflow = create_test_workflow(user, template=template_4)
        uncount_workflow.status = WorkflowStatus.DONE
        date_created = uncount_workflow.date_created - timedelta(days=2)
        uncount_workflow.date_created = date_created
        uncount_workflow.date_completed = timezone.now() - timedelta(days=2)
        uncount_workflow.save(update_fields=[
            'status',
            'date_completed',
            'date_created',
        ])

        seventh_workflow = create_test_workflow(user, template=template_4)
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
            is_account_owner=True,
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
            is_account_owner=True,
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
        api_client,
    ):
        # arrange
        account = create_test_account()
        create_test_user(
            email='owner@test.test',
            account=account,
            is_account_owner=True,
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
        api_client,
    ):
        # arrange
        account = create_test_account()
        create_test_user(
            email='owner@test.test',
            account=account,
            is_account_owner=True,
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
        mocker,
        api_client,
    ):
        # arrange
        mocker.patch(
            'src.processes.tasks.webhooks.'
            'send_task_completed_webhook.delay',
        )
        account = create_test_account()
        create_test_user(
            email='owner@test.test',
            account=account,
            is_account_owner=True,
        )
        user = create_test_user(account=account, is_account_owner=False)
        api_client.token_authenticate(user)

        workflow = create_test_workflow(user)
        task = workflow.tasks.get(number=1)
        r1 = api_client.post(
            f'/workflows/{workflow.id}/task-complete',
            data={'task_id': task.id},
        )
        task_2 = workflow.tasks.get(number=2)
        date_started = timezone.now() - timedelta(days=7)
        task_2.date_started = date_started
        task_2.date_first_started = date_started
        task_2.due_date = date_started + timedelta(hours=1)  # overdue
        task_2.save(update_fields=[
            'due_date',
            'date_started',
            'date_first_started',
        ])
        text_comment = 'text_comment'
        r2 = api_client.post(
            f'/v2/tasks/{task_2.id}/revert',
            data={
                'comment': text_comment,
            },
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
        assert response.status_code == 200
        assert response.data['started'] is None
        assert response.data['completed'] is None
        assert response.data['in_progress'] == 1
        assert response.data['overdue'] == 0


class TestDashboardOverviewTemplateOwnerViewerE2E:
    """E2E: overview/breakdown for owner/viewer, one or many templates."""

    def test_overview__with_date_range_params__returns_200(self, api_client):
        # arrange
        account = create_test_account()
        user = create_test_user(account=account, is_account_owner=True)
        create_test_template(user)
        api_client.token_authenticate(user)
        date_from = timezone.now() - timedelta(days=1)
        date_to = timezone.now() + timedelta(days=1)

        # act
        response = api_client.get(
            '/reports/dashboard/workflows/overview',
            data={
                'date_from_tsp': int(date_from.timestamp()),
                'date_to_tsp': int(date_to.timestamp()),
            },
        )

        # assert
        assert response.status_code == 200
        assert 'started' in response.data
        assert 'in_progress' in response.data
        assert 'completed' in response.data
        assert 'overdue' in response.data

    def test_overview__template_owner__one_template__workflows_counted__ok(
        self,
        api_client,
    ):
        # arrange: template owner; workflows started by same user (owner)
        account = create_test_account()
        create_test_user(
            email='owner@test.test',
            account=account,
            is_account_owner=True,
        )
        user = create_test_user(account=account, is_account_owner=False)
        template = create_test_template(user, is_active=True)
        create_test_workflow(user=user, template=template)
        create_test_workflow(user=user, template=template)
        create_test_workflow(user=user, template=template)
        api_client.token_authenticate(user)

        # act
        response = api_client.get('/reports/dashboard/workflows/overview')

        # assert
        assert response.status_code == 200
        assert response.data['started'] >= 3
        assert response.data['in_progress'] >= 3

    def test_overview__template_viewer_only__one_tpl__workflows_counted__ok(
        self,
        api_client,
    ):
        # arrange: viewer only (no workflow ownership); owner has workflows
        account = create_test_account()
        owner = create_test_user(account=account, email='owner@test.test')
        create_test_user(
            email='account_owner@test.test',
            account=account,
            is_account_owner=True,
        )
        template = create_test_template(owner, is_active=True)
        create_test_workflow(user=owner, template=template)
        create_test_workflow(user=owner, template=template)
        viewer = create_test_user(
            account=account,
            email='viewer@test.test',
            is_account_owner=False,
        )
        TemplateViewer.objects.create(
            template=template,
            type=ViewerType.USER,
            user=viewer,
            account=account,
        )
        api_client.token_authenticate(viewer)

        # act
        response = api_client.get('/reports/dashboard/workflows/overview')

        # assert
        assert response.status_code == 200
        assert response.data['started'] >= 2
        assert response.data['in_progress'] >= 2

    def test_overview__template_viewer__multi_templates__sees_accessible__ok(
        self,
        api_client,
    ):
        # arrange: viewer of one template; another template not accessible
        account = create_test_account()
        create_test_user(
            email='account_owner@test.test',
            account=account,
            is_account_owner=True,
        )
        owner = create_test_user(account=account, email='owner@test.test')
        template_visible = create_test_template(owner, is_active=True)
        template_hidden = create_test_template(owner, is_active=True)
        create_test_workflow(user=owner, template=template_visible)
        create_test_workflow(user=owner, template=template_hidden)
        viewer = create_test_user(
            account=account,
            email='viewer@test.test',
            is_account_owner=False,
        )
        TemplateViewer.objects.create(
            template=template_visible,
            type=ViewerType.USER,
            user=viewer,
            account=account,
        )
        api_client.token_authenticate(viewer)

        # act
        overview = api_client.get('/reports/dashboard/workflows/overview')
        breakdown = api_client.get('/reports/dashboard/workflows/breakdown')

        # assert
        assert overview.status_code == 200
        assert breakdown.status_code == 200
        assert len(breakdown.data) == 1
        assert breakdown.data[0]['template_id'] == template_visible.id
        assert overview.data['started'] >= 1
        assert overview.data['in_progress'] >= 1

    def test_overview__and_breakdown__counts_consistent__template_owner__ok(
        self,
        api_client,
    ):
        # arrange
        account = create_test_account()
        create_test_user(
            email='account_owner@test.test',
            account=account,
            is_account_owner=True,
        )
        user = create_test_user(account=account, is_account_owner=False)
        t1 = create_test_template(user, is_active=True)
        t2 = create_test_template(user, is_active=True)
        create_test_workflow(user=user, template=t1)
        create_test_workflow(user=user, template=t1)
        create_test_workflow(user=user, template=t2)
        api_client.token_authenticate(user)

        # act
        overview = api_client.get('/reports/dashboard/workflows/overview')
        breakdown = api_client.get('/reports/dashboard/workflows/breakdown')

        # assert
        assert overview.status_code == 200
        assert breakdown.status_code == 200
        sum_started = sum(b['started'] for b in breakdown.data)
        sum_in_progress = sum(b['in_progress'] for b in breakdown.data)
        sum_completed = sum(b['completed'] for b in breakdown.data)
        sum_overdue = sum(b['overdue'] for b in breakdown.data)
        assert overview.data['started'] == sum_started
        assert overview.data['in_progress'] == sum_in_progress
        assert overview.data['completed'] == sum_completed
        assert overview.data['overdue'] == sum_overdue

    def test_overview__and_breakdown__counts_consistent__template_viewer__ok(
        self,
        api_client,
    ):
        # arrange: viewer of one template, workflows owned by owner
        account = create_test_account()
        create_test_user(
            email='account_owner@test.test',
            account=account,
            is_account_owner=True,
        )
        owner = create_test_user(account=account, email='owner@test.test')
        template = create_test_template(owner, is_active=True)
        create_test_workflow(user=owner, template=template)
        create_test_workflow(user=owner, template=template)
        viewer = create_test_user(
            account=account,
            email='viewer@test.test',
            is_account_owner=False,
        )
        TemplateViewer.objects.create(
            template=template,
            type=ViewerType.USER,
            user=viewer,
            account=account,
        )
        api_client.token_authenticate(viewer)

        # act
        overview = api_client.get('/reports/dashboard/workflows/overview')
        breakdown = api_client.get('/reports/dashboard/workflows/breakdown')

        # assert
        assert overview.status_code == 200
        assert breakdown.status_code == 200
        assert len(breakdown.data) == 1
        sum_started = sum(b['started'] for b in breakdown.data)
        sum_in_progress = sum(b['in_progress'] for b in breakdown.data)
        sum_completed = sum(b['completed'] for b in breakdown.data)
        sum_overdue = sum(b['overdue'] for b in breakdown.data)
        assert overview.data['started'] == sum_started
        assert overview.data['in_progress'] == sum_in_progress
        assert overview.data['completed'] == sum_completed
        assert overview.data['overdue'] == sum_overdue


class TestDashboardWorkflowBreakdown:

    def test_workflow_breakdown__ok(
        self,
        api_client,
    ):
        # arrange
        account = create_test_account()
        create_test_user(
            email='owner@test.test',
            account=account,
            is_account_owner=True,
        )
        user = create_test_user(account=account, is_account_owner=False)
        template_1 = create_test_template(user)
        template_2 = create_test_template(user, is_active=True)
        template_3 = create_test_template(user, is_active=True)
        template_4 = create_test_template(user, is_active=True)
        draft_template = create_test_template(user)

        workflow_1 = create_test_workflow(user, template=template_1)
        workflow_1.status = WorkflowStatus.DONE
        date_created = workflow_1.date_created - timedelta(days=2)
        workflow_1.date_created = date_created
        workflow_1.date_completed = timezone.now()
        workflow_1.save(update_fields=[
            'status',
            'date_completed',
            'date_created',
        ])

        overdue_workflow = create_test_workflow(user, template=template_1)
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
            'date_created',
        ])

        workflow_2 = create_test_workflow(user, template=template_1)
        workflow_2.status = WorkflowStatus.RUNNING
        workflow_2.save(update_fields=['status'])

        not_overdue_workflow = create_test_workflow(
            user=user,
            template=template_1,
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

        workflow_4 = create_test_workflow(user, template=template_2)
        workflow_4.status = WorkflowStatus.DONE
        workflow_4.date_completed = timezone.now()
        workflow_4.save(update_fields=['status', 'date_completed'])

        uncount_workflow = create_test_workflow(user, template=template_4)
        uncount_workflow.status = WorkflowStatus.DONE
        date_created = uncount_workflow.date_created - timedelta(days=2)
        uncount_workflow.date_created = date_created
        uncount_workflow.date_completed = timezone.now() - timedelta(days=2)
        uncount_workflow.save(update_fields=[
            'status',
            'date_completed',
            'date_created',
        ])

        seventh_workflow = create_test_workflow(user, template=template_4)
        seventh_workflow.status = WorkflowStatus.DELAYED
        seventh_workflow.save(update_fields=['status'])

        api_client.token_authenticate(user)

        # act
        response = api_client.get('/reports/dashboard/workflows/breakdown')

        # assert
        assert response.status_code == 200
        assert len(response.data) == 5
        assert response.data[0]['template_id'] == template_1.id
        assert response.data[0]['template_name'] == template_1.name
        assert response.data[0]['is_active'] == template_1.is_active
        assert response.data[0]['started'] == 1
        assert response.data[0]['completed'] == 2
        assert response.data[0]['in_progress'] == 3
        assert response.data[0]['overdue'] == 1

        assert response.data[1]['template_id'] == template_2.id
        assert response.data[1]['template_name'] == template_2.name
        assert response.data[1]['is_active'] == template_2.is_active
        assert response.data[1]['started'] == 1
        assert response.data[1]['completed'] == 1
        assert response.data[1]['in_progress'] == 1
        assert response.data[1]['overdue'] == 0

        assert response.data[2]['template_id'] == template_4.id
        assert response.data[2]['template_name'] == template_4.name
        assert response.data[2]['is_active'] == template_4.is_active
        assert response.data[2]['started'] == 1
        assert response.data[2]['completed'] == 0
        assert response.data[2]['in_progress'] == 1
        assert response.data[2]['overdue'] == 0

        assert response.data[3]['template_id'] == template_3.id
        assert response.data[3]['template_name'] == template_3.name
        assert response.data[3]['is_active'] == template_3.is_active
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

    def test_workflow_breakdown__template_owners_is_deleted__ok(
        self,
        api_client,
    ):
        # arrange
        user = create_test_user(is_account_owner=False)
        template = create_test_template(user, tasks_count=1)
        TemplateOwner.objects.filter(user_id=user.id).delete()
        workflow_1 = create_test_workflow(user, template=template)
        workflow_1.status = WorkflowStatus.DONE
        date_created = workflow_1.date_created - timedelta(days=2)
        workflow_1.date_created = date_created
        workflow_1.date_completed = timezone.now()
        workflow_1.save(update_fields=[
            'status',
            'date_completed',
            'date_created',
        ])

        api_client.token_authenticate(user)

        # act
        response = api_client.get('/reports/dashboard/workflows/breakdown')

        # assert
        assert response.status_code == 200
        assert len(response.data) == 0

    def test_workflow_breakdown__legacy_template__not_count(
        self,
        api_client,
    ):
        # arrange
        account = create_test_account()
        create_test_user(
            email='owner@test.test',
            account=account,
            is_account_owner=True,
        )
        user = create_test_user(account=account, is_account_owner=False)
        template_1 = create_test_template(user)
        template_2 = create_test_template(user, is_active=True)

        workflow_1 = create_test_workflow(user, template=template_1)
        workflow_1.status = WorkflowStatus.DONE
        date_created = workflow_1.date_created - timedelta(days=2)
        workflow_1.date_created = date_created
        workflow_1.date_completed = timezone.now()
        workflow_1.save(update_fields=[
            'status',
            'date_completed',
            'date_created',
        ])

        overdue_workflow = create_test_workflow(user, template=template_1)
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
            'date_created',
        ])

        workflow_2 = create_test_workflow(user, template=template_1)
        workflow_2.status = WorkflowStatus.RUNNING
        workflow_2.save(update_fields=['status'])

        workflow_4 = create_test_workflow(user, template=template_2)
        workflow_4.status = WorkflowStatus.DONE
        workflow_4.date_completed = timezone.now()
        workflow_4.save(update_fields=['status', 'date_completed'])
        api_client.token_authenticate(user)
        api_client.delete(f'/templates/{template_2.id}')

        # act
        response = api_client.get('/reports/dashboard/workflows/breakdown')

        # assert
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]['template_id'] == template_1.id
        assert response.data[0]['template_name'] == template_1.name
        assert response.data[0]['is_active'] == template_1.is_active
        assert response.data[0]['started'] == 1
        assert response.data[0]['completed'] == 2
        assert response.data[0]['in_progress'] == 3
        assert response.data[0]['overdue'] == 1

    def test_workflow_breakdown__now__ok(
        self,
        api_client,
    ):

        # arrange
        account = create_test_account()
        create_test_user(
            email='owner@test.test',
            account=account,
            is_account_owner=True,
        )
        user = create_test_user(account=account, is_account_owner=False)
        template_1 = create_test_template(user, name='first')
        template_2 = create_test_template(
            user,
            is_active=True,
            name='second',
        )
        template_3 = create_test_template(
            user,
            is_active=True,
            name='third',
        )
        template_4 = create_test_template(
            user,
            is_active=True,
            name='fourth',
        )
        draft_template = create_test_template(
            user,
            is_active=False,
            name='draft',
        )

        workflow_1 = create_test_workflow(user, template=template_1)
        workflow_1.status = WorkflowStatus.DONE
        date_created = workflow_1.date_created - timedelta(days=2)
        workflow_1.date_created = date_created
        workflow_1.date_completed = timezone.now()
        workflow_1.save(update_fields=[
            'status',
            'date_completed',
            'date_created',
        ])

        overdue_workflow = create_test_workflow(user, template=template_1)
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
            'date_created',
        ])

        workflow_2 = create_test_workflow(user, template=template_1)
        workflow_2.status = WorkflowStatus.RUNNING
        workflow_2.save(update_fields=['status'])

        not_overdue_workflow = create_test_workflow(
            user=user,
            template=template_1,
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

        workflow_4 = create_test_workflow(user, template=template_2)
        workflow_4.status = WorkflowStatus.DONE
        workflow_4.date_completed = timezone.now()
        workflow_4.save(update_fields=['status', 'date_completed'])

        uncount_workflow = create_test_workflow(user, template=template_4)
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
        seventh_workflow = create_test_workflow(user, template=template_4)
        seventh_workflow.status = WorkflowStatus.DELAYED
        seventh_workflow.save(update_fields=['status'])

        api_client.token_authenticate(user)

        # act
        response = api_client.get(
            '/reports/dashboard/workflows/breakdown',
            data={'now': True},
        )

        # assert
        assert response.status_code == 200
        assert len(response.data) == 5
        assert response.data[0]['is_active'] == template_1.is_active
        assert response.data[0]['in_progress'] == 2
        assert response.data[0]['started'] is None
        assert response.data[0]['completed'] is None
        assert response.data[0]['overdue'] == 1
        assert response.data[0]['template_name'] == template_1.name
        assert response.data[0]['template_id'] == template_1.id

        assert response.data[1]['is_active'] == template_2.is_active
        assert response.data[1]['started'] is None
        assert response.data[1]['completed'] is None
        assert response.data[1]['in_progress'] == 0
        assert response.data[1]['overdue'] == 0
        assert response.data[1]['template_name'] == template_2.name
        assert response.data[1]['template_id'] == template_2.id

        assert response.data[2]['is_active'] == template_3.is_active
        assert response.data[2]['started'] is None
        assert response.data[2]['completed'] is None
        assert response.data[2]['in_progress'] == 0
        assert response.data[2]['overdue'] == 0
        assert response.data[2]['template_name'] == template_3.name
        assert response.data[2]['template_id'] == template_3.id

        assert response.data[3]['is_active'] == template_4.is_active
        assert response.data[3]['in_progress'] == 0
        assert response.data[3]['started'] is None
        assert response.data[3]['completed'] is None
        assert response.data[3]['overdue'] == 0
        assert response.data[3]['template_name'] == template_4.name
        assert response.data[3]['template_id'] == template_4.id

        assert response.data[4]['is_active'] is False
        assert response.data[4]['started'] is None
        assert response.data[4]['completed'] is None
        assert response.data[4]['in_progress'] == 0
        assert response.data[4]['overdue'] == 0
        assert response.data[4]['template_name'] == draft_template.name
        assert response.data[4]['template_id'] == draft_template.id

    def test_workflow_breakdown__now_template_owners_is_deleted__ok(
        self,
        api_client,
    ):
        # arrange
        user = create_test_user(is_account_owner=False)
        template = create_test_template(user, tasks_count=1)
        TemplateOwner.objects.filter(user_id=user.id).delete()
        workflow_1 = create_test_workflow(user, template=template)
        workflow_1.status = WorkflowStatus.DONE
        date_created = workflow_1.date_created - timedelta(days=2)
        workflow_1.date_created = date_created
        workflow_1.date_completed = timezone.now()
        workflow_1.save(update_fields=[
            'status',
            'date_completed',
            'date_created',
        ])

        api_client.token_authenticate(user)

        # act
        response = api_client.get(
            '/reports/dashboard/workflows/breakdown',
            data={'now': True},
        )

        # assert
        assert response.status_code == 200
        assert len(response.data) == 0

    def test_workflow_breakdown__draft_template_with_zero_workflows__ok(
        self,
        api_client,
    ):
        # arrange
        account = create_test_account()
        create_test_user(
            email='owner@test.test',
            account=account,
            is_account_owner=True,
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
        api_client,
    ):
        # arrange
        account = create_test_account()
        create_test_user(
            email='owner@test.test',
            account=account,
            is_account_owner=True,
        )
        user = create_test_user(account=account, is_account_owner=False)
        api_client.token_authenticate(user)
        date_now = timezone.now()
        date_from = (date_now - timedelta(hours=1))
        date_to = (date_now + timedelta(hours=1))
        draft_template = create_test_template(
            user=user,
            is_active=False,
            tasks_count=1,
        )
        active_template = create_test_template(
            user=user,
            is_active=True,
            tasks_count=1,
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
                'status',
            ],
        )

        # act
        response = api_client.get(
            path='/reports/dashboard/workflows/breakdown',
            data={
                'date_from_tsp': date_from.timestamp(),
                'date_to_tsp': date_to.timestamp(),
            },
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
        api_client,
    ):
        # arrange
        account = create_test_account()
        create_test_user(
            email='owner@test.test',
            account=account,
            is_account_owner=True,
        )
        user = create_test_user(account=account, is_account_owner=False)
        api_client.token_authenticate(user)
        date_now = timezone.now()
        date_from = (date_now - timedelta(hours=1))
        date_to = (date_now + timedelta(hours=1))
        draft_template = create_test_template(
            user=user,
            is_active=False,
            tasks_count=1,
        )
        active_template = create_test_template(
            user=user,
            is_active=True,
            tasks_count=1,
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
                'status',
            ],
        )

        # act
        response = api_client.get(
            path='/reports/dashboard/workflows/breakdown',
            data={
                'date_from_tsp': date_from.timestamp(),
                'date_to_tsp': date_to.timestamp(),
            },
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
        api_client,
    ):
        # arrange
        account = create_test_account()
        create_test_user(
            email='owner@test.test',
            account=account,
            is_account_owner=True,
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
        api_client,
    ):
        # arrange
        account = create_test_account()
        create_test_user(
            email='owner@test.test',
            account=account,
            is_account_owner=True,
        )
        user = create_test_user(account=account, is_account_owner=False)
        overdue_workflow = create_test_workflow(user, tasks_count=1)
        overdue_workflow.date_created = timezone.now() - timedelta(minutes=5)
        overdue_workflow.due_date = timezone.now() - timedelta(minutes=1)
        overdue_workflow.save(update_fields=[
            'due_date',
            'date_created',
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
        api_client,
    ):
        # arrange
        account = create_test_account()
        create_test_user(
            email='owner@test.test',
            account=account,
            is_account_owner=True,
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
        template = overdue_workflow.template
        api_client.token_authenticate(user)

        # act
        response = api_client.get(
            '/reports/dashboard/workflows/breakdown',
            data={'now': True},
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
        api_client,
    ):
        # arrange
        account = create_test_account()
        create_test_user(
            email='owner@test.test',
            account=account,
            is_account_owner=True,
        )
        user = create_test_user(account=account, is_account_owner=False)
        overdue_workflow = create_test_workflow(user, tasks_count=1)
        overdue_workflow.date_created = timezone.now() - timedelta(minutes=5)
        overdue_workflow.due_date = timezone.now() - timedelta(minutes=1)
        overdue_workflow.save(update_fields=[
            'due_date',
            'date_created',
        ])
        template = overdue_workflow.template
        api_client.token_authenticate(user)
        api_client.token_authenticate(user)

        # act
        response = api_client.get(
            '/reports/dashboard/workflows/breakdown',
            data={'now': True},
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
        mocker,
        api_client,
    ):
        # arrange
        mocker.patch(
            'src.processes.tasks.webhooks.'
            'send_task_completed_webhook.delay',
        )
        account = create_test_account()
        create_test_user(
            email='owner@test.test',
            account=account,
            is_account_owner=True,
        )
        user = create_test_user(account=account, is_account_owner=False)
        template_1 = create_test_template(user)
        template_2 = create_test_template(user, is_active=True)

        workflow_1 = create_test_workflow(user, template=template_1)
        task = workflow_1.tasks.get(number=1)
        api_client.token_authenticate(user)
        api_client.post(
            f'/workflows/{workflow_1.id}/task-complete',
            data={'task_id': task.id},
        )

        overdue_workflow = create_test_workflow(user, template=template_1)
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
            data={'task_id': task.id},
        )
        api_client.post(
            f'/workflows/{overdue_workflow.id}/task-complete',
            data={'task_id': overdue_workflow.tasks.get(number=2).id},
        )

        workflow_2 = create_test_workflow(user, template=template_1)
        workflow_2.status = WorkflowStatus.RUNNING
        workflow_2.save(update_fields=['status'])

        workflow_4 = create_test_workflow(user, template=template_2)
        workflow_4.status = WorkflowStatus.DONE
        workflow_4.date_completed = timezone.now()
        workflow_4.save(update_fields=['status', 'date_completed'])

        # act
        response = api_client.get(
            '/reports/dashboard/workflows/by-tasks',
            data={'template_id': template_1.id},
        )

        # assert
        assert response.status_code == 200
        assert len(response.data) == 3
        assert response.data[0]['id']
        assert response.data[0]['api_name']
        assert response.data[0]['name']
        assert response.data[0]['number'] == 1
        assert response.data[0]['started'] == 2
        assert response.data[0]['completed'] == 2
        assert response.data[0]['in_progress'] == 3
        assert response.data[0]['overdue'] == 1

        assert response.data[1]['id']
        assert response.data[1]['api_name']
        assert response.data[1]['name']
        assert response.data[1]['number'] == 2
        assert response.data[1]['started'] == 2
        assert response.data[1]['completed'] == 1
        assert response.data[1]['in_progress'] == 2
        assert response.data[1]['overdue'] == 0

        assert response.data[2]['id']
        assert response.data[2]['api_name']
        assert response.data[2]['name']
        assert response.data[2]['number'] == 3
        assert response.data[2]['started'] == 1
        assert response.data[2]['completed'] == 0
        assert response.data[2]['in_progress'] == 1
        assert response.data[2]['overdue'] == 0

    def test_workflow_breakdown__user_is_not_template_owner__not_found(
        self,
        api_client,
    ):

        # arrange
        account = create_test_account()
        create_test_user(
            email='owner@test.test',
            account=account,
            is_account_owner=True,
        )
        user = create_test_user(account=account, is_account_owner=False)
        template_1 = create_test_template(user, is_active=True)
        create_test_workflow(user, template=template_1)
        another_user = create_test_user(
            account=user.account,
            email='test@test.test',
        )
        api_client.token_authenticate(another_user)

        # act
        response = api_client.get(
            '/reports/dashboard/workflows/by-tasks',
            data={'template_id': template_1.id},
        )

        # assert
        assert response.status_code == 404

    def test_workflow_breakdown__now__ok(
        self,
        mocker,
        api_client,
    ):

        # arrange
        mocker.patch(
            'src.processes.tasks.webhooks.'
            'send_task_completed_webhook.delay',
        )
        account = create_test_account()
        create_test_owner(account=account)
        user = create_test_admin(account=account)
        template_1 = create_test_template(user)

        create_test_workflow(user, template=template_1)
        create_test_workflow(
            user,
            template=template_1,
            active_task_number=2,
        )
        create_test_workflow(
            user=user,
            template=template_1,
            active_task_number=3,
        )
        template_2 = create_test_template(user, is_active=True)
        create_test_workflow(
            user=user,
            template=template_2,
            status=WorkflowStatus.DONE,
        )
        api_client.token_authenticate(user)

        # act
        response = api_client.get(
            '/reports/dashboard/workflows/by-tasks',
            data={'template_id': template_1.id, 'now': True},
        )

        # assert
        assert response.status_code == 200
        assert len(response.data) == 3
        assert response.data[0]['id']
        assert response.data[0]['api_name']
        assert response.data[0]['name']
        assert response.data[0]['number'] == 1
        assert response.data[0]['in_progress'] == 1
        assert response.data[0]['started'] is None
        assert response.data[0]['completed'] is None
        assert response.data[0]['overdue'] == 0

        assert response.data[1]['id']
        assert response.data[1]['api_name']
        assert response.data[1]['name']
        assert response.data[1]['number'] == 2
        assert response.data[1]['in_progress'] == 1
        assert response.data[1]['started'] is None
        assert response.data[1]['completed'] is None
        assert response.data[1]['overdue'] == 0

        assert response.data[2]['id']
        assert response.data[2]['api_name']
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
        api_client,
    ):

        # arrange
        account = create_test_account()
        create_test_user(
            email='owner@test.test',
            account=account,
            is_account_owner=True,
        )
        user = create_test_user(account=account, is_account_owner=False)
        api_client.token_authenticate(user)
        template = create_test_template(
            user=user,
            is_active=is_active,
            tasks_count=1,
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
        assert response.data[0]['api_name'] == template_task.api_name
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
        api_client,
    ):

        # arrange
        account = create_test_account()
        create_test_user(
            email='owner@test.test',
            account=account,
            is_account_owner=True,
        )
        user = create_test_user(account=account, is_account_owner=False)
        api_client.token_authenticate(user)
        template = create_test_template(
            user=user,
            is_active=is_active,
            tasks_count=1,
        )
        workflow = create_test_workflow(
            template=template,
            user=user,
            tasks_count=1,
        )

        template_task = template.tasks.get()
        mocker.patch(
            'src.analysis.services.AnalyticService.'
            'workflows_terminated',
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
        assert response.data[0]['api_name'] == template_task.api_name
        assert response.data[0]['name'] == template_task.name
        assert response.data[0]['number'] == 1
        assert response.data[0]['started'] == 0
        assert response.data[0]['completed'] == 0
        assert response.data[0]['in_progress'] == 0
        assert response.data[0]['overdue'] == 0

    def test_workflow_breakdown__overdue_task__ok(
        self,
        api_client,
    ):
        # arrange
        account = create_test_account()
        create_test_user(
            email='owner@test.test',
            account=account,
            is_account_owner=True,
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
        assert response.data[0]['api_name'] == template_task.api_name
        assert response.data[0]['name'] == template_task.name
        assert response.data[0]['number'] == 1
        assert response.data[0]['started'] == 1
        assert response.data[0]['completed'] == 0
        assert response.data[0]['in_progress'] == 1
        assert response.data[0]['overdue'] == 1

    def test_workflow_breakdown__overdue_diff_workflow_tasks__ok(
        self,
        api_client,
    ):
        # arrange
        user = create_test_user()
        template = create_test_template(user=user, tasks_count=3)
        template_task_1 = template.tasks.get(number=1)
        template_task_2 = template.tasks.get(number=2)
        template_task_3 = template.tasks.get(number=3)
        date_started = timezone.now() - timedelta(hours=1)

        workflow_1 = create_test_workflow(user, template=template)
        task_1 = workflow_1.tasks.get(number=1)
        task_1.date_started = date_started
        task_1.due_date = date_started + timedelta(minutes=5)
        task_1.save(update_fields=['due_date', 'date_started'])

        workflow_2 = create_test_workflow(user, template=template)
        task_2 = workflow_2.tasks.get(number=2)
        task_2.date_started = date_started
        task_2.due_date = date_started + timedelta(minutes=5)
        task_2.save(update_fields=['due_date', 'date_started'])
        api_client.token_authenticate(user)

        # act
        response = api_client.get(
            '/reports/dashboard/workflows/by-tasks',
            data={'template_id': template.id},
        )

        # assert
        assert response.status_code == 200
        assert len(response.data) == 3
        assert response.data[0]['id'] == template_task_1.id
        assert response.data[0]['api_name'] == template_task_1.api_name
        assert response.data[0]['number'] == 1
        assert response.data[0]['overdue'] == 1
        assert response.data[1]['id'] == template_task_2.id
        assert response.data[1]['api_name'] == template_task_2.api_name
        assert response.data[1]['number'] == 2
        assert response.data[1]['overdue'] == 1
        assert response.data[2]['id'] == template_task_3.id
        assert response.data[2]['api_name'] == template_task_3.api_name
        assert response.data[2]['number'] == 3
        assert response.data[2]['overdue'] == 0

    def test_workflow_breakdown__in_progress__ok(
        self,
        mocker,
        api_client,
    ):

        """ Bug case when template task api name is same
            in different templates """

        # arrange
        mocker.patch(
            'src.processes.tasks.webhooks.'
            'send_task_completed_webhook.delay',
        )
        account = create_test_account()
        create_test_user(
            email='owner@test.test',
            account=account,
            is_account_owner=True,
        )
        user = create_test_user(account=account, is_account_owner=False)
        template = create_test_template(user, tasks_count=1)
        task = template.tasks.first()
        template_2 = create_test_template(user, tasks_count=1)
        task_2 = template_2.tasks.first()
        task_2.api_name = task.api_name
        task_2.save()
        create_test_workflow(user, template=template)
        create_test_workflow(user, template=template_2)
        api_client.token_authenticate(user)
        date_from = template.date_created - timedelta(hours=1)
        date_to = template.date_created + timedelta(hours=1)

        # act
        response = api_client.get(
            '/reports/dashboard/workflows/by-tasks',
            data={
                'template_id': template.id,
                'date_from_tsp': date_from.timestamp(),
                'date_to_tsp': date_to.timestamp(),
            },
        )

        # assert
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]['id']
        assert response.data[0]['api_name']
        assert response.data[0]['name']
        assert response.data[0]['number'] == 1
        assert response.data[0]['started'] == 1
        assert response.data[0]['completed'] == 0
        assert response.data[0]['in_progress'] == 1
        assert response.data[0]['overdue'] == 0

    def test_workflow_breakdown__now__overdue_task__ok(
        self,
        api_client,
    ):

        # arrange
        account = create_test_account()
        create_test_user(
            email='owner@test.test',
            account=account,
            is_account_owner=True,
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
        template = overdue_workflow.template
        template_task = template.tasks.first()
        api_client.token_authenticate(user)

        # act
        response = api_client.get(
            '/reports/dashboard/workflows/by-tasks',
            data={
                'template_id': template.id,
                'now': True,
            },
        )

        # assert
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]['id'] == template_task.id
        assert response.data[0]['name'] == template_task.name
        assert response.data[0]['api_name'] == template_task.api_name
        assert response.data[0]['number'] == 1
        assert response.data[0]['in_progress'] == 1
        assert response.data[0]['started'] is None
        assert response.data[0]['completed'] is None
        assert response.data[0]['overdue'] == 1

    def test_workflow_breakdown__now__overdue_diff_workflow_tasks__ok(
        self,
        api_client,
    ):
        # arrange
        user = create_test_user()
        template = create_test_template(user=user, tasks_count=3)
        template_task_1 = template.tasks.get(number=1)
        template_task_2 = template.tasks.get(number=2)
        template_task_3 = template.tasks.get(number=3)
        date_started = timezone.now() - timedelta(hours=1)

        workflow_1 = create_test_workflow(user, template=template)
        task_1 = workflow_1.tasks.get(number=1)
        task_1.date_started = date_started
        task_1.due_date = date_started + timedelta(minutes=5)
        task_1.save(update_fields=['due_date', 'date_started'])

        workflow_2 = create_test_workflow(
            user=user,
            template=template,
            active_task_number=2,
        )
        task_2 = workflow_2.tasks.get(number=2)
        task_2.date_started = date_started
        task_2.due_date = date_started + timedelta(minutes=5)
        task_2.save(update_fields=['due_date', 'date_started'])
        api_client.token_authenticate(user)

        # act
        response = api_client.get(
            '/reports/dashboard/workflows/by-tasks',
            data={
                'template_id': template.id,
                'now': True,
            },
        )

        # assert
        assert response.status_code == 200
        assert len(response.data) == 3
        assert response.data[0]['id'] == template_task_1.id
        assert response.data[0]['api_name'] == template_task_1.api_name
        assert response.data[0]['number'] == 1
        assert response.data[0]['overdue'] == 1

        assert response.data[1]['id'] == template_task_2.id
        assert response.data[1]['api_name'] == template_task_2.api_name
        assert response.data[1]['number'] == 2
        assert response.data[1]['overdue'] == 1

        assert response.data[2]['id'] == template_task_3.id
        assert response.data[2]['api_name'] == template_task_3.api_name
        assert response.data[2]['number'] == 3
        assert response.data[2]['overdue'] == 0

    def test_workflow_breakdown__now__overdue_workflow__ok(
        self,
        api_client,
    ):

        # arrange
        user = create_test_user()
        template = create_test_template(user=user, tasks_count=2)
        template_task_1 = template.tasks.get(number=1)
        template_task_2 = template.tasks.get(number=2)
        date_created = timezone.now() - timedelta(hours=1)

        workflow = create_test_workflow(
            user=user,
            template=template,
            active_task_number=2,
        )
        workflow.date_created = date_created
        workflow.due_date = date_created + timedelta(minutes=5)
        workflow.save(
            update_fields=['due_date', 'date_created'],
        )
        api_client.token_authenticate(user)

        # act
        response = api_client.get(
            '/reports/dashboard/workflows/by-tasks',
            data={
                'template_id': template.id,
                'now': True,
            },
        )

        # assert
        assert response.status_code == 200
        assert len(response.data) == 2
        assert response.data[0]['id'] == template_task_1.id
        assert response.data[0]['api_name'] == template_task_1.api_name
        assert response.data[0]['name'] == template_task_1.name
        assert response.data[0]['number'] == 1
        assert response.data[0]['in_progress'] == 0
        assert response.data[0]['started'] is None
        assert response.data[0]['completed'] is None
        assert response.data[0]['overdue'] == 0

        assert response.data[1]['id'] == template_task_2.id
        assert response.data[1]['api_name'] == template_task_2.api_name
        assert response.data[1]['name'] == template_task_2.name
        assert response.data[1]['number'] == 2
        assert response.data[1]['in_progress'] == 1
        assert response.data[1]['started'] is None
        assert response.data[1]['completed'] is None
        assert response.data[1]['overdue'] == 1

    def test_workflow_breakdown__now__in_progress__ok(
        self,
        mocker,
        api_client,
    ):

        """ Bug case when template task api name is same
            in different templates """

        # arrange
        mocker.patch(
            'src.processes.tasks.webhooks.'
            'send_task_completed_webhook.delay',
        )
        account = create_test_account()
        create_test_user(
            email='owner@test.test',
            account=account,
            is_account_owner=True,
        )
        user = create_test_user(account=account, is_account_owner=False)
        template = create_test_template(user, tasks_count=1)
        task = template.tasks.first()
        template_2 = create_test_template(user, tasks_count=1)
        task_2 = template_2.tasks.first()
        task_2.api_name = task.api_name
        task_2.save()
        create_test_workflow(user, template=template)
        create_test_workflow(user, template=template_2)
        api_client.token_authenticate(user)

        # act
        response = api_client.get(
            '/reports/dashboard/workflows/by-tasks',
            data={
                'template_id': template.id,
                'now': True,
            },
        )

        # assert
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]['id']
        assert response.data[0]['api_name']
        assert response.data[0]['name']
        assert response.data[0]['number'] == 1
        assert response.data[0]['started'] is None
        assert response.data[0]['completed'] is None
        assert response.data[0]['in_progress'] == 1
        assert response.data[0]['overdue'] == 0


class TestOverviewQueryAnalysis:
    """Additional tests for OverviewQuery and OverviewNowQuery analysis."""

    def test_overview_query__date_range_filtering__correct_counts(
        self,
        api_client,
    ):
        """Test correct date range filtering in OverviewQuery."""

        # arrange
        account = create_test_account()
        user = create_test_user(account=account, is_account_owner=True)
        template = create_test_template(user)

        # Workflow created 5 days ago and completed 3 days ago
        old_workflow = create_test_workflow(user, template=template)
        old_date_created = timezone.now() - timedelta(days=5)
        old_date_completed = timezone.now() - timedelta(days=3)
        old_workflow.date_created = old_date_created
        old_workflow.date_completed = old_date_completed
        old_workflow.status = WorkflowStatus.DONE
        old_workflow.save(update_fields=[
            'date_created',
            'date_completed',
            'status',
        ])

        # Workflow created yesterday and completed today
        recent_workflow = create_test_workflow(user, template=template)
        recent_date_created = timezone.now() - timedelta(days=1)
        recent_date_completed = timezone.now()
        recent_workflow.date_created = recent_date_created
        recent_workflow.date_completed = recent_date_completed
        recent_workflow.status = WorkflowStatus.DONE
        recent_workflow.save(update_fields=[
            'date_created',
            'date_completed',
            'status',
        ])

        # Workflow in progress (created 2 days ago)
        in_progress_workflow = create_test_workflow(user, template=template)
        in_progress_date_created = timezone.now() - timedelta(days=2)
        in_progress_workflow.date_created = in_progress_date_created
        in_progress_workflow.status = WorkflowStatus.RUNNING
        in_progress_workflow.save(update_fields=[
            'date_created',
            'status',
        ])

        api_client.token_authenticate(user)

        # act - request for last 2 days
        date_from = timezone.now() - timedelta(days=2)
        # Add hour to capture completed
        date_to = timezone.now() + timedelta(hours=1)
        response = api_client.get(
            '/reports/dashboard/workflows/overview',
            data={
                'date_from_tsp': int(date_from.timestamp()),
                'date_to_tsp': int(date_to.timestamp()),
            },
        )

        # assert
        assert response.status_code == 200
        # Should count: started=2 (both in range), completed=1,
        # in_progress=2, overdue=0
        assert response.data['started'] == 2
        assert response.data['completed'] == 1
        assert response.data['in_progress'] == 2
        assert response.data['overdue'] == 0

    def test_overview_now_query__only_running_workflows__correct_counts(
        self,
        api_client,
    ):
        """Test OverviewNowQuery - counts only RUNNING workflows."""

        # arrange
        account = create_test_account()
        user = create_test_user(account=account, is_account_owner=True)
        template = create_test_template(user)

        # Completed workflow (should not be counted)
        completed_workflow = create_test_workflow(user, template=template)
        completed_workflow.status = WorkflowStatus.DONE
        completed_workflow.date_completed = timezone.now()
        completed_workflow.save(update_fields=['status', 'date_completed'])

        # Delayed workflow (should not be counted in now)
        delayed_workflow = create_test_workflow(user, template=template)
        delayed_workflow.status = WorkflowStatus.DELAYED
        delayed_workflow.save(update_fields=['status'])

        # Active workflow (should be counted)
        running_workflow = create_test_workflow(user, template=template)
        running_workflow.status = WorkflowStatus.RUNNING
        running_workflow.save(update_fields=['status'])

        # Active overdue workflow
        overdue_workflow = create_test_workflow(user, template=template)
        overdue_workflow.status = WorkflowStatus.RUNNING
        overdue_workflow.save(update_fields=['status'])

        # Make task overdue
        task = overdue_workflow.tasks.first()
        past_time = timezone.now() - timedelta(hours=1)
        task.date_started = past_time
        task.due_date = past_time + timedelta(minutes=30)
        task.save(update_fields=['date_started', 'due_date'])

        api_client.token_authenticate(user)

        # act
        response = api_client.get(
            '/reports/dashboard/workflows/overview',
            data={'now': True},
        )

        # assert
        assert response.status_code == 200
        # OverviewNowQuery returns NULL for started and completed
        assert response.data['started'] is None
        assert response.data['completed'] is None
        # Should be 2 active workflows (running + overdue)
        assert response.data['in_progress'] == 2
        # One overdue
        assert response.data['overdue'] == 1

    def test_overview_query__template_viewer_access__sees_only_accessible(
        self,
        api_client,
    ):
        """Test template viewer access - sees only accessible templates."""

        # arrange
        account = create_test_account()
        owner = create_test_user(
            account=account,
            is_account_owner=True,
            email='owner@test.test',
        )
        viewer = create_test_user(
            account=account,
            is_account_owner=False,
            email='viewer@test.test',
        )

        # Template viewer has access to
        accessible_template = create_test_template(owner)
        TemplateViewer.objects.create(
            template=accessible_template,
            user=viewer,
            type=ViewerType.USER,
            account_id=account.id,
        )

        # Template viewer does NOT have access to
        inaccessible_template = create_test_template(owner)

        # Workflow for accessible template
        accessible_workflow = create_test_workflow(
            owner,
            template=accessible_template,
        )
        accessible_workflow.status = WorkflowStatus.RUNNING
        accessible_workflow.save(update_fields=['status'])

        # Workflow for inaccessible template
        inaccessible_workflow = create_test_workflow(
            owner,
            template=inaccessible_template,
        )
        inaccessible_workflow.status = WorkflowStatus.RUNNING
        inaccessible_workflow.save(update_fields=['status'])

        api_client.token_authenticate(viewer)

        # act
        response = api_client.get(
            '/reports/dashboard/workflows/overview',
            data={'now': True},
        )

        # assert
        assert response.status_code == 200
        # Viewer should see only workflow of accessible template
        assert response.data['in_progress'] == 1
        assert response.data['overdue'] == 0

    def test_overview_query__overdue_calculation__task_and_workflow_due_dates(
        self,
        api_client,
    ):
        """Overdue calculation - by task and workflow due_date."""

        # arrange
        account = create_test_account()
        user = create_test_user(account=account, is_account_owner=True)
        template = create_test_template(user, tasks_count=2)

        # Workflow with overdue task
        workflow_with_overdue_task = create_test_workflow(
            user,
            template=template,
        )
        task = workflow_with_overdue_task.tasks.first()
        past_time = timezone.now() - timedelta(hours=2)
        task.date_started = past_time
        task.due_date = past_time + timedelta(hours=1)  # Overdue by 1 hour
        task.save(update_fields=['date_started', 'due_date'])

        # Workflow with overdue workflow due_date
        workflow_with_overdue_due_date = create_test_workflow(
            user,
            template=template,
        )
        workflow_due_date = timezone.now() - timedelta(hours=1)
        workflow_with_overdue_due_date.due_date = workflow_due_date
        workflow_with_overdue_due_date.save(update_fields=['due_date'])

        # Normal workflow without overdue
        create_test_workflow(user, template=template)

        api_client.token_authenticate(user)

        # act
        response = api_client.get(
            '/reports/dashboard/workflows/overview',
            data={'now': True},
        )

        # assert
        assert response.status_code == 200
        assert response.data['in_progress'] == 3
        # Should be 2 overdue workflows
        assert response.data['overdue'] == 2

    def test_overview_query__legacy_template_access__workflow_starter_access(
        self,
        api_client,
    ):
        """Test legacy template access via workflow_starter_id."""

        # arrange
        account = create_test_account()
        owner = create_test_user(
            account=account,
            is_account_owner=True,
            email='owner@legacy.test',
        )
        starter = create_test_user(
            account=account,
            is_account_owner=False,
            email='starter@legacy.test',
        )
        template = create_test_template(owner)

        # Create legacy workflow where starter is initiator
        legacy_workflow = create_test_workflow(owner, template=template)
        legacy_workflow.is_legacy_template = True
        legacy_workflow.workflow_starter_id = starter.id
        legacy_workflow.status = WorkflowStatus.RUNNING
        legacy_workflow.save(update_fields=[
            'is_legacy_template',
            'workflow_starter_id',
            'status',
        ])

        # Normal workflow (not legacy) - starter should not see it
        normal_workflow = create_test_workflow(owner, template=template)
        normal_workflow.status = WorkflowStatus.RUNNING
        normal_workflow.save(update_fields=['status'])

        api_client.token_authenticate(starter)

        # act
        response = api_client.get(
            '/reports/dashboard/workflows/overview',
            data={'now': True},
        )

        # assert
        assert response.status_code == 200
        # Starter should see only legacy workflow
        assert response.data['in_progress'] == 1
        assert response.data['overdue'] == 0

    def test_overview_query__sql_injection_protection__safe_parameters(
        self,
        api_client,
    ):
        """Test SQL injection protection via query parameters."""

        # arrange
        account = create_test_account()
        user = create_test_user(account=account, is_account_owner=True)
        template = create_test_template(user)
        create_test_workflow(user, template=template)

        api_client.token_authenticate(user)

        # act - SQL injection attempt via timestamp parameters
        malicious_timestamp = "1234567890; DROP TABLE processes_workflow; --"
        response = api_client.get(
            '/reports/dashboard/workflows/overview',
            data={
                'date_from_tsp': malicious_timestamp,
                'date_to_tsp': int(timezone.now().timestamp()),
            },
        )

        # assert - validation error expected, not SQL error
        assert response.status_code == 400
        # Verify table still exists
        assert Workflow.objects.count() == 1

    def test_overview_query__empty_account__zero_counts(
        self,
        api_client,
    ):
        """Test empty account - all counters should be 0."""

        # arrange
        account = create_test_account()
        user = create_test_user(account=account, is_account_owner=True)
        # Do not create any templates or workflows

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
        assert response.data['in_progress'] == 0
        assert response.data['overdue'] == 0

    def test_overview_query__deleted_templates_excluded__correct_counts(
        self,
        api_client,
    ):
        """Test excluded deleted templates from count."""

        # arrange
        account = create_test_account()
        user = create_test_user(account=account, is_account_owner=True)

        # Active template
        active_template = create_test_template(user)
        active_workflow = create_test_workflow(user, template=active_template)
        active_workflow.status = WorkflowStatus.RUNNING
        active_workflow.save(update_fields=['status'])

        # Deleted template
        deleted_template = create_test_template(user)
        deleted_template.is_deleted = True
        deleted_template.save(update_fields=['is_deleted'])
        workflow_deleted_tpl = create_test_workflow(
            user, template=deleted_template,
        )
        workflow_deleted_tpl.status = WorkflowStatus.RUNNING
        workflow_deleted_tpl.save(update_fields=['status'])

        api_client.token_authenticate(user)

        # act
        response = api_client.get(
            '/reports/dashboard/workflows/overview',
            data={'now': True},
        )

        # assert
        assert response.status_code == 200
        # Should count only workflow of active template
        assert response.data['in_progress'] == 1
        assert response.data['overdue'] == 0
