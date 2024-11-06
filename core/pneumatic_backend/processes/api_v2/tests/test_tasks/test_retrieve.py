import pytest
from datetime import timedelta
from django.utils import timezone
from pneumatic_backend.accounts.enums import (
    BillingPlanType,
)
from pneumatic_backend.processes.models import (
    FieldTemplate,
    Delay,
    Workflow,
    Template,
    FieldTemplateSelection,
    TaskPerformer,
    Checklist,
    ChecklistSelection,
    ChecklistTemplate,
    ChecklistTemplateSelection,
    FileAttachment,
)
from pneumatic_backend.processes.tasks.update_workflow import update_workflows
from pneumatic_backend.processes.tests.fixtures import (
    create_test_user,
    create_test_workflow,
    create_test_template,
    create_test_account,
    create_test_guest
)
from pneumatic_backend.processes.api_v2.services.task.performers import (
    TaskPerformersService
)
from pneumatic_backend.authentication.enums import AuthTokenType
from pneumatic_backend.processes.enums import (
    PerformerType,
    FieldType,
    WorkflowStatus,
)
from pneumatic_backend.authentication.services import GuestJWTAuthService
from pneumatic_backend.processes.api_v2.services import WorkflowEventService
from pneumatic_backend.utils.dates import date_format


pytestmark = pytest.mark.django_db


