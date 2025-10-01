import pytest
from datetime import timedelta, datetime, time
from django.contrib.auth import get_user_model
from django.utils import timezone
from src.processes.models import (
    TaskPerformer,
    FieldTemplate,
    ConditionTemplate,
    RuleTemplate,
    PredicateTemplate
)
from src.processes.tests.fixtures import (
    create_test_template,
    create_test_workflow,
    create_test_account,
    create_test_owner,
    create_test_admin,
    create_test_group
)
from src.processes.enums import (
    WorkflowStatus,
    PredicateOperator,
    TaskStatus,
    ConditionAction,
    PerformerType
)
from src.processes.enums import (
    FieldType,
    DirectlyStatus
)

UserModel = get_user_model()
pytestmark = pytest.mark.django_db


class TestDashboardMyTasksOverview:

    def test_my_tasks__started__ok(
        self,
        mocker,
        api_client
    ):
        # arrange
        mocker.patch(
            'src.processes.tasks.webhooks.'
            'send_task_completed_webhook.delay'
        )
        account = create_test_account()
        user = create_test_owner(account=account)
        workflow = create_test_workflow(
            user=user,
            active_task_number=2,
            tasks_count=3
        )
        task_1 = workflow.tasks.get(number=1)
        task_1.date_first_started = timezone.now() - timedelta(minutes=1)
        task_1.save()

        # Not found task
        task_2 = workflow.tasks.get(number=2)
        task_2.date_first_started = timezone.now() + timedelta(hours=1)
        task_2.save()

        api_client.token_authenticate(user)

        # act
        response = api_client.get('/reports/dashboard/tasks/overview')

        # assert
        assert response.status_code == 200
        assert response.data['started'] == 1

    def test_my_tasks_started__performer_user_and_group__ok(
        self,
        mocker,
        api_client
    ):
        # arrange
        mocker.patch(
            'src.processes.tasks.webhooks.'
            'send_task_completed_webhook.delay'
        )
        account = create_test_account()
        user = create_test_owner(account=account)
        group = create_test_group(account, users=[user])
        group2 = create_test_group(account, users=[user])
        workflow = create_test_workflow(user=user, tasks_count=1)
        task_1 = workflow.tasks.get(number=1)
        TaskPerformer.objects.create(
            task_id=task_1.id,
            type=PerformerType.GROUP,
            group_id=group.id,
        )
        TaskPerformer.objects.create(
            task_id=task_1.id,
            type=PerformerType.GROUP,
            group_id=group2.id,
        )
        task_1.save()

        api_client.token_authenticate(user)

        # act
        response = api_client.get('/reports/dashboard/tasks/overview')

        # assert
        assert response.status_code == 200
        assert response.data['started'] == 1

    def test_my_tasks_in_progress__performer_user_and_group__ok(
        self,
        mocker,
        api_client
    ):
        # arrange
        mocker.patch(
            'src.processes.tasks.webhooks.'
            'send_task_completed_webhook.delay'
        )
        account = create_test_account()
        user = create_test_owner(account=account)
        group = create_test_group(account, users=[user])
        group2 = create_test_group(account, users=[user])
        workflow = create_test_workflow(user=user, tasks_count=1)
        task_1 = workflow.tasks.get(number=1)
        task_1.date_started = timezone.now() - timedelta(hours=1)
        task_1.status = TaskStatus.ACTIVE
        TaskPerformer.objects.create(
            task_id=task_1.id,
            type=PerformerType.GROUP,
            group_id=group.id,
        )
        TaskPerformer.objects.create(
            task_id=task_1.id,
            type=PerformerType.GROUP,
            group_id=group2.id,
        )
        task_1.save()

        api_client.token_authenticate(user)

        # act
        response = api_client.get('/reports/dashboard/tasks/overview')

        # assert
        assert response.status_code == 200
        assert response.data['in_progress'] == 1

    def test_my_tasks_completed__performer_user_and_group__ok(
        self,
        mocker,
        api_client
    ):
        # arrange
        mocker.patch(
            'src.processes.tasks.webhooks.'
            'send_task_completed_webhook.delay'
        )
        account = create_test_account()
        user = create_test_owner(account=account)
        group = create_test_group(account, users=[user])
        group2 = create_test_group(account, users=[user])
        workflow = create_test_workflow(user=user, tasks_count=1)
        task_1 = workflow.tasks.get(number=1)
        task_1.date_started = timezone.now() - timedelta(hours=2)
        task_1.date_completed = timezone.now() - timedelta(hours=1)
        task_1.status = TaskStatus.COMPLETED
        TaskPerformer.objects.create(
            task_id=task_1.id,
            type=PerformerType.GROUP,
            group_id=group.id,
        )
        TaskPerformer.objects.create(
            task_id=task_1.id,
            type=PerformerType.GROUP,
            group_id=group2.id,
        )
        task_1.save()

        api_client.token_authenticate(user)

        # act
        response = api_client.get('/reports/dashboard/tasks/overview')

        # assert
        assert response.status_code == 200
        assert response.data['completed'] == 1

    def test_my_tasks_overdue__performer_user_and_group__ok(
        self,
        mocker,
        api_client
    ):
        # arrange
        mocker.patch(
            'src.processes.tasks.webhooks.'
            'send_task_completed_webhook.delay'
        )
        account = create_test_account()
        user = create_test_owner(account=account)
        group = create_test_group(account, users=[user])
        group2 = create_test_group(account, users=[user])
        workflow = create_test_workflow(user=user, tasks_count=1)
        task_1 = workflow.tasks.get(number=1)
        task_1.date_started = timezone.now() - timedelta(hours=2)
        task_1.due_date = timezone.now() - timedelta(hours=1)
        task_1.status = TaskStatus.ACTIVE
        TaskPerformer.objects.create(
            task_id=task_1.id,
            type=PerformerType.GROUP,
            group_id=group.id,
        )
        TaskPerformer.objects.create(
            task_id=task_1.id,
            type=PerformerType.GROUP,
            group_id=group2.id,
        )
        task_1.save()

        api_client.token_authenticate(user)

        # act
        response = api_client.get('/reports/dashboard/tasks/overview')

        # assert
        assert response.status_code == 200
        assert response.data['overdue'] == 1

    @pytest.mark.parametrize(
        'task_status',
        (
            TaskStatus.ACTIVE,
            TaskStatus.DELAYED,
        )
    )
    def test_my_tasks__in_progress__allowed_task_status__ok(
        self,
        mocker,
        api_client,
        task_status
    ):
        # arrange
        mocker.patch(
            'src.processes.tasks.webhooks.'
            'send_task_completed_webhook.delay'
        )
        account = create_test_account()
        user = create_test_owner(account=account)
        workflow = create_test_workflow(
            user=user,
            tasks_count=2
        )
        task_1 = workflow.tasks.get(number=1)
        task_1.date_started = timezone.now() - timedelta(hours=1)
        task_1.status = task_status
        task_1.save()

        api_client.token_authenticate(user)

        # act
        response = api_client.get('/reports/dashboard/tasks/overview')

        # assert
        assert response.status_code == 200
        assert response.data['in_progress'] == 1

    @pytest.mark.parametrize(
        'task_status',
        (
            TaskStatus.PENDING,
            TaskStatus.SKIPPED
        )
    )
    def test_my_tasks__in_progress__not_allowed_task_status__ok(
        self,
        mocker,
        api_client,
        task_status
    ):

        # arrange
        mocker.patch(
            'src.processes.tasks.webhooks.'
            'send_task_completed_webhook.delay'
        )
        account = create_test_account()
        user = create_test_owner(account=account)
        workflow = create_test_workflow(
            user=user,
            tasks_count=2
        )
        task_1 = workflow.tasks.get(number=1)
        task_1.date_started = timezone.now() - timedelta(hours=1)
        task_1.status = task_status
        task_1.save()

        api_client.token_authenticate(user)

        # act
        response = api_client.get('/reports/dashboard/tasks/overview')

        # assert
        assert response.status_code == 200
        assert response.data['in_progress'] == 0

    def test_my_tasks__in_progress__task_completed_today__ok(
        self,
        mocker,
        api_client,
    ):
        # arrange
        mocker.patch(
            'src.processes.tasks.webhooks.'
            'send_task_completed_webhook.delay'
        )
        account = create_test_account()
        user = create_test_owner(account=account)
        workflow = create_test_workflow(
            user=user,
            tasks_count=2
        )
        now_date = timezone.now()
        date_from = datetime.combine(now_date, time.min)
        date_to = now_date
        task_1 = workflow.tasks.get(number=1)
        task_1.date_started = date_to - timedelta(minutes=1)
        task_1.status = TaskStatus.COMPLETED
        task_1.date_completed = date_from + timedelta(minutes=1)
        task_1.save()

        api_client.token_authenticate(user)

        # act
        response = api_client.get('/reports/dashboard/tasks/overview')

        # assert
        assert response.status_code == 200
        assert response.data['in_progress'] == 1

    def test_my_tasks__in_progress__task_completed_ahead_of_time__not_count(
        self,
        mocker,
        api_client,
    ):
        # arrange
        mocker.patch(
            'src.processes.tasks.webhooks.'
            'send_task_completed_webhook.delay'
        )
        account = create_test_account()
        user = create_test_owner(account=account)
        workflow = create_test_workflow(
            user=user,
            tasks_count=2
        )
        now_date = timezone.now()
        date_from = datetime.combine(now_date, time.min)
        date_to = now_date
        task_1 = workflow.tasks.get(number=1)
        task_1.date_started = date_to - timedelta(minutes=1)
        task_1.status = TaskStatus.COMPLETED
        task_1.date_completed = date_from - timedelta(minutes=1)
        task_1.save()

        api_client.token_authenticate(user)

        # act
        response = api_client.get('/reports/dashboard/tasks/overview')

        # assert
        assert response.status_code == 200
        assert response.data['in_progress'] == 0

    def test_my_tasks__in_progress__task_started_ahead_of_time__not_count(
        self,
        mocker,
        api_client,
    ):
        # arrange
        mocker.patch(
            'src.processes.tasks.webhooks.'
            'send_task_completed_webhook.delay'
        )
        account = create_test_account()
        user = create_test_owner(account=account)
        workflow = create_test_workflow(
            user=user,
            tasks_count=2
        )
        now_date = timezone.now()
        date_from = datetime.combine(now_date, time.min)
        date_to = now_date
        task_1 = workflow.tasks.get(number=1)
        task_1.date_started = date_to + timedelta(minutes=1)
        task_1.status = TaskStatus.COMPLETED
        task_1.date_completed = date_from + timedelta(minutes=1)
        task_1.save()

        api_client.token_authenticate(user)

        # act
        response = api_client.get('/reports/dashboard/tasks/overview')

        # assert
        assert response.status_code == 200
        assert response.data['in_progress'] == 0

    @pytest.mark.parametrize(
        'task_status',
        (
            TaskStatus.ACTIVE,
            TaskStatus.DELAYED,
        )
    )
    def test_my_tasks__overdue_task_allowed_status__ok(
        self,
        mocker,
        api_client,
        task_status
    ):
        # arrange
        mocker.patch(
            'src.processes.tasks.webhooks.'
            'send_task_completed_webhook.delay'
        )
        account = create_test_account()
        user = create_test_owner(account=account)
        workflow = create_test_workflow(
            user=user,
            active_task_number=2,
            tasks_count=3
        )
        now_date = timezone.now()
        date_to = now_date
        task_1 = workflow.tasks.get(number=1)
        task_1.status = task_status
        task_1.date_started = date_to - timedelta(minutes=1)
        task_1.due_date = task_1.date_started + timedelta(minutes=1)
        task_1.save()

        api_client.token_authenticate(user)

        # act
        response = api_client.get('/reports/dashboard/tasks/overview')

        # assert
        assert response.status_code == 200
        assert response.data['started'] == 1

    @pytest.mark.parametrize(
        'task_status',
        (
            TaskStatus.PENDING,
            TaskStatus.SKIPPED,
        )
    )
    def test_my_tasks__overdue_task_not_allowed_status__not_count(
        self,
        mocker,
        api_client,
        task_status
    ):
        # arrange
        mocker.patch(
            'src.processes.tasks.webhooks.'
            'send_task_completed_webhook.delay'
        )
        account = create_test_account()
        user = create_test_owner(account=account)
        workflow = create_test_workflow(
            user=user,
            active_task_number=2,
            tasks_count=3
        )
        now_date = timezone.now()
        date_to = now_date
        task_1 = workflow.tasks.get(number=1)
        task_1.status = task_status
        task_1.date_started = date_to - timedelta(minutes=1)
        task_1.due_date = task_1.date_started + timedelta(minutes=1)
        task_1.save()

        api_client.token_authenticate(user)

        # act
        response = api_client.get('/reports/dashboard/tasks/overview')

        # assert
        assert response.status_code == 200
        assert response.data['started'] == 0

    def test_my_tasks__overdue_task_completed_today__ok(
        self,
        mocker,
        api_client,
    ):
        # arrange
        mocker.patch(
            'src.processes.tasks.webhooks.'
            'send_task_completed_webhook.delay'
        )
        account = create_test_account()
        user = create_test_owner(account=account)
        workflow = create_test_workflow(
            user=user,
            active_task_number=2,
            tasks_count=3
        )
        now_date = timezone.now()
        date_from = datetime.combine(now_date, time.min)
        date_to = now_date
        task_1 = workflow.tasks.get(number=1)
        task_1.status = TaskStatus.COMPLETED
        task_1.date_started = date_to - timedelta(minutes=2)
        task_1.date_completed = date_from + timedelta(minutes=1)
        task_1.due_date = task_1.date_started + timedelta(minutes=1)
        task_1.save()

        api_client.token_authenticate(user)

        # act
        response = api_client.get('/reports/dashboard/tasks/overview')

        # assert
        assert response.status_code == 200
        assert response.data['started'] == 1

    def test_my_tasks__overdue_workflow_completed_today__ok(
        self,
        mocker,
        api_client,
    ):
        # arrange
        mocker.patch(
            'src.processes.tasks.webhooks.'
            'send_task_completed_webhook.delay'
        )
        account = create_test_account()
        user = create_test_owner(account=account)
        workflow = create_test_workflow(
            user=user,
            active_task_number=2,
            tasks_count=3,
            status=WorkflowStatus.DONE
        )
        now_date = timezone.now()
        date_from = datetime.combine(now_date, time.min)
        date_to = now_date
        task_1 = workflow.tasks.get(number=1)
        task_1.date_started = date_to - timedelta(minutes=2)
        task_1.due_date = task_1.date_started + timedelta(minutes=1)
        task_1.save()

        workflow.date_completed = date_from + timedelta(minutes=1)
        workflow.save()

        api_client.token_authenticate(user)

        # act
        response = api_client.get('/reports/dashboard/tasks/overview')

        # assert
        assert response.status_code == 200
        assert response.data['started'] == 1

    def test__my_tasks__deleted_performer__ok(
        self,
        api_client
    ):

        # arrange
        account = create_test_account()
        create_test_owner(account=account)
        user = create_test_admin(account=account)
        workflow = create_test_workflow(user, tasks_count=1)
        task = workflow.tasks.get(number=1)
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
        mocker,
        api_client
    ):
        # arrange
        mocker.patch(
            'src.processes.tasks.webhooks.'
            'send_task_completed_webhook.delay'
        )
        account = create_test_account()
        create_test_owner(account=account)
        template_owner = create_test_admin(account=account)
        user = create_test_admin(
            email='testinguser@pneumatic.app',
            account=account,
        )
        template_1 = create_test_template(template_owner)
        template_2 = create_test_template(template_owner, is_active=True)
        template_task_1 = template_1.tasks.get(number=1)
        template_task_1.add_raw_performer(user)

        template_task_1 = template_2.tasks.get(number=1)
        template_task_1.add_raw_performer(user)

        workflow_1 = create_test_workflow(template_owner, template_1)
        task = workflow_1.tasks.get(number=1)
        api_client.token_authenticate(user)
        api_client.post(
            f'/workflows/{workflow_1.id}/task-complete',
            data={'task_id': task.id},
        )

        overdue_workflow = create_test_workflow(template_owner, template_1)
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
        task = overdue_workflow.tasks.get(number=1)
        api_client.post(
            f'/workflows/{overdue_workflow.id}/task-complete',
            data={'task_id': task.id},
        )

        api_client.delete(f'/templates/{template_1.id}')

        workflow_4 = create_test_workflow(template_owner, template_2)
        workflow_4.status = WorkflowStatus.DONE
        workflow_4.date_completed = timezone.now()
        workflow_4.save(update_fields=['status', 'date_completed'])

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
        account = create_test_account()
        create_test_owner(account=account)
        create_test_admin(account=account)
        user = create_test_admin(
            email='testinguser@pneumatic.app',
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
        mocker,
        api_client,
    ):
        """ caused by: https://my.pneumatic.app/workflows/12359 """
        # arrange
        mocker.patch(
            'src.processes.tasks.webhooks.'
            'send_task_completed_webhook.delay'
        )
        account = create_test_account()
        create_test_owner(account=account)
        template_owner = create_test_admin(account=account)
        user = create_test_admin(
            email='testinguser@pneumatic.app',
            account=account,
        )
        template_1 = create_test_template(template_owner, is_active=True)

        template_task_1 = template_1.tasks.get(number=1)
        template_task_1.require_completion_by_all = True
        template_task_1.save()
        template_task_1.add_raw_performer(user)

        workflow_1 = create_test_workflow(template_owner, template_1)
        task = workflow_1.tasks.get(number=1)
        api_client.token_authenticate(user)
        api_client.post(
            f'/workflows/{workflow_1.id}/task-complete',
            data={'task_id': task.id},
        )

        overdue_workflow = create_test_workflow(template_owner, template_1)
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
            data={'task_id': task.id},
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
        mocker,
        api_client
    ):
        # arrange
        mocker.patch(
            'src.processes.tasks.webhooks.'
            'send_task_completed_webhook.delay'
        )
        account = create_test_account()
        create_test_owner(account=account)
        template_owner = create_test_admin(account=account)
        user = create_test_admin(
            email='testinguser@pneumatic.app',
            account=account,
        )
        template_1 = create_test_template(template_owner)
        template_2 = create_test_template(template_owner, is_active=True)

        template_task_1 = template_1.tasks.get(number=1)
        template_task_1.add_raw_performer(user)

        template_task_1 = template_2.tasks.get(number=1)
        template_task_1.add_raw_performer(user)

        workflow_1 = create_test_workflow(template_owner, template_1)
        task = workflow_1.tasks.get(number=1)
        api_client.token_authenticate(user)
        api_client.post(
            f'/workflows/{workflow_1.id}/task-complete',
            data={'task_id': task.id},
        )

        overdue_workflow = create_test_workflow(template_owner, template_1)
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

        workflow_2 = create_test_workflow(template_owner, template_1)
        workflow_2.status = WorkflowStatus.RUNNING
        workflow_2.save(update_fields=['status'])

        workflow_4 = create_test_workflow(template_owner, template_2)
        workflow_4.status = WorkflowStatus.DONE
        workflow_4.date_completed = timezone.now()
        workflow_4.save(update_fields=['status', 'date_completed'])

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
        create_test_owner(account=account)
        user = create_test_admin(account=account)
        workflow = create_test_workflow(user, tasks_count=1)
        task = workflow.tasks.get(number=1)
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

    def test_my_tasks__group_assignment__ok(
        self,
        mocker,
        api_client
    ):
        # arrange
        mocker.patch(
            'src.processes.tasks.webhooks.'
            'send_task_completed_webhook.delay'
        )
        user = create_test_owner()
        group = create_test_group(user.account, users=[user])
        workflow = create_test_workflow(
            user=user,
            active_task_number=1,
            tasks_count=1
        )
        task = workflow.tasks.get(number=1)
        TaskPerformer.objects.filter(
            task=task
        ).update(directly_status=DirectlyStatus.DELETED)
        TaskPerformer.objects.create(
            task=task,
            type=PerformerType.GROUP,
            group=group,
        )

        api_client.token_authenticate(user)

        # act
        response = api_client.get('/reports/dashboard/tasks/overview')

        # assert
        assert response.status_code == 200
        assert response.data['in_progress'] == 1
        assert response.data['started'] == 1
        assert response.data['completed'] == 0
        assert response.data['overdue'] == 0

    def test_my_tasks_now_in_progress__performer_user_and_group__ok(
        self,
        mocker,
        api_client
    ):
        # arrange
        mocker.patch(
            'src.processes.tasks.webhooks.'
            'send_task_completed_webhook.delay'
        )
        account = create_test_account()
        user = create_test_owner(account=account)
        group = create_test_group(account, users=[user])
        group2 = create_test_group(account, users=[user])
        workflow = create_test_workflow(user=user, tasks_count=1)
        task_1 = workflow.tasks.get(number=1)
        task_1.date_started = timezone.now() - timedelta(hours=1)
        task_1.status = TaskStatus.ACTIVE
        TaskPerformer.objects.create(
            task_id=task_1.id,
            type=PerformerType.GROUP,
            group_id=group.id,
        )
        TaskPerformer.objects.create(
            task_id=task_1.id,
            type=PerformerType.GROUP,
            group_id=group2.id,
        )
        task_1.save()

        api_client.token_authenticate(user)

        # act
        response = api_client.get(
            '/reports/dashboard/tasks/overview',
            data={'now': True}
        )

        # assert
        assert response.status_code == 200
        assert response.data['in_progress'] == 1

    def test_my_tasks_now_overdue__performer_user_and_group__ok(
        self,
        mocker,
        api_client
    ):
        # arrange
        mocker.patch(
            'src.processes.tasks.webhooks.'
            'send_task_completed_webhook.delay'
        )
        account = create_test_account()
        user = create_test_owner(account=account)
        group = create_test_group(account, users=[user])
        group2 = create_test_group(account, users=[user])
        workflow = create_test_workflow(user=user, tasks_count=1)
        task_1 = workflow.tasks.get(number=1)
        task_1.date_started = timezone.now() - timedelta(hours=2)
        task_1.due_date = timezone.now() - timedelta(hours=1)
        task_1.status = TaskStatus.ACTIVE
        TaskPerformer.objects.create(
            task_id=task_1.id,
            type=PerformerType.GROUP,
            group_id=group.id,
        )
        TaskPerformer.objects.create(
            task_id=task_1.id,
            type=PerformerType.GROUP,
            group_id=group2.id,
        )
        task_1.save()

        api_client.token_authenticate(user)

        # act
        response = api_client.get(
            '/reports/dashboard/tasks/overview',
            data={'now': True}
        )

        # assert
        assert response.status_code == 200
        assert response.data['overdue'] == 1


