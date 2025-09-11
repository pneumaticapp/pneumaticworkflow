import pytest
from django.contrib.auth import get_user_model
from src.authentication.enums import AuthTokenType
from src.processes.tests.fixtures import (
    create_test_user,
    create_test_workflow,
    create_test_guest,
    create_test_account,
    create_test_template,
    create_test_group, create_test_owner, create_test_admin
)
from src.processes.services.tasks.exceptions import (
    GroupPerformerServiceException
)
from src.processes.services.tasks.performers import (
    PerformersServiceException,
)
from src.processes.models import TaskPerformer
from src.utils.validation import ErrorCode
from src.processes.models.templates.owner import (
    TemplateOwner
)
from src.processes.enums import OwnerType

UserModel = get_user_model()
pytestmark = pytest.mark.django_db


class TestTaskCreatePerformer:

    def test_create__request_user_is_account_owner__ok(
        self,
        mocker,
        api_client
    ):

        # arrange
        account = create_test_account()
        account_owner = create_test_user(
            account=account,
            email='owner@test.test',
            is_account_owner=True
        )
        request_user = create_test_user(
            account=account,
            is_admin=True,
            is_account_owner=False
        )
        user_performer = create_test_user(
            account=account,
            email='user2@test.test',
            is_account_owner=False
        )
        template = create_test_template(user=request_user, tasks_count=1)
        TemplateOwner.objects.filter(
            template=template,
            type=OwnerType.USER,
            user_id=account_owner.id
        ).delete()
        workflow = create_test_workflow(user=request_user, template=template)
        task = workflow.tasks.get(number=1)
        api_client.token_authenticate(account_owner)
        service_create_performer_mock = mocker.patch(
            'src.processes.services.tasks.performers.'
            'TaskPerformersService.create_performer'
        )
        current_url = '/page'

        # act
        response = api_client.post(
            f'/v2/tasks/{task.id}/create-performer',
            data={'user_id': user_performer.id},
            **{'HTTP_X_CURRENT_URL': current_url}

        )
        task.refresh_from_db()

        # assert
        assert response.status_code == 204
        service_create_performer_mock.assert_called_once_with(
            task=task,
            user_key=user_performer.id,
            request_user=account_owner,
            current_url=current_url,
            is_superuser=False,
            auth_type=AuthTokenType.USER,
        )
        assert not TemplateOwner.objects.filter(
            template=template,
            type=OwnerType.USER,
            user_id=account_owner.id
        ).exists()

    def test_create__request_user_is_template_owner_admin__ok(
        self,
        mocker,
        api_client
    ):

        # arrange
        account = create_test_account()
        create_test_user(
            account=account,
            email='owner@test.test',
            is_account_owner=True
        )
        request_user = create_test_user(
            account=account,
            is_admin=True,
            is_account_owner=False
        )
        user_performer = create_test_user(
            account=request_user.account,
            email='user2@test.test',
            is_account_owner=False
        )
        template = create_test_template(user=request_user, tasks_count=1)
        workflow = create_test_workflow(user=request_user, template=template)
        task = workflow.tasks.get(number=1)
        api_client.token_authenticate(request_user)
        service_create_performer_mock = mocker.patch(
            'src.processes.services.tasks.performers.'
            'TaskPerformersService.create_performer'
        )
        current_url = '/page'

        # act
        response = api_client.post(
            f'/v2/tasks/{task.id}/create-performer',
            data={'user_id': user_performer.id},
            **{'HTTP_X_CURRENT_URL': current_url}

        )
        task.refresh_from_db()

        # assert
        assert response.status_code == 204
        service_create_performer_mock.assert_called_once_with(
            task=task,
            user_key=user_performer.id,
            request_user=request_user,
            current_url=current_url,
            is_superuser=False,
            auth_type=AuthTokenType.USER
        )

    def test_create__request_user_template_owner_not_admin__permission_denied(
        self,
        mocker,
        api_client
    ):

        # arrange
        account = create_test_account()
        account_owner = create_test_user(
            account=account,
            email='owner@test.test',
            is_account_owner=True
        )
        request_user = create_test_user(
            account=account,
            is_admin=False,
            is_account_owner=False
        )
        user_performer = create_test_user(
            account=request_user.account,
            email='user2@test.test',
            is_account_owner=False
        )
        template = create_test_template(user=account_owner, tasks_count=1)
        TemplateOwner.objects.create(
            template=template,
            account=account,
            type=OwnerType.USER,
            user_id=request_user.id,
        )
        workflow = create_test_workflow(user=account_owner, template=template)
        task = workflow.tasks.get(number=1)
        api_client.token_authenticate(request_user)
        service_create_performer_mock = mocker.patch(
            'src.processes.services.tasks.performers.'
            'TaskPerformersService.create_performer'
        )
        current_url = '/page'

        # act
        response = api_client.post(
            f'/v2/tasks/{task.id}/create-performer',
            data={'user_id': user_performer.id},
            **{'HTTP_X_CURRENT_URL': current_url}

        )
        task.refresh_from_db()

        # assert
        assert response.status_code == 403
        service_create_performer_mock.assert_not_called()

    def test_create__request_user_not_template_owner_admin__permission_denied(
        self,
        mocker,
        api_client
    ):

        # arrange
        account = create_test_account()
        account_owner = create_test_user(
            account=account,
            email='owner@test.test',
            is_account_owner=True
        )
        request_user = create_test_user(
            account=account,
            is_admin=True,
            is_account_owner=False
        )
        user_performer = create_test_user(
            account=account,
            email='user2@test.test',
            is_account_owner=False
        )
        template = create_test_template(user=account_owner, tasks_count=1)
        TemplateOwner.objects.filter(
            template=template,
            type=OwnerType.USER,
            user_id=request_user.id
        ).delete()
        workflow = create_test_workflow(user=account_owner, template=template)
        task = workflow.tasks.get(number=1)
        api_client.token_authenticate(request_user)
        service_create_performer_mock = mocker.patch(
            'src.processes.services.tasks.performers.'
            'TaskPerformersService.create_performer'
        )
        current_url = '/page'

        # act
        response = api_client.post(
            f'/v2/tasks/{task.id}/create-performer',
            data={'user_id': user_performer.id},
            **{'HTTP_X_CURRENT_URL': current_url}

        )
        task.refresh_from_db()

        # assert
        assert response.status_code == 403
        service_create_performer_mock.assert_not_called()
        assert not template.owners.filter(user_id=request_user.id).exists()

    def test_create__request_user_is_not_account_user__not_found(
        self,
        mocker,
        api_client
    ):

        # arrange
        request_user = create_test_user()
        user_performer = create_test_user(
            account=request_user.account,
            email='user3@test.test',
            is_account_owner=False
        )
        another_account_user = create_test_user(email='user2@test.test')
        api_client.token_authenticate(another_account_user)
        workflow = create_test_workflow(request_user)
        task = workflow.tasks.get(number=1)
        service_create_performer_mock = mocker.patch(
            'src.processes.services.tasks.performers.'
            'TaskPerformersService.create_performer'
        )

        # act
        response = api_client.post(
            f'/v2/tasks/{task.id}/create-performer',
            data={'user_id': user_performer.id}
        )

        # assert
        assert response.status_code == 404
        service_create_performer_mock.asert_not_called()

    def test_create__request_user_is_not_authenticated__permission_denied(
        self,
        mocker,
        api_client
    ):
        # arrange
        request_user = create_test_user()
        user_performer = create_test_user(
            account=request_user.account,
            email='user3@test.test',
            is_account_owner=False
        )
        workflow = create_test_workflow(request_user)
        task = workflow.tasks.get(number=1)
        service_create_performer_mock = mocker.patch(
            'src.processes.services.tasks.performers.'
            'TaskPerformersService.create_performer'
        )

        # act
        response = api_client.post(
            f'/v2/tasks/{task.id}/create-performer',
            data={'user_id': user_performer.id}
        )

        # assert
        assert response.status_code == 401
        service_create_performer_mock.asert_not_called()

    def test_create__not_exist_task_id__not_found(
        self,
        mocker,
        api_client
    ):

        # arrange
        account = create_test_account()
        request_user = create_test_owner(account=account)
        user_performer = create_test_admin(account=account)
        api_client.token_authenticate(request_user)
        not_existent_task_id = 999999999
        service_create_performer_mock = mocker.patch(
            'src.processes.services.tasks.performers.'
            'TaskPerformersService.create_performer'
        )

        # act
        response = api_client.post(
            f'/v2/tasks/{not_existent_task_id}/create-performer',
            data={'user_id': user_performer.id}
        )

        # assert
        assert response.status_code == 404
        service_create_performer_mock.asert_not_called()

    def test_create__another_account_task__permission_denied(
        self,
        mocker,
        api_client
    ):

        # arrange
        account = create_test_account()
        request_user = create_test_owner(account=account)
        user_performer = create_test_admin(account=account)
        api_client.token_authenticate(request_user)
        create_test_workflow(request_user)

        another_account = create_test_account()
        another_account_user = create_test_owner(
            account=another_account,
            email='another@test.test'
        )
        another_workflow = create_test_workflow(
            user=another_account_user,
            tasks_count=1
        )
        another_task = another_workflow.tasks.get(number=1)
        service_create_performer_mock = mocker.patch(
            'src.processes.services.tasks.performers.'
            'TaskPerformersService.create_performer'
        )

        # act
        response = api_client.post(
            f'/v2/tasks/{another_task}/create-performer',
            data={'user_id': user_performer.id}
        )

        # assert
        assert response.status_code == 403
        service_create_performer_mock.asert_not_called()

    def test_create__service_exception__validation_error(
        self,
        mocker,
        api_client
    ):

        # arrange
        request_user = create_test_user()
        user_performer = create_test_user(
            account=request_user.account,
            email='user2@test.test',
            is_account_owner=False
        )
        workflow = create_test_workflow(request_user)
        task = workflow.tasks.get(number=1)
        api_client.token_authenticate(request_user)
        error_message = 'error message'
        service_create_performer_mock = mocker.patch(
            'src.processes.services.tasks.performers.'
            'TaskPerformersService.create_performer',
            side_effect=PerformersServiceException(message=error_message)
        )
        current_url = '/page'

        # act
        response = api_client.post(
            f'/v2/tasks/{task.id}/create-performer',
            data={'user_id': user_performer.id},
            **{'HTTP_X_CURRENT_URL': current_url}
        )

        # assert
        assert response.status_code == 400
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['message'] == error_message
        service_create_performer_mock.assert_called_once_with(
            task=task,
            user_key=user_performer.id,
            request_user=request_user,
            current_url=current_url,
            is_superuser=False,
            auth_type=AuthTokenType.USER
        )


