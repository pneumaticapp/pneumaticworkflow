# pylint:disable=redefined-outer-name
from time import sleep

import pytest
from django.contrib.auth import get_user_model
from django.db.models import F

from pneumatic_backend.accounts.enums import BillingPlanType
from pneumatic_backend.authentication.enums import AuthTokenType
from pneumatic_backend.processes.models import (
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
    Predicate,
    Template,
    WorkflowEvent,
)
from pneumatic_backend.processes.services.versioning.schemas import (
    TemplateSchemaV1,
)
from pneumatic_backend.processes.services.versioning.versioning import (
    TemplateVersioningService,
)
from pneumatic_backend.processes.tests.fixtures import (
    create_test_user,
    create_test_template,
    create_test_workflow,
    create_invited_user,
    create_checklist_template,
    create_test_account,
)
from pneumatic_backend.processes.enums import (
    WorkflowStatus,
    FieldType,
    PredicateOperator,
    PerformerType,
    WorkflowEventType,
)
from pneumatic_backend.processes.api_v2.services.workflows\
    .workflow_version import (
        WorkflowUpdateVersionService
    )
from pneumatic_backend.processes.api_v2.services.task\
    .checklist_selection import (
        ChecklistSelectionService
    )


UserModel = get_user_model()


pytestmark = pytest.mark.django_db


