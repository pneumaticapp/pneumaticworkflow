import pytest
from pneumatic_backend.processes.permissions import GuestTaskPermission
from pneumatic_backend.processes.tests.fixtures import (
    create_test_template,
    create_checklist_template,
    create_test_guest,
    create_test_user,
    create_test_workflow,
)

pytestmark = pytest.mark.django_db


class TestGuestPermission:

    def test_has_permission__user__return_true(self, mocker):

        # arrange
        user = create_test_user()
        request_mock = mocker.Mock()
        request_mock.user = user
        permission = GuestTaskPermission()

        # act
        result = permission.has_permission(
            request=request_mock,
            view=mocker.Mock()
        )

        # assert
        assert result is True

    def test_has_permission__guest__check_access(self, mocker):

        # arrange
        guest = create_test_guest()
        request_mock = mocker.Mock()
        request_mock.user = guest
        permission = GuestTaskPermission()
        request_to_task_mock = mocker.patch(
            'pneumatic_backend.processes.permissions.GuestTaskPermission.'
            '_request_to_task',
            return_value=False
        )
        request_to_checklist = mocker.patch(
            'pneumatic_backend.processes.permissions.GuestTaskPermission.'
            '_request_to_checklist',
            return_value=False
        )

        # act
        result = permission.has_permission(
            request=request_mock,
            view=mocker.Mock()
        )

        # assert
        assert result is False
        request_to_task_mock.assert_called_with(request_mock)
        request_to_checklist.assert_called_with(request_mock)

    @pytest.mark.parametrize(
        'path',
        (
            '/v2/tasks/1',
            '/v2/tasks/1/'
        )
    )
    def test_request_to_task__return_true(self, path, mocker):

        # arrange
        request_mock = mocker.Mock()
        request_mock.path = path
        request_mock.task_id = 1
        permission = GuestTaskPermission()

        # act
        result = permission._request_to_task(request_mock)

        # assert
        assert result is True

    @pytest.mark.parametrize(
        'path',
        (
            '/v2/tasks/',
            '/v2/tasks/a/'
            '/v2/tasks/null/'
            '/tasks/1'
            '/tasks/1/checklists'
        )
    )
    def test_request_to_task__invalid_path__return_false(self, path, mocker):

        # arrange
        request_mock = mocker.Mock()
        request_mock.path = path
        request_mock.task_id = 1
        permission = GuestTaskPermission()

        # act
        result = permission._request_to_task(request_mock)

        # assert
        assert result is False

    def test_request_to_task__invalid_task_id__return_false(
        self,
        mocker
    ):

        # arrange
        request_mock = mocker.Mock()
        request_mock.task_id = 2
        request_mock.path = '/v2/tasks/1'
        permission = GuestTaskPermission()

        # act
        result = permission._request_to_task(request_mock)

        # assert
        assert result is False

    @pytest.mark.parametrize(
        'path',
        (
            '/v2/tasks/checklists/%d',
            '/v2/tasks/checklists/%d/',
            '/v2/tasks/checklists/%d/mark',
            '/v2/tasks/checklists/%d/mark/',
            '/v2/tasks/checklists/%d/unmark',
            '/v2/tasks/checklists/%d/unmark/',
        )
    )
    def test_request_to_checklist__return_true(self, path, mocker):

        # arrange
        user = create_test_user()
        template = create_test_template(user, tasks_count=1)
        create_checklist_template(task_template=template.tasks.first())
        workflow = create_test_workflow(user=user, template=template)
        task = workflow.tasks.first()
        checklist = task.checklists.first()
        checklist_path = path % checklist.id
        request_mock = mocker.Mock()
        request_mock.path = checklist_path
        request_mock.task_id = task.id
        permission = GuestTaskPermission()

        # act
        result = permission._request_to_checklist(request_mock)

        # assert
        assert result is True

    @pytest.mark.parametrize(
        'path',
        (
            '/tasks/checklists/1',
            '/v2/tasks/performers',
            '/v2/tasks/checklists/m',
            '/v2/tasks/checklists/null',
            '/v2/tasks/checklists/a/mark',
            '/v2/tasks/performers/null/mark ',
        )
    )
    def test_request_to_checklist__invalid_path_return_false(
        self,
        path,
        mocker
    ):

        # arrange
        request_mock = mocker.Mock()
        request_mock.path = path
        permission = GuestTaskPermission()

        # act
        result = permission._request_to_checklist(request_mock)

        # assert
        assert result is False

    def test_request_to_checklist__invalid_task_id__return_false(
        self,
        mocker
    ):

        # arrange
        user = create_test_user()
        template = create_test_template(user, tasks_count=2)
        create_checklist_template(task_template=template.tasks.get(number=1))
        workflow = create_test_workflow(user=user, template=template)
        task_1 = workflow.tasks.get(number=1)
        task_2 = workflow.tasks.get(number=2)
        checklist = task_1.checklists.first()
        request_mock = mocker.Mock()
        request_mock.path = f'/v2/tasks/checklists/{checklist.id}/'
        request_mock.task_id = task_2.id
        permission = GuestTaskPermission()

        # act
        result = permission._request_to_checklist(request_mock)

        # assert
        assert result is False