class TestTaskDeletePerformer:

    def test_delete__request_user_is_account_owner__ok(
        self,
        mocker,
        api_client
    ):

        # arrange
        account = create_test_account()
        account_owner = create_test_user(
            account=account,
            email='owner@test.test',
            is_account_owner=True
        )
        request_user = create_test_user(
            account=account,
            is_admin=True,
            is_account_owner=False
        )
        user_performer = create_test_user(
            account=account,
            email='user2@test.test',
            is_account_owner=False
        )
        template = create_test_template(user=request_user, tasks_count=1)
        TemplateOwner.objects.filter(
            template=template,
            type=OwnerType.USER,
            user_id=account_owner.id
        ).delete()
        workflow = create_test_workflow(user=request_user, template=template)
        task = workflow.tasks.get(number=1)
        api_client.token_authenticate(account_owner)
        service_delete_performer_mock = mocker.patch(
            'src.processes.services.tasks.performers.'
            'TaskPerformersService.delete_performer'
        )

        # act
        response = api_client.post(
            f'/v2/tasks/{task.id}/delete-performer',
            data={'user_id': user_performer.id}
        )

        # assert
        assert response.status_code == 204
        service_delete_performer_mock.assert_called_once_with(
            task=task,
            user_key=user_performer.id,
            request_user=account_owner,
            is_superuser=False,
            auth_type=AuthTokenType.USER
        )
        assert not TemplateOwner.objects.filter(
            template=template,
            type=OwnerType.USER,
            user_id=account_owner.id
        ).exists()

    def test_delete__request_user_is_template_owner_admin__ok(
        self,
        mocker,
        api_client
    ):

        # arrange
        account = create_test_account()
        create_test_user(
            account=account,
            email='owner@test.test',
            is_account_owner=True
        )
        request_user = create_test_user(
            account=account,
            is_admin=True,
            is_account_owner=False
        )
        user_performer = create_test_user(
            account=account,
            email='user2@test.test',
            is_account_owner=False
        )
        template = create_test_template(user=request_user, tasks_count=1)
        workflow = create_test_workflow(user=request_user, template=template)
        task = workflow.tasks.get(number=1)
        api_client.token_authenticate(request_user)
        service_delete_performer_mock = mocker.patch(
            'src.processes.services.tasks.performers.'
            'TaskPerformersService.delete_performer'
        )

        # act
        response = api_client.post(
            f'/v2/tasks/{task.id}/delete-performer',
            data={'user_id': user_performer.id}
        )

        # assert
        assert response.status_code == 204
        service_delete_performer_mock.assert_called_once_with(
            task=task,
            user_key=user_performer.id,
            request_user=request_user,
            is_superuser=False,
            auth_type=AuthTokenType.USER
        )
        assert template.owners.filter(user_id=request_user.id).exists()

    def test_delete__request_user_not_template_owner_admin__permission_denied(
        self,
        mocker,
        api_client
    ):
        # arrange
        account = create_test_account()
        account_owner = create_test_user(
            account=account,
            email='owner@test.test',
            is_account_owner=True
        )
        request_user = create_test_user(
            account=account,
            is_admin=True,
            is_account_owner=False
        )
        user_performer = create_test_user(
            account=request_user.account,
            email='user2@test.test',
            is_account_owner=False
        )
        template = create_test_template(user=account_owner, tasks_count=1)
        TemplateOwner.objects.filter(
            template=template,
            type=OwnerType.USER,
            user_id=request_user.id
        ).delete()
        workflow = create_test_workflow(user=account_owner, template=template)
        task = workflow.tasks.get(number=1)
        api_client.token_authenticate(request_user)

        service_delete_performer_mock = mocker.patch(
            'src.processes.services.tasks.performers.'
            'TaskPerformersService.delete_performer'
        )

        # act
        response = api_client.post(
            f'/v2/tasks/{task.id}/delete-performer',
            data={'user_id': user_performer.id}
        )

        # assert
        assert response.status_code == 403
        service_delete_performer_mock.asert_not_called()
        assert not template.owners.filter(user_id=request_user.id).exists()

    def test_delete__request_user_template_owner_not_admin__permission_denied(
        self,
        mocker,
        api_client
    ):
        # arrange
        account = create_test_account()
        account_owner = create_test_user(
            account=account,
            email='owner@test.test',
            is_account_owner=True
        )
        request_user = create_test_user(
            account=account,
            is_admin=False,
            is_account_owner=False
        )
        user_performer = create_test_user(
            account=request_user.account,
            email='user2@test.test',
            is_account_owner=False
        )
        template = create_test_template(user=account_owner, tasks_count=1)
        TemplateOwner.objects.create(
            template=template,
            account=account,
            type=OwnerType.USER,
            user_id=request_user.id,
        )
        workflow = create_test_workflow(user=account_owner, template=template)
        task = workflow.tasks.get(number=1)
        api_client.token_authenticate(request_user)
        service_delete_performer_mock = mocker.patch(
            'src.processes.services.tasks.performers.'
            'TaskPerformersService.delete_performer'
        )

        # act
        response = api_client.post(
            f'/v2/tasks/{task.id}/delete-performer',
            data={'user_id': user_performer.id}
        )

        # assert
        assert response.status_code == 403
        service_delete_performer_mock.asert_not_called()

    def test_delete__request_user_is_not_account_user__not_found(
        self,
        mocker,
        api_client
    ):

        # arrange
        template_owner = create_test_user()
        user_performer = create_test_user(
            account=template_owner.account,
            email='user2@test.test',
            is_account_owner=False
        )
        request_user = create_test_user(email='user3@test.test')
        api_client.token_authenticate(request_user)
        workflow = create_test_workflow(template_owner)
        task = workflow.tasks.get(number=1)
        service_delete_performer_mock = mocker.patch(
            'src.processes.services.tasks.performers.'
            'TaskPerformersService.delete_performer'
        )

        # act
        response = api_client.post(
            f'/v2/tasks/{task.id}/delete-performer',
            data={'user_id': user_performer.id}
        )

        # assert
        assert response.status_code == 404
        service_delete_performer_mock.asert_not_called()

    def test_delete__request_user_is_not_authenticated__permission_denied(
        self,
        mocker,
        api_client
    ):
        # arrange
        request_user = create_test_user()
        user_performer = create_test_user(
            account=request_user.account,
            email='user2@test.test',
            is_account_owner=False
        )
        workflow = create_test_workflow(request_user)
        task = workflow.tasks.get(number=1)
        service_delete_performer_mock = mocker.patch(
            'src.processes.services.tasks.performers.'
            'TaskPerformersService.delete_performer'
        )

        # act
        response = api_client.post(
            f'/v2/tasks/{task.id}/delete-performer',
            data={'user_id': user_performer.id}
        )

        # assert
        assert response.status_code == 401
        service_delete_performer_mock.asert_not_called()

    def test_delete___not_exist_task_id__not_found(
        self,
        mocker,
        api_client
    ):
        # arrange
        request_user = create_test_user()
        user_performer = create_test_user(
            account=request_user.account,
            email='user2@test.test',
            is_account_owner=False
        )
        api_client.token_authenticate(request_user)
        create_test_workflow(request_user)
        not_existent_task_id = 9999
        service_delete_performer_mock = mocker.patch(
            'src.processes.services.tasks.performers.'
            'TaskPerformersService.delete_performer'
        )

        # act
        response = api_client.post(
            f'/v2/tasks/{not_existent_task_id}/delete-performer',
            data={'user_id': user_performer.id}
        )

        # assert
        assert response.status_code == 404
        service_delete_performer_mock.asert_not_called()

    def test_delete__service_exception__validation_error(
        self,
        mocker,
        api_client
    ):

        # arrange
        request_user = create_test_user()
        user_performer = create_test_user(
            account=request_user.account,
            email='user2@test.test',
            is_account_owner=False
        )
        workflow = create_test_workflow(request_user)
        task = workflow.tasks.get(number=1)
        api_client.token_authenticate(request_user)
        error_message = 'error message'
        service_delete_performer_mock = mocker.patch(
            'src.processes.services.tasks.performers.'
            'TaskPerformersService.delete_performer',
            side_effect=PerformersServiceException(message=error_message)
        )

        # act
        response = api_client.post(
            f'/v2/tasks/{task.id}/delete-performer',
            data={'user_id': user_performer.id}
        )

        # assert
        assert response.status_code == 400
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['message'] == error_message
        service_delete_performer_mock.assert_called_once_with(
            task=task,
            user_key=user_performer.id,
            request_user=request_user,
            is_superuser=False,
            auth_type=AuthTokenType.USER
        )


