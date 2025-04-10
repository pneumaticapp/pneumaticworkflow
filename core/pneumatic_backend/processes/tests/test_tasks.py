from datetime import timedelta
import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from pneumatic_backend.authentication.enums import AuthTokenType
from pneumatic_backend.processes.tasks.tasks import complete_tasks
from pneumatic_backend.processes.models import (
    Workflow,
    TaskPerformer,
    TemplateOwner
)
from pneumatic_backend.processes.services.versioning.schemas import (
    TemplateSchemaV1,
)
from pneumatic_backend.processes.services.versioning.versioning import (
    TemplateVersioningService,
)
from pneumatic_backend.processes.tasks.delay import (
    continue_delayed_workflows,
)
from pneumatic_backend.processes.tasks.update_workflow import (
    update_workflows,
)
from pneumatic_backend.processes.tests.fixtures import (
    create_test_user,
    create_test_account,
    create_test_group,
    create_test_template,
    create_test_workflow
)
from pneumatic_backend.processes.enums import (
    PerformerType,
    OwnerType,
    DirectlyStatus,
)
from pneumatic_backend.processes.utils.workflows import (
    resume_delayed_workflows
)
from pneumatic_backend.processes.services.workflow_action import (
    WorkflowActionService
)
from pneumatic_backend.processes.tasks.update_workflow import (
    update_workflow_owners,
)

UserModel = get_user_model()
pytestmark = pytest.mark.django_db


