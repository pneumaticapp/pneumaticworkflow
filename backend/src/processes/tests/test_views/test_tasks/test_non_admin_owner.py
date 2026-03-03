"""
Tests for non-admin workflow owners - task operations.

Non-admin users who are workflow owners should have viewer-level access:
- Can view tasks (read-only)
- Cannot manage task performers
- Cannot change due dates
"""
import pytest
from django.utils import timezone

from src.processes.enums import (
    OwnerType,
    PerformerType,
    StarterType,
    ViewerType,
)
from src.processes.models.templates.owner import TemplateOwner
from src.processes.models.templates.starter import TemplateStarter
from src.processes.models.templates.viewer import TemplateViewer
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_template,
    create_test_user,
    create_test_workflow,
)

pytestmark = pytest.mark.django_db


class TestNonAdminWorkflowOwnerTaskRetrieve:
    """Non-admin workflow owners can retrieve task (read-only)."""

    def test_retrieve__non_admin_workflow_owner__ok_read_only(
        self,
        api_client,
    ):
        # arrange
        account = create_test_account()
        admin_owner = create_test_user(
            email='admin@test.test',
            account=account,
            is_admin=True,
            is_account_owner=True,
        )
        non_admin_owner = create_test_user(
            email='nonadmin@test.test',
            account=account,
            is_admin=False,
            is_account_owner=False,
        )
        template = create_test_template(
            user=admin_owner,
            is_active=True,
            tasks_count=1,
        )
        TemplateOwner.objects.create(
            template=template,
            account=account,
            type=OwnerType.USER,
            user=non_admin_owner,
        )
        template.viewers.create(
            account=account,
            type=OwnerType.USER,
            user=non_admin_owner,
        )
        workflow = create_test_workflow(
            user=admin_owner,
            template=template,
        )
        workflow.owners.add(non_admin_owner)
        task = workflow.tasks.get(number=1)
        api_client.token_authenticate(non_admin_owner)

        # act
        response = api_client.get(f'/v2/tasks/{task.id}')

        # assert
        assert response.status_code == 200
        assert response.data['id'] == task.id
        assert response.data['is_read_only_viewer'] is True

    def test_retrieve__admin_workflow_owner__ok_not_read_only(
        self,
        api_client,
    ):
        # arrange
        account = create_test_account()
        admin_owner = create_test_user(
            email='admin@test.test',
            account=account,
            is_admin=True,
            is_account_owner=False,
        )
        template = create_test_template(
            user=admin_owner,
            is_active=True,
            tasks_count=1,
        )
        template.viewers.create(
            account=account,
            type=OwnerType.USER,
            user=admin_owner,
        )
        workflow = create_test_workflow(
            user=admin_owner,
            template=template,
        )
        task = workflow.tasks.get(number=1)
        api_client.token_authenticate(admin_owner)

        # act
        response = api_client.get(f'/v2/tasks/{task.id}')

        # assert
        assert response.status_code == 200
        assert response.data['id'] == task.id
        assert response.data['is_read_only_viewer'] is False


