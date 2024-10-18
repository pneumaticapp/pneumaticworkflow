# pylint:disable=redefined-outer-name
import pytest
from pneumatic_backend.utils.validation import ErrorCode
from pneumatic_backend.processes.messages import workflow as messages
from pneumatic_backend.processes.enums import (
    WorkflowStatus,
    DirectlyStatus,
)
from pneumatic_backend.processes.models import TaskPerformer
from pneumatic_backend.processes.tests.fixtures import (
    create_test_user,
    create_test_workflow,
    create_test_template,
    create_test_account,
    create_test_guest,
)
from pneumatic_backend.authentication.enums import AuthTokenType


pytestmark = pytest.mark.django_db


class TestFinishWorkflow:

    # End workflow

    def test_finish__ok(
        self,
        mocker,
        api_client,
        analytics_mock
    ):

        # arrange
        user = create_test_user()
        workflow = create_test_workflow(
            user=user,
            finalizable=True,
            tasks_count=2
        )
        task_1 = workflow.tasks.get(number=1)
        task_2 = workflow.tasks.get(number=2)
        deactivate_cache_mock = mocker.patch(
            'pneumatic_backend.authentication.services.'
            'GuestJWTAuthService.deactivate_task_guest_cache'
        )
        send_removed_task_notification_mock = mocker.patch(
            'pneumatic_backend.processes.services.websocket.WSSender.'
            'send_removed_task_notification'
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
        analytics_mock.workflows_ended.assert_called_once_with(
            user=user,
            workflow=workflow,
            auth_type=AuthTokenType.USER,
            is_superuser=False
        )
        deactivate_cache_mock.assert_has_calls(
            [
                mocker.call(task_id=task_1.id),
                mocker.call(task_id=task_2.id)
            ]
        )
        send_removed_task_notification_mock.assert_called_once_with(
            task=task_1,
            user_ids=(user.id,)
        )

    def test_finish__legacy_template__ok(
        self,
        mocker,
        analytics_mock,
        api_client
    ):

        # arrange
        user = create_test_user()
        template = create_test_template(
            user=user,
            is_active=True,
            tasks_count=1,
            finalizable=True
        )
        workflow = create_test_workflow(
            user=user,
            template=template,
        )
        api_client.token_authenticate(user)
        api_client.delete(f'/templates/{template.id}')
        mocker.patch(
            'pneumatic_backend.processes.services.websocket.WSSender.'
            'send_removed_task_notification'
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
        analytics_mock.workflows_ended.assert_called_once_with(
            user=user,
            workflow=workflow,
            auth_type=AuthTokenType.USER,
            is_superuser=False
        )

    def test_finish__notification__for_not_completed_only(
        self,
        mocker,
        api_client,
        analytics_mock
    ):

        # arrange
        account = create_test_account()
        user = create_test_user(account=account)
        workflow = create_test_workflow(
            user=user,
            finalizable=True,
            tasks_count=2
        )
        task_1 = workflow.tasks.get(number=1)
        deleted_performer = create_test_user(
            account=account,
            email='deleted@test.test',
            is_account_owner=False
        )
        TaskPerformer.objects.create(
            task_id=task_1.id,
            user_id=deleted_performer.id,
            directly_status=DirectlyStatus.DELETED
        )
        completed_performer = create_test_user(
            account=account,
            email='user_3@test.test',
            is_account_owner=False
        )
        TaskPerformer.objects.create(
            task_id=task_1.id,
            user_id=completed_performer.id,
            is_completed=True
        )
        guest = create_test_guest(account=account)
        TaskPerformer.objects.create(
            task_id=task_1.id,
            user_id=guest.id,
        )

        user_4 = create_test_user(
            account=account,
            email='user_4@test.test',
            is_account_owner=False
        )
        TaskPerformer.objects.create(
            task_id=task_1.id,
            user_id=user_4.id,
        )

        mocker.patch(
            'pneumatic_backend.authentication.services.'
            'GuestJWTAuthService.deactivate_task_guest_cache'
        )
        send_removed_task_notification_mock = mocker.patch(
            'pneumatic_backend.processes.services.websocket.WSSender.'
            'send_removed_task_notification'
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
        send_removed_task_notification_mock.assert_called_once_with(
            task=task_1,
            user_ids=(user.id, user_4.id)
        )

    def test_finish__already_finished__validation_error(
        self,
        api_client,
        analytics_mock
    ):

        # arrange
        user = create_test_user()
        workflow = create_test_workflow(
            user=user,
            finalizable=True
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
        analytics_mock
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
        analytics_mock
    ):

        # arrange
        user = create_test_user()
        workflow = create_test_workflow(
            user=user,
            finalizable=True
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
