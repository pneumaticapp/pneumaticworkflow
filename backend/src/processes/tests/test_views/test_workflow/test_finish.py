from datetime import timedelta

import pytest
from django.utils import timezone

from src.accounts.enums import BillingPlanType

from src.authentication.enums import AuthTokenType
from src.processes.enums import (
    DirectlyStatus,
    WorkflowStatus,
)
from src.processes.messages import workflow as messages
from src.processes.models.workflows.task import TaskPerformer
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_admin,
    create_test_guest,
    create_test_not_admin,
    create_test_owner,
    create_test_template,
    create_test_user,
    create_test_workflow,
)
from src.utils.validation import ErrorCode

pytestmark = pytest.mark.django_db


class TestFinishWorkflow:

    # End workflow

    def test_finish__ok(
        self,
        mocker,
        api_client,
        analysis_mock,
    ):

        # arrange
        user = create_test_user()
        workflow = create_test_workflow(
            user=user,
            finalizable=True,
            tasks_count=2,
        )
        task_1 = workflow.tasks.get(number=1)
        task_2 = workflow.tasks.get(number=2)
        deactivate_cache_mock = mocker.patch(
            'src.authentication.services.guest_auth.'
            'GuestJWTAuthService.deactivate_task_guest_cache',
        )
        send_removed_task_notification_mock = mocker.patch(
            'src.notifications.tasks'
            '.send_removed_task_notification.delay',
        )
        api_client.token_authenticate(user)

        # act
        response = api_client.post(
            f'/workflows/{workflow.id}/finish',
            data={},
        )
        workflow.refresh_from_db()

        # assert
        assert response.status_code == 204
        assert workflow.status == WorkflowStatus.DONE
        assert workflow.date_completed
        analysis_mock.workflows_ended.assert_called_once_with(
            user=user,
            workflow=workflow,
            auth_type=AuthTokenType.USER,
            is_superuser=False,
        )
        deactivate_cache_mock.assert_has_calls(
            [
                mocker.call(task_id=task_1.id),
                mocker.call(task_id=task_2.id),
            ],
        )
        send_removed_task_notification_mock.assert_called_once_with(
            task_id=task_1.id,
            recipients=[(user.id, user.email)],
            account_id=task_1.account_id,
        )

    def test_finish__legacy_template__ok(
        self,
        mocker,
        analysis_mock,
        api_client,
    ):

        # arrange
        user = create_test_user()
        template = create_test_template(
            user=user,
            is_active=True,
            tasks_count=1,
            finalizable=True,
        )
        workflow = create_test_workflow(
            user=user,
            template=template,
        )
        api_client.token_authenticate(user)
        api_client.delete(f'/templates/{template.id}')
        mocker.patch(
            'src.notifications.tasks'
            '.send_removed_task_notification.delay',
        )

        # act
        response = api_client.post(
            f'/workflows/{workflow.id}/finish',
            data={},
        )

        workflow.refresh_from_db()

        # assert
        assert response.status_code == 204
        assert workflow.status == WorkflowStatus.DONE
        analysis_mock.workflows_ended.assert_called_once_with(
            user=user,
            workflow=workflow,
            auth_type=AuthTokenType.USER,
            is_superuser=False,
        )

    def test_finish__notification__for_not_completed_only(
        self,
        mocker,
        api_client,
        analysis_mock,
    ):

        # arrange
        account = create_test_account()
        user = create_test_user(account=account)
        workflow = create_test_workflow(
            user=user,
            finalizable=True,
            tasks_count=2,
        )
        task_1 = workflow.tasks.get(number=1)
        deleted_performer = create_test_user(
            account=account,
            email='deleted@test.test',
            is_account_owner=False,
        )
        TaskPerformer.objects.create(
            task_id=task_1.id,
            user_id=deleted_performer.id,
            directly_status=DirectlyStatus.DELETED,
        )
        completed_performer = create_test_user(
            account=account,
            email='user_3@test.test',
            is_account_owner=False,
        )
        TaskPerformer.objects.create(
            task_id=task_1.id,
            user_id=completed_performer.id,
            is_completed=True,
        )
        guest = create_test_guest(account=account)
        TaskPerformer.objects.create(
            task_id=task_1.id,
            user_id=guest.id,
        )

        user_4 = create_test_user(
            account=account,
            email='user_4@test.test',
            is_account_owner=False,
        )
        TaskPerformer.objects.create(
            task_id=task_1.id,
            user_id=user_4.id,
        )

        mocker.patch(
            'src.authentication.services.guest_auth.'
            'GuestJWTAuthService.deactivate_task_guest_cache',
        )
        send_removed_task_notification_mock = mocker.patch(
            'src.notifications.tasks'
            '.send_removed_task_notification.delay',
        )
        api_client.token_authenticate(user)

        # act
        response = api_client.post(
            f'/workflows/{workflow.id}/finish',
            data={},
        )
        workflow.refresh_from_db()

        # assert
        assert response.status_code == 204
        expected_user_ids = {(user.id, user.email), (user_4.id, user_4.email)}
        send_removed_task_notification_mock.assert_called_once()
        call_args = send_removed_task_notification_mock.call_args[1]
        assert set(call_args['recipients']) == expected_user_ids
        assert call_args['task_id'] == task_1.id
        assert call_args['account_id'] == task_1.account_id

    def test_finish__already_finished__validation_error(
        self,
        api_client,
        analysis_mock,
    ):

        # arrange
        user = create_test_user()
        workflow = create_test_workflow(
            user=user,
            finalizable=True,
        )
        api_client.token_authenticate(user)

        # act
        api_client.post(
            f'/workflows/{workflow.id}/finish',
            data={},
        )
        response = api_client.post(
            f'/workflows/{workflow.id}/finish',
            data={},
        )
        workflow.refresh_from_db()

        # assert
        assert response.status_code == 400
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['message'] == messages.MSG_PW_0008

    def test_finish__not_finalizable__validation_error(
        self,
        api_client,
        analysis_mock,
    ):

        # arrange
        user = create_test_user()
        workflow = create_test_workflow(
            user=user,
            finalizable=False,
        )
        api_client.token_authenticate(user)

        # act
        response = api_client.post(
            f'/workflows/{workflow.id}/finish',
            data={},
        )
        workflow.refresh_from_db()

        # assert
        assert response.status_code == 400
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['message'] == messages.MSG_PW_0009

    def test_finish__user_can_not_finish_workflow__validation_error(
        self,
        api_client,
        analysis_mock,
    ):

        # arrange
        user = create_test_user()
        workflow = create_test_workflow(
            user=user,
            finalizable=True,
        )
        another_user = create_test_user(
            email='icannotfinishworkflow@pneumatic.app',
            account=user.account,
            is_account_owner=False,
            is_admin=True,
        )
        workflow.members.add(another_user)
        api_client.token_authenticate(another_user)

        # act
        response = api_client.post(
            f'/workflows/{workflow.id}/finish',
            data={},
        )
        workflow.refresh_from_db()

        # assert
        assert response.status_code == 403