class TestNonAdminWorkflowOwnerTaskPerformer:
    """Non-admin workflow owners cannot manage task performers."""

    def test_create_performer__non_admin_workflow_owner__permission_denied(
        self,
        api_client,
    ):
        # arrange
        account = create_test_account()
        admin_owner = create_test_user(
            email='admin@test.test',
            account=account,
            is_admin=True,
            is_account_owner=True,
        )
        non_admin_owner = create_test_user(
            email='nonadmin@test.test',
            account=account,
            is_admin=False,
            is_account_owner=False,
        )
        another_user = create_test_user(
            email='another@test.test',
            account=account,
            is_admin=False,
            is_account_owner=False,
        )
        template = create_test_template(
            user=admin_owner,
            is_active=True,
            tasks_count=1,
        )
        workflow = create_test_workflow(
            user=admin_owner,
            template=template,
        )
        workflow.owners.add(non_admin_owner)
        task = workflow.tasks.get(number=1)
        api_client.token_authenticate(non_admin_owner)

        # act
        response = api_client.post(
            f'/v2/tasks/{task.id}/create-performer',
            data={
                'type': PerformerType.USER,
                'source_id': another_user.id,
            },
        )

        # assert
        assert response.status_code == 403

    def test_create_performer__admin_workflow_owner__ok(self, api_client):
        # arrange
        account = create_test_account()
        admin_owner = create_test_user(
            email='admin@test.test',
            account=account,
            is_admin=True,
            is_account_owner=False,
        )
        another_user = create_test_user(
            email='another@test.test',
            account=account,
            is_admin=False,
            is_account_owner=False,
        )
        template = create_test_template(
            user=admin_owner,
            is_active=True,
            tasks_count=1,
        )
        workflow = create_test_workflow(
            user=admin_owner,
            template=template,
        )
        task = workflow.tasks.get(number=1)
        api_client.token_authenticate(admin_owner)

        # act
        response = api_client.post(
            f'/v2/tasks/{task.id}/create-performer',
            data={'user_id': another_user.id},
        )

        # assert
        assert response.status_code == 204

    def test_delete_performer__non_admin_workflow_owner__permission_denied(
        self,
        api_client,
    ):
        # arrange
        account = create_test_account()
        admin_owner = create_test_user(
            email='admin@test.test',
            account=account,
            is_admin=True,
            is_account_owner=True,
        )
        non_admin_owner = create_test_user(
            email='nonadmin@test.test',
            account=account,
            is_admin=False,
            is_account_owner=False,
        )
        template = create_test_template(
            user=admin_owner,
            is_active=True,
            tasks_count=1,
        )
        workflow = create_test_workflow(
            user=admin_owner,
            template=template,
        )
        workflow.owners.add(non_admin_owner)
        task = workflow.tasks.get(number=1)
        performer = task.taskperformer_set.first()
        api_client.token_authenticate(non_admin_owner)

        # act
        response = api_client.post(
            f'/v2/tasks/{task.id}/delete-performer',
            data={
                'user_id': performer.user_id,
            },
        )

        # assert
        assert response.status_code == 403


class TestNonAdminWorkflowOwnerTaskDueDate:
    """Non-admin workflow owners cannot change task due dates."""

    def test_due_date__non_admin_workflow_owner__permission_denied(
        self,
        api_client,
    ):
        # arrange
        account = create_test_account()
        admin_owner = create_test_user(
            email='admin@test.test',
            account=account,
            is_admin=True,
            is_account_owner=True,
        )
        non_admin_owner = create_test_user(
            email='nonadmin@test.test',
            account=account,
            is_admin=False,
            is_account_owner=False,
        )
        template = create_test_template(
            user=admin_owner,
            is_active=True,
            tasks_count=1,
        )
        workflow = create_test_workflow(
            user=admin_owner,
            template=template,
        )
        workflow.owners.add(non_admin_owner)
        task = workflow.tasks.get(number=1)
        api_client.token_authenticate(non_admin_owner)
        new_due_date = timezone.now() + timezone.timedelta(days=7)

        # act
        response = api_client.post(
            f'/v2/tasks/{task.id}/due-date',
            data={
                'due_date_tsp': new_due_date.timestamp(),
            },
        )

        # assert
        assert response.status_code == 403

    def test_due_date__admin_workflow_owner__ok(self, api_client):
        # arrange
        account = create_test_account()
        admin_owner = create_test_user(
            email='admin@test.test',
            account=account,
            is_admin=True,
            is_account_owner=False,
        )
        template = create_test_template(
            user=admin_owner,
            is_active=True,
            tasks_count=1,
        )
        workflow = create_test_workflow(
            user=admin_owner,
            template=template,
        )
        task = workflow.tasks.get(number=1)
        api_client.token_authenticate(admin_owner)
        new_due_date = timezone.now() + timezone.timedelta(days=7)

        # act
        response = api_client.post(
            f'/v2/tasks/{task.id}/due-date',
            data={
                'due_date_tsp': new_due_date.timestamp(),
            },
        )

        # assert
        assert response.status_code == 204