class TestContinueDelayedWorkflows:

    def test_continue_delayed_workflows__ok(self, mocker):

        # arrange
        periodic_lock_mock = mocker.patch(
            'pneumatic_backend.celery.periodic_lock'
        )
        periodic_lock_mock.__enter__.return_value = True
        resume_delayed_workflows_mock = mocker.patch(
            'pneumatic_backend.processes.tasks.delay.resume_delayed_workflows'
        )

        # act
        continue_delayed_workflows()

        # assert
        resume_delayed_workflows_mock.assert_called_once()

    def test_resume_delayed_workflows__delay_expired__resume(
        self,
        mocker,
        api_client
    ):

        # arrange
        mocker.patch(
            'pneumatic_backend.processes.tasks.webhooks.'
            'send_workflow_started_webhook.delay',
        )
        mocker.patch(
            'pneumatic_backend.processes.tasks.webhooks.'
            'send_task_completed_webhook.delay'
        )
        user = create_test_user()
        api_client.token_authenticate(user)

        # act
        response_create = api_client.post(
            path='/templates',
            data={
                'name': 'Template',
                'owners': [
                    {
                        'type': OwnerType.USER,
                        'source_id': user.id
                    },
                ],
                'kickoff': {},
                'is_active': True,
                'tasks': [
                    {
                        'number': 1,
                        'name': 'First step',
                        'raw_performers': [
                            {
                                'type': PerformerType.USER,
                                'source_id': user.id
                            }
                        ]
                    },
                    {
                        'number': 2,
                        'name': 'Second step',
                        'delay': '01:00:00',
                        'raw_performers': [
                            {
                                'type': PerformerType.USER,
                                'source_id': user.id
                            }
                        ]
                    }
                ]
            }
        )

        template_id = response_create.data['id']
        response_run = api_client.post(
            path=f'/templates/{template_id}/run',
            data={'name': 'Test template'}
        )
        workflow_id = response_run.data['id']
        workflow = Workflow.objects.get(id=workflow_id)

        response_complete = api_client.post(
            path=f'/workflows/{workflow_id}/task-complete',
            data={'task_id': workflow.current_task_instance.id}
        )
        workflow.refresh_from_db()
        current_task = workflow.tasks.get(number=2)
        delay = current_task.get_active_delay()
        delay.start_date = (timezone.now() - timedelta(days=2))
        delay.save()

        service_init_mock = mocker.patch.object(
            WorkflowActionService,
            attribute='__init__',
            return_value=None
        )
        resume_workflow_mock = mocker.patch(
            'pneumatic_backend.processes.services.'
            'workflow_action.WorkflowActionService.resume_workflow'
        )
        workflow.refresh_from_db()

        # act
        resume_delayed_workflows()

        # assert
        assert response_run.status_code == 200
        assert response_complete.status_code == 204
        workflow.refresh_from_db()
        service_init_mock.assert_called_once_with(
            workflow=workflow,
            user=user,
            is_superuser=False,
            auth_type=AuthTokenType.USER
        )
        resume_workflow_mock.assert_called_once_with()

    def test_resume_delayed_workflows__delay_not_expired__not_resume(
        self,
        mocker,
        api_client
    ):

        # arrange
        mocker.patch(
            'pneumatic_backend.processes.tasks.webhooks.'
            'send_workflow_started_webhook.delay',
        )
        mocker.patch(
            'pneumatic_backend.processes.tasks.webhooks.'
            'send_task_completed_webhook.delay'
        )
        user = create_test_user()
        api_client.token_authenticate(user)

        # act
        response_create = api_client.post(
            path='/templates',
            data={
                'name': 'Template',
                'owners': [
                    {
                        'type': OwnerType.USER,
                        'source_id': user.id
                    },
                ],
                'kickoff': {},
                'is_active': True,
                'tasks': [
                    {
                        'number': 1,
                        'name': 'First step',
                        'raw_performers': [
                            {
                                'type': PerformerType.USER,
                                'source_id': user.id
                            }
                        ]
                    },
                    {
                        'number': 2,
                        'name': 'Second step',
                        'delay': '01:00:00',
                        'raw_performers': [
                            {
                                'type': PerformerType.USER,
                                'source_id': user.id
                            }
                        ]
                    }
                ]
            }
        )

        template_id = response_create.data['id']
        response_run = api_client.post(
            path=f'/templates/{template_id}/run',
            data={'name': 'Test template'}
        )
        workflow_id = response_run.data['id']
        workflow = Workflow.objects.get(id=workflow_id)

        response_complete = api_client.post(
            path=f'/workflows/{workflow_id}/task-complete',
            data={'task_id': workflow.current_task_instance.id}
        )
        workflow.refresh_from_db()

        service_init_mock = mocker.patch.object(
            WorkflowActionService,
            attribute='__init__',
            return_value=None
        )
        resume_workflow_mock = mocker.patch(
            'pneumatic_backend.processes.services.'
            'workflow_action.WorkflowActionService.resume_workflow'
        )
        workflow.refresh_from_db()

        # act
        resume_delayed_workflows()

        # assert
        assert response_run.status_code == 200
        assert response_complete.status_code == 204
        workflow.refresh_from_db()
        service_init_mock.assert_not_called()
        resume_workflow_mock.assert_not_called()