class TestCreateGuestPerformer:

    def test_create__request_user_is_account_owner__ok(
        self,
        mocker,
        api_client
    ):

        # arrange
        account = create_test_account()
        account_owner = create_test_user(
            account=account,
            email='owner@test.test',
            is_account_owner=True
        )
        request_user = create_test_user(
            account=account,
            is_admin=True,
            is_account_owner=False
        )
        guest_user = create_test_guest(
            account=request_user.account,
            email='GUEST@TEST.TEST'
        )
        template = create_test_template(user=request_user, tasks_count=1)
        TemplateOwner.objects.filter(
            template=template,
            type=OwnerType.USER,
            user_id=account_owner.id
        ).delete()
        workflow = create_test_workflow(user=request_user, template=template)
        task = workflow.tasks.get(number=1)
        task_performer = TaskPerformer.objects.create(
            task_id=task.id,
            user_id=guest_user.id
        )
        api_client.token_authenticate(account_owner)
        service_create_guest_mock = mocker.patch(
            'src.processes.services.tasks.guests.'
            'GuestPerformersService.create_performer',
            return_value=(guest_user, task_performer)
        )
        current_url = '/page'

        # act
        response = api_client.post(
            f'/v2/tasks/{task.id}/create-guest-performer',
            data={'email': guest_user.email},
            **{'HTTP_X_CURRENT_URL': current_url}
        )

        # assert
        assert response.status_code == 200
        assert response.data['id'] == guest_user.id
        assert response.data['email'] == guest_user.email
        assert response.data['first_name'] == guest_user.first_name
        assert response.data['last_name'] == guest_user.last_name
        assert response.data['phone'] == guest_user.phone
        assert response.data['photo'] == guest_user.photo
        assert response.data['status'] == guest_user.status
        assert response.data['status'] == guest_user.status
        assert response.data['is_admin'] == guest_user.is_admin
        assert response.data['is_account_owner'] == (
            guest_user.is_account_owner
        )
        service_create_guest_mock.assert_called_once_with(
            task=task,
            user_key=guest_user.email.lower(),
            request_user=account_owner,
            current_url=current_url,
            is_superuser=False,
            auth_type=AuthTokenType.USER
        )

    def test_create__request_user_is_template_owner_admin__ok(
        self,
        mocker,
        api_client
    ):

        # arrange
        account = create_test_account()
        create_test_user(
            account=account,
            email='owner@test.test',
            is_account_owner=True
        )
        request_user = create_test_user(
            account=account,
            is_admin=True,
            is_account_owner=False
        )
        guest_user = create_test_guest(
            account=request_user.account,
            email='GUEST@TEST.TEST'
        )
        template = create_test_template(user=request_user, tasks_count=1)
        workflow = create_test_workflow(user=request_user, template=template)
        task = workflow.tasks.get(number=1)
        task_performer = TaskPerformer.objects.create(
            task_id=task.id,
            user_id=guest_user.id
        )
        api_client.token_authenticate(request_user)
        service_create_guest_mock = mocker.patch(
            'src.processes.services.tasks.guests.'
            'GuestPerformersService.create_performer',
            return_value=(guest_user, task_performer)
        )
        current_url = '/page'

        # act
        response = api_client.post(
            f'/v2/tasks/{task.id}/create-guest-performer',
            data={'email': guest_user.email},
            **{'HTTP_X_CURRENT_URL': current_url}
        )

        # assert
        assert response.status_code == 200
        service_create_guest_mock.assert_called_once_with(
            task=task,
            user_key=guest_user.email.lower(),
            request_user=request_user,
            current_url=current_url,
            is_superuser=False,
            auth_type=AuthTokenType.USER
        )

    def test_create__request_user_template_owner_not_admin__permission_denied(
        self,
        mocker,
        api_client
    ):
        # arrange

        account = create_test_account()
        account_owner = create_test_user(
            account=account,
            email='owner@test.test',
            is_account_owner=True
        )
        request_user = create_test_user(
            account=account,
            is_admin=False,
            is_account_owner=False
        )
        guest_email = 'guest@test.test'

        template = create_test_template(user=account_owner, tasks_count=1)
        TemplateOwner.objects.create(
            template=template,
            account=account,
            type=OwnerType.USER,
            user_id=request_user.id,
        )
        workflow = create_test_workflow(user=account_owner, template=template)
        task = workflow.tasks.get(number=1)
        api_client.token_authenticate(request_user)
        service_create_guest_mock = mocker.patch(
            'src.processes.services.tasks.guests.'
            'GuestPerformersService.create_performer'
        )

        # act
        response = api_client.post(
            f'/v2/tasks/{task.id}/create-guest-performer',
            data={'email': guest_email}
        )

        # assert
        assert response.status_code == 403
        service_create_guest_mock.asert_not_called()

    def test_create__request_user_is_not_account_user__not_found(
        self,
        mocker,
        api_client
    ):

        # arrange
        request_user = create_test_user()
        guest_email = 'guest@test.test'
        another_account_user = create_test_user(email='user2@test.test')
        api_client.token_authenticate(another_account_user)
        workflow = create_test_workflow(request_user)
        task = workflow.tasks.get(number=1)
        service_create_guest_mock = mocker.patch(
            'src.processes.services.tasks.guests.'
            'GuestPerformersService.create_performer'
        )

        # act
        response = api_client.post(
            f'/v2/tasks/{task.id}/create-guest-performer',
            data={'email': guest_email}
        )

        # assert
        assert response.status_code == 404
        service_create_guest_mock.asert_not_called()

    def test_create__request_user_is_not_authenticated__permission_denied(
        self,
        mocker,
        api_client
    ):
        # arrange
        request_user = create_test_user()
        guest_email = 'guest@test.test'

        workflow = create_test_workflow(request_user)
        task = workflow.tasks.get(number=1)
        service_create_guest_mock = mocker.patch(
            'src.processes.services.tasks.guests.'
            'GuestPerformersService.create_performer'
        )

        # act
        response = api_client.post(
            f'/v2/tasks/{task.id}/create-guest-performer',
            data={'email': guest_email}
        )

        # assert
        assert response.status_code == 401
        service_create_guest_mock.asert_not_called()

    def test_create__not_exist_task_id__not_found(
        self,
        mocker,
        api_client
    ):

        # arrange
        request_user = create_test_user()
        guest_email = 'guest@test.test'
        api_client.token_authenticate(request_user)
        create_test_workflow(request_user)
        not_existent_task_id = 999999999
        service_create_guest_mock = mocker.patch(
            'src.processes.services.tasks.guests.'
            'GuestPerformersService.create_performer'
        )

        # act
        response = api_client.post(
            f'/v2/tasks/{not_existent_task_id}/create-guest-performer',
            data={'email': guest_email}
        )

        # assert
        assert response.status_code == 404
        service_create_guest_mock.asert_not_called()

    def test_create__service_exception__validation_error(
        self,
        mocker,
        api_client
    ):

        # arrange
        request_user = create_test_user()
        guest_email = 'guest@test.test'
        workflow = create_test_workflow(request_user)
        task = workflow.tasks.get(number=1)
        api_client.token_authenticate(request_user)
        error_message = 'error message'
        service_create_guest_mock = mocker.patch(
            'src.processes.services.tasks.guests.'
            'GuestPerformersService.create_performer',
            side_effect=PerformersServiceException(message=error_message)
        )
        current_url = '/page'

        # act
        response = api_client.post(
            f'/v2/tasks/{task.id}/create-guest-performer',
            data={'email': guest_email},
            **{'HTTP_X_CURRENT_URL': current_url}
        )

        # assert
        assert response.status_code == 400
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['message'] == error_message
        service_create_guest_mock.assert_called_once_with(
            task=task,
            user_key=guest_email,
            request_user=request_user,
            current_url=current_url,
            is_superuser=False,
            auth_type=AuthTokenType.USER
        )


