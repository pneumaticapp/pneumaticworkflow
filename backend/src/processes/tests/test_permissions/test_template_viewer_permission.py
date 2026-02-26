import pytest
from django.contrib.auth import get_user_model
from unittest.mock import Mock

from src.processes.enums import ViewerType
from src.processes.models.templates.viewer import TemplateViewer
from src.processes.permissions import (
    TemplateViewerPermission,
    WorkflowMemberOrViewerPermission,
)
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_group,
    create_test_template,
    create_test_user,
    create_test_workflow,
)

UserModel = get_user_model()

pytestmark = pytest.mark.django_db


class TestTemplateViewerPermission:

    def test_has_permission__account_owner__ok(self):
        # arrange
        account = create_test_account()
        account_owner = create_test_user(
            account=account,
            is_account_owner=True,
        )
        template = create_test_template(user=account_owner, account=account)
        workflow = create_test_workflow(template=template, user=account_owner)

        request = Mock()
        request.user = account_owner

        view = Mock()
        view.kwargs = {'pk': str(workflow.id)}

        permission = TemplateViewerPermission()

        # act
        result = permission.has_permission(request, view)

        # assert
        assert result is True

    def test_has_permission__template_viewer_user__ok(self):
        # arrange
        account = create_test_account()
        template_owner = create_test_user(account=account)
        template = create_test_template(user=template_owner, account=account)
        workflow = create_test_workflow(template=template, user=template_owner)

        viewer_user = create_test_user(
            account=account,
            email='viewer@test.com',
        )

        # Create template viewer
        TemplateViewer.objects.create(
            template=template,
            type=ViewerType.USER,
            user=viewer_user,
            account=account,
        )

        request = Mock()
        request.user = viewer_user

        view = Mock()
        view.kwargs = {'pk': str(workflow.id)}

        permission = TemplateViewerPermission()

        # act
        result = permission.has_permission(request, view)

        # assert
        assert result is True

    def test_has_permission__template_viewer_group__ok(self):
        # arrange
        account = create_test_account()
        template_owner = create_test_user(account=account)
        template = create_test_template(user=template_owner, account=account)
        workflow = create_test_workflow(template=template, user=template_owner)

        viewer_user = create_test_user(
            account=account,
            email='viewer@test.com',
        )
        group = create_test_group(account=account, name='Viewers Group')
        group.users.add(viewer_user)

        # Create template viewer for group
        TemplateViewer.objects.create(
            template=template,
            type=ViewerType.GROUP,
            group=group,
            account=account,
        )

        request = Mock()
        request.user = viewer_user

        view = Mock()
        view.kwargs = {'pk': str(workflow.id)}

        permission = TemplateViewerPermission()

        # act
        result = permission.has_permission(request, view)

        # assert
        assert result is True

    def test_has_permission__not_viewer__denied(self):
        # arrange
        account = create_test_account()
        template_owner = create_test_user(account=account)
        template = create_test_template(user=template_owner, account=account)
        workflow = create_test_workflow(template=template, user=template_owner)

        random_user = create_test_user(
            account=account,
            email='random@test.com',
        )

        request = Mock()
        request.user = random_user

        view = Mock()
        view.kwargs = {'pk': str(workflow.id)}

        permission = TemplateViewerPermission()

        # act
        result = permission.has_permission(request, view)

        # assert
        assert result is False

    def test_has_permission__invalid_workflow_id__denied(self):
        # arrange
        account = create_test_account()
        user = create_test_user(account=account)

        request = Mock()
        request.user = user

        view = Mock()
        view.kwargs = {'pk': 'invalid'}

        permission = TemplateViewerPermission()

        # act
        result = permission.has_permission(request, view)

        # assert
        assert result is False

    def test_has_permission__missing_workflow_id__denied(self):
        # arrange
        account = create_test_account()
        user = create_test_user(account=account)

        request = Mock()
        request.user = user

        view = Mock()
        view.kwargs = {}

        permission = TemplateViewerPermission()

        # act
        result = permission.has_permission(request, view)

        # assert
        assert result is False


class TestWorkflowMemberOrViewerPermission:

    def test_has_permission__workflow_member__ok(self):
        # arrange
        account = create_test_account()
        template_owner = create_test_user(account=account)
        template = create_test_template(user=template_owner, account=account)
        workflow = create_test_workflow(template=template, user=template_owner)

        member_user = create_test_user(
            account=account,
            email='member@test.com',
        )
        workflow.members.add(member_user)

        request = Mock()
        request.user = member_user

        view = Mock()
        view.kwargs = {'pk': str(workflow.id)}

        permission = WorkflowMemberOrViewerPermission()

        # act
        result = permission.has_permission(request, view)

        # assert
        assert result is True

    def test_has_permission__template_viewer__ok(self):
        # arrange
        account = create_test_account()
        template_owner = create_test_user(account=account)
        template = create_test_template(user=template_owner, account=account)
        workflow = create_test_workflow(template=template, user=template_owner)

        viewer_user = create_test_user(
            account=account,
            email='viewer@test.com',
        )

        # Create template viewer
        TemplateViewer.objects.create(
            template=template,
            type=ViewerType.USER,
            user=viewer_user,
            account=account,
        )

        request = Mock()
        request.user = viewer_user

        view = Mock()
        view.kwargs = {'pk': str(workflow.id)}

        permission = WorkflowMemberOrViewerPermission()

        # act
        result = permission.has_permission(request, view)

        # assert
        assert result is True

    def test_has_permission__neither_member_nor_viewer__denied(self):
        # arrange
        account = create_test_account()
        template_owner = create_test_user(account=account)
        template = create_test_template(user=template_owner, account=account)
        workflow = create_test_workflow(template=template, user=template_owner)

        random_user = create_test_user(
            account=account,
            email='random@test.com',
        )

        request = Mock()
        request.user = random_user

        view = Mock()
        view.kwargs = {'pk': str(workflow.id)}

        permission = WorkflowMemberOrViewerPermission()

        # act
        result = permission.has_permission(request, view)

        # assert
        assert result is False
