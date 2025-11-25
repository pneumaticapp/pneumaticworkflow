from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from src.accounts.enums import (
    BillingPlanType,
    UserStatus,
)
from src.authentication.enums import AuthTokenType
from src.authentication.tokens import GuestToken
from src.processes.enums import (
    DirectlyStatus,
    OwnerType,
    PerformerType,
    TaskStatus,
    WorkflowEventType,
    WorkflowStatus,
)
from src.processes.messages import workflow as messages
from src.processes.models.templates.owner import TemplateOwner
from src.processes.models.workflows.event import WorkflowEvent
from src.processes.models.workflows.task import TaskPerformer
from src.processes.serializers.workflows.events import (
    TaskEventJsonSerializer,
)
from src.processes.services.tasks.base import (
    BasePerformerService2,
    BasePerformersService,
)
from src.processes.services.tasks.exceptions import (
    GroupPerformerServiceException,
    PerformersServiceException,
)
from src.processes.services.tasks.groups import (
    GroupPerformerService,
)
from src.processes.services.tasks.guests import (
    GuestPerformersService,
)
from src.processes.services.tasks.performers import (
    TaskPerformersService,
)
from src.processes.services.workflow_action import (
    WorkflowActionService,
)
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_admin,
    create_test_group,
    create_test_guest,
    create_test_template,
    create_test_user,
    create_test_workflow,
)

UserModel = get_user_model()
pytestmark = pytest.mark.django_db