class TestDeleteGuestPerformer:

    def test_delete__request_user_is_account_owner__ok(
        self,
        mocker,
        api_client
    ):

        # arrange
        account = create_test_account()
        account_owner = create_test_user(
            account=account,
            email='owner@test.test',
            is_account_owner=True
        )
        request_user = create_test_user(
            account=account,
            is_admin=True,
            is_account_owner=False
        )
        guest_email = 'guest@test.test'
        template = create_test_template(user=request_user, tasks_count=1)
        TemplateOwner.objects.filter(
            template=template,
            type=OwnerType.USER,
            user_id=account_owner.id
        ).delete()
        workflow = create_test_workflow(user=request_user, template=template)
        task = workflow.tasks.get(number=1)
        api_client.token_authenticate(account_owner)
        service_delete_guest_mock = mocker.patch(
            'src.processes.services.tasks.guests.'
            'GuestPerformersService.delete_performer'
        )

        # act
        response = api_client.post(
            f'/v2/tasks/{task.id}/delete-guest-performer',
            data={'email': guest_email}
        )

        # assert
        assert response.status_code == 204
        service_delete_guest_mock.assert_called_once_with(
            task=task,
            user_key=guest_email,
            request_user=account_owner,
            is_superuser=False,
            auth_type=AuthTokenType.USER
        )
        assert not TemplateOwner.objects.filter(
            template=template,
            type=OwnerType.USER,
            user_id=account_owner.id
        ).exists()

    def test_delete__request_user_is_template_owner_admin__ok(
        self,
        mocker,
        api_client
    ):

        # arrange
        account = create_test_account()
        create_test_user(
            account=account,
            email='owner@test.test',
            is_account_owner=True
        )
        request_user = create_test_user(
            account=account,
            is_admin=True,
            is_account_owner=False
        )
        guest_email = 'guest@test.test'
        template = create_test_template(user=request_user, tasks_count=1)
        workflow = create_test_workflow(user=request_user, template=template)
        task = workflow.tasks.get(number=1)
        api_client.token_authenticate(request_user)
        service_delete_guest_mock = mocker.patch(
            'src.processes.services.tasks.guests.'
            'GuestPerformersService.delete_performer'
        )

        # act
        response = api_client.post(
            f'/v2/tasks/{task.id}/delete-guest-performer',
            data={'email': guest_email}
        )

        # assert
        assert response.status_code == 204
        service_delete_guest_mock.assert_called_once_with(
            task=task,
            user_key=guest_email,
            request_user=request_user,
            is_superuser=False,
            auth_type=AuthTokenType.USER
        )
        assert template.owners.filter(user_id=request_user.id).exists()

    def test_delete__request_user_not_template_owner_admin__permission_denied(
        self,
        mocker,
        api_client
    ):
        # arrange
        account = create_test_account()
        account_owner = create_test_user(
            account=account,
            email='owner@test.test',
            is_account_owner=True
        )
        request_user = create_test_user(
            account=account,
            is_admin=True,
            is_account_owner=False
        )
        guest_email = 'guest@test.test'
        template = create_test_template(user=account_owner, tasks_count=1)
        TemplateOwner.objects.filter(
            template=template,
            type=OwnerType.USER,
            user_id=request_user.id
        ).delete()
        workflow = create_test_workflow(user=account_owner, template=template)
        task = workflow.tasks.get(number=1)
        api_client.token_authenticate(request_user)
        service_delete_guest_mock = mocker.patch(
            'src.processes.services.tasks.guests.'
            'GuestPerformersService.delete_performer'
        )

        # act
        response = api_client.post(
            f'/v2/tasks/{task.id}/delete-guest-performer',
            data={'email': guest_email}
        )

        # assert
        assert response.status_code == 403
        service_delete_guest_mock.asert_not_called()
        assert not template.owners.filter(user_id=request_user.id).exists()

    def test_delete__request_user_template_owner_not_admin__permission_denied(
        self,
        mocker,
        api_client
    ):
        # arrange
        account = create_test_account()
        account_owner = create_test_user(
            account=account,
            email='owner@test.test',
            is_account_owner=True
        )
        request_user = create_test_user(
            account=account,
            is_admin=False,
            is_account_owner=False
        )
        guest_email = 'guest@test.test'
        template = create_test_template(user=account_owner, tasks_count=1)
        TemplateOwner.objects.create(
            template=template,
            account=account,
            type=OwnerType.USER,
            user_id=request_user.id,
        )
        workflow = create_test_workflow(user=account_owner, template=template)
        task = workflow.tasks.get(number=1)
        api_client.token_authenticate(request_user)
        service_delete_guest_mock = mocker.patch(
            'src.processes.services.tasks.guests.'
            'GuestPerformersService.delete_performer'
        )

        # act
        response = api_client.post(
            f'/v2/tasks/{task.id}/delete-guest-performer',
            data={'email': guest_email}
        )

        # assert
        assert response.status_code == 403
        service_delete_guest_mock.asert_not_called()
        assert TemplateOwner.objects.filter(
            template=template,
            type=OwnerType.USER,
            user_id=request_user.id
        ).exists()

    def test_delete__request_user_is_not_account_user__not_found(
        self,
        mocker,
        api_client
    ):

        # arrange
        template_owner = create_test_user()
        guest_email = 'guest@test.test'
        request_user = create_test_user(email='user3@test.test')
        api_client.token_authenticate(request_user)
        workflow = create_test_workflow(template_owner)
        task = workflow.tasks.get(number=1)
        service_delete_guest_mock = mocker.patch(
            'src.processes.services.tasks.guests.'
            'GuestPerformersService.delete_performer'
        )

        # act
        response = api_client.post(
            f'/v2/tasks/{task.id}/delete-guest-performer',
            data={'email': guest_email}
        )

        # assert
        assert response.status_code == 404
        service_delete_guest_mock.asert_not_called()

    def test_delete__request_user_is_not_authenticated__permission_denied(
        self,
        mocker,
        api_client
    ):
        # arrange
        request_user = create_test_user()
        guest_email = 'guest@test.test'

        workflow = create_test_workflow(request_user)
        task = workflow.tasks.get(number=1)
        service_delete_guest_mock = mocker.patch(
            'src.processes.services.tasks.guests.'
            'GuestPerformersService.delete_performer'
        )

        # act
        response = api_client.post(
            f'/v2/tasks/{task.id}/delete-guest-performer',
            data={'email': guest_email}
        )

        # assert
        assert response.status_code == 401
        service_delete_guest_mock.asert_not_called()

    def test_delete___not_exist_task_id__not_found(
        self,
        mocker,
        api_client
    ):

        # arrange
        request_user = create_test_user()
        guest_email = 'guest@test.test'
        api_client.token_authenticate(request_user)
        create_test_workflow(request_user)
        not_existent_task_id = 999999999
        service_delete_guest_mock = mocker.patch(
            'src.processes.services.tasks.guests.'
            'GuestPerformersService.delete_performer'
        )

        # act
        response = api_client.post(
            f'/v2/tasks/{not_existent_task_id}/delete-guest-performer',
            data={'email': guest_email}
        )

        # assert
        assert response.status_code == 404
        service_delete_guest_mock.asert_not_called()

    def test_delete__service_exception__validation_error(
        self,
        mocker,
        api_client
    ):

        # arrange
        request_user = create_test_user()
        guest_email = 'guest@test.test'
        workflow = create_test_workflow(request_user)
        task = workflow.tasks.get(number=1)
        api_client.token_authenticate(request_user)
        error_message = 'error message'
        service_delete_guest_mock = mocker.patch(
            'src.processes.services.tasks.guests.'
            'GuestPerformersService.delete_performer',
            side_effect=PerformersServiceException(message=error_message)
        )

        # act
        response = api_client.post(
            f'/v2/tasks/{task.id}/delete-guest-performer',
            data={'email': guest_email}
        )

        # assert
        assert response.status_code == 400
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['message'] == error_message
        service_delete_guest_mock.assert_called_once_with(
            task=task,
            user_key=guest_email,
            request_user=request_user,
            is_superuser=False,
            auth_type=AuthTokenType.USER
        )