class TestWorkflowUpdate:

    def test_update__ok(self):

        # arrange
        user = create_test_user()
        template = create_test_template(user=user, is_active=True)
        kickoff_template = template.kickoff_instance
        workflow = create_test_workflow(
            user=user,
            template=template
        )
        kickoff_template.description = '*Italic text*'
        kickoff_template.save()

        first_task = template.tasks.order_by('number').first()
        first_task.name = 'New task name'
        first_task.description = '**Bold [link](http://test.com)**'
        first_task.save()
        field_one = FieldTemplate.objects.create(
            type=FieldType.TEXT,
            name='Text field',
            task=first_task,
            template=template,
        )
        field_two = FieldTemplate.objects.create(
            type=FieldType.CHECKBOX,
            name='Checkbox field',
            task=first_task,
            template=template,
        )
        selection_one = FieldTemplateSelection.objects.create(
            value='first',
            field_template=field_two,
            template=template,
        )
        selection_two = FieldTemplateSelection.objects.create(
            value='second',
            field_template=field_two,
            template=template,
        )
        condition_template = ConditionTemplate.objects.create(
            task=first_task,
            action=ConditionTemplate.SKIP_TASK,
            order=0,
            template=template,
        )
        rule_1 = RuleTemplate.objects.create(
            condition=condition_template,
            template=template,
        )
        rule_2 = RuleTemplate.objects.create(
            condition=condition_template,
            template=template,
        )
        predicate_1 = PredicateTemplate.objects.create(
            rule=rule_1,
            operator=PredicateOperator.EQUAL,
            field_type=FieldType.STRING,
            field='surrogate-field-1',
            value='123',
            template=template,
        )
        predicate_2 = PredicateTemplate.objects.create(
            rule=rule_1,
            operator=PredicateOperator.EQUAL,
            field_type=FieldType.STRING,
            field='surrogate-field-2',
            value='456',
            template=template,
        )
        predicate_3 = PredicateTemplate.objects.create(
            rule=rule_2,
            operator=PredicateOperator.EQUAL,
            field_type=FieldType.STRING,
            field='surrogate-field-3',
            value='789',
            template=template,
        )
        kickoff_field_one = FieldTemplate.objects.create(
            type=FieldType.TEXT,
            name='Text field',
            kickoff=kickoff_template,
            template=template,
        )
        kickoff_field_two = FieldTemplate.objects.create(
            type=FieldType.CHECKBOX,
            name='Checkbox field',
            kickoff=kickoff_template,
            template=template,
        )
        kickoff_selection_one = FieldTemplateSelection.objects.create(
            value='first',
            field_template=kickoff_field_two,
            template=template,
        )
        kickoff_selection_two = FieldTemplateSelection.objects.create(
            value='second',
            field_template=kickoff_field_two,
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
        assert kickoff.description == '*Italic text*'
        assert kickoff.clear_description == 'Italic text'
        kickoff_text_field = kickoff.output.filter(
            name='Text field'
        )
        kickoff_checkbox_field = kickoff.output.filter(
            name='Checkbox field'
        )

        first_workflow_task = workflow.tasks.order_by('number').first()
        task_text_field = first_workflow_task.output.filter(
            name='Text field'
        )
        task_checkbox_field = first_workflow_task.output.filter(
            name='Checkbox field'
        )

        assert kickoff.description == '*Italic text*'
        assert kickoff.clear_description == 'Italic text'
        assert first_workflow_task.name == first_task.name
        assert first_workflow_task.description == (
            '**Bold [link](http://test.com)**'
        )
        assert first_workflow_task.clear_description == 'Bold link'
        assert first_task.conditions.count() == 1
        condition = first_task.conditions.get()
        assert condition.rules.count() == 2
        assert Predicate.objects.filter(template_id__in=[
            predicate_1.id,
            predicate_2.id,
            predicate_3.id,
        ]).count() == 3
        assert task_text_field.exists() is True
        assert task_text_field.first().name == field_one.name
        assert task_checkbox_field.exists() is True
        assert task_checkbox_field.first().name == field_two.name
        assert task_checkbox_field.first().type == FieldType.CHECKBOX
        assert task_checkbox_field.first().selections.count() == 2
        assert task_checkbox_field.first().selections.order_by(
            'value'
        ).first().value == selection_one.value
        assert task_checkbox_field.first().selections.order_by(
            'value'
        ).last().value == selection_two.value
        assert kickoff_text_field.exists() is True
        assert kickoff_text_field.first().name == kickoff_field_one.name
        assert kickoff_checkbox_field.exists() is True
        assert kickoff_checkbox_field.first().name == kickoff_field_two.name
        assert kickoff_checkbox_field.first().selections.count() == 2
        assert kickoff_checkbox_field.first().selections.order_by(
            'value'
        ).first().value == kickoff_selection_one.value
        assert kickoff_checkbox_field.first().selections.order_by(
            'value'
        ).last().value == kickoff_selection_two.value

    def test_update__end_workflow__ok(self, mocker, api_client):

        # arrange
        user = create_test_user()
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

        deactivate_cache_mock = mocker.patch(
            'pneumatic_backend.authentication.services.'
            'GuestJWTAuthService.deactivate_task_guest_cache'
        )
        api_client.token_authenticate(user)
        response_complete = api_client.post(
            f'/workflows/{workflow.id}/task-complete',
            data={
                'task_id': workflow.current_task_instance.id
            }
        )
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
        assert response_complete.status_code == 204
        deactivate_cache_mock.assert_called_once_with(task_id=task.id)

    def test_complete_task__execute_condition_in_next(
        self,
        api_client,
    ):
        # arrange
        user = create_test_user()
        another_user = create_invited_user(
            user=user,
            email='anotheruser@pneumatic.app',
            is_admin=True,
        )
        template = create_test_template(
            user=user,
            is_active=True
        )
        kickoff = template.kickoff_instance
        kickoff_field_one = FieldTemplate.objects.create(
            type=FieldType.TEXT,
            name='Text field',
            kickoff=kickoff,
            template=template,
        )
        first_task = template.tasks.order_by('number').first()
        first_task.require_completion_by_all = True
        first_task.save()
        first_task.add_raw_performer(user=another_user)
        second_task = template.tasks.get(number=2)
        condition_template = ConditionTemplate.objects.create(
            task=second_task,
            action=ConditionTemplate.SKIP_TASK,
            order=0,
            template=template,
        )
        rule_1 = RuleTemplate.objects.create(
            condition=condition_template,
            template=template,
        )
        PredicateTemplate.objects.create(
            rule=rule_1,
            operator=PredicateOperator.EQUAL,
            field_type=FieldType.STRING,
            field=kickoff_field_one.api_name,
            value='123',
            template=template,
        )

        api_client.token_authenticate(user)
        response = api_client.post(
            f'/templates/{template.id}/run',
            data={
                'name': 'Workflow',
                'kickoff': {
                    kickoff_field_one.api_name: '123',
                }
            }
        )
        workflow = Workflow.objects.get(id=response.data['workflow_id'])

        api_client.post(
            f'/workflows/{workflow.id}/task-complete',
            data={
                'task_id': workflow.current_task_instance.id,
            }
        )

        first_task.require_completion_by_all = False
        first_task.save()
        template.refresh_from_db()
        template = TemplateVersioningService(
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
            data=template.data,
            version=template.version
        )

        # assert
        workflow.refresh_from_db()
        assert workflow.current_task == 3

    def test_delete_last_field_in_task__delete_from_processes(self):
        user = create_test_user()
        template = create_test_template(user)
        first_task = template.tasks.order_by('number').first()
        first_task.name = 'New task name'
        first_task.save()
        field_one = FieldTemplate.objects.create(
            type=FieldType.STRING,
            name='Text field',
            task=first_task,
            template=template,
        )
        template.refresh_from_db()
        workflow = create_test_workflow(user, template)
        workflow_task = workflow.current_task_instance
        TaskField.objects.create(
            name='Some text field',
            type=FieldType.STRING,
            api_name=field_one.api_name,
            is_required=True,
            task=workflow_task,
            template_id=field_one.id,
            workflow=workflow
        )

        FieldTemplate.objects.filter(task=first_task).delete()

        template.version += 1
        template.save()
        template.refresh_from_db()
        template = TemplateVersioningService(TemplateSchemaV1).save(template)
        workflow.refresh_from_db()
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

        first_workflow_task = workflow.tasks.order_by('number').first()
        task_text_field = first_workflow_task.output.filter(
            name='Text field'
        )

        assert first_workflow_task.name == first_task.name
        assert task_text_field.exists() is False

    def test_add_delay_before_current_task__not_delayed_wf(
        self,
        api_client,
    ):
        # arrange
        user = create_test_user()
        template = create_test_template(user, is_active=True)
        workflow = create_test_workflow(user, template)

        workflow_second_task = workflow.tasks.get(number=2)
        assert workflow_second_task.delay_set.exists() is False

        api_client.token_authenticate(user)
        response = api_client.post(
            f'/workflows/{workflow.id}/task-complete',
            data={
                'task_id': workflow.current_task_instance.id,
            }
        )
        assert response.status_code == 204
        workflow.refresh_from_db()

        template_task_2 = template.tasks.get(number=2)
        template_task_2.delay = '00:05:00'
        template_task_2.save()

        template.version += 1
        template.save()
        template.refresh_from_db()
        template = TemplateVersioningService(TemplateSchemaV1).save(
            template
        )
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
        workflow_second_task.refresh_from_db()
        delay = workflow_second_task.delay_set.first()
        assert workflow.status == WorkflowStatus.RUNNING
        assert delay.start_date is None
        assert delay.end_date is None

    def test_update__remove_delay_from_current_task_with_delay__ok(
        self,
        api_client
    ):
        # arrange
        user = create_test_user()
        template = create_test_template(user=user)
        template_task_2 = template.tasks.get(number=2)
        template_task_2.delay = '01:00:00'
        template_task_2.save(update_fields=['delay'])
        workflow = create_test_workflow(user=user, template=template)
        api_client.token_authenticate(user)

        response_complete = api_client.post(
            f'/workflows/{workflow.id}/task-complete',
            data={
                'task_id': workflow.current_task_instance.id,
            }
        )

        template_task_2.delay = None
        template_task_2.save(update_fields=['delay'])
        template.version += 1
        template.save(update_fields=['version'])
        template.refresh_from_db()

        template = TemplateVersioningService(TemplateSchemaV1).save(template)
        workflow.refresh_from_db()
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
        assert response_complete.status_code == 204
        workflow.refresh_from_db()
        assert workflow.status == WorkflowStatus.RUNNING
        delay_json = WorkflowEvent.objects.get(
            type=WorkflowEventType.DELAY,
            workflow=workflow,
        ).delay_json
        assert delay_json['start_date']
        assert delay_json['end_date'] is None
        task_2 = workflow.tasks.get(number=2)
        assert task_2.get_active_delay() is None
        assert task_2.date_started is not None
        assert WorkflowEvent.objects.filter(
            type=WorkflowEventType.TASK_START,
            workflow=workflow,
        ).count() == 1

    def test_decrease_delay__already_expired__next_task(self, api_client):
        # arrange
        user = create_test_user()
        template = create_test_template(user)
        template_task_2 = template.tasks.get(number=2)
        template_task_2.delay = '00:05:00'
        template_task_2.save()
        workflow = create_test_workflow(user, template)

        workflow_second_task = workflow.tasks.get(number=2)

        api_client.token_authenticate(user)
        response = api_client.post(
            f'/workflows/{workflow.id}/task-complete',
            data={
                'task_id': workflow.current_task_instance.id,
            }
        )
        assert response.status_code == 204
        assert workflow_second_task.delay_set.exists() is True

        template_task_2.delay = '00:00:01'
        template_task_2.save()
        template.version += 1
        template.save()
        template.refresh_from_db()
        template = TemplateVersioningService(TemplateSchemaV1).save(template)
        workflow.refresh_from_db()
        version_service = WorkflowUpdateVersionService(
            instance=workflow,
            user=user,
            is_superuser=False,
            auth_type=AuthTokenType.USER
        )
        sleep(2)

        # act
        version_service.update_from_version(
            data=template.data,
            version=template.version
        )

        # assert
        workflow.refresh_from_db()
        workflow_second_task.refresh_from_db()
        assert workflow_second_task.delay_set.exists() is True
        assert workflow.status == 0
        assert workflow_second_task.date_started
        assert WorkflowEvent.objects.filter(
            type=WorkflowEventType.TASK_START,
            workflow=workflow,
        ).count() == 1
        delay_json = WorkflowEvent.objects.get(
            type=WorkflowEventType.DELAY,
            workflow=workflow,
        ).delay_json
        assert delay_json['start_date']
        assert delay_json['end_date'] is None

    def test_delay_template__edit_anything__do_not_move_to_next(
        self,
        api_client,
    ):
        # arrange
        user = create_test_user()
        template = create_test_template(user)
        template_task_2 = template.tasks.get(number=2)
        template_task_2.delay = '01:00:00'
        template_task_2.save()
        workflow = create_test_workflow(user=user, template=template)
        api_client.token_authenticate(user)

        response_complete = api_client.post(
            f'/workflows/{workflow.id}/task-complete',
            data={
                'task_id': workflow.current_task_instance.id,
            }
        )

        template_task_2.description = 'Edited'
        template_task_2.save(update_fields=['description'])
        template.version += 1
        template.save(update_fields=['version'])
        template.refresh_from_db()
        template = TemplateVersioningService(TemplateSchemaV1).save(template)
        workflow.refresh_from_db()
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
        assert response_complete.status_code == 204

        workflow.refresh_from_db()
        assert workflow.status == WorkflowStatus.DELAYED

        task_2 = workflow.tasks.get(number=2)
        assert task_2.date_started is None
        assert task_2.get_active_delay()

        assert WorkflowEvent.objects.filter(
            type=WorkflowEventType.TASK_START,
            workflow=workflow,
        ).count() == 0
        delay_json = WorkflowEvent.objects.get(
            type=WorkflowEventType.DELAY,
            workflow=workflow,
        ).delay_json
        assert delay_json['start_date']
        assert not delay_json['end_date']

    def test_update_existing_values(self):
        # arrange
        user = create_test_user()
        template = create_test_template(
            user=user,
            is_active=True
        )
        kickoff = template.kickoff_instance
        workflow = create_test_workflow(user, template)
        workflow_task = workflow.tasks.order_by('number').first()

        first_task = template.tasks.order_by('number').first()
        first_task.name = 'New task name'
        first_task.save()
        field_one = FieldTemplate.objects.create(
            type=FieldType.TEXT,
            name='Text field',
            task=first_task,
            template=template,
        )
        TaskField.objects.create(
            name='Some text field',
            type=FieldType.STRING,
            api_name=field_one.api_name,
            is_required=True,
            task=workflow_task,
            template_id=field_one.id,
            workflow=workflow
        )
        field_two = FieldTemplate.objects.create(
            type=FieldType.CHECKBOX,
            name='Checkbox field',
            task=first_task,
            template=template,
        )
        second_workflow_field = TaskField.objects.create(
            name='Some text',
            type=FieldType.CHECKBOX,
            api_name=field_two.api_name,
            is_required=True,
            task=workflow_task,
            template_id=field_two.id,
            workflow=workflow
        )
        selection_one = FieldTemplateSelection.objects.create(
            value='first',
            field_template=field_two,
            template=template,
        )
        selection_two = FieldTemplateSelection.objects.create(
            value='second',
            field_template=field_two,
            template=template,
        )
        FieldSelection.objects.create(
            value='first',
            field=second_workflow_field,
            template_id=selection_one.id,
        )
        FieldSelection.objects.create(
            value='old',
            field=second_workflow_field,
            template_id=selection_two.id,
        )
        kickoff_field_one = FieldTemplate.objects.create(
            type=FieldType.TEXT,
            name='Text field',
            kickoff=kickoff,
            template=template,
        )
        TaskField.objects.create(
            type=FieldType.TEXT,
            name='Old name',
            api_name=kickoff_field_one.api_name,
            kickoff=workflow.kickoff_instance,
            is_required=True,
            template_id=kickoff_field_one.id,
            workflow=workflow
        )
        kickoff_field_two = FieldTemplate.objects.create(
            type=FieldType.CHECKBOX,
            name='Checkbox field',
            kickoff=kickoff,
            template=template,
        )
        FieldTemplateSelection.objects.create(
            value='first',
            field_template=kickoff_field_two,
            template=template,
        )
        FieldTemplateSelection.objects.create(
            value='second',
            field_template=kickoff_field_two,
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

        first_workflow_task = workflow.tasks.order_by('number').first()
        task_fields = first_workflow_task.output.all()

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
            api_name=field_one.api_name
        ).first().type == FieldType.TEXT
        assert task_fields.filter(
            api_name=field_one.api_name
        ).first().name == field_one.name
        assert task_fields.filter(
            api_name=field_two.api_name
        ).first().name == field_two.name
        assert task_fields.filter(
            api_name=field_two.api_name
        ).first().selections.count() == 2
        assert 'old' not in task_fields.filter(
            api_name=field_two.api_name
        ).first().selections.values_list('value', flat=True)
        assert 'first' in task_fields.filter(
            api_name=field_two.api_name
        ).first().selections.values_list('value', flat=True)
        assert 'second' in task_fields.filter(
            api_name=field_two.api_name
        ).first().selections.values_list('value', flat=True)

    def test_update_new_tasks(self):
        # arrange
        user = create_test_user()
        template = create_test_template(user)
        workflow = create_test_workflow(user, template)

        last_number = template.tasks.order_by('number').last().number
        new_task = TaskTemplate.objects.create(
            account=user.account,
            name='New task',
            description='New description',
            number=last_number+1,
            template=template,
            require_completion_by_all=True
        )
        field_one = FieldTemplate.objects.create(
            type=FieldType.TEXT,
            name='Text field',
            task=new_task,
            template=template,
        )
        field_two = FieldTemplate.objects.create(
            type=FieldType.CHECKBOX,
            name='Checkbox field',
            task=new_task,
            template=template,
        )
        first_selection = FieldTemplateSelection.objects.create(
            value='first',
            field_template=field_two,
            template=template,
        )
        second_selection = FieldTemplateSelection.objects.create(
            value='second',
            field_template=field_two,
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
        ).first().name == field_one.name
        assert last_task.output.filter(
            type=FieldType.CHECKBOX
        ).exists() is True
        assert last_task.output.filter(
            type=FieldType.CHECKBOX
        ).first().name == field_two.name
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

    def test_update__new_task_in_urgent_workflow__urgent_too(
        self,
        api_client,
    ):
        # arrange
        user = create_test_user()
        template = create_test_template(user)
        workflow = create_test_workflow(user, template)
        api_client.token_authenticate(user)
        api_client.patch(
            path=f'/workflows/{workflow.id}',
            data={'is_urgent': True}
        )
        workflow.refresh_from_db()

        last_number = template.tasks.order_by('number').last().number
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

    def test_update__add_attachment_to_task_description(self):
        # arrange
        user = create_test_user()
        template = create_test_template(
            user=user,
            is_active=True
        )
        kickoff = template.kickoff_instance
        kickoff_field_one = FieldTemplate.objects.create(
            type=FieldType.FILE,
            name='Screenshot',
            kickoff=kickoff,
            template=template,
        )
        workflow = create_test_workflow(user, template)
        file_field = TaskField.objects.create(
            type=FieldType.FILE,
            name='Old name',
            api_name=kickoff_field_one.api_name,
            kickoff=workflow.kickoff_instance,
            template_id=kickoff_field_one.id,
            workflow=workflow,
            value='http://file.png'
        )
        attachment = FileAttachment.objects.create(
            name='attachment',
            url='http://file.png',
            workflow=workflow,
            output=file_field,
            account_id=user.account_id,
        )

        first_task = template.tasks.order_by('number').first()
        first_task.description = (
            'Screenshot: {{ %s }}' % kickoff_field_one.api_name
        )
        first_task.save(update_fields=['description'])

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
        first_task = Task.objects.get(workflow=workflow, number=1)

        assert first_task.description_template == (
            'Screenshot: {{ %s }}' % kickoff_field_one.api_name
        )
        expected = (
            f'Screenshot: [{kickoff_field_one.name}]'
            f'({attachment.url})'
        )
        assert first_task.description == expected

    def test_not_require_completion_by_all_for_current__go_to_next(
        self,
        api_client,
    ):
        # arrange
        user = create_test_user()
        invited = create_invited_user(user)
        template = create_test_template(user)
        template_task_2 = template.tasks.get(number=2)
        template_task_2.add_raw_performer(invited)
        template_task_2.require_completion_by_all = True
        template_task_2.save()

        workflow = create_test_workflow(user, template)
        workflow_second_task = workflow.tasks.get(number=2)
        workflow_first_task = workflow.tasks.get(number=1)
        api_client.token_authenticate(user)
        api_client.post(
            f'/workflows/{workflow.id}/task-complete',
            data={
                'task_id': workflow_first_task.id
            }
        )
        api_client.post(
            f'/workflows/{workflow.id}/task-complete',
            data={
                'task_id': workflow_second_task.id
            }
        )
        template_task_2.require_completion_by_all = False
        template_task_2.save()
        template.version += 1
        template.save()

        template.refresh_from_db()
        template = TemplateVersioningService(TemplateSchemaV1).save(template)
        workflow.refresh_from_db()
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
        workflow_second_task.refresh_from_db()
        assert workflow_second_task.performers.count() == 2
        assert workflow_second_task.taskperformer_set.get(
            user=user
        ).is_completed
        assert workflow.current_task == 3

    def test_remove_not_completed_user_from_task__go_to_next(
        self,
        api_client,
    ):
        # arrange
        user = create_test_user()
        api_client.token_authenticate(user)
        invited = create_invited_user(user)
        template = create_test_template(user)
        template_task_2 = template.tasks.get(number=2)
        template_task_2.add_raw_performer(invited)
        template_task_2.require_completion_by_all = True
        template_task_2.save()

        workflow = create_test_workflow(user, template)
        task_1 = workflow.tasks.get(number=1)
        response1 = api_client.post(
            f'/workflows/{workflow.id}/task-complete',
            data={
                'task_id': task_1.id
            }
        )
        assert response1.status_code == 204
        task_2 = workflow.tasks.get(number=2)
        response2 = api_client.post(
            f'/workflows/{workflow.id}/task-complete',
            data={
                'task_id': task_2.id
            }
        )
        assert response2.status_code == 204
        template_task_2.delete_raw_performer(invited)
        template.version += 1
        template.save()

        template.refresh_from_db()
        template = TemplateVersioningService(TemplateSchemaV1).save(template)
        workflow.refresh_from_db()
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
        task_2.refresh_from_db()
        assert task_2.performers.count() == 1
        assert task_2.performers.first() == user
        assert task_2.taskperformer_set.get(
            user=user
        ).is_completed
        assert workflow.current_task == 3

    def test_go_to_next_with_delay__workflow_delayed(
        self,
        api_client,
    ):
        # arrange
        user = create_test_user()
        invited = create_invited_user(user)
        template = create_test_template(user)
        template_task_1 = template.tasks.get(number=1)
        template_task_1.add_raw_performer(invited)
        template_task_1.require_completion_by_all = True
        template_task_1.save()
        template_task_2 = template.tasks.get(number=2)
        template_task_2.delay = '00:05:00'
        template_task_2.save()

        workflow = create_test_workflow(user, template)
        task_2 = workflow.tasks.get(number=2)
        api_client.token_authenticate(user)
        api_client.post(
            f'/workflows/{workflow.id}/task-complete',
            data={
                'task_id': workflow.current_task_instance.id
            }
        )

        template_task_1.delete_raw_performer(invited)
        template.version += 1
        template.save()

        template.refresh_from_db()
        template_version = TemplateVersioningService(
            TemplateSchemaV1
        ).save(template)
        workflow.refresh_from_db()
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
        workflow.refresh_from_db()
        task_2.refresh_from_db()
        assert task_2.performers.count() == 1
        assert task_2.performers.first() == user
        assert workflow.current_task == 2
        assert workflow.status == WorkflowStatus.DELAYED
        assert workflow.current_task_instance.date_started is None

    def test_add_user_to_current_task__ok(
        self,
        mocker,
        api_client
    ):

        # arrange
        user = create_test_user()
        template = create_test_template(
            user,
            is_active=True,
        )
        user.account.billing_plan = BillingPlanType.PREMIUM
        user.account.save()
        invited = create_invited_user(user)

        api_client.token_authenticate(user)
        response = api_client.post(f'/templates/{template.id}/run')
        workflow = Workflow.objects.get(id=response.data['workflow_id'])

        first_task = template.tasks.get(number=1)
        first_task.add_raw_performer(invited)

        template.version += 1
        template.save()
        template.refresh_from_db()
        template = TemplateVersioningService(TemplateSchemaV1).save(template)
        send_new_task_notification_mock = mocker.patch(
            'pneumatic_backend.processes.services.websocket.WSSender.'
            'send_new_task_notification'
        )
        send_removed_task_notification_mock = mocker.patch(
            'pneumatic_backend.processes.services.websocket.WSSender.'
            'send_removed_task_notification'
        )
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
        send_new_task_notification_mock.assert_called_once()
        send_removed_task_notification_mock.assert_not_called()

    def test_remove_user_from_current_task__ok(
        self,
        mocker,
        api_client
    ):

        # arrange
        account = create_test_account(
            plan=BillingPlanType.PREMIUM
        )
        user = create_test_user(account=account)
        user_2 = create_test_user(
            account=account,
            is_account_owner=False,
            email='second@performer.com'
        )
        template = create_test_template(
            user,
            is_active=True,
        )
        first_task = template.tasks.get(number=1)
        first_task.add_raw_performer(user_2)

        api_client.token_authenticate(user)
        response = api_client.post(f'/templates/{template.id}/run')
        workflow = Workflow.objects.get(id=response.data['workflow_id'])

        first_task.delete_raw_performer(user_2)
        template.version += 1
        template.save()
        template.refresh_from_db()
        template = TemplateVersioningService(TemplateSchemaV1).save(template)
        send_new_task_notification_mock = mocker.patch(
            'pneumatic_backend.processes.services.websocket.WSSender.'
            'send_new_task_notification'
        )
        send_removed_task_notification_mock = mocker.patch(
            'pneumatic_backend.processes.services.websocket.WSSender.'
            'send_removed_task_notification'
        )
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
        current_task = workflow.current_task_instance
        assert workflow.members.filter(id=user_2.id).exists()
        send_new_task_notification_mock.assert_not_called()
        send_removed_task_notification_mock.assert_called_once_with(
            task=current_task,
            user_ids={user_2.id},
            sync=False
        )

    def test_update__prev_task_checklist__not_changed(
        self,
        api_client
    ):

        # arrange
        user = create_test_user()
        user_2 = create_test_user(account=user.account, email='t@t.t')
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

        template.template_owners.add(user_2)
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
                    field_template_1.api_name: str(user.id),
                    field_template_2.api_name: 'field text',
                }
            }
        )
        workflow = Workflow.objects.get(id=response_run.data['workflow_id'])
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
            user=user
        )
        selection_service.mark()
        selection_service = ChecklistSelectionService(
            instance=selection_21,
            user=user_2
        )
        selection_service.mark()

        response_complete = api_client.post(
            f'/workflows/{workflow.id}/task-complete',
            data={
                'task_id': workflow.current_task_instance.id
            }
        )
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
        assert response_complete.status_code == 204
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

    def test_update__current_task_checklist__updated(
        self,
        api_client
    ):

        # arrange
        user = create_test_user()
        user_2 = create_test_user(account=user.account, email='t@t.t')
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
        template.template_owners.add(user_2)
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
                    field_template_1.api_name: str(user.id),
                    field_template_2.api_name: 'field text',
                }
            }
        )
        workflow = Workflow.objects.get(id=response_run.data['workflow_id'])

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

    def test_update__next_task_checklist__updated(
        self,
        api_client
    ):

        # arrange
        user = create_test_user()
        user_2 = create_test_user(account=user.account, email='t@t.t')
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
        template.template_owners.add(user_2)
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
                    field_template_1.api_name: str(user.id),
                    field_template_2.api_name: 'field text',
                }
            }
        )
        workflow = Workflow.objects.get(id=response_run.data['workflow_id'])

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

    def test_update__disable_name_template__not_change_wf_name(self):

        # arrange
        user = create_test_user()
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

    def test_update__enable_name_template__not_change_wf_name(self):

        # arrange
        user = create_test_user()
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