class TestTaskView:

    def test_retrieve__ok(self, api_client, mocker):
        # arrange
        user = create_test_user()
        api_client.token_authenticate(user)
        workflow = create_test_workflow(user=user, tasks_count=1)
        task = workflow.tasks.get(number=1)
        task.due_date = task.date_first_started + timedelta(hours=24)
        task.save(update_fields=['due_date'])

        identify_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.views.task.TaskViewSet.'
            'identify'
        )
        group_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.views.task.TaskViewSet.'
            'group'
        )

        # act
        response = api_client.get(f'/v2/tasks/{task.id}')

        # assert
        assert response.status_code == 200
        task.refresh_from_db()
        assert response.data['id'] == task.id
        assert response.data['is_urgent'] is False
        assert response.data['date_started'] == (
            task.date_started.strftime(date_format)
        )
        assert response.data['date_started_tsp'] == (
            task.date_started.timestamp()
        )
        assert response.data['date_completed'] is None
        assert response.data['date_completed_tsp'] is None
        assert response.data['due_date'] == (
            task.due_date.strftime(date_format)
        )
        assert response.data['due_date_tsp'] == task.due_date.timestamp()
        assert response.data['delay'] is None
        assert response.data['sub_workflows'] == []
        assert response.data['checklists'] == []

        workflow_data = response.data['workflow']
        assert workflow_data['id'] == workflow.id
        assert workflow_data['name'] == workflow.name
        assert workflow_data['status'] == workflow.status
        assert workflow_data['current_task'] == workflow.current_task
        assert workflow_data['template_name'] == workflow.get_template_name()
        assert workflow_data['date_completed'] is None
        assert workflow_data['date_completed_tsp'] is None

        identify_mock.assert_not_called()
        group_mock.assert_not_called()

    def test_retrieve__delayed__ok(self, api_client, mocker):
        # arrange
        mocker.patch(
            'pneumatic_backend.processes.api_v2.views.task.TaskViewSet.'
            'identify'
        )
        mocker.patch(
            'pneumatic_backend.processes.api_v2.views.task.TaskViewSet.group'
        )
        user = create_test_user()
        api_client.token_authenticate(user)
        workflow = create_test_workflow(user=user, tasks_count=1)
        task = workflow.current_task_instance
        delay = Delay.objects.create(
            duration=timedelta(days=2),
            task=task,
            start_date=timezone.now(),
        )

        # act
        response = api_client.get(f'/v2/tasks/{task.id}')

        # assert
        assert response.status_code == 200
        task.refresh_from_db()
        assert response.data['id'] == task.id
        assert response.data['is_urgent'] is False
        assert response.data['date_started'] == (
            task.date_started.strftime(date_format)
        )
        assert response.data['date_started_tsp'] == (
            task.date_started.timestamp()
        )
        assert response.data['date_completed'] is None
        assert response.data['date_completed_tsp'] is None
        assert response.data['due_date'] is None
        assert response.data['due_date_tsp'] is None
        delay_data = response.data['delay']
        assert delay_data['id'] == delay.id
        assert delay_data['duration'] == '2 00:00:00'
        assert delay_data['start_date'] == (
            delay.start_date.strftime(date_format)
        )
        assert delay_data['start_date_tsp'] == delay.start_date.timestamp()
        assert delay_data['estimated_end_date'] == (
            delay.estimated_end_date.strftime(date_format)
        )
        assert delay_data['estimated_end_date_tsp'] == (
            delay.estimated_end_date.timestamp()
        )
        assert delay_data['end_date'] is None
        assert delay_data['end_date_tsp'] is None
        workflow_data = response.data['workflow']
        assert workflow_data['id'] == workflow.id
        assert workflow_data['name'] == workflow.name
        assert workflow_data['status'] == workflow.status
        assert workflow_data['current_task'] == workflow.current_task
        assert workflow_data['template_name'] == workflow.get_template_name()
        assert workflow_data['date_completed'] is None
        assert workflow_data['date_completed_tsp'] is None

    def test_retrieve__workflow_member__ok(self, api_client):
        # arrange
        user = create_test_user()
        another_user = create_test_user(
            account=user.account,
            email='admin@test.test',
            is_account_owner=False
        )
        workflow = create_test_workflow(user)
        tasks = workflow.tasks.order_by('number')
        task = tasks[0]

        api_client.token_authenticate(another_user)

        # act
        response = api_client.get(f'/v2/tasks/{task.id}')

        # assert
        assert response.status_code == 200
        assert response.data['id'] == task.id
        assert response.data['workflow']['id'] == workflow.id

    def test_retrieve__account_owner_not_wf_member__ok(self, api_client):

        # arrange
        account = create_test_account(plan=BillingPlanType.PREMIUM)
        account_owner = create_test_user(account=account)
        user = create_test_user(account=account, email='t@t.t')
        workflow = create_test_workflow(user, tasks_count=1)
        task = workflow.tasks.first()
        api_client.token_authenticate(account_owner)

        # act
        response = api_client.get(f'/v2/tasks/{task.id}')

        # assert
        assert response.status_code == 200
        assert response.data['id'] == task.id

    def test_retrieve__admin_not_workflow_member__permission_denied(
        self,
        api_client
    ):
        # arrange
        user = create_test_user()
        user.account.billing_plan = BillingPlanType.PREMIUM
        user.account.save()
        another_user = create_test_user(
            account=user.account,
            email='admin@test.test',
            is_account_owner=False
        )
        workflow = create_test_workflow(user)
        workflow.members.remove(another_user)
        tasks = workflow.tasks.order_by('number')
        task = tasks[0]

        api_client.token_authenticate(another_user)

        # act
        response = api_client.get(f'/v2/tasks/{task.id}')

        # assert
        assert response.status_code == 403

    def test_retrieve__delayed_task__not_found(self, api_client):
        # arrange
        user = create_test_user()
        workflow = create_test_workflow(user)
        tasks = workflow.tasks.order_by('number')
        Delay.objects.create(
            task=tasks[1],
            duration=timedelta(seconds=1000),
        )

        api_client.token_authenticate(user)

        api_client.post(
            f'/workflows/{workflow.id}/task-complete',
            data={
                'task_id': tasks[0].id,
            }
        )
        workflow.refresh_from_db()
        task_one = workflow.current_task_instance

        # act
        response = api_client.get(f'/v2/tasks/{task_one.id}')

        # assert
        assert response.status_code == 404

    def test_retrieve__del_delay_before_current_task__found(
        self,
        mocker,
        api_client
    ):

        """ Caused by bug: https://my.pneumatic.app/workflows/11741"""

        # arrange
        user = create_test_user()
        api_client.token_authenticate(user)
        request_data = {
            'name': 'Template',
            'template_owners': [user.id],
            'is_active': True,
            'kickoff': {},
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
                    'delay': '00:10:00',
                    'raw_performers': [
                        {
                            'type': PerformerType.USER,
                            'source_id': user.id
                        }
                    ]
                }
            ]
        }
        response = api_client.post(
            path='/templates',
            data=request_data
        )
        template = Template.objects.get(id=response.data['id'])

        workflow = create_test_workflow(user, template=template)
        tasks = workflow.tasks.order_by('number')
        api_client.post(
            f'/workflows/{workflow.id}/task-complete',
            data={
                'task_id': tasks[0].id,
            }
        )
        workflow.refresh_from_db()
        task_one = workflow.current_task_instance

        template_data = api_client.get(
            f'/templates/{workflow.template_id}'
        ).data
        template_data['tasks'][1].pop('delay')
        mocker.patch(
            'pneumatic_backend.processes.api_v2.services.templates.'
            'integrations.TemplateIntegrationsService.template_updated'
        )

        api_client.put(
            f'/templates/{workflow.template_id}',
            data=template_data,
        )
        template.refresh_from_db()
        update_workflows(
            template_id=template.id,
            version=template.version,
            updated_by=user.id,
            is_superuser=False,
            auth_type=AuthTokenType.USER
        )

        # act
        response = api_client.get(f'/v2/tasks/{task_one.id}')

        # assert
        assert response.status_code == 200

    def test_retrieve__completed_task__ok(self, api_client):
        # arrange
        user = create_test_user()
        workflow = create_test_workflow(user)
        tasks = workflow.tasks.order_by('number')
        task = tasks[0]
        api_client.token_authenticate(user)

        api_client.post(
            f'/workflows/{workflow.id}/task-complete',
            data={
                'task_id': task.id,
            }
        )
        workflow.refresh_from_db()

        # act
        response = api_client.get(f'/v2/tasks/{task.id}')

        # assert
        assert response.status_code == 200
        task.refresh_from_db()
        assert response.data['date_started'] == (
            task.date_started.strftime(date_format)
        )
        assert response.data['date_started_tsp'] == (
            task.date_started.timestamp()
        )
        assert response.data['date_completed'] == (
            task.date_completed.strftime(date_format)
        )
        assert response.data['date_completed_tsp'] == (
            task.date_completed.timestamp()
        )

    def test_retrieve__user_completed_task__return_as_completed(
        self,
        api_client,
    ):
        """ https://trello.com/c/75aESAb0 """
        # arrange
        user = create_test_user()
        another_user = create_test_user(
            email='another_user@test.com',
            account=user.account,
        )
        workflow = create_test_workflow(user)
        task = workflow.tasks.order_by('number').first()
        task.require_completion_by_all = True
        task.save()
        raw_performer = task.add_raw_performer(another_user)
        task.update_performers(raw_performer)
        api_client.token_authenticate(user)

        api_client.post(
            f'/workflows/{workflow.id}/task-complete',
            data={
                'task_id': task.id,
            }
        )
        workflow.refresh_from_db()

        # act
        response = api_client.get(f'/v2/tasks/{task.id}')

        # assert
        task.refresh_from_db()
        assert response.status_code == 200
        assert response.data['is_completed'] is True
        assert task.is_completed is False

    def test_retrieve__revert_delayed_task__not_found(self, api_client):

        # arrange
        user = create_test_user()
        api_client.token_authenticate(user)
        workflow = create_test_workflow(
            user=user,
            tasks_count=2
        )
        tasks = workflow.tasks.order_by('number')
        first_task = tasks.first()
        second_task = tasks.last()
        Delay.objects.create(
            task=second_task,
            duration=timedelta(hours=1)
        )

        response1 = api_client.post(
            f'/workflows/{workflow.id}/task-complete',
            data={'task_id': first_task.id}
        )
        response2 = api_client.post(
            f'/workflows/{workflow.id}/task-complete',
            data={'task_id': second_task.id}
        )
        response3 = api_client.post(
            f'/workflows/{workflow.id}/task-revert',
        )
        workflow.refresh_from_db()
        current_task = workflow.current_task_instance

        # act
        response4 = api_client.get(f'/v2/tasks/{current_task.id}')

        # assert
        assert response1.status_code == 204
        assert response2.status_code == 400
        assert response3.status_code == 400
        assert response4.status_code == 404
        assert current_task.id == second_task.id

    def test_retrieve__reverted_task__ok(self, api_client):

        # arrange
        user = create_test_user()
        api_client.token_authenticate(user)
        workflow = create_test_workflow(
            user=user,
            tasks_count=2
        )
        task = workflow.current_task_instance
        second_task = task.next

        api_client.post(
            f'/workflows/{workflow.id}/task-complete',
            data={'task_id': task.id}
        )
        api_client.post(
            f'/workflows/{workflow.id}/task-revert',
        )
        workflow.refresh_from_db()

        # act
        response = api_client.get(f'/v2/tasks/{second_task.id}')

        # assert
        assert response.status_code == 200
        task.refresh_from_db()
        assert response.data['id'] == second_task.id
        assert response.data['date_started'] is None
        assert response.data['date_started_tsp'] is None
        assert response.data['date_completed'] is None
        assert response.data['date_completed_tsp'] is None
        assert response.data['due_date'] is None
        assert response.data['due_date_tsp'] is None
        workflow_data = response.data['workflow']
        assert workflow_data['id'] == workflow.id
        assert workflow_data['name'] == workflow.name
        assert workflow_data['status'] == workflow.status
        assert workflow_data['current_task'] == task.number
        assert workflow_data['template_name'] == workflow.get_template_name()
        assert workflow_data['date_completed'] is None
        assert workflow_data['date_completed_tsp'] is None

    def test_retrieve__deleted_performer__ok(self, api_client):

        # arrange
        user = create_test_user()
        user2 = create_test_user(email='t@t.t', account=user.account)
        api_client.token_authenticate(user)
        template = create_test_template(
            user=user,
            is_active=True,
            tasks_count=1
        )
        workflow = create_test_workflow(user, template)
        task = workflow.current_task_instance
        TaskPerformersService.create_performer(
            request_user=user,
            user_key=user2.id,
            task=task,
            run_actions=False,
            current_url='/page',
            is_superuser=False
        )
        TaskPerformersService.delete_performer(
            request_user=user,
            user_key=user2.id,
            task=task,
            run_actions=False
        )

        # act
        response = api_client.get(f'/v2/tasks/{task.id}')

        # assert
        assert response.status_code == 200
        assert response.data['id'] == task.id
        assert len(response.data['performers']) == 1
        assert response.data['performers'][0] == user.id

    def test_retrieve__get_performers_type_field__ok(
        self,
        api_client
    ):
        # arrange
        user = create_test_user()
        user2 = create_test_user(
            email='test2@pneumatic.app',
            account=user.account
        )
        api_client.token_authenticate(user)

        template = create_test_template(
            user=user,
            tasks_count=2,
            is_active=True
        )

        field_template = FieldTemplate.objects.create(
            name='First task performer',
            type=FieldType.USER,
            is_required=True,
            kickoff=template.kickoff_instance,
            template=template,
        )

        template_first_task = template.tasks.order_by(
            'number'
        ).first()
        template_first_task.delete_raw_performers()
        template_first_task.add_raw_performer(
            performer_type=PerformerType.FIELD,
            field=field_template
        )
        response = api_client.post(
            f'/templates/{template.id}/run',
            data={
                'name': 'Test template',
                'kickoff': {
                    field_template.api_name: user2.id
                }
            }
        )
        workflow_id = response.data['workflow_id']
        workflow = Workflow.objects.get(pk=workflow_id)
        first_task = workflow.current_task_instance

        # act
        response = api_client.get(f'/v2/tasks/{first_task.id}')
        performers = response.data['performers']

        # assert
        assert len(performers) == 1
        assert performers[0] == user2.id

    def test_retrieve__is_urgent__ok(self, api_client):

        # arrange
        user = create_test_user()
        api_client.token_authenticate(user)
        workflow = create_test_workflow(
            user=user,
            is_urgent=True,
            tasks_count=1
        )
        task = workflow.tasks.first()

        # act
        response = api_client.get(f'/v2/tasks/{task.id}')

        # assert
        assert response.status_code == 200
        assert response.data['id'] == task.id
        assert response.data['is_urgent'] is True

    def test_retrieve__field_user__ok(self, api_client):

        # arrange
        user = create_test_user()
        api_client.token_authenticate(user)
        template = create_test_template(
            user=user,
            is_active=True,
            tasks_count=1
        )
        template_task = template.tasks.first()
        FieldTemplate.objects.create(
            name='User Field',
            order=1,
            type=FieldType.USER,
            is_required=True,
            task=template_task,
            template=template,
        )
        response = api_client.post(
            path=f'/templates/{template.id}/run',
            data={
                'name': 'Test name',
            }
        )
        workflow = Workflow.objects.get(id=response.data['workflow_id'])
        task = workflow.tasks.first()

        field = task.output.first()
        field.value = user.get_full_name()
        field.user_id = user.id
        field.save(update_fields=['value', 'user_id'])

        # act
        response = api_client.get(f'/v2/tasks/{task.id}')

        # assert
        assert response.status_code == 200
        field_data = response.data['output'][0]
        assert field_data['id'] == field.id
        assert field_data['type'] == field.type
        assert field_data['is_required'] == field.is_required
        assert field_data['name'] == field.name
        assert field_data['description'] == field.description
        assert field_data['api_name'] == field.api_name
        # TODO Replace in https://my.pneumatic.app/workflows/18137/
        assert field_data['value'] == str(user.id)  # user.get_full_name()
        assert field_data['selections'] == []
        assert field_data['attachments'] == []
        assert field_data['order'] == field.order
        assert field_data['user_id'] == user.id

    def test_retrieve__field_with_selections__ok(self, api_client):

        # arrange
        user = create_test_user()
        api_client.token_authenticate(user)
        template = create_test_template(
            user=user,
            is_active=True,
            tasks_count=1
        )
        template_task = template.tasks.first()
        field_template = FieldTemplate.objects.create(
            name='User Field',
            order=1,
            type=FieldType.CHECKBOX,
            is_required=True,
            task=template_task,
            template=template,
        )
        FieldTemplateSelection.objects.create(
            field_template=field_template,
            template=template,
            value='some value',
        )
        response = api_client.post(
            path=f'/templates/{template.id}/run',
            data={
                'name': 'Test name'
            }
        )

        workflow = Workflow.objects.get(id=response.data['workflow_id'])
        task = workflow.tasks.first()
        field = task.output.first()
        field.value = 'some value'
        field.save(update_fields=['value'])
        selection = field.selections.first()
        selection.is_selected = True
        selection.save(update_fields=['is_selected'])

        # act
        response = api_client.get(f'/v2/tasks/{task.id}')

        # assert
        assert response.status_code == 200
        field_data = response.data['output'][0]
        assert field_data['id'] == field.id
        assert field_data['type'] == field.type
        assert field_data['is_required'] == field.is_required
        assert field_data['name'] == field.name
        assert field_data['description'] == field.description
        assert field_data['api_name'] == field.api_name
        assert field_data['attachments'] == []
        assert field_data['order'] == field.order
        assert field_data['user_id'] is None
        assert field_data['value'] == 'some value'
        selection_data = field_data['selections'][0]
        assert selection_data['id'] == selection.id
        assert selection_data['api_name'] == selection.api_name
        assert selection_data['is_selected'] is True
        assert selection_data['value'] == selection.value

    def test_retrieve__field_with_attachments__ok(self, api_client):

        # arrange
        user = create_test_user()
        api_client.token_authenticate(user)
        template = create_test_template(
            user=user,
            is_active=True,
            tasks_count=1
        )
        template_task = template.tasks.first()
        FieldTemplate.objects.create(
            name='File Field',
            order=1,
            type=FieldType.FILE,
            is_required=True,
            task=template_task,
            template=template,
        )

        response = api_client.post(
            path=f'/templates/{template.id}/run',
            data={
                'name': 'Test name'
            }
        )

        workflow = Workflow.objects.get(id=response.data['workflow_id'])
        task = workflow.tasks.first()
        field = task.output.first()
        attachment = FileAttachment.objects.create(
            name='john.cena',
            url='https://john.cena/john.cena',
            size=1488,
            account_id=user.account_id,
            output=field
        )
        field.value = attachment.url
        field.save(update_fields=['value'])

        # act
        response = api_client.get(f'/v2/tasks/{task.id}')

        # assert
        assert response.status_code == 200
        field_data = response.data['output'][0]
        assert field_data['id'] == field.id
        assert field_data['type'] == field.type
        assert field_data['is_required'] == field.is_required
        assert field_data['name'] == field.name
        assert field_data['description'] == field.description
        assert field_data['api_name'] == field.api_name
        assert field_data['selections'] == []
        assert field_data['order'] == field.order
        assert field_data['user_id'] is None
        # TODO Replace in https://my.pneumatic.app/workflows/18137/
        assert field_data['value'] == attachment.url
        attachment_data = field_data['attachments'][0]
        assert attachment_data['id'] == attachment.id
        assert attachment_data['name'] == attachment.name
        assert attachment_data['url'] == attachment.url

    def test_retrieve__fields_ordering__ok(self, api_client):

        # arrange
        user = create_test_user()
        api_client.token_authenticate(user)
        template = create_test_template(
            user=user,
            is_active=True,
            tasks_count=1
        )
        template_task = template.tasks.first()
        field_template_1 = FieldTemplate.objects.create(
            name='Field 1',
            order=1,
            type=FieldType.USER,
            is_required=True,
            task=template_task,
            template=template,
        )
        field_template_0 = FieldTemplate.objects.create(
            name='Field 0',
            order=0,
            type=FieldType.STRING,
            is_required=False,
            task=template_task,
            template=template,
        )
        field_template_2 = FieldTemplate.objects.create(
            name='Field 2',
            order=2,
            type=FieldType.DROPDOWN,
            is_required=False,
            task=template_task,
            template=template,
        )
        FieldTemplateSelection.objects.create(
            field_template=field_template_2,
            template=template,
            value='value 3',
        )
        response = api_client.post(
            path=f'/templates/{template.id}/run',
            data={
                'name': 'Test name'
            }
        )

        workflow = Workflow.objects.get(id=response.data['workflow_id'])
        task = workflow.tasks.first()

        # act
        response = api_client.get(f'/v2/tasks/{task.id}')

        # assert
        assert response.status_code == 200
        fields = response.data['output']
        assert len(fields) == 3
        assert fields[0]['order'] == 2
        assert fields[0]['api_name'] == field_template_2.api_name
        assert fields[1]['order'] == 1
        assert fields[1]['api_name'] == field_template_1.api_name
        assert fields[2]['order'] == 0
        assert fields[2]['api_name'] == field_template_0.api_name

    def test_retrieve__guest__ok(self, api_client, mocker):

        # arrange
        account = create_test_account()
        account_owner = create_test_user(
            account=account,
            email='owner@test.test',
            is_account_owner=True,
        )
        guest = create_test_guest(account=account)
        workflow = create_test_workflow(account_owner, tasks_count=1)
        task = workflow.tasks.first()
        TaskPerformer.objects.create(
            task_id=task.id,
            user_id=guest.id
        )

        str_token = GuestJWTAuthService.get_str_token(
            task_id=task.id,
            user_id=guest.id,
            account_id=account.id
        )
        identify_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.views.task.TaskViewSet.'
            'identify'
        )
        group_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.views.task.TaskViewSet.'
            'group'
        )

        # act
        response = api_client.get(
            f'/v2/tasks/{task.id}',
            **{'X-Guest-Authorization': str_token}
        )

        # assert
        assert response.status_code == 200
        assert guest.id in response.data['performers']
        identify_mock.assert_called_once_with(guest)
        group_mock.assert_called_once_with(guest)

    def test_retrieve__guest_from_another_task__permission_denied(
        self,
        mocker,
        api_client
    ):
        # TODO Deprecated, case checked in GuestPermission test

        # arrange
        account = create_test_account()
        account_owner = create_test_user(
            account=account,
            email='owner@test.test',
            is_account_owner=True,
        )
        workflow = create_test_workflow(account_owner, tasks_count=2)
        task_1 = workflow.tasks.get(number=1)
        guest_1 = create_test_guest(account=account)
        TaskPerformer.objects.create(
            task_id=task_1.id,
            user_id=guest_1.id
        )
        GuestJWTAuthService.get_str_token(
            task_id=task_1.id,
            user_id=guest_1.id,
            account_id=account.id
        )

        workflow_2 = create_test_workflow(account_owner, tasks_count=1)
        task_2 = workflow_2.tasks.get(number=1)
        guest_2 = create_test_guest(
            account=account,
            email='guest2@test.test'
        )
        TaskPerformer.objects.create(
            task_id=task_2.id,
            user_id=guest_2.id
        )
        str_token_2 = GuestJWTAuthService.get_str_token(
            task_id=task_2.id,
            user_id=guest_2.id,
            account_id=account.id
        )
        mocker.patch(
            'pneumatic_backend.processes.api_v2.views.task.TaskViewSet.'
            'identify'
        )
        mocker.patch(
            'pneumatic_backend.processes.api_v2.views.task.TaskViewSet.'
            'group'
        )

        # act
        response = api_client.get(
            f'/v2/tasks/{task_1.id}',
            **{'X-Guest-Authorization': str_token_2}
        )

        # assert
        assert response.status_code == 403

    # TODO tmp
    def test_retrieve__checklists__ok(self, api_client, mocker):

        # arrange
        user = create_test_user()
        api_client.token_authenticate(user)
        template = create_test_template(
            user=user,
            is_active=True,
            tasks_count=1
        )
        template_task = template.tasks.first()
        checklist_template = ChecklistTemplate.objects.create(
            template=template,
            task=template_task,
            api_name='checklist-1'
        )
        (
            ChecklistTemplateSelection.objects.create(
                checklist=checklist_template,
                template=template,
                value='some value',
                api_name='cl-selection-1'
            )
        )

        response = api_client.post(
            path=f'/templates/{template.id}/run',
            data={'name': 'Test name'}
        )
        workflow = Workflow.objects.get(id=response.data['workflow_id'])
        task = workflow.tasks.first()
        mocker.patch(
            'pneumatic_backend.processes.api_v2.views.task.TaskViewSet.'
            'identify'
        )
        mocker.patch(
            'pneumatic_backend.processes.api_v2.views.task.TaskViewSet.'
            'group'
        )

        # act
        response = api_client.get(f'/v2/tasks/{task.id}')

        # assert
        assert response.status_code == 200
        assert response.data['id'] == task.id
        assert response.data['checklists_total'] == 1
        assert response.data['checklists_marked'] == 0
        assert len(response.data['checklists']) == 1
        checklist_data = response.data['checklists'][0]
        checklist = Checklist.objects.get(api_name='checklist-1')
        selection = ChecklistSelection.objects.get(
            checklist=checklist,
            api_name='cl-selection-1'
        )
        assert checklist_data['id'] == checklist.id
        assert checklist_data['api_name'] == checklist.api_name
        selection_data = checklist_data['selections'][0]
        assert selection_data['id'] == selection.id
        assert selection_data['api_name'] == selection.api_name
        assert selection_data['is_selected'] == selection.is_selected
        assert selection_data['value'] == selection.value

    def test_retrieve__with_comment__ok(self, api_client, mocker):

        # arrange
        user = create_test_user()
        api_client.token_authenticate(user)
        workflow = create_test_workflow(user=user, tasks_count=1)
        task = workflow.tasks.get(number=1)

        mocker.patch(
            'pneumatic_backend.processes.api_v2.views.task.TaskViewSet.'
            'identify'
        )
        mocker.patch(
            'pneumatic_backend.processes.api_v2.views.task.TaskViewSet.'
            'group'
        )
        WorkflowEventService.workflow_run_event(workflow)
        WorkflowEventService.comment_created_event(
            user=user,
            workflow=workflow,
            text='Some text',
            after_create_actions=False
        )

        # act
        response = api_client.get(f'/v2/tasks/{task.id}')

        # assert
        assert response.status_code == 200
        assert response.data['id'] == task.id

    def test_retrieve__sub_workflows_ordering__ok(self, api_client, mocker):

        # arrange
        mocker.patch(
            'pneumatic_backend.processes.api_v2.views.task.TaskViewSet.'
            'identify'
        )
        mocker.patch(
            'pneumatic_backend.processes.api_v2.views.task.TaskViewSet.'
            'group'
        )
        user = create_test_user()
        api_client.token_authenticate(user)
        workflow = create_test_workflow(user=user, tasks_count=1)
        ancestor_task = workflow.current_task_instance
        sub_wf_1 = create_test_workflow(
            user=user,
            tasks_count=1,
            ancestor_task=ancestor_task
        )
        sub_wf_2 = create_test_workflow(
            user=user,
            tasks_count=1,
            ancestor_task=ancestor_task
        )

        # act
        response = api_client.get(f'/v2/tasks/{ancestor_task.id}')

        # assert
        assert response.status_code == 200
        data = response.data['sub_workflows']
        assert len(data) == 2
        assert data[0]['id'] == sub_wf_2.id
        assert data[1]['id'] == sub_wf_1.id

    def test_retrieve__sub_workflows__ok(self, api_client, mocker):
        # arrange
        mocker.patch(
            'pneumatic_backend.processes.api_v2.views.task.TaskViewSet.'
            'identify'
        )
        mocker.patch(
            'pneumatic_backend.processes.api_v2.views.task.TaskViewSet.'
            'group'
        )
        user = create_test_user()
        api_client.token_authenticate(user)
        workflow = create_test_workflow(user=user, tasks_count=1)
        ancestor_task = workflow.current_task_instance
        sub_wf = create_test_workflow(
            name='Lovely sub workflow',
            user=user,
            tasks_count=3,
            ancestor_task=ancestor_task,
            due_date=timezone.now() + timedelta(days=3),
            is_urgent=True,
            status=WorkflowStatus.DELAYED
        )
        sub_wf.current_task = 3
        sub_wf.save()
        task_1 = sub_wf.tasks.get(number=1)
        task_1.is_completed = True
        task_1.date_completed = timezone.now()
        task_1.save()

        task_2 = sub_wf.tasks.get(number=2)
        task_2.is_completed = True
        task_2.date_completed = timezone.now()
        task_2.save()

        task_3 = sub_wf.tasks.get(number=3)
        task_3.due_date = timezone.now() + timedelta(hours=8)
        task_3.date_started = timezone.now()
        task_3.save()
        delay = Delay.objects.create(
            duration=timedelta(days=2),
            task=task_3,
            start_date=timezone.now(),
        )
        # act
        response = api_client.get(f'/v2/tasks/{ancestor_task.id}')

        # assert
        assert response.status_code == 200
        data = response.data['sub_workflows'][0]
        assert data['id'] == sub_wf.id
        assert data['name'] == sub_wf.name
        assert data['status'] == sub_wf.status
        assert data['date_created'] == (
            sub_wf.date_created.strftime(date_format)
        )
        assert data['date_created_tsp'] == sub_wf.date_created.timestamp()
        assert data['due_date'] == sub_wf.due_date.strftime(date_format)
        assert data['due_date_tsp'] == sub_wf.due_date.timestamp()
        assert data['tasks_count'] == 3
        assert data['is_external'] is False
        assert data['is_urgent'] is True
        assert data['workflow_starter'] == user.id
        assert data['current_task'] == 3

        passed_tasks = data['passed_tasks']
        assert len(passed_tasks) == 2
        assert passed_tasks[0]['id'] == task_1.id
        assert passed_tasks[0]['name'] == task_1.name
        assert passed_tasks[0]['number'] == 1
        assert passed_tasks[1]['id'] == task_2.id
        assert passed_tasks[1]['name'] == task_2.name
        assert passed_tasks[1]['number'] == 2

        assert data['template']['id'] == sub_wf.template.id
        assert data['template']['name'] == sub_wf.template.name
        assert data['template']['is_active'] == sub_wf.template.is_active
        assert data['template']['template_owners'] == [user.id]

        current_task = data['task']
        assert current_task['id'] == task_3.id
        assert current_task['name'] == task_3.name
        assert current_task['number'] == 3
        assert current_task['due_date'] == (
            task_3.due_date.strftime(date_format)
        )
        assert current_task['due_date_tsp'] == task_3.due_date.timestamp()
        assert current_task['date_started'] == (
            task_3.date_started.strftime(date_format)
        )
        assert current_task['date_started_tsp'] == (
            task_3.date_started.timestamp()
        )
        assert current_task['performers'] == [user.id]
        assert current_task['checklists_total'] == 0
        assert current_task['checklists_marked'] == 0

        delay_data = current_task['delay']
        assert delay_data['id'] == delay.id
        assert delay_data['duration'] == '2 00:00:00'
        assert delay_data['start_date'] == (
            delay.start_date.strftime(date_format)
        )
        assert delay_data['start_date_tsp'] == delay.start_date.timestamp()
        assert delay_data['estimated_end_date'] == (
            delay.estimated_end_date.strftime(date_format)
        )
        assert delay_data['estimated_end_date_tsp'] == (
            delay.estimated_end_date.timestamp()
        )
        assert delay_data['end_date'] is None
        assert delay_data['end_date_tsp'] is None