class TestDashboardMyTasksBreakdown:

    def test_my_tasks_breakdown__ok(
        self,
        mocker,
        api_client
    ):
        # arrange
        mocker.patch(
            'src.processes.tasks.webhooks.'
            'send_task_completed_webhook.delay'
        )
        account = create_test_account()
        create_test_owner(account=account)
        template_owner = create_test_admin(account=account)
        user = create_test_admin(
            email='testinguser@pneumatic.app',
            account=account,
        )
        template_1 = create_test_template(template_owner)
        template_2 = create_test_template(template_owner, is_active=True)
        third_template = create_test_template(template_owner, is_active=True)

        template_task_1 = template_1.tasks.get(number=1)
        template_task_1.add_raw_performer(user)

        template_task_1 = template_2.tasks.get(number=1)
        template_task_1.add_raw_performer(user)

        template_task_2 = third_template.tasks.get(number=2)
        template_task_2.add_raw_performer(user)

        workflow_1 = create_test_workflow(template_owner, template_1)
        task = workflow_1.tasks.get(number=1)
        api_client.token_authenticate(user)
        api_client.post(
            f'/workflows/{workflow_1.id}/task-complete',
            data={'task_id': task.id},
        )

        overdue_workflow = create_test_workflow(template_owner, template_1)
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
            data={'task_id': task.id},
        )
        workflow_3 = create_test_workflow(template_owner, template_1)
        task = workflow_3.tasks.get(number=1)
        api_client.post(
            f'/workflows/{workflow_3.id}/task-complete',
            data={'task_id': task.id},
        )

        api_client.token_authenticate(template_owner)
        api_client.post(
            f'/workflows/{overdue_workflow.id}/task-complete',
            data={'task_id': overdue_workflow.tasks.get(number=2).id},
        )

        workflow_2 = create_test_workflow(template_owner, template_1)
        workflow_2.status = WorkflowStatus.RUNNING
        workflow_2.save(update_fields=['status'])

        workflow_4 = create_test_workflow(template_owner, template_2)
        workflow_4.status = WorkflowStatus.DONE
        workflow_4.date_completed = timezone.now()
        workflow_4.save(update_fields=['status', 'date_completed'])

        api_client.token_authenticate(user)

        # act
        response = api_client.get('/reports/dashboard/tasks/breakdown')

        # assert
        assert response.status_code == 200
        assert len(response.data) == 2
        assert response.data[0]['template_id'] == template_1.id
        assert response.data[0]['template_name'] == template_1.name
        assert response.data[0]['started'] == 3
        assert response.data[0]['completed'] == 3
        assert response.data[0]['in_progress'] == 4
        assert response.data[0]['overdue'] == 1
        assert response.data[1]['template_id'] == template_2.id
        assert response.data[1]['template_name'] == template_2.name
        assert response.data[1]['started'] == 1
        assert response.data[1]['completed'] == 0
        assert response.data[1]['in_progress'] == 1
        assert response.data[1]['overdue'] == 0

    def test_my_tasks_breakdown__deleted_performer__ok(
        self,
        api_client
    ):

        # arrange
        account = create_test_account()
        create_test_owner(account=account)
        user = create_test_admin(account=account)
        workflow = create_test_workflow(user, tasks_count=1)
        task = workflow.tasks.get(number=1)
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
        mocker,
        api_client,
    ):
        """ caused by: https://my.pneumatic.app/workflows/12359 """
        # arrange
        mocker.patch(
            'src.processes.tasks.webhooks.'
            'send_task_completed_webhook.delay'
        )
        account = create_test_account()
        create_test_owner(account=account)
        template_owner = create_test_admin(account=account)
        user = create_test_admin(
            email='testinguser@pneumatic.app',
            account=account,
        )
        template_1 = create_test_template(template_owner, is_active=True)

        template_task_1 = template_1.tasks.get(number=1)
        template_task_1.require_completion_by_all = True
        template_task_1.save()
        template_task_1.add_raw_performer(user)

        workflow_1 = create_test_workflow(template_owner, template_1)
        task = workflow_1.tasks.get(number=1)
        api_client.token_authenticate(user)
        api_client.post(
            f'/workflows/{workflow_1.id}/task-complete',
            data={'task_id': task.id},
        )

        overdue_workflow = create_test_workflow(template_owner, template_1)
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
            data={'task_id': task.id},
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
        assert owner_response.data[0]['template_id'] == template_1.id
        assert owner_response.data[0]['in_progress'] == 1
        assert owner_response.data[0]['overdue'] == 0
        assert user_response.status_code == 200
        assert user_response.data[0]['template_id'] == template_1.id
        assert user_response.data[0]['in_progress'] == 1
        assert user_response.data[0]['overdue'] == 1

    def test_my_tasks_breakdown__regular_user__ok(
        self,
        api_client
    ):
        # arrange
        account = create_test_account()
        create_test_owner(account=account)
        user = create_test_admin(
            email='testinguser@pneumatic.app',
            account=account,
        )
        api_client.token_authenticate(user)

        # act
        response = api_client.get('/reports/dashboard/tasks/breakdown')

        # assert
        assert response.status_code == 200
        assert response.data == []

    def test_my_tasks_breakdown__overdue_tasks(
        self,
        mocker,
        api_client
    ):
        # arrange
        mocker.patch(
            'src.processes.tasks.webhooks.'
            'send_task_completed_webhook.delay'
        )
        account = create_test_account()
        create_test_owner(account=account)
        template_owner = create_test_admin(account=account)
        user = create_test_admin(
            email='testinguser@pneumatic.app',
            account=account,
        )
        template_1 = create_test_template(template_owner)

        template_task_1 = template_1.tasks.get(number=1)
        template_task_1.add_raw_performer(user)

        api_client.token_authenticate(user)

        overdue_workflow = create_test_workflow(template_owner, template_1)
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
            data={'task_id': task.id},
        )

        not_overdue_workflow = create_test_workflow(
            user=template_owner,
            template=template_1,
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
        assert response.data[0]['template_id'] == template_1.id
        assert response.data[0]['template_name'] == template_1.name
        assert response.data[0]['started'] == 0
        assert response.data[0]['completed'] == 1
        assert response.data[0]['in_progress'] == 1
        assert response.data[0]['overdue'] == 1

    def test_my_tasks_breakdown_now(
        self,
        mocker,
        api_client
    ):
        # arrange
        mocker.patch(
            'src.processes.tasks.webhooks.'
            'send_task_completed_webhook.delay'
        )
        account = create_test_account()
        create_test_owner(account=account)
        template_owner = create_test_admin(account=account)
        user = create_test_admin(
            email='testinguser@pneumatic.app',
            account=account,
        )
        template_1 = create_test_template(template_owner)
        template_2 = create_test_template(template_owner, is_active=True)
        third_template = create_test_template(template_owner, is_active=True)

        template_task_1 = template_1.tasks.get(number=1)
        template_task_1.add_raw_performer(user)

        template_task_1 = template_2.tasks.get(number=1)
        template_task_1.add_raw_performer(user)

        template_task_2 = third_template.tasks.get(number=2)
        template_task_2.add_raw_performer(user)

        workflow_1 = create_test_workflow(template_owner, template_1)
        task = workflow_1.tasks.get(number=1)
        api_client.token_authenticate(user)
        api_client.post(
            f'/workflows/{workflow_1.id}/task-complete',
            data={'task_id': task.id},
        )

        overdue_workflow = create_test_workflow(template_owner, template_1)
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
        workflow_3 = create_test_workflow(template_owner, template_1)
        task = workflow_3.tasks.get(number=1)
        api_client.post(
            f'/workflows/{workflow_3.id}/task-complete',
            data={'task_id': task.id},
        )

        workflow_2 = create_test_workflow(template_owner, template_1)
        workflow_2.status = WorkflowStatus.RUNNING
        workflow_2.save(update_fields=['status'])

        workflow_4 = create_test_workflow(template_owner, template_2)
        workflow_4.status = WorkflowStatus.DONE
        workflow_4.date_completed = timezone.now()
        workflow_4.save(update_fields=['status', 'date_completed'])

        api_client.token_authenticate(user)

        # act
        response = api_client.get(
            '/reports/dashboard/tasks/breakdown',
            data={'now': True},
        )

        # assert
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]['template_id'] == template_1.id
        assert response.data[0]['template_name'] == template_1.name
        assert response.data[0]['in_progress'] == 2
        assert response.data[0]['started'] is None
        assert response.data[0]['completed'] is None
        assert response.data[0]['overdue'] == 1

    def test_my_tasks_breakdown_now__deleted_performer__ok(
        self,
        api_client
    ):

        # arrange
        account = create_test_account()
        create_test_owner(account=account)
        user = create_test_admin(account=account)
        workflow = create_test_workflow(user, tasks_count=1)
        task = workflow.tasks.get(number=1)
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

    def test_my_tasks_breakdown_now__performer_user_and_group__ok(
        self,
        mocker,
        api_client
    ):
        # arrange
        mocker.patch(
            'src.processes.tasks.webhooks.'
            'send_task_completed_webhook.delay'
        )
        account = create_test_account()
        create_test_owner(account=account)
        template_owner = create_test_admin(account=account)
        user = create_test_admin(
            email='testinguser@pneumatic.app',
            account=account,
        )
        template_1 = create_test_template(template_owner)
        template_task_1 = template_1.tasks.get(number=1)
        template_task_1.add_raw_performer(user)
        workflow_1 = create_test_workflow(template_owner, template_1)
        task_1 = workflow_1.tasks.get(number=1)
        group = create_test_group(account, users=[user])
        group2 = create_test_group(account, users=[user])
        TaskPerformer.objects.filter(task=task_1).delete()
        TaskPerformer.objects.create(
            task_id=task_1.id,
            type=PerformerType.GROUP,
            group_id=group.id,
        )
        TaskPerformer.objects.create(
            task_id=task_1.id,
            type=PerformerType.GROUP,
            group_id=group2.id,
        )

        task_1.date_started = timezone.now() - timedelta(hours=1)
        task_1.status = TaskStatus.ACTIVE
        task_1.save()

        api_client.token_authenticate(user)

        # act
        response = api_client.get(
            '/reports/dashboard/tasks/breakdown',
            data={'now': True}
        )

        # assert
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]['template_id'] == template_1.id
        assert response.data[0]['template_name'] == template_1.name
        assert response.data[0]['in_progress'] == 1
        assert response.data[0]['started'] is None
        assert response.data[0]['completed'] is None
        assert response.data[0]['overdue'] == 0

    def test_my_tasks_breakdown__group_assignment__ok(
        self,
        mocker,
        api_client
    ):
        # arrange
        mocker.patch(
            'src.processes.tasks.webhooks.'
            'send_task_completed_webhook.delay'
        )
        account = create_test_account()
        create_test_owner(account=account)
        template_owner = create_test_admin(account=account)
        user = create_test_admin(
            email='testinguser@pneumatic.app',
            account=account,
        )
        group = create_test_group(user.account, users=[user])
        template_1 = create_test_template(template_owner)
        template_2 = create_test_template(template_owner, is_active=True)
        third_template = create_test_template(template_owner, is_active=True)

        template_task_1 = template_1.tasks.get(number=1)
        template_task_1.add_raw_performer(
            group=group,
            performer_type=PerformerType.GROUP
        )

        template_task_1 = template_2.tasks.get(number=1)
        template_task_1.add_raw_performer(
            group=group,
            performer_type=PerformerType.GROUP
        )

        template_task_2 = third_template.tasks.get(number=2)
        template_task_2.add_raw_performer(
            group=group,
            performer_type=PerformerType.GROUP
        )

        workflow_1 = create_test_workflow(template_owner, template_1)
        task = workflow_1.tasks.get(number=1)
        api_client.token_authenticate(user)
        api_client.post(
            f'/workflows/{workflow_1.id}/task-complete',
            data={'task_id': task.id},
        )

        overdue_workflow = create_test_workflow(template_owner, template_1)
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
            data={'task_id': task.id},
        )
        workflow_3 = create_test_workflow(template_owner, template_1)
        task = workflow_3.tasks.get(number=1)
        api_client.post(
            f'/workflows/{workflow_3.id}/task-complete',
            data={'task_id': task.id},
        )

        api_client.token_authenticate(template_owner)
        api_client.post(
            f'/workflows/{overdue_workflow.id}/task-complete',
            data={'task_id': overdue_workflow.tasks.get(number=2).id},
        )

        workflow_2 = create_test_workflow(template_owner, template_1)
        workflow_2.status = WorkflowStatus.RUNNING
        workflow_2.save(update_fields=['status'])

        workflow_4 = create_test_workflow(template_owner, template_2)
        workflow_4.status = WorkflowStatus.DONE
        workflow_4.date_completed = timezone.now()
        workflow_4.save(update_fields=['status', 'date_completed'])

        api_client.token_authenticate(user)

        # act
        response = api_client.get('/reports/dashboard/tasks/breakdown')

        # assert
        assert response.status_code == 200
        assert len(response.data) == 2
        assert response.data[0]['template_id'] == template_1.id
        assert response.data[0]['template_name'] == template_1.name
        assert response.data[0]['started'] == 3
        assert response.data[0]['completed'] == 3
        assert response.data[0]['in_progress'] == 4
        assert response.data[0]['overdue'] == 1
        assert response.data[1]['template_id'] == template_2.id
        assert response.data[1]['template_name'] == template_2.name
        assert response.data[1]['started'] == 1
        assert response.data[1]['completed'] == 0
        assert response.data[1]['in_progress'] == 1
        assert response.data[1]['overdue'] == 0


