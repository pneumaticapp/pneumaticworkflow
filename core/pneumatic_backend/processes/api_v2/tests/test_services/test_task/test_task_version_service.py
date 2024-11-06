import pytest
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth import get_user_model
from pneumatic_backend.processes.tests.fixtures import (
    create_test_user,
    create_test_workflow,
)
from pneumatic_backend.authentication.enums import AuthTokenType
from pneumatic_backend.processes.services.workflow_action import (
    WorkflowActionService
)
from pneumatic_backend.processes.api_v2.services.task.task_version import (
    TaskUpdateVersionService
)
from pneumatic_backend.processes.models import (
    Delay,
    RawDueDate,
)
from pneumatic_backend.processes.enums import (
    DirectlyStatus,
    WorkflowStatus,
    DueDateRule,
    FieldType,
    PredicateOperator,
)

UserModel = get_user_model()
pytestmark = pytest.mark.django_db


class TestTaskUpdateVersionService:

    def test_update_from_version__only_required_fields__ok(self, mocker):

        # arrange
        user = create_test_user()
        workflow = create_test_workflow(user, tasks_count=1)
        task = workflow.current_task_instance
        service = TaskUpdateVersionService(
            user=user,
            instance=task,
            auth_type=AuthTokenType.USER,
            is_superuser=False
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
                }
            ],
        }

        fields_values = {'key': 'value'}
        fields_values_mock = mocker.patch(
            'pneumatic_backend.processes.models.workflows.workflow.Workflow.'
            'get_fields_markdown_values',
            return_value=fields_values
        )
        create_or_update_instance_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.services.task.task_version.'
            'TaskUpdateVersionService._create_or_update_instance'
        )
        update_fields_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.services.task.task_version.'
            'TaskUpdateVersionService._update_fields'
        )
        update_conditions_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.services.task.task_version.'
            'TaskUpdateVersionService._update_conditions'
        )
        update_checklists_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.services.task.task_version.'
            'TaskUpdateVersionService._update_checklists'
        )
        update_raw_due_date_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.services.task.task_version.'
            'TaskUpdateVersionService._update_raw_due_date'
        )
        set_due_date_from_template = mocker.patch(
            'pneumatic_backend.processes.api_v2.services.task.task.'
            'TaskService.set_due_date_from_template'
        )
        update_raw_performers_mock = mocker.patch(
            'pneumatic_backend.processes.models.workflows.task.Task.'
            'update_raw_performers_from_task_template'
        )
        update_performers_mock = mocker.patch(
            'pneumatic_backend.processes.models.workflows.task.Task.'
            'update_performers'
        )
        raw_performer = mocker.Mock()
        add_raw_performer_mock = mocker.patch(
            'pneumatic_backend.processes.models.workflows.task.Task.'
            'add_raw_performer',
            return_value=raw_performer
        )
        update_delay_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.services.task.task_version.'
            'TaskUpdateVersionService._update_delay'
        )

        # act
        service.update_from_version(
            data=data,
            version=1,
            workflow=workflow,
        )

        # assert
        fields_values_mock.assert_called_once_with(
            tasks_filter_kwargs={'number__lt': data['number']},
        )
        create_or_update_instance_mock.assert_called_once_with(
            data=data,
            workflow=workflow,
            prev_tasks_fields_values=fields_values
        )
        update_fields_mock.assert_called_once_with(data=None)
        update_conditions_mock.assert_called_once_with(data=None)
        update_checklists_mock.assert_called_once_with(
            data=None,
            version=version,
            fields_values=fields_values
        )
        update_raw_due_date_mock.assert_called_once_with(data=None)
        set_due_date_from_template.assert_called_once()
        task.refresh_from_db()
        assert task.due_date is None

        update_raw_performers_mock.assert_called_once_with(data)
        update_performers_mock.assert_called_once()
        add_raw_performer_mock.assert_not_called()
        update_delay_mock.assert_called_once_with(new_duration=None)

    def test_update_from_version__all_fields__current_task__ok(self, mocker):

        # arrange
        user = create_test_user()
        workflow = create_test_workflow(user, tasks_count=1)
        task = workflow.current_task_instance
        service = TaskUpdateVersionService(
            user=user,
            instance=task,
            auth_type=AuthTokenType.USER,
            is_superuser=False
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
                }
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
                                }
                            ]
                        }
                    ]
                }
            ],
            'raw_performers': [
                {
                    'id': 55,
                    'type': 'user',
                    'user_id': 27,
                    'api_name': None,
                }
            ],
            'raw_due_date': {
                'api_name': 'raw-due-date-bwybf0',
                'rule': 'after task started',
                'duration_months': 3,
                'duration': '1 00:00:00',
                'source_id': 'task-r5btf7'
            },
            'checklists': [
                {
                    'api_name': 'checklist-1',
                    'selections': [
                        {
                            'api_name': 'cl-selection-1',
                            'value': 'some value 1'
                        }
                    ]
                }
            ]
        }

        fields_values = {'key': 'value'}
        fields_values_mock = mocker.patch(
            'pneumatic_backend.processes.models.workflows.workflow.Workflow.'
            'get_fields_markdown_values',
            return_value=fields_values
        )
        create_or_update_instance_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.services.task.task_version.'
            'TaskUpdateVersionService._create_or_update_instance'
        )
        update_fields_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.services.task.task_version.'
            'TaskUpdateVersionService._update_fields'
        )
        update_conditions_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.services.task.task_version.'
            'TaskUpdateVersionService._update_conditions'
        )
        update_checklists_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.services.task.task_version.'
            'TaskUpdateVersionService._update_checklists'
        )
        update_raw_due_date_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.services.task.task_version.'
            'TaskUpdateVersionService._update_raw_due_date'
        )
        set_due_date_from_template = mocker.patch(
            'pneumatic_backend.processes.api_v2.services.task.task.'
            'TaskService.set_due_date_from_template'
        )
        update_raw_performers_mock = mocker.patch(
            'pneumatic_backend.processes.models.workflows.task.Task.'
            'update_raw_performers_from_task_template'
        )
        update_performers_mock = mocker.patch(
            'pneumatic_backend.processes.models.workflows.task.Task.'
            'update_performers'
        )
        raw_performer = mocker.Mock()
        add_raw_performer_mock = mocker.patch(
            'pneumatic_backend.processes.models.workflows.task.Task.'
            'add_raw_performer',
            return_value=raw_performer
        )
        update_delay_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.services.task.task_version.'
            'TaskUpdateVersionService._update_delay'
        )

        # act
        service.update_from_version(
            data=data,
            version=1,
            workflow=workflow,
        )

        # assert
        fields_values_mock.assert_called_once_with(
            tasks_filter_kwargs={'number__lt': data['number']},
        )
        create_or_update_instance_mock.assert_called_once_with(
            data=data,
            workflow=workflow,
            prev_tasks_fields_values=fields_values
        )
        update_fields_mock.assert_called_once_with(
            data=data['fields']
        )
        update_conditions_mock.assert_called_once_with(
            data=data['conditions']
        )
        update_checklists_mock.assert_called_once_with(
            data=data['checklists'],
            version=version,
            fields_values=fields_values
        )
        update_raw_due_date_mock.assert_called_once_with(
            data=data['raw_due_date']
        )
        set_due_date_from_template.assert_called_once()
        update_raw_performers_mock.assert_called_once_with(data)
        update_performers_mock.assert_called_once()
        add_raw_performer_mock.assert_not_called()
        update_delay_mock.assert_called_once_with(new_duration=data['delay'])

    def test_update_from_version__future_task__ok(self, mocker):

        # arrange
        user = create_test_user()
        workflow = create_test_workflow(user, tasks_count=2)
        task = workflow.tasks.get(number=2)
        service = TaskUpdateVersionService(
            user=user,
            instance=task,
            auth_type=AuthTokenType.USER,
            is_superuser=False
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
                }
            ],
            'raw_due_date': {
                'api_name': 'raw-due-date-bwybf0',
                'rule': 'after task started',
                'duration': '1 00:00:00',
                'source_id': 'task-r5btf7'
            },
        }

        mocker.patch(
            'pneumatic_backend.processes.api_v2.services.task.task_version.'
            'TaskUpdateVersionService._create_or_update_instance'
        )
        mocker.patch(
            'pneumatic_backend.processes.api_v2.services.task.task_version.'
            'TaskUpdateVersionService._update_fields'
        )
        mocker.patch(
            'pneumatic_backend.processes.api_v2.services.task.task_version.'
            'TaskUpdateVersionService._update_conditions'
        )
        mocker.patch(
            'pneumatic_backend.processes.api_v2.services.task.task_version.'
            'TaskUpdateVersionService._update_checklists'
        )
        update_raw_due_date_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.services.task.task_version.'
            'TaskUpdateVersionService._update_raw_due_date'
        )
        set_due_date_from_template = mocker.patch(
            'pneumatic_backend.processes.api_v2.services.task.task.'
            'TaskService.set_due_date_from_template'
        )
        update_raw_performers_mock = mocker.patch(
            'pneumatic_backend.processes.models.workflows.task.Task.'
            'update_raw_performers_from_task_template'
        )
        update_performers_mock = mocker.patch(
            'pneumatic_backend.processes.models.workflows.task.Task.'
            'update_performers'
        )
        raw_performer = mocker.Mock()
        add_raw_performer_mock = mocker.patch(
            'pneumatic_backend.processes.models.workflows.task.Task.'
            'add_raw_performer',
            return_value=raw_performer
        )
        mocker.patch(
            'pneumatic_backend.processes.api_v2.services.task.task_version.'
            'TaskUpdateVersionService._update_delay'
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
        mocker
    ):

        # arrange
        user = create_test_user()
        workflow = create_test_workflow(user, tasks_count=2)
        workflow.current_task = 2
        workflow.save(update_fields=['current_task'])
        task = workflow.tasks.get(number=1)
        service = TaskUpdateVersionService(
            user=user,
            instance=task,
            auth_type=AuthTokenType.USER,
            is_superuser=False
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
                }
            ],
            'raw_due_date': {
                'api_name': 'raw-due-date-bwybf0',
                'rule': 'after task started',
                'duration': '1 00:00:00',
                'source_id': 'task-r5btf7'
            },
        }

        mocker.patch(
            'pneumatic_backend.processes.api_v2.services.task.task_version.'
            'TaskUpdateVersionService._create_or_update_instance'
        )
        mocker.patch(
            'pneumatic_backend.processes.api_v2.services.task.task_version.'
            'TaskUpdateVersionService._update_fields'
        )
        mocker.patch(
            'pneumatic_backend.processes.api_v2.services.task.task_version.'
            'TaskUpdateVersionService._update_conditions'
        )
        mocker.patch(
            'pneumatic_backend.processes.api_v2.services.task.task_version.'
            'TaskUpdateVersionService._update_checklists'
        )
        update_raw_due_date_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.services.task.task_version.'
            'TaskUpdateVersionService._update_raw_due_date'
        )
        set_due_date_from_template = mocker.patch(
            'pneumatic_backend.processes.api_v2.services.task.task.'
            'TaskService.set_due_date_from_template'
        )
        update_raw_performers_mock = mocker.patch(
            'pneumatic_backend.processes.models.workflows.task.Task.'
            'update_raw_performers_from_task_template'
        )
        update_performers_mock = mocker.patch(
            'pneumatic_backend.processes.models.workflows.task.Task.'
            'update_performers'
        )
        raw_performer = mocker.Mock()
        add_raw_performer_mock = mocker.patch(
            'pneumatic_backend.processes.models.workflows.task.Task.'
            'add_raw_performer',
            return_value=raw_performer
        )
        mocker.patch(
            'pneumatic_backend.processes.api_v2.services.task.task_version.'
            'TaskUpdateVersionService._update_delay'
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
        mocker
    ):

        # arrange
        user = create_test_user()
        workflow = create_test_workflow(user, tasks_count=2)
        workflow.current_task = 2
        workflow.save(update_fields=['current_task'])
        task = workflow.tasks.get(number=1)
        task.raw_performers.all().delete()
        task.performers.all().delete()
        service = TaskUpdateVersionService(
            user=user,
            instance=task,
            auth_type=AuthTokenType.USER,
            is_superuser=False
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
                }
            ],
            'raw_due_date': {
                'api_name': 'raw-due-date-bwybf0',
                'rule': 'after task started',
                'duration': '1 00:00:00',
                'source_id': 'task-r5btf7'
            },
        }

        mocker.patch(
            'pneumatic_backend.processes.api_v2.services.task.task_version.'
            'TaskUpdateVersionService._create_or_update_instance'
        )
        mocker.patch(
            'pneumatic_backend.processes.api_v2.services.task.task_version.'
            'TaskUpdateVersionService._update_fields'
        )
        mocker.patch(
            'pneumatic_backend.processes.api_v2.services.task.task_version.'
            'TaskUpdateVersionService._update_conditions'
        )
        mocker.patch(
            'pneumatic_backend.processes.api_v2.services.task.task_version.'
            'TaskUpdateVersionService._update_checklists'
        )
        update_raw_due_date_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.services.task.task_version.'
            'TaskUpdateVersionService._update_raw_due_date'
        )
        set_due_date_from_template = mocker.patch(
            'pneumatic_backend.processes.api_v2.services.task.task.'
            'TaskService.set_due_date_from_template'
        )
        update_raw_performers_mock = mocker.patch(
            'pneumatic_backend.processes.models.workflows.task.Task.'
            'update_raw_performers_from_task_template'
        )

        raw_performer = mocker.Mock()
        add_raw_performer_mock = mocker.patch(
            'pneumatic_backend.processes.models.workflows.task.Task.'
            'add_raw_performer',
            return_value=raw_performer
        )
        mocker.patch(
            'pneumatic_backend.processes.api_v2.services.task.task_version.'
            'TaskUpdateVersionService._update_delay'
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
        user = create_test_user()
        workflow = create_test_workflow(user=user, tasks_count=1)
        task = workflow.current_task_instance
        delay = Delay.objects.create(
            task=task,
            start_date=timezone.now(),
            duration=timedelta(days=1)
        )
        service = TaskUpdateVersionService(
            user=user,
            instance=task,
            auth_type=AuthTokenType.USER,
            is_superuser=False
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
        mocker
    ):

        # arrange
        user = create_test_user()
        workflow = create_test_workflow(user=user, tasks_count=1)
        task = workflow.current_task_instance
        old_duration = timedelta(days=1)
        delay = Delay.objects.create(
            task=task,
            start_date=timezone.now(),
            duration=old_duration,
            directly_status=DirectlyStatus.CREATED
        )
        service = TaskUpdateVersionService(
            user=user,
            instance=task,
            auth_type=AuthTokenType.USER,
            is_superuser=False
        )
        new_duration_str = '14 00:00:00'

        # act
        service._update_delay(new_duration=new_duration_str)

        # assert
        delay.refresh_from_db()
        assert delay.duration == old_duration

    def test_update_delay__new_duration_and_not_delay__create(
        self,
        mocker
    ):

        # arrange
        user = create_test_user()
        workflow = create_test_workflow(user=user, tasks_count=1)
        task = workflow.current_task_instance
        service = TaskUpdateVersionService(
            user=user,
            instance=task,
            auth_type=AuthTokenType.USER,
            is_superuser=False
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
        mocker
    ):
        # arrange
        user = create_test_user()
        workflow = create_test_workflow(user=user, tasks_count=1)
        task = workflow.current_task_instance
        service = TaskUpdateVersionService(
            user=user,
            instance=task,
            auth_type=AuthTokenType.USER,
            is_superuser=False
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
        user = create_test_user()
        workflow = create_test_workflow(user=user, tasks_count=1)
        workflow.status = WorkflowStatus.DELAYED
        workflow.save(update_fields=['status'])
        task = workflow.current_task_instance
        old_duration = timedelta(days=1)
        delay = Delay.objects.create(
            task=task,
            start_date=timezone.now(),
            duration=old_duration,
            directly_status=DirectlyStatus.CREATED
        )
        service = TaskUpdateVersionService(
            user=user,
            instance=task,
            sync=False,
            auth_type=AuthTokenType.USER,
            is_superuser=False
        )
        resume_workflow_init_mock = mocker.patch.object(
            WorkflowActionService,
            attribute='__init__',
            return_value=None
        )
        resume_workflow_mock = mocker.patch(
            'pneumatic_backend.processes.services.'
            'workflow_action.WorkflowActionService.resume_workflow'
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
        resume_workflow_mock.assert_not_called()

    def test_update_delay__not_duration_and_current_task_delay__end_delay(
        self
    ):

        # arrange
        user = create_test_user()
        workflow = create_test_workflow(user=user, tasks_count=1)
        workflow.status = WorkflowStatus.DELAYED
        workflow.save(update_fields=['status'])
        task = workflow.current_task_instance
        delay = Delay.objects.create(
            task=task,
            start_date=timezone.now(),
            duration=timedelta(days=1)
        )
        sync = True
        service = TaskUpdateVersionService(
            user=user,
            instance=task,
            sync=sync,
            auth_type=AuthTokenType.USER,
            is_superuser=False
        )

        # act
        service._update_delay()

        # assert
        delay.refresh_from_db()
        assert delay.end_date

    def test_update_delay__not_duration_and_future_task_delay__delete_delay(
        self,
        mocker,
    ):

        # arrange
        user = create_test_user()
        workflow = create_test_workflow(user=user, tasks_count=2)
        workflow.status = WorkflowStatus.DELAYED
        workflow.save(update_fields=['status'])
        task_2 = workflow.tasks.get(number=2)
        delay = Delay.objects.create(
            task=task_2,
            start_date=timezone.now(),
            duration=timedelta(days=1)
        )
        service = TaskUpdateVersionService(
            user=user,
            instance=task_2,
            auth_type=AuthTokenType.USER,
            is_superuser=False
        )

        # act
        service._update_delay()

        # assert
        assert not Delay.objects.filter(id=delay.id).exists()

    def test__update_raw_due_date__not_version_data__delete_previous(self):

        # arrange
        user = create_test_user()
        workflow = create_test_workflow(user, tasks_count=1)
        task = workflow.current_task_instance
        raw_due_date = RawDueDate.objects.create(
            rule=DueDateRule.AFTER_WORKFLOW_STARTED,
            duration=timedelta(hours=1),
            task=task
        )
        service = TaskUpdateVersionService(
            user=user,
            instance=task,
            auth_type=AuthTokenType.USER,
            is_superuser=False
        )

        # act
        service._update_raw_due_date(data=None)

        # assert
        assert not RawDueDate.objects.filter(id=raw_due_date.id).exists()

    def test__update_raw_due_date__create_new__ok(self):

        # arrange
        user = create_test_user()
        workflow = create_test_workflow(user, tasks_count=1)
        task = workflow.current_task_instance
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
            is_superuser=False
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

    def test__update_raw_due_date__update_existent__ok(self):

        # arrange
        user = create_test_user()
        workflow = create_test_workflow(user, tasks_count=1)
        task = workflow.current_task_instance
        raw_due_date = RawDueDate.objects.create(
            rule=DueDateRule.AFTER_WORKFLOW_STARTED,
            duration=timedelta(hours=1),
            task=task,
            api_name='raw-due-date-1'
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
            is_superuser=False
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
