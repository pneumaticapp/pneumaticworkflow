import pytest
from django.contrib.auth import get_user_model
from src.authentication.enums import AuthTokenType
from src.processes.models import (
    TaskTemplate,
    Workflow,
    Task,
    FieldTemplate,
    FieldTemplateSelection,
    Checklist,
    ChecklistSelection,
    TaskField,
    FieldSelection,
    FileAttachment,
    ConditionTemplate,
    RuleTemplate,
    PredicateTemplate,
    TemplateOwner
)
from src.processes.services.versioning.schemas import (
    TemplateSchemaV1,
)
from src.processes.services.versioning.versioning import (
    TemplateVersioningService,
)
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_owner,
    create_test_admin,
    create_test_template,
    create_test_workflow,
    create_invited_user,
    create_checklist_template,
)
from src.processes.enums import (
    FieldType,
    PredicateOperator,
    OwnerType,
    ConditionAction,
)
from src.processes.services.workflows.workflow_version import (
        WorkflowUpdateVersionService
    )
from src.processes.services.tasks.checklist_selection import (
        ChecklistSelectionService
    )


UserModel = get_user_model()


pytestmark = pytest.mark.django_db


class TestWorkflowUpdateVersionService:

    def test_update_from_version__ok(self):

        # arrange
        account = create_test_account()
        user = create_test_owner(account=account)
        template = create_test_template(
            user=user,
            is_active=True,
            tasks_count=1
        )
        kickoff_template = template.kickoff_instance
        workflow = create_test_workflow(
            user=user,
            template=template
        )
        template_task_1 = template.tasks.get(number=1)
        template_task_1.name = 'New task name'
        template_task_1.description = '**Bold [link](http://test.com)**'
        template_task_1.save()
        FieldTemplate.objects.create(
            type=FieldType.NUMBER,
            name='Number field',
            kickoff=kickoff_template,
            template=template,
        )
        field_template = FieldTemplate.objects.create(
            type=FieldType.TEXT,
            name='Text field',
            task=template_task_1,
            template=template,
        )
        condition_template = ConditionTemplate.objects.create(
            task=template_task_1,
            action=ConditionAction.SKIP_TASK,
            order=0,
            template=template,
        )
        rule_template = RuleTemplate.objects.create(
            condition=condition_template,
            template=template,
        )
        PredicateTemplate.objects.create(
            rule=rule_template,
            operator=PredicateOperator.EQUAL,
            field_type=FieldType.STRING,
            field=field_template.api_name,
            value='Skip',
            template=template,
        )
        template.refresh_from_db()
        template = TemplateVersioningService(TemplateSchemaV1).save(template)

        version_service = WorkflowUpdateVersionService(
            instance=workflow,
            user=user,
            is_superuser=False,
            auth_type=AuthTokenType.USER
        )

        # act
        version_service.update_from_version(
            data=template.data,
            version=template.version
        )

        # assert
        kickoff = workflow.kickoff_instance
        assert kickoff.output.filter(
            type=FieldType.NUMBER,
            name='Number field',
            value=''
        ).exists()

        task_1 = workflow.tasks.get(number=1)
        assert task_1.name == template_task_1.name
        assert task_1.description == template_task_1.description
        assert task_1.clear_description == 'Bold link'
        assert task_1.output.filter(
            type=FieldType.TEXT,
            name=field_template.name,
            task=task_1,
            value=''
        ).exists()

        assert task_1.conditions.count() == 1
        condition = task_1.conditions.get(
            action=ConditionAction.SKIP_TASK
        )
        assert condition.rules.count() == 1
        rule = condition.rules.get()
        assert rule.predicates.count() == 1
        assert rule.predicates.get(
            operator=PredicateOperator.EQUAL,
            field_type=FieldType.STRING,
            field=field_template.api_name,
            value='Skip',
        )

    def test_update_from_version__end_workflow__ok(
        self,
        mocker,
        api_client
    ):

        # arrange
        account = create_test_account()
        user = create_test_owner(account=account)
        template = create_test_template(
            user=user,
            is_active=True,
            tasks_count=2
        )
        workflow = create_test_workflow(
            user=user,
            template=template
        )
        task = workflow.tasks.get(number=1)
        mocker.patch(
            'src.processes.tasks.webhooks.'
            'send_task_completed_webhook.delay'
        )
        api_client.token_authenticate(user)
        response_complete = api_client.post(f'/v2/tasks/{task.id}/complete')
        workflow.refresh_from_db()
        template.tasks.get(number=2).delete()
        template.refresh_from_db()
        template = TemplateVersioningService(TemplateSchemaV1).save(template)
        version_service = WorkflowUpdateVersionService(
            instance=workflow,
            user=user,
            is_superuser=False,
            auth_type=AuthTokenType.USER
        )

        # act
        version_service.update_from_version(
            data=template.data,
            version=template.version
        )

        # assert
        assert response_complete.status_code == 200

    def test_update_from_version__existing_values(self):
        # arrange
        account = create_test_account()
        user = create_test_owner(account=account)
        template = create_test_template(
            user=user,
            is_active=True
        )
        kickoff = template.kickoff_instance
        workflow = create_test_workflow(user, template)
        workflow_task = workflow.tasks.get(number=1)

        task_1 = template.tasks.get(number=1)
        task_1.name = 'New task name'
        task_1.save()
        field_template_1 = FieldTemplate.objects.create(
            type=FieldType.TEXT,
            name='Text field',
            task=task_1,
            template=template,
        )
        TaskField.objects.create(
            name='Some text field',
            type=FieldType.STRING,
            api_name=field_template_1.api_name,
            is_required=True,
            task=workflow_task,
            workflow=workflow
        )
        field_template_2 = FieldTemplate.objects.create(
            type=FieldType.CHECKBOX,
            name='Checkbox field',
            task=task_1,
            template=template,
        )
        second_workflow_field = TaskField.objects.create(
            name='Some text',
            type=FieldType.CHECKBOX,
            api_name=field_template_2.api_name,
            is_required=True,
            task=workflow_task,
            workflow=workflow
        )
        FieldTemplateSelection.objects.create(
            value='first',
            field_template=field_template_2,
            template=template,
        )
        FieldTemplateSelection.objects.create(
            value='second',
            field_template=field_template_2,
            template=template,
        )
        FieldSelection.objects.create(
            value='first',
            field=second_workflow_field,
        )
        FieldSelection.objects.create(
            value='old',
            field=second_workflow_field,
        )
        kickoff_field_template_1 = FieldTemplate.objects.create(
            type=FieldType.TEXT,
            name='Text field',
            kickoff=kickoff,
            template=template,
        )
        TaskField.objects.create(
            type=FieldType.TEXT,
            name='Old name',
            api_name=kickoff_field_template_1.api_name,
            kickoff=workflow.kickoff_instance,
            is_required=True,
            workflow=workflow
        )
        kickoff_field_template_2 = FieldTemplate.objects.create(
            type=FieldType.CHECKBOX,
            name='Checkbox field',
            kickoff=kickoff,
            template=template,
        )
        FieldTemplateSelection.objects.create(
            value='first',
            field_template=kickoff_field_template_2,
            template=template,
        )
        FieldTemplateSelection.objects.create(
            value='second',
            field_template=kickoff_field_template_2,
            template=template,
        )

        template.refresh_from_db()
        template = TemplateVersioningService(TemplateSchemaV1).save(template)
        version_service = WorkflowUpdateVersionService(
            instance=workflow,
            user=user,
            is_superuser=False,
            auth_type=AuthTokenType.USER
        )

        # act
        version_service.update_from_version(
            data=template.data,
            version=template.version
        )

        # assert
        kickoff_fields = workflow.kickoff_instance.output.all()

        task_1 = workflow.tasks.get(number=1)
        task_fields = task_1.output.all()

        assert kickoff_fields.count() == 2
        assert kickoff_fields.filter(name='Old name').exists() is False
        assert kickoff_fields.filter(
            type=FieldType.TEXT
        ).first().name == 'Text field'
        assert kickoff_fields.filter(
            type=FieldType.TEXT
        ).first().is_required is False
        assert kickoff_fields.filter(
            type=FieldType.CHECKBOX
        ).first().selections.count() == 2
        assert kickoff_fields.filter(
            type=FieldType.CHECKBOX
        ).first().selections.filter(value='Old name').exists() is False
        assert task_fields.count() == 2
        assert task_fields.filter(
            api_name=field_template_1.api_name
        ).first().type == FieldType.TEXT
        assert task_fields.filter(
            api_name=field_template_1.api_name
        ).first().name == field_template_1.name
        assert task_fields.filter(
            api_name=field_template_2.api_name
        ).first().name == field_template_2.name
        assert task_fields.filter(
            api_name=field_template_2.api_name
        ).first().selections.count() == 2
        assert 'old' not in task_fields.filter(
            api_name=field_template_2.api_name
        ).first().selections.values_list('value', flat=True)
        assert 'first' in task_fields.filter(
            api_name=field_template_2.api_name
        ).first().selections.values_list('value', flat=True)
        assert 'second' in task_fields.filter(
            api_name=field_template_2.api_name
        ).first().selections.values_list('value', flat=True)

    def test_update_from_version__new_tasks(self):
        # arrange
        account = create_test_account()
        user = create_test_owner(account=account)
        template = create_test_template(user)
        workflow = create_test_workflow(user, template)

        last_number = 3
        new_task = TaskTemplate.objects.create(
            account=user.account,
            name='New task',
            description='New description',
            number=last_number+1,
            template=template,
            require_completion_by_all=True
        )
        field_template_1 = FieldTemplate.objects.create(
            type=FieldType.TEXT,
            name='Text field',
            task=new_task,
            template=template,
        )
        field_template_2 = FieldTemplate.objects.create(
            type=FieldType.CHECKBOX,
            name='Checkbox field',
            task=new_task,
            template=template,
        )
        first_selection = FieldTemplateSelection.objects.create(
            value='first',
            field_template=field_template_2,
            template=template,
        )
        second_selection = FieldTemplateSelection.objects.create(
            value='second',
            field_template=field_template_2,
            template=template,
        )

        template.refresh_from_db()
        template = TemplateVersioningService(TemplateSchemaV1).save(template)
        version_service = WorkflowUpdateVersionService(
            instance=workflow,
            user=user,
            is_superuser=False,
            auth_type=AuthTokenType.USER
        )

        # act
        version_service.update_from_version(
            data=template.data,
            version=template.version
        )

        # assert
        workflow = Workflow.objects.get(id=workflow.id)
        last_task = workflow.tasks.filter(number=last_number+1)

        assert last_task.exists() is True
        last_task = last_task.first()
        assert last_task.name == new_task.name
        assert last_task.description == new_task.description
        assert (
            last_task.require_completion_by_all ==
            new_task.require_completion_by_all
        )
        assert last_task.output.filter(
            type=FieldType.TEXT
        ).exists() is True
        assert last_task.output.filter(
            type=FieldType.TEXT
        ).first().name == field_template_1.name
        assert last_task.output.filter(
            type=FieldType.CHECKBOX
        ).exists() is True
        assert last_task.output.filter(
            type=FieldType.CHECKBOX
        ).first().name == field_template_2.name
        assert last_task.output.filter(
            type=FieldType.CHECKBOX
        ).first().selections.count() == 2
        assert last_task.output.filter(
            type=FieldType.CHECKBOX
        ).first().selections.order_by(
            'value'
        ).first().value == first_selection.value
        assert last_task.output.filter(
            type=FieldType.CHECKBOX
        ).first().selections.order_by(
            'value'
        ).last().value == second_selection.value

    def test_update_from_version__new_task_in_urgent_workflow__urgent_too(
        self,
        api_client,
    ):
        # arrange
        account = create_test_account()
        user = create_test_owner(account=account)
        template = create_test_template(user)
        workflow = create_test_workflow(user, template)
        api_client.token_authenticate(user)
        api_client.patch(
            path=f'/workflows/{workflow.id}',
            data={'is_urgent': True}
        )
        workflow.refresh_from_db()

        last_number = 3
        TaskTemplate.objects.create(
            account=user.account,
            name='New task',
            description='New description',
            number=last_number + 1,
            template=template,
            require_completion_by_all=True
        )

        template.refresh_from_db()
        template = TemplateVersioningService(TemplateSchemaV1).save(template)
        version_service = WorkflowUpdateVersionService(
            instance=workflow,
            user=user,
            is_superuser=False,
            auth_type=AuthTokenType.USER
        )

        # act
        version_service.update_from_version(
            data=template.data,
            version=template.version
        )

        # assert
        workflow = Workflow.objects.get(id=workflow.id)
        last_task = workflow.tasks.filter(number=last_number + 1).first()
        assert last_task.is_urgent

    def test_update_from_version__add_attachment_to_task_description(self):
        # arrange
        account = create_test_account()
        user = create_test_owner(account=account)
        template = create_test_template(
            user=user,
            is_active=True
        )
        kickoff = template.kickoff_instance
        kickoff_field_template_1 = FieldTemplate.objects.create(
            type=FieldType.FILE,
            name='Screenshot',
            kickoff=kickoff,
            template=template,
        )
        workflow = create_test_workflow(user, template)
        file_field = TaskField.objects.create(
            type=FieldType.FILE,
            name='Old name',
            api_name=kickoff_field_template_1.api_name,
            kickoff=workflow.kickoff_instance,
            workflow=workflow,
            value='http://file.png',
            clear_value='http://clear-file.png',
            markdown_value='[attachment](http://file.png)',
        )
        attachment = FileAttachment.objects.create(
            name='attachment',
            url='http://file.png',
            workflow=workflow,
            output=file_field,
            account_id=user.account_id,
        )

        task_1 = template.tasks.get(number=1)
        task_1.description = (
            'Screenshot: {{ %s }}' % kickoff_field_template_1.api_name
        )
        task_1.save(update_fields=['description'])

        template.refresh_from_db()
        template = TemplateVersioningService(TemplateSchemaV1).save(template)
        version_service = WorkflowUpdateVersionService(
            instance=workflow,
            user=user,
            is_superuser=False,
            auth_type=AuthTokenType.USER
        )

        # act
        version_service.update_from_version(
            data=template.data,
            version=template.version
        )

        # assert
        task_1 = Task.objects.get(workflow=workflow, number=1)

        assert task_1.description_template == (
            'Screenshot: {{ %s }}' % kickoff_field_template_1.api_name
        )
        expected = (
            f'Screenshot: [{attachment.name}]({attachment.url})'
        )
        assert task_1.description == expected

    def test_update_from_version__add_user_to_current_task__ok(
        self,
        mocker,
        api_client
    ):

        # arrange
        account = create_test_account()
        user = create_test_owner(account=account)
        template = create_test_template(
            user,
            is_active=True,
        )
        invited = create_invited_user(user)

        api_client.token_authenticate(user)
        response = api_client.post(f'/templates/{template.id}/run')
        workflow = Workflow.objects.get(id=response.data['id'])

        task_1 = template.tasks.get(number=1)
        task_1.add_raw_performer(invited)

        template.version += 1
        template.save()
        template.refresh_from_db()
        template = TemplateVersioningService(TemplateSchemaV1).save(template)

        version_service = WorkflowUpdateVersionService(
            instance=workflow,
            user=user,
            is_superuser=False,
            auth_type=AuthTokenType.USER
        )

        # act
        version_service.update_from_version(
            data=template.data,
            version=template.version
        )

        # assert
        workflow.refresh_from_db()
        assert workflow.members.filter(id=invited.id).exists()

    def test_update_from_version__remove_user_from_current_task__ok(
        self,
        mocker,
        api_client
    ):

        # arrange
        account = create_test_account()
        owner = create_test_owner(account=account)
        user_2 = create_test_admin(account=account)
        template = create_test_template(owner, is_active=True)
        task_1 = template.tasks.get(number=1)
        task_1.add_raw_performer(user_2)

        api_client.token_authenticate(owner)
        response = api_client.post(f'/templates/{template.id}/run')
        workflow = Workflow.objects.get(id=response.data['id'])

        task_1.delete_raw_performer(user_2)
        template.version += 1
        template.save()
        template.refresh_from_db()
        template = TemplateVersioningService(TemplateSchemaV1).save(template)
        version_service = WorkflowUpdateVersionService(
            instance=workflow,
            user=owner,
            is_superuser=False,
            auth_type=AuthTokenType.USER
        )

        # act
        version_service.update_from_version(
            data=template.data,
            version=template.version
        )

        # assert
        workflow.refresh_from_db()
        assert workflow.members.filter(id=user_2.id).exists()

    def test_update_from_version__prev_task_checklist__not_changed(
        self,
        api_client
    ):

        # arrange
        account = create_test_account()
        owner = create_test_owner(account=account)
        user_2 = create_test_admin(account=account)
        api_client.token_authenticate(user_2)
        template = create_test_template(
            user=owner,
            is_active=True,
            tasks_count=2
        )
        field_template_1 = FieldTemplate.objects.create(
            type=FieldType.USER,
            name='user',
            kickoff=template.kickoff_instance,
            template=template,
        )
        field_template_2 = FieldTemplate.objects.create(
            type=FieldType.STRING,
            name='text',
            kickoff=template.kickoff_instance,
            template=template
        )
        TemplateOwner.objects.create(
            template=template,
            account=account,
            type=OwnerType.USER,
            user_id=user_2.id,
        )
        template_task_1 = template.tasks.get(number=1)
        template_task_1.add_raw_performer(user_2)
        checklist_template_11 = create_checklist_template(
            task_template=template_task_1,
            api_name_prefix='first-',
            selections_count=2
        )
        cl_selection_template_11 = checklist_template_11.selections.get(
            api_name='first-cl-selection-1'
        )
        cl_selection_template_11.value = (
            '+ {{%s}} +' % field_template_1.api_name
        )
        cl_selection_template_11.save(update_fields=['value'])
        cl_selection_template_12 = checklist_template_11.selections.get(
            api_name='first-cl-selection-2'
        )
        checklist_template_12 = create_checklist_template(
            task_template=template_task_1,
            api_name_prefix='second-',
        )

        # fill workflow
        response_run = api_client.post(
            f'/templates/{template.id}/run',
            data={
                'name': 'Workflow',
                'kickoff': {
                    field_template_1.api_name: str(owner.email),
                    field_template_2.api_name: 'field text',
                }
            }
        )
        workflow = Workflow.objects.get(id=response_run.data['id'])
        task_1 = workflow.tasks.get(number=1)
        checklist_1 = task_1.checklists.get(api_name='first-checklist')
        selection_11 = checklist_1.selections.get(
            api_name='first-cl-selection-1'
        )
        selection_12 = checklist_1.selections.get(
            api_name='first-cl-selection-2'
        )
        checklist_2 = task_1.checklists.get(api_name='second-checklist')
        selection_21 = checklist_2.selections.get(
            api_name='second-cl-selection-1'
        )
        selection_service = ChecklistSelectionService(
            instance=selection_11,
            user=user_2
        )
        selection_service.mark()
        selection_service = ChecklistSelectionService(
            instance=selection_12,
            user=owner
        )
        selection_service.mark()
        selection_service = ChecklistSelectionService(
            instance=selection_21,
            user=user_2
        )
        selection_service.mark()

        response_complete = api_client.post(f'/v2/tasks/{task_1.id}/complete')
        workflow.refresh_from_db()

        # Change template checklists and selections
        cl_selection_template_11.value = (
            '+ {{%s}} +' % field_template_2.api_name
        )
        cl_selection_template_11.save(update_fields=['value'])
        cl_selection_template_12.delete()
        checklist_template_12.delete()

        template.refresh_from_db()
        template_version = TemplateVersioningService(
            TemplateSchemaV1
        ).save(template)

        version_service = WorkflowUpdateVersionService(
            instance=workflow,
            user=owner,
            is_superuser=False,
            auth_type=AuthTokenType.USER
        )

        # act
        version_service.update_from_version(
            data=template_version.data,
            version=template_version.version
        )

        # assert
        assert response_complete.status_code == 200
        selection_11.refresh_from_db()
        assert selection_11.value == f'+ field text +'
        assert selection_11.is_selected
        assert selection_11.date_selected
        assert selection_11.selected_user_id == user_2.id

        assert not ChecklistSelection.objects.filter(
            api_name=selection_12.api_name,
            checklist=checklist_1
        ).exists()

        assert not Checklist.objects.filter(
            api_name=checklist_2.api_name,
            task=task_1
        ).exists()

        task_1.refresh_from_db()
        assert task_1.checklists_total == 1
        assert task_1.checklists_marked == 1

    def test_update_from_version__current_task_checklist__updated(
        self,
        api_client
    ):

        # arrange
        account = create_test_account()
        user = create_test_owner(account=account)
        user_2 = create_test_admin(account=account)
        api_client.token_authenticate(user_2)
        template = create_test_template(
            user=user,
            is_active=True,
            tasks_count=2
        )
        field_template_1 = FieldTemplate.objects.create(
            type=FieldType.USER,
            name='user',
            kickoff=template.kickoff_instance,
            template=template,
        )
        field_template_2 = FieldTemplate.objects.create(
            type=FieldType.STRING,
            name='text',
            kickoff=template.kickoff_instance,
            template=template
        )
        TemplateOwner.objects.create(
            template=template,
            account=user.account,
            type=OwnerType.USER,
            user_id=user_2.id,
        )
        template_task_1 = template.tasks.get(number=1)
        template_task_1.add_raw_performer(user_2)
        checklist_template_11 = create_checklist_template(
            task_template=template_task_1,
            api_name_prefix='first-',
            selections_count=2
        )
        cl_selection_template_11 = checklist_template_11.selections.get(
            api_name='first-cl-selection-1'
        )
        cl_selection_template_12 = checklist_template_11.selections.get(
            api_name='first-cl-selection-2'
        )
        checklist_template_12 = create_checklist_template(
            task_template=template_task_1,
            api_name_prefix='second-',
        )

        # fill workflow
        response_run = api_client.post(
            f'/templates/{template.id}/run',
            data={
                'name': 'Workflow',
                'kickoff': {
                    field_template_1.api_name: str(user.email),
                    field_template_2.api_name: 'field text',
                }
            }
        )
        workflow = Workflow.objects.get(id=response_run.data['id'])

        task_1 = workflow.tasks.get(number=1)
        checklist_1 = task_1.checklists.get(api_name='first-checklist')
        selection_11 = checklist_1.selections.get(
            api_name='first-cl-selection-1'
        )
        selection_12 = checklist_1.selections.get(
            api_name='first-cl-selection-2'
        )
        checklist_2 = task_1.checklists.get(api_name='second-checklist')
        selection_service = ChecklistSelectionService(
            instance=selection_11,
            user=user_2
        )
        selection_service.mark()

        # Change template checklists and selections
        cl_selection_template_11.value = (
            '+ {{%s}} +' % field_template_2.api_name
        )
        cl_selection_template_11.save(update_fields=['value'])
        cl_selection_template_12.delete()
        checklist_template_12.delete()

        template.refresh_from_db()
        template_version = TemplateVersioningService(
            TemplateSchemaV1
        ).save(template)

        version_service = WorkflowUpdateVersionService(
            instance=workflow,
            user=user,
            is_superuser=False,
            auth_type=AuthTokenType.USER
        )

        # act
        version_service.update_from_version(
            data=template_version.data,
            version=template_version.version
        )

        # assert
        task_1.refresh_from_db()
        selection_11.refresh_from_db()
        assert selection_11.value == f'+ field text +'
        assert selection_11.is_selected
        assert selection_11.date_selected
        assert selection_11.selected_user_id == user_2.id

        assert not ChecklistSelection.objects.filter(
            api_name=selection_12.api_name,
            checklist=checklist_1
        ).exists()

        assert not Checklist.objects.filter(
            api_name=checklist_2.api_name,
            task=task_1
        ).exists()

        assert task_1.checklists_total == 1
        assert task_1.checklists_marked == 1

    def test_update_from_version__next_task_checklist__updated(
        self,
        api_client
    ):

        # arrange
        account = create_test_account()
        owner = create_test_owner(account=account)
        user_2 = create_test_admin(account=account)
        api_client.token_authenticate(user_2)
        template = create_test_template(
            user=owner,
            is_active=True,
            tasks_count=2
        )
        field_template_1 = FieldTemplate.objects.create(
            type=FieldType.USER,
            name='user',
            kickoff=template.kickoff_instance,
            template=template,
        )
        field_template_2 = FieldTemplate.objects.create(
            type=FieldType.STRING,
            name='text',
            kickoff=template.kickoff_instance,
            template=template
        )
        TemplateOwner.objects.create(
            template=template,
            account=account,
            type=OwnerType.USER,
            user_id=user_2.id,
        )
        template_task_2 = template.tasks.get(number=2)
        template_task_2.add_raw_performer(user_2)
        checklist_template_11 = create_checklist_template(
            task_template=template_task_2,
            api_name_prefix='first-',
            selections_count=2
        )
        cl_selection_template_11 = checklist_template_11.selections.get(
            api_name='first-cl-selection-1'
        )
        cl_selection_template_12 = checklist_template_11.selections.get(
            api_name='first-cl-selection-2'
        )
        checklist_template_12 = create_checklist_template(
            task_template=template_task_2,
            api_name_prefix='second-',
        )

        # fill workflow
        response_run = api_client.post(
            f'/templates/{template.id}/run',
            data={
                'name': 'Workflow',
                'kickoff': {
                    field_template_1.api_name: str(owner.email),
                    field_template_2.api_name: 'field text',
                }
            }
        )
        workflow = Workflow.objects.get(id=response_run.data['id'])

        task_2 = workflow.tasks.get(number=2)
        checklist_1 = task_2.checklists.get(api_name='first-checklist')
        selection_11 = checklist_1.selections.get(
            api_name='first-cl-selection-1'
        )
        selection_12 = checklist_1.selections.get(
            api_name='first-cl-selection-2'
        )
        checklist_2 = task_2.checklists.get(api_name='second-checklist')

        # Change template checklists and selections
        cl_selection_template_11.value = (
            '+ {{%s}} +' % field_template_2.api_name
        )
        cl_selection_template_11.save(update_fields=['value'])
        cl_selection_template_12.delete()
        checklist_template_12.delete()

        template.refresh_from_db()
        template_version = TemplateVersioningService(
            TemplateSchemaV1
        ).save(template)

        version_service = WorkflowUpdateVersionService(
            instance=workflow,
            user=owner,
            is_superuser=False,
            auth_type=AuthTokenType.USER
        )

        # act
        version_service.update_from_version(
            data=template_version.data,
            version=template_version.version
        )

        # assert
        task_2.refresh_from_db()
        selection_11.refresh_from_db()
        assert selection_11.value == f'+ field text +'
        assert not selection_11.is_selected
        assert selection_11.date_selected is None
        assert selection_11.selected_user_id is None

        assert not ChecklistSelection.objects.filter(
            api_name=selection_12.api_name,
            checklist=checklist_1
        ).exists()

        assert not Checklist.objects.filter(
            api_name=checklist_2.api_name,
            task=task_2
        ).exists()

        assert task_2.checklists_total == 1
        assert task_2.checklists_marked == 0

    def test_update_from_version__disable_name_template__not_change_wf_name(
        self
    ):

        # arrange
        account = create_test_account()
        user = create_test_owner(account=account)
        old_template_name = 'Old template name'
        wf_name_template = ''
        template = create_test_template(
            user=user,
            name=old_template_name,
            is_active=True,
            wf_name_template=wf_name_template,
        )
        old_wf_name = f'{old_template_name} Wow!'
        workflow = create_test_workflow(
            name=old_wf_name,
            user=user,
            template=template,
            name_template=wf_name_template
        )

        template.name = 'New name'
        template.save(update_fields=['name'])
        template.refresh_from_db()
        template = TemplateVersioningService(TemplateSchemaV1).save(template)

        version_service = WorkflowUpdateVersionService(
            instance=workflow,
            user=user,
            is_superuser=False,
            auth_type=AuthTokenType.USER
        )

        # act
        version_service.update_from_version(
            data=template.data,
            version=template.version
        )

        # assert
        workflow.refresh_from_db()
        assert workflow.name == old_wf_name
        assert workflow.name_template == wf_name_template

    def test_update_from_version__enable_name_template__not_change_wf_name(
        self
    ):

        # arrange
        account = create_test_account()
        user = create_test_owner(account=account)
        template = create_test_template(
            user=user,
            name='Old template name',
            is_active=True,
        )
        old_wf_name = 'Old wf name'
        workflow = create_test_workflow(
            name=old_wf_name,
            name_template=old_wf_name,
            user=user,
            template=template,
        )

        wf_name_template = '{{ template-name }} Wow!'
        new_template_name = 'New name'
        template.name = new_template_name
        template.wf_name_template = wf_name_template
        template.save()
        template.refresh_from_db()
        template = TemplateVersioningService(TemplateSchemaV1).save(template)

        version_service = WorkflowUpdateVersionService(
            instance=workflow,
            user=user,
            is_superuser=False,
            auth_type=AuthTokenType.USER
        )

        # act
        version_service.update_from_version(
            data=template.data,
            version=template.version
        )

        # assert
        workflow.refresh_from_db()
        assert workflow.name == old_wf_name
        assert workflow.name_template == old_wf_name
