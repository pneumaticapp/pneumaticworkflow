# ruff: noqa: UP031
from datetime import timedelta

import pytest

from src.authentication.enums import AuthTokenType
from src.processes.enums import (
    ConditionAction,
    DueDateRule,
    FieldType,
    OwnerType,
    PerformerType,
    PredicateOperator,
    PredicateType,
    TaskStatus,
)
from src.processes.messages import template as messages
from src.processes.models.templates.fields import (
    FieldTemplate,
)
from src.processes.models.templates.raw_due_date import RawDueDateTemplate
from src.processes.models.templates.task import TaskTemplate
from src.processes.models.workflows.fields import (
    TaskField,
)
from src.processes.models.workflows.workflow import Workflow
from src.processes.services.versioning.schemas import (
    TemplateSchemaV1,
)
from src.processes.services.versioning.versioning import (
    TemplateVersioningService,
)
from src.processes.services.workflows.workflow_version import (
    WorkflowUpdateVersionService,
)
from src.processes.tests.fixtures import (
    create_invited_user,
    create_test_account,
    create_test_template,
    create_test_user,
    create_test_workflow,
)
from src.utils.validation import ErrorCode

pytestmark = pytest.mark.django_db


class TestUpdateTemplateTask:

    def test_update__all_fields__ok(
        self,
        mocker,
        api_client,
    ):

        # arrange
        user = create_test_user()
        user2 = create_test_user(
            email='test2@pneumatic.app',
            account=user.account,
        )
        api_client.token_authenticate(user)

        template = create_test_template(
            user=user,
            tasks_count=1,
            is_active=True,
        )
        task = template.tasks.first()
        kickoff = template.kickoff_instance
        FieldTemplate.objects.create(
            name='Name',
            api_name='name',
            type=FieldType.USER,
            kickoff=kickoff,
            is_required=True,
            template=template,
        )
        mocker.patch(
            'src.processes.services.templates.'
            'integrations.TemplateIntegrationsService.template_updated',
        )
        duration = '01:00:00'

        request_data = {
            'id': task.id,
            'number': 1,
            'name': 'Changed first step',
            'api_name': task.api_name,
            'description': 'Changed desc',
            'require_completion_by_all': True,
            'raw_performers': [
                {
                    'type': PerformerType.USER,
                    'source_id': user2.id,
                },
                {
                    'type': PerformerType.WORKFLOW_STARTER,
                    'source_id': None,
                },
                {
                    'type': PerformerType.FIELD,
                    'source_id': 'user-field-2',
                },
            ],
            'delay': None,
            'revert_task': None,
            'raw_due_date': {
                'api_name': 'raw-due-date-bwybf0',
                'rule': 'after task started',
                'duration_months': 0,
                'duration': duration,
                'source_id': task.api_name,
            },
            'fields': [],
        }

        # act
        response = api_client.put(
            path=f'/templates/{template.id}',
            data={
                'id': template.id,
                'name': template.name,
                'is_active': True,
                'owners': [
                    {
                        'type': OwnerType.USER,
                        'source_id': user.id,
                    },
                    {
                        'type': OwnerType.USER,
                        'source_id': user2.id,
                    },
                ],
                'kickoff': {
                    'fields': [
                        {
                            'order': 2,
                            'is_required': True,
                            'name': 'First step new performer',
                            'type': FieldType.USER,
                            'api_name': 'user-field-2',
                        },
                    ],
                },
                'tasks': [request_data],
            },
        )

        # assert
        assert response.status_code == 200
        assert len(response.data['tasks']) == 1
        response_data = response.data['tasks'][0]
        assert response_data.get('api_name')
        assert response_data['name'] == request_data['name']
        assert response_data['number'] == request_data['number']
        assert response_data['description'] == request_data['description']
        assert len(response_data['raw_performers']) == len(
            request_data['raw_performers'],
        )
        assert response_data['delay'] is None
        assert response_data['revert_task'] is None
        assert response_data['raw_due_date']['duration'] == duration
        assert response_data['fields'] == request_data['fields']
        assert response_data['require_completion_by_all'] == (
            request_data['require_completion_by_all']
        )

        task.refresh_from_db()
        assert task.name == request_data['name']
        assert task.number == request_data['number']
        assert task.description == request_data['description']
        assert task.raw_performers.count() == len(
            request_data['raw_performers'],
        )
        assert task.raw_performers.first().user.id == user2.id
        assert task.raw_performers.last().field.api_name == 'user-field-2'
        assert task.revert_task is None
        assert task.delay is None
        assert task.fields.count() == len(request_data['fields'])
        assert task.require_completion_by_all == (
            request_data['require_completion_by_all']
        )
        assert task.account_id == user.account.id

    def test_update__delete__ok(
        self,
        mocker,
        api_client,
    ):

        # arrange
        user = create_test_user()
        api_client.token_authenticate(user)

        template = create_test_template(
            user=user,
            tasks_count=2,
            is_active=True,
        )
        first_task = template.tasks.first()
        second_task = template.tasks.last()
        mocker.patch(
            'src.processes.services.templates.'
            'integrations.TemplateIntegrationsService.template_updated',
        )

        # act
        response = api_client.put(
            path=f'/templates/{template.id}',
            data={
                'id': template.id,
                'name': template.name,
                'is_active': True,
                'owners': [
                    {
                        'type': OwnerType.USER,
                        'source_id': user.id,
                    },
                ],
                'kickoff': {},
                'tasks': [
                    {
                        'id': second_task.id,
                        'name': second_task.name,
                        'api_name': second_task.api_name,
                        'number': 1,
                        'raw_performers': [
                            {
                                'type': PerformerType.USER,
                                'source_id': user.id,
                            },
                        ],
                    },
                ],
            },
        )

        # assert
        assert response.status_code == 200
        data = response.json()
        template.refresh_from_db()
        assert len(data['tasks']) == 1
        assert template.tasks.count() == 1
        assert not TaskTemplate.objects.filter(id=first_task.id).exists()

    def test_update__add_task_in_beginning__ok(
        self,
        mocker,
        api_client,
    ):
        """ caused by: https://my.pneumatic.app/workflows/12627"""

        # arrange
        user = create_test_user()
        api_client.token_authenticate(user)
        new_task = {
            'number': 1,
            'name': 'Second step',
            'raw_performers': [
                {
                    'type': PerformerType.USER,
                    'source_id': user.id,
                },
            ],
        }
        first_task = {
            'number': 1,
            'name': 'First step',
            'raw_performers': [
                {
                    'type': PerformerType.USER,
                    'source_id': user.id,
                },
            ],
            'fields': [
                {
                    'type': FieldType.STRING,
                    'order': 0,
                    'name': 'Field',
                    'is_required': False,
                    'api_name': 'field-123456',
                },
            ],
        }
        second_task = {
            'number': 2,
            'name': '{{field-123456}} Second step',
            'raw_performers': [
                {
                    'type': PerformerType.USER,
                    'source_id': user.id,
                },
            ],
            'description': '{{field-123456}}',
        }

        response = api_client.post(
            path='/templates',
            data={
                'name': 'Template',
                'owners': [
                    {
                        'type': OwnerType.USER,
                        'source_id': user.id,
                    },
                ],
                'kickoff': {},
                'is_active': True,
                'tasks': [
                    first_task,
                    second_task,
                ],
            },
        )

        template_data = response.data
        template_id = template_data['id']
        template_data['tasks'][0]['number'] = 2
        template_data['tasks'][1]['number'] = 3
        template_data['tasks'].insert(0, new_task)
        template_data['owners'] = [
            {
                'type': OwnerType.USER,
                'source_id': user.id,
            },
        ]
        mocker.patch(
            'src.processes.services.templates.'
            'integrations.TemplateIntegrationsService.template_updated',
        )

        # act
        response = api_client.put(
            path=f'/templates/{template_id}',
            data=template_data,
        )

        # assert
        assert response.status_code == 200
        assert len(response.data['tasks']) == 3

    def test_update__incorrect_performer__validation_error(
        self,
        mocker,
        api_client,
    ):

        """ Check that performer user not found in account users """

        # arrange
        user = create_test_user()
        another_user = create_test_user(email='test2@pneumatic.app')
        api_client.token_authenticate(user)

        template = create_test_template(
            user=user,
            is_active=True,
            tasks_count=1,
        )
        task = template.tasks.first()
        mocker.patch(
            'src.processes.services.templates.'
            'integrations.TemplateIntegrationsService.template_updated',
        )

        # act
        response = api_client.put(
            path=f'/templates/{template.id}',
            data={
                'name': 'Template',
                'owners': [
                    {
                        'type': OwnerType.USER,
                        'source_id': user.id,
                    },
                ],
                'is_active': True,
                'description': '',
                'kickoff': {},
                'tasks': [
                    {
                        'id': task.id,
                        'name': task.name,
                        'number': task.number,
                        'raw_performers': [
                            {
                                'type': PerformerType.USER,
                                'source_id': another_user.id,
                            },
                        ],
                    },
                ],
            },
        )

        # assert
        assert response.status_code == 400

    def test_update__performer_type_field_after_template_run__ok(
        self,
        mocker,
        api_client,
    ):
        """ Create template with one task,
            run it, then edit task for change
            user performer to field performer """

        # arrange
        user = create_test_user()
        api_client.token_authenticate(user)

        template = create_test_template(
            user=user,
            tasks_count=2,
            is_active=True,
        )
        response = api_client.post(
            f'/templates/{template.id}/run',
            data={
                'name': 'Test template',
            },
        )
        workflow_id = response.data['id']

        template_first_task = template.tasks.first()
        raw_performer_1 = template_first_task.raw_performers.get(user=user)
        template_last_task = template.tasks.last()
        field = FieldTemplate.objects.create(
            name='Second task performer',
            type=FieldType.USER,
            is_required=True,
            task=template_first_task,
            template=template,
        )
        mocker.patch(
            'src.processes.services.templates.'
            'integrations.TemplateIntegrationsService.template_updated',
        )

        # act
        response = api_client.put(
            f'/templates/{template.id}',
            data={
                'name': 'Template',
                'owners': [
                    {
                        'type': OwnerType.USER,
                        'source_id': user.id,
                    },
                ],
                'is_active': True,
                'kickoff': {
                    'fields': [],
                },
                'tasks': [
                    {
                        'id': template_first_task.id,
                        'number': template_first_task.number,
                        'name': template_first_task.name,
                        'api_name': template_first_task.api_name,
                        'raw_performers': [
                            {
                                'type': PerformerType.USER,
                                'source_id': user.id,
                                'api_name': raw_performer_1.api_name,
                            },
                        ],
                        'fields': [
                            {
                                'id': field.id,
                                'type': field.type,
                                'order': field.order,
                                'name': field.name,
                                'is_required': field.is_required,
                                'api_name': field.api_name,
                            },
                        ],
                    },
                    {
                        'id': template_last_task.id,
                        'number': template_last_task.number,
                        'name': template_last_task.name,
                        'api_name': template_last_task.api_name,
                        'raw_performers': [
                            {
                                'type': PerformerType.FIELD,
                                'source_id': field.api_name,
                                'api_name': 'raw-performer-3',
                            },
                        ],
                    },
                ],
            },
        )

        # assert
        workflow = Workflow.objects.get(pk=workflow_id)
        second_task = workflow.tasks.get(number=2)
        assert response.status_code == 200
        assert second_task.raw_performers.count() == 1
        assert second_task.raw_performers.get(
            type=PerformerType.FIELD,
            field__api_name=field.api_name,
            api_name='raw-performer-3',
        )

    def test_update__task_performer_type_field_for_next_task__ok(
        self,
        mocker,
        api_client,
    ):
        """ 1.Creates a template with one task.
            2.Run workflow
            3.Add second and third tasks with performer type field
            4.Assert that both 'performer type field' exist in created tasks

            Additionally checks the correct order in which to rocess tasks
            in the 'CreateOrUpdateMixin.create_or_update_related' method """

        # arrange
        user = create_test_user()
        api_client.token_authenticate(user)

        template = create_test_template(
            user=user,
            tasks_count=1,
            is_active=True,
        )
        task_template_1 = template.tasks.first()
        mocker.patch(
            'src.processes.services.templates.'
            'integrations.TemplateIntegrationsService.template_updated',
        )

        # act
        response = api_client.put(
            path=f'/templates/{template.id}',
            data={
                'name': 'Template',
                'owners': [
                    {
                        'type': OwnerType.USER,
                        'source_id': user.id,
                    },
                ],
                'is_active': True,
                'kickoff': {},
                'tasks': [
                    {
                        'id': task_template_1.id,
                        'number': task_template_1.number,
                        'name': task_template_1.name,
                        'api_name': task_template_1.api_name,
                        'raw_performers': [
                            {
                                'type': PerformerType.USER,
                                'source_id': user.id,
                                'api_name': 'raw-performer-3',
                            },
                        ],
                        'fields': [
                            {
                                'name': 'Second task performer №1',
                                'description': '',
                                'is_required': True,
                                'api_name': 'user-field-1',
                                'order': 1,
                                'type': FieldType.USER,
                            },
                        ],
                    },
                    {
                        'number': 2,
                        'name': 'Second task',
                        'raw_performers': [
                            {
                                'type': PerformerType.FIELD,
                                'source_id': 'user-field-1',
                                'api_name': 'raw-performer-4',
                            },
                        ],
                        'fields': [
                            {
                                'name': 'Third task performer №1',
                                'description': '',
                                'is_required': True,
                                'api_name': 'user-field-2',
                                'order': 1,
                                'type': FieldType.USER,
                            },
                        ],
                    },
                    {
                        'name': 'Third step',
                        'number': 3,
                        'raw_performers': [
                            {
                                'type': PerformerType.FIELD,
                                'source_id': 'user-field-1',
                                'api_name': 'raw-performer-5',
                            },
                            {
                                'type': PerformerType.FIELD,
                                'source_id': 'user-field-2',
                                'api_name': 'raw-performer-6',
                            },
                        ],
                    },
                ],
            },
        )

        # assert
        assert response.status_code == 200
        template.refresh_from_db()
        tasks = list(template.tasks.order_by('number'))
        assert len(tasks) == 3

        second_task = tasks[1]
        assert second_task.raw_performers.count() == 1
        assert second_task.raw_performers.first().field.api_name == (
            'user-field-1'
        )
        third_task = tasks[2]
        assert third_task.raw_performers.count() == 2
        performers = third_task.raw_performers.all().order_by('id')
        assert performers.first().field.api_name == 'user-field-1'
        assert performers.last().field.api_name == 'user-field-2'

    def test_update__performer_type_field_from_previous_step__validation_error(
        self,
        mocker,
        api_client,
    ):
        """ Checking for adding field to task performers
            created before task with field """

        # arrange
        user = create_test_user()
        api_client.token_authenticate(user)

        template = create_test_template(
            user=user,
            tasks_count=2,
            is_active=True,
        )
        task_template2 = template.tasks.last()
        field_template = FieldTemplate.objects.create(
            name='performer',
            type=FieldType.USER,
            is_required=True,
            task=task_template2,
            template=template,
        )
        task_template1 = template.tasks.first()
        mocker.patch(
            'src.processes.services.templates.'
            'integrations.TemplateIntegrationsService.template_updated',
        )

        # act
        response = api_client.put(
            path=f'/templates/{template.id}',
            data={
                'name': 'Template',
                'owners': [
                    {
                        'type': OwnerType.USER,
                        'source_id': user.id,
                    },
                ],
                'is_active': True,
                'kickoff': {},
                'tasks': [
                    {
                        'id': task_template1.id,
                        'number': task_template1.number,
                        'name': task_template1.name,
                        'raw_performers': [
                            {
                                'type': PerformerType.FIELD,
                                'source_id': field_template.api_name,
                                'api_name': 'raw-performer-7',
                            },
                        ],
                    },
                ],
            },
        )

        # assert
        assert response.status_code == 400

    def test_update__require_competition_by_all_performer_type_field__ok(
        self,
        mocker,
        api_client,
    ):
        """ Bug case info: https://trello.com/c/byARLoa7 """

        # arrange
        user = create_test_user()
        api_client.token_authenticate(user)
        user2 = create_test_user(
            email='test2@pneumatic.app',
            account=user.account,
        )

        template = create_test_template(
            user=user,
            tasks_count=2,
            is_active=True,
        )
        field_template_kickoff = FieldTemplate.objects.create(
            name="Kickoff user field",
            type=FieldType.USER,
            is_required=True,
            kickoff=template.kickoff_instance,
            template=template,
        )

        task_template1 = template.tasks.first()
        task_template1.require_completion_by_all = True
        task_template1.save()

        field_template_first_task = FieldTemplate.objects.create(
            name="First task user field",
            type=FieldType.USER,
            is_required=True,
            task=task_template1,
            template=template,
        )
        task_template2 = template.tasks.last()
        task_template2.description = (
            '{{%s}} {{%s}}' % (
                field_template_kickoff.api_name,
                field_template_first_task.api_name,
            )
        )
        task_template2.delete_raw_performers()
        task_template2.add_raw_performer(
            performer_type=PerformerType.FIELD,
            field=field_template_kickoff,
        )
        task_template2.add_raw_performer(
            performer_type=PerformerType.FIELD,
            field=field_template_first_task,
        )
        task_template2.save()

        response = api_client.post(
            f'/templates/{template.id}/run',
            data={
                'name': 'Test workflow',
                'kickoff': {
                    field_template_kickoff.api_name: user.email,
                },
            },
        )

        workflow_id = response.data['id']
        workflow = Workflow.objects.get(id=workflow_id)
        task = workflow.tasks.get(number=1)
        api_client.post(
            f'/v2/tasks/{task.id}/complete',
            data={
                'output': {
                    field_template_first_task.api_name: user2.email,
                },
            },
        )
        mocker.patch(
            'src.processes.services.templates.'
            'integrations.TemplateIntegrationsService.template_updated',
        )

        # act
        response = api_client.put(
            path=f'/templates/{template.id}',
            data={
                'name': 'Template',
                'owners': [
                    {
                        'type': OwnerType.USER,
                        'source_id': user.id,
                    },
                    {
                        'type': OwnerType.USER,
                        'source_id': user2.id,
                    },
                ],
                'kickoff': {
                    'fields': [
                        {
                            'type': field_template_kickoff.type,
                            'order': field_template_kickoff.order,
                            'name': field_template_kickoff.name,
                            'is_required': field_template_kickoff.is_required,
                            'api_name': field_template_kickoff.api_name,
                        },
                    ],
                },
                'tasks': [
                    {
                        'id': task_template1.id,
                        'number': task_template1.number,
                        'name': task_template1.name,
                        'require_completion_by_all': False,
                        'raw_performers': [
                            {
                                'type': PerformerType.USER,
                                'source_id': user.id,
                                'api_name': 'raw-performer-1',
                            },
                        ],
                        'fields': [
                            {
                                'type': field_template_first_task.type,
                                'order': field_template_first_task.order,
                                'name': field_template_first_task.name,
                                'is_required': True,
                                'api_name': field_template_first_task.api_name,
                            },
                        ],
                    },
                    {
                        'id': task_template2.id,
                        'number': task_template2.number,
                        'name': task_template2.name,
                        'description': task_template2.description,
                        'raw_performers': [
                            {
                                'type': PerformerType.FIELD,
                                'source_id': field_template_kickoff.api_name,
                                'api_name': 'raw-performer-3',
                            },
                            {
                                'type': PerformerType.FIELD,
                                'source_id': (
                                    field_template_first_task.api_name
                                ),
                                'api_name': 'raw-performer-12',
                            },
                        ],
                    },
                ],
            },
        )

        # assert
        assert response.status_code == 200
        workflow.refresh_from_db()
        task2 = workflow.tasks.get(number=2)
        assert task2.description == (
            f'{user.get_full_name()} {user.get_full_name()}'
        )

        performers = task2.performers.order_by('id')
        assert performers.count() == 2
        assert performers.first().id == user.id
        assert performers.last().id == user2.id

    def test_update__change_performer_for_active_task__ok(
        self,
        mocker,
        api_client,
    ):

        # arrange
        user1 = create_test_user()
        user2 = create_test_user(
            email='test2@pneumatic.app',
            account=user1.account,
        )
        user1_new = create_test_user(
            email='test3@pneumatic.app',
            account=user1.account,
        )
        user2_new = create_test_user(
            email='test4@pneumatic.app',
            account=user1.account,
        )
        api_client.token_authenticate(user1)

        template = create_test_template(
            user=user1,
            tasks_count=1,
            is_active=True,
        )
        kickoff = template.kickoff_instance
        field_template_1 = FieldTemplate.objects.create(
            name="Kickoff user field 1",
            type=FieldType.USER,
            is_required=True,
            kickoff=kickoff,
            template=template,
        )
        field_template_2 = FieldTemplate.objects.create(
            name="Kickoff user field 2",
            type=FieldType.USER,
            is_required=True,
            kickoff=kickoff,
            template=template,
        )
        task_template = template.tasks.first()
        task_template.delete_raw_performers()
        task_template.add_raw_performer(
            performer_type=PerformerType.FIELD,
            field=field_template_1,
        )

        response = api_client.post(
            f'/templates/{template.id}/run',
            data={
                'name': 'Test workflow',
                'kickoff': {
                    field_template_1.api_name: user2.email,
                    field_template_2.api_name: user2_new.email,
                },
            },
        )

        workflow_id = response.data['id']
        workflow = Workflow.objects.get(id=workflow_id)
        task_template = template.tasks.first()
        mocker.patch(
            'src.processes.services.templates.'
            'integrations.TemplateIntegrationsService.template_updated',
        )

        # act
        response = api_client.put(
            f"/templates/{template.id}",
            data={
                'name': 'Template',
                'owners': [
                    {
                        'type': OwnerType.USER,
                        'source_id': user1.id,
                    },
                    {
                        'type': OwnerType.USER,
                        'source_id': user2.id,
                    },
                    {
                        'type': OwnerType.USER,
                        'source_id': user1_new.id,
                    },
                    {
                        'type': OwnerType.USER,
                        'source_id': user2_new.id,
                    },
                ],
                'is_active': True,
                'kickoff': {
                    'fields': [
                        {
                            'id': field_template_2.id,
                            'type': field_template_2.type,
                            'order': field_template_2.order,
                            'name': field_template_2.name,
                            'is_required': field_template_2.is_required,
                            'api_name': field_template_2.api_name,
                        },
                     ],
                },
                'tasks': [
                    {
                        'id': task_template.id,
                        'number': task_template.number,
                        'name': task_template.name,
                        'api_name': task_template.api_name,
                        'raw_performers': [
                            {
                                'type': PerformerType.USER,
                                'source_id': user1_new.id,
                                'api_name': 'raw-performer-1',
                            },
                            {
                                'type': PerformerType.FIELD,
                                'source_id': field_template_2.api_name,
                                'api_name': 'raw-performer-2',
                            },
                        ],
                    },
                ],
            },
        )

        # assert
        assert response.status_code == 200
        workflow.refresh_from_db()
        task = workflow.tasks.first()
        task_field2 = TaskField.objects.get(
            api_name=field_template_2.api_name,
        )
        raw_performers = task.raw_performers.all()
        assert raw_performers.count() == 2
        assert raw_performers.get(user_id=user1_new.id)
        assert raw_performers.get(field__api_name=task_field2.api_name)

        performers = task.performers.all()
        assert performers.count() == 2
        assert performers.get(id=user1_new.id)
        assert performers.get(id=user2_new.id)

    def test_update__change_performer_for_completed_task__do_nothing(
        self,
        mocker,
        api_client,
    ):

        # arrange
        user1 = create_test_user()
        user1_new = create_test_user(
            email='test3@pneumatic.app',
            account=user1.account,
        )
        user2 = create_invited_user(
            user=user1,
            email='test2@pneumatic.app',
        )
        user2_new = create_invited_user(
            user=user1,
            email='test4@pneumatic.app',
        )
        api_client.token_authenticate(user=user1)

        template = create_test_template(
            user=user1,
            tasks_count=2,
            is_active=True,
        )
        kickoff = template.kickoff_instance
        field_template_1 = FieldTemplate.objects.create(
            name="Kickoff user field 1",
            type=FieldType.USER,
            is_required=True,
            kickoff=kickoff,
            template=template,
        )
        field_template_2 = FieldTemplate.objects.create(
            name="Kickoff user field 2",
            type=FieldType.USER,
            is_required=True,
            kickoff=kickoff,
            template=template,
        )
        template_first_task = template.tasks.first()
        template_first_task.add_raw_performer(
            performer_type=PerformerType.FIELD,
            field=field_template_1,
        )

        response = api_client.post(
            f'/templates/{template.id}/run',
            data={
                'name': 'Test workflow',
                'kickoff': {
                    field_template_1.api_name: user2.email,
                    field_template_2.api_name: user2_new.email,
                },
            },
        )

        workflow_id = response.data['id']
        workflow = Workflow.objects.get(id=workflow_id)
        task = workflow.tasks.get(number=1)
        api_client.post(f'/v2/tasks/{task.id}/complete')
        mocker.patch(
            'src.processes.services.templates.'
            'integrations.TemplateIntegrationsService.template_updated',
        )

        # act
        response = api_client.put(
            f'/templates/{template.id}',
            data={
                'name': 'Template',
                'owners': [
                    {
                        'type': OwnerType.USER,
                        'source_id': user1.id,
                    },
                    {
                        'type': OwnerType.USER,
                        'source_id': user2.id,
                    },
                    {
                        'type': OwnerType.USER,
                        'source_id': user1_new.id,
                    },
                    {
                        'type': OwnerType.USER,
                        'source_id': user2_new.id,
                    },
                ],
                'is_active': True,
                'kickoff': {
                    'fields': [
                        {
                            'id': field_template_1.id,
                            'type': field_template_1.type,
                            'order': field_template_1.order,
                            'name': field_template_1.name,
                            'is_required': field_template_1.is_required,
                            'api_name': field_template_1.api_name,
                        },
                        {
                            'id': field_template_2.id,
                            'type': field_template_2.type,
                            'order': field_template_2.order,
                            'name': field_template_2.name,
                            'is_required': field_template_2.is_required,
                            'api_name': field_template_2.api_name,
                        },
                    ],
                },
                'tasks': [
                    {
                        'id': template_first_task.id,
                        'number': template_first_task.number,
                        'name': template_first_task.name,
                        'api_name': template_first_task.api_name,
                        'raw_performers': [
                            {
                                'type': PerformerType.USER,
                                'source_id': user1_new.id,
                                'api_name': 'raw-performer-1',
                            },
                            {
                                'type': PerformerType.FIELD,
                                'source_id': field_template_2.api_name,
                                'api_name': 'raw-performer-2',
                            },
                        ],
                    },
                ],
            },
        )

        # assert
        assert response.status_code == 200
        workflow.refresh_from_db()
        completed_task = workflow.tasks.get(number=1)
        assert completed_task.is_completed
        raw_performers = completed_task.raw_performers.all()
        assert raw_performers.count() == 2
        raw_performer_1 = raw_performers.get(type=PerformerType.USER)
        assert raw_performer_1.user_id == user1.id
        raw_performer_2 = raw_performers.get(type=PerformerType.FIELD)
        assert raw_performer_2.field.api_name == field_template_1.api_name

        performers = completed_task.performers.all()
        assert performers.count() == 2
        assert performers.get(id=user1.id)
        assert performers.get(id=user2.id)

    def test_update__remove_performer_type_field_from_active_task__ok(
        self,
        mocker,
        api_client,
    ):

        # arrange
        user1 = create_test_user()
        user2 = create_test_user(
            email='test2@pneumatic.app',
            account=user1.account,
        )
        api_client.token_authenticate(user=user1)

        template = create_test_template(
            user=user1,
            tasks_count=2,
            is_active=True,
        )

        field_template = FieldTemplate.objects.create(
            name="Kickoff user field",
            type=FieldType.USER,
            is_required=True,
            kickoff=template.kickoff_instance,
            template=template,
        )

        for task_template in template.tasks.all():
            task_template.delete_raw_performers()
            task_template.add_raw_performer(
                performer_type=PerformerType.FIELD,
                field=field_template,
            )
            task_template.add_raw_performer(
                performer_type=PerformerType.WORKFLOW_STARTER,
            )
            task_template.save()

        response = api_client.post(
            f'/templates/{template.id}/run',
            data={
                'name': 'Test workflow',
                'kickoff': {
                    field_template.api_name: user2.email,
                },
            },
        )

        workflow_id = response.data['id']
        workflow = Workflow.objects.get(id=workflow_id)
        template_first_task = template.tasks.first()
        template_second_task = template.tasks.last()
        mocker.patch(
            'src.processes.services.templates.'
            'integrations.TemplateIntegrationsService.template_updated',
        )

        # act
        response = api_client.put(
            f'/templates/{template.id}',
            data={
                'name': 'Template',
                'owners': [
                    {
                        'type': OwnerType.USER,
                        'source_id': user1.id,
                    },
                    {
                        'type': OwnerType.USER,
                        'source_id': user2.id,
                    },
                ],
                'is_active': True,
                'kickoff': {
                    'fields': [
                        {
                            'id': field_template.id,
                            'type': field_template.type,
                            'order': field_template.order,
                            'name': field_template.name,
                            'is_required': field_template.is_required,
                            'api_name': field_template.api_name,
                        },
                    ],
                },
                'tasks': [
                    {
                        'id': template_first_task.id,
                        'number': template_first_task.number,
                        'name': template_first_task.name,
                        'api_name': template_first_task.api_name,
                        'raw_performers': [
                            {
                                'type': PerformerType.WORKFLOW_STARTER,
                                'source_id': None,
                                'api_name': 'raw-performer-1',
                            },
                        ],
                    },
                    {
                        'id': template_second_task.id,
                        'number': template_second_task.number,
                        'name': template_second_task.name,
                        'api_name': template_second_task.api_name,
                        'raw_performers': [
                            {
                                'type': PerformerType.WORKFLOW_STARTER,
                                'source_id': None,
                                'api_name': 'raw-performer-2',
                            },
                        ],
                    },
                ],
            },
        )
        workflow.refresh_from_db()

        # assert
        assert response.status_code == 200
        tasks = response.data['tasks']
        assert len(tasks[0]['raw_performers']) == 1
        assert tasks[0]['raw_performers'][0]['type'] == (
            PerformerType.WORKFLOW_STARTER
        )
        assert len(tasks[1]['raw_performers']) == 1
        assert tasks[1]['raw_performers'][0]['type'] == (
            PerformerType.WORKFLOW_STARTER
        )

    def test_update__different_performers_in_different_workflows__ok(
        self,
        mocker,
        api_client,
    ):

        # arrange
        user1 = create_test_user()
        user2 = create_test_user(
            email='test2@pneumatic.app',
            account=user1.account,
        )
        user3 = create_test_user(
            email='test3@pneumatic.app',
            account=user1.account,
        )
        api_client.token_authenticate(user=user1)

        template = create_test_template(
            user=user1,
            tasks_count=1,
            is_active=True,
        )

        field_template = FieldTemplate.objects.create(
            name="Kickoff user field",
            type=FieldType.USER,
            is_required=True,
            kickoff=template.kickoff_instance,
            template=template,
        )

        response = api_client.post(
            f'/templates/{template.id}/run',
            data={
                'name': 'Test workflow 1',
                'kickoff': {
                    field_template.api_name: user2.email,
                },
            },
        )
        workflow_1 = Workflow.objects.get(id=response.data['id'])

        response = api_client.post(
            f'/templates/{template.id}/run',
            data={
                'name': 'Test workflow 2',
                'kickoff': {
                    field_template.api_name: user3.email,
                },
            },
        )
        workflow_2 = Workflow.objects.get(id=response.data['id'])

        task_template = template.tasks.first()
        mocker.patch(
            'src.processes.services.templates.'
            'integrations.TemplateIntegrationsService.template_updated',
        )

        # act
        response = api_client.put(
            f'/templates/{template.id}',
            data={
                'name': 'Template',
                'owners': [
                    {
                        'type': OwnerType.USER,
                        'source_id': user1.id,
                    },
                    {
                        'type': OwnerType.USER,
                        'source_id': user2.id,
                    },
                    {
                        'type': OwnerType.USER,
                        'source_id': user3.id,
                    },
                ],
                'is_active': True,
                'kickoff': {
                    'fields': [
                        {
                            'id': field_template.id,
                            'type': field_template.type,
                            'order': field_template.order,
                            'name': field_template.name,
                            'is_required': field_template.is_required,
                            'api_name': field_template.api_name,
                        },
                    ],
                },
                'tasks': [
                    {
                        'id': task_template.id,
                        'number': task_template.number,
                        'name': task_template.name,
                        'api_name': task_template.api_name,
                        'raw_performers': [
                            {
                                'type': PerformerType.WORKFLOW_STARTER,
                                'source_id': None,
                                'api_name': 'raw-performer-1',
                            },
                            {
                                'type': PerformerType.FIELD,
                                'source_id':  field_template.api_name,
                                'api_name': 'raw-performer-2',
                            },
                        ],
                    },
                ],
            },
        )

        # assert
        assert response.status_code == 200
        workflow_1.refresh_from_db()
        workflow_1_task = workflow_1.tasks.first()
        assert workflow_1_task.raw_performers.count() == 2
        assert workflow_1_task.performers.count() == 2
        assert workflow_1_task.performers.first().id == user1.id
        assert workflow_1_task.performers.last().id == user2.id

        workflow_2.refresh_from_db()
        workflow_2_task = workflow_2.tasks.first()
        assert workflow_2_task.raw_performers.count() == 2
        assert workflow_2_task.performers.count() == 2
        assert workflow_2_task.performers.first().id == user1.id
        assert workflow_2_task.performers.last().id == user3.id

    def test_update__get_default_performer_type_field__ok(
        self,
        mocker,
        api_client,
    ):
        """ For bug case when after template editing
            - workflow updates and their tasks lose performers.
            In this case need return default performer """

        # arrange
        # 1. Create workflow with two tasks
        user = create_test_user()
        api_client.token_authenticate(user)

        template = create_test_template(
            user=user,
            tasks_count=2,
            is_active=True,
        )
        response = api_client.post(
            f'/templates/{template.id}/run',
            data={
                'name': 'Test workflow',
            },
        )
        workflow = Workflow.objects.get(id=response.data['id'])

        # 2. Add user-field to kickoff and second task as field performer
        field_template = FieldTemplate.objects.create(
            name="performer",
            type=FieldType.USER,
            is_required=True,
            kickoff=template.kickoff_instance,
            template=template,
        )
        task_template_1 = template.tasks.first()
        task_template_2 = template.tasks.last()
        mocker.patch(
            'src.processes.services.templates.'
            'integrations.TemplateIntegrationsService.template_updated',
        )

        api_client.put(
            f"/templates/{template.id}",
            data={
                'name': 'Template',
                'owners': [
                    {
                        'type': OwnerType.USER,
                        'source_id': user.id,
                    },
                ],
                'kickoff': {
                    'fields': [
                        {
                            'id': field_template.id,
                            'type': field_template.type,
                            'order': field_template.order,
                            'name': field_template.name,
                            'is_required': field_template.is_required,
                            'api_name': field_template.api_name,
                        },
                    ],
                },
                'tasks': [
                    {
                        'id': task_template_1.id,
                        'number': task_template_1.number,
                        'name': task_template_1.name,
                        'raw_performers': [
                            {
                                'type': PerformerType.USER,
                                'source_id': user.id,
                                'api_name': 'raw-performer-1',
                            },
                        ],
                    },
                    {
                        'id': task_template_2.id,
                        'number': task_template_2.number,
                        'name': task_template_2.name,
                        'raw_performers': [
                            {
                                'type': PerformerType.FIELD,
                                'source_id': field_template.api_name,
                                'api_name': 'raw-performer-2',
                            },
                        ],
                    },
                ],
            },
        )
        send_new_task_notification_mock = mocker.patch(
            'src.notifications.tasks'
            '.send_new_task_notification.delay',
        )

        # act
        workflow.refresh_from_db()
        task_1 = workflow.tasks.get(number=1)
        response_complete = api_client.post(f'/v2/tasks/{task_1.id}/complete')
        workflow.refresh_from_db()
        task_2 = workflow.tasks.get(number=2)

        # assert
        assert response_complete.status_code == 200
        assert task_2.status == TaskStatus.ACTIVE
        assert task_2.performers.count() == 1
        assert task_2.performers.first().id == user.id
        send_new_task_notification_mock.assert_called_once()

    def test_update__active_task_due_date_updated__ok(
        self,
        mocker,
        api_client,
    ):

        # arrange
        user = create_test_user()
        api_client.token_authenticate(user)
        workflow = create_test_workflow(user, tasks_count=1)

        template = workflow.template
        template_task = template.tasks.first()
        RawDueDateTemplate.objects.create(
            task=template_task,
            template=template,
            duration=timedelta(days=1),
            rule=DueDateRule.AFTER_TASK_STARTED,
            source_id=template_task.api_name,
        )
        version_service = TemplateVersioningService(
            schema=TemplateSchemaV1,
        )
        version = version_service.save(template=workflow.template)
        version_dict = version.data
        version_service = WorkflowUpdateVersionService(
            is_superuser=False,
            auth_type=AuthTokenType.USER,
            instance=workflow,
            user=user,
        )

        # act
        version_service.update_from_version(
            data=version_dict,
            version=1,
        )

        # assert
        task = workflow.tasks.get(number=1)
        due_date = task.date_first_started + timedelta(days=1)
        assert task.due_date == due_date

    def test_update__change_task_api_name__create_new(
        self,
        mocker,
        api_client,
    ):
        # arrange
        user = create_test_user()
        api_client.token_authenticate(user)

        template = create_test_template(
            user=user,
            tasks_count=1,
            is_active=True,
        )
        task = template.tasks.first()
        FieldTemplate.objects.create(
            name='Name',
            api_name='name',
            type=FieldType.USER,
            kickoff=template.kickoff_instance,
            is_required=True,
            template=template,
        )
        mocker.patch(
            'src.processes.services.templates.'
            'integrations.TemplateIntegrationsService.template_updated',
        )
        new_task_api_name = 'new-api-name'

        request_data = {
            'id': task.id,
            'number': 1,
            'api_name': new_task_api_name,
            'name': 'Changed first step',
            'description': 'Changed desc',
            'require_completion_by_all': True,
            'raw_performers': [
                {
                    'type': PerformerType.USER,
                    'source_id': user.id,
                    'api_name': 'raw-performer-3',
                },
                {
                    'type': PerformerType.WORKFLOW_STARTER,
                    'source_id': None,
                    'api_name': 'raw-performer-4',
                },
                {
                    'type': PerformerType.FIELD,
                    'source_id': 'user-field-2',
                    'api_name': 'raw-performer-5',
                },
            ],
            'delay': None,
            'fields': [],
        }

        # act
        response = api_client.put(
            path=f'/templates/{template.id}',
            data={
                'id': template.id,
                'name': template.name,
                'is_active': True,
                'owners': [
                    {
                        'type': OwnerType.USER,
                        'source_id': user.id,
                    },
                ],
                'kickoff': {
                    'fields': [
                        {
                            'order': 2,
                            'is_required': True,
                            'name': 'First step new performer',
                            'type': FieldType.USER,
                            'api_name': 'user-field-2',
                        },
                    ],
                },
                'tasks': [request_data],
            },
        )

        # assert
        assert response.status_code == 200
        assert response.data['tasks'][0]['api_name'] == new_task_api_name

    def test_update__unspecified_task_api_name__create_new(
        self,
        mocker,
        api_client,
    ):
        # arrange
        user = create_test_user()
        api_client.token_authenticate(user)

        template = create_test_template(
            user=user,
            tasks_count=1,
            is_active=True,
        )
        kickoff = template.kickoff_instance
        task = template.tasks.first()
        FieldTemplate.objects.create(
            name='Name',
            api_name='name',
            type=FieldType.USER,
            kickoff=kickoff,
            is_required=True,
            template=template,
        )
        mocker.patch(
            'src.processes.services.templates.'
            'integrations.TemplateIntegrationsService.template_updated',
        )

        # act
        response = api_client.put(
            path=f'/templates/{template.id}',
            data={
                'id': template.id,
                'name': template.name,
                'is_active': True,
                'owners': [
                    {
                        'type': OwnerType.USER,
                        'source_id': user.id,
                    },
                ],
                'kickoff': {},
                'tasks': [
                    {
                        'id': task.id,
                        'number': task.number,
                        'name': task.name,
                        'raw_performers': [
                            {
                                'type': PerformerType.USER,
                                'source_id': user.id,
                                'api_name': 'raw-performer-3',
                            },
                        ],
                        'fields': [],
                    },
                ],
            },
        )

        # assert
        assert response.status_code == 200
        assert response.data['tasks'][0]['api_name']

    def test_update__due_in__event_fired(
        self,
        mocker,
        api_client,
    ):
        # arrange
        user = create_test_user()
        api_client.token_authenticate(user)
        duration = '10:00:00'

        template = create_test_template(
            user=user,
            tasks_count=1,
            is_active=True,
        )
        task = template.tasks.first()
        mocker.patch(
            'src.processes.services.templates.'
            'integrations.TemplateIntegrationsService.template_updated',
        )
        analysis_mock = mocker.patch(
            'src.processes.serializers.templates.task.'
            'AnalyticService.templates_task_due_date_created',
        )

        # act
        response = api_client.put(
            path=f'/templates/{template.id}',
            data={
                'id': template.id,
                'name': template.name,
                'is_active': True,
                'owners': [
                    {
                        'type': OwnerType.USER,
                        'source_id': user.id,
                    },
                ],
                'kickoff': {},
                'tasks': [
                    {
                        'id': task.id,
                        'number': 1,
                        'name': 'Changed first step',
                        'raw_performers': [
                            {
                                'type': PerformerType.USER,
                                'source_id': user.id,
                                'api_name': 'raw-performer-3',
                            },
                        ],
                        'raw_due_date': {
                            'api_name': 'raw-due-date-bwybf0',
                            'rule': 'after task started',
                            'duration_months': 0,
                            'duration': duration,
                            'source_id': task.api_name,
                        },
                        'api_name': task.api_name,
                        'fields': [],
                        'conditions': [],
                    },
                ],
            },
        )

        # assert
        assert response.status_code == 200
        task_data = response.data['tasks'][0]
        assert task_data['raw_due_date']['duration'] == duration
        analysis_mock.assert_called_once_with(
            user=user,
            template=template,
            task=template.tasks.first(),
            auth_type=AuthTokenType.USER,
            is_superuser=False,
        )

    def test_update__draft_due_in__event_not_fired(
        self,
        mocker,
        api_client,
    ):
        # arrange
        analysis_mock = mocker.patch(
            'src.processes.serializers.templates.task.'
            'AnalyticService.templates_task_due_date_created',
        )
        user = create_test_user()
        api_client.token_authenticate(user)
        duration = '10:00:00'

        # act
        response = api_client.post(
            path='/templates',
            data={
                'name': 'Template',
                'owners': [
                    {
                        'type': OwnerType.USER,
                        'source_id': user.id,
                    },
                ],
                'kickoff': {},
                'is_active': False,
                'tasks': [
                    {
                        'number': 1,
                        'name': 'First step',
                        'api_name': 'task-1',
                        'raw_performers': [
                            {
                                'type': PerformerType.USER,
                                'source_id': user.id,
                                'api_name': 'raw-performer-3',
                            },
                        ],
                        'raw_due_date': {
                            'api_name': 'raw-due-date-bwybf0',
                            'rule': 'after task started',
                            'duration_months': 0,
                            'duration': duration,
                            'source_id': 'task-1',
                        },
                    },
                ],
            },
        )

        # assert
        assert response.status_code == 200
        task_data = response.data['tasks'][0]
        assert task_data['raw_due_date']['duration'] == duration
        analysis_mock.assert_not_called()

    def test_update__with_equal_api_names__save_last(
        self,
        mocker,
        api_client,
    ):

        # arrange
        user = create_test_user()
        step_name = 'Second step'
        api_client.token_authenticate(user)

        template = create_test_template(
            user=user,
            tasks_count=1,
            is_active=True,
        )
        task = template.tasks.first()
        mocker.patch(
            'src.processes.services.templates.'
            'integrations.TemplateIntegrationsService.template_updated',
        )

        # act
        response = api_client.put(
            path=f'/templates/{template.id}',
            data={
                'id': template.id,
                'name': template.name,
                'is_active': True,
                'owners': [
                    {
                        'type': OwnerType.USER,
                        'source_id': user.id,
                    },
                ],
                'kickoff': {},
                'tasks': [
                    {
                        'id': task.id,
                        'number': task.number,
                        'name': task.name,
                        'api_name': task.api_name,
                        'description': task.description,
                        'require_completion_by_all': (
                            task.require_completion_by_all
                        ),
                        'raw_performers': [
                            {
                                'type': PerformerType.USER,
                                'source_id': user.id,
                                'api_name': 'raw-performer-3',
                            },
                        ],
                    },
                    {
                        'number': 2,
                        'name': step_name,
                        'api_name': task.api_name,
                        'raw_performers': [
                            {
                                'type': PerformerType.USER,
                                'source_id': user.id,
                                'api_name': 'raw-performer-3',
                            },
                        ],
                    },
                ],
            },
        )

        # assert
        assert response.status_code == 200
        assert len(response.data['tasks']) == 1
        response_data = response.data['tasks'][0]
        assert response_data['name'] == step_name
        assert response_data['number'] == 2
        assert response_data['api_name'] == task.api_name

    def test_update__set_revert_task__ok(
        self,
        mocker,
        api_client,
    ):

        # arrange
        user = create_test_user()
        api_client.token_authenticate(user)
        template = create_test_template(
            user=user,
            tasks_count=2,
            is_active=True,
        )
        task_1 = template.tasks.get(number=1)
        task_2 = template.tasks.get(number=2)

        mocker.patch(
            'src.processes.services.templates.'
            'integrations.TemplateIntegrationsService.template_updated',
        )

        request_data = [
            {
                'id': task_1.id,
                'number': task_1.number,
                'name': task_1.name,
                'api_name': task_1.api_name,
                'raw_performers': [
                    {
                        'type': PerformerType.USER,
                        'source_id': str(user.id),
                    },
                ],
            },
            {
                'id': task_2.id,
                'number': task_2.number,
                'name': task_2.name,
                'api_name': task_2.api_name,
                'revert_task': task_1.api_name,
                'raw_performers': [
                    {
                        'type': PerformerType.USER,
                        'source_id': str(user.id),
                    },
                ],
                'conditions': [
                    {
                        'order': 1,
                        'action': ConditionAction.START_TASK,
                        'rules': [
                            {
                                'predicates': [
                                    {
                                      'field_type': PredicateType.TASK,
                                      'operator': PredicateOperator.COMPLETED,
                                      'field': task_1.api_name,
                                      'value': None,
                                    },
                                ],
                            },
                        ],
                    },
                ],
            },
        ]

        # act
        response = api_client.put(
            path=f'/templates/{template.id}',
            data={
                'id': template.id,
                'name': template.name,
                'is_active': True,
                'owners': [
                    {
                        'type': OwnerType.USER,
                        'source_id': user.id,
                    },
                ],
                'kickoff': {},
                'tasks': request_data,
            },
        )

        # assert
        assert response.status_code == 200
        response_data = response.data['tasks'][1]
        assert response_data['revert_task'] == task_1.api_name
        task_2.refresh_from_db()
        assert task_2.revert_task == task_1.api_name

    def test_update__delete_revert_task__ok(
        self,
        mocker,
        api_client,
    ):

        # arrange
        user = create_test_user()
        api_client.token_authenticate(user)
        template = create_test_template(
            user=user,
            tasks_count=2,
            is_active=True,
        )
        task_1 = template.tasks.get(number=1)
        task_2 = template.tasks.get(number=2)
        task_2.revert_task = task_1.api_name
        task_2.save()

        mocker.patch(
            'src.processes.services.templates.'
            'integrations.TemplateIntegrationsService.template_updated',
        )

        request_data = [
            {
                'id': task_1.id,
                'number': task_1.number,
                'name': task_1.name,
                'api_name': task_1.api_name,
                'raw_performers': [
                    {
                        'type': PerformerType.USER,
                        'source_id': str(user.id),
                    },
                ],
            },
            {
                'id': task_2.id,
                'number': task_2.number,
                'name': task_2.name,
                'api_name': task_2.api_name,
                'revert_task': None,
                'raw_performers': [
                    {
                        'type': PerformerType.USER,
                        'source_id': str(user.id),
                    },
                ],
            },
        ]

        # act
        response = api_client.put(
            path=f'/templates/{template.id}',
            data={
                'id': template.id,
                'name': template.name,
                'is_active': True,
                'owners': [
                    {
                        'type': OwnerType.USER,
                        'source_id': user.id,
                    },
                ],
                'kickoff': {},
                'tasks': request_data,
            },
        )

        # assert
        assert response.status_code == 200
        response_data = response.data['tasks'][1]
        assert response_data['revert_task'] is None
        task_2.refresh_from_db()
        assert task_2.revert_task is None

    def test_update__not_existent_revert_task__validation_error(
        self,
        mocker,
        api_client,
    ):

        # arrange
        user = create_test_user()
        api_client.token_authenticate(user)
        template = create_test_template(
            user=user,
            tasks_count=2,
            is_active=True,
        )
        task_1 = template.tasks.get(number=1)
        task_2 = template.tasks.get(number=2)

        mocker.patch(
            'src.processes.services.templates.'
            'integrations.TemplateIntegrationsService.template_updated',
        )
        not_existent_api_name = 'task-not_existent_api_name'

        request_data = [
            {
                'id': task_1.id,
                'number': task_1.number,
                'name': task_1.name,
                'api_name': task_1.api_name,
                'raw_performers': [
                    {
                        'type': PerformerType.USER,
                        'source_id': str(user.id),
                    },
                ],
            },
            {
                'id': task_2.id,
                'number': task_2.number,
                'name': task_2.name,
                'api_name': task_2.api_name,
                'revert_task': not_existent_api_name,
                'raw_performers': [
                    {
                        'type': PerformerType.USER,
                        'source_id': str(user.id),
                    },
                ],
            },
        ]

        # act
        response = api_client.put(
            path=f'/templates/{template.id}',
            data={
                'id': template.id,
                'name': template.name,
                'is_active': True,
                'owners': [
                    {
                        'type': OwnerType.USER,
                        'source_id': user.id,
                    },
                ],
                'kickoff': {},
                'tasks': request_data,
            },
        )

        # assert
        assert response.status_code == 400
        message = messages.MSG_PT_0059(
            name=task_2.name,
            api_name=not_existent_api_name,
        )
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['message'] == message
        assert response.data['details']['reason'] == message
        assert response.data['details']['api_name'] == task_2.api_name

    def test_update__revert_task_to_itself__validation_error(
        self,
        mocker,
        api_client,
    ):

        # arrange
        user = create_test_user()
        api_client.token_authenticate(user)
        template = create_test_template(
            user=user,
            tasks_count=1,
            is_active=True,
        )
        task = template.tasks.get(number=1)

        mocker.patch(
            'src.processes.services.templates.'
            'integrations.TemplateIntegrationsService.template_updated',
        )
        request_data = [
            {
                'id': task.id,
                'number': task.number,
                'name': task.name,
                'api_name': task.api_name,
                'revert_task': task.api_name,
                'raw_performers': [
                    {
                        'type': PerformerType.USER,
                        'source_id': str(user.id),
                    },
                ],
            },
        ]

        # act
        response = api_client.put(
            path=f'/templates/{template.id}',
            data={
                'id': template.id,
                'name': template.name,
                'is_active': True,
                'owners': [
                    {
                        'type': OwnerType.USER,
                        'source_id': user.id,
                    },
                ],
                'kickoff': {},
                'tasks': request_data,
            },
        )

        # assert
        assert response.status_code == 400
        message = messages.MSG_PT_0060(name=task.name)
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['message'] == message
        assert response.data['details']['reason'] == message
        assert response.data['details']['api_name'] == task.api_name