class TestUpdateWorkflow:

    def test_update(self, api_client):

        user = create_test_user()
        template = create_test_template(
            user=user,
            is_active=True,
            tasks_count=1
        )
        api_client.token_authenticate(user)
        workflow_id = api_client.post(
            f'/templates/{template.id}/run',
            data={
                'name': 'Test workflow'
            }
        ).data['id']
        first_task = template.tasks.get(number=1)
        first_task.name = 'New task name'
        first_task.save()
        template.version += 1
        template.save()
        TemplateVersioningService(TemplateSchemaV1).save(template)

        update_workflows(
            template_id=template.id,
            version=template.version,
            updated_by=user.id,
            auth_type=AuthTokenType.USER,
            is_superuser=True
        )

        workflow = Workflow.objects.get(id=workflow_id)

        assert workflow.version == template.version
        assert workflow.current_task_instance.name == 'New task name'

    def test_update__add_group__ok(self):
        # arrange
        user = create_test_user()
        another_user = create_test_user(
            account=user.account,
            email='another@pneumatic.app'
        )
        group = create_test_group(user=user, users=[another_user, ])
        template = create_test_template(
            user=user,
            is_active=True,
            tasks_count=1
        )
        workflow = create_test_workflow(
            user=user,
            template=template
        )

        first_task = template.tasks.get(number=1)
        first_task.add_raw_performer(
            group=group,
            performer_type=PerformerType.GROUP
        )
        first_task.save()
        template.version += 1
        template.save()
        TemplateVersioningService(TemplateSchemaV1).save(template)

        # act
        update_workflows(
            template_id=template.id,
            version=template.version,
            updated_by=user.id,
            auth_type=AuthTokenType.USER,
            is_superuser=True
        )

        # assert
        workflow = Workflow.objects.get(id=workflow.id)
        task = workflow.tasks.get(number=1)
        performers = TaskPerformer.objects.filter(task=task)
        group_performer = performers.filter(
            type=PerformerType.GROUP,
            group_id=group.id
        ).first()
        assert workflow.version == template.version
        assert group_performer is not None
        assert group_performer.group_id == group.id

    def test_update__template_version_difference(self, api_client):
        user = create_test_user()
        template = create_test_template(
            user=user,
            is_active=True,
            tasks_count=1
        )
        api_client.token_authenticate(user)
        workflow_id = api_client.post(
            f'/templates/{template.id}/run',
            data={
                'name': 'Test workflow'
            }
        ).data['id']
        workflow = Workflow.objects.get(id=workflow_id)
        version = workflow.version
        task_name = workflow.current_task_instance.name

        first_task = template.tasks.get(number=1)
        first_task.name = 'New task name'
        first_task.save()
        template.version += 1
        template.save()
        TemplateVersioningService(TemplateSchemaV1).save(template)

        update_workflows(
            template_id=template.id,
            version=template.version-1,
            updated_by=user.id,
            auth_type=AuthTokenType.USER,
            is_superuser=True
        )
        workflow.refresh_from_db()

        assert workflow.version == version
        assert workflow.current_task_instance.name == task_name

    def test_update__process_version_difference(self, api_client):
        user = create_test_user()
        template = create_test_template(
            user=user,
            is_active=True,
            tasks_count=1
        )
        api_client.token_authenticate(user)
        workflow_id = api_client.post(
            f'/templates/{template.id}/run',
            data={
                'name': 'Test workflow'
            }
        ).data['id']
        workflow = Workflow.objects.get(id=workflow_id)
        workflow.version += 5
        workflow.save()
        version = workflow.version
        task_name = workflow.current_task_instance.name

        first_task = template.tasks.get(number=1)
        first_task.name = 'New task name'
        first_task.save()
        template.version += 1
        template.save()
        TemplateVersioningService(TemplateSchemaV1).save(template)

        update_workflows(
            template_id=template.id,
            version=template.version,
            updated_by=user.id,
            auth_type=AuthTokenType.USER,
            is_superuser=True
        )
        workflow.refresh_from_db()

        assert workflow.version == version
        assert workflow.current_task_instance.name == task_name


class TestCompleteTasks:

    def test_call(self, api_client):

        # arrange
        user = create_test_user()
        second_user = create_test_user(
            email='second_user@pneumatic.app',
            account=user.account,
        )
        workflow = create_test_workflow(
            user=user
        )
        second_workflow = create_test_workflow(
            user=user
        )
        second_workflow_first_task = second_workflow.current_task_instance
        second_workflow_first_task.performers.add(second_user)
        second_workflow_first_task.require_completion_by_all = True
        second_workflow_first_task.save()
        first_task = workflow.current_task_instance
        first_task.require_completion_by_all = True
        first_task.save()
        first_task.taskperformer_set.filter(user=user).update(
            is_completed=True,
        )
        second_workflow_first_task.taskperformer_set.filter(
            user=user
        ).update(is_completed=True)

        # act
        complete_tasks(
            is_superuser=False,
            auth_type=AuthTokenType.USER,
            user_id=user.id
        )

        # assert
        first_task.refresh_from_db()
        second_workflow_first_task.refresh_from_db()
        assert first_task.is_completed
        assert second_workflow_first_task.is_completed is False