class TestDashboardMyTasksBreakdownBySteps:

    def test_my_tasks_breakdown_by_steps__ok(
        self,
        mocker,
        api_client
    ):
        # arrange
        mocker.patch(
            'src.processes.tasks.webhooks.'
            'send_task_completed_webhook.delay'
        )
        account = create_test_account()
        create_test_owner(account=account)
        template_owner = create_test_admin(account=account)
        user = create_test_admin(
            email='testinguser@pneumatic.app',
            account=account,
        )
        template_1 = create_test_template(template_owner)
        template_2 = create_test_template(template_owner, is_active=True)

        template_task_1 = template_1.tasks.get(number=1)
        template_task_1.add_raw_performer(user)
        template_task_2 = template_1.tasks.get(number=2)
        template_task_2.add_raw_performer(user)

        template_2_template_task_1 = template_2.tasks.get(number=1)
        template_2_template_task_1.add_raw_performer(user)

        workflow_1 = create_test_workflow(template_owner, template_1)
        task = workflow_1.tasks.get(number=1)
        api_client.token_authenticate(user)
        api_client.post(
            f'/workflows/{workflow_1.id}/task-complete',
            data={'task_id': task.id},
        )

        overdue_workflow = create_test_workflow(template_owner, template_1)
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
            data={'task_id': task.id},
        )
        workflow_3 = create_test_workflow(template_owner, template_1)
        task = workflow_3.tasks.get(number=1)
        api_client.post(
            f'/workflows/{workflow_3.id}/task-complete',
            data={'task_id': task.id},
        )

        api_client.token_authenticate(template_owner)
        api_client.post(
            f'/workflows/{overdue_workflow.id}/task-complete',
            data={'task_id': overdue_workflow.tasks.get(number=2).id},
        )

        workflow_2 = create_test_workflow(template_owner, template_1)
        workflow_2.status = WorkflowStatus.RUNNING
        workflow_2.save(update_fields=['status'])

        workflow_4 = create_test_workflow(template_owner, template_2)
        workflow_4.status = WorkflowStatus.DONE
        workflow_4.date_completed = timezone.now()
        workflow_4.save(update_fields=['status', 'date_completed'])

        api_client.token_authenticate(user)

        # act
        response = api_client.get(
            '/reports/dashboard/tasks/by-steps',
            data={'template_id': template_1.id},
        )

        # assert
        assert response.status_code == 200
        assert len(response.data) == 2
        assert response.data[0]['id'] == template_task_1.id
        assert response.data[0]['api_name'] == template_task_1.api_name
        assert response.data[0]['name'] == template_task_1.name
        assert response.data[0]['number'] == template_task_1.number
        assert response.data[0]['started'] == 3
        assert response.data[0]['completed'] == 3
        assert response.data[0]['in_progress'] == 4
        assert response.data[0]['overdue'] == 1

        assert response.data[1]['id'] == template_task_2.id
        assert response.data[1]['api_name'] == template_task_2.api_name
        assert response.data[1]['name'] == template_task_2.name
        assert response.data[1]['number'] == template_task_2.number
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
        create_test_owner(account=account)
        user = create_test_admin(account=account)
        workflow = create_test_workflow(user, tasks_count=1)
        task = workflow.tasks.get(number=1)
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
        mocker,
        api_client,
    ):
        """ caused by: https://my.pneumatic.app/workflows/12359 """
        # arrange
        mocker.patch(
            'src.processes.tasks.webhooks.'
            'send_task_completed_webhook.delay'
        )
        account = create_test_account()
        create_test_owner(account=account)
        template_owner = create_test_admin(account=account)
        user = create_test_admin(
            email='testinguser@pneumatic.app',
            account=account,
        )
        template_1 = create_test_template(template_owner, is_active=True)

        template_task_1 = template_1.tasks.get(number=1)
        template_task_1.require_completion_by_all = True
        template_task_1.save()
        template_task_1.add_raw_performer(user)
        template_1.tasks.get(number=2)

        workflow_1 = create_test_workflow(template_owner, template_1)
        task = workflow_1.tasks.get(number=1)
        api_client.token_authenticate(user)
        api_client.post(
            f'/workflows/{workflow_1.id}/task-complete',
            data={'task_id': task.id},
        )

        overdue_workflow = create_test_workflow(template_owner, template_1)
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
            data={'task_id': task.id},
        )

        # act
        template_owner_response = api_client.get(
            '/reports/dashboard/tasks/by-steps',
            data={
                'template_id': template_1.id,
                'now': True,
            },
        )
        api_client.token_authenticate(user)
        regular_user_response = api_client.get(
            '/reports/dashboard/tasks/by-steps',
            data={
                'template_id': template_1.id,
                'now': True,
            },
        )

        # assert
        assert template_owner_response.status_code == 200
        assert len(template_owner_response.data) == 3
        assert template_owner_response.data[0]['id'] == template_task_1.id
        assert template_owner_response.data[0]['in_progress'] == 1
        assert template_owner_response.data[0]['overdue'] == 0
        assert regular_user_response.status_code == 200
        assert len(regular_user_response.data) == 1
        assert regular_user_response.data[0]['id'] == template_task_1.id
        assert regular_user_response.data[0]['in_progress'] == 1
        assert regular_user_response.data[0]['overdue'] == 1

    def test_my_tasks_breakdown__skipped_tasks__not_count_in_progress(
        self,
        api_client
    ):
        # arrange
        account = create_test_account()
        create_test_owner(account=account)
        user = create_test_admin()

        template = create_test_template(
            user=user,
            tasks_count=2,
            is_active=True
        )
        field_api_name = 'field-api-name-1'
        FieldTemplate.objects.create(
            kickoff=template.kickoff_instance,
            type=FieldType.STRING,
            name='Skip first task marker',
            template=template,
            api_name=field_api_name
        )
        template_task_1 = template.tasks.get(number=1)
        template_task_2 = template.tasks.get(number=2)

        condition_template = ConditionTemplate.objects.create(
            task=template_task_1,
            action=ConditionAction.SKIP_TASK,
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
            field=field_api_name,
            value='skip',
            template=template,
        )

        api_client.token_authenticate(user)

        response_run_1 = api_client.post(
            f'/templates/{template.id}/run',
            data={'kickoff': {field_api_name: 'skip'}}
        )
        response_run_2 = api_client.post(
            f'/templates/{template.id}/run',
            data={'kickoff': {field_api_name: 'no-skip'}}
        )

        # act
        response = api_client.get(
            '/reports/dashboard/tasks/by-steps',
            data={'template_id': template.id},
        )
        # assert
        assert response_run_1.status_code == 200
        assert response_run_2.status_code == 200
        assert response.status_code == 200
        assert response.data[0]['id']
        assert response.data[0]['api_name']
        assert response.data[0]['name'] == template_task_1.name
        assert response.data[0]['number'] == 1
        assert response.data[0]['started'] == 1
        assert response.data[0]['completed'] == 0
        assert response.data[0]['in_progress'] == 1
        assert response.data[0]['overdue'] == 0

        assert response.data[1]['id']
        assert response.data[1]['api_name']
        assert response.data[1]['name'] == template_task_2.name
        assert response.data[1]['number'] == 2
        assert response.data[1]['started'] == 1
        assert response.data[1]['completed'] == 0
        assert response.data[1]['in_progress'] == 1
        assert response.data[1]['overdue'] == 0

    def test_my_tasks_breakdown__now__ok(
        self,
        mocker,
        api_client
    ):
        # arrange
        mocker.patch(
            'src.processes.tasks.webhooks.'
            'send_task_completed_webhook.delay'
        )
        account = create_test_account()
        create_test_owner(account=account)
        template_owner = create_test_admin(account=account)
        user = create_test_admin(
            email='testinguser@pneumatic.app',
            account=account,
        )
        template_1 = create_test_template(template_owner)
        template_2 = create_test_template(template_owner, is_active=True)

        template_task_1 = template_1.tasks.get(number=1)
        template_task_1.add_raw_performer(user)
        template_task_2 = template_1.tasks.get(number=2)
        template_task_2.add_raw_performer(user)

        template_2_template_task_1 = template_2.tasks.get(number=1)
        template_2_template_task_1.add_raw_performer(user)

        workflow_1 = create_test_workflow(template_owner, template_1)
        task = workflow_1.tasks.get(number=1)
        api_client.token_authenticate(user)
        api_client.post(
            f'/workflows/{workflow_1.id}/task-complete',
            data={'task_id': task.id},
        )

        overdue_workflow = create_test_workflow(template_owner, template_1)
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
        workflow_3 = create_test_workflow(template_owner, template_1)
        task = workflow_3.tasks.get(number=1)
        api_client.post(
            f'/workflows/{workflow_3.id}/task-complete',
            data={'task_id': task.id},
        )

        workflow_2 = create_test_workflow(template_owner, template_1)
        workflow_2.status = WorkflowStatus.RUNNING
        workflow_2.save(update_fields=['status'])
        task = workflow_2.tasks.get(number=1)

        api_client.post(
            f'/workflows/{workflow_2.id}/task-complete',
            data={'task_id': task.id},
        )

        workflow_4 = create_test_workflow(template_owner, template_2)
        workflow_4.status = WorkflowStatus.DONE
        workflow_4.date_completed = timezone.now()
        workflow_4.save(update_fields=['status', 'date_completed'])

        api_client.token_authenticate(user)

        # act
        response = api_client.get(
            '/reports/dashboard/tasks/by-steps',
            data={'template_id': template_1.id, 'now': True},
        )

        # assert
        assert response.status_code == 200
        assert len(response.data) == 2
        assert response.data[0]['id'] == template_task_1.id
        assert response.data[0]['api_name'] == template_task_1.api_name
        assert response.data[0]['name'] == template_task_1.name
        assert response.data[0]['number'] == template_task_1.number
        assert response.data[0]['in_progress'] == 1
        assert response.data[0]['started'] is None
        assert response.data[0]['completed'] is None
        assert response.data[0]['overdue'] == 1

        assert response.data[1]['id'] == template_task_2.id
        assert response.data[1]['api_name'] == template_task_2.api_name
        assert response.data[1]['name'] == template_task_2.name
        assert response.data[1]['number'] == template_task_2.number
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
        create_test_owner(account=account)
        user = create_test_admin(account=account)
        workflow = create_test_workflow(user, tasks_count=1)
        task = workflow.tasks.get(number=1)
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
        create_test_owner(account=account)
        template_owner = create_test_admin(account=account)
        user = create_test_admin(
            email='testinguser@pneumatic.app',
            account=account,
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
        assert response.data[0]['api_name'] == task_template.api_name
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
        create_test_owner(account=account)
        template_owner = create_test_admin(account=account)
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
        assert response.data[0]['api_name'] == task_template.api_name
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
        create_test_owner(account=account)
        template_owner = create_test_admin(account=account)
        user = create_test_admin(
            email='testinguser@pneumatic.app',
            account=account,
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
        assert response.data[0]['api_name'] == task_template.api_name
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
        create_test_owner(account=account)
        template_owner = create_test_admin(account=account)
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
        assert response.data[0]['api_name'] == task_template.api_name
        assert response.data[0]['name'] == task_template.name
        assert response.data[0]['number'] == 1
        assert response.data[0]['started'] is None
        assert response.data[0]['completed'] is None
        assert response.data[0]['in_progress'] == 1
        assert response.data[0]['overdue'] == 0

    def test_my_tasks_breakdown_by_steps_now__performer_user_and_group__ok(
        self,
        mocker,
        api_client
    ):
        # arrange
        mocker.patch(
            'src.processes.tasks.webhooks.'
            'send_task_completed_webhook.delay'
        )
        account = create_test_account()
        create_test_owner(account=account)
        template_owner = create_test_admin(account=account)
        user = create_test_admin(
            email='testinguser@pneumatic.app',
            account=account,
        )
        template_1 = create_test_template(template_owner)
        template_task_1 = template_1.tasks.get(number=1)
        template_task_1.add_raw_performer(user)
        workflow_1 = create_test_workflow(template_owner, template_1)
        task_1 = workflow_1.tasks.get(number=1)
        group = create_test_group(account, users=[user])
        group2 = create_test_group(account, users=[user])
        TaskPerformer.objects.filter(task=task_1).delete()
        TaskPerformer.objects.create(
            task_id=task_1.id,
            type=PerformerType.GROUP,
            group_id=group.id,
        )
        TaskPerformer.objects.create(
            task_id=task_1.id,
            type=PerformerType.GROUP,
            group_id=group2.id,
        )
        task_1.date_started = timezone.now() - timedelta(hours=1)
        task_1.status = TaskStatus.ACTIVE
        task_1.save()

        api_client.token_authenticate(user)

        # act
        response = api_client.get(
            '/reports/dashboard/tasks/by-steps',
            data={'template_id': template_1.id, 'now': True},
        )

        # assert
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]['id'] == template_task_1.id
        assert response.data[0]['api_name'] == template_task_1.api_name
        assert response.data[0]['name'] == template_task_1.name
        assert response.data[0]['number'] == 1
        assert response.data[0]['in_progress'] == 1
        assert response.data[0]['started'] is None
        assert response.data[0]['completed'] is None
        assert response.data[0]['overdue'] == 0

    def test_my_tasks_breakdown__group_assignment__ok(
        self,
        mocker,
        api_client
    ):
        # arrange
        mocker.patch(
            'src.processes.tasks.webhooks.'
            'send_task_completed_webhook.delay'
        )
        user = create_test_owner()
        group = create_test_group(user.account, users=[user])
        workflow = create_test_workflow(
            user=user,
            active_task_number=1,
            tasks_count=1
        )
        task = workflow.tasks.get(number=1)

        TaskPerformer.objects.filter(
            task=task
        ).update(directly_status=DirectlyStatus.DELETED)

        TaskPerformer.objects.create(
            task=task,
            type=PerformerType.GROUP,
            group=group,
        )

        api_client.token_authenticate(user)

        # act
        response = api_client.get('/reports/dashboard/tasks/breakdown')

        # assert
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]['template_id'] == workflow.template.id
        assert response.data[0]['template_name'] == workflow.template.name
        assert response.data[0]['in_progress'] == 1
        assert response.data[0]['started'] == 1
        assert response.data[0]['completed'] == 0
        assert response.data[0]['overdue'] == 0
