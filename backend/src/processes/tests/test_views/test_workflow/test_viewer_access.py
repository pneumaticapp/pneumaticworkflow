import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status

from src.processes.enums import ViewerType
from src.processes.models.templates.viewer import TemplateViewer
from src.processes.models.workflows.task import TaskPerformer
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_group,
    create_test_template,
    create_test_user,
    create_test_workflow,
)

UserModel = get_user_model()

pytestmark = pytest.mark.django_db


class TestWorkflowViewerAccess:

    def test_workflow_retrieve__template_viewer__ok(self, api_client):
        # arrange
        account = create_test_account()
        template_owner = create_test_user(account=account)
        template = create_test_template(template_owner)
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

        api_client.token_authenticate(viewer_user)
        url = reverse('workflows-detail', args=[workflow.id])

        # act
        response = api_client.get(url)

        # assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['id'] == workflow.id

    def test_workflow_retrieve__group_template_viewer__ok(self, api_client):
        # arrange
        account = create_test_account()
        template_owner = create_test_user(account=account)
        template = create_test_template(template_owner)
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

        api_client.token_authenticate(viewer_user)
        url = reverse('workflows-detail', args=[workflow.id])

        # act
        response = api_client.get(url)

        # assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['id'] == workflow.id

    def test_workflow_retrieve__not_viewer__forbidden(self, api_client):
        # arrange
        account = create_test_account()
        template_owner = create_test_user(account=account)
        template = create_test_template(template_owner)
        workflow = create_test_workflow(template=template, user=template_owner)

        random_user = create_test_user(
            account=account,
            email='random@test.com',
            is_admin=False,
            is_account_owner=False,
        )

        api_client.token_authenticate(random_user)
        url = reverse('workflows-detail', args=[workflow.id])

        # act
        response = api_client.get(url)

        # assert
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_workflow_events__template_viewer__ok(self, api_client):
        # arrange
        account = create_test_account()
        template_owner = create_test_user(account=account)
        template = create_test_template(template_owner)
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

        api_client.token_authenticate(viewer_user)
        url = reverse('workflows-events', args=[workflow.id])

        # act
        response = api_client.get(url)

        # assert
        assert response.status_code == status.HTTP_200_OK

    def test_workflow_events__not_viewer__forbidden(self, api_client):
        # arrange
        account = create_test_account()
        template_owner = create_test_user(account=account)
        template = create_test_template(template_owner)
        workflow = create_test_workflow(template=template, user=template_owner)

        random_user = create_test_user(
            account=account,
            email='random@test.com',
            is_admin=False,
            is_account_owner=False,
        )

        api_client.token_authenticate(random_user)
        url = reverse('workflows-events', args=[workflow.id])

        # act
        response = api_client.get(url)

        # assert
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_workflow_update__template_viewer__forbidden(self, api_client):
        # arrange
        account = create_test_account()
        template_owner = create_test_user(account=account)
        template = create_test_template(template_owner)
        workflow = create_test_workflow(template=template, user=template_owner)

        viewer_user = create_test_user(
            account=account,
            email='viewer@test.com',
            is_admin=False,
            is_account_owner=False,
        )

        # Create template viewer
        TemplateViewer.objects.create(
            template=template,
            type=ViewerType.USER,
            user=viewer_user,
            account=account,
        )

        api_client.token_authenticate(viewer_user)
        url = reverse('workflows-detail', args=[workflow.id])
        data = {'name': 'Updated Name'}

        # act
        response = api_client.patch(url, data)

        # assert
        # Template viewers should NOT be able to update workflows
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_workflow_terminate__template_viewer__forbidden(self, api_client):
        # arrange
        account = create_test_account()
        template_owner = create_test_user(account=account)
        template = create_test_template(template_owner)
        workflow = create_test_workflow(template=template, user=template_owner)

        viewer_user = create_test_user(
            account=account,
            email='viewer@test.com',
            is_admin=False,
            is_account_owner=False,
        )

        # Create template viewer
        TemplateViewer.objects.create(
            template=template,
            type=ViewerType.USER,
            user=viewer_user,
            account=account,
        )

        api_client.token_authenticate(viewer_user)
        url = reverse('workflows-detail', args=[workflow.id])

        # act
        response = api_client.delete(url)

        # assert
        # Template viewers should NOT be able to terminate workflows
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_workflow_return_to__template_viewer__forbidden(self, api_client):
        # arrange
        account = create_test_account()
        template_owner = create_test_user(account=account)
        template = create_test_template(template_owner)
        workflow = create_test_workflow(template=template, user=template_owner)

        viewer_user = create_test_user(
            account=account,
            email='viewer@test.com',
            is_admin=False,
            is_account_owner=False,
        )

        # Create template viewer
        TemplateViewer.objects.create(
            template=template,
            type=ViewerType.USER,
            user=viewer_user,
            account=account,
        )

        task = workflow.tasks.order_by('number').first()
        api_client.token_authenticate(viewer_user)
        url = reverse('workflows-return-to', args=[workflow.id])
        data = {'task_api_name': task.api_name}

        # act
        response = api_client.post(url, data)

        # assert
        # Template viewers cannot return workflows to previous steps
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_workflow_list__template_viewer__includes_viewer_workflows(
            self, api_client,
    ):
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

        # Create template viewer for template1 only
        TemplateViewer.objects.create(
            template=template1,
            type=ViewerType.USER,
            user=viewer_user,
            account=account,
        )

        api_client.token_authenticate(viewer_user)
        url = reverse('workflows-list')

        # act
        response = api_client.get(url)

        # assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Should include workflow1 (from template where user is viewer)
        # Should NOT include workflow2 (from template where user is not viewer)
        workflow_ids = [item['id'] for item in data['results']]
        assert workflow1.id in workflow_ids
        assert workflow2.id not in workflow_ids

    def test_workflow_list__account_owner__sees_all_workflows(
            self, api_client,
    ):
        # arrange
        account = create_test_account()
        account_owner = create_test_user(
            account=account,
            is_account_owner=True,
        )
        template = create_test_template(account_owner)
        workflow = create_test_workflow(template=template, user=account_owner)

        api_client.token_authenticate(account_owner)
        url = reverse('workflows-list')

        # act
        response = api_client.get(url)

        # assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        workflow_ids = [item['id'] for item in data['results']]
        assert workflow.id in workflow_ids

    def test_workflow_partial_update__owner_and_viewer__treated_as_owner(
            self, api_client,
    ):
        # arrange: user is both template owner and template viewer
        account = create_test_account()
        user = create_test_user(
            account=account,
            is_admin=True,
            is_account_owner=False,
        )
        template = create_test_template(user)
        workflow = create_test_workflow(template=template, user=user)
        TemplateViewer.objects.create(
            template=template,
            type=ViewerType.USER,
            user=user,
            account=account,
        )
        api_client.token_authenticate(user)
        url = reverse('workflows-detail', args=[workflow.id])
        data = {'name': 'Updated by owner'}

        # act
        response = api_client.patch(url, data)

        # assert: owner has priority, so write is allowed
        assert response.status_code == status.HTTP_200_OK
        workflow.refresh_from_db()
        assert workflow.name == 'Updated by owner'

    def test_workflow_retrieve__template_viewer__is_read_only_viewer_true(
        self, api_client,
    ):
        # arrange
        account = create_test_account()
        template_owner = create_test_user(account=account)
        template = create_test_template(template_owner)
        workflow = create_test_workflow(template=template, user=template_owner)

        viewer_user = create_test_user(
            account=account,
            email='viewer@test.com',
            is_admin=False,
            is_account_owner=False,
        )

        # Create template viewer
        TemplateViewer.objects.create(
            template=template,
            type=ViewerType.USER,
            user=viewer_user,
            account=account,
        )

        api_client.token_authenticate(viewer_user)
        url = reverse('workflows-detail', args=[workflow.id])

        # act
        response = api_client.get(url)

        # assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['is_read_only_viewer'] is True

    def test_workflow_retrieve__admin_template_viewer__is_read_only_viewer_ok(
        self, api_client,
    ):
        """Admin who is ONLY template viewer should have read-only access."""
        # arrange
        account = create_test_account()
        template_owner = create_test_user(account=account)
        template = create_test_template(template_owner)
        workflow = create_test_workflow(template=template, user=template_owner)

        admin_viewer = create_test_user(
            account=account,
            email='admin_viewer@test.com',
            is_admin=True,
            is_account_owner=False,
        )

        # Create template viewer for admin
        TemplateViewer.objects.create(
            template=template,
            type=ViewerType.USER,
            user=admin_viewer,
            account=account,
        )

        api_client.token_authenticate(admin_viewer)
        url = reverse('workflows-detail', args=[workflow.id])

        # act
        response = api_client.get(url)

        # assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['is_read_only_viewer'] is True

    def test_workflow_retrieve__template_owner__is_read_only_viewer_false(
        self, api_client,
    ):
        # arrange
        account = create_test_account()
        template_owner = create_test_user(account=account)
        template = create_test_template(template_owner)
        workflow = create_test_workflow(template=template, user=template_owner)

        api_client.token_authenticate(template_owner)
        url = reverse('workflows-detail', args=[workflow.id])

        # act
        response = api_client.get(url)

        # assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['is_read_only_viewer'] is False

    def test_workflow_retrieve__task_performer__is_read_only_viewer_false(
        self, api_client,
    ):
        """
        Task performers have full access (is_read_only_viewer=False).
        Being in workflow.members is not enough - must be performer on a task.
        """
        # arrange
        account = create_test_account()
        template_owner = create_test_user(account=account)
        template = create_test_template(template_owner, tasks_count=1)
        workflow = create_test_workflow(template=template, user=template_owner)

        performer_user = create_test_user(
            account=account,
            email='performer@test.com',
            is_admin=False,
            is_account_owner=False,
        )
        task = workflow.tasks.first()
        TaskPerformer.objects.create(
            task=task,
            user=performer_user,
        )
        workflow.members.add(performer_user)

        api_client.token_authenticate(performer_user)
        url = reverse('workflows-detail', args=[workflow.id])

        # act
        response = api_client.get(url)

        # assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['is_read_only_viewer'] is False

    def test_workflow_retrieve__workflow_member__ok_read_only(
        self, api_client,
    ):
        """
        Users in workflow.members (e.g., mentioned in comments, performers)
        have read-only access to the workflow.
        """
        # arrange
        account = create_test_account()
        template_owner = create_test_user(account=account)
        template = create_test_template(template_owner)
        workflow = create_test_workflow(template=template, user=template_owner)

        member_user = create_test_user(
            account=account,
            email='member@test.com',
            is_admin=False,
            is_account_owner=False,
        )
        workflow.members.add(member_user)

        api_client.token_authenticate(member_user)
        url = reverse('workflows-detail', args=[workflow.id])

        # act
        response = api_client.get(url)

        # assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['is_read_only_viewer'] is True

    def test_workflow_retrieve__no_template__member_is_read_only_viewer_true(
        self, api_client,
    ):
        """
        When a workflow has no associated template, a non-owner/non-performer
        member must receive is_read_only_viewer=True (read-only), not False.

        Regression test for the bug where `if not template: return False`
        incorrectly granted full access.
        """
        # arrange
        account = create_test_account()
        template_owner = create_test_user(account=account)
        template = create_test_template(template_owner)
        workflow = create_test_workflow(template=template, user=template_owner)

        # Detach the template to simulate a legacy/templateless workflow
        workflow.template = None
        workflow.save(update_fields=['template'])

        member_user = create_test_user(
            account=account,
            email='member_no_template@test.com',
            is_admin=False,
            is_account_owner=False,
        )
        workflow.members.add(member_user)

        api_client.token_authenticate(member_user)
        url = reverse('workflows-detail', args=[workflow.id])

        # act
        response = api_client.get(url)

        # assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # Without a template, a plain member must be read-only, not full-access
        assert data['is_read_only_viewer'] is True