class TestUpdateWorkflowOwners:

    def test__delete_group_owner_only__ok(self):
        """
        When deleting a group, an owner of the group type
        is deleted in template, and owner user is deleted in workflow.
        """

        # arrange
        account = create_test_account()
        user = create_test_user(account=account)
        template = create_test_template(
            user=user,
            is_active=True,
            tasks_count=1
        )
        TemplateOwner.objects.all().delete()
        group = create_test_group(user=user, users=[user])
        TemplateOwner.objects.create(
            template=template,
            account=account,
            type=OwnerType.GROUP,
            group_id=group.id,
        )
        workflow = create_test_workflow(
            user=user,
            template=template
        )
        group.delete()

        # act
        update_workflow_owners([template.id])

        # assert
        assert workflow.owners.all().count() == 0

    def test__add_template_owner_is_deleted__ok(self):
        """
        Verifies that soft-deleted template owners (is_deleted=True)
        are not propagated to workflow owners and members
        """
        # arrange
        account = create_test_account()
        user = create_test_user(account=account)
        template = create_test_template(
            user=user,
            is_active=True,
            tasks_count=1
        )
        TemplateOwner.objects.all().delete()
        group = create_test_group(user=user, users=[user])
        workflow = create_test_workflow(
            user=user,
            template=template
        )
        task = workflow.tasks.get(number=1)
        task.performers.all().delete()
        TemplateOwner.objects.create(
            template=template,
            account=account,
            type=OwnerType.GROUP,
            group_id=group.id,
            is_deleted=True
        )

        # act
        update_workflow_owners([template.id])

        # assert
        assert workflow.owners.all().count() == 0
        assert workflow.members.all().count() == 0

    def test__delete_group_owner_user_owner_persists_same_user__ok(self):
        """
        There are 2 owner types in the template. When deleting a group,
           the user owner (same user) persists in workflow.
        """

        # arrange
        account = create_test_account()
        user = create_test_user(account=account)
        template = create_test_template(
            user=user,
            is_active=True,
            tasks_count=1
        )
        group_to_delete = create_test_group(user=user, users=[user])
        TemplateOwner.objects.create(
            template=template,
            account=account,
            type=OwnerType.GROUP,
            group_id=group_to_delete.id,
        )
        workflow = create_test_workflow(
            user=user,
            template=template
        )
        group_to_delete.delete()

        # act
        update_workflow_owners([template.id])

        # assert
        assert workflow.owners.all().count() == 1
        assert workflow.owners.get(id=user.id)

    def test__delete_group_owner_user_owner_persists_different_user__ok(self):
        """
        There are 2 owner types in the template. When deleting a group,
        the user owner (different user) persists in workflow.
        """

        # arrange
        account = create_test_account()
        user = create_test_user(account=account)
        user_2 = create_test_user(account=account, email='test1@test.test')
        template = create_test_template(
            user_2,
            is_active=True,
            tasks_count=1
        )
        group_to_delete = create_test_group(user=user_2, users=[user])
        TemplateOwner.objects.create(
            template=template,
            account=account,
            type=OwnerType.GROUP,
            group_id=group_to_delete.id,
        )
        workflow = create_test_workflow(
            user=user_2,
            template=template
        )
        group_to_delete.delete()

        # act
        update_workflow_owners([template.id])

        # assert
        assert workflow.owners.all().count() == 1
        assert workflow.owners.get(id=user_2.id)

    def test__delete_group_owner_with_users_user_owner_persists__ok(self):
        """There are 2 owner types in the template. When deleting a group with
           users, the user owner persists in workflow."""

        # arrange
        account = create_test_account()
        user = create_test_user(account=account)
        user_2 = create_test_user(account=account, email='test1@test.test')
        user_3 = create_test_user(account=account, email='test2@test.test')
        template = create_test_template(
            user=user,
            is_active=True,
            tasks_count=1
        )
        group_to_delete = create_test_group(user=user, users=[user_2, user_3])
        TemplateOwner.objects.create(
            template=template,
            account=account,
            type=OwnerType.GROUP,
            group_id=group_to_delete.id,
        )
        workflow = create_test_workflow(
            user=user_2,
            template=template
        )
        group_to_delete.delete()

        # act
        update_workflow_owners([template.id])

        # assert
        assert workflow.owners.all().count() == 1
        assert workflow.owners.get(id=user.id)

    def test__delete_one_group_owner_user_owner_persists_empty_group__ok(self):
        """There are 2 group owners in the template. When deleting one group,
           the user owner persists, second group is empty."""

        # arrange
        account = create_test_account()
        user = create_test_user(account=account)
        user_2 = create_test_user(account=account, email='test1@test.test')
        user_3 = create_test_user(account=account, email='test2@test.test')
        template = create_test_template(
            user=user,
            is_active=True,
            tasks_count=1
        )
        group_to_delete = create_test_group(user=user, users=[user_2, user_3])
        group = create_test_group(user=user)
        TemplateOwner.objects.create(
            template=template,
            account=account,
            type=OwnerType.GROUP,
            group_id=group_to_delete.id,
        )
        TemplateOwner.objects.create(
            template=template,
            account=account,
            type=OwnerType.GROUP,
            group_id=group.id,
        )
        workflow = create_test_workflow(
            user=user_2,
            template=template
        )
        group_to_delete.delete()

        # act
        update_workflow_owners([template.id])

        # assert
        assert workflow.owners.all().count() == 1
        assert workflow.owners.get(id=user.id)

    def test__delete_one_group_owner_other_group_owner_persists__ok(self):
        """There are 2 group owners in the template. When deleting one group,
           the other group owner and its user persist in workflow."""

        # arrange
        account = create_test_account()
        user = create_test_user(account=account)
        user_2 = create_test_user(account=account, email='test1@test.test')
        template = create_test_template(
            user=user,
            is_active=True,
            tasks_count=1
        )
        TemplateOwner.objects.filter(user_id=user.id).delete()
        group = create_test_group(user=user, users=[user])
        group_to_delete = create_test_group(user=user, users=[user_2])
        TemplateOwner.objects.create(
            template=template,
            account=account,
            type=OwnerType.GROUP,
            group_id=group_to_delete.id,
        )
        TemplateOwner.objects.create(
            template=template,
            account=account,
            type=OwnerType.GROUP,
            group_id=group.id,
        )
        workflow = create_test_workflow(
            user=user,
            template=template
        )
        group_to_delete.delete()

        # act
        update_workflow_owners([template.id])

        # assert
        assert workflow.owners.all().count() == 1
        assert workflow.owners.get(id=user.id)

    def test__delete_group_owner_other_template_unchanged__ok(self):
        """When deleting a group owner in one template, the other template
           and its workflow remain unchanged."""

        # arrange
        account = create_test_account()
        user = create_test_user(account=account)
        template = create_test_template(
            user=user,
            is_active=True,
            tasks_count=1
        )
        template_2 = create_test_template(
            user=user,
            is_active=True,
            tasks_count=1
        )
        TemplateOwner.objects.filter(user_id=user.id).delete()
        group = create_test_group(user=user, users=[user])
        TemplateOwner.objects.create(
            template=template,
            account=account,
            type=OwnerType.GROUP,
            group_id=group.id,
        )
        group_to_delete = create_test_group(user=user, users=[user])
        TemplateOwner.objects.create(
            template=template_2,
            account=account,
            type=OwnerType.GROUP,
            group_id=group_to_delete.id,
        )
        workflow = create_test_workflow(
            user=user,
            template=template
        )
        workflow_2 = create_test_workflow(
            user=user,
            template=template_2
        )
        group_to_delete.delete()

        # act
        update_workflow_owners([template_2.id])

        # assert
        assert template.owners.all().count() == 1
        assert template.owners.get(group_id=group.id)
        assert workflow.owners.all().count() == 1
        assert workflow.owners.get(id=user.id)
        assert template_2.owners.all().count() == 0
        assert workflow_2.owners.all().count() == 0

    def test__delete_group_owner_different_account_unchanged__ok(self):
        """When deleting a group owner in one account, the template and
           workflow in another account remain unchanged."""

        # arrange
        account = create_test_account()
        user = create_test_user(account=account)
        template = create_test_template(
            user=user,
            is_active=True,
            tasks_count=1
        )
        TemplateOwner.objects.filter(user_id=user.id).delete()
        group = create_test_group(user=user, users=[user])
        TemplateOwner.objects.create(
            template=template,
            account=account,
            type=OwnerType.GROUP,
            group_id=group.id,
        )
        workflow = create_test_workflow(
            user=user,
            template=template
        )
        account_another = create_test_account()
        user_account_another = create_test_user(
            account=account_another,
            email='test1@test.test'
        )
        template_account_another = create_test_template(
            user_account_another,
            is_active=True,
            tasks_count=1
        )
        TemplateOwner.objects.filter(
            type=OwnerType.USER,
            user_id=user_account_another.id
        ).delete()
        group_to_delete = create_test_group(
            user=user_account_another,
            users=[user_account_another, ]
        )
        TemplateOwner.objects.create(
            template=template_account_another,
            account=account_another,
            type=OwnerType.GROUP,
            group_id=group_to_delete.id,
        )
        workflow_account_another = create_test_workflow(
            user=user_account_another,
            template=template_account_another
        )
        group_to_delete.delete()

        # act
        update_workflow_owners([template_account_another.id])

        # assert
        assert template.owners.all().count() == 1
        assert template.owners.get(group_id=group.id)
        assert workflow.owners.all().count() == 1
        assert workflow.owners.get(id=user.id)
        assert template_account_another.owners.all().count() == 0
        assert workflow_account_another.owners.all().count() == 0

    def test__update_group_owner_user_in_owners_and_members__ok(self):

        # arrange
        account = create_test_account()
        user = create_test_user(account=account)
        template = create_test_template(
            user=user,
            is_active=True,
            tasks_count=1
        )
        TemplateOwner.objects.filter(user_id=user.id).delete()
        group = create_test_group(user=user, users=[user])
        TemplateOwner.objects.create(
            template=template,
            account=account,
            type=OwnerType.GROUP,
            group_id=group.id,
        )
        workflow = create_test_workflow(
            user=user,
            template=template
        )

        # act
        update_workflow_owners([template.id])

        # assert
        assert workflow.owners.all().count() == 1
        assert workflow.owners.get(id=user.id)
        assert workflow.members.all().count() == 1
        assert workflow.members.get(id=user.id)

    def test__update_group_owner_new_user_one_owner_two_members__ok(self):
        """When a group owns a template and its users change, workflow has one
        owner and two members."""
        # arrange
        account = create_test_account()
        user = create_test_user(account=account)
        user_2 = create_test_user(
            account=account,
            email='master@test.test'
        )
        template = create_test_template(
            user=user,
            is_active=True,
            tasks_count=1
        )
        TemplateOwner.objects.filter(user_id=user.id).delete()
        group = create_test_group(user=user, users=[user])
        TemplateOwner.objects.create(
            template=template,
            account=account,
            type=OwnerType.GROUP,
            group_id=group.id,
        )
        workflow = create_test_workflow(
            user=user,
            template=template
        )
        group.users.set([user_2])
        group.save()

        # act
        update_workflow_owners([template.id])

        # assert
        assert workflow.owners.all().count() == 1
        assert workflow.owners.get(id=user_2.id)
        assert workflow.members.all().count() == 2
        assert workflow.members.filter(id=user.id).exists()
        assert workflow.members.filter(id=user_2.id).exists()

    def test__add_group_in_taskperformer__ok(self):
        # arrange
        account = create_test_account()
        user = create_test_user(account=account)
        user_in_group = create_test_user(
            account=account,
            email='groupuser@test.test'
        )
        template = create_test_template(
            user=user,
            is_active=True,
            tasks_count=1
        )
        workflow = create_test_workflow(
            user=user,
            template=template
        )
        group = create_test_group(user=user, users=[user_in_group])
        task = workflow.tasks.first()
        TaskPerformer.objects.create(
            task=task,
            group=group,
            type=PerformerType.GROUP
        )

        # act
        update_workflow_owners([template.id])

        # assert
        assert workflow.members.filter(id=user_in_group.id).exists()

    def test__add_user_in_taskperformer__ok(self):
        # arrange
        account = create_test_account()
        user = create_test_user(account=account)
        task_performer_user = create_test_user(
            account=account,
            email='taskperformer@test.test'
        )
        template = create_test_template(
            user=user,
            is_active=True,
            tasks_count=1
        )
        workflow = create_test_workflow(
            user=user,
            template=template
        )
        task = workflow.tasks.first()
        TaskPerformer.objects.create(
            task=task,
            user=task_performer_user,
            type=PerformerType.USER
        )

        # act
        update_workflow_owners([template.id])

        # assert
        assert workflow.members.filter(id=task_performer_user.id).exists()

    def test__add_group_and_user_in_taskperformer__ok(self):
        # arrange
        account = create_test_account()
        user = create_test_user(account=account)
        group_user = create_test_user(
            account=account,
            email='groupuser@test.test'
        )
        direct_user = create_test_user(
            account=account,
            email='directuser@test.test'
        )
        template = create_test_template(
            user=user,
            is_active=True,
            tasks_count=1
        )
        workflow = create_test_workflow(
            user=user,
            template=template
        )
        group = create_test_group(user=user, users=[group_user])
        task = workflow.tasks.first()
        TaskPerformer.objects.create(
            task=task,
            group=group,
            type=PerformerType.GROUP
        )
        TaskPerformer.objects.create(
            task=task,
            user=direct_user,
            type=PerformerType.USER
        )

        # act
        update_workflow_owners([template.id])

        # assert
        assert workflow.members.filter(id=group_user.id).exists()
        assert workflow.members.filter(id=direct_user.id).exists()

    def test__add_user_in_owner_and_taskperformer__ok(self):
        # arrange
        account = create_test_account()
        user = create_test_user(account=account)
        common_user = create_test_user(
            account=account,
            email='common@test.test'
        )
        template = create_test_template(
            user=user,
            is_active=True,
            tasks_count=1
        )
        TemplateOwner.objects.create(
            template=template,
            account=account,
            type=OwnerType.USER,
            user=common_user
        )
        workflow = create_test_workflow(
            user=user,
            template=template
        )
        task = workflow.tasks.first()
        TaskPerformer.objects.create(
            task=task,
            user=common_user,
            type=PerformerType.USER
        )

        # act
        update_workflow_owners([template.id])

        # assert
        assert workflow.members.filter(id=common_user.id).count() == 1

    def test__add_performer_with_status_deleted__ok(self):
        # arrange
        account = create_test_account()
        user = create_test_user(account=account)
        deleted_performer = create_test_user(
            account=account,
            email='deleted@test.test'
        )
        template = create_test_template(
            user=user,
            is_active=True,
            tasks_count=1
        )
        workflow = create_test_workflow(
            user=user,
            template=template
        )
        task = workflow.tasks.first()
        TaskPerformer.objects.create(
            task=task,
            user=deleted_performer,
            type=PerformerType.USER,
            directly_status=DirectlyStatus.DELETED
        )

        # act
        update_workflow_owners([template.id])

        # assert
        assert not workflow.members.filter(id=deleted_performer.id).exists()

    def test__update_group_taskperformer_add_members__ok(self, api_client):
        # arrange
        account = create_test_account()
        user = create_test_user(account=account)
        user_in_group = create_test_user(
            account=account,
            email='groupuser@test.test'
        )
        template = create_test_template(
            user=user,
            is_active=True,
            tasks_count=1
        )
        workflow = create_test_workflow(
            user=user,
            template=template
        )
        group = create_test_group(user=user)
        task = workflow.tasks.first()
        TaskPerformer.objects.create(
            task=task,
            group=group,
            type=PerformerType.GROUP
        )
        update_workflow_owners([template.id])
        group.users.set([user, user_in_group])
        group.save()

        # act
        update_workflow_owners([template.id])

        # assert
        assert workflow.members.filter(id=user_in_group.id).exists()