class TestMoveToCorrectStep:

    def test_current_last_task__deleted__workflow_done(self, api_client):
        # arrange
        user = create_test_user()
        template = create_test_template(user)
        workflow = create_test_workflow(user, template)
        api_client.token_authenticate(user)

        last_task = workflow.tasks.order_by('number').last()
        tasks = workflow.tasks.filter(
            number__lt=last_task.number
        ).order_by('number')
        for task in tasks:
            api_client.post(
                f'/workflows/{workflow.id}/task-complete',
                data={
                    'task_id': task.id
                }
            )
        template.tasks.filter(number=last_task.number).delete()
        template.version += 1
        template.save()
        template.refresh_from_db()

        template = TemplateVersioningService(TemplateSchemaV1).save(template)

        assert len(template.data.get('tasks')) == 2
        workflow.refresh_from_db()
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
        assert workflow.current_task == 2
        assert workflow.tasks_count == 2
        assert workflow.status == WorkflowStatus.DONE
        assert workflow.current_task_instance.id != last_task.id

    def test_move_added_before_current(self, api_client):
        # arrange
        user = create_test_user()
        template = create_test_template(user)
        workflow = create_test_workflow(user, template)
        api_client.token_authenticate(user)

        tasks_count = workflow.tasks_count
        template.tasks.update(number=F('number')+1)
        new_task_template = TaskTemplate.objects.create(
            account=template.account,
            number=1,
            name='New task',
            template=template,
        )
        new_task_template.add_raw_performer(user)

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
        assert workflow.current_task == 2
        assert workflow.tasks_count == tasks_count + 1
        new_added_task = workflow.tasks.get(number=1)
        assert new_added_task.is_completed is False
        assert new_added_task.date_completed is None
        assert new_added_task.date_first_started is None
        assert new_added_task.date_started is None
        assert new_added_task.is_skipped is True

    def test_move_added_before_current_old_not_changed(self, api_client):

        # arrange
        user = create_test_user()
        template = create_test_template(user, tasks_count=3, is_active=True)
        workflow = create_test_workflow(user=user, template=template)

        api_client.token_authenticate(user)
        response_complete_1 = api_client.post(
            f'/workflows/{workflow.id}/task-complete',
            data={
                'task_id': workflow.current_task_instance.id,
            }
        )
        old_task_1 = workflow.tasks.get(number=1)
        template.tasks.update(number=F('number')+1)
        new_task_template = TaskTemplate.objects.create(
            account=template.account,
            number=1,
            name='New task №1',
            template=template,
        )
        new_task_template.add_raw_performer(user)

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
        assert response_complete_1.status_code == 204
        old_task_1.refresh_from_db()
        workflow.refresh_from_db()
        assert old_task_1.number == 2
        assert workflow.tasks_count == 4
        assert old_task_1.is_completed is True
        assert old_task_1.date_completed is not None
        assert old_task_1.date_first_started is not None
        assert old_task_1.date_started is not None
        assert old_task_1.is_skipped is False
        assert old_task_1.taskperformer_set.filter(
            user_id=user.id,
            is_completed=True
        ).exclude_directly_deleted().exists()

    def test_move_changed_last_performers(self, api_client):
        # TODO ничерта не ясно что за кейс
        # arrange
        user = create_test_user()
        invited = create_invited_user(user)
        template = create_test_template(user)
        workflow = create_test_workflow(user, template)
        last_task = workflow.tasks.order_by('number').last()
        raw_performer = last_task.add_raw_performer(invited)
        last_task.update_performers(raw_performer)
        last_task.require_completion_by_all = True
        last_task.save()

        api_client.token_authenticate(user)
        tasks = workflow.tasks.filter(
            number__lte=last_task.number
        ).order_by('number')
        for task in tasks:
            api_client.post(
                f'/workflows/{workflow.id}/task-complete',
                data={
                    'task_id': task.id
                }
            )

        last_task_template = template.tasks.order_by('number').last()
        last_task_template.delete_raw_performers()
        last_task_template.add_raw_performer(user)

        workflow.refresh_from_db()
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
        last_task.refresh_from_db()

        assert workflow.status == WorkflowStatus.DONE
        assert last_task.is_completed is True

    def test_events_not_sent(self, api_client):

        # arrange
        user = create_test_user()
        template = create_test_template(user)
        workflow = create_test_workflow(user, template)
        api_client.token_authenticate(user)

        template.tasks.update(number=F('number')+1)
        new_task_template = TaskTemplate.objects.create(
            account=template.account,
            number=1,
            name='New task №1',
            template=template,
        )
        new_task_template.add_raw_performer(user)
        events_count = workflow.events.count()

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
        workflow.refresh_from_db()

        # assert
        assert workflow.events.count() == events_count

    def test_delete_current_task__move_to_next(self, mocker, api_client):

        # arrange
        user = create_test_user()
        api_client.token_authenticate(user)
        response_create = api_client.post(
            path='/templates',
            data={
                'name': 'Template',
                'template_owners': [user.id],
                'is_active': True,
                'kickoff': {},
                'tasks': [
                    {
                        'number': 1,
                        'name': 'Step 1',
                        'raw_performers': [
                            {
                                'type': PerformerType.USER,
                                'source_id': user.id
                            }
                        ]
                    },
                    {
                        'number': 2,
                        'name': 'Step 2',
                        'raw_performers': [
                            {
                                'type': PerformerType.USER,
                                'source_id': user.id
                            }
                        ]
                    },
                    {
                        'number': 3,
                        'name': 'Step 3',
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
        template = Template.objects.get(id=response_create.data['id'])
        task_template_1 = template.tasks.get(number=1)
        task_template_3 = template.tasks.get(number=3)
        response_run = api_client.post(
            f'/templates/{template.id}/run',
            data={'name': 'Workflow'}
        )
        workflow = Workflow.objects.get(id=response_run.data['workflow_id'])
        task_1 = workflow.current_task_instance
        response_complete = api_client.post(
            f'/workflows/{workflow.id}/task-complete',
            data={
                'task_id': task_1.id
            }
        )

        response_update = api_client.put(
            path=f'/templates/{template.id}',
            data={
                'id': template.id,
                'is_active': True,
                'is_public': template.is_public,
                'description': template.description,
                'name': template.name,
                'template_owners': [user.id],
                'finalizable': True,
                'kickoff': {
                    'id': template.kickoff_instance.id
                },
                'tasks': [
                    {
                        'id': task_template_1.id,
                        'api_name': task_template_1.api_name,
                        'number': 1,
                        'name': task_template_1.name,
                        'raw_performers': [
                            {
                                'type': PerformerType.USER,
                                'source_id': user.id
                            }
                        ]
                    },
                    {
                        'id': task_template_3.id,
                        'api_name': task_template_3.api_name,
                        'number': 2,
                        'name': task_template_3.name,
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

        template.refresh_from_db()
        workflow.refresh_from_db()

        template = TemplateVersioningService(TemplateSchemaV1).save(template)
        version_service = WorkflowUpdateVersionService(
            instance=workflow,
            user=user,
            is_superuser=False,
            auth_type=AuthTokenType.USER,
            sync=True
        )

        # act
        version_service.update_from_version(
            data=template.data,
            version=template.version
        )

        # assert
        assert response_create.status_code == 200
        assert response_run.status_code == 200
        assert response_complete.status_code == 204
        assert response_update.status_code == 200
        workflow.refresh_from_db()
        assert workflow.current_task == 2
        assert workflow.status == WorkflowStatus.RUNNING
        task_3 = workflow.current_task_instance
        assert task_3.number == 2
        assert task_3.date_started is not None
        assert task_3.date_first_started is not None
        assert task_3.date_completed is None
        assert task_3.is_skipped is False
        assert task_3.taskperformer_set.count() == 1
        task_performer = task_3.taskperformer_set.first()
        assert task_performer.is_completed is False
        assert task_performer.date_completed is None
        assert task_performer.user == user
        assert WorkflowEvent.objects.get(
            account=user.account,
            workflow=workflow,
            type=WorkflowEventType.TASK_START,
            task_json__number=2,
            task_json__id=task_3.id
        )

    def test_delete_delayed_current_task__move_to_next(
        self,
        api_client,
    ):
        # arrange
        user = create_test_user()
        api_client.token_authenticate(user)

        # act
        response_create = api_client.post(
            path='/templates',
            data={
                'name': 'Template',
                'template_owners': [user.id],
                'is_active': True,
                'kickoff': {},
                'tasks': [
                    {
                        'number': 1,
                        'name': 'Step 1',
                        'raw_performers': [
                            {
                                'type': PerformerType.USER,
                                'source_id': user.id
                            }
                        ]
                    },
                    {
                        'number': 2,
                        'name': 'Step 2',
                        'delay': '01:00:00',
                        'raw_performers': [
                            {
                                'type': PerformerType.USER,
                                'source_id': user.id
                            }
                        ]
                    },
                    {
                        'number': 3,
                        'name': 'Step 3',
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
        template = Template.objects.get(id=response_create.data['id'])
        task_template_1 = template.tasks.get(number=1)
        task_template_3 = template.tasks.get(number=3)

        response_run = api_client.post(
            f'/templates/{template.id}/run',
            data={'name': 'Workflow'}
        )
        workflow = Workflow.objects.get(id=response_run.data['workflow_id'])
        task_1 = workflow.current_task_instance
        response_complete = api_client.post(
            f'/workflows/{workflow.id}/task-complete',
            data={
                'task_id': task_1.id,
            }
        )

        response_update = api_client.put(
            path=f'/templates/{template.id}',
            data={
                'id': template.id,
                'is_active': True,
                'is_public': template.is_public,
                'description': template.description,
                'name': template.name,
                'template_owners': [user.id],
                'finalizable': True,
                'kickoff': {
                    'id': template.kickoff_instance.id
                },
                'tasks': [
                    {
                        'id': task_template_1.id,
                        'api_name': task_template_1.api_name,
                        'number': 1,
                        'name': task_template_1.name,
                        'raw_performers': [
                            {
                                'type': PerformerType.USER,
                                'source_id': user.id
                            }
                        ]
                    },
                    {
                        'id': task_template_3.id,
                        'api_name': task_template_3.api_name,
                        'number': 2,
                        'name': task_template_3.name,
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

        template.refresh_from_db()
        workflow.refresh_from_db()

        template = TemplateVersioningService(
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
            data=template.data,
            version=template.version
        )

        # assert
        assert response_create.status_code == 200
        assert response_run.status_code == 200
        assert response_complete.status_code == 204
        assert response_update.status_code == 200
        workflow.refresh_from_db()
        assert workflow.current_task == 2
        assert workflow.status == WorkflowStatus.RUNNING
        task_3 = workflow.current_task_instance
        assert task_3.number == 2
        assert task_3.date_started is not None
        assert task_3.date_first_started is not None
        assert task_3.date_completed is None
        assert task_3.is_skipped is False
        assert task_3.taskperformer_set.count() == 1
        task_performer = task_3.taskperformer_set.first()
        assert task_performer.is_completed is False
        assert task_performer.date_completed is None
        assert task_performer.user == user
        assert WorkflowEvent.objects.get(
            account=user.account,
            workflow=workflow,
            type=WorkflowEventType.TASK_START,
            task_json__number=2,
            task_json__id=task_3.id
        )
