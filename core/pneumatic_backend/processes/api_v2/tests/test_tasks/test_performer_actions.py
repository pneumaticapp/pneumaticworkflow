import pytest
from django.contrib.auth import get_user_model
from pneumatic_backend.processes.tests.fixtures import (
    create_test_user,
    create_test_workflow,
    create_test_guest,
    create_test_account,
    create_test_template,
)
from pneumatic_backend.processes.api_v2.services.task.exceptions import (
    PerformersServiceException
)
from pneumatic_backend.processes.models import TaskPerformer
from pneumatic_backend.utils.validation import ErrorCode


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
        template.template_owners.remove(account_owner)
        workflow = create_test_workflow(user=request_user, template=template)
        task = workflow.current_task_instance
        api_client.token_authenticate(account_owner)
        service_create_performer_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.services.task.performers.'
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
            is_superuser=False
        )
        assert not template.template_owners.filter(
            id=account_owner.id
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
        task = workflow.current_task_instance
        api_client.token_authenticate(request_user)
        service_create_performer_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.services.task.performers.'
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
            is_superuser=False
        )
        assert template.template_owners.filter(id=request_user.id).exists()

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
        template.template_owners.add(request_user)
        workflow = create_test_workflow(user=account_owner, template=template)
        task = workflow.current_task_instance
        api_client.token_authenticate(request_user)
        service_create_performer_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.services.task.performers.'
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
        template.template_owners.remove(request_user)
        workflow = create_test_workflow(user=account_owner, template=template)

        task = workflow.current_task_instance
        api_client.token_authenticate(request_user)
        service_create_performer_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.services.task.performers.'
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
        assert not template.template_owners.filter(id=request_user.id).exists()

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
        task = workflow.current_task_instance
        service_create_performer_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.services.task.performers.'
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
        task = workflow.current_task_instance
        service_create_performer_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.services.task.performers.'
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
        request_user = create_test_user()
        user_performer = create_test_user(
            account=request_user.account,
            email='user2@test.test',
            is_account_owner=False
        )
        api_client.token_authenticate(request_user)
        create_test_workflow(request_user)
        not_existent_task_id = 999
        service_create_performer_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.services.task.performers.'
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
        task = workflow.current_task_instance
        api_client.token_authenticate(request_user)
        error_message = 'error message'
        service_create_performer_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.services.task.performers.'
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
            is_superuser=False
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
        template.template_owners.remove(account_owner)
        workflow = create_test_workflow(user=request_user, template=template)
        task = workflow.current_task_instance
        api_client.token_authenticate(account_owner)
        service_delete_performer_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.services.task.performers.'
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
        )
        assert not template.template_owners.filter(
            id=account_owner.id
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
        task = workflow.current_task_instance
        api_client.token_authenticate(request_user)
        service_delete_performer_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.services.task.performers.'
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
        )
        assert template.template_owners.filter(id=request_user.id).exists()

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
        template.template_owners.remove(request_user)
        workflow = create_test_workflow(user=account_owner, template=template)
        task = workflow.current_task_instance
        api_client.token_authenticate(request_user)

        service_delete_performer_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.services.task.performers.'
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
        assert not template.template_owners.filter(id=request_user.id).exists()

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
        template.template_owners.add(request_user)
        workflow = create_test_workflow(user=account_owner, template=template)
        task = workflow.current_task_instance
        api_client.token_authenticate(request_user)
        service_delete_performer_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.services.task.performers.'
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
        task = workflow.current_task_instance
        service_delete_performer_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.services.task.performers.'
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
        task = workflow.current_task_instance
        service_delete_performer_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.services.task.performers.'
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
        not_existent_task_id = 999
        service_delete_performer_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.services.task.performers.'
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
        task = workflow.current_task_instance
        api_client.token_authenticate(request_user)
        error_message = 'error message'
        service_delete_performer_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.services.task.performers.'
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
            request_user=request_user
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
        template.template_owners.remove(account_owner)
        workflow = create_test_workflow(user=request_user, template=template)
        task = workflow.current_task_instance
        task_performer = TaskPerformer.objects.create(
            task_id=task.id,
            user_id=guest_user.id
        )
        api_client.token_authenticate(account_owner)
        service_create_guest_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.services.task.guests.'
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
        assert response.data['is_staff'] == guest_user.is_admin
        assert response.data['is_admin'] == guest_user.is_admin
        assert response.data['is_account_owner'] == (
            guest_user.is_account_owner
        )
        service_create_guest_mock.assert_called_once_with(
            task=task,
            user_key=guest_user.email.lower(),
            request_user=account_owner,
            current_url=current_url,
            is_superuser=False
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
        task = workflow.current_task_instance
        task_performer = TaskPerformer.objects.create(
            task_id=task.id,
            user_id=guest_user.id
        )
        api_client.token_authenticate(request_user)
        service_create_guest_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.services.task.guests.'
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
            is_superuser=False
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
        template.template_owners.add(request_user)
        workflow = create_test_workflow(user=account_owner, template=template)
        task = workflow.current_task_instance
        api_client.token_authenticate(request_user)
        service_create_guest_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.services.task.guests.'
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
        task = workflow.current_task_instance
        service_create_guest_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.services.task.guests.'
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
        task = workflow.current_task_instance
        service_create_guest_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.services.task.guests.'
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
        not_existent_task_id = 999
        service_create_guest_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.services.task.guests.'
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
        task = workflow.current_task_instance
        api_client.token_authenticate(request_user)
        error_message = 'error message'
        service_create_guest_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.services.task.guests.'
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
            is_superuser=False
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
        template.template_owners.remove(account_owner)
        workflow = create_test_workflow(user=request_user, template=template)
        task = workflow.current_task_instance
        api_client.token_authenticate(account_owner)
        service_delete_guest_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.services.task.guests.'
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
            request_user=account_owner
        )
        assert not template.template_owners.filter(
            id=account_owner.id
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
        task = workflow.current_task_instance
        api_client.token_authenticate(request_user)
        service_delete_guest_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.services.task.guests.'
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
            request_user=request_user
        )
        assert template.template_owners.filter(id=request_user.id).exists()

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
        template.template_owners.remove(request_user)
        workflow = create_test_workflow(user=account_owner, template=template)
        task = workflow.current_task_instance
        api_client.token_authenticate(request_user)
        service_delete_guest_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.services.task.guests.'
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
        assert not template.template_owners.filter(id=request_user.id).exists()

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
        template.template_owners.add(request_user)
        workflow = create_test_workflow(user=account_owner, template=template)
        task = workflow.current_task_instance
        api_client.token_authenticate(request_user)
        service_delete_guest_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.services.task.guests.'
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
        assert template.template_owners.filter(id=request_user.id).exists()

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
        task = workflow.current_task_instance
        service_delete_guest_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.services.task.guests.'
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
        task = workflow.current_task_instance
        service_delete_guest_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.services.task.guests.'
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
        not_existent_task_id = 999
        service_delete_guest_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.services.task.guests.'
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
        task = workflow.current_task_instance
        api_client.token_authenticate(request_user)
        error_message = 'error message'
        service_delete_guest_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.services.task.guests.'
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
            request_user=request_user
        )