class TestBasePerformersService:

    def test_get_valid_deleted_performer__guest_last_performer__ok(self):

        # arrange
        template_owner = create_test_user(is_account_owner=True)
        guest = create_test_guest(account=template_owner.account)
        workflow = create_test_workflow(template_owner)
        task = workflow.tasks.get(number=1)
        TaskPerformer.objects.create(
            task_id=task.id,
            user_id=guest.id,
        )

        # act
        task_performer = (
            BasePerformersService._get_valid_deleted_task_performer(
                task=task,
                user=template_owner,
            )
        )
        # assert
        assert task_performer.user_id == template_owner.id

    def test_validate__request_user_is_performer__ok(self, mocker):

        # arrange
        account = create_test_account(plan=BillingPlanType.PREMIUM)
        template_owner = create_test_user(
            account=account,
            is_account_owner=True,
            email='owner@test.test',
        )
        request_user = create_test_user(
            account=account,
            is_account_owner=False,
            email='test@test.test',
        )
        user_performer = create_test_user(
            account=account,
            is_account_owner=False,
            email='performer@test.test',
        )
        template = create_test_template(
            user=template_owner,
            is_active=True,
            tasks_count=1,
        )
        template_task = template.tasks.first()
        template_task.add_raw_performer(request_user)
        workflow = create_test_workflow(template_owner, template=template)
        task = workflow.tasks.get(number=1)
        mocker.patch(
            'src.processes.services.tasks.base.'
            'BasePerformersService._get_user_for_create',
            return_value=user_performer,
        )
        current_url = '/page'
        is_superuser = False
        auth_type = AuthTokenType.USER

        # act
        BasePerformersService.create_performer(
            request_user=request_user,
            user_key=user_performer.id,
            task=task,
            current_url=current_url,
            auth_type=auth_type,
            is_superuser=is_superuser,
        )

        # assert
        assert task.taskperformer_set.get(
            user_id=user_performer.id,
        ).directly_status == DirectlyStatus.CREATED

    def test_validate__request_user_is_account_owner__ok(self, mocker):

        # arrange
        account = create_test_account()
        template_owner = create_test_user(
            account=account,
            is_account_owner=True,
            email='owner@test.test',
        )
        request_user = create_test_user(
            account=account,
            is_account_owner=True,
            email='account-owner@test.test',
        )
        user_performer = create_test_user(
            account=account,
            is_account_owner=False,
            email='performer@test.test',
        )
        template = create_test_template(
            user=template_owner,
            is_active=True,
            tasks_count=1,
        )
        TemplateOwner.objects.filter(
            template=template,
            type=OwnerType.USER,
            user_id=request_user.id,
        ).delete()
        workflow = create_test_workflow(template_owner, template=template)
        task = workflow.tasks.get(number=1)
        mocker.patch(
            'src.processes.services.tasks.base.'
            'BasePerformersService._get_user_for_create',
            return_value=user_performer,
        )
        current_url = '/page'
        is_superuser = False
        auth_type = AuthTokenType.USER

        # act
        BasePerformersService.create_performer(
            request_user=request_user,
            user_key=user_performer.id,
            task=task,
            auth_type=auth_type,
            current_url=current_url,
            is_superuser=is_superuser,
        )

        # assert
        assert task.taskperformer_set.get(
            user_id=user_performer.id,
        ).directly_status == DirectlyStatus.CREATED

    @pytest.mark.parametrize('is_legacy_template', (True, False))
    def test_validate__request_user_not_template_owner__exception(
        self,
        is_legacy_template,
    ):

        # arrange
        account = create_test_account(plan=BillingPlanType.PREMIUM)
        user = create_test_user(
            account=account,
            is_account_owner=False,
        )
        user_performer = create_test_user(
            account=account,
            email='performer@test.test',
            is_account_owner=False,
        )
        workflow = create_test_workflow(user_performer)
        workflow.is_legacy_template = is_legacy_template
        workflow.save()
        task = workflow.tasks.get(number=1)
        current_url = '/page'
        is_superuser = False
        auth_type = AuthTokenType.USER

        # act
        with pytest.raises(PerformersServiceException) as ex:
            BasePerformersService.create_performer(
                request_user=user,
                user_key=user_performer.id,
                task=task,
                auth_type=auth_type,
                current_url=current_url,
                is_superuser=is_superuser,
            )

        # assert
        assert ex.value.message == messages.MSG_PW_0021

    def test_validate__workflow_ended__exception(self):

        # arrange
        account = create_test_account()
        request_user = create_test_user(
            account=account,
            email='test@test.test',
            is_account_owner=False,
        )
        user_performer = create_test_user(
            account=account,
            email='performer@test.test',
            is_account_owner=False,
        )
        workflow = create_test_workflow(request_user)
        workflow.status = WorkflowStatus.DONE
        workflow.save()
        task = workflow.tasks.get(number=1)

        # act
        with pytest.raises(PerformersServiceException) as ex:
            BasePerformersService._validate(
                request_user=user_performer,
                task=task,
            )

        # assert
        assert ex.value.message == messages.MSG_PW_0017

    def test_validate__not_active_task__raise_exception(
        self,
        mocker,
        api_client,
    ):

        # arrange
        account = create_test_account()
        template_owner = create_test_user(
            account=account,
            email='test@test.test',
            is_account_owner=True,
        )
        user_performer = create_test_user(
            account=account,
            email='performer@test.test',
            is_account_owner=False,
        )
        mocker.patch(
            'src.processes.services.tasks.performers.'
            'send_new_task_notification.delay',
        )
        workflow = create_test_workflow(template_owner, tasks_count=3)
        task_1 = workflow.tasks.get(number=1)
        api_client.token_authenticate(template_owner)
        response_complete = api_client.post(f'/v2/tasks/{task_1.id}/complete')
        workflow.refresh_from_db()

        # act
        with pytest.raises(PerformersServiceException) as ex_prev:
            BasePerformersService._validate(
                request_user=user_performer,
                task=workflow.tasks.get(number=1),
            )
        with pytest.raises(PerformersServiceException) as ex_next:
            BasePerformersService._validate(
                request_user=user_performer,
                task=workflow.tasks.get(number=3),
            )

        # assert
        assert response_complete.status_code == 200
        assert ex_prev.value.message == messages.MSG_PW_0018
        assert ex_next.value.message == messages.MSG_PW_0018
        task_1.refresh_from_db()
        assert task_1.is_completed
        task_2 = workflow.tasks.get(number=2)
        assert task_2.is_active

    def test_validate__request_user_not_performer_not_owner__exception(self):

        # arrange
        account = create_test_account(plan=BillingPlanType.PREMIUM)
        template_owner = create_test_user(
            account=account,
            email='owner@test.test',
            is_account_owner=False,
        )
        request_user = create_test_user(
            account=account,
            email='test@test.test',
            is_account_owner=False,
        )
        user_performer = create_test_user(
            account=account,
            email='performer@test.test',
            is_account_owner=False,
        )
        workflow = create_test_workflow(template_owner)
        task = workflow.tasks.get(number=1)
        current_url = '/page'
        is_superuser = False
        auth_type = AuthTokenType.USER

        # act
        with pytest.raises(PerformersServiceException) as ex:
            BasePerformersService.create_performer(
                request_user=request_user,
                user_key=user_performer.id,
                task=task,
                auth_type=auth_type,
                current_url=current_url,
                is_superuser=is_superuser,
            )

        # assert
        assert ex.value.message == messages.MSG_PW_0021

    def test_validate__request_user_deleted_performer__exception(self):

        # arrange
        account = create_test_account(plan=BillingPlanType.PREMIUM)
        template_owner = create_test_user(
            account=account,
            email='owner@test.test',
            is_account_owner=False,
        )
        request_user = create_test_user(
            account=account,
            email='test@test.test',
            is_account_owner=False,
        )
        user_performer = create_test_user(
            account=account,
            email='performer@test.test',
            is_account_owner=False,
        )
        workflow = create_test_workflow(template_owner)
        task = workflow.tasks.get(number=1)
        TaskPerformer.objects.create(
            task_id=task.id,
            user_id=request_user.id,
            directly_status=DirectlyStatus.DELETED,
        )
        current_url = '/page'
        is_superuser = False
        auth_type = AuthTokenType.USER

        # act
        with pytest.raises(PerformersServiceException) as ex:
            BasePerformersService.create_performer(
                request_user=request_user,
                user_key=user_performer.id,
                task=task,
                auth_type=auth_type,
                current_url=current_url,
                is_superuser=is_superuser,
            )

        # assert
        assert ex.value.message == messages.MSG_PW_0021

    def test_create_performer__ok(self, mocker):

        # arrange
        template_owner = create_test_user(is_account_owner=False)
        user_performer = create_test_user(
            account=template_owner.account,
            email='performer@test.test',
            is_account_owner=False,
        )
        workflow = create_test_workflow(template_owner)
        task = workflow.tasks.get(number=1)
        validate_mock = mocker.patch(
            'src.processes.services.tasks.base.'
            'BasePerformersService._validate',
        )
        validate_create_mock = mocker.patch(
            'src.processes.services.tasks.base.'
            'BasePerformersService._validate_create',
        )
        create_actions_mock = mocker.patch(
            'src.processes.services.tasks.base.'
            'BasePerformersService._create_actions',
        )
        get_user_for_create_mock = mocker.patch(
            'src.processes.services.tasks.base.'
            'BasePerformersService._get_user_for_create',
            return_value=user_performer,
        )
        current_url = '/page'
        is_superuser = False
        auth_type = AuthTokenType.USER

        # act
        user, task_performer = BasePerformersService.create_performer(
            request_user=template_owner,
            user_key=user_performer.id,
            task=task,
            auth_type=auth_type,
            current_url=current_url,
            is_superuser=is_superuser,
        )

        # assert
        assert user.id == user_performer.id
        assert task_performer.directly_status == DirectlyStatus.CREATED
        validate_mock.assert_called_once_with(
            task=task,
            request_user=template_owner,
        )
        validate_create_mock.assert_called_once_with(
            task=task,
            request_user=template_owner,
        )
        create_actions_mock.assert_called_once_with(
            task=task,
            request_user=template_owner,
            user=user_performer,
            current_url=current_url,
            is_superuser=is_superuser,
            auth_type=auth_type,
        )
        get_user_for_create_mock.assert_called_once_with(
            user_key=user_performer.id,
            account_id=template_owner.account_id,
        )

    def test_create_performer__already_created__skip(self, mocker):

        # arrange
        template_owner = create_test_user(is_account_owner=False)
        user_performer = create_test_user(
            account=template_owner.account,
            email='performer@test.test',
            is_account_owner=False,
        )
        workflow = create_test_workflow(template_owner)
        task = workflow.tasks.get(number=1)
        TaskPerformer.objects.create(
            task_id=task.id,
            user_id=user_performer.id,
            directly_status=DirectlyStatus.CREATED,
        )
        mocker.patch(
            'src.processes.services.tasks.base.'
            'BasePerformersService._validate',
        )
        mocker.patch(
            'src.processes.services.tasks.base.'
            'BasePerformersService._validate_create',
        )
        create_actions_mock = mocker.patch(
            'src.processes.services.tasks.base.'
            'BasePerformersService._create_actions',
        )
        mocker.patch(
            'src.processes.services.tasks.base.'
            'BasePerformersService._get_user_for_create',
            return_value=user_performer,
        )
        current_url = '/page'
        is_superuser = False
        auth_type = AuthTokenType.USER

        # act
        user, task_performer = BasePerformersService.create_performer(
            request_user=template_owner,
            user_key=user_performer.id,
            task=task,
            auth_type=auth_type,
            current_url=current_url,
            is_superuser=is_superuser,
        )

        # assert
        assert user.id == user_performer.id
        assert task_performer.directly_status == DirectlyStatus.CREATED
        create_actions_mock.assert_not_called()

    def test_create_performer__existent_with_no_status__skip(self, mocker):

        # arrange
        template_owner = create_test_user(is_account_owner=False)
        user_performer = create_test_user(
            account=template_owner.account,
            email='performer@test.test',
            is_account_owner=False,
        )
        workflow = create_test_workflow(template_owner)
        task = workflow.tasks.get(number=1)
        TaskPerformer.objects.create(
            task_id=task.id,
            user_id=user_performer.id,
            directly_status=DirectlyStatus.NO_STATUS,
        )
        mocker.patch(
            'src.processes.services.tasks.base.'
            'BasePerformersService._validate',
        )
        mocker.patch(
            'src.processes.services.tasks.base.'
            'BasePerformersService._validate_create',
        )
        create_actions_mock = mocker.patch(
            'src.processes.services.tasks.base.'
            'BasePerformersService._create_actions',
        )
        mocker.patch(
            'src.processes.services.tasks.base.'
            'BasePerformersService._get_user_for_create',
            return_value=user_performer,
        )
        current_url = '/page'
        is_superuser = False
        auth_type = AuthTokenType.USER

        # act
        user, task_performer = BasePerformersService.create_performer(
            request_user=template_owner,
            user_key=user_performer.id,
            task=task,
            auth_type=auth_type,
            current_url=current_url,
            is_superuser=is_superuser,
        )

        # assert
        assert user.id == user_performer.id
        assert task_performer.directly_status == DirectlyStatus.NO_STATUS
        create_actions_mock.assert_not_called()

    def test_create_performer__restore_deleted__ok(self, mocker):

        # arrange
        template_owner = create_test_user(is_account_owner=False)
        user_performer = create_test_user(
            account=template_owner.account,
            email='performer@test.test',
            is_account_owner=False,
        )
        workflow = create_test_workflow(template_owner)
        task = workflow.tasks.get(number=1)
        TaskPerformer.objects.create(
            task_id=task.id,
            user_id=user_performer.id,
            directly_status=DirectlyStatus.DELETED,
        )
        mocker.patch(
            'src.processes.services.tasks.base.'
            'BasePerformersService._validate',
        )
        mocker.patch(
            'src.processes.services.tasks.base.'
            'BasePerformersService._validate_create',
        )
        create_actions_mock = mocker.patch(
            'src.processes.services.tasks.base.'
            'BasePerformersService._create_actions',
        )
        mocker.patch(
            'src.processes.services.tasks.base.'
            'BasePerformersService._get_user_for_create',
            return_value=user_performer,
        )
        current_url = '/page'
        is_superuser = False
        auth_type = AuthTokenType.USER

        # act
        user, task_performer = BasePerformersService.create_performer(
            request_user=template_owner,
            user_key=user_performer.id,
            task=task,
            auth_type=auth_type,
            current_url=current_url,
            is_superuser=is_superuser,
        )

        # assert
        assert user.id == user_performer.id
        assert task_performer.directly_status == DirectlyStatus.CREATED
        create_actions_mock.assert_called_once_with(
            task=task,
            request_user=template_owner,
            user=user_performer,
            current_url=current_url,
            is_superuser=is_superuser,
            auth_type=auth_type,
        )

    def test_delete_performer__ok(self, mocker):

        # arrange
        template_owner = create_test_user(is_account_owner=False)
        user_performer = create_test_user(
            account=template_owner.account,
            email='performer@test.test',
            is_account_owner=False,
        )
        workflow = create_test_workflow(template_owner)
        task = workflow.tasks.get(number=1)
        TaskPerformer.objects.create(
            task_id=task.id,
            user_id=user_performer.id,
        )
        validate_mock = mocker.patch(
            'src.processes.services.tasks.base.'
            'BasePerformersService._validate',
        )
        delete_actions_mock = mocker.patch(
            'src.processes.services.tasks.base.'
            'BasePerformersService._delete_actions',
        )
        get_user_for_delete_mock = mocker.patch(
            'src.processes.services.tasks.base.'
            'BasePerformersService._get_user_for_delete',
            return_value=user_performer,
        )
        is_superuser = False
        auth_type = AuthTokenType.USER

        # act
        BasePerformersService.delete_performer(
            request_user=template_owner,
            user_key=user_performer.id,
            task=task,
            auth_type=auth_type,
            is_superuser=is_superuser,
        )

        # assert
        assert task.taskperformer_set.get(
            user_id=user_performer.id,
        ).directly_status == DirectlyStatus.DELETED
        validate_mock.assert_called_once_with(
            task=task,
            request_user=template_owner,
        )
        get_user_for_delete_mock.assert_called_once_with(
            user_key=user_performer.id,
            account_id=template_owner.account_id,
        )
        delete_actions_mock.assert_called_once_with(
            task=task,
            request_user=template_owner,
            user=user_performer,
            is_superuser=is_superuser,
            auth_type=auth_type,
        )

    def test_delete_performer__previously_created__ok(self, mocker):

        # arrange
        template_owner = create_test_user(is_account_owner=False)
        user_performer = create_test_user(
            account=template_owner.account,
            email='performer@test.test',
            is_account_owner=False,
        )
        workflow = create_test_workflow(template_owner)
        task = workflow.tasks.get(number=1)
        TaskPerformer.objects.create(
            task_id=task.id,
            user_id=user_performer.id,
            directly_status=DirectlyStatus.CREATED,
        )
        mocker.patch(
            'src.processes.services.tasks.base.'
            'BasePerformersService._validate',
        )
        delete_actions_mock = mocker.patch(
            'src.processes.services.tasks.base.'
            'BasePerformersService._delete_actions',
        )
        mocker.patch(
            'src.processes.services.tasks.base.'
            'BasePerformersService._get_user_for_delete',
            return_value=user_performer,
        )
        is_superuser = False
        auth_type = AuthTokenType.USER

        # act
        BasePerformersService.delete_performer(
            request_user=template_owner,
            user_key=user_performer.id,
            task=task,
            auth_type=auth_type,
            is_superuser=is_superuser,
        )

        # assert
        assert task.taskperformer_set.get(
            user_id=user_performer.id,
        ).directly_status == DirectlyStatus.DELETED
        delete_actions_mock.assert_called_once_with(
            task=task,
            request_user=template_owner,
            user=user_performer,
            is_superuser=is_superuser,
            auth_type=auth_type,
        )

    def test_delete_performer__not_existent__skip(self, mocker):

        # arrange
        template_owner = create_test_user(is_account_owner=False)
        user_performer = create_test_user(
            account=template_owner.account,
            email='performer@test.test',
            is_account_owner=False,
        )
        workflow = create_test_workflow(template_owner)
        task = workflow.tasks.get(number=1)
        mocker.patch(
            'src.processes.services.tasks.base.'
            'BasePerformersService._validate',
        )
        delete_actions_mock = mocker.patch(
            'src.processes.services.tasks.base.'
            'BasePerformersService._delete_actions',
        )
        mocker.patch(
            'src.processes.services.tasks.base.'
            'BasePerformersService._get_user_for_delete',
            return_value=user_performer,
        )
        is_superuser = False
        auth_type = AuthTokenType.USER

        # act
        BasePerformersService.delete_performer(
            request_user=template_owner,
            user_key=user_performer.id,
            task=task,
            auth_type=auth_type,
            is_superuser=is_superuser,
        )

        # assert
        assert not task.taskperformer_set.filter(
            user_id=user_performer.id,
        ).exists()
        delete_actions_mock.assert_not_called()

    def test_delete_performer__yourself__ok(self, mocker):

        # arrange
        request_user = create_test_user(is_account_owner=False)
        user_performer = create_test_user(
            account=request_user.account,
            email='performer@test.test',
            is_account_owner=False,
        )
        workflow = create_test_workflow(request_user)
        task = workflow.tasks.get(number=1)
        TaskPerformer.objects.create(
            task_id=task.id,
            user_id=user_performer.id,
            directly_status=DirectlyStatus.NO_STATUS,
        )

        validate_mock = mocker.patch(
            'src.processes.services.tasks.base.'
            'BasePerformersService._validate',
        )
        delete_actions_mock = mocker.patch(
            'src.processes.services.tasks.base.'
            'BasePerformersService._delete_actions',
        )
        mocker.patch(
            'src.processes.services.tasks.base.'
            'BasePerformersService._get_user_for_delete',
            return_value=request_user,
        )
        is_superuser = False
        auth_type = AuthTokenType.USER

        # act
        BasePerformersService.delete_performer(
            request_user=request_user,
            user_key=request_user.id,
            task=task,
            auth_type=auth_type,
            is_superuser=is_superuser,
        )

        # assert
        assert task.taskperformer_set.get(
            user_id=request_user.id,
        ).directly_status == DirectlyStatus.DELETED
        validate_mock.assert_called_once_with(
            task=task,
            request_user=request_user,
        )
        delete_actions_mock.assert_called_once_with(
            task=task,
            request_user=request_user,
            user=request_user,
            is_superuser=is_superuser,
            auth_type=auth_type,
        )

    def test_delete_performer__last_performer__exception(self, mocker):

        # arrange
        request_user = create_test_user(is_account_owner=False)
        workflow = create_test_workflow(request_user)
        task = workflow.tasks.get(number=1)
        mocker.patch(
            'src.processes.services.tasks.base.'
            'BasePerformersService._validate',
        )
        delete_actions_mock = mocker.patch(
            'src.processes.services.tasks.base.'
            'BasePerformersService._delete_actions',
        )
        mocker.patch(
            'src.processes.services.tasks.base.'
            'BasePerformersService._get_user_for_delete',
            return_value=request_user,
        )
        is_superuser = False
        auth_type = AuthTokenType.USER

        # act
        with pytest.raises(PerformersServiceException) as ex:
            BasePerformersService.delete_performer(
                request_user=request_user,
                user_key=request_user.id,
                task=task,
                auth_type=auth_type,
                is_superuser=is_superuser,
            )

        # assert
        assert ex.value.message == messages.MSG_PW_0016
        delete_actions_mock.assert_not_called()