class TestUpdateTemplateRawPerformer:

    def test_update__add_raw_performers__ok(
        self,
        mocker,
        api_client,
    ):

        # arrange
        account = create_test_account()
        user = create_test_user(account=account)
        user2 = create_test_user(
            email='test2@pneumatic.app',
            account=account,
        )
        api_client.token_authenticate(user)

        template = create_test_template(
            user=user,
            tasks_count=1,
            is_active=True,
        )
        task = template.tasks.first()
        raw_performer = task.raw_performers.first()
        mocker.patch(
            'src.processes.services.templates.'
            'integrations.TemplateIntegrationsService.template_updated',
        )

        # act
        response = api_client.put(
            path=f'/templates/{template.id}',
            data={
                'id': template.id,
                'name': template.name,
                'is_active': True,
                'owners': [
                    {
                        'type': OwnerType.USER,
                        'source_id': user.id,
                    },
                    {
                        'type': OwnerType.USER,
                        'source_id': user2.id,
                    },
                ],
                'kickoff': {
                    'fields': [
                        {
                            'order': 1,
                            'is_required': True,
                            'name': 'First step performer',
                            'type': FieldType.USER,
                            'api_name': 'user-field-1',
                        },
                    ],
                },
                'tasks': [
                    {
                        'id': task.id,
                        'number': task.number,
                        'name': task.name,
                        'api_name': task.api_name,
                        'description': task.description,
                        'raw_performers': [
                            {
                                'id': raw_performer.id,
                                'type': raw_performer.type,
                                'source_id': raw_performer.user_id,
                                'api_name': 'raw-performer-3',
                            },
                            {
                                'type': PerformerType.FIELD,
                                'source_id': 'user-field-1',
                                'api_name': 'raw-performer-4',
                            },
                        ],
                    },
                ],
            },
        )

        # assert
        assert response.status_code == 200
        response_data = response.data['tasks'][0]
        assert len(response_data['raw_performers']) == 2

        task.refresh_from_db()
        raw_performer = task.raw_performers.first()
        assert task.raw_performers.all().count() == 2
        raw_performer_1 = task.raw_performers.get(user_id=user.id)
        assert raw_performer_1.id == raw_performer.id
        assert raw_performer_1.type == PerformerType.USER
        raw_performer_2 = task.raw_performers.get(
            field__api_name='user-field-1',
        )
        assert raw_performer_2.type == PerformerType.FIELD

    def test_update__change_raw_performers__ok(
        self,
        mocker,
        api_client,
    ):

        # arrange
        account = create_test_account()
        user = create_test_user(account=account)
        user2 = create_test_user(
            email='test2@pneumatic.app',
            account=account,
        )
        api_client.token_authenticate(user)

        template = create_test_template(
            user=user,
            tasks_count=1,
            is_active=True,
        )
        task = template.tasks.first()
        task.add_raw_performer(user)

        mocker.patch(
            'src.processes.services.templates.'
            'integrations.TemplateIntegrationsService.template_updated',
        )

        # act
        response = api_client.put(
            path=f'/templates/{template.id}',
            data={
                'id': template.id,
                'name': template.name,
                'is_active': True,
                'owners': [
                    {
                        'type': OwnerType.USER,
                        'source_id': user.id,
                    },
                    {
                        'type': OwnerType.USER,
                        'source_id': user2.id,
                    },
                ],
                'kickoff': {
                    'fields': [
                        {
                            'order': 1,
                            'is_required': True,
                            'name': 'First step performer',
                            'type': FieldType.USER,
                            'api_name': 'user-field-1',
                        },
                    ],
                },
                'tasks': [
                    {
                        'id': task.id,
                        'number': 1,
                        'name': 'Changed first step',
                        'api_name': task.api_name,
                        'description': 'Changed desc',
                        'raw_performers': [
                            {
                                'type': PerformerType.WORKFLOW_STARTER,
                                'source_id': None,
                                'api_name': 'raw-performer-1',
                            },
                            {
                                'type': PerformerType.USER,
                                'source_id': user2.id,
                                'api_name': 'raw-performer-2',
                            },
                            {
                                'type': PerformerType.FIELD,
                                'source_id': 'user-field-1',
                                'api_name': 'raw-performer-3',
                            },
                        ],
                        'fields': [],
                    },
                ],
            },
        )

        # assert
        assert response.status_code == 200
        assert len(response.data['tasks']) == 1
        response_data = response.data['tasks'][0]
        assert len(response_data['raw_performers']) == 3

        task.refresh_from_db()
        raw_performers = task.raw_performers.all()
        assert raw_performers.count() == 3
        raw_performer_1 = raw_performers.get(type=PerformerType.USER)
        assert raw_performer_1.user_id == user2.id
        raw_performer_2 = raw_performers.get(type=PerformerType.FIELD)
        assert raw_performer_2.field.api_name == 'user-field-1'
        assert raw_performers.get(
            type=PerformerType.WORKFLOW_STARTER,
        )

    def test_update__with_equal_api_names__save_last(
        self,
        mocker,
        api_client,
    ):

        # arrange
        account = create_test_account()
        user = create_test_user(account=account)
        user2 = create_test_user(
            email='test2@pneumatic.app',
            account=account,
        )
        api_client.token_authenticate(user)

        template = create_test_template(
            user=user,
            tasks_count=1,
            is_active=True,
        )
        task = template.tasks.first()

        performer = task.add_raw_performer(user)
        mocker.patch(
            'src.processes.services.templates.'
            'integrations.TemplateIntegrationsService.template_updated',
        )

        # act
        response = api_client.put(
            path=f'/templates/{template.id}',
            data={
                'id': template.id,
                'name': template.name,
                'is_active': True,
                'owners': [
                    {
                        'type': OwnerType.USER,
                        'source_id': user.id,
                    },
                    {
                        'type': OwnerType.USER,
                        'source_id': user2.id,
                    },
                ],
                'kickoff': {},
                'tasks': [
                    {
                        'id': task.id,
                        'number': 1,
                        'name': 'Changed first step',
                        'api_name': task.api_name,
                        'description': 'Changed desc',
                        'raw_performers': [
                            {
                                'type': PerformerType.USER,
                                'source_id': user.id,
                                'api_name': performer.api_name,
                            },
                            {
                                'type': PerformerType.USER,
                                'source_id': user2.id,
                                'api_name': performer.api_name,
                            },

                        ],
                        'fields': [],
                    },
                ],
            },
        )

        # assert
        assert response.status_code == 200
        assert len(response.data['tasks']) == 1
        response_data = response.data['tasks'][0]
        assert len(response_data['raw_performers']) == 1

        task.refresh_from_db()
        assert task.raw_performers.all().count() == 1
        raw_performer = task.raw_performers.first()
        assert raw_performer.type == PerformerType.USER
        assert raw_performer.user.id == user2.id
        assert raw_performer.api_name == raw_performer.api_name

    def test_update__with_equal_api_names__validation_error(
        self,
        mocker,
        api_client,
    ):

        # arrange
        account = create_test_account()
        user = create_test_user(account=account)
        user2 = create_test_user(
            email='test2@pneumatic.app',
            account=account,
        )
        api_client.token_authenticate(user)
        step_name = 'Changed last step'
        template = create_test_template(
            user=user,
            tasks_count=2,
            is_active=True,
        )
        task_first = template.tasks.first()
        task_last = template.tasks.last()
        raw_performer = task_first.add_raw_performer(user)
        task_last.add_raw_performer(user)
        mocker.patch(
            'src.processes.services.templates.'
            'integrations.TemplateIntegrationsService.template_updated',
        )

        # act
        response = api_client.put(
            path=f'/templates/{template.id}',
            data={
                'id': template.id,
                'name': template.name,
                'is_active': True,
                'owners': [
                    {
                        'type': OwnerType.USER,
                        'source_id': user.id,
                    },
                    {
                        'type': OwnerType.USER,
                        'source_id': user2.id,
                    },
                ],
                'kickoff': {
                    'fields': [
                        {
                            'order': 1,
                            'is_required': True,
                            'name': 'First step performer',
                            'type': FieldType.USER,
                            'api_name': 'user-field-1',
                        },
                    ],
                },
                'tasks': [
                    {
                        'id': task_first.id,
                        'number': 1,
                        'name': 'Changed first step',
                        'api_name': task_first.api_name,
                        'description': 'Changed desc first',
                        'raw_performers': [
                            {
                                'type': PerformerType.USER,
                                'source_id': user.id,
                                'api_name': raw_performer.api_name,
                            },
                        ],
                    },
                    {
                        'id': task_last.id,
                        'number': 2,
                        'name': 'Changed last step',
                        'api_name': task_last.api_name,
                        'description': 'Changed desc last',
                        'raw_performers': [
                            {
                                'type': PerformerType.USER,
                                'source_id': user.id,
                                'api_name': raw_performer.api_name,
                            },
                        ],
                    },
                ],
            },
        )

        assert response.status_code == 400
        message = messages.MSG_PT_0056(
            name=step_name,
            api_name=raw_performer.api_name,
        )
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['message'] == message
        assert response.data['details']['reason'] == message
        assert response.data['details']['api_name'] == raw_performer.api_name

    def test_update__delete_raw_performers__ok(
        self,
        mocker,
        api_client,
    ):

        # arrange
        account = create_test_account()
        user = create_test_user(account=account)
        user2 = create_test_user(
            email='test2@pneumatic.app',
            account=account,
        )
        api_client.token_authenticate(user)

        template = create_test_template(
            user=user,
            tasks_count=1,
            is_active=True,
        )
        task = template.tasks.first()
        field_template = FieldTemplate.objects.create(
            name='performer',
            type=FieldType.USER,
            is_required=True,
            kickoff=template.kickoff_instance,
            template=template,
        )
        task.add_raw_performer(user)
        task.add_raw_performer(
            performer_type=PerformerType.FIELD,
            field=field_template,
        )
        task.add_raw_performer(
            performer_type=PerformerType.WORKFLOW_STARTER,
        )
        mocker.patch(
            'src.processes.services.templates.'
            'integrations.TemplateIntegrationsService.template_updated',
        )

        # act
        response = api_client.put(
            path=f'/templates/{template.id}',
            data={
                'id': template.id,
                'name': template.name,
                'is_active': True,
                'owners': [
                    {
                        'type': OwnerType.USER,
                        'source_id': user.id,
                    },
                    {
                        'type': OwnerType.USER,
                        'source_id': user2.id,
                    },
                ],
                'kickoff': {
                    'fields': [
                        {
                            'id': field_template.id,
                            'order': field_template.order,
                            'is_required': field_template.is_required,
                            'name': field_template.name,
                            'type': field_template.type,
                            'api_name': field_template.api_name,
                        },
                    ],
                },
                'tasks': [
                    {
                        'id': task.id,
                        'number': 1,
                        'name': 'Changed first step',
                        'api_name': task.api_name,
                        'description': 'Changed desc',
                        'require_completion_by_all': True,
                        'raw_performers': [
                            {
                                'type': PerformerType.USER,
                                'source_id': user2.id,
                                'api_name': 'raw-performer-3',
                            },
                        ],
                        'delay': None,
                        'raw_due_date': {
                            'rule': 'after task started',
                            'duration_months': 0,
                            'duration': '01:00:00',
                            'source_id': task.api_name,
                        },
                        'fields': [],
                    },
                ],
            },
        )

        # assert
        assert response.status_code == 200
        data = response.json()
        assert len(data['tasks']) == 1

        response_data = data['tasks'][0]
        assert len(response_data['raw_performers']) == 1
        raw_performer = response_data['raw_performers'][0]
        assert raw_performer['type'] == PerformerType.USER
        assert raw_performer['source_id'] == str(user2.id)
        task.refresh_from_db()
        assert task.raw_performers.all().count() == 1
        raw_performer = task.raw_performers.first()
        assert raw_performer.type == PerformerType.USER
        assert raw_performer.user.id == user2.id

    def test_update__delete_similar_raw_performer_performer_not_deleted__ok(
        self,
        mocker,
        api_client,
    ):

        # arrange
        account = create_test_account()
        user = create_test_user(account=account)
        api_client.token_authenticate(user)

        template = create_test_template(
            user=user,
            tasks_count=1,
            is_active=True,
        )
        task_template = template.tasks.first()
        field_template = FieldTemplate.objects.create(
            name='performer',
            type=FieldType.USER,
            is_required=True,
            kickoff=template.kickoff_instance,
            template=template,
        )
        raw_performer_1 = task_template.raw_performers.first()
        task_template.add_raw_performer(
            performer_type=PerformerType.FIELD,
            field=field_template,
        )
        task_template.add_raw_performer(
            performer_type=PerformerType.WORKFLOW_STARTER,
        )
        response = api_client.post(
            f'/templates/{template.id}/run',
            data={
                'name': 'Test template',
                'kickoff': {
                    field_template.api_name: user.email,
                },
            },
        )
        workflow = Workflow.objects.get(id=response.data['id'])
        mocker.patch(
            'src.processes.services.templates.'
            'integrations.TemplateIntegrationsService.template_updated',
        )

        # act
        response = api_client.put(
            path=f'/templates/{template.id}',
            data={
                'id': template.id,
                'name': template.name,
                'is_active': template.is_active,
                'owners': [
                    {
                        'type': OwnerType.USER,
                        'source_id': user.id,
                    },
                ],
                'kickoff': {
                    'fields': [],
                },
                'tasks': [
                    {
                        'id': task_template.id,
                        'number': task_template.number,
                        'name': task_template.name,
                        'api_name': task_template.api_name,
                        'raw_performers': [
                            {
                                'id': raw_performer_1.id,
                                'type': raw_performer_1.type,
                                'source_id': raw_performer_1.user_id,
                                'api_name': 'raw-performer-3',
                            },
                        ],
                    },
                ],
            },
        )

        # assert
        assert response.status_code == 200
        task = workflow.tasks.first()
        assert task.raw_performers.count() == 1
        assert task.performers.count() == 1
        assert task.performers.first().id == user.id

    def test_update__type_workflow_starter_public_template__validation_error(
        self,
        mocker,
        api_client,
    ):
        # arrange
        user = create_test_user()
        template = create_test_template(
            user=user,
            is_active=True,
            is_public=True,
            tasks_count=1,
        )
        api_client.token_authenticate(user)
        task = template.tasks.first()
        mocker.patch(
            'src.processes.services.templates.'
            'integrations.TemplateIntegrationsService.template_updated',
        )

        # act
        response = api_client.put(
            path=f'/templates/{template.id}',
            data={
                'id': template.id,
                'name': template.name,
                'is_active': True,
                'owners': [
                    {
                        'type': OwnerType.USER,
                        'source_id': user.id,
                    },
                ],
                'kickoff': {},
                'tasks': [
                    {
                        'id': task.id,
                        'number': task.number,
                        'name': task.name,
                        'api_name': task.api_name,
                        'description': task.description,
                        'raw_performers': [
                            {
                                'type': PerformerType.WORKFLOW_STARTER,
                                'source_id': None,
                                'api_name': 'raw-performer-3',
                            },
                        ],
                    },
                ],
            },
        )

        # assert
        assert response.status_code == 400
        assert response.data['message'] == messages.MSG_PT_0035
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['details']['reason'] == messages.MSG_PT_0035
        assert response.data['details']['api_name'] == task.api_name