class TestNonAdminTemplateOwnerTaskReadOnly:
    """Non-admin template owners viewing task should have read-only access."""

    def test_retrieve__non_admin_template_owner__read_only(self, api_client):
        # arrange
        account = create_test_account()
        admin_owner = create_test_user(
            email='admin@test.test',
            account=account,
            is_admin=True,
            is_account_owner=True,
        )
        non_admin_owner = create_test_user(
            email='nonadmin@test.test',
            account=account,
            is_admin=False,
            is_account_owner=False,
        )
        template = create_test_template(
            user=admin_owner,
            is_active=True,
            tasks_count=1,
        )
        TemplateOwner.objects.create(
            template=template,
            account=account,
            type=OwnerType.USER,
            user=non_admin_owner,
        )
        template.viewers.create(
            account=account,
            type=OwnerType.USER,
            user=non_admin_owner,
        )
        workflow = create_test_workflow(
            user=admin_owner,
            template=template,
        )
        task = workflow.tasks.get(number=1)
        api_client.token_authenticate(non_admin_owner)

        # act
        response = api_client.get(f'/v2/tasks/{task.id}')

        # assert
        assert response.status_code == 200
        assert response.data['is_read_only_viewer'] is True

    def test_retrieve__admin_template_owner__not_read_only(self, api_client):
        # arrange
        account = create_test_account()
        admin_owner = create_test_user(
            email='admin@test.test',
            account=account,
            is_admin=True,
            is_account_owner=False,
        )
        template = create_test_template(
            user=admin_owner,
            is_active=True,
            tasks_count=1,
        )
        template.viewers.create(
            account=account,
            type=OwnerType.USER,
            user=admin_owner,
        )
        workflow = create_test_workflow(
            user=admin_owner,
            template=template,
        )
        task = workflow.tasks.get(number=1)
        api_client.token_authenticate(admin_owner)

        # act
        response = api_client.get(f'/v2/tasks/{task.id}')

        # assert
        assert response.status_code == 200
        assert response.data['is_read_only_viewer'] is False


class TestAdminOnlyTemplateViewerTaskReadOnly:
    """
    Bug 1: Admin who is ONLY Template Viewer should have read-only task access.
    """

    def test_retrieve__admin_only_viewer__read_only(self, api_client):
        # arrange
        account = create_test_account()
        account_owner = create_test_user(
            email='owner@test.test',
            account=account,
            is_admin=True,
            is_account_owner=True,
        )
        admin_viewer = create_test_user(
            email='admin_viewer@test.test',
            account=account,
            is_admin=True,
            is_account_owner=False,
        )
        template = create_test_template(
            user=account_owner,
            is_active=True,
            tasks_count=1,
        )
        TemplateViewer.objects.create(
            template=template,
            account=account,
            type=ViewerType.USER,
            user=admin_viewer,
        )
        workflow = create_test_workflow(
            user=account_owner,
            template=template,
        )
        task = workflow.tasks.get(number=1)
        api_client.token_authenticate(admin_viewer)

        # act
        response = api_client.get(f'/v2/tasks/{task.id}')

        # assert
        assert response.status_code == 200
        assert response.data['is_read_only_viewer'] is True