class TestTaskPerformersService:

    def test_get_user_for_create__active__ok(self, api_client):

        # arrange
        account_owner = create_test_user(is_account_owner=True)
        user_performer = create_test_user(
            account=account_owner.account,
            email='test@test.test',
            is_account_owner=False,
        )

        # act
        user = TaskPerformersService._get_user_for_create(
            user_key=user_performer.id,
            account_id=account_owner.account_id,
        )

        # assert
        assert user.id == user_performer.id

    def test_get_user_for_create__invited__ok(
        self,
        api_client,
    ):

        # arrange
        account_owner = create_test_user(is_account_owner=True)
        api_client.token_authenticate(account_owner)
        invited_email = 'invited@test.test'
        api_client.post(
            '/accounts/invites',
            data={
                'users': [
                    {
                        'email': invited_email,
                        'type': 'email',
                    },
                ],
            },
        )
        invited_user_performer = UserModel.objects.on_account(
            account_owner.account.id,
        ).get(email=invited_email)

        # act
        user = TaskPerformersService._get_user_for_create(
            user_key=invited_user_performer.id,
            account_id=account_owner.account_id,
        )

        # assert
        assert user.id == invited_user_performer.id

    def test_get_user_for_create__transferred_user__ok(
        self,
        api_client,
    ):

        # arrange
        account_1 = create_test_account(name='transfer from')
        account_2 = create_test_account(name='transfer to')
        user_to_transfer = create_test_user(
            account=account_1,
            email='transferred@test.test',
            is_account_owner=True,
        )
        account_2_owner = create_test_user(
            account=account_2,
            is_account_owner=True,
        )
        api_client.token_authenticate(account_2_owner)
        api_client.post(
            '/accounts/invites',
            data={
                'users': [
                    {
                        'email': user_to_transfer.email,
                        'type': 'email',
                    },
                ],
            },
        )
        invited_user = UserModel.objects.on_account(
            account_2.id,
        ).get(email=user_to_transfer.email)

        # act
        user = TaskPerformersService._get_user_for_create(
            user_key=invited_user.id,
            account_id=account_2_owner.account_id,
        )

        # assert
        assert user.id == invited_user.id

    def test_get_user_for_create__inactive__raise_exception(self, api_client):

        # arrange
        account_owner = create_test_user(is_account_owner=True)
        inactive_user = create_test_user(
            account=account_owner.account,
            email='inactive@test.test',
            status=UserStatus.INACTIVE,
            is_account_owner=False,
        )
        api_client.token_authenticate(account_owner)

        # act
        with pytest.raises(PerformersServiceException) as ex:
            TaskPerformersService._get_user_for_create(
                user_key=inactive_user.id,
                account_id=account_owner.account_id,
            )

        # assert
        assert ex.value.message == messages.MSG_PW_0014

    def test_get_user_for_create__guest__raise_exception(self, api_client):

        # arrange
        account_owner = create_test_user(is_account_owner=True)
        guest_user = create_test_guest(
            account=account_owner.account,
            email='inactive@test.test',
        )
        api_client.token_authenticate(account_owner)

        # act
        with pytest.raises(PerformersServiceException) as ex:
            TaskPerformersService._get_user_for_create(
                user_key=guest_user.id,
                account_id=account_owner.account_id,
            )

        # assert
        assert ex.value.message == messages.MSG_PW_0014

    def test_get_user_for_create__is_not_account_user__raise_exception(
        self,
        api_client,
    ):

        # arrange
        account_owner = create_test_user(is_account_owner=True)
        user_performer = create_test_user(
            email='performer@test.test',
            is_account_owner=False,
        )

        # act
        with pytest.raises(PerformersServiceException) as ex:
            TaskPerformersService._get_user_for_create(
                user_key=user_performer.id,
                account_id=account_owner.account_id,
            )

        # assert
        assert ex.value.message == messages.MSG_PW_0014

    def test_get_user_for_delete__active__ok(self, api_client):

        # arrange
        account_owner = create_test_user(is_account_owner=True)
        user_performer = create_test_user(
            account=account_owner.account,
            email='test@test.test',
            is_account_owner=False,
        )

        # act
        user = TaskPerformersService._get_user_for_delete(
            user_key=user_performer.id,
            account_id=account_owner.account_id,
        )

        # assert
        assert user.id == user_performer.id

    def test_get_user_for_delete__invited__ok(
        self,
        api_client,
    ):

        # arrange
        account_owner = create_test_user(is_account_owner=True)
        api_client.token_authenticate(account_owner)
        invited_email = 'invited@test.test'
        api_client.post(
            '/accounts/invites',
            data={
                'users': [
                    {
                        'email': invited_email,
                        'type': 'email',
                    },
                ],
            },
        )
        invited_user_performer = UserModel.objects.on_account(
            account_owner.account.id,
        ).get(email=invited_email)

        # act
        user = TaskPerformersService._get_user_for_delete(
            user_key=invited_user_performer.id,
            account_id=account_owner.account_id,
        )

        # assert
        assert user.id == invited_user_performer.id

    def test_get_user_for_delete__transferred_user__ok(
        self,
        api_client,
    ):

        # arrange
        account_1 = create_test_account(name='transfer from')
        account_2 = create_test_account(name='transfer to')
        user_to_transfer = create_test_user(
            account=account_1,
            email='transferred@test.test',
            is_account_owner=False,
        )
        account_2_owner = create_test_user(
            account=account_2,
            is_account_owner=True,
        )
        api_client.token_authenticate(account_2_owner)
        api_client.post(
            '/accounts/invites',
            data={
                'users': [
                    {
                        'email': user_to_transfer.email,
                        'type': 'email',
                    },
                ],
            },
        )

        invited_user = UserModel.objects.on_account(
            account_2.id,
        ).get(email=user_to_transfer.email)

        # act
        user = TaskPerformersService._get_user_for_delete(
            user_key=invited_user.id,
            account_id=account_2_owner.account_id,
        )

        # assert
        assert user.id == invited_user.id

    def test_get_user_for_delete__inactive__ok(self, api_client):

        # arrange
        account_owner = create_test_user(is_account_owner=True)
        inactive_user = create_test_user(
            account=account_owner.account,
            email='inactive@test.test',
            status=UserStatus.INACTIVE,
            is_account_owner=False,
        )
        api_client.token_authenticate(account_owner)

        # act
        user = TaskPerformersService._get_user_for_delete(
            user_key=inactive_user.id,
            account_id=account_owner.account_id,
        )

        # assert
        assert user.id == inactive_user.id

    def test_get_user_for_delete__guest__raise_exception(self, api_client):

        # arrange
        account_owner = create_test_user(is_account_owner=True)
        guest_user = create_test_guest(
            account=account_owner.account,
            email='inactive@test.test',
        )
        api_client.token_authenticate(account_owner)

        # act
        with pytest.raises(PerformersServiceException) as ex:
            TaskPerformersService._get_user_for_delete(
                user_key=guest_user.id,
                account_id=account_owner.account_id,
            )

        # assert
        assert ex.value.message == messages.MSG_PW_0014

    def test_get_user_for_delete__is_not_account_user__raise_exception(
        self,
        api_client,
    ):

        # arrange
        account_owner = create_test_user(is_account_owner=True)
        user_performer = create_test_user(
            email='performer@test.test',
            is_account_owner=False,
        )

        # act
        with pytest.raises(PerformersServiceException) as ex:
            TaskPerformersService._get_user_for_delete(
                user_key=user_performer.id,
                account_id=account_owner.account_id,
            )

        # assert
        assert ex.value.message == messages.MSG_PW_0014

    def test_create_actions__ok(self, mocker):

        # arrange
        logo_lg = 'https://some.com/image.png'
        account = create_test_account(logo_lg=logo_lg, log_api_requests=True)
        create_test_user(
            account=account,
            is_account_owner=True,
            email='owner@test.test',
        )
        photo = 'http://image.com/avatar.png'
        request_user = create_test_user(
            account=account,
            photo=photo,
            is_account_owner=False,
        )
        user_performer = create_test_user(
            account=account,
            email='performer@test.test',
            is_account_owner=False,
        )
        workflow = create_test_workflow(request_user)
        task = workflow.tasks.get(number=1)
        task.due_date = timezone.now() + timedelta(hours=1)
        task.save(update_fields=['due_date'])
        send_new_task_websocket_mock = mocker.patch(
            'src.notifications.tasks'
            '.send_new_task_websocket.delay',
        )
        send_new_task_notification_mock = mocker.patch(
            'src.processes.services.tasks.performers.'
            'send_new_task_notification.delay',
        )
        is_superuser = False
        auth_type = AuthTokenType.USER

        # act
        TaskPerformersService._create_actions(
            request_user=request_user,
            user=user_performer,
            task=task,
            auth_type=auth_type,
            is_superuser=is_superuser,
        )

        # assert
        assert user_performer in workflow.members.all()
        send_new_task_websocket_mock.assert_not_called()
        send_new_task_notification_mock.assert_called_once_with(
            logging=account.log_api_requests,
            account_id=account.id,
            recipients=[(
                user_performer.id,
                user_performer.email,
                user_performer.is_new_tasks_subscriber,
            )],
            task_id=task.id,
            task_name=task.name,
            task_description=task.description,
            workflow_name=workflow.name,
            template_name=workflow.get_template_name(),
            workflow_starter_name=request_user.name,
            workflow_starter_photo=photo,
            due_date_timestamp=task.due_date.timestamp(),
            logo_lg=logo_lg,
            is_returned=False,
        )
        assert WorkflowEvent.objects.filter(
            workflow=workflow,
            account=request_user.account,
            type=WorkflowEventType.TASK_PERFORMER_CREATED,
            task_json=TaskEventJsonSerializer(
                instance=task,
                context={
                    'event_type': WorkflowEventType.TASK_PERFORMER_CREATED,
                },
            ).data,
        ).count() == 1

    def test_create_actions__user_in_group__not_send(self, mocker):

        # arrange
        logo_lg = 'https://some.com/image.png'
        account = create_test_account(logo_lg=logo_lg, log_api_requests=True)
        create_test_user(
            account=account,
            is_account_owner=True,
            email='owner@test.test',
        )
        photo = 'http://image.com/avatar.png'
        request_user = create_test_user(
            account=account,
            photo=photo,
            is_account_owner=False,
        )
        user_performer = create_test_user(
            account=account,
            email='performer@test.test',
            is_account_owner=False,
        )
        workflow = create_test_workflow(request_user)
        task = workflow.tasks.get(number=1)
        task.due_date = timezone.now() + timedelta(hours=1)
        task.save(update_fields=['due_date'])
        group = create_test_group(account, users=[user_performer])
        TaskPerformer.objects.create(
            task_id=task.id,
            type=PerformerType.GROUP,
            group_id=group.id,
        )
        send_new_task_websocket_mock = mocker.patch(
            'src.notifications.tasks'
            '.send_new_task_websocket.delay',
        )
        send_new_task_notification_mock = mocker.patch(
            'src.processes.services.tasks.performers.'
            'send_new_task_notification.delay',
        )
        is_superuser = False
        auth_type = AuthTokenType.USER

        # act
        TaskPerformersService._create_actions(
            request_user=request_user,
            user=user_performer,
            task=task,
            auth_type=auth_type,
            is_superuser=is_superuser,
        )

        # assert
        assert user_performer in workflow.members.all()
        send_new_task_websocket_mock.assert_not_called()
        send_new_task_notification_mock.assert_not_called()
        assert WorkflowEvent.objects.filter(
            workflow=workflow,
            account=request_user.account,
            type=WorkflowEventType.TASK_PERFORMER_CREATED,
            task_json=TaskEventJsonSerializer(
                instance=task,
                context={
                    'event_type': WorkflowEventType.TASK_PERFORMER_CREATED,
                },
            ).data,
        ).count() == 1

    def test_create_actions__add_yourself__not_send_email(self, mocker):

        # arrange
        account = create_test_account()
        user = create_test_user(
            account=account,
            is_account_owner=False,
        )
        workflow = create_test_workflow(user=user, tasks_count=1)
        task = workflow.tasks.get(number=1)
        performer_created_event_mock = mocker.patch(
            'src.processes.services.events.'
            'WorkflowEventService.performer_created_event',
        )
        send_new_task_websocket_mock = mocker.patch(
            'src.notifications.tasks'
            '.send_new_task_websocket.delay',
        )
        send_new_task_notification_mock = mocker.patch(
            'src.processes.services.tasks.performers.'
            'send_new_task_notification.delay',
        )
        is_superuser = False
        auth_type = AuthTokenType.USER

        # act
        TaskPerformersService._create_actions(
            request_user=user,
            user=user,
            task=task,
            auth_type=auth_type,
            is_superuser=is_superuser,
        )

        # assert
        performer_created_event_mock.assert_called_once_with(
            user=user,
            task=task,
            performer=user,
        )
        send_new_task_websocket_mock.assert_called_once_with(
            task_id=task.id,
            recipients=[(user.id, user.email, user.is_new_tasks_subscriber)],
            account_id=account.id,
            logging=account.log_api_requests,
        )
        send_new_task_notification_mock.assert_not_called()

    def test_create_actions__legacy_workflow__ok(self, mocker):

        # arrange
        account = create_test_account()
        user = create_test_user(
            account=account,
            is_account_owner=False,
        )
        user_performer = create_test_user(
            is_account_owner=False,
            account=account,
            email='performer@test.test',
        )
        workflow = create_test_workflow(user=user, tasks_count=1)
        legacy_template_name = 'Legacy'
        workflow.template.delete()
        workflow.legacy_template_name = legacy_template_name
        workflow.is_legacy_template = True
        workflow.save()
        task = workflow.tasks.get(number=1)
        send_new_task_websocket_mock = mocker.patch(
            'src.notifications.tasks'
            '.send_new_task_websocket.delay',
        )
        send_new_task_notification_mock = mocker.patch(
            'src.processes.services.tasks.performers.'
            'send_new_task_notification.delay',
        )
        is_superuser = False
        auth_type = AuthTokenType.USER

        # act
        TaskPerformersService._create_actions(
            request_user=user,
            user=user_performer,
            task=task,
            auth_type=auth_type,
            is_superuser=is_superuser,
        )

        # assert
        send_new_task_websocket_mock.assert_not_called()
        send_new_task_notification_mock.assert_called_once_with(
            logging=account.log_api_requests,
            account_id=account.id,
            recipients=[(
                user_performer.id,
                user_performer.email,
                user_performer.is_new_tasks_subscriber,
            )],
            task_id=task.id,
            task_name=task.name,
            task_description=task.description,
            workflow_name=workflow.name,
            template_name=workflow.get_template_name(),
            workflow_starter_name=user.name,
            workflow_starter_photo=None,
            due_date_timestamp=None,
            logo_lg=None,
            is_returned=False,
        )

    def test_create_actions__external_workflow__ok(self, mocker):

        # arrange
        account = create_test_account()
        user = create_test_user(
            account=account,
            is_account_owner=False,
        )
        user_performer = create_test_user(
            is_account_owner=False,
            account=account,
            email='performer@test.test',
        )
        workflow = create_test_workflow(user=user, tasks_count=1)
        workflow.workflow_starter = None
        workflow.save()
        task = workflow.tasks.get(number=1)
        send_new_task_websocket_mock = mocker.patch(
            'src.notifications.tasks'
            '.send_new_task_websocket.delay',
        )
        send_new_task_notification_mock = mocker.patch(
            'src.processes.services.tasks.performers.'
            'send_new_task_notification.delay',
        )
        is_superuser = False
        auth_type = AuthTokenType.USER

        # act
        TaskPerformersService._create_actions(
            request_user=user,
            user=user_performer,
            task=task,
            auth_type=auth_type,
            is_superuser=is_superuser,
        )

        # assert
        send_new_task_websocket_mock.assert_not_called()
        send_new_task_notification_mock.assert_called_once_with(
            logging=account.log_api_requests,
            account_id=account.id,
            recipients=[(
                user_performer.id,
                user_performer.email,
                user_performer.is_new_tasks_subscriber,
            )],
            task_id=task.id,
            task_name=task.name,
            task_description=task.description,
            workflow_name=workflow.name,
            template_name=workflow.template.name,
            workflow_starter_name=None,
            workflow_starter_photo=None,
            due_date_timestamp=None,
            logo_lg=None,
            is_returned=False,
        )

    def test_create_actions__not_send_notify_for_transfered__ok(self, mocker):

        # arrange
        request_user = create_test_user(is_account_owner=False)
        transfer_performer = create_test_user(
            email='performer@test.test',
            is_account_owner=False,
        )
        workflow = create_test_workflow(request_user)
        task = workflow.tasks.get(number=1)
        send_new_task_notification_mock = mocker.patch(
            'src.processes.services.tasks.performers.'
            'send_new_task_notification.delay',
        )
        is_superuser = False
        auth_type = AuthTokenType.USER

        # act
        TaskPerformersService._create_actions(
            request_user=request_user,
            user=transfer_performer,
            task=task,
            auth_type=auth_type,
            is_superuser=is_superuser,
        )

        # assert
        send_new_task_notification_mock.assert_not_called()
        assert WorkflowEvent.objects.filter(
            workflow=workflow,
            account=request_user.account,
            type=WorkflowEventType.TASK_PERFORMER_CREATED,
            task_json=TaskEventJsonSerializer(
                instance=task,
                context={
                    'event_type': WorkflowEventType.TASK_PERFORMER_CREATED,
                },
            ).data,
        ).count() == 1
        workflow.refresh_from_db()
        assert transfer_performer in workflow.members.all()

    def test_create_actions__with_deleted_group_taskperformer__ok(
        self,
        mocker,
    ):

        # arrange
        account = create_test_account()

        request_user = create_test_admin(
            account=account, email='request@test.test',
        )
        user_performer = create_test_admin(
            account=account, email='performer@test.test',
        )

        group = create_test_group(account=account, name='TestGroup')
        user1 = create_test_user(account=account, email='user1@test.test')
        group.users.set([user1, user_performer])

        workflow = create_test_workflow(request_user)
        task = workflow.tasks.get(number=1)
        task.due_date = timezone.now() + timedelta(hours=1)
        task.save(update_fields=['due_date'])

        workflow2 = create_test_workflow(request_user)
        task2 = workflow2.tasks.get(number=1)
        task2.due_date = timezone.now() + timedelta(hours=1)
        task2.save(update_fields=['due_date'])

        TaskPerformer.objects.create(
            task=task,
            group=group,
            type=PerformerType.GROUP,
        )

        TaskPerformer.objects.create(
            task=task2,
            group=group,
            type=PerformerType.GROUP,
            directly_status=DirectlyStatus.DELETED,
        )

        send_new_task_websocket_mock = mocker.patch(
            'src.notifications.tasks'
            '.send_new_task_websocket.delay',
        )
        send_new_task_notification_mock = mocker.patch(
            'src.processes.services.tasks.performers.'
            'send_new_task_notification.delay',
        )
        is_superuser = False
        auth_type = AuthTokenType.USER

        # act
        TaskPerformersService._create_actions(
            request_user=request_user,
            user=user_performer,
            task=task,
            auth_type=auth_type,
            is_superuser=is_superuser,
        )

        # assert
        assert user_performer in workflow.members.all()
        send_new_task_websocket_mock.assert_not_called()
        send_new_task_notification_mock.assert_not_called()
        assert WorkflowEvent.objects.filter(
            workflow=workflow,
            account=request_user.account,
            type=WorkflowEventType.TASK_PERFORMER_CREATED,
            task_json=TaskEventJsonSerializer(
                instance=task,
                context={
                    'event_type': WorkflowEventType.TASK_PERFORMER_CREATED,
                },
            ).data,
        ).count() == 1

    def test_delete_actions__user_in_group__not_send(
        self,
        mocker,
    ):

        # arrange
        account = create_test_account()
        request_user = create_test_user(
            account=account,
            is_account_owner=True,
        )
        user_performer_1 = create_test_user(
            is_account_owner=False,
            is_admin=False,
            account=account,
            email='performer_1@test.test',
        )
        deleted_performer = create_test_user(
            is_account_owner=False,
            is_admin=True,
            account=account,
            email='performer_2@test.test',
        )
        workflow = create_test_workflow(request_user)
        task = workflow.tasks.get(number=1)
        task.taskperformer_set.filter(
            user_id=request_user.id,
        ).delete()
        task.taskperformer_set.create(
            user=user_performer_1,
            is_completed=False,
        )
        task.taskperformer_set.create(
            user=deleted_performer,
            is_completed=False,
            directly_status=DirectlyStatus.DELETED,
        )
        group = create_test_group(account, users=[deleted_performer])
        TaskPerformer.objects.create(
            task_id=task.id,
            type=PerformerType.GROUP,
            group_id=group.id,
        )
        workflow_action_service_init_mock = mocker.patch.object(
            WorkflowActionService,
            attribute='__init__',
            return_value=None,
        )
        complete_task_mock = mocker.patch(
            'src.processes.services.workflow_action'
            '.WorkflowActionService.complete_task',
        )
        performer_deleted_event_mock = mocker.patch(
            'src.processes.services.events.'
            'WorkflowEventService.performer_deleted_event',
        )
        send_task_deleted_notification_mock = mocker.patch(
            'src.notifications.tasks'
            '.send_removed_task_deleted_notification.delay',
        )
        is_superuser = False
        auth_type = AuthTokenType.USER

        # act
        TaskPerformersService._delete_actions(
            request_user=request_user,
            user=deleted_performer,
            task=task,
            auth_type=auth_type,
            is_superuser=is_superuser,
        )

        # assert
        workflow_action_service_init_mock.assert_not_called()
        complete_task_mock.assert_not_called()
        performer_deleted_event_mock.assert_called_once_with(
            user=request_user,
            task=task,
            performer=deleted_performer,
        )
        send_task_deleted_notification_mock.assert_not_called()

    def test_delete_actions_not_last_completed__not_complete_task(
        self,
        mocker,
    ):

        # arrange
        account = create_test_account()
        request_user = create_test_user(
            account=account,
            is_account_owner=True,
        )
        user_performer_1 = create_test_user(
            is_account_owner=False,
            is_admin=False,
            account=account,
            email='performer_1@test.test',
        )
        deleted_performer = create_test_user(
            is_account_owner=False,
            is_admin=True,
            account=account,
            email='performer_2@test.test',
        )
        workflow = create_test_workflow(request_user)
        task = workflow.tasks.get(number=1)
        task.taskperformer_set.filter(
            user_id=request_user.id,
        ).delete()
        task.taskperformer_set.create(
            user=user_performer_1,
            is_completed=False,
        )
        task.taskperformer_set.create(
            user=deleted_performer,
            is_completed=False,
            directly_status=DirectlyStatus.DELETED,
        )
        workflow_action_service_init_mock = mocker.patch.object(
            WorkflowActionService,
            attribute='__init__',
            return_value=None,
        )
        complete_task_mock = mocker.patch(
            'src.processes.services.workflow_action'
            '.WorkflowActionService.complete_task',
        )
        performer_deleted_event_mock = mocker.patch(
            'src.processes.services.events.'
            'WorkflowEventService.performer_deleted_event',
        )
        send_task_deleted_notification_mock = mocker.patch(
            'src.notifications.tasks'
            '.send_removed_task_deleted_notification.delay',
        )
        is_superuser = False
        auth_type = AuthTokenType.USER

        # act
        TaskPerformersService._delete_actions(
            request_user=request_user,
            user=deleted_performer,
            task=task,
            auth_type=auth_type,
            is_superuser=is_superuser,
        )

        # assert
        workflow_action_service_init_mock.assert_not_called()
        complete_task_mock.assert_not_called()
        performer_deleted_event_mock.assert_called_once_with(
            user=request_user,
            task=task,
            performer=deleted_performer,
        )
        send_task_deleted_notification_mock.assert_called_once_with(
            task_id=task.id,
            recipients=[(deleted_performer.id, deleted_performer.email)],
            account_id=account.id,
        )

    def test_delete_actions__last_completed_performer__complete_task(
        self,
        mocker,
    ):

        # arrange
        account = create_test_account()
        request_user = create_test_user(
            account=account,
            is_account_owner=True,
        )
        user_performer_1 = create_test_user(
            is_account_owner=False,
            is_admin=False,
            account=account,
            email='performer_1@test.test',
        )
        deleted_performer = create_test_user(
            is_account_owner=False,
            is_admin=True,
            account=account,
            email='performer_2@test.test',
        )
        workflow = create_test_workflow(request_user)
        task = workflow.tasks.get(number=1)
        task.taskperformer_set.filter(
            user_id=request_user.id,
        ).delete()
        task.taskperformer_set.create(
            user=user_performer_1,
            is_completed=True,
        )
        task.taskperformer_set.create(
            user=deleted_performer,
            is_completed=False,
            directly_status=DirectlyStatus.DELETED,
        )

        workflow_action_service_init_mock = mocker.patch.object(
            WorkflowActionService,
            attribute='__init__',
            return_value=None,
        )
        complete_task_mock = mocker.patch(
            'src.processes.services.workflow_action'
            '.WorkflowActionService.complete_task',
        )
        performer_deleted_event_mock = mocker.patch(
            'src.processes.services.events.'
            'WorkflowEventService.performer_deleted_event',
        )
        send_task_deleted_notification_mock = mocker.patch(
            'src.notifications.tasks'
            '.send_removed_task_deleted_notification.delay',
        )
        is_superuser = False
        auth_type = AuthTokenType.USER

        # act
        TaskPerformersService._delete_actions(
            request_user=request_user,
            user=deleted_performer,
            task=task,
            auth_type=auth_type,
            is_superuser=is_superuser,
        )

        # assert
        workflow_action_service_init_mock.assert_called_once_with(
            workflow=workflow,
            user=user_performer_1,
            is_superuser=False,
            auth_type=AuthTokenType.USER,
        )
        complete_task_mock.assert_called_once_with(task=task)
        performer_deleted_event_mock.assert_called_once_with(
            user=request_user,
            task=task,
            performer=deleted_performer,
        )
        send_task_deleted_notification_mock.assert_not_called()

    def test_delete_actions__rcba_last_completed_performer__complete_task(
        self,
        mocker,
    ):
        """ Case when task.require_completion_by_all is True
            and deleted last not completed user in result
            should complete task """

        # arrange
        account = create_test_account()
        request_user = create_test_user(
            account=account,
            is_account_owner=True,
        )
        user_performer_1 = create_test_user(
            is_account_owner=False,
            is_admin=False,
            account=account,
            email='performer_1@test.test',
        )
        deleted_performer = create_test_user(
            is_account_owner=False,
            is_admin=True,
            account=account,
            email='performer_2@test.test',
        )
        workflow = create_test_workflow(request_user)
        task = workflow.tasks.get(number=1)
        task.require_completion_by_all = True
        task.save(update_fields=['require_completion_by_all'])
        task.taskperformer_set.filter(
            user_id=request_user.id,
        ).delete()
        task.taskperformer_set.create(
            user=user_performer_1,
            is_completed=True,
        )
        task.taskperformer_set.create(
            user=deleted_performer,
            is_completed=False,
            directly_status=DirectlyStatus.DELETED,
        )

        workflow_action_service_init_mock = mocker.patch.object(
            WorkflowActionService,
            attribute='__init__',
            return_value=None,
        )
        complete_task_mock = mocker.patch(
            'src.processes.services.workflow_action'
            '.WorkflowActionService.complete_task',
        )
        performer_deleted_event_mock = mocker.patch(
            'src.processes.services.events.'
            'WorkflowEventService.performer_deleted_event',
        )
        send_task_deleted_notification_mock = mocker.patch(
            'src.notifications.tasks'
            '.send_removed_task_deleted_notification.delay',
        )
        is_superuser = False
        auth_type = AuthTokenType.USER

        # act
        TaskPerformersService._delete_actions(
            request_user=request_user,
            user=deleted_performer,
            task=task,
            auth_type=auth_type,
            is_superuser=is_superuser,
        )

        # assert
        workflow_action_service_init_mock.assert_called_once_with(
            workflow=workflow,
            user=user_performer_1,
            is_superuser=False,
            auth_type=AuthTokenType.USER,
        )
        complete_task_mock.assert_called_once_with(task=task)
        performer_deleted_event_mock.assert_called_once_with(
            user=request_user,
            task=task,
            performer=deleted_performer,
        )
        send_task_deleted_notification_mock.assert_not_called()

    def test_delete_actions__with_deleted_group_taskperformer__ok(
        self,
        mocker,
    ):

        # arrange
        account = create_test_account()

        request_user = create_test_admin(
            account=account, email='request@test.test',
        )
        deleted_performer = create_test_admin(
            account=account, email='performer@test.test',
        )

        group = create_test_group(account=account, name='TestGroup')
        user1 = create_test_user(account=account, email='user1@test.test')
        group.users.set([user1, deleted_performer])

        workflow = create_test_workflow(request_user)
        task = workflow.tasks.get(number=1)
        task.due_date = timezone.now() + timedelta(hours=1)
        task.save(update_fields=['due_date'])

        workflow2 = create_test_workflow(request_user)
        task2 = workflow2.tasks.get(number=1)
        task2.due_date = timezone.now() + timedelta(hours=1)
        task2.save(update_fields=['due_date'])

        TaskPerformer.objects.create(
            task=task,
            group=group,
            type=PerformerType.GROUP,
        )

        TaskPerformer.objects.create(
            task=task2,
            group=group,
            type=PerformerType.GROUP,
            directly_status=DirectlyStatus.DELETED,
        )

        workflow_action_service_init_mock = mocker.patch.object(
            WorkflowActionService,
            attribute='__init__',
            return_value=None,
        )
        complete_task_mock = mocker.patch(
            'src.processes.services.workflow_action'
            '.WorkflowActionService.complete_task',
        )
        performer_deleted_event_mock = mocker.patch(
            'src.processes.services.events.'
            'WorkflowEventService.performer_deleted_event',
        )
        send_task_deleted_notification_mock = mocker.patch(
            'src.notifications.tasks'
            '.send_removed_task_deleted_notification.delay',
        )
        is_superuser = False
        auth_type = AuthTokenType.USER

        # act
        TaskPerformersService._delete_actions(
            request_user=request_user,
            user=deleted_performer,
            task=task,
            auth_type=auth_type,
            is_superuser=is_superuser,
        )

        # assert
        workflow_action_service_init_mock.assert_not_called()
        complete_task_mock.assert_not_called()
        performer_deleted_event_mock.assert_called_once_with(
            user=request_user,
            task=task,
            performer=deleted_performer,
        )
        send_task_deleted_notification_mock.assert_not_called()


