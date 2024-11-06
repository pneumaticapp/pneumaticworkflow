import pytest
from django.contrib.auth import get_user_model
from pneumatic_backend.processes.tests.fixtures import (
    create_test_user,
    create_test_template,
    create_test_workflow,
    create_checklist_template,
    create_test_guest,
    create_test_account,
)
from pneumatic_backend.processes.models import (
    ChecklistSelection,
    TaskPerformer,
)
from pneumatic_backend.processes.api_v2.services.task.exceptions import (
    ChecklistServiceException
)
from pneumatic_backend.processes.api_v2.services.task.performers import (
    TaskPerformersService
)
from pneumatic_backend.authentication.services import GuestJWTAuthService
from pneumatic_backend.utils.validation import ErrorCode


UserModel = get_user_model()
pytestmark = pytest.mark.django_db


class TestChecklistRetrieve:

    def test_retrieve__performer__ok(
        self,
        api_client
    ):

        # arrange
        user = create_test_user()
        user_2 = create_test_user(
            account=user.account,
            email='t@t.t',
            is_account_owner=False
        )
        api_client.token_authenticate(user_2)
        template = create_test_template(
            user=user,
            is_active=True,
            tasks_count=1
        )
        create_checklist_template(task_template=template.tasks.first())
        workflow = create_test_workflow(template=template, user=user)
        task = workflow.tasks.first()
        task.performers.add(user_2)
        checklist = task.checklists.first()

        # act
        response = api_client.get(f'/v2/tasks/checklists/{checklist.id}')

        # assert
        assert response.status_code == 200
        assert response.data['id'] == checklist.id
        assert response.data['api_name'] == checklist.api_name
        selection_data = response.data['selections'][0]
        selection = ChecklistSelection.objects.get(
            checklist=checklist,
            api_name='cl-selection-1',
            value='some value 1'
        )
        assert selection_data['id'] == selection.id
        assert selection_data['api_name'] == selection.api_name
        assert selection_data['is_selected'] == selection.is_selected
        assert selection_data['value'] == selection.value

    def test_retrieve__account_owner__ok(
        self,
        api_client
    ):

        # arrange
        user = create_test_user(is_account_owner=True)
        api_client.token_authenticate(user)
        template = create_test_template(
            user=user,
            is_active=True,
            tasks_count=1
        )
        create_checklist_template(task_template=template.tasks.first())
        workflow = create_test_workflow(template=template, user=user)
        task = workflow.tasks.first()
        checklist = task.checklists.first()

        # act
        response = api_client.get(f'/v2/tasks/checklists/{checklist.id}')

        # assert
        assert response.status_code == 200
        assert response.data['id'] == checklist.id
        assert response.data['api_name'] == checklist.api_name
        selection_data = response.data['selections'][0]
        selection = ChecklistSelection.objects.get(
            checklist=checklist,
            api_name='cl-selection-1',
            value='some value 1'
        )
        assert selection_data['id'] == selection.id
        assert selection_data['api_name'] == selection.api_name
        assert selection_data['is_selected'] == selection.is_selected
        assert selection_data['value'] == selection.value

    def test_retrieve__guest__ok(
        self,
        api_client
    ):

        # arrange
        account = create_test_account()
        account_owner = create_test_user(
            account=account,
            email='owner@test.test',
            is_account_owner=True,
        )
        guest = create_test_guest(account=account)
        template = create_test_template(account_owner, tasks_count=1)
        create_checklist_template(task_template=template.tasks.first())
        workflow = create_test_workflow(
            user=account_owner,
            template=template,
        )
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
        checklist = task.checklists.first()

        # act
        response = api_client.get(
            f'/v2/tasks/checklists/{checklist.id}',
            **{'X-Guest-Authorization': str_token}
        )

        # assert
        assert response.status_code == 200

    def test_retrieve__not_permission__not_found(
        self,
        api_client
    ):

        # arrange
        user = create_test_user()
        user_2 = create_test_user(
            account=user.account,
            email='t@t.t',
            is_account_owner=False
        )
        template = create_test_template(
            user=user,
            is_active=True,
            tasks_count=1
        )
        create_checklist_template(task_template=template.tasks.first())
        workflow = create_test_workflow(template=template, user=user)
        workflow.members.remove(user_2)
        task = workflow.tasks.first()
        checklist = task.checklists.first()
        api_client.token_authenticate(user_2)

        # act
        response = api_client.get(f'/v2/tasks/checklists/{checklist.id}')

        # assert
        assert response.status_code == 404
        assert user_2.is_account_owner is False
        assert not workflow.members.filter(id=user_2.id).exists()
        assert not task.performers.filter(id=user_2.id).exists()

    def test_retrieve__deleted_performer__ok(
        self,
        api_client
    ):

        # arrange
        user = create_test_user()
        user_2 = create_test_user(
            account=user.account,
            email='t@t.t',
            is_account_owner=False
        )
        api_client.token_authenticate(user_2)
        template = create_test_template(
            user=user,
            is_active=True,
            tasks_count=1
        )
        create_checklist_template(task_template=template.tasks.first())
        workflow = create_test_workflow(template=template, user=user)
        task = workflow.tasks.first()
        TaskPerformersService.create_performer(
            request_user=user,
            user_key=user_2.id,
            task=task,
            run_actions=False,
            current_url='/page',
            is_superuser=False
        )
        TaskPerformersService.delete_performer(
            request_user=user,
            user_key=user_2.id,
            task=task,
            run_actions=False
        )
        checklist = task.checklists.first()

        # act
        response = api_client.get(f'/v2/tasks/checklists/{checklist.id}')

        # assert
        assert response.status_code == 200