class TestTaskCreateGroupPerformer:
    def test_create__request_user_is_account_owner__ok(
        self,
        mocker,
        api_client
    ):

        # arrange
        account = create_test_account()
        account_owner = create_test_user(
            account=account,
            email='owner@test.test',
            is_account_owner=True
        )
        request_user = create_test_user(
            account=account,
            is_admin=True,
            is_account_owner=False
        )
        user_2 = create_test_user(
            email='t2@t.t',
            account=account,
            is_account_owner=False
        )
        user_3 = create_test_user(
            email='t3@t.t',
            account=account,
            is_account_owner=False
        )
        group = create_test_group(account, users=[user_2, user_3])
        template = create_test_template(user=request_user, tasks_count=1)
        TemplateOwner.objects.filter(
            template=template,
            type=OwnerType.USER,
            user_id=account_owner.id
        ).delete()
        TemplateOwner.objects.filter(
            template=template,
            type=OwnerType.USER,
            user_id=account_owner.id
        ).delete()
        workflow = create_test_workflow(user=request_user, template=template)
        task = workflow.tasks.get(number=1)
        api_client.token_authenticate(account_owner)
        service_create_performer_mock = mocker.patch(
            'src.processes.services.tasks.groups.'
            'GroupPerformerService.create_performer'
        )
        current_url = '/page'

        # act
        response = api_client.post(
            f'/v2/tasks/{task.id}/create-group-performer',
            data={'group_id': group.id},
            **{'HTTP_X_CURRENT_URL': current_url}

        )

        # assert
        assert response.status_code == 204
        service_create_performer_mock.assert_called_once_with(
            group_id=group.id,
        )
        assert not TemplateOwner.objects.filter(
            template=template,
            type=OwnerType.USER,
            user_id=account_owner.id
        ).exists()

    def test_create__request_user_is_template_owner_admin__ok(
        self,
        mocker,
        api_client
    ):

        # arrange
        account = create_test_account()
        create_test_user(
            account=account,
            email='owner@test.test',
            is_account_owner=True
        )
        request_user = create_test_user(
            account=account,
            is_admin=True,
            is_account_owner=False
        )
        user_2 = create_test_user(
            email='t2@t.t',
            account=account,
            is_account_owner=False
        )
        group = create_test_group(account, users=[user_2])
        template = create_test_template(user=request_user, tasks_count=1)
        workflow = create_test_workflow(user=request_user, template=template)
        task = workflow.tasks.get(number=1)
        api_client.token_authenticate(request_user)
        service_create_performer_mock = mocker.patch(
            'src.processes.services.tasks.groups.'
            'GroupPerformerService.create_performer'
        )
        current_url = '/page'

        # act
        response = api_client.post(
            f'/v2/tasks/{task.id}/create-group-performer',
            data={'group_id': group.id},
            **{'HTTP_X_CURRENT_URL': current_url}

        )

        # assert
        assert response.status_code == 204
        service_create_performer_mock.assert_called_once_with(
            group_id=group.id,
        )

    def test_create__request_user_template_owner_not_admin__permission_denied(
        self,
        mocker,
        api_client
    ):

        # arrange
        account = create_test_account()
        account_owner = create_test_user(
            account=account,
            email='owner@test.test',
            is_account_owner=True
        )
        request_user = create_test_user(
            account=account,
            is_admin=False,
            is_account_owner=False
        )
        user_2 = create_test_user(
            email='t2@t.t',
            account=account,
            is_account_owner=False
        )
        group = create_test_group(account, users=[user_2])
        template = create_test_template(user=account_owner, tasks_count=1)
        TemplateOwner.objects.create(
            template=template,
            account=account,
            type=OwnerType.USER,
            user_id=request_user.id,
        )
        workflow = create_test_workflow(user=account_owner, template=template)
        task = workflow.tasks.get(number=1)
        api_client.token_authenticate(request_user)
        service_create_performer_mock = mocker.patch(
            'src.processes.services.tasks.groups.'
            'GroupPerformerService.create_performer'
        )
        current_url = '/page'

        # act
        response = api_client.post(
            f'/v2/tasks/{task.id}/create-group-performer',
            data={'group_id': group.id},
            **{'HTTP_X_CURRENT_URL': current_url}

        )

        # assert
        assert response.status_code == 403
        service_create_performer_mock.assert_not_called()

    def test_create__request_user_not_template_owner_admin__permission_denied(
        self,
        mocker,
        api_client
    ):

        # arrange
        account = create_test_account()
        account_owner = create_test_user(
            account=account,
            email='owner@test.test',
            is_account_owner=True
        )
        request_user = create_test_user(
            account=account,
            is_admin=True,
            is_account_owner=False
        )
        user_2 = create_test_user(
            email='t2@t.t',
            account=account,
            is_account_owner=False
        )
        user_3 = create_test_user(
            email='t3@t.t',
            account=account,
            is_account_owner=False
        )
        group = create_test_group(account, users=[user_2, user_3])
        template = create_test_template(user=account_owner, tasks_count=1)
        TemplateOwner.objects.filter(
            template=template,
            type=OwnerType.USER,
            user_id=request_user.id
        ).delete()
        workflow = create_test_workflow(user=account_owner, template=template)
        task = workflow.tasks.get(number=1)
        api_client.token_authenticate(request_user)
        service_create_performer_mock = mocker.patch(
            'src.processes.services.tasks.groups.'
            'GroupPerformerService.create_performer'
        )
        current_url = '/page'

        # act
        response = api_client.post(
            f'/v2/tasks/{task.id}/create-group-performer',
            data={'group_id': group.id},
            **{'HTTP_X_CURRENT_URL': current_url}

        )

        # assert
        assert response.status_code == 403
        service_create_performer_mock.assert_not_called()
        assert not TemplateOwner.objects.filter(
            template=template,
            type=OwnerType.USER,
            user_id=request_user.id
        ).exists()

    def test_create__request_user_is_not_account_user__not_found(
        self,
        mocker,
        api_client
    ):

        # arrange
        request_user = create_test_user()
        group = create_test_group(request_user.account)
        another_account_user = create_test_user(email='user2@test.test')
        api_client.token_authenticate(another_account_user)
        workflow = create_test_workflow(request_user)
        task = workflow.tasks.get(number=1)
        service_create_performer_mock = mocker.patch(
            'src.processes.services.tasks.groups.'
            'GroupPerformerService.create_performer'
        )

        # act
        response = api_client.post(
            f'/v2/tasks/{task.id}/create-group-performer',
            data={'group_id': group.id}
        )

        # assert
        assert response.status_code == 404
        service_create_performer_mock.asert_not_called()

    def test_create__request_user_is_not_authenticated__permission_denied(
        self,
        mocker,
        api_client
    ):
        # arrange
        request_user = create_test_user()
        group = create_test_group(request_user.account)
        workflow = create_test_workflow(request_user)
        task = workflow.tasks.get(number=1)
        service_create_performer_mock = mocker.patch(
            'src.processes.services.tasks.groups.'
            'GroupPerformerService.create_performer'
        )

        # act
        response = api_client.post(
            f'/v2/tasks/{task.id}/create-performer',
            data={'group_id': group.id}
        )

        # assert
        assert response.status_code == 401
        service_create_performer_mock.asert_not_called()

    def test_create__not_exist_task_id__not_found(
        self,
        mocker,
        api_client
    ):

        # arrange
        request_user = create_test_user()
        group = create_test_group(request_user.account)
        api_client.token_authenticate(request_user)
        create_test_workflow(request_user)
        not_existent_task_id = 999999999
        service_create_performer_mock = mocker.patch(
            'src.processes.services.tasks.groups.'
            'GroupPerformerService.create_performer'
        )

        # act
        response = api_client.post(
            f'/v2/tasks/{not_existent_task_id}/create-group-performer',
            data={'group_id': group.id}
        )

        # assert
        assert response.status_code == 404
        service_create_performer_mock.asert_not_called()

    def test_create__service_exception__validation_error(
        self,
        mocker,
        api_client
    ):

        # arrange
        request_user = create_test_user()
        group = create_test_group(request_user.account)
        workflow = create_test_workflow(request_user)
        task = workflow.tasks.get(number=1)
        api_client.token_authenticate(request_user)
        error_message = 'error message'
        service_create_performer_mock = mocker.patch(
            'src.processes.services.tasks.groups.'
            'GroupPerformerService.create_performer',
            side_effect=GroupPerformerServiceException(message=error_message)
        )
        current_url = '/page'

        # act
        response = api_client.post(
            f'/v2/tasks/{task.id}/create-group-performer',
            data={'group_id': group.id},
            **{'HTTP_X_CURRENT_URL': current_url}
        )

        # assert
        assert response.status_code == 400
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['message'] == error_message
        service_create_performer_mock.assert_called_once_with(
            group_id=group.id,
        )


