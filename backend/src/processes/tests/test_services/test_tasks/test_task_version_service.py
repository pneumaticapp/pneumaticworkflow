from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from src.authentication.enums import AuthTokenType
from src.processes.enums import (
    DirectlyStatus,
    DueDateRule,
    FieldType,
    PerformerType,
    PredicateOperator,
    TaskStatus,
    WorkflowStatus,
)
from src.processes.models.workflows.raw_due_date import RawDueDate
from src.processes.models.workflows.task import (
    Delay,
    TaskPerformer,
)
from src.processes.services.tasks.task_version import (
    TaskUpdateVersionService,
)
from src.processes.services.versioning.schemas import (
    TaskSchemaV1,
)
from src.processes.services.workflow_action import (
    WorkflowActionService,
)
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_admin,
    create_test_group,
    create_test_not_admin,
    create_test_owner,
    create_test_template,
    create_test_workflow,
)

UserModel = get_user_model()
pytestmark = pytest.mark.django_db


class TestTaskUpdateVersionService:

    def test_create_or_update_instance__update_all_fields__ok(self, mocker):

        # arrange
        name = 'One of task {{ some-api_name }}'
        api_name = 'task-1'
        revert_task = 'task-0'
        description = 'Some \n {{ another-api_name }} description'

        user = create_test_owner()
        template = create_test_template(user=user, tasks_count=1)
        workflow = create_test_workflow(
            user=user,
            template=template,
            is_urgent=True,
        )
        clear_description = 'Some \n clear description'
        clear_mock = mocker.patch(
            'src.services.markdown.MarkdownService.clear',
            return_value=clear_description,
        )
        template_task = template.tasks.get(number=1)
        template_task.api_name = api_name
        template_task.name = name
        template_task.revert_task = revert_task
        template_task.name_template = name
        template_task.description = description
        template_task.description_template = description
        template_task.require_completion_by_all = True
        template_task.save()
        task_data = TaskSchemaV1(instance=template_task).data

        task = workflow.tasks.get(number=1)

        service = TaskUpdateVersionService(
            user=user,
            instance=task,
            auth_type=AuthTokenType.USER,
            is_superuser=False,
        )

        # act
        task = service._create_or_update_instance(
            data=task_data,
            workflow=workflow,
            fields_values={},
        )

        # assert
        assert task.api_name == api_name
        assert task.account == user.account
        assert task.workflow == workflow
        assert task.name == name
        assert task.revert_task == revert_task
        assert task.name_template == name
        assert task.description == description
        assert task.clear_description == clear_description
        assert task.description_template == description
        assert task.number == 1
        assert task.require_completion_by_all is True
        assert task.is_urgent is True
        clear_mock.assert_called_once_with(description)

    def test_create_or_update_instance__remove_revert_task__ok(self):

        # arrange
        user = create_test_owner()
        template = create_test_template(user=user, tasks_count=1)
        template_task = template.tasks.get(number=1)
        task_data = TaskSchemaV1(instance=template_task).data
        workflow = create_test_workflow(
            user=user,
            template=template,
        )
        task = workflow.tasks.get(number=1)
        service = TaskUpdateVersionService(
            user=user,
            instance=task,
            auth_type=AuthTokenType.USER,
            is_superuser=False,
        )

        # act
        task = service._create_or_update_instance(
            data=task_data,
            workflow=workflow,
            fields_values={},
        )

        # assert
        assert task.revert_task is None

    def test_update_from_version__only_required_fields__ok(self, mocker):

        # arrange
        user = create_test_owner()
        workflow = create_test_workflow(user, tasks_count=1)
        task = workflow.tasks.get(number=1)
        service = TaskUpdateVersionService(
            user=user,
            instance=task,
            auth_type=AuthTokenType.USER,
            is_superuser=False,
        )
        version = 1
        data = {
            'id': 27,
            'api_name': 'task-r5btf7',
            'name': 'Task №1',
            'description': None,
            'number': 1,
            'require_completion_by_all': False,
            'raw_performers': [
                {
                    'id': 55,
                    'type': 'user',
                    'user_id': 27,
                    'api_name': 'raw-performer-1',
                },
            ],
        }

        fields_values = {'key': 'value'}
        fields_values_mock = mocker.patch(
            'src.processes.models.workflows.workflow.Workflow.'
            'get_fields_markdown_values',
            return_value=fields_values,
        )
        create_or_update_instance_mock = mocker.patch(
            'src.processes.services.tasks.task_version.'
            'TaskUpdateVersionService._create_or_update_instance',
        )
        update_fields_mock = mocker.patch(
            'src.processes.services.tasks.task_version.'
            'TaskUpdateVersionService._update_fields',
        )
        update_conditions_mock = mocker.patch(
            'src.processes.services.tasks.task_version.'
            'TaskUpdateVersionService._update_conditions',
        )
        update_checklists_mock = mocker.patch(
            'src.processes.services.tasks.task_version.'
            'TaskUpdateVersionService._update_checklists',
        )
        update_raw_due_date_mock = mocker.patch(
            'src.processes.services.tasks.task_version.'
            'TaskUpdateVersionService._update_raw_due_date',
        )
        set_due_date_from_template = mocker.patch(
            'src.processes.services.tasks.task.'
            'TaskService.set_due_date_from_template',
        )
        update_performers_mock = mocker.patch(
            'src.processes.services.tasks.task_version.'
            'TaskUpdateVersionService._update_performers',
        )
        update_delay_mock = mocker.patch(
            'src.processes.services.tasks.task_version.'
            'TaskUpdateVersionService._update_delay',
        )

        # act
        service.update_from_version(
            data=data,
            version=1,
            workflow=workflow,
        )

        # assert
        fields_values_mock.assert_called_once_with(
            tasks_filter_kwargs={'task__status': TaskStatus.COMPLETED},
        )
        create_or_update_instance_mock.assert_called_once_with(
            data=data,
            workflow=workflow,
            fields_values=fields_values,
        )
        update_fields_mock.assert_called_once_with(data=None)
        update_conditions_mock.assert_called_once_with(data=None)
        update_checklists_mock.assert_called_once_with(
            data=None,
            version=version,
            fields_values=fields_values,
        )
        update_raw_due_date_mock.assert_called_once_with(data=None)
        set_due_date_from_template.assert_called_once()
        task.refresh_from_db()
        assert task.due_date is None

        update_performers_mock.assert_called_once_with(data)
        update_performers_mock.assert_called_once()
        update_delay_mock.assert_called_once_with(new_duration=None)

    def test_update_from_version__all_fields__active_task__ok(self, mocker):

        # arrange
        user = create_test_owner()
        workflow = create_test_workflow(user, tasks_count=1)
        task = workflow.tasks.get(number=1)
        service = TaskUpdateVersionService(
            user=user,
            instance=task,
            auth_type=AuthTokenType.USER,
            is_superuser=False,
        )
        version = 1
        data = {
            'id': 27,
            'api_name': 'task-r5btf7',
            'name': 'Task №1',
            'description': '*Some text*',
            'clear_description': 'Some text',
            'number': 1,
            'require_completion_by_all': False,
            'fields': [
                {
                    'order': 1,
                    'name': 'First step performer',
                    'type': FieldType.USER,
                    'api_name': 'user-field-1',
                    'is_required': True,
                },
            ],
            'delay': '1 00:00:00',
            'conditions': [
                {
                    'order': 1,
                    'api_name': 'condition-1',
                    'action': 'skip_task',
                    'rules': [
                        {
                            'api_name': 'rule-1',
                            'predicates': [
                                {
                                    'operator': PredicateOperator.EQUAL,
                                    'field': 'client-name-1',
                                    'field_type': FieldType.TEXT,
                                    'value': 'Captain Marvel',
                                },
                            ],
                        },
                    ],
                },
            ],
            'raw_performers': [
                {
                    'id': 55,
                    'type': 'user',
                    'user_id': 27,
                    'api_name': None,
                },
            ],
            'raw_due_date': {
                'api_name': 'raw-due-date-bwybf0',
                'rule': 'after task started',
                'duration_months': 3,
                'duration': '1 00:00:00',
                'source_id': 'task-r5btf7',
            },
            'checklists': [
                {
                    'api_name': 'checklist-1',
                    'selections': [
                        {
                            'api_name': 'cl-selection-1',
                            'value': 'some value 1',
                        },
                    ],
                },
            ],
        }

        fields_values = {'key': 'value'}
        fields_values_mock = mocker.patch(
            'src.processes.models.workflows.workflow.Workflow.'
            'get_fields_markdown_values',
            return_value=fields_values,
        )
        create_or_update_instance_mock = mocker.patch(
            'src.processes.services.tasks.task_version.'
            'TaskUpdateVersionService._create_or_update_instance',
        )
        update_fields_mock = mocker.patch(
            'src.processes.services.tasks.task_version.'
            'TaskUpdateVersionService._update_fields',
        )
        update_conditions_mock = mocker.patch(
            'src.processes.services.tasks.task_version.'
            'TaskUpdateVersionService._update_conditions',
        )
        update_checklists_mock = mocker.patch(
            'src.processes.services.tasks.task_version.'
            'TaskUpdateVersionService._update_checklists',
        )
        update_raw_due_date_mock = mocker.patch(
            'src.processes.services.tasks.task_version.'
            'TaskUpdateVersionService._update_raw_due_date',
        )
        set_due_date_from_template = mocker.patch(
            'src.processes.services.tasks.task.'
            'TaskService.set_due_date_from_template',
        )
        update_performers_mock = mocker.patch(
            'src.processes.services.tasks.task_version.'
            'TaskUpdateVersionService._update_performers',
        )
        update_delay_mock = mocker.patch(
            'src.processes.services.tasks.task_version.'
            'TaskUpdateVersionService._update_delay',
        )

        # act
        service.update_from_version(
            data=data,
            version=1,
            workflow=workflow,
        )

        # assert
        fields_values_mock.assert_called_once_with(
            tasks_filter_kwargs={'task__status': TaskStatus.COMPLETED},
        )
        create_or_update_instance_mock.assert_called_once_with(
            data=data,
            workflow=workflow,
            fields_values=fields_values,
        )
        update_fields_mock.assert_called_once_with(
            data=data['fields'],
        )
        update_conditions_mock.assert_called_once_with(
            data=data['conditions'],
        )
        update_checklists_mock.assert_called_once_with(
            data=data['checklists'],
            version=version,
            fields_values=fields_values,
        )
        update_raw_due_date_mock.assert_called_once_with(
            data=data['raw_due_date'],
        )
        set_due_date_from_template.assert_called_once()
        update_performers_mock.assert_called_once_with(data)
        update_performers_mock.assert_called_once()
        update_delay_mock.assert_called_once_with(new_duration=data['delay'])

    def test_update_from_version__future_task__ok(self, mocker):

        # arrange
        user = create_test_owner()
        workflow = create_test_workflow(user, tasks_count=2)
        task = workflow.tasks.get(number=2)
        service = TaskUpdateVersionService(
            user=user,
            instance=task,
            auth_type=AuthTokenType.USER,
            is_superuser=False,
        )
        data = {
            'id': 27,
            'api_name': 'task-r5btf7',
            'name': 'Task №1',
            'description': None,
            'number': 1,
            'require_completion_by_all': False,
            'raw_performers': [
                {
                    'id': 55,
                    'type': 'user',
                    'user_id': 27,
                    'api_name': 'raw-performer-1',
                },
            ],
            'raw_due_date': {
                'api_name': 'raw-due-date-bwybf0',
                'rule': 'after task started',
                'duration': '1 00:00:00',
                'source_id': 'task-r5btf7',
            },
        }

        mocker.patch(
            'src.processes.services.tasks.task_version.'
            'TaskUpdateVersionService._create_or_update_instance',
        )
        mocker.patch(
            'src.processes.services.tasks.task_version.'
            'TaskUpdateVersionService._update_fields',
        )
        mocker.patch(
            'src.processes.services.tasks.task_version.'
            'TaskUpdateVersionService._update_conditions',
        )
        mocker.patch(
            'src.processes.services.tasks.task_version.'
            'TaskUpdateVersionService._update_checklists',
        )
        update_raw_due_date_mock = mocker.patch(
            'src.processes.services.tasks.task_version.'
            'TaskUpdateVersionService._update_raw_due_date',
        )
        set_due_date_from_template = mocker.patch(
            'src.processes.services.tasks.task.'
            'TaskService.set_due_date_from_template',
        )
        update_raw_performers_mock = mocker.patch(
            'src.processes.models.workflows.task.Task.'
            'update_raw_performers_from_task_template',
        )
        update_performers_mock = mocker.patch(
            'src.processes.models.workflows.task.Task.'
            'update_performers',
        )
        raw_performer = mocker.Mock()
        add_raw_performer_mock = mocker.patch(
            'src.processes.models.workflows.task.Task.'
            'add_raw_performer',
            return_value=raw_performer,
        )
        mocker.patch(
            'src.processes.services.tasks.task_version.'
            'TaskUpdateVersionService._update_delay',
        )

        # act
        service.update_from_version(
            data=data,
            version=1,
            workflow=workflow,
        )

        # assert
        update_raw_performers_mock.assert_called_once_with(data)
        update_performers_mock.assert_not_called()
        update_raw_due_date_mock.assert_called_once_with(
            data=data['raw_due_date'],
        )
        set_due_date_from_template.assert_not_called()
        add_raw_performer_mock.assert_not_called()

    def test_update_from_version__completed_task__with_performer__ok(
        self,
        mocker,
    ):

        # arrange
        user = create_test_owner()
        workflow = create_test_workflow(
            user=user,
            tasks_count=2,
            active_task_number=2,
        )
        task = workflow.tasks.get(number=1)
        service = TaskUpdateVersionService(
            user=user,
            instance=task,
            auth_type=AuthTokenType.USER,
            is_superuser=False,
        )
        data = {
            'id': 27,
            'api_name': 'task-r5btf7',
            'name': 'Task №1',
            'description': None,
            'number': 1,
            'require_completion_by_all': False,
            'raw_performers': [
                {
                    'id': 55,
                    'type': 'user',
                    'user_id': 27,
                    'api_name': 'raw-performer-1',
                },
            ],
            'raw_due_date': {
                'api_name': 'raw-due-date-bwybf0',
                'rule': 'after task started',
                'duration': '1 00:00:00',
                'source_id': 'task-r5btf7',
            },
            'parents': [],
        }

        mocker.patch(
            'src.processes.services.tasks.task_version.'
            'TaskUpdateVersionService._create_or_update_instance',
        )
        mocker.patch(
            'src.processes.services.tasks.task_version.'
            'TaskUpdateVersionService._update_fields',
        )
        mocker.patch(
            'src.processes.services.tasks.task_version.'
            'TaskUpdateVersionService._update_conditions',
        )
        mocker.patch(
            'src.processes.services.tasks.task_version.'
            'TaskUpdateVersionService._update_checklists',
        )
        update_raw_due_date_mock = mocker.patch(
            'src.processes.services.tasks.task_version.'
            'TaskUpdateVersionService._update_raw_due_date',
        )
        set_due_date_from_template = mocker.patch(
            'src.processes.services.tasks.task.'
            'TaskService.set_due_date_from_template',
        )
        update_raw_performers_mock = mocker.patch(
            'src.processes.models.workflows.task.Task.'
            'update_raw_performers_from_task_template',
        )
        update_performers_mock = mocker.patch(
            'src.processes.models.workflows.task.Task.'
            'update_performers',
        )
        raw_performer = mocker.Mock()
        add_raw_performer_mock = mocker.patch(
            'src.processes.models.workflows.task.Task.'
            'add_raw_performer',
            return_value=raw_performer,
        )
        mocker.patch(
            'src.processes.services.tasks.task_version.'
            'TaskUpdateVersionService._update_delay',
        )

        # act
        service.update_from_version(
            data=data,
            version=1,
            workflow=workflow,
        )

        # assert
        update_raw_performers_mock.assert_not_called()
        update_performers_mock.assert_not_called()
        update_raw_due_date_mock.assert_not_called()
        set_due_date_from_template.assert_not_called()
        add_raw_performer_mock.assert_not_called()

    def test_update_from_version__completed_task__not_performer__set_default(
        self,
        mocker,
    ):

        # arrange
        user = create_test_owner()
        workflow = create_test_workflow(
            user,
            tasks_count=2,
            active_task_number=2,
        )
        task = workflow.tasks.get(number=1)
        task.raw_performers.all().delete()
        task.performers.all().delete()
        service = TaskUpdateVersionService(
            user=user,
            instance=task,
            auth_type=AuthTokenType.USER,
            is_superuser=False,
        )
        data = {
            'id': 27,
            'api_name': 'task-r5btf7',
            'name': 'Task №1',
            'description': None,
            'number': 1,
            'require_completion_by_all': False,
            'raw_performers': [
                {
                    'id': 55,
                    'type': 'user',
                    'user_id': 27,
                    'api_name': 'raw-performer-1',
                },
            ],
            'raw_due_date': {
                'api_name': 'raw-due-date-bwybf0',
                'rule': 'after task started',
                'duration': '1 00:00:00',
                'source_id': 'task-r5btf7',
            },
            'parents': [],
        }

        mocker.patch(
            'src.processes.services.tasks.task_version.'
            'TaskUpdateVersionService._create_or_update_instance',
        )
        mocker.patch(
            'src.processes.services.tasks.task_version.'
            'TaskUpdateVersionService._update_fields',
        )
        mocker.patch(
            'src.processes.services.tasks.task_version.'
            'TaskUpdateVersionService._update_conditions',
        )
        mocker.patch(
            'src.processes.services.tasks.task_version.'
            'TaskUpdateVersionService._update_checklists',
        )
        update_raw_due_date_mock = mocker.patch(
            'src.processes.services.tasks.task_version.'
            'TaskUpdateVersionService._update_raw_due_date',
        )
        set_due_date_from_template = mocker.patch(
            'src.processes.services.tasks.task.'
            'TaskService.set_due_date_from_template',
        )
        update_raw_performers_mock = mocker.patch(
            'src.processes.models.workflows.task.Task.'
            'update_raw_performers_from_task_template',
        )

        raw_performer = mocker.Mock()
        add_raw_performer_mock = mocker.patch(
            'src.processes.models.workflows.task.Task.'
            'add_raw_performer',
            return_value=raw_performer,
        )
        mocker.patch(
            'src.processes.services.tasks.task_version.'
            'TaskUpdateVersionService._update_delay',
        )

        # act
        service.update_from_version(
            data=data,
            version=1,
            workflow=workflow,
        )

        # assert
        update_raw_performers_mock.assert_not_called()
        update_raw_due_date_mock.assert_not_called()
        set_due_date_from_template.assert_not_called()
        add_raw_performer_mock.assert_not_called()

    def test_update_delay__new_duration_and_active_delay__update(
        self,
    ):

        # arrange
        user = create_test_owner()
        workflow = create_test_workflow(user=user, tasks_count=1)
        task = workflow.tasks.get(number=1)
        delay = Delay.objects.create(
            task=task,
            start_date=timezone.now(),
            duration=timedelta(days=1),
            workflow=workflow,
        )
        service = TaskUpdateVersionService(
            user=user,
            instance=task,
            auth_type=AuthTokenType.USER,
            is_superuser=False,
        )
        new_duration_str = '14 00:00:00'
        new_duration = timedelta(days=14)

        # act
        service._update_delay(new_duration=new_duration_str)

        # assert
        delay.refresh_from_db()
        assert delay.directly_status == DirectlyStatus.NO_STATUS
        assert delay.duration == new_duration

    def test_update_delay__new_duration_and_force_delay__not_update(
        self,
    ):

        # arrange
        user = create_test_owner()
        workflow = create_test_workflow(user=user, tasks_count=1)
        task = workflow.tasks.get(number=1)
        old_duration = timedelta(days=1)
        delay = Delay.objects.create(
            task=task,
            start_date=timezone.now(),
            duration=old_duration,
            directly_status=DirectlyStatus.CREATED,
            workflow=workflow,
        )
        service = TaskUpdateVersionService(
            user=user,
            instance=task,
            auth_type=AuthTokenType.USER,
            is_superuser=False,
        )
        new_duration_str = '14 00:00:00'

        # act
        service._update_delay(new_duration=new_duration_str)

        # assert
        delay.refresh_from_db()
        assert delay.duration == old_duration

    def test_update_delay__new_duration_and_not_delay__create(
        self,
    ):

        # arrange
        user = create_test_owner()
        workflow = create_test_workflow(user=user, tasks_count=1)
        task = workflow.tasks.get(number=1)
        service = TaskUpdateVersionService(
            user=user,
            instance=task,
            auth_type=AuthTokenType.USER,
            is_superuser=False,
        )
        new_duration_str = '14 00:00:00'
        new_duration = timedelta(days=14)

        # act
        service._update_delay(new_duration=new_duration_str)

        # assert
        assert Delay.objects.filter(
            task=task,
            directly_status=DirectlyStatus.NO_STATUS,
            duration=new_duration,
            start_date=None,
            end_date=None,

        ).exists()

    def test_update_delay__not_duration_and_not_delay__not_update(
        self,
    ):
        # arrange
        user = create_test_owner()
        workflow = create_test_workflow(user=user, tasks_count=1)
        task = workflow.tasks.get(number=1)
        service = TaskUpdateVersionService(
            user=user,
            instance=task,
            auth_type=AuthTokenType.USER,
            is_superuser=False,
        )

        # act
        service._update_delay()

        # assert
        assert not Delay.objects.filter(task=task).exists()

    def test_update_delay__not_duration_and_force_delay__not_update(
        self,
        mocker,
    ):

        # arrange
        user = create_test_owner()
        workflow = create_test_workflow(user=user, tasks_count=1)
        workflow.status = WorkflowStatus.DELAYED
        workflow.save(update_fields=['status'])
        task = workflow.tasks.get(number=1)
        old_duration = timedelta(days=1)
        delay = Delay.objects.create(
            task=task,
            start_date=timezone.now(),
            duration=old_duration,
            directly_status=DirectlyStatus.CREATED,
            workflow=workflow,
        )
        service = TaskUpdateVersionService(
            user=user,
            instance=task,
            sync=False,
            auth_type=AuthTokenType.USER,
            is_superuser=False,
        )
        resume_workflow_init_mock = mocker.patch.object(
            WorkflowActionService,
            attribute='__init__',
            return_value=None,
        )
        resume_task_mock = mocker.patch(
            'src.processes.services.'
            'workflow_action.WorkflowActionService.resume_task',
        )

        # act
        service._update_delay()

        # assert
        workflow.refresh_from_db()
        delay.refresh_from_db()
        assert delay.duration == old_duration
        assert delay.end_date is None
        assert workflow.status == WorkflowStatus.DELAYED
        resume_workflow_init_mock.assert_not_called()
        resume_task_mock.assert_not_called()

    def test_update_delay__not_duration_and_active_task_delay__end_delay(
        self,
    ):

        # arrange
        user = create_test_owner()
        workflow = create_test_workflow(user=user, tasks_count=1)
        workflow.status = WorkflowStatus.DELAYED
        workflow.save(update_fields=['status'])
        task = workflow.tasks.get(number=1)
        delay = Delay.objects.create(
            task=task,
            start_date=timezone.now(),
            duration=timedelta(days=1),
            workflow=workflow,
        )
        sync = True
        service = TaskUpdateVersionService(
            user=user,
            instance=task,
            sync=sync,
            auth_type=AuthTokenType.USER,
            is_superuser=False,
        )

        # act
        service._update_delay()

        # assert
        delay.refresh_from_db()
        assert delay.end_date

    def test_update_delay__not_duration_and_future_task_delay__delete_delay(
        self,
    ):

        # arrange
        user = create_test_owner()
        workflow = create_test_workflow(user=user, tasks_count=2)
        workflow.status = WorkflowStatus.DELAYED
        workflow.save(update_fields=['status'])
        task_2 = workflow.tasks.get(number=2)
        delay = Delay.objects.create(
            task=task_2,
            start_date=timezone.now(),
            duration=timedelta(days=1),
            workflow=workflow,
        )
        service = TaskUpdateVersionService(
            user=user,
            instance=task_2,
            auth_type=AuthTokenType.USER,
            is_superuser=False,
        )

        # act
        service._update_delay()

        # assert
        assert not Delay.objects.filter(id=delay.id).exists()

    def test_update_raw_due_date__not_version_data__delete_previous(self):

        # arrange
        user = create_test_owner()
        workflow = create_test_workflow(user, tasks_count=1)
        task = workflow.tasks.get(number=1)
        raw_due_date = RawDueDate.objects.create(
            rule=DueDateRule.AFTER_WORKFLOW_STARTED,
            duration=timedelta(hours=1),
            task=task,
        )
        service = TaskUpdateVersionService(
            user=user,
            instance=task,
            auth_type=AuthTokenType.USER,
            is_superuser=False,
        )

        # act
        service._update_raw_due_date(data=None)

        # assert
        assert not RawDueDate.objects.filter(id=raw_due_date.id).exists()

    def test_update_raw_due_date__create_new__ok(self):

        # arrange
        user = create_test_owner()
        workflow = create_test_workflow(user, tasks_count=1)
        task = workflow.tasks.get(number=1)
        data = {
            'rule': DueDateRule.AFTER_TASK_STARTED,
            'api_name': 'raw-due-date-1',
            'duration': '01:00:00',
            'source_id': task.api_name,
        }
        service = TaskUpdateVersionService(
            user=user,
            instance=task,
            auth_type=AuthTokenType.USER,
            is_superuser=False,
        )

        # act
        service._update_raw_due_date(data=data)

        # assert
        assert RawDueDate.objects.get(
            task=task,
            rule=data['rule'],
            api_name=data['api_name'],
            duration=timedelta(hours=1),
            source_id=data['source_id'],
        )

    def test_update_raw_due_date__update_existent__ok(self):

        # arrange
        user = create_test_owner()
        workflow = create_test_workflow(user, tasks_count=1)
        task = workflow.tasks.get(number=1)
        raw_due_date = RawDueDate.objects.create(
            rule=DueDateRule.AFTER_WORKFLOW_STARTED,
            duration=timedelta(hours=1),
            task=task,
            api_name='raw-due-date-1',
        )
        data = {
            'rule': DueDateRule.AFTER_TASK_STARTED,
            'api_name': 'raw-due-date-2',
            'duration': '02:00:00',
            'source_id': task.api_name,
        }
        service = TaskUpdateVersionService(
            user=user,
            instance=task,
            auth_type=AuthTokenType.USER,
            is_superuser=False,
        )

        # act
        service._update_raw_due_date(data=data)

        # assert
        raw_due_date.refresh_from_db()
        assert raw_due_date.rule == data['rule']
        assert raw_due_date.api_name == data['api_name']
        assert raw_due_date.duration == timedelta(hours=2)
        assert raw_due_date.source_id == data['source_id']
        assert raw_due_date.task_id == task.id

    def test_update_performers__add_new_user_performers__ok(self, mocker):

        # arrange
        account = create_test_account()
        owner = create_test_owner(account=account)
        workflow = create_test_workflow(owner, tasks_count=1)
        task = workflow.tasks.get(number=1)
        performer = create_test_not_admin(account=account)
        update_raw_performers_from_task_template_mock = mocker.patch(
            'src.processes.models.workflows.task.Task.'
            'update_raw_performers_from_task_template',
        )
        created_user_ids = [performer.id]
        created_group_ids = []
        deleted_user_ids = []
        deleted_group_ids = []
        update_performers_mock = mocker.patch(
            'src.processes.models.workflows.task.Task.'
            'update_performers',
            return_value=(
                created_user_ids,
                created_group_ids,
                deleted_user_ids,
                deleted_group_ids,
            ),
        )
        add_raw_performer_mock = mocker.patch(
            'src.processes.models.workflows.task.Task.'
            'add_raw_performer',
        )
        send_new_task_notification_mock = mocker.patch(
            'src.processes.services.tasks.task_version.'
            'send_new_task_notification.delay',
        )
        send_task_deleted_notification_mock = mocker.patch(
            'src.processes.services.tasks.task_version.'
            'send_task_deleted_notification.delay',
        )
        service = TaskUpdateVersionService(
            user=owner,
            instance=task,
            auth_type=AuthTokenType.USER,
            is_superuser=False,
        )
        data_mock = mocker.Mock()
        task_data_mock = mocker.Mock()
        get_data_for_list_mock = mocker.patch(
            'src.processes.models.workflows.task.Task.'
            'get_data_for_list',
            return_value=task_data_mock,
        )

        # act
        service._update_performers(data_mock)

        # assert
        update_raw_performers_from_task_template_mock.assert_called_once_with(
            data_mock,
        )
        update_performers_mock.assert_called_once()
        add_raw_performer_mock.assert_not_called()
        get_data_for_list_mock.assert_called_once()
        send_new_task_notification_mock.assert_called_once_with(
            logging=account.log_api_requests,
            account_id=account.id,
            recipients=[(
                performer.id,
                performer.email,
                performer.is_new_tasks_subscriber,
            )],
            task_id=task.id,
            task_name=task.name,
            task_data=task_data_mock,
            task_description=task.description,
            workflow_name=workflow.name,
            template_name=workflow.get_template_name(),
            workflow_starter_name=owner.name,
            workflow_starter_photo=owner.photo,
            due_date_timestamp=None,
            logo_lg=account.logo_lg,
            is_returned=False,
        )
        send_task_deleted_notification_mock.assert_not_called()

    def test_update_performers__add_new_group_performers__ok(self, mocker):

        # arrange
        account = create_test_account()
        owner = create_test_owner(account=account)
        workflow = create_test_workflow(owner, tasks_count=1)
        task = workflow.tasks.get(number=1)
        performer = create_test_not_admin(account=account)
        group = create_test_group(account=account, users=[performer])
        update_raw_performers_from_task_template_mock = mocker.patch(
            'src.processes.models.workflows.task.Task.'
            'update_raw_performers_from_task_template',
        )
        created_user_ids = []
        created_group_ids = [group.id]
        deleted_user_ids = []
        deleted_group_ids = []
        update_performers_mock = mocker.patch(
            'src.processes.models.workflows.task.Task.'
            'update_performers',
            return_value=(
                created_user_ids,
                created_group_ids,
                deleted_user_ids,
                deleted_group_ids,
            ),
        )
        add_raw_performer_mock = mocker.patch(
            'src.processes.models.workflows.task.Task.'
            'add_raw_performer',
        )
        send_new_task_notification_mock = mocker.patch(
            'src.processes.services.tasks.task_version.'
            'send_new_task_notification.delay',
        )
        send_task_deleted_notification_mock = mocker.patch(
            'src.processes.services.tasks.task_version.'
            'send_task_deleted_notification.delay',
        )
        service = TaskUpdateVersionService(
            user=owner,
            instance=task,
            auth_type=AuthTokenType.USER,
            is_superuser=False,
        )
        data_mock = mocker.Mock()
        task_data_mock = mocker.Mock()
        get_data_for_list_mock = mocker.patch(
            'src.processes.models.workflows.task.Task.'
            'get_data_for_list',
            return_value=task_data_mock,
        )

        # act
        service._update_performers(data_mock)

        # assert
        update_raw_performers_from_task_template_mock.assert_called_once_with(
            data_mock,
        )
        update_performers_mock.assert_called_once()
        add_raw_performer_mock.assert_not_called()
        get_data_for_list_mock.assert_called_once()
        send_new_task_notification_mock.assert_called_once_with(
            logging=account.log_api_requests,
            account_id=account.id,
            recipients=[(
                performer.id,
                performer.email,
                performer.is_new_tasks_subscriber,
            )],
            task_id=task.id,
            task_name=task.name,
            task_data=task_data_mock,
            task_description=task.description,
            workflow_name=workflow.name,
            template_name=workflow.get_template_name(),
            workflow_starter_name=owner.name,
            workflow_starter_photo=owner.photo,
            due_date_timestamp=None,
            logo_lg=account.logo_lg,
            is_returned=False,
        )
        send_task_deleted_notification_mock.assert_not_called()

    def test_update_performers__remove_user_performers__ok(self, mocker):

        # arrange
        account = create_test_account()
        owner = create_test_owner(account=account)
        workflow = create_test_workflow(owner, tasks_count=1)
        task = workflow.tasks.get(number=1)
        performer = create_test_not_admin(account=account)
        update_raw_performers_from_task_template_mock = mocker.patch(
            'src.processes.models.workflows.task.Task.'
            'update_raw_performers_from_task_template',
        )
        created_user_ids = []
        created_group_ids = []
        deleted_user_ids = [performer.id]
        deleted_group_ids = []
        update_performers_mock = mocker.patch(
            'src.processes.models.workflows.task.Task.'
            'update_performers',
            return_value=(
                created_user_ids,
                created_group_ids,
                deleted_user_ids,
                deleted_group_ids,
            ),
        )
        add_raw_performer_mock = mocker.patch(
            'src.processes.models.workflows.task.Task.'
            'add_raw_performer',
        )
        send_new_task_notification_mock = mocker.patch(
            'src.processes.services.tasks.task_version.'
            'send_new_task_notification.delay',
        )
        send_task_deleted_notification_mock = mocker.patch(
            'src.processes.services.tasks.task_version.'
            'send_task_deleted_notification.delay',
        )
        service = TaskUpdateVersionService(
            user=owner,
            instance=task,
            auth_type=AuthTokenType.USER,
            is_superuser=False,
        )
        data_mock = mocker.Mock()
        task_data_mock = mocker.Mock()
        get_data_for_list_mock = mocker.patch(
            'src.processes.models.workflows.task.Task.'
            'get_data_for_list',
            return_value=task_data_mock,
        )

        # act
        service._update_performers(data_mock)

        # assert
        update_raw_performers_from_task_template_mock.assert_called_once_with(
            data_mock,
        )
        update_performers_mock.assert_called_once()
        add_raw_performer_mock.assert_not_called()
        get_data_for_list_mock.assert_called_once()
        send_new_task_notification_mock.assert_not_called()
        send_task_deleted_notification_mock.assert_called_once_with(
            task_id=task.id,
            recipients=[(performer.id, performer.email)],
            account_id=account.id,
            task_data=task_data_mock,
        )

    def test_update_performers__remove_group_performers__ok(self, mocker):

        # arrange
        account = create_test_account()
        owner = create_test_owner(account=account)
        workflow = create_test_workflow(owner, tasks_count=1)
        task = workflow.tasks.get(number=1)
        performer = create_test_not_admin(account=account)
        group = create_test_group(account=account, users=[performer])
        update_raw_performers_from_task_template_mock = mocker.patch(
            'src.processes.models.workflows.task.Task.'
            'update_raw_performers_from_task_template',
        )
        created_user_ids = []
        created_group_ids = []
        deleted_user_ids = []
        deleted_group_ids = [group.id]
        update_performers_mock = mocker.patch(
            'src.processes.models.workflows.task.Task.'
            'update_performers',
            return_value=(
                created_user_ids,
                created_group_ids,
                deleted_user_ids,
                deleted_group_ids,
            ),
        )
        add_raw_performer_mock = mocker.patch(
            'src.processes.models.workflows.task.Task.'
            'add_raw_performer',
        )
        send_new_task_notification_mock = mocker.patch(
            'src.processes.services.tasks.task_version.'
            'send_new_task_notification.delay',
        )
        send_task_deleted_notification_mock = mocker.patch(
            'src.processes.services.tasks.task_version.'
            'send_task_deleted_notification.delay',
        )
        service = TaskUpdateVersionService(
            user=owner,
            instance=task,
            auth_type=AuthTokenType.USER,
            is_superuser=False,
        )
        data_mock = mocker.Mock()
        task_data_mock = mocker.Mock()
        get_data_for_list_mock = mocker.patch(
            'src.processes.models.workflows.task.Task.'
            'get_data_for_list',
            return_value=task_data_mock,
        )

        # act
        service._update_performers(data_mock)

        # assert
        update_raw_performers_from_task_template_mock.assert_called_once_with(
            data_mock,
        )
        update_performers_mock.assert_called_once()
        add_raw_performer_mock.assert_not_called()
        get_data_for_list_mock.assert_called_once()
        send_new_task_notification_mock.assert_not_called()
        send_task_deleted_notification_mock.assert_called_once_with(
            task_id=task.id,
            recipients=[(performer.id, performer.email)],
            account_id=account.id,
            task_data=task_data_mock,
        )

    def test_update_performers__set_default_performer_account_owner__ok(
        self,
        mocker,
    ):

        # arrange
        account = create_test_account()
        owner = create_test_owner(account=account)
        user = create_test_admin(account=account)
        workflow = create_test_workflow(user, tasks_count=1, is_external=True)
        task = workflow.tasks.get(number=1)
        task.performers.all().delete()
        update_raw_performers_from_task_template_mock = mocker.patch(
            'src.processes.models.workflows.task.Task.'
            'update_raw_performers_from_task_template',
        )
        created_user_ids = []
        created_group_ids = []
        deleted_user_ids = []
        deleted_group_ids = []
        update_performers_mock = mocker.patch(
            'src.processes.models.workflows.task.Task.'
            'update_performers',
            return_value=(
                created_user_ids,
                created_group_ids,
                deleted_user_ids,
                deleted_group_ids,
            ),
        )
        add_raw_performer_mock = mocker.patch(
            'src.processes.models.workflows.task.Task.'
            'add_raw_performer',
        )
        send_new_task_notification_mock = mocker.patch(
            'src.processes.services.tasks.task_version.'
            'send_new_task_notification.delay',
        )
        send_task_deleted_notification_mock = mocker.patch(
            'src.processes.services.tasks.task_version.'
            'send_task_deleted_notification.delay',
        )
        service = TaskUpdateVersionService(
            user=owner,
            instance=task,
            auth_type=AuthTokenType.USER,
            is_superuser=False,
        )
        data_mock = mocker.Mock()
        task_data_mock = mocker.Mock()
        get_data_for_list_mock = mocker.patch(
            'src.processes.models.workflows.task.Task.'
            'get_data_for_list',
            return_value=task_data_mock,
        )

        # act
        service._update_performers(data_mock)

        # assert
        update_raw_performers_from_task_template_mock.assert_called_once_with(
            data_mock,
        )
        update_performers_mock.assert_called_once()
        add_raw_performer_mock.assert_called_once_with(owner)
        task.refresh_from_db()
        assert task.performers.count() == 1
        assert task.performers.get(id=owner.id)
        get_data_for_list_mock.assert_called_once()
        send_new_task_notification_mock.assert_called_once_with(
            logging=account.log_api_requests,
            account_id=account.id,
            recipients=[(
                owner.id,
                owner.email,
                owner.is_new_tasks_subscriber,
            )],
            task_id=task.id,
            task_name=task.name,
            task_data=task_data_mock,
            task_description=task.description,
            workflow_name=workflow.name,
            template_name=workflow.get_template_name(),
            workflow_starter_name=None,
            workflow_starter_photo=None,
            due_date_timestamp=None,
            logo_lg=account.logo_lg,
            is_returned=False,
        )
        send_task_deleted_notification_mock.assert_not_called()

    def test_update_performers__set_default_performer__workflow_starter__ok(
        self,
        mocker,
    ):

        # arrange
        account = create_test_account()
        create_test_owner(account=account)
        workflow_starter = create_test_not_admin(account=account)
        user = create_test_admin(account=account)
        workflow = create_test_workflow(workflow_starter, tasks_count=1)
        task = workflow.tasks.get(number=1)
        task.performers.all().delete()
        update_raw_performers_from_task_template_mock = mocker.patch(
            'src.processes.models.workflows.task.Task.'
            'update_raw_performers_from_task_template',
        )
        created_user_ids = []
        created_group_ids = []
        deleted_user_ids = []
        deleted_group_ids = []
        update_performers_mock = mocker.patch(
            'src.processes.models.workflows.task.Task.'
            'update_performers',
            return_value=(
                created_user_ids,
                created_group_ids,
                deleted_user_ids,
                deleted_group_ids,
            ),
        )
        add_raw_performer_mock = mocker.patch(
            'src.processes.models.workflows.task.Task.'
            'add_raw_performer',
        )
        send_new_task_notification_mock = mocker.patch(
            'src.processes.services.tasks.task_version.'
            'send_new_task_notification.delay',
        )
        send_task_deleted_notification_mock = mocker.patch(
            'src.processes.services.tasks.task_version.'
            'send_task_deleted_notification.delay',
        )
        service = TaskUpdateVersionService(
            user=user,
            instance=task,
            auth_type=AuthTokenType.USER,
            is_superuser=False,
        )
        data_mock = mocker.Mock()
        task_data_mock = mocker.Mock()
        get_data_for_list_mock = mocker.patch(
            'src.processes.models.workflows.task.Task.'
            'get_data_for_list',
            return_value=task_data_mock,
        )

        # act
        service._update_performers(data_mock)

        # assert
        update_raw_performers_from_task_template_mock.assert_called_once_with(
            data_mock,
        )
        update_performers_mock.assert_called_once()
        add_raw_performer_mock.assert_called_once_with(workflow_starter)
        task.refresh_from_db()
        assert task.performers.count() == 1
        assert task.performers.get(id=workflow_starter.id)
        get_data_for_list_mock.assert_called_once()
        send_new_task_notification_mock.assert_called_once_with(
            logging=account.log_api_requests,
            account_id=account.id,
            recipients=[(
                workflow_starter.id,
                workflow_starter.email,
                workflow_starter.is_new_tasks_subscriber,
            )],
            task_id=task.id,
            task_name=task.name,
            task_data=task_data_mock,
            task_description=task.description,
            workflow_name=workflow.name,
            template_name=workflow.get_template_name(),
            workflow_starter_name=workflow_starter.name,
            workflow_starter_photo=workflow_starter.photo,
            due_date_timestamp=None,
            logo_lg=account.logo_lg,
            is_returned=False,
        )
        send_task_deleted_notification_mock.assert_not_called()

    def test_update_performers__new_user_already_performer__not_sent(
        self,
        mocker,
    ):

        # arrange
        account = create_test_account()
        owner = create_test_owner(account=account)
        workflow = create_test_workflow(owner, tasks_count=1)
        performer = create_test_not_admin(account=account)
        task = workflow.tasks.get(number=1)
        task.performers.all().delete()
        task.performers.add(performer)
        group = create_test_group(account=account, users=[performer])
        update_raw_performers_from_task_template_mock = mocker.patch(
            'src.processes.models.workflows.task.Task.'
            'update_raw_performers_from_task_template',
        )
        created_user_ids = []
        created_group_ids = [group.id]
        deleted_user_ids = []
        deleted_group_ids = []
        update_performers_mock = mocker.patch(
            'src.processes.models.workflows.task.Task.'
            'update_performers',
            return_value=(
                created_user_ids,
                created_group_ids,
                deleted_user_ids,
                deleted_group_ids,
            ),
        )
        add_raw_performer_mock = mocker.patch(
            'src.processes.models.workflows.task.Task.'
            'add_raw_performer',
        )
        send_new_task_notification_mock = mocker.patch(
            'src.processes.services.tasks.task_version.'
            'send_new_task_notification.delay',
        )
        send_task_deleted_notification_mock = mocker.patch(
            'src.processes.services.tasks.task_version.'
            'send_task_deleted_notification.delay',
        )
        service = TaskUpdateVersionService(
            user=owner,
            instance=task,
            auth_type=AuthTokenType.USER,
            is_superuser=False,
        )
        data_mock = mocker.Mock()
        task_data_mock = mocker.Mock()
        get_data_for_list_mock = mocker.patch(
            'src.processes.models.workflows.task.Task.'
            'get_data_for_list',
            return_value=task_data_mock,
        )

        # act
        service._update_performers(data_mock)

        # assert
        update_raw_performers_from_task_template_mock.assert_called_once_with(
            data_mock,
        )
        update_performers_mock.assert_called_once()
        add_raw_performer_mock.assert_not_called()
        get_data_for_list_mock.assert_not_called()
        send_new_task_notification_mock.assert_not_called()
        send_task_deleted_notification_mock.assert_not_called()

    def test_update_performers__new_group_user_already_performer__not_sent(
        self,
        mocker,
    ):

        # arrange
        account = create_test_account()
        owner = create_test_owner(account=account)
        workflow = create_test_workflow(owner, tasks_count=1)
        performer = create_test_not_admin(account=account)
        task = workflow.tasks.get(number=1)
        task.performers.all().delete()
        group = create_test_group(account=account, users=[performer])
        TaskPerformer.objects.create(
            task_id=task.id,
            type=PerformerType.GROUP,
            group_id=group.id,
        )
        task.performers.add(performer)
        update_raw_performers_from_task_template_mock = mocker.patch(
            'src.processes.models.workflows.task.Task.'
            'update_raw_performers_from_task_template',
        )
        created_user_ids = [performer.id]
        created_group_ids = []
        deleted_user_ids = []
        deleted_group_ids = []
        update_performers_mock = mocker.patch(
            'src.processes.models.workflows.task.Task.'
            'update_performers',
            return_value=(
                created_user_ids,
                created_group_ids,
                deleted_user_ids,
                deleted_group_ids,
            ),
        )
        add_raw_performer_mock = mocker.patch(
            'src.processes.models.workflows.task.Task.'
            'add_raw_performer',
        )
        send_new_task_notification_mock = mocker.patch(
            'src.processes.services.tasks.task_version.'
            'send_new_task_notification.delay',
        )
        send_task_deleted_notification_mock = mocker.patch(
            'src.processes.services.tasks.task_version.'
            'send_task_deleted_notification.delay',
        )
        service = TaskUpdateVersionService(
            user=owner,
            instance=task,
            auth_type=AuthTokenType.USER,
            is_superuser=False,
        )
        data_mock = mocker.Mock()
        task_data_mock = mocker.Mock()
        get_data_for_list_mock = mocker.patch(
            'src.processes.models.workflows.task.Task.'
            'get_data_for_list',
            return_value=task_data_mock,
        )

        # act
        service._update_performers(data_mock)

        # assert
        update_raw_performers_from_task_template_mock.assert_called_once_with(
            data_mock,
        )
        update_performers_mock.assert_called_once()
        add_raw_performer_mock.assert_not_called()
        get_data_for_list_mock.assert_not_called()
        send_new_task_notification_mock.assert_not_called()
        send_task_deleted_notification_mock.assert_not_called()

    def test_update_performers__removed_user_already_performer__not_sent(
        self,
        mocker,
    ):

        # arrange
        account = create_test_account()
        owner = create_test_owner(account=account)
        workflow = create_test_workflow(owner, tasks_count=1)
        performer = create_test_not_admin(account=account)
        task = workflow.tasks.get(number=1)
        task.performers.all().delete()
        group = create_test_group(account=account, users=[performer])
        TaskPerformer.objects.create(
            task_id=task.id,
            type=PerformerType.GROUP,
            group_id=group.id,
        )
        update_raw_performers_from_task_template_mock = mocker.patch(
            'src.processes.models.workflows.task.Task.'
            'update_raw_performers_from_task_template',
        )
        created_user_ids = []
        created_group_ids = []
        deleted_user_ids = [performer.id]
        deleted_group_ids = []
        update_performers_mock = mocker.patch(
            'src.processes.models.workflows.task.Task.'
            'update_performers',
            return_value=(
                created_user_ids,
                created_group_ids,
                deleted_user_ids,
                deleted_group_ids,
            ),
        )
        add_raw_performer_mock = mocker.patch(
            'src.processes.models.workflows.task.Task.'
            'add_raw_performer',
        )
        send_new_task_notification_mock = mocker.patch(
            'src.processes.services.tasks.task_version.'
            'send_new_task_notification.delay',
        )
        send_task_deleted_notification_mock = mocker.patch(
            'src.processes.services.tasks.task_version.'
            'send_task_deleted_notification.delay',
        )
        service = TaskUpdateVersionService(
            user=owner,
            instance=task,
            auth_type=AuthTokenType.USER,
            is_superuser=False,
        )
        data_mock = mocker.Mock()
        task_data_mock = mocker.Mock()
        get_data_for_list_mock = mocker.patch(
            'src.processes.models.workflows.task.Task.'
            'get_data_for_list',
            return_value=task_data_mock,
        )

        # act
        service._update_performers(data_mock)

        # assert
        update_raw_performers_from_task_template_mock.assert_called_once_with(
            data_mock,
        )
        update_performers_mock.assert_called_once()
        add_raw_performer_mock.assert_not_called()
        get_data_for_list_mock.assert_not_called()
        send_new_task_notification_mock.assert_not_called()
        send_task_deleted_notification_mock.assert_not_called()

    def test_update_performers__removed_group_user_already_performer__not_sent(
        self,
        mocker,
    ):

        # arrange
        account = create_test_account()
        owner = create_test_owner(account=account)
        workflow = create_test_workflow(owner, tasks_count=1)
        performer = create_test_not_admin(account=account)
        task = workflow.tasks.get(number=1)
        task.performers.all().delete()
        task.performers.add(performer)
        group = create_test_group(account=account, users=[performer])
        update_raw_performers_from_task_template_mock = mocker.patch(
            'src.processes.models.workflows.task.Task.'
            'update_raw_performers_from_task_template',
        )
        created_user_ids = []
        created_group_ids = []
        deleted_user_ids = []
        deleted_group_ids = [group.id]
        update_performers_mock = mocker.patch(
            'src.processes.models.workflows.task.Task.'
            'update_performers',
            return_value=(
                created_user_ids,
                created_group_ids,
                deleted_user_ids,
                deleted_group_ids,
            ),
        )
        add_raw_performer_mock = mocker.patch(
            'src.processes.models.workflows.task.Task.'
            'add_raw_performer',
        )
        send_new_task_notification_mock = mocker.patch(
            'src.processes.services.tasks.task_version.'
            'send_new_task_notification.delay',
        )
        send_task_deleted_notification_mock = mocker.patch(
            'src.processes.services.tasks.task_version.'
            'send_task_deleted_notification.delay',
        )
        service = TaskUpdateVersionService(
            user=owner,
            instance=task,
            auth_type=AuthTokenType.USER,
            is_superuser=False,
        )
        data_mock = mocker.Mock()
        task_data_mock = mocker.Mock()
        get_data_for_list_mock = mocker.patch(
            'src.processes.models.workflows.task.Task.'
            'get_data_for_list',
            return_value=task_data_mock,
        )

        # act
        service._update_performers(data_mock)

        # assert
        update_raw_performers_from_task_template_mock.assert_called_once_with(
            data_mock,
        )
        update_performers_mock.assert_called_once()
        add_raw_performer_mock.assert_not_called()
        get_data_for_list_mock.assert_not_called()
        send_new_task_notification_mock.assert_not_called()
        send_task_deleted_notification_mock.assert_not_called()