def test_finish__not_authenticated__permission_denied(api_client):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner, tasks_count=1)

    # act
    response = api_client.post(
        f'/workflows/{workflow.id}/finish',
        data={},
    )

    # assert
    assert response.status_code == 401


def test_finish__expired_subscription__permission_denied(api_client):

    # arrange
    account = create_test_account(
        plan=BillingPlanType.UNLIMITED,
        plan_expiration=timezone.now() - timedelta(hours=1),
    )
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner, tasks_count=1)
    api_client.token_authenticate(owner)

    # act
    response = api_client.post(
        f'/workflows/{workflow.id}/finish',
        data={},
    )

    # assert
    assert response.status_code == 403


def test_finish__billing_plan__permission_denied(api_client):

    # arrange
    account = create_test_account(plan=None)
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner, tasks_count=1)
    api_client.token_authenticate(owner)

    # act
    response = api_client.post(
        f'/workflows/{workflow.id}/finish',
        data={},
    )

    # assert
    assert response.status_code == 403


def test_finish__not_admin__permission_denied(api_client):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    not_admin = create_test_not_admin(account=account)
    workflow = create_test_workflow(user=owner, tasks_count=1)
    api_client.token_authenticate(not_admin)

    # act
    response = api_client.post(
        f'/workflows/{workflow.id}/finish',
        data={},
    )

    # assert
    assert response.status_code == 403


def test_finish__not_owner__permission_denied(api_client):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    admin = create_test_admin(
        account=account,
        email='admin@test.test',
    )
    workflow = create_test_workflow(user=owner, tasks_count=1)
    api_client.token_authenticate(admin)

    # act
    response = api_client.post(
        f'/workflows/{workflow.id}/finish',
        data={},
    )

    # assert
    assert response.status_code == 403


def test_finish__users_overlimited__permission_denied(api_client):

    # arrange
    account = create_test_account(
        plan=BillingPlanType.PREMIUM,
        max_users=1,
    )
    owner = create_test_owner(account=account)
    create_test_not_admin(account=account)
    account.active_users = 2
    account.save()
    workflow = create_test_workflow(user=owner, tasks_count=1)
    api_client.token_authenticate(owner)

    # act
    response = api_client.post(
        f'/workflows/{workflow.id}/finish',
        data={},
    )

    # assert
    assert response.status_code == 403


def test_finish__not_found__not_found(api_client):

    # arrange
    user = create_test_owner()
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        '/workflows/99999999/finish',
        data={},
    )

    # assert
    assert response.status_code == 404


def test_finish__analytic_ended_called__ok(api_client, mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    template = create_test_template(
        user=owner,
        is_active=True,
        finalizable=True,
    )
    workflow = create_test_workflow(user=owner, template=template)
    api_client.token_authenticate(owner)
    analytic_mock = mocker.patch(
        'src.processes.views.workflow'
        '.AnalyticService.workflows_ended',
    )
    force_complete_mock = mocker.patch(
        'src.processes.views.workflow'
        '.WorkflowActionService.force_complete_workflow',
    )

    # act
    response = api_client.post(
        f'/workflows/{workflow.id}/finish',
        data={},
    )

    # assert
    assert response.status_code == 204
    analytic_mock.assert_called_once()
    force_complete_mock.assert_called_once()