class TestTaskDeleteGroupPerformer:

    def test_delete__request_user_is_account_owner__ok(
        self,
        mocker,
        api_client
    ):

        # arrange
        account = create_test_account()
        account_owner = create_test_user(
            account=account,
            email='owner@test.test',
            is_account_owner=True
        )
        request_user = create_test_user(
            account=account,
            is_admin=True,
            is_account_owner=False
        )
        group = create_test_group(request_user.account)
        template = create_test_template(user=request_user, tasks_count=1)
        TemplateOwner.objects.filter(
            template=template,
            type=OwnerType.USER,
            user_id=account_owner.id
        ).delete()
        workflow = create_test_workflow(user=request_user, template=template)
        task = workflow.tasks.get(number=1)
        api_client.token_authenticate(account_owner)
        service_delete_performer_mock = mocker.patch(
            'src.processes.services.tasks.groups.'
            'GroupPerformerService.delete_performer'
        )

        # act
        response = api_client.post(
            f'/v2/tasks/{task.id}/delete-group-performer',
            data={'group_id': group.id}
        )

        # assert
        assert response.status_code == 204
        service_delete_performer_mock.assert_called_once_with(
            group_id=group.id,
        )
        assert not TemplateOwner.objects.filter(
            template=template,
            type=OwnerType.USER,
            user_id=account_owner.id
        ).exists()

    def test_delete__request_user_is_template_owner_admin__ok(
        self,
        mocker,
        api_client
    ):

        # arrange
        account = create_test_account()
        create_test_user(
            account=account,
            email='owner@test.test',
            is_account_owner=True
        )
        request_user = create_test_user(
            account=account,
            is_admin=True,
            is_account_owner=False
        )
        group = create_test_group(account)
        template = create_test_template(user=request_user, tasks_count=1)
        workflow = create_test_workflow(user=request_user, template=template)
        task = workflow.tasks.get(number=1)
        api_client.token_authenticate(request_user)
        service_delete_performer_mock = mocker.patch(
            'src.processes.services.tasks.groups.'
            'GroupPerformerService.delete_performer'
        )

        # act
        response = api_client.post(
            f'/v2/tasks/{task.id}/delete-group-performer',
            data={'group_id': group.id}
        )

        # assert
        assert response.status_code == 204
        service_delete_performer_mock.assert_called_once_with(
            group_id=group.id,
        )
        assert TemplateOwner.objects.filter(
            template=template,
            type=OwnerType.USER,
            user_id=request_user.id
        ).exists()

    def test_delete__request_user_not_template_owner_admin__permission_denied(
        self,
        mocker,
        api_client
    ):
        # arrange
        account = create_test_account()
        account_owner = create_test_user(
            account=account,
            email='owner@test.test',
            is_account_owner=True
        )
        request_user = create_test_user(
            account=account,
            is_admin=True,
            is_account_owner=False
        )
        group = create_test_group(account)
        template = create_test_template(user=account_owner, tasks_count=1)
        TemplateOwner.objects.filter(
            template=template,
            type=OwnerType.USER,
            user_id=request_user.id
        ).delete()
        workflow = create_test_workflow(user=account_owner, template=template)
        task = workflow.tasks.get(number=1)
        api_client.token_authenticate(request_user)

        service_delete_performer_mock = mocker.patch(
            'src.processes.services.tasks.groups.'
            'GroupPerformerService.delete_performer'
        )

        # act
        response = api_client.post(
            f'/v2/tasks/{task.id}/delete-group-performer',
            data={'group_id': group.id}
        )

        # assert
        assert response.status_code == 403
        service_delete_performer_mock.asert_not_called()
        assert not TemplateOwner.objects.filter(
            template=template,
            type=OwnerType.USER,
            user_id=request_user.id
        ).exists()

    def test_delete__request_user_template_owner_not_admin__permission_denied(
        self,
        mocker,
        api_client
    ):
        # arrange
        account = create_test_account()
        account_owner = create_test_user(
            account=account,
            email='owner@test.test',
            is_account_owner=True
        )
        request_user = create_test_user(
            account=account,
            is_admin=False,
            is_account_owner=False
        )
        group = create_test_group(account)
        template = create_test_template(user=account_owner, tasks_count=1)
        TemplateOwner.objects.create(
            template=template,
            account=account,
            type=OwnerType.USER,
            user_id=request_user.id,
        )
        workflow = create_test_workflow(user=account_owner, template=template)
        task = workflow.tasks.get(number=1)
        api_client.token_authenticate(request_user)
        service_delete_performer_mock = mocker.patch(
            'src.processes.services.tasks.groups.'
            'GroupPerformerService.delete_performer'
        )

        # act
        response = api_client.post(
            f'/v2/tasks/{task.id}/delete-group-performer',
            data={'group_id': group.id}
        )

        # assert
        assert response.status_code == 403
        service_delete_performer_mock.asert_not_called()

    def test_delete__request_user_is_not_account_user__not_found(
        self,
        mocker,
        api_client
    ):

        # arrange
        template_owner = create_test_user()
        request_user = create_test_user(email='user3@test.test')
        group = create_test_group(template_owner.account)
        api_client.token_authenticate(request_user)
        workflow = create_test_workflow(template_owner)
        task = workflow.tasks.get(number=1)
        service_delete_performer_mock = mocker.patch(
            'src.processes.services.tasks.groups.'
            'GroupPerformerService.delete_performer'
        )

        # act
        response = api_client.post(
            f'/v2/tasks/{task.id}/delete-group-performer',
            data={'group_id': group.id}
        )

        # assert
        assert response.status_code == 404
        service_delete_performer_mock.asert_not_called()

    def test_delete__request_user_is_not_authenticated__permission_denied(
        self,
        mocker,
        api_client
    ):
        # arrange
        request_user = create_test_user()
        group = create_test_group(request_user.account)
        workflow = create_test_workflow(request_user)
        task = workflow.tasks.get(number=1)
        service_delete_performer_mock = mocker.patch(
            'src.processes.services.tasks.groups.'
            'GroupPerformerService.delete_performer'
        )

        # act
        response = api_client.post(
            f'/v2/tasks/{task.id}/delete-group-performer',
            data={'group_id': group.id}
        )

        # assert
        assert response.status_code == 401
        service_delete_performer_mock.asert_not_called()

    def test_delete___not_exist_task_id__not_found(
        self,
        mocker,
        api_client
    ):
        # arrange
        request_user = create_test_user()
        group = create_test_group(request_user.account)
        api_client.token_authenticate(request_user)
        create_test_workflow(request_user)
        not_existent_task_id = 999999999
        service_delete_performer_mock = mocker.patch(
            'src.processes.services.tasks.groups.'
            'GroupPerformerService.delete_performer'
        )

        # act
        response = api_client.post(
            f'/v2/tasks/{not_existent_task_id}/delete-group-performer',
            data={'group_id': group.id}
        )

        # assert
        assert response.status_code == 404
        service_delete_performer_mock.asert_not_called()

    def test_delete__service_exception__validation_error(
        self,
        mocker,
        api_client
    ):

        # arrange
        request_user = create_test_user()
        group = create_test_group(request_user.account)
        workflow = create_test_workflow(request_user)
        task = workflow.tasks.get(number=1)
        api_client.token_authenticate(request_user)
        error_message = 'error message'
        service_delete_performer_mock = mocker.patch(
            'src.processes.services.tasks.groups.'
            'GroupPerformerService.delete_performer',
            side_effect=GroupPerformerServiceException(message=error_message)
        )

        # act
        response = api_client.post(
            f'/v2/tasks/{task.id}/delete-group-performer',
            data={'group_id': group.id}
        )

        # assert
        assert response.status_code == 400
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['message'] == error_message
        service_delete_performer_mock.assert_called_once_with(
            group_id=group.id
        )