class TestChecklistMark:

    def test_mark__performer__ok(
        self,
        mocker,
        api_client
    ):

        # arrange
        user = create_test_user()
        api_client.token_authenticate(user)
        template = create_test_template(
            user=user,
            is_active=True,
            tasks_count=1
        )
        create_checklist_template(task_template=template.tasks.first())
        workflow = create_test_workflow(template=template, user=user)
        task = workflow.tasks.first()
        checklist = task.checklists.first()
        selection = ChecklistSelection.objects.get(
            checklist=checklist,
            api_name='cl-selection-1'
        )
        mark_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.views.checklist.'
            'ChecklistService.mark'
        )

        # act
        response = api_client.post(
            path=f'/v2/tasks/checklists/{checklist.id}/mark',
            data={
                'selection_id': selection.id
            }
        )

        # assert
        assert response.status_code == 200
        assert response.data['id'] == checklist.id
        assert response.data['api_name'] == checklist.api_name
        selection_data = response.data['selections'][0]
        selection.refresh_from_db()
        assert selection_data['id'] == selection.id
        assert selection_data['api_name'] == selection.api_name
        assert selection_data['is_selected'] is False
        assert selection_data['value'] == selection.value
        mark_mock.assert_called_once_with(
            selection_id=selection.id
        )

    @pytest.mark.parametrize('value', ('undefined', []))
    def test_mark__invalid_selection_id__validation_error(
        self,
        value,
        mocker,
        api_client
    ):

        # arrange
        user = create_test_user()
        api_client.token_authenticate(user)
        template = create_test_template(
            user=user,
            is_active=True,
            tasks_count=1
        )
        create_checklist_template(task_template=template.tasks.first())
        workflow = create_test_workflow(template=template, user=user)
        task = workflow.tasks.first()
        checklist = task.checklists.first()
        mark_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.views.checklist.'
            'ChecklistService.mark'
        )

        # act
        response = api_client.post(
            path=f'/v2/tasks/checklists/{checklist.id}/mark',
            data={
                'selection_id': value
            }
        )

        # assert
        assert response.status_code == 400
        message = 'A valid integer is required.'
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['message'] == message
        assert response.data['details']['reason'] == message
        assert response.data['details']['name'] == 'selection_id'
        mark_mock.assert_not_called()

    def test_mark__selection_id_is_null__validation_error(
        self,
        mocker,
        api_client
    ):

        # arrange
        user = create_test_user()
        api_client.token_authenticate(user)
        template = create_test_template(
            user=user,
            is_active=True,
            tasks_count=1
        )
        create_checklist_template(task_template=template.tasks.first())
        workflow = create_test_workflow(template=template, user=user)
        task = workflow.tasks.first()
        checklist = task.checklists.first()
        mark_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.views.checklist.'
            'ChecklistService.mark'
        )

        # act
        response = api_client.post(
            path=f'/v2/tasks/checklists/{checklist.id}/mark',
            data={
                'selection_id': None
            }
        )

        # assert
        assert response.status_code == 400
        message = 'This field may not be null.'
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['message'] == message
        assert response.data['details']['reason'] == message
        assert response.data['details']['name'] == 'selection_id'
        mark_mock.assert_not_called()

    def test_mark__service_exception__validation_error(
        self,
        mocker,
        api_client
    ):

        # arrange
        user = create_test_user()
        api_client.token_authenticate(user)
        template = create_test_template(
            user=user,
            is_active=True,
            tasks_count=1
        )
        create_checklist_template(task_template=template.tasks.first())
        workflow = create_test_workflow(template=template, user=user)
        task = workflow.tasks.first()
        checklist = task.checklists.first()
        selection = ChecklistSelection.objects.get(
            checklist=checklist,
            api_name='cl-selection-1'
        )
        message = 'some message'
        mark_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.views.checklist.'
            'ChecklistService.mark',
            side_effect=ChecklistServiceException(message)
        )

        # act
        response = api_client.post(
            path=f'/v2/tasks/checklists/{checklist.id}/mark',
            data={
                'selection_id': selection.id
            }
        )

        # assert
        assert response.status_code == 400
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['message'] == message
        mark_mock.assert_called_once_with(
            selection_id=selection.id
        )

    def test_mark__guest__ok(
        self,
        mocker,
        api_client
    ):

        # arrange
        account = create_test_account()
        account_owner = create_test_user(
            account=account,
            email='owner@test.test',
            is_account_owner=True,
        )
        guest = create_test_guest(account=account)
        template = create_test_template(
            user=account_owner,
            is_active=True,
            tasks_count=1
        )
        create_checklist_template(task_template=template.tasks.first())
        workflow = create_test_workflow(template=template, user=account_owner)
        task = workflow.tasks.first()
        TaskPerformer.objects.create(
            task_id=task.id,
            user_id=guest.id
        )
        checklist = task.checklists.first()
        selection = ChecklistSelection.objects.get(
            checklist=checklist,
            api_name='cl-selection-1'
        )
        mark_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.views.checklist.'
            'ChecklistService.mark'
        )
        str_token = GuestJWTAuthService.get_str_token(
            task_id=task.id,
            user_id=guest.id,
            account_id=account.id
        )

        # act
        response = api_client.post(
            path=f'/v2/tasks/checklists/{checklist.id}/mark',
            data={
                'selection_id': selection.id
            },
            **{'X-Guest-Authorization': str_token}
        )

        # assert
        assert response.status_code == 200
        mark_mock.assert_called_once_with(
            selection_id=selection.id
        )


