import json
import pytest
from rest_framework_simplejwt.exceptions import (
    AuthenticationFailed,
    InvalidToken
)
from pneumatic_backend.authentication.services import GuestJWTAuthService
from pneumatic_backend.authentication.tokens import GuestToken
from pneumatic_backend.processes.tests.fixtures import (
    create_test_workflow,
    create_test_account,
    create_test_user,
    create_test_guest
)
from pneumatic_backend.processes.enums import (
    WorkflowStatus,
    DirectlyStatus
)
from pneumatic_backend.authentication.enums import (
    GuestCachedStatus
)
from pneumatic_backend.accounts.enums import (
    UserStatus
)
from pneumatic_backend.processes.models import TaskPerformer
from pneumatic_backend.authentication import messages


pytestmark = pytest.mark.django_db


class TestGuestJWTAuthService:

    def test_get_str_token__ok(self):

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

        # act
        str_token = GuestJWTAuthService.get_str_token(
            task_id=task.id,
            user_id=guest.id,
            account_id=account.id
        )

        # assert
        token = GuestToken(str_token)
        assert token['account_id'] == account.id
        assert token['user_id'] == guest.id
        assert token['task_id'] == task.id

    def test_authenticate__ok(self, mocker, session_mock):

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
        request = mocker.Mock(
            headers={'X-Guest-Authorization': str_token},
            session=session_mock,
        )

        # act
        user, __ = GuestJWTAuthService().authenticate(request=request)

        # assert
        assert user.id == guest.id

    def test_authenticate__bearer_token__raise_exception(
        self,
        mocker,
        session_mock,
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
        request = mocker.Mock(
            headers={'X-Guest-Authorization': f'Bearer {str_token}'},
            session=session_mock,
        )

        # act
        with pytest.raises(AuthenticationFailed) as ex:
            GuestJWTAuthService().authenticate(request=request)

        # assert
        assert ex.value.detail['detail'] == messages.MSG_AU_0007

    def test_authenticate__invalid_token__raise_exception(self, mocker):

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

        str_invalid_token = 'qwesdsgr.gdfhywefsdd.aeqw3ryr'
        request = mocker.Mock(
            headers={'X-Guest-Authorization': str_invalid_token}
        )

        # act
        with pytest.raises(InvalidToken) as ex:
            GuestJWTAuthService().authenticate(request=request)

        # assert
        assert ex.value.detail['detail'] == messages.MSG_AU_0010

    def test_authenticate__empty_token__return_none(
        self,
        mocker,
        session_mock,
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

        request = mocker.Mock(
            headers={'X-Guest-Authorization': ''},
            session=session_mock,
        )

        # act
        user = GuestJWTAuthService().authenticate(request=request)

        # assert
        assert user is None

    @pytest.mark.parametrize('wf_status', WorkflowStatus.END_STATUSES)
    def test_authenticate__workflow_ended__raise_exception(
        self,
        mocker,
        wf_status,
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
        workflow.status = wf_status
        workflow.save()
        task = workflow.tasks.first()
        TaskPerformer.objects.create(
            task_id=task.id,
            user_id=guest.id
        )

        str_invalid_token = GuestJWTAuthService.get_str_token(
            task_id=task.id,
            user_id=guest.id,
            account_id=account.id
        )
        request = mocker.Mock(
            headers={'X-Guest-Authorization': str_invalid_token}
        )

        # act
        with pytest.raises(AuthenticationFailed) as ex:
            GuestJWTAuthService().authenticate(request=request)

        # assert
        assert ex.value.detail['detail'] == messages.MSG_AU_0009

    def test_authenticate__performer_deleted__raise_exception(self, mocker):

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
            user_id=guest.id,
            directly_status=DirectlyStatus.DELETED
        )
        str_invalid_token = GuestJWTAuthService.get_str_token(
            task_id=task.id,
            user_id=guest.id,
            account_id=account.id
        )
        request = mocker.Mock(
            headers={'X-Guest-Authorization': str_invalid_token}
        )

        # act
        with pytest.raises(AuthenticationFailed) as ex:
            GuestJWTAuthService().authenticate(request=request)

        # assert
        assert ex.value.detail['detail'] == messages.MSG_AU_0009

    def test_authenticate__guest_inactive__raise_exception(self, mocker):

        # arrange
        account = create_test_account()
        account_owner = create_test_user(
            account=account,
            email='owner@test.test',
            is_account_owner=True,
        )
        guest = create_test_guest(account=account)
        guest.status = UserStatus.INACTIVE
        guest.save()
        workflow = create_test_workflow(account_owner, tasks_count=1)
        task = workflow.tasks.first()
        TaskPerformer.objects.create(
            task_id=task.id,
            user_id=guest.id,
        )
        str_invalid_token = GuestJWTAuthService.get_str_token(
            task_id=task.id,
            user_id=guest.id,
            account_id=account.id
        )
        request = mocker.Mock(
            headers={'X-Guest-Authorization': str_invalid_token}
        )

        # act
        with pytest.raises(AuthenticationFailed) as ex:
            GuestJWTAuthService().authenticate(request=request)

        # assert
        assert ex.value.detail['detail'] == messages.MSG_AU_0009

    def test_set_guest_cache__create_new__ok(self, mocker):

        # arrange
        task_id = 55
        user_id = 44
        key = f'task-{task_id}-guests'
        result_json_value = json.dumps({user_id: GuestCachedStatus.ACTIVE})
        cache_get_mock = mocker.patch(
            'pneumatic_backend.authentication.services.guest_auth.'
            'GuestJWTAuthService.cache.get',
            return_value=None
        )
        cache_set_mock = mocker.patch(
            'pneumatic_backend.authentication.services.guest_auth.'
            'GuestJWTAuthService.cache.set'
        )
        service = GuestJWTAuthService()

        # act
        service._set_guest_cache(
            task_id=task_id,
            user_id=user_id,
            status=GuestCachedStatus.ACTIVE
        )

        # assert
        cache_get_mock.assert_called_once_with(key, {})
        cache_set_mock.assert_called_once_with(
            key, result_json_value, service.CACHE_TIMEOUT
        )

    def test_set_guest_cache__update_existent__ok(self, mocker):

        # arrange
        task_id = 55
        user_id = 44
        key = f'task-{task_id}-guests'
        cache_json_value = json.dumps({
            user_id: GuestCachedStatus.INACTIVE,
            45: GuestCachedStatus.INACTIVE
        })
        result_json_value = json.dumps({
            user_id: GuestCachedStatus.ACTIVE,
            45: GuestCachedStatus.INACTIVE
        })
        cache_get_mock = mocker.patch(
            'pneumatic_backend.authentication.services.guest_auth.'
            'GuestJWTAuthService.cache.get',
            return_value=cache_json_value
        )
        cache_set_mock = mocker.patch(
            'pneumatic_backend.authentication.services.guest_auth.'
            'GuestJWTAuthService.cache.set'
        )
        service = GuestJWTAuthService()

        # act
        service._set_guest_cache(
            task_id=task_id,
            user_id=user_id,
            status=GuestCachedStatus.ACTIVE
        )

        # assert
        cache_get_mock.assert_called_once_with(key, {})
        cache_set_mock.assert_called_once_with(
            key, result_json_value, service.CACHE_TIMEOUT
        )

    def test_set_guest_cache__for_all_guest_users__ok(self, mocker):

        # arrange
        task_id = 55
        key = f'task-{task_id}-guests'
        cache_json_value = json.dumps({
            44: GuestCachedStatus.INACTIVE,
            45: GuestCachedStatus.INACTIVE
        })
        result_json_value = json.dumps({
            44: GuestCachedStatus.ACTIVE,
            45: GuestCachedStatus.ACTIVE
        })
        cache_get_mock = mocker.patch(
            'pneumatic_backend.authentication.services.guest_auth'
            '.GuestJWTAuthService.cache.get',
            return_value=cache_json_value
        )
        cache_set_mock = mocker.patch(
            'pneumatic_backend.authentication.services.guest_auth'
            '.GuestJWTAuthService.cache.set',
        )
        service = GuestJWTAuthService()

        # act
        service._set_guest_cache(
            task_id=task_id,
            status=GuestCachedStatus.ACTIVE
        )

        # assert
        cache_get_mock.assert_called_once_with(key, {})
        cache_set_mock.assert_called_once_with(
            key, result_json_value, service.CACHE_TIMEOUT
        )

    def test_deactivate_task_guest_cache__ok(self, mocker):

        # act
        task_id = 55
        user_id = 45
        set_guest_cache_mock = mocker.patch(
            'pneumatic_backend.authentication.services.GuestJWTAuthService'
            '._set_guest_cache'
        )

        # act
        GuestJWTAuthService.deactivate_task_guest_cache(
            task_id=task_id,
            user_id=user_id
        )

        # assert
        set_guest_cache_mock.assert_called_once_with(
            task_id=task_id,
            user_id=user_id,
            status=GuestCachedStatus.INACTIVE
        )

    def test_activate_task_guest_cache__ok(self, mocker):

        # act
        task_id = 55
        user_id = 45
        set_guest_cache_mock = mocker.patch(
            'pneumatic_backend.authentication.services.GuestJWTAuthService'
            '._set_guest_cache'
        )

        # act
        GuestJWTAuthService.activate_task_guest_cache(
            task_id=task_id,
            user_id=user_id
        )

        # assert
        set_guest_cache_mock.assert_called_once_with(
            task_id=task_id,
            user_id=user_id,
            status=GuestCachedStatus.ACTIVE
        )

    def test_get_cached_user__active_and_user_exists__ok(self, mocker):

        # arrange
        owner = create_test_user(
            is_account_owner=True,
            email='owner@test.test',
        )
        guest = create_test_guest(account=owner.account)
        task_id = 55
        key = f'task-{task_id}-guests'
        service = GuestJWTAuthService()
        token = service.get_token(
            task_id=task_id,
            user_id=guest.id,
            account_id=guest.account_id
        )
        cache_json_value = json.dumps({
            guest.id: GuestCachedStatus.ACTIVE,
        })
        cache_get_mock = mocker.patch(
            'pneumatic_backend.authentication.services.guest_auth.'
            'GuestJWTAuthService.cache.get',
            return_value=cache_json_value
        )
        cache_set_mock = mocker.patch(
            'pneumatic_backend.authentication.services.guest_auth.'
            'GuestJWTAuthService.cache.set'
        )

        # act
        user = service.get_cached_user(
            validated_token=token
        )

        # assert
        assert user.id == guest.id
        cache_get_mock.assert_called_once_with(key, {})
        cache_set_mock.assert_not_called()

    def test_get_cached_user__active_and_not_user_exists__raise_exception(
        self,
        mocker
    ):

        # arrange
        account_id = 35
        user_id = 45
        task_id = 55
        key = f'task-{task_id}-guests'
        service = GuestJWTAuthService()
        token = service.get_token(
            task_id=task_id,
            user_id=user_id,
            account_id=account_id
        )
        cache_json_value = json.dumps({
            user_id: GuestCachedStatus.ACTIVE,
        })
        result_json_value = json.dumps({
            user_id: GuestCachedStatus.INACTIVE,
        })
        cache_get_mock = mocker.patch(
            'pneumatic_backend.authentication.services.guest_auth.'
            'GuestJWTAuthService.cache.get',
            return_value=cache_json_value
        )
        cache_set_mock = mocker.patch(
            'pneumatic_backend.authentication.services.guest_auth.'
            'GuestJWTAuthService.cache.set'
        )

        # act
        with pytest.raises(AuthenticationFailed):
            service.get_cached_user(validated_token=token)

        # assert
        cache_get_mock.assert_called_once_with(key, {})
        cache_set_mock.assert_called_once_with(
            key,
            result_json_value,
            service.CACHE_TIMEOUT
        )

    def test_get_cached_user__inactive__raise_exception(
        self,
        mocker
    ):

        # arrange
        account_id = 35
        user_id = 45
        task_id = 55
        key = f'task-{task_id}-guests'
        service = GuestJWTAuthService()
        token = service.get_token(
            task_id=task_id,
            user_id=user_id,
            account_id=account_id
        )
        cache_json_value = json.dumps({
            user_id: GuestCachedStatus.INACTIVE,
        })
        cache_get_mock = mocker.patch(
            'pneumatic_backend.authentication.services.guest_auth.'
            'GuestJWTAuthService.cache.get',
            return_value=cache_json_value
        )
        cache_set_mock = mocker.patch(
            'pneumatic_backend.authentication.services.guest_auth.'
            'GuestJWTAuthService.cache.set'
        )

        # act
        with pytest.raises(AuthenticationFailed):
            service.get_cached_user(validated_token=token)

        # assert
        cache_get_mock.assert_called_once_with(key, {})
        cache_set_mock.assert_not_called()

    def test_get_cached_user__not_in_cache_get_from_db__ok(self, mocker):

        # arrange
        owner = create_test_user(
            is_account_owner=True,
            email='owner@test.test',
        )
        guest = create_test_guest(account=owner.account)
        task_id = 55
        key = f'task-{task_id}-guests'
        service = GuestJWTAuthService()
        token = service.get_token(
            task_id=task_id,
            user_id=guest.id,
            account_id=guest.account_id
        )
        result_json_value = json.dumps({
            guest.id: GuestCachedStatus.ACTIVE,
        })
        cache_get_mock = mocker.patch(
            'pneumatic_backend.authentication.services.guest_auth.'
            'GuestJWTAuthService.cache.get',
            return_value=None
        )
        cache_set_mock = mocker.patch(
            'pneumatic_backend.authentication.services.guest_auth.'
            'GuestJWTAuthService.cache.set'
        )
        get_user_mock = mocker.patch(
            'pneumatic_backend.authentication.services.guest_auth.'
            'GuestJWTAuthService.get_user',
            return_value=guest
        )

        # act
        user = service.get_cached_user(
            validated_token=token
        )

        # assert
        assert user.id == guest.id
        cache_get_mock.assert_called_once_with(key, {})
        cache_set_mock.assert_called_once_with(
            key,
            result_json_value,
            service.CACHE_TIMEOUT
        )
        get_user_mock.assert_called_once_with(token)

    def test_get_cached_user__not_in_cache_not_in_db__raise_exception(
        self,
        mocker
    ):

        # arrange
        account_id = 35
        user_id = 55
        task_id = 55
        key = f'task-{task_id}-guests'
        service = GuestJWTAuthService()
        token = service.get_token(
            task_id=task_id,
            user_id=user_id,
            account_id=account_id
        )
        result_json_value = json.dumps({
            user_id: GuestCachedStatus.INACTIVE,
        })
        cache_get_mock = mocker.patch(
            'pneumatic_backend.authentication.services.guest_auth.'
            'GuestJWTAuthService.cache.get',
            return_value=None
        )
        cache_set_mock = mocker.patch(
            'pneumatic_backend.authentication.services.guest_auth.'
            'GuestJWTAuthService.cache.set'
        )
        get_user_mock = mocker.patch(
            'pneumatic_backend.authentication.services.guest_auth.'
            'GuestJWTAuthService.get_user',
            side_effect=AuthenticationFailed()
        )

        # act
        with pytest.raises(AuthenticationFailed):
            service.get_cached_user(validated_token=token)

        # assert
        cache_get_mock.assert_called_once_with(key, {})
        cache_set_mock.assert_called_once_with(
            key,
            result_json_value,
            service.CACHE_TIMEOUT
        )
        get_user_mock.assert_called_once_with(token)

    def test_get_user__ok(self):

        # arrange
        account = create_test_account()
        account_owner = create_test_user(
            account=account,
            is_account_owner=True
        )
        guest = create_test_guest(account=account)
        workflow = create_test_workflow(user=account_owner, tasks_count=2)
        task_1 = workflow.tasks.get(number=1)
        TaskPerformer.objects.create(
            task_id=task_1.id,
            user_id=guest.id
        )
        service = GuestJWTAuthService()
        token = service.get_token(
            task_id=task_1.id,
            user_id=guest.id,
            account_id=account.id
        )

        # act
        user = service.get_user(token)

        # assert
        assert user.id == guest.id

    def test_get_user__task_not_started__raise_exception(self):

        # arrange
        account = create_test_account()
        account_owner = create_test_user(
            account=account,
            is_account_owner=True
        )
        guest = create_test_guest(account=account)
        workflow = create_test_workflow(user=account_owner, tasks_count=2)
        task_2 = workflow.tasks.get(number=2)
        TaskPerformer.objects.create(
            task_id=task_2.id,
            user_id=guest.id
        )
        service = GuestJWTAuthService()
        token = service.get_token(
            task_id=task_2.id,
            user_id=guest.id,
            account_id=account.id
        )

        # act
        with pytest.raises(AuthenticationFailed) as ex:
            service.get_user(token)

        # assert
        assert ex.value.detail['detail'] == messages.MSG_AU_0009