class TestGuestPerformersService:

    def test_get_user_for_create__ok(self, mocker):

        # arrange
        account_owner = create_test_user(is_account_owner=True)
        user_guest = create_test_guest(account=account_owner.account)
        get_or_create_guest_user_mock = mocker.patch(
            'src.accounts.services.guests.'
            'GuestService.get_or_create',
            return_value=user_guest,
        )

        # act
        user = GuestPerformersService._get_user_for_create(
            user_key=user_guest.email,
            account_id=account_owner.account_id,
        )

        # assert
        assert user.id == user_guest.id
        get_or_create_guest_user_mock.assert_called_once_with(
            email=user_guest.email,
            account_id=account_owner.account_id,
        )

    def test_get_user_for_delete__ok(self):

        # arrange
        account_owner = create_test_user(is_account_owner=True)
        user_guest = create_test_guest(account=account_owner.account)

        # act
        user = GuestPerformersService._get_user_for_delete(
            user_key=user_guest.email,
            account_id=account_owner.account_id,
        )

        # assert
        assert user.id == user_guest.id

    def test_get_user_for_delete__not_found__raise_exception(self):

        # arrange
        another_account = create_test_account(name='another')
        create_test_user(
            is_account_owner=True,
            account=another_account,
            email='owner@test.test',
        )
        user_guest = create_test_guest(account=another_account)
        account_owner = create_test_user(is_account_owner=True)

        # act
        with pytest.raises(PerformersServiceException) as ex:
            GuestPerformersService._get_user_for_delete(
                user_key=user_guest.email,
                account_id=account_owner.account_id,
            )

        # assert
        assert ex.value.message == messages.MSG_PW_0014

    def test_create_actions__ok(self, mocker):

        # arrange
        logo_lg = 'https://site.com/logo-lg.jpg'
        account = create_test_account(logo_lg=logo_lg)
        create_test_user(
            email='owner@test.test',
            account=account,
            is_account_owner=True,
        )
        request_user = create_test_user(
            account=account,
            is_account_owner=False,
        )
        user_guest = create_test_guest(account=account)
        workflow = create_test_workflow(request_user)
        task = workflow.tasks.get(number=1)
        task.due_date = task.date_first_started + timedelta(hours=1)
        task.save(update_fields=['due_date'])
        token_str = str(GuestToken())
        get_token_mock = mocker.patch(
            'src.authentication.services.guest_auth.'
            'GuestJWTAuthService.get_str_token',
            return_value=token_str,
        )
        send_guest_new_task_mock = mocker.patch(
            'src.notifications.tasks.send_guest_new_task.delay',
        )
        users_guest_invite_sent_mock = mocker.patch(
            'src.analysis.services.AnalyticService.'
            'users_guest_invite_sent',
        )
        users_guest_invited_mock = mocker.patch(
            'src.analysis.services.AnalyticService.'
            'users_guest_invited',
        )
        activate_cache_mock = mocker.patch(
            'src.authentication.services.guest_auth.'
            'GuestJWTAuthService.activate_task_guest_cache',
        )
        current_url = '/page'
        is_superuser = False

        # act
        GuestPerformersService._create_actions(
            request_user=request_user,
            user=user_guest,
            task=task,
            current_url=current_url,
            is_superuser=is_superuser,
        )

        # assert
        assert WorkflowEvent.objects.filter(
            workflow=workflow,
            account=request_user.account,
            type=WorkflowEventType.TASK_PERFORMER_CREATED,
            task_json=TaskEventJsonSerializer(
                instance=task,
                context={
                    'event_type': WorkflowEventType.TASK_PERFORMER_CREATED,
                },
            ).data,
        ).count() == 1
        get_token_mock.assert_called_once_with(
            user_id=user_guest.id,
            task_id=task.id,
            account_id=user_guest.account_id,
        )
        send_guest_new_task_mock.assert_called_once_with(
            logging=account.log_api_requests,
            token=token_str,
            sender_name=request_user.get_full_name(),
            user_id=user_guest.id,
            user_email=user_guest.email,
            task_id=task.id,
            task_name=task.name,
            task_description=task.description,
            task_due_date=task.due_date,
            logo_lg=account.logo_lg,
            account_id=account.id,
        )
        users_guest_invite_sent_mock.assert_called_once_with(
            task=task,
            invite_from=request_user,
            invite_to=user_guest,
            current_url=current_url,
            is_superuser=is_superuser,
        )
        users_guest_invited_mock.assert_called_once_with(
            invite_from=request_user,
            invite_to=user_guest,
            is_superuser=is_superuser,
        )
        activate_cache_mock.assert_called_once_with(
            task_id=task.id,
            user_id=user_guest.id,
        )

    def test_delete_actions_not_last_completed__not_complete_task(
        self,
        mocker,
    ):
        # arrange
        account = create_test_account()
        request_user = create_test_user(
            account=account,
            is_account_owner=True,
        )
        user_performer_1 = create_test_user(
            is_account_owner=False,
            account=account,
            email='performer_1@test.test',
        )
        deleted_guest = create_test_guest(account=account)
        workflow = create_test_workflow(request_user)
        task = workflow.tasks.get(number=1)
        task.taskperformer_set.filter(
            user_id=request_user.id,
        ).delete()
        task.taskperformer_set.create(
            user=user_performer_1,
            is_completed=False,
        )
        task.taskperformer_set.create(
            user=deleted_guest,
            is_completed=False,
            directly_status=DirectlyStatus.DELETED,
        )
        deactivate_cache_mock = mocker.patch(
            'src.authentication.services.guest_auth.'
            'GuestJWTAuthService.deactivate_task_guest_cache',
        )
        workflow_action_service_init_mock = mocker.patch.object(
            WorkflowActionService,
            attribute='__init__',
            return_value=None,
        )
        complete_task_mock = mocker.patch(
            'src.processes.services.workflow_action'
            '.WorkflowActionService.complete_task',
        )
        performer_deleted_event_mock = mocker.patch(
            'src.processes.services.events.'
            'WorkflowEventService.performer_deleted_event',
        )

        # act
        GuestPerformersService._delete_actions(
            request_user=request_user,
            user=deleted_guest,
            task=task,
        )

        # assert
        performer_deleted_event_mock.assert_called_once_with(
            user=request_user,
            task=task,
            performer=deleted_guest,
        )
        deactivate_cache_mock.assert_called_once_with(
            task_id=task.id,
            user_id=deleted_guest.id,
        )
        workflow_action_service_init_mock.assert_not_called()
        complete_task_mock.assert_not_called()

    def test_delete_actions__last_completed_performer__complete_task(
        self,
        mocker,
    ):
        # arrange
        account = create_test_account()
        request_user = create_test_user(
            account=account,
            is_account_owner=True,
        )
        user_performer_1 = create_test_user(
            is_account_owner=False,
            account=account,
            email='performer_1@test.test',
        )
        deleted_guest = create_test_guest(account=account)
        workflow = create_test_workflow(request_user)
        task = workflow.tasks.get(number=1)
        task.taskperformer_set.filter(
            user_id=request_user.id,
        ).delete()
        task.taskperformer_set.create(
            user=user_performer_1,
            is_completed=True,
        )
        task.taskperformer_set.create(
            user=deleted_guest,
            is_completed=False,
            directly_status=DirectlyStatus.DELETED,
        )
        deactivate_cache_mock = mocker.patch(
            'src.authentication.services.guest_auth.'
            'GuestJWTAuthService.deactivate_task_guest_cache',
        )
        workflow_action_service_init_mock = mocker.patch.object(
            WorkflowActionService,
            attribute='__init__',
            return_value=None,
        )
        complete_task_mock = mocker.patch(
            'src.processes.services.workflow_action'
            '.WorkflowActionService.complete_task',
        )
        performer_deleted_event_mock = mocker.patch(
            'src.processes.services.events.'
            'WorkflowEventService.performer_deleted_event',
        )

        # act
        GuestPerformersService._delete_actions(
            request_user=request_user,
            user=deleted_guest,
            task=task,
        )

        # assert
        performer_deleted_event_mock.assert_called_once_with(
            user=request_user,
            task=task,
            performer=deleted_guest,
        )
        deactivate_cache_mock.assert_called_once_with(
            task_id=task.id,
            user_id=deleted_guest.id,
        )
        workflow_action_service_init_mock.assert_called_once_with(
            workflow=workflow,
            user=user_performer_1,
            is_superuser=False,
            auth_type=AuthTokenType.USER,
        )
        complete_task_mock.assert_called_once_with(task=task)

    def test_delete_actions__rcba_last_completed_performer__complete_task(
        self,
        mocker,
    ):
        # arrange
        account = create_test_account()
        request_user = create_test_user(
            account=account,
            is_account_owner=True,
        )
        user_performer_1 = create_test_user(
            is_account_owner=False,
            account=account,
            email='performer_1@test.test',
        )
        deleted_guest = create_test_guest(account=account)
        workflow = create_test_workflow(request_user)
        task = workflow.tasks.get(number=1)
        task.require_completion_by_all = True
        task.save(update_fields=['require_completion_by_all'])
        task.taskperformer_set.filter(
            user_id=request_user.id,
        ).delete()
        task.taskperformer_set.create(
            user=user_performer_1,
            is_completed=True,
        )
        task.taskperformer_set.create(
            user=deleted_guest,
            is_completed=False,
            directly_status=DirectlyStatus.DELETED,
        )
        deactivate_cache_mock = mocker.patch(
            'src.authentication.services.guest_auth.'
            'GuestJWTAuthService.deactivate_task_guest_cache',
        )
        workflow_action_service_init_mock = mocker.patch.object(
            WorkflowActionService,
            attribute='__init__',
            return_value=None,
        )
        complete_task_mock = mocker.patch(
            'src.processes.services.workflow_action'
            '.WorkflowActionService.complete_task',
        )
        performer_deleted_event_mock = mocker.patch(
            'src.processes.services.events.'
            'WorkflowEventService.performer_deleted_event',
        )

        # act
        GuestPerformersService._delete_actions(
            request_user=request_user,
            user=deleted_guest,
            task=task,
        )

        # assert
        performer_deleted_event_mock.assert_called_once_with(
            user=request_user,
            task=task,
            performer=deleted_guest,
        )
        deactivate_cache_mock.assert_called_once_with(
            task_id=task.id,
            user_id=deleted_guest.id,
        )
        workflow_action_service_init_mock.assert_called_once_with(
            workflow=workflow,
            user=user_performer_1,
            is_superuser=False,
            auth_type=AuthTokenType.USER,
        )
        complete_task_mock.assert_called_once_with(task=task)

    def test_validate_create__limit_guests_reached__raise_exception(
        self,
        mocker,
    ):

        # arrange
        account = create_test_account()
        request_user = create_test_user(
            account=account,
            is_account_owner=True,
            email='owner@test.test',
        )
        user_guest = create_test_guest(account=account)
        user_guest_2 = create_test_guest(
            account=account,
            email='guest2@test.test',
        )
        user_guest_3 = create_test_guest(
            account=account,
            email='guest3@test.test',
        )

        workflow = create_test_workflow(request_user)
        task = workflow.tasks.get(number=1)

        TaskPerformer.objects.create(
            task_id=task.id,
            user_id=user_guest.id,
        )
        TaskPerformer.objects.create(
            task_id=task.id,
            user_id=user_guest_2.id,
        )
        TaskPerformer.objects.create(
            task_id=task.id,
            user_id=user_guest_3.id,
            directly_status=DirectlyStatus.DELETED,
        )
        mocker.patch(
            'src.processes.services.tasks.guests.'
            'GuestPerformersService.MAX_GUEST_PERFORMERS', 2,
        )

        # act
        with pytest.raises(PerformersServiceException) as ex:
            GuestPerformersService._validate_create(
                request_user=request_user,
                task=task,
            )

        # assert
        assert ex.value.message == messages.MSG_PW_0015


