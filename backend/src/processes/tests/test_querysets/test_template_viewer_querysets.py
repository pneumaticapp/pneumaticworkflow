import pytest
from django.contrib.auth import get_user_model

from src.processes.enums import ViewerType
from src.processes.models.templates.template import Template
from src.processes.models.templates.viewer import TemplateViewer
from src.processes.models.workflows.workflow import Workflow
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_group,
    create_test_template,
    create_test_user,
    create_test_workflow,
)

UserModel = get_user_model()

pytestmark = pytest.mark.django_db


class TestTemplateQuerySetWithViewer:

    def test_with_template_viewer__user_viewer__ok(self):
        # arrange
        account = create_test_account()
        template_owner = create_test_user(account=account)
        template1 = create_test_template(
            user=template_owner,
            name='Template 1',
        )
        template2 = create_test_template(
            user=template_owner,
            name='Template 2',
        )

        viewer_user = create_test_user(
            account=account,
            email='viewer@test.com',
        )

        # Create viewer for template1 only
        TemplateViewer.objects.create(
            template=template1,
            type=ViewerType.USER,
            user=viewer_user,
            account=account,
        )

        # act
        templates = Template.objects.with_template_viewer(viewer_user.id)

        # assert
        assert template1 in templates
        assert template2 not in templates

    def test_with_template_viewer__group_viewer__ok(self):
        # arrange
        account = create_test_account()
        template_owner = create_test_user(account=account)
        template1 = create_test_template(
            user=template_owner,
            name='Template 1',
        )
        template2 = create_test_template(
            user=template_owner,
            name='Template 2',
        )

        viewer_user = create_test_user(
            account=account,
            email='viewer@test.com',
        )
        group = create_test_group(account=account, name='Viewers Group')
        group.users.add(viewer_user)

        # Create viewer for template1 only
        TemplateViewer.objects.create(
            template=template1,
            type=ViewerType.GROUP,
            group=group,
            account=account,
        )

        # act
        templates = Template.objects.with_template_viewer(viewer_user.id)

        # assert
        assert template1 in templates
        assert template2 not in templates

    def test_with_template_viewer__no_viewers__empty(self):
        # arrange
        account = create_test_account()
        template_owner = create_test_user(account=account)
        template = create_test_template(
            user=template_owner,
        )

        random_user = create_test_user(
            account=account,
            email='random@test.com',
        )

        # act
        templates = Template.objects.with_template_viewer(random_user.id)

        # assert
        assert template not in templates
        assert not templates.exists()

    def test_with_template_viewer__multiple_viewers__ok(self):
        # arrange
        account = create_test_account()
        template_owner = create_test_user(account=account)
        template = create_test_template(
            user=template_owner,
        )

        viewer_user1 = create_test_user(
            account=account,
            email='viewer1@test.com',
        )
        viewer_user2 = create_test_user(
            account=account,
            email='viewer2@test.com',
        )
        group = create_test_group(account=account, name='Viewers Group')
        group.users.add(viewer_user2)

        # Create multiple viewers for same template
        TemplateViewer.objects.create(
            template=template,
            type=ViewerType.USER,
            user=viewer_user1,
            account=account,
        )
        TemplateViewer.objects.create(
            template=template,
            type=ViewerType.GROUP,
            group=group,
            account=account,
        )

        # act
        templates1 = Template.objects.with_template_viewer(viewer_user1.id)
        templates2 = Template.objects.with_template_viewer(viewer_user2.id)

        # assert
        assert template in templates1
        assert template in templates2


class TestWorkflowQuerySetWithViewer:

    def test_with_template_viewer__user_viewer__ok(self):
        # arrange
        account = create_test_account()
        template_owner = create_test_user(account=account)
        template1 = create_test_template(
            user=template_owner,
            name='Template 1',
        )
        template2 = create_test_template(
            user=template_owner,
            name='Template 2',
        )
        workflow1 = create_test_workflow(
            template=template1, user=template_owner,
        )
        workflow2 = create_test_workflow(
            template=template2, user=template_owner,
        )

        viewer_user = create_test_user(
            account=account,
            email='viewer@test.com',
        )

        # Create viewer for template1 only
        TemplateViewer.objects.create(
            template=template1,
            type=ViewerType.USER,
            user=viewer_user,
            account=account,
        )

        # act
        workflows = Workflow.objects.with_template_viewer(viewer_user.id)

        # assert
        assert workflow1 in workflows
        assert workflow2 not in workflows

    def test_with_template_viewer__group_viewer__ok(self):
        # arrange
        account = create_test_account()
        template_owner = create_test_user(account=account)
        template1 = create_test_template(
            user=template_owner,
            name='Template 1',
        )
        template2 = create_test_template(
            user=template_owner,
            name='Template 2',
        )
        workflow1 = create_test_workflow(
            template=template1, user=template_owner,
        )
        workflow2 = create_test_workflow(
            template=template2, user=template_owner,
        )

        viewer_user = create_test_user(
            account=account,
            email='viewer@test.com',
        )
        group = create_test_group(account=account, name='Viewers Group')
        group.users.add(viewer_user)

        # Create viewer for template1 only
        TemplateViewer.objects.create(
            template=template1,
            type=ViewerType.GROUP,
            group=group,
            account=account,
        )

        # act
        workflows = Workflow.objects.with_template_viewer(viewer_user.id)

        # assert
        assert workflow1 in workflows
        assert workflow2 not in workflows

    def test_with_template_viewer__legacy_workflow__excluded(self):
        # arrange
        account = create_test_account()
        template_owner = create_test_user(account=account)
        template = create_test_template(
            user=template_owner,
        )
        workflow = create_test_workflow(template=template, user=template_owner)

        # Make workflow legacy (no template)
        workflow.template = None
        workflow.is_legacy_template = True
        workflow.save()

        viewer_user = create_test_user(
            account=account,
            email='viewer@test.com',
        )

        # Create viewer for template
        TemplateViewer.objects.create(
            template=template,
            type=ViewerType.USER,
            user=viewer_user,
            account=account,
        )

        # act
        workflows = Workflow.objects.with_template_viewer(viewer_user.id)

        # assert
        assert workflow not in workflows
        assert not workflows.exists()

    def test_with_template_viewer__no_viewers__empty(self):
        # arrange
        account = create_test_account()
        template_owner = create_test_user(account=account)
        template = create_test_template(
            user=template_owner,
        )
        workflow = create_test_workflow(template=template, user=template_owner)

        random_user = create_test_user(
            account=account,
            email='random@test.com',
        )

        # act
        workflows = Workflow.objects.with_template_viewer(random_user.id)

        # assert
        assert workflow not in workflows
        assert not workflows.exists()
