import pytest
from django.contrib.auth import get_user_model
from unittest.mock import Mock

from src.processes.enums import ViewerType, OwnerType
from src.processes.models.templates.viewer import TemplateViewer
from src.processes.models.templates.owner import TemplateOwner
from src.processes.models.workflows.task import TaskPerformer
from src.processes.permissions import TaskCommentPermission
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_group,
    create_test_template,
    create_test_user,
    create_test_workflow,
)

UserModel = get_user_model()

pytestmark = pytest.mark.django_db


class TestTaskCommentPermission:

    def test_has_permission__account_owner__ok(self):
        # arrange
        account = create_test_account()
        account_owner = create_test_user(
            account=account,
            is_account_owner=True,
        )
        template = create_test_template(user=account_owner)
        workflow = create_test_workflow(template=template, user=account_owner)
        task = workflow.tasks.get(number=1)

        request = Mock()
        request.user = account_owner

        view = Mock()
        view.kwargs = {'pk': str(task.id)}

        permission = TaskCommentPermission()

        # act
        result = permission.has_permission(request, view)

        # assert
        assert result is True

    def test_has_permission__admin__ok(self):
        # arrange
        account = create_test_account()
        admin_user = create_test_user(
            account=account,
            is_admin=True,
        )
        template_owner = create_test_user(
            account=account, email='owner@test.com',
        )
        template = create_test_template(user=template_owner)
        workflow = create_test_workflow(template=template, user=template_owner)
        task = workflow.tasks.get(number=1)

        request = Mock()
        request.user = admin_user

        view = Mock()
        view.kwargs = {'pk': str(task.id)}

        permission = TaskCommentPermission()

        # act
        result = permission.has_permission(request, view)

        # assert
        assert result is True

    def test_has_permission__workflow_member__ok(self):
        # arrange
        account = create_test_account()
        template_owner = create_test_user(account=account)
        template = create_test_template(user=template_owner)
        workflow = create_test_workflow(template=template, user=template_owner)
        task = workflow.tasks.get(number=1)

        member_user = create_test_user(
            account=account,
            email='member@test.com',
            is_account_owner=False,
            is_admin=False,
        )
        workflow.members.add(member_user)

        request = Mock()
        request.user = member_user

        view = Mock()
        view.kwargs = {'pk': str(task.id)}

        permission = TaskCommentPermission()

        # act
        result = permission.has_permission(request, view)

        # assert
        assert result is True

    def test_has_permission__workflow_owner__ok(self):
        # arrange
        account = create_test_account()
        template_owner = create_test_user(account=account)
        template = create_test_template(user=template_owner)
        workflow = create_test_workflow(template=template, user=template_owner)
        task = workflow.tasks.get(number=1)

        workflow_owner = create_test_user(
            account=account,
            email='wf_owner@test.com',
            is_account_owner=False,
            is_admin=False,
        )
        workflow.owners.add(workflow_owner)

        request = Mock()
        request.user = workflow_owner

        view = Mock()
        view.kwargs = {'pk': str(task.id)}

        permission = TaskCommentPermission()

        # act
        result = permission.has_permission(request, view)

        # assert
        assert result is True

    def test_has_permission__task_performer__ok(self):
        # arrange
        account = create_test_account()
        template_owner = create_test_user(account=account)
        template = create_test_template(user=template_owner)
        workflow = create_test_workflow(template=template, user=template_owner)
        task = workflow.tasks.get(number=1)

        performer_user = create_test_user(
            account=account,
            email='performer@test.com',
            is_account_owner=False,
            is_admin=False,
        )
        TaskPerformer.objects.create(
            task_id=task.id,
            user_id=performer_user.id,
        )

        request = Mock()
        request.user = performer_user

        view = Mock()
        view.kwargs = {'pk': str(task.id)}

        permission = TaskCommentPermission()

        # act
        result = permission.has_permission(request, view)

        # assert
        assert result is True

    def test_has_permission__template_owner_user__ok(self):
        # arrange
        account = create_test_account()
        template_owner = create_test_user(account=account)
        template = create_test_template(user=template_owner)
        workflow = create_test_workflow(template=template, user=template_owner)
        task = workflow.tasks.get(number=1)

        owner_user = create_test_user(
            account=account,
            email='owner@test.com',
            is_account_owner=False,
            is_admin=False,
        )

        # Create template owner
        TemplateOwner.objects.create(
            template=template,
            type=OwnerType.USER,
            user=owner_user,
            account=account,
        )

        request = Mock()
        request.user = owner_user

        view = Mock()
        view.kwargs = {'pk': str(task.id)}

        permission = TaskCommentPermission()

        # act
        result = permission.has_permission(request, view)

        # assert
        assert result is True

    def test_has_permission__template_owner_group__ok(self):
        # arrange
        account = create_test_account()
        template_owner = create_test_user(account=account)
        template = create_test_template(user=template_owner)
        workflow = create_test_workflow(template=template, user=template_owner)
        task = workflow.tasks.get(number=1)

        owner_user = create_test_user(
            account=account,
            email='owner@test.com',
            is_account_owner=False,
            is_admin=False,
        )
        group = create_test_group(account=account, name='Owners Group')
        group.users.add(owner_user)

        # Create template owner for group
        TemplateOwner.objects.create(
            template=template,
            type=OwnerType.GROUP,
            group=group,
            account=account,
        )

        request = Mock()
        request.user = owner_user

        view = Mock()
        view.kwargs = {'pk': str(task.id)}

        permission = TaskCommentPermission()

        # act
        result = permission.has_permission(request, view)

        # assert
        assert result is True

    def test_has_permission__template_viewer_not_performer__denied(self):
        # arrange
        account = create_test_account()
        template_owner = create_test_user(
            account=account, email='owner@test.com',
        )
        template = create_test_template(user=template_owner)
        workflow = create_test_workflow(template=template, user=template_owner)
        task = workflow.tasks.get(number=1)

        # Create a separate user who is only template viewer
        viewer_user = create_test_user(
            account=account,
            email='viewer@test.com',
            is_account_owner=False,
            is_admin=False,
        )

        # Create template viewer
        TemplateViewer.objects.create(
            template=template,
            type=ViewerType.USER,
            user=viewer_user,
            account=account,
        )

        # Remove template_owner as task performer to test pure template viewer
        TaskPerformer.objects.filter(task_id=task.id).delete()

        request = Mock()
        request.user = viewer_user

        view = Mock()
        view.kwargs = {'pk': str(task.id)}

        permission = TaskCommentPermission()

        # act
        result = permission.has_permission(request, view)

        # assert
        assert result is False

    def test_has_permission__template_viewer_and_performer__ok(self):
        # arrange
        account = create_test_account()
        template_owner = create_test_user(
            account=account, email='owner@test.com',
        )
        template = create_test_template(user=template_owner)
        workflow = create_test_workflow(template=template, user=template_owner)
        task = workflow.tasks.get(number=1)

        # Create a separate user who is template viewer
        viewer_user = create_test_user(
            account=account,
            email='viewer@test.com',
            is_account_owner=False,
            is_admin=False,
        )

        # Create template viewer
        TemplateViewer.objects.create(
            template=template,
            type=ViewerType.USER,
            user=viewer_user,
            account=account,
        )

        # Make user a task performer
        TaskPerformer.objects.create(
            task_id=task.id,
            user_id=viewer_user.id,
        )

        request = Mock()
        request.user = viewer_user

        view = Mock()
        view.kwargs = {'pk': str(task.id)}

        permission = TaskCommentPermission()

        # act
        result = permission.has_permission(request, view)

        # assert
        assert result is True

    def test_has_permission__random_user__denied(self):
        # arrange
        account = create_test_account()
        template_owner = create_test_user(account=account)
        template = create_test_template(user=template_owner)
        workflow = create_test_workflow(template=template, user=template_owner)
        task = workflow.tasks.get(number=1)

        # Create a different user who is NOT template owner
        random_user = create_test_user(
            account=account,
            email='random@test.com',
            is_account_owner=False,
            is_admin=False,
        )

        # Remove template_owner as task performer to test random user
        TaskPerformer.objects.filter(task_id=task.id).delete()

        request = Mock()
        request.user = random_user

        view = Mock()
        view.kwargs = {'pk': str(task.id)}

        permission = TaskCommentPermission()

        # act
        result = permission.has_permission(request, view)

        # assert
        assert result is False

    def test_has_permission__invalid_task_id__denied(self):
        # arrange
        account = create_test_account()
        user = create_test_user(account=account)

        request = Mock()
        request.user = user

        view = Mock()
        view.kwargs = {'pk': 'invalid'}

        permission = TaskCommentPermission()

        # act
        result = permission.has_permission(request, view)

        # assert
        assert result is False

    def test_has_permission__missing_task_id__denied(self):
        # arrange
        account = create_test_account()
        user = create_test_user(account=account)

        request = Mock()
        request.user = user

        view = Mock()
        view.kwargs = {}

        permission = TaskCommentPermission()

        # act
        result = permission.has_permission(request, view)

        # assert
        assert result is False

    def test_has_permission__task_not_found__denied(self):
        # arrange
        account = create_test_account()
        user = create_test_user(
            account=account,
            is_account_owner=False,
            is_admin=False,
        )

        request = Mock()
        request.user = user

        view = Mock()
        view.kwargs = {'pk': '99999'}  # Non-existent task ID

        permission = TaskCommentPermission()

        # act
        result = permission.has_permission(request, view)

        # assert
        assert result is False