class TestBasePerformerService2:
    def test_get_valid_deleted_task_performer__group_performer__ok(self):

        # arrange
        account = create_test_account(plan=BillingPlanType.PREMIUM)
        user = create_test_user(account=account)
        template = create_test_template(user=user, is_active=True)
        group = create_test_group(account, users=[user])
        task_template = template.tasks.get(number=1)
        task_template.add_raw_performer(
            group=group,
            performer_type=PerformerType.GROUP,
        )
        workflow = create_test_workflow(user, template=template)
        task = workflow.tasks.get(number=1)
        service = BasePerformerService2(
            user=user,
            task=task,
            is_superuser=False,
            auth_type=AuthTokenType.USER,
        )

        # act
        task_performer = service._get_valid_deleted_task_performer(
            group=group,
        )

        # assert
        assert task_performer.group_id == group.id

    def test_get_valid_deleted_task_performer__last_performer__raise_exception(
        self,
    ):

        # arrange
        account = create_test_account(plan=BillingPlanType.PREMIUM)
        user = create_test_user(account=account)
        template = create_test_template(user=user, is_active=True)
        group = create_test_group(account, users=[user])
        task_template = template.tasks.get(number=1)
        task_template.delete_raw_performers()
        task_template.add_raw_performer(
            group=group,
            performer_type=PerformerType.GROUP,
        )
        workflow = create_test_workflow(user, template=template)
        task = workflow.tasks.get(number=1)
        service = BasePerformerService2(
            user=user,
            task=task,
            is_superuser=False,
            auth_type=AuthTokenType.USER,
        )

        # act
        with pytest.raises(GroupPerformerServiceException) as ex:
            service._get_valid_deleted_task_performer(
                    group=group,
                )

        # assert
        assert ex.value.message == messages.MSG_PW_0016

    def test_validate__workflow_is_completed__raise_exception(self):

        # arrange
        account = create_test_account(plan=BillingPlanType.PREMIUM)
        user = create_test_user(account=account)
        workflow = create_test_workflow(
            user=user,
            status=WorkflowStatus.DONE,
        )
        task = workflow.tasks.get(number=1)
        service = BasePerformerService2(
            user=user,
            task=task,
            is_superuser=False,
            auth_type=AuthTokenType.USER,
        )

        # act
        with pytest.raises(GroupPerformerServiceException) as ex:
            service._validate()

        # assert
        assert ex.value.message == messages.MSG_PW_0017

    def test_validate__not_active_task__raise_exception(self):

        # arrange
        account = create_test_account(plan=BillingPlanType.PREMIUM)
        user = create_test_user(account=account)
        workflow = create_test_workflow(user=user)
        task = workflow.tasks.get(number=2)
        service = BasePerformerService2(
            user=user,
            task=task,
            is_superuser=False,
            auth_type=AuthTokenType.USER,
        )

        # act
        with pytest.raises(GroupPerformerServiceException) as ex:
            service._validate()

        # assert
        assert ex.value.message == messages.MSG_PW_0018

    def test_validate__user_not_admin__raise_exception(self):

        # arrange
        account = create_test_account(plan=BillingPlanType.PREMIUM)
        user = create_test_user(account=account)
        request_user = create_test_user(
            account=account,
            is_admin=False,
            email='owner@test.test',
        )
        workflow = create_test_workflow(user=user)
        task = workflow.tasks.get(number=1)
        service = BasePerformerService2(
            user=request_user,
            task=task,
            is_superuser=False,
            auth_type=AuthTokenType.USER,
        )

        # act
        with pytest.raises(GroupPerformerServiceException) as ex:
            service._validate()

        # assert
        assert ex.value.message == messages.MSG_PW_0021

    def test_validate__user_not_owner_and_not_task_performer__raise_exception(
        self,
    ):

        # arrange
        account = create_test_account(plan=BillingPlanType.PREMIUM)
        user = create_test_user(account=account)
        request_user = create_test_user(
            account=account,
            is_account_owner=False,
            email='owner@test.test',
        )
        workflow = create_test_workflow(user=user)
        task = workflow.tasks.get(number=1)
        service = BasePerformerService2(
            user=request_user,
            task=task,
            is_superuser=False,
            auth_type=AuthTokenType.USER,
        )

        # act
        with pytest.raises(GroupPerformerServiceException) as ex:
            service._validate()

        # assert
        assert ex.value.message == messages.MSG_PW_0021