class TestChecklistUnMark:

    def test_unmark__performer__ok(
        self,
        mocker,
        api_client
    ):

        # arrange
        user = create_test_user()
        api_client.token_authenticate(user)
        template = create_test_template(
            user=user,
            is_active=True,
            tasks_count=1
        )
        create_checklist_template(task_template=template.tasks.first())
        workflow = create_test_workflow(template=template, user=user)
        task = workflow.tasks.first()
        checklist = task.checklists.first()
        selection = ChecklistSelection.objects.get(
            checklist=checklist,
            api_name='cl-selection-1'
        )
        unmark_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.views.checklist.'
            'ChecklistService.unmark'
        )

        # act
        response = api_client.post(
            path=f'/v2/tasks/checklists/{checklist.id}/unmark',
            data={
                'selection_id': selection.id
            }
        )

        # assert
        assert response.status_code == 200
        assert response.data['id'] == checklist.id
        assert response.data['api_name'] == checklist.api_name
        selection_data = response.data['selections'][0]
        selection.refresh_from_db()
        assert selection_data['id'] == selection.id
        assert selection_data['api_name'] == selection.api_name
        assert selection_data['is_selected'] is False
        assert selection_data['value'] == selection.value
        unmark_mock.assert_called_once_with(
            selection_id=selection.id
        )

    @pytest.mark.parametrize('value', ('undefined', []))
    def test_unmark__invalid_selection_id__validation_error(
        self,
        value,
        mocker,
        api_client
    ):

        # arrange
        user = create_test_user()
        api_client.token_authenticate(user)
        template = create_test_template(
            user=user,
            is_active=True,
            tasks_count=1
        )
        create_checklist_template(task_template=template.tasks.first())
        workflow = create_test_workflow(template=template, user=user)
        task = workflow.tasks.first()
        checklist = task.checklists.first()

        mark_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.views.checklist.'
            'ChecklistService.mark'
        )

        # act
        response = api_client.post(
            path=f'/v2/tasks/checklists/{checklist.id}/unmark',
            data={
                'selection_id': value
            }
        )

        # assert
        assert response.status_code == 400
        message = 'A valid integer is required.'
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['message'] == message
        assert response.data['details']['reason'] == message
        assert response.data['details']['name'] == 'selection_id'
        mark_mock.assert_not_called()

    def test_unmark__selection_id_is_null__validation_error(
        self,
        mocker,
        api_client
    ):

        # arrange
        user = create_test_user()
        api_client.token_authenticate(user)
        template = create_test_template(
            user=user,
            is_active=True,
            tasks_count=1
        )
        create_checklist_template(task_template=template.tasks.first())
        workflow = create_test_workflow(template=template, user=user)
        task = workflow.tasks.first()
        checklist = task.checklists.first()
        unmark_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.views.checklist.'
            'ChecklistService.unmark'
        )

        # act
        response = api_client.post(
            path=f'/v2/tasks/checklists/{checklist.id}/unmark',
            data={
                'selection_id': None
            }
        )

        # assert
        assert response.status_code == 400
        message = 'This field may not be null.'
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['message'] == message
        assert response.data['details']['reason'] == message
        assert response.data['details']['name'] == 'selection_id'
        unmark_mock.assert_not_called()

    def test_unmark__service_exception__validation_error(
        self,
        mocker,
        api_client
    ):

        # arrange
        user = create_test_user()
        api_client.token_authenticate(user)
        template = create_test_template(
            user=user,
            is_active=True,
            tasks_count=1
        )
        create_checklist_template(task_template=template.tasks.first())
        workflow = create_test_workflow(template=template, user=user)
        task = workflow.tasks.first()
        checklist = task.checklists.first()
        selection = ChecklistSelection.objects.get(
            checklist=checklist,
            api_name='cl-selection-1'
        )
        message = 'some message'
        unmark_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.views.checklist.'
            'ChecklistService.unmark',
            side_effect=ChecklistServiceException(message)
        )

        # act
        response = api_client.post(
            path=f'/v2/tasks/checklists/{checklist.id}/unmark',
            data={
                'selection_id': selection.id
            }
        )

        # assert
        assert response.status_code == 400
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['message'] == message
        unmark_mock.assert_called_once_with(
            selection_id=selection.id
        )

    def test_unmark__guest__ok(
        self,
        mocker,
        api_client
    ):

        # arrange
        account = create_test_account()
        account_owner = create_test_user(
            account=account,
            email='owner@test.test',
            is_account_owner=True,
        )
        guest = create_test_guest(account=account)
        template = create_test_template(
            user=account_owner,
            is_active=True,
            tasks_count=1
        )
        create_checklist_template(task_template=template.tasks.first())
        workflow = create_test_workflow(template=template, user=account_owner)
        task = workflow.tasks.first()
        TaskPerformer.objects.create(
            task_id=task.id,
            user_id=guest.id
        )
        checklist = task.checklists.first()
        selection = ChecklistSelection.objects.get(
            checklist=checklist,
            api_name='cl-selection-1'
        )
        unmark_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.views.checklist.'
            'ChecklistService.unmark'
        )
        str_token = GuestJWTAuthService.get_str_token(
            task_id=task.id,
            user_id=guest.id,
            account_id=account.id
        )

        # act
        response = api_client.post(
            path=f'/v2/tasks/checklists/{checklist.id}/unmark',
            data={
                'selection_id': selection.id
            },
            **{'X-Guest-Authorization': str_token}
        )

        # assert
        assert response.status_code == 200
        unmark_mock.assert_called_once_with(
            selection_id=selection.id
        )