class TestRoleChangeFromOwnerToViewerTask:
    """
    Bug 2: Admin removed from Template Owners and added to Template Viewers
    should have read-only access to existing tasks.
    """

    def test_retrieve__admin_removed_from_owners_to_viewers__read_only(
        self,
        api_client,
    ):
        # arrange
        account = create_test_account()
        account_owner = create_test_user(
            email='owner@test.test',
            account=account,
            is_admin=True,
            is_account_owner=True,
        )
        admin_user = create_test_user(
            email='admin@test.test',
            account=account,
            is_admin=True,
            is_account_owner=False,
        )
        template = create_test_template(
            user=account_owner,
            is_active=True,
            tasks_count=1,
        )
        template_owner = TemplateOwner.objects.create(
            template=template,
            account=account,
            type=OwnerType.USER,
            user=admin_user,
        )
        workflow = create_test_workflow(
            user=account_owner,
            template=template,
        )
        workflow.owners.add(admin_user)
        task = workflow.tasks.get(number=1)

        template_owner.is_deleted = True
        template_owner.save()
        TemplateViewer.objects.create(
            template=template,
            account=account,
            type=ViewerType.USER,
            user=admin_user,
        )
        api_client.token_authenticate(admin_user)

        # act
        response = api_client.get(f'/v2/tasks/{task.id}')

        # assert
        assert response.status_code == 200
        assert response.data['is_read_only_viewer'] is True

    def test_retrieve__admin_removed_from_owners_to_starters__read_only(
        self,
        api_client,
    ):
        # arrange
        account = create_test_account()
        account_owner = create_test_user(
            email='owner@test.test',
            account=account,
            is_admin=True,
            is_account_owner=True,
        )
        admin_user = create_test_user(
            email='admin@test.test',
            account=account,
            is_admin=True,
            is_account_owner=False,
        )
        template = create_test_template(
            user=account_owner,
            is_active=True,
            tasks_count=1,
        )
        template_owner = TemplateOwner.objects.create(
            template=template,
            account=account,
            type=OwnerType.USER,
            user=admin_user,
        )
        workflow = create_test_workflow(
            user=account_owner,
            template=template,
        )
        workflow.owners.add(admin_user)
        task = workflow.tasks.get(number=1)

        template_owner.is_deleted = True
        template_owner.save()
        workflow.owners.remove(admin_user)
        workflow.members.remove(admin_user)
        TemplateStarter.objects.create(
            template=template,
            account=account,
            type=StarterType.USER,
            user=admin_user,
        )
        api_client.token_authenticate(admin_user)

        # act
        response = api_client.get(f'/v2/tasks/{task.id}')

        # assert
        # Template Starters should NOT have access to tasks they didn't start
        assert response.status_code == 403


class TestNonAdminRoleChangeTaskReadOnly:
    """
    Bug 3: Non-admin who was Template Owner and then moved to
    Template Viewers/Starters should have read-only or no access.
    """

    def test_retrieve__non_admin_moved_from_owner_to_viewer__read_only(
        self,
        api_client,
    ):
        # arrange
        account = create_test_account()
        account_owner = create_test_user(
            email='owner@test.test',
            account=account,
            is_admin=True,
            is_account_owner=True,
        )
        non_admin_user = create_test_user(
            email='nonadmin@test.test',
            account=account,
            is_admin=False,
            is_account_owner=False,
        )
        template = create_test_template(
            user=account_owner,
            is_active=True,
            tasks_count=1,
        )
        template_owner = TemplateOwner.objects.create(
            template=template,
            account=account,
            type=OwnerType.USER,
            user=non_admin_user,
        )
        workflow = create_test_workflow(
            user=account_owner,
            template=template,
        )
        workflow.owners.add(non_admin_user)
        task = workflow.tasks.get(number=1)

        template_owner.is_deleted = True
        template_owner.save()
        TemplateViewer.objects.create(
            template=template,
            account=account,
            type=ViewerType.USER,
            user=non_admin_user,
        )
        api_client.token_authenticate(non_admin_user)

        # act
        response = api_client.get(f'/v2/tasks/{task.id}')

        # assert
        assert response.status_code == 200
        assert response.data['is_read_only_viewer'] is True

    def test_retrieve__non_admin_moved_from_owner_to_starter__read_only(
        self,
        api_client,
    ):
        # arrange
        account = create_test_account()
        account_owner = create_test_user(
            email='owner@test.test',
            account=account,
            is_admin=True,
            is_account_owner=True,
        )
        non_admin_user = create_test_user(
            email='nonadmin@test.test',
            account=account,
            is_admin=False,
            is_account_owner=False,
        )
        template = create_test_template(
            user=account_owner,
            is_active=True,
            tasks_count=1,
        )
        template_owner = TemplateOwner.objects.create(
            template=template,
            account=account,
            type=OwnerType.USER,
            user=non_admin_user,
        )
        workflow = create_test_workflow(
            user=account_owner,
            template=template,
        )
        workflow.owners.add(non_admin_user)
        task = workflow.tasks.get(number=1)

        template_owner.is_deleted = True
        template_owner.save()
        workflow.owners.remove(non_admin_user)
        workflow.members.remove(non_admin_user)
        TemplateStarter.objects.create(
            template=template,
            account=account,
            type=StarterType.USER,
            user=non_admin_user,
        )
        api_client.token_authenticate(non_admin_user)

        # act
        response = api_client.get(f'/v2/tasks/{task.id}')

        # assert
        # Template Starters should NOT have access to tasks they didn't start
        assert response.status_code == 403