class TestGroupPerformerService:

    def test_get_group__ok(self):

        # arrange
        account = create_test_account(plan=BillingPlanType.PREMIUM)
        user = create_test_user(account=account)
        group = create_test_group(account, users=[user])
        workflow = create_test_workflow(user=user)
        task = workflow.tasks.get(number=1)
        service = GroupPerformerService(
            user=user,
            task=task,
            is_superuser=False,
            auth_type=AuthTokenType.USER,
        )

        # act
        return_group = service._get_group(group_id=group.id)

        # assert
        assert return_group == group

    def test_get_group__invalid_group_id__ok(self):

        # arrange
        account = create_test_account(plan=BillingPlanType.PREMIUM)
        user = create_test_user(account=account)
        workflow = create_test_workflow(user=user)
        task = workflow.tasks.get(number=1)
        service = GroupPerformerService(
            user=user,
            task=task,
            is_superuser=False,
            auth_type=AuthTokenType.USER,
        )

        # act
        with pytest.raises(GroupPerformerServiceException) as ex:
            service._get_group(group_id=5436)

        # assert
        assert ex.value.message == messages.MSG_PW_0082

    def test_get_group__group_another_account__ok(self):

        # arrange
        user = create_test_user(email='test3@test.test')
        another_acc_user = create_test_user()
        group = create_test_group(another_acc_user.account)
        workflow = create_test_workflow(user=user)
        task = workflow.tasks.get(number=1)
        service = GroupPerformerService(
            user=user,
            task=task,
            is_superuser=False,
            auth_type=AuthTokenType.USER,
        )

        # act
        with pytest.raises(GroupPerformerServiceException) as ex:
            service._get_group(group_id=group.id)

        # assert
        assert ex.value.message == messages.MSG_PW_0082

    def test_create_group_actions__ok(self, mocker):

        # arrange
        logo_lg = 'https://some.com/image.png'
        account = create_test_account(logo_lg=logo_lg, log_api_requests=True)
        photo = 'http://image.com/avatar.png'
        user = create_test_user(account=account, photo=photo)
        user2 = create_test_user(account=account, email='test2@test.test')
        user3 = create_test_user(account=account, email='test3@test.test')
        group = create_test_group(account, users=[user2, user3])
        workflow = create_test_workflow(user=user)
        task = workflow.tasks.get(number=1)
        task.due_date = timezone.now() + timedelta(hours=1)
        task.save(update_fields=['due_date'])
        service = GroupPerformerService(
            user=user,
            task=task,
            is_superuser=False,
            auth_type=AuthTokenType.USER,
        )
        performer_group_created_event_mock = mocker.patch(
            'src.processes.services.events.'
            'WorkflowEventService.performer_group_created_event',
        )
        send_new_task_notification_mock = mocker.patch(
            'src.processes.services.tasks.performers.'
            'send_new_task_notification.delay',
        )
        send_new_task_websocket_mock = mocker.patch(
            'src.notifications.tasks'
            '.send_new_task_websocket.delay',
        )

        # act
        service._create_group_actions(group=group)

        # assert
        performer_group_created_event_mock.assert_called_once_with(
            user=user,
            task=task,
            performer=group,
        )
        send_new_task_websocket_mock.assert_not_called()
        send_new_task_notification_mock.assert_called_once_with(
            logging=account.log_api_requests,
            account_id=account.id,
            recipients=[
                (user2.id, user2.email, user2.is_new_tasks_subscriber),
                (user3.id, user3.email, user3.is_new_tasks_subscriber),
            ],
            task_id=task.id,
            task_name=task.name,
            task_description=task.description,
            workflow_name=workflow.name,
            template_name=workflow.get_template_name(),
            workflow_starter_name=user.name,
            workflow_starter_photo=photo,
            due_date_timestamp=task.due_date.timestamp(),
            logo_lg=logo_lg,
            is_returned=False,
        )

    def test_create_group_actions__user_is_performer__ok(self, mocker):

        # arrange
        logo_lg = 'https://some.com/image.png'
        account = create_test_account(logo_lg=logo_lg, log_api_requests=True)
        photo = 'http://image.com/avatar.png'
        user = create_test_user(account=account, photo=photo)
        user2 = create_test_user(account=account, email='test2@test.test')
        group = create_test_group(account, users=[user2])
        workflow = create_test_workflow(user=user)
        task = workflow.tasks.get(number=1)
        task.taskperformer_set.create(
            user=user2,
            is_completed=False,
        )
        service = GroupPerformerService(
            user=user,
            task=task,
            is_superuser=False,
            auth_type=AuthTokenType.USER,
        )
        performer_group_created_event_mock = mocker.patch(
            'src.processes.services.events.'
            'WorkflowEventService.performer_group_created_event',
        )
        send_new_task_notification_mock = mocker.patch(
            'src.processes.services.tasks.performers.'
            'send_new_task_notification.delay',
        )
        send_new_task_websocket_mock = mocker.patch(
            'src.notifications.tasks'
            '.send_new_task_websocket.delay',
        )

        # act
        service._create_group_actions(group=group)

        # assert
        performer_group_created_event_mock.assert_called_once_with(
            user=user,
            task=task,
            performer=group,
        )
        send_new_task_notification_mock.assert_not_called()
        send_new_task_websocket_mock.assert_not_called()

    def test_create_group_actions__yourself__ok(self, mocker):

        # arrange
        logo_lg = 'https://some.com/image.png'
        account = create_test_account(logo_lg=logo_lg, log_api_requests=True)
        photo = 'http://image.com/avatar.png'
        user = create_test_user(account=account, photo=photo)
        user2 = create_test_user(account=account, email='test2@test.test')
        group = create_test_group(account, users=[user2])
        workflow = create_test_workflow(user=user)
        task = workflow.tasks.get(number=1)
        service = GroupPerformerService(
            user=user2,
            task=task,
            is_superuser=False,
            auth_type=AuthTokenType.USER,
        )
        performer_group_created_event_mock = mocker.patch(
            'src.processes.services.events.'
            'WorkflowEventService.performer_group_created_event',
        )
        send_new_task_notification_mock = mocker.patch(
            'src.processes.services.tasks.performers.'
            'send_new_task_notification.delay',
        )
        send_new_task_websocket_mock = mocker.patch(
            'src.notifications.tasks'
            '.send_new_task_websocket.delay',
        )

        # act
        service._create_group_actions(group=group)

        # assert
        performer_group_created_event_mock.assert_called_once_with(
            user=user2,
            task=task,
            performer=group,
        )
        send_new_task_notification_mock.assert_not_called()
        send_new_task_websocket_mock.assert_called_once_with(
            task_id=task.id,
            recipients=[(user2.id, user2.email, user.is_new_tasks_subscriber)],
            account_id=account.id,
            logging=account.log_api_requests,
        )

    def test_create_group_actions__missing_recipients__ok(self, mocker):

        # arrange
        account = create_test_account()
        user = create_test_user(account=account)
        user2 = create_test_user(account=account, email='test2@test.test')
        group = create_test_group(account, users=[user, user2])
        workflow = create_test_workflow(user=user)
        task = workflow.tasks.get(number=1)
        service = GroupPerformerService(
            user=user2,
            task=task,
            is_superuser=False,
            auth_type=AuthTokenType.USER,
        )
        performer_group_created_event_mock = mocker.patch(
            'src.processes.services.events.'
            'WorkflowEventService.performer_group_created_event',
        )
        send_new_task_notification_mock = mocker.patch(
            'src.processes.services.tasks.performers.'
            'send_new_task_notification.delay',
        )
        send_new_task_websocket_mock = mocker.patch(
            'src.notifications.tasks'
            '.send_new_task_websocket.delay',
        )

        # act
        service._create_group_actions(group=group)

        # assert
        performer_group_created_event_mock.assert_called_once_with(
            user=user2,
            task=task,
            performer=group,
        )
        send_new_task_notification_mock.assert_not_called()
        send_new_task_websocket_mock.assert_called_once_with(
            task_id=task.id,
            recipients=[(user2.id, user2.email, user.is_new_tasks_subscriber)],
            account_id=account.id,
            logging=account.log_api_requests,
        )

    def test_create_group_actions__not_users_for_send_notification__ok(
        self, mocker,
    ):

        # arrange
        account = create_test_account()
        user = create_test_user(account=account)
        group = create_test_group(account, users=[user])
        workflow = create_test_workflow(user=user)
        task = workflow.tasks.get(number=1)
        service = GroupPerformerService(
            user=user,
            task=task,
            is_superuser=False,
            auth_type=AuthTokenType.USER,
        )
        performer_created_event_mock = mocker.patch(
            'src.processes.services.events.'
            'WorkflowEventService.performer_group_created_event',
        )
        send_new_task_notification_mock = mocker.patch(
            'src.processes.services.tasks.performers.'
            'send_new_task_notification.delay',
        )
        send_new_task_websocket_mock = mocker.patch(
            'src.notifications.tasks'
            '.send_new_task_websocket.delay',
        )

        # act
        service._create_group_actions(group=group)

        # assert
        performer_created_event_mock.assert_called_once_with(
            user=user,
            task=task,
            performer=group,
        )
        send_new_task_notification_mock.assert_not_called()
        send_new_task_websocket_mock.assert_not_called()

    def test_create_performer__ok(self, mocker):

        # arrange
        account = create_test_account()
        user = create_test_user(account=account)
        group = create_test_group(account, users=[user])
        workflow = create_test_workflow(user=user)
        task = workflow.tasks.get(number=1)
        validate_mock = mocker.patch(
            'src.processes.services.tasks.base.'
            'BasePerformerService2._validate',
        )
        validate_create_mock = mocker.patch(
            'src.processes.services.tasks.base.'
            'BasePerformerService2._validate_create',
        )
        create_group_actions_mock = mocker.patch(
            'src.processes.services.tasks.groups.'
            'GroupPerformerService._create_group_actions',
        )
        get_group_mock = mocker.patch(
            'src.processes.services.tasks.groups.'
            'GroupPerformerService._get_group',
            return_value=group,
        )
        service = GroupPerformerService(
            user=user,
            task=task,
            is_superuser=False,
            auth_type=AuthTokenType.USER,
        )

        # act
        service.create_performer(
            group_id=group.id,
            run_actions=True,
        )

        # assert
        validate_mock.assert_called_once_with()
        validate_create_mock.assert_called_once_with()
        create_group_actions_mock.assert_called_once_with(group=group)
        get_group_mock.assert_called_once_with(group_id=group.id)
        assert TaskPerformer.objects.filter(
            group=group,
            type=PerformerType.GROUP,
            task=task,
            directly_status=DirectlyStatus.CREATED,
        ).count() == 1

    def test_create_performer__already_created__skip(self, mocker):

        account = create_test_account()
        user = create_test_user(account=account)
        group = create_test_group(account, users=[user])
        workflow = create_test_workflow(user=user)
        task = workflow.tasks.get(number=1)
        TaskPerformer.objects.create(
            task_id=task.id,
            type=PerformerType.GROUP,
            group_id=group.id,
            directly_status=DirectlyStatus.CREATED,
        )
        validate_mock = mocker.patch(
            'src.processes.services.tasks.base.'
            'BasePerformerService2._validate',
        )
        validate_create_mock = mocker.patch(
            'src.processes.services.tasks.base.'
            'BasePerformerService2._validate_create',
        )
        create_group_actions_mock = mocker.patch(
            'src.processes.services.tasks.groups.'
            'GroupPerformerService._create_group_actions',
        )
        get_group_mock = mocker.patch(
            'src.processes.services.tasks.groups.'
            'GroupPerformerService._get_group',
            return_value=group,
        )
        service = GroupPerformerService(
            user=user,
            task=task,
            is_superuser=False,
            auth_type=AuthTokenType.USER,
        )

        # act
        service.create_performer(
            group_id=group.id,
            run_actions=True,
        )

        # assert
        validate_mock.assert_called_once_with()
        validate_create_mock.assert_called_once_with()
        create_group_actions_mock.assert_not_called()
        get_group_mock.assert_called_once_with(group_id=group.id)

    def test_create_performer__existent_with_no_status__skip(self, mocker):

        # arrange
        account = create_test_account()
        user = create_test_user(account=account)
        group = create_test_group(account, users=[user])
        workflow = create_test_workflow(user=user)
        task = workflow.tasks.get(number=1)
        TaskPerformer.objects.create(
            task_id=task.id,
            type=PerformerType.GROUP,
            group_id=group.id,
            directly_status=DirectlyStatus.NO_STATUS,
        )
        validate_mock = mocker.patch(
            'src.processes.services.tasks.base.'
            'BasePerformerService2._validate',
        )
        validate_create_mock = mocker.patch(
            'src.processes.services.tasks.base.'
            'BasePerformerService2._validate_create',
        )
        create_group_actions_mock = mocker.patch(
            'src.processes.services.tasks.groups.'
            'GroupPerformerService._create_group_actions',
        )
        get_group_mock = mocker.patch(
            'src.processes.services.tasks.groups.'
            'GroupPerformerService._get_group',
            return_value=group,
        )
        service = GroupPerformerService(
            user=user,
            task=task,
            is_superuser=False,
            auth_type=AuthTokenType.USER,
        )

        # act
        service.create_performer(
            group_id=group.id,
            run_actions=True,
        )

        # assert
        validate_mock.assert_called_once_with()
        validate_create_mock.assert_called_once_with()
        get_group_mock.assert_called_once_with(group_id=group.id)
        create_group_actions_mock.assert_not_called()

    def test_create_performer__restore_deleted__ok(self, mocker):

        # arrange
        account = create_test_account()
        user = create_test_user(account=account)
        group = create_test_group(account, users=[user])
        workflow = create_test_workflow(user=user)
        task = workflow.tasks.get(number=1)
        performer = TaskPerformer.objects.create(
            task_id=task.id,
            type=PerformerType.GROUP,
            group_id=group.id,
            directly_status=DirectlyStatus.DELETED,
        )
        validate_mock = mocker.patch(
            'src.processes.services.tasks.base.'
            'BasePerformerService2._validate',
        )
        validate_create_mock = mocker.patch(
            'src.processes.services.tasks.base.'
            'BasePerformerService2._validate_create',
        )
        create_group_actions_mock = mocker.patch(
            'src.processes.services.tasks.groups.'
            'GroupPerformerService._create_group_actions',
        )
        get_group_mock = mocker.patch(
            'src.processes.services.tasks.groups.'
            'GroupPerformerService._get_group',
            return_value=group,
        )
        service = GroupPerformerService(
            user=user,
            task=task,
            is_superuser=False,
            auth_type=AuthTokenType.USER,
        )

        # act
        service.create_performer(
            group_id=group.id,
            run_actions=True,
        )

        # assert
        validate_mock.assert_called_once_with()
        validate_create_mock.assert_called_once_with()
        get_group_mock.assert_called_once_with(group_id=group.id)
        create_group_actions_mock.assert_called_once_with(group=group)
        performer.refresh_from_db()
        assert performer.directly_status == DirectlyStatus.CREATED

    def test_delete_performer__ok(self, mocker):

        # arrange
        account = create_test_account()
        user = create_test_user(account=account)
        group = create_test_group(account, users=[user])
        workflow = create_test_workflow(user=user)
        task = workflow.tasks.get(number=1)
        performer = TaskPerformer.objects.create(
            task_id=task.id,
            type=PerformerType.GROUP,
            group_id=group.id,
        )
        validate_mock = mocker.patch(
            'src.processes.services.tasks.base.'
            'BasePerformerService2._validate',
        )
        get_valid_deleted_task_performer_mock = mocker.patch(
            'src.processes.services.tasks.base.'
            'BasePerformerService2._get_valid_deleted_task_performer',
            return_value=performer,
        )
        get_group_mock = mocker.patch(
            'src.processes.services.tasks.groups.'
            'GroupPerformerService._get_group',
            return_value=group,
        )
        delete_group_actions_mock = mocker.patch(
            'src.processes.services.tasks.groups.'
            'GroupPerformerService._delete_group_actions',
        )

        service = GroupPerformerService(
            user=user,
            task=task,
            is_superuser=False,
            auth_type=AuthTokenType.USER,
        )

        # act
        service.delete_performer(group_id=group.id)

        # assert
        validate_mock.assert_called_once_with()
        get_group_mock.assert_called_once_with(group_id=group.id)
        get_valid_deleted_task_performer_mock.assert_called_once_with(
            group=group,
        )
        delete_group_actions_mock.assert_called_once_with(group=group)
        performer.refresh_from_db()
        assert performer.directly_status == DirectlyStatus.DELETED

    def test_delete_performer__previously_created__ok(self, mocker):

        # arrange
        account = create_test_account()
        user = create_test_user(account=account)
        group = create_test_group(account, users=[user])
        workflow = create_test_workflow(user=user)
        task = workflow.tasks.get(number=1)
        performer = TaskPerformer.objects.create(
            task_id=task.id,
            type=PerformerType.GROUP,
            group_id=group.id,
            directly_status=DirectlyStatus.CREATED,
        )
        validate_mock = mocker.patch(
            'src.processes.services.tasks.base.'
            'BasePerformerService2._validate',
        )
        get_valid_deleted_task_performer_mock = mocker.patch(
            'src.processes.services.tasks.base.'
            'BasePerformerService2._get_valid_deleted_task_performer',
            return_value=performer,
        )
        get_group_mock = mocker.patch(
            'src.processes.services.tasks.groups.'
            'GroupPerformerService._get_group',
            return_value=group,
        )
        delete_group_actions_mock = mocker.patch(
            'src.processes.services.tasks.groups.'
            'GroupPerformerService._delete_group_actions',
        )

        service = GroupPerformerService(
            user=user,
            task=task,
            is_superuser=False,
            auth_type=AuthTokenType.USER,
        )

        # act
        service.delete_performer(group_id=group.id)

        # assert
        validate_mock.assert_called_once_with()
        get_group_mock.assert_called_once_with(group_id=group.id)
        get_valid_deleted_task_performer_mock.assert_called_once_with(
            group=group,
        )
        delete_group_actions_mock.assert_called_once_with(group=group)
        performer.refresh_from_db()
        assert performer.directly_status == DirectlyStatus.DELETED

    def test_delete_performer__not_existent__skip(self, mocker):

        # arrange
        account = create_test_account()
        user = create_test_user(account=account)
        group = create_test_group(account, users=[user])
        workflow = create_test_workflow(user=user)
        task = workflow.tasks.get(number=1)
        validate_mock = mocker.patch(
            'src.processes.services.tasks.base.'
            'BasePerformerService2._validate',
        )
        get_valid_deleted_task_performer_mock = mocker.patch(
            'src.processes.services.tasks.base.'
            'BasePerformerService2._get_valid_deleted_task_performer',
            return_value=None,
        )
        get_group_mock = mocker.patch(
            'src.processes.services.tasks.groups.'
            'GroupPerformerService._get_group',
            return_value=group,
        )
        delete_group_actions_mock = mocker.patch(
            'src.processes.services.tasks.groups.'
            'GroupPerformerService._delete_group_actions',
        )

        service = GroupPerformerService(
            user=user,
            task=task,
            is_superuser=False,
            auth_type=AuthTokenType.USER,
        )

        # act
        service.delete_performer(group_id=group.id)

        # assert
        validate_mock.assert_called_once_with()
        get_group_mock.assert_called_once_with(group_id=group.id)
        get_valid_deleted_task_performer_mock.assert_called_once_with(
            group=group,
        )
        delete_group_actions_mock.assert_not_called()

    def test_delete_performer__last_performer__exception(self, mocker):

        # arrange
        account = create_test_account()
        user = create_test_user(account=account)
        group = create_test_group(account, users=[user])
        template = create_test_template(user=user, is_active=True)
        task_template = template.tasks.get(number=1)
        task_template.delete_raw_performers()
        task_template.add_raw_performer(
            group=group,
            performer_type=PerformerType.GROUP,
        )
        workflow = create_test_workflow(user=user, template=template)
        task = workflow.tasks.get(number=1)
        validate_mock = mocker.patch(
            'src.processes.services.tasks.base.'
            'BasePerformerService2._validate',
        )
        get_group_mock = mocker.patch(
            'src.processes.services.tasks.groups.'
            'GroupPerformerService._get_group',
            return_value=group,
        )
        delete_group_actions_mock = mocker.patch(
            'src.processes.services.tasks.groups.'
            'GroupPerformerService._delete_group_actions',
        )

        service = GroupPerformerService(
            user=user,
            task=task,
            is_superuser=False,
            auth_type=AuthTokenType.USER,
        )

        # act
        with pytest.raises(GroupPerformerServiceException) as ex:
            service.delete_performer(group_id=group.id)

        # assert
        assert ex.value.message == messages.MSG_PW_0016
        validate_mock.assert_called_once_with()
        get_group_mock.assert_called_once_with(group_id=group.id)
        delete_group_actions_mock.assert_not_called()

    def test_delete_group_actions__task_not_completed__ok(self, mocker):

        # arrange
        account = create_test_account()
        user = create_test_user(account=account)
        user2 = create_test_user(account=account, email='test2@test.test')
        user3 = create_test_user(account=account, email='test3@test.test')
        group = create_test_group(account, users=[user2, user3])
        template = create_test_template(user=user, is_active=True)
        workflow = create_test_workflow(user=user, template=template)
        task = workflow.tasks.get(number=1)
        performer = task.taskperformer_set.get(user=user)
        performer.is_completed = True
        performer.save()
        task.add_raw_performer(
            group_id=group.id,
            performer_type=PerformerType.GROUP,
        )
        service = GroupPerformerService(
            user=user,
            task=task,
            is_superuser=False,
            auth_type=AuthTokenType.USER,
        )
        performer_group_deleted_event_mock = mocker.patch(
            'src.processes.services.events.'
            'WorkflowEventService.performer_group_deleted_event',
        )
        send_task_deleted_notification_mock = mocker.patch(
            'src.notifications.tasks'
            '.send_removed_task_deleted_notification.delay',
        )
        workflow_action_service_init_mock = mocker.patch.object(
            WorkflowActionService,
            attribute='__init__',
            return_value=None,
        )
        complete_task_mock = mocker.patch(
            'src.processes.services.workflow_action'
            '.WorkflowActionService.complete_task',
        )

        # act
        service._delete_group_actions(group=group)

        # assert
        workflow_action_service_init_mock.assert_called_once_with(
            user=user,
            workflow=workflow,
            is_superuser=False,
            auth_type=AuthTokenType.USER,
        )
        performer_group_deleted_event_mock.assert_called_once_with(
            user=user,
            task=task,
            performer=group,
        )
        send_task_deleted_notification_mock.assert_not_called()
        complete_task_mock.assert_called_once_with(task=task)

    def test_delete_group_actions__task_completed__ok(self, mocker):

        # arrange
        account = create_test_account()
        user = create_test_user(account=account)
        user2 = create_test_user(account=account, email='test2@test.test')
        group = create_test_group(account, users=[user2])
        template = create_test_template(user=user, is_active=True)
        workflow = create_test_workflow(user=user, template=template)
        task = workflow.tasks.get(number=1)
        task.status = TaskStatus.COMPLETED
        task.save()
        TaskPerformer.objects.create(
            task_id=task.id,
            type=PerformerType.GROUP,
            group_id=group.id,
            directly_status=DirectlyStatus.DELETED,
        )
        service = GroupPerformerService(
            user=user,
            task=task,
            is_superuser=False,
            auth_type=AuthTokenType.USER,
        )
        performer_group_deleted_event_mock = mocker.patch(
            'src.processes.services.events.'
            'WorkflowEventService.performer_group_deleted_event',
        )
        send_task_deleted_notification_mock = mocker.patch(
            'src.notifications.tasks'
            '.send_removed_task_deleted_notification.delay',
        )
        workflow_action_service_init_mock = mocker.patch.object(
            WorkflowActionService,
            attribute='__init__',
            return_value=None,
        )
        complete_task_mock = mocker.patch(
            'src.processes.services.workflow_action.'
            'WorkflowActionService.start_workflow',
        )

        # act
        service._delete_group_actions(group=group)

        # assert
        performer_group_deleted_event_mock.assert_called_once_with(
            user=user,
            task=task,
            performer=group,
        )
        send_task_deleted_notification_mock.assert_called_once_with(
            task_id=task.id,
            recipients=[(user2.id, user2.email)],
            account_id=account.id,
        )
        workflow_action_service_init_mock.assert_not_called()
        complete_task_mock.assert_not_called()

    def test_delete_group_actions__user_is_performer__not_send(self, mocker):

        # arrange
        account = create_test_account()
        user = create_test_user(account=account)
        user2 = create_test_user(account=account, email='test2@test.test')
        group = create_test_group(account, users=[user2])
        template = create_test_template(user=user, is_active=True)
        workflow = create_test_workflow(user=user, template=template)
        task = workflow.tasks.get(number=1)
        task.taskperformer_set.create(
            user=user2,
            is_completed=False,
        )
        TaskPerformer.objects.create(
            task_id=task.id,
            type=PerformerType.GROUP,
            group_id=group.id,
            directly_status=DirectlyStatus.DELETED,
        )
        service = GroupPerformerService(
            user=user,
            task=task,
            is_superuser=False,
            auth_type=AuthTokenType.USER,
        )
        performer_group_deleted_event_mock = mocker.patch(
            'src.processes.services.events.'
            'WorkflowEventService.performer_group_deleted_event',
        )
        send_task_deleted_notification_mock = mocker.patch(
            'src.notifications.tasks'
            '.send_removed_task_deleted_notification.delay',
        )
        workflow_action_service_init_mock = mocker.patch.object(
            WorkflowActionService,
            attribute='__init__',
            return_value=None,
        )
        complete_task_mock = mocker.patch(
            'src.processes.services.workflow_action'
            '.WorkflowActionService.complete_task',
        )

        # act
        service._delete_group_actions(group=group)

        # assert
        performer_group_deleted_event_mock.assert_called_once_with(
            user=user,
            task=task,
            performer=group,
        )
        send_task_deleted_notification_mock.assert_not_called()
        workflow_action_service_init_mock.assert_not_called()
        complete_task_mock.assert_not_called()
