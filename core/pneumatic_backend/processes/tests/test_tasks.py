from datetime import timedelta
import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from pneumatic_backend.accounts.enums import BillingPlanType
from pneumatic_backend.authentication.enums import AuthTokenType
from pneumatic_backend.processes.tasks.tasks import complete_tasks
from pneumatic_backend.processes.models import (
    Workflow,
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
    OwnerType
)
from pneumatic_backend.processes.utils.workflows import (
    resume_delayed_workflows
)
from pneumatic_backend.processes.services.workflow_action import (
    WorkflowActionService
)
from pneumatic_backend.processes.models.templates.owner import (
    TemplateOwner
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
                'template_owners': [user.id],
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
            user=user,
            is_superuser=False,
            auth_type=AuthTokenType.USER
        )
        resume_workflow_mock.assert_called_once_with(workflow)

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
                'template_owners': [user.id],
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
            is_active=True
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

    def test_update__template_version_difference(self, api_client):
        user = create_test_user()
        template = create_test_template(
            user=user,
            is_active=True
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
            is_active=True
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

    def test_delete__owner_only_group__ok(self):
        '''When deleting a group, an owner of the group type
           is deleted in template, and owner user is deleted in workflow.'''

        # arrange
        account = create_test_account(plan=BillingPlanType.PREMIUM)
        user = create_test_user(account=account)
        template = create_test_template(user=user, is_active=True)
        TemplateOwner.objects.filter(
            type=OwnerType.USER,
            user_id=user.id
        ).delete()
        group = create_test_group(user=user, users=[user, ])
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

    def test_delete__same_user_equal__ok(self):
        '''There are 2 owner types in the template.
           We check that when deleting an owner of the group type,
           the owner of the user type is not deleted. Same user is in group
           and is assigned directly to owner in template.'''

        # arrange
        account = create_test_account(plan=BillingPlanType.PREMIUM)
        user = create_test_user(account=account)
        template = create_test_template(user, is_active=True)
        group_to_delete = create_test_group(user=user, users=[user, ])
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

    def test_delete__different_user_equal__ok(self):
        '''There are 2 owner types in the template.
           We check that when deleting an owner of the group type,
           the owner of the user type is not deleted.
           2 different users, user in group, and user_2 owner in template.'''

        # arrange
        account = create_test_account(plan=BillingPlanType.PREMIUM)
        user = create_test_user(account=account)
        user_2 = create_test_user(account=account, email='test1@test.test')
        template = create_test_template(user_2, is_active=True)
        group_to_delete = create_test_group(user=user_2, users=[user, ])
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

    def test_delete__user_owner_remains__ok(self):
        '''There are 2 owner types in the template. We check that when
           deleting an owner of the group type, the owner of the user
           type is not deleted. there are 2 different users in the group,
           other than the owner type of user.'''

        # arrange
        account = create_test_account(plan=BillingPlanType.PREMIUM)
        user = create_test_user(account=account)
        user_2 = create_test_user(account=account, email='test1@test.test')
        user_3 = create_test_user(account=account, email='test2@test.test')
        template = create_test_template(user, is_active=True)
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

    def test_delete__other_owner_group_remains__ok(self):
        '''2 groups, each group has 1 user. In template 2, the owner of
           group type (both groups) - delete group 1 and check that the second
           owner of the group type remains in template and the user from
           second group also remains in owner workflow.'''

        # arrange
        account = create_test_account(plan=BillingPlanType.PREMIUM)
        user = create_test_user(account=account)
        user_2 = create_test_user(account=account, email='test1@test.test')
        template = create_test_template(user, is_active=True)
        TemplateOwner.objects.filter(
            type=OwnerType.USER,
            user_id=user.id
        ).delete()
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

    def test_delete__other_templates_not_changed__ok(self):
        '''2 groups and 2 templates, each template has an owner of
           group type - delete group 1, the changes affect the first template
           and its workflow, and the second template and its workflow have
           not changed.'''

        # arrange
        account = create_test_account(plan=BillingPlanType.PREMIUM)
        user = create_test_user(account=account)
        template = create_test_template(user, is_active=True)
        TemplateOwner.objects.filter(
            template=template,
            type=OwnerType.USER,
            user_id=user.id
        ).delete()
        template_2 = create_test_template(user, is_active=True)
        TemplateOwner.objects.filter(
            template=template_2,
            type=OwnerType.USER,
            user_id=user.id
        ).delete()
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

    def test_delete__different_accounts__ok(self):
        '''As the base account has only 2 accounts, deleting the group in
           first account should not affect the template and workflow of
           second account.'''

        # arrange
        account = create_test_account(plan=BillingPlanType.PREMIUM)
        user = create_test_user(account=account)
        template = create_test_template(user, is_active=True)
        TemplateOwner.objects.filter(type=OwnerType.USER,
                                     user_id=user.id).delete()
        group = create_test_group(user=user, users=[user, ])
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
        account_another = create_test_account(plan=BillingPlanType.PREMIUM)
        user_account_another = create_test_user(
            account=account_another,
            email='test1@test.test'
        )
        template_account_another = create_test_template(
            user_account_another,
            is_active=True
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
