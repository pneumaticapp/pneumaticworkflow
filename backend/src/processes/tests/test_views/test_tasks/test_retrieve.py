from datetime import timedelta

import pytest
from django.utils import timezone

from src.accounts.enums import (
    BillingPlanType,
)
from src.authentication.enums import AuthTokenType
from src.authentication.services.guest_auth import GuestJWTAuthService
from src.processes.enums import (
    FieldType,
    OwnerType,
    PerformerType,
    TaskStatus,
    WorkflowStatus,
)
from src.processes.models.templates.checklist import (
    ChecklistTemplate,
    ChecklistTemplateSelection,
)
from src.processes.models.templates.fields import (
    FieldTemplate,
    FieldTemplateSelection,
)
from src.processes.models.templates.template import Template
from src.processes.models.workflows.checklist import (
    Checklist,
    ChecklistSelection,
)
from src.processes.models.workflows.task import (
    Delay,
    TaskPerformer,
)
from src.processes.models.workflows.workflow import Workflow
from src.processes.services.events import WorkflowEventService
from src.processes.services.tasks.performers import (
    TaskPerformersService,
)
from src.processes.tasks.update_workflow import update_workflows
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_admin,
    create_test_attachment,
    create_test_group,
    create_test_guest,
    create_test_owner,
    create_test_template,
    create_test_user,
    create_test_workflow,
)
from src.utils.dates import date_format

pytestmark = pytest.mark.django_db


def test_retrieve__ok(api_client, mocker):
    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)
    workflow = create_test_workflow(user=user, tasks_count=1)
    task = workflow.tasks.get(number=1)
    task.due_date = task.date_first_started + timedelta(hours=24)
    task.save(update_fields=['due_date'])

    identify_mock = mocker.patch(
        'src.processes.views.task.TaskViewSet.'
        'identify',
    )
    group_mock = mocker.patch(
        'src.processes.views.task.TaskViewSet.'
        'group',
    )

    # act
    response = api_client.get(f'/v2/tasks/{task.id}')

    # assert
    assert response.status_code == 200
    task.refresh_from_db()
    assert response.data['id'] == task.id
    assert response.data['name'] == task.name
    assert response.data['api_name'] == task.api_name
    assert response.data['description'] == task.description
    assert response.data['is_urgent'] is False
    assert response.data['date_started_tsp'] == (
        task.date_started.timestamp()
    )
    assert response.data['date_completed_tsp'] is None
    assert response.data['due_date_tsp'] == task.due_date.timestamp()
    assert response.data['delay'] is None
    assert response.data['sub_workflows'] == []
    assert response.data['checklists'] == []
    assert response.data['status'] == TaskStatus.ACTIVE
    assert response.data['revert_tasks'] == []

    workflow_data = response.data['workflow']
    assert workflow_data['id'] == workflow.id
    assert workflow_data['name'] == workflow.name
    assert workflow_data['status'] == workflow.status
    assert workflow_data['template_name'] == workflow.get_template_name()
    assert workflow_data['date_completed_tsp'] is None

    identify_mock.assert_not_called()
    group_mock.assert_not_called()


def test_retrieve__delayed__ok(api_client, mocker):
    # arrange
    mocker.patch(
        'src.processes.views.task.TaskViewSet.'
        'identify',
    )
    mocker.patch(
        'src.processes.views.task.TaskViewSet.group',
    )
    user = create_test_user()
    api_client.token_authenticate(user)
    workflow = create_test_workflow(user=user, tasks_count=1)
    task = workflow.tasks.get(number=1)
    task.status = TaskStatus.DELAYED
    task.save()
    delay = Delay.objects.create(
        duration=timedelta(days=2),
        task=task,
        start_date=timezone.now(),
        workflow=workflow,
    )

    # act
    response = api_client.get(f'/v2/tasks/{task.id}')

    # assert
    assert response.status_code == 200
    task.refresh_from_db()
    assert response.data['id'] == task.id
    assert response.data['is_urgent'] is False
    assert response.data['date_started_tsp'] == (
        task.date_started.timestamp()
    )
    assert response.data['date_completed_tsp'] is None
    assert response.data['due_date_tsp'] is None
    assert response.data['status'] == TaskStatus.DELAYED

    delay_data = response.data['delay']
    assert delay_data['id'] == delay.id
    assert delay_data['duration'] == '2 00:00:00'
    assert delay_data['start_date_tsp'] == delay.start_date.timestamp()
    assert delay_data['estimated_end_date'] == (
        delay.estimated_end_date.strftime(date_format)
    )
    assert delay_data['estimated_end_date_tsp'] == (
        delay.estimated_end_date.timestamp()
    )
    assert delay_data['end_date_tsp'] is None
    workflow_data = response.data['workflow']
    assert workflow_data['id'] == workflow.id
    assert workflow_data['name'] == workflow.name
    assert workflow_data['status'] == workflow.status
    assert workflow_data['template_name'] == workflow.get_template_name()
    assert workflow_data['date_completed_tsp'] is None


def test_retrieve__workflow_member__ok(api_client):
    # arrange
    user = create_test_user()
    another_user = create_test_user(
        account=user.account,
        email='admin@test.test',
        is_account_owner=False,
    )
    workflow = create_test_workflow(user)
    workflow.members.add(another_user)
    tasks = workflow.tasks.order_by('number')
    task = tasks[0]

    api_client.token_authenticate(another_user)

    # act
    response = api_client.get(f'/v2/tasks/{task.id}')

    # assert
    assert response.status_code == 200
    assert response.data['id'] == task.id
    assert response.data['workflow']['id'] == workflow.id


def test_retrieve__account_owner_not_wf_member__ok(api_client):

    # arrange
    account = create_test_account(plan=BillingPlanType.PREMIUM)
    account_owner = create_test_user(account=account)
    user = create_test_user(account=account, email='t@t.t')
    workflow = create_test_workflow(user, tasks_count=1)
    task = workflow.tasks.get(number=1)
    api_client.token_authenticate(account_owner)

    # act
    response = api_client.get(f'/v2/tasks/{task.id}')

    # assert
    assert response.status_code == 200
    assert response.data['id'] == task.id


def test_retrieve__admin_not_workflow_member__permission_denied(api_client):
    # arrange
    user = create_test_user()
    user.account.billing_plan = BillingPlanType.PREMIUM
    user.account.save()
    another_user = create_test_user(
        account=user.account,
        email='admin@test.test',
        is_account_owner=False,
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


def test_retrieve__delayed_task__not_found(api_client, mocker):

    # arrange
    mocker.patch(
        'src.processes.tasks.webhooks.'
        'send_task_completed_webhook.delay',
    )
    user = create_test_user()
    workflow = create_test_workflow(user)
    task_1 = workflow.tasks.get(number=1)
    task_2 = workflow.tasks.get(number=2)
    Delay.objects.create(
        task=task_2,
        duration=timedelta(seconds=1000),
        workflow=workflow,
    )

    api_client.token_authenticate(user)
    api_client.post(f'/v2/tasks/{task_1.id}/complete')

    # act
    response = api_client.get(f'/v2/tasks/{task_2.id}')

    # assert
    assert response.status_code == 404


def test_retrieve__delete_delay_before_active_task__found(
    mocker,
    api_client,
):

    """ Caused by bug: https://my.pneumatic.app/workflows/11741"""

    # arrange
    mocker.patch(
        'src.processes.tasks.webhooks.'
        'send_workflow_started_webhook.delay',
    )
    mocker.patch(
        'src.processes.tasks.webhooks.'
        'send_task_completed_webhook.delay',
    )
    user = create_test_user()
    api_client.token_authenticate(user)
    request_data = {
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
                'number': 1,
                'name': 'First step',
                'raw_performers': [
                    {
                        'type': PerformerType.USER,
                        'source_id': user.id,
                    },
                ],
            },
            {
                'number': 2,
                'name': 'Second step',
                'delay': '00:10:00',
                'raw_performers': [
                    {
                        'type': PerformerType.USER,
                        'source_id': user.id,
                    },
                ],
            },
        ],
    }
    response = api_client.post(
        path='/templates',
        data=request_data,
    )
    template = Template.objects.get(id=response.data['id'])

    workflow = create_test_workflow(user, template=template)
    task_1 = workflow.tasks.get(number=1)
    api_client.post(f'/v2/tasks/{task_1.id}/complete')
    workflow.refresh_from_db()

    template_data = api_client.get(
        f'/templates/{workflow.template_id}',
    ).data
    template_data['tasks'][1].pop('delay')
    mocker.patch(
        'src.processes.services.templates.'
        'integrations.TemplateIntegrationsService.template_updated',
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
        auth_type=AuthTokenType.USER,
    )

    # act
    response = api_client.get(f'/v2/tasks/{task_1.id}')

    # assert
    assert response.status_code == 200


def test_retrieve__completed_task__ok(api_client, mocker):

    # arrange
    mocker.patch(
        'src.processes.tasks.webhooks.'
        'send_task_completed_webhook.delay',
    )
    user = create_test_user()
    workflow = create_test_workflow(user)
    tasks = workflow.tasks.order_by('number')
    task = tasks[0]
    api_client.token_authenticate(user)

    api_client.post(f'/v2/tasks/{task.id}/complete')
    workflow.refresh_from_db()

    # act
    response = api_client.get(f'/v2/tasks/{task.id}')

    # assert
    assert response.status_code == 200
    task.refresh_from_db()
    assert response.data['date_started_tsp'] == (
        task.date_started.timestamp()
    )
    assert response.data['date_completed_tsp'] == (
        task.date_completed.timestamp()
    )
    assert response.data['status'] == TaskStatus.COMPLETED
    performer = task.taskperformer_set.first()
    assert response.data['performers'] == [
        {
            'source_id': user.id,
            'type': 'user',
            'is_completed': True,
            'date_completed_tsp': performer.date_completed.timestamp(),
        },
    ]


def test_retrieve__user_completed_task__return_as_completed(
    mocker,
    api_client,
):
    """ https://trello.com/c/75aESAb0 """
    # arrange
    mocker.patch(
        'src.processes.tasks.webhooks.'
        'send_task_completed_webhook.delay',
    )
    user = create_test_user()
    another_user = create_test_user(
        email='another_user@test.com',
        account=user.account,
    )
    workflow = create_test_workflow(user)
    task = workflow.tasks.get(number=1)
    task.require_completion_by_all = True
    task.save()
    raw_performer = task.add_raw_performer(another_user)
    task.update_performers(raw_performer)
    api_client.token_authenticate(user)
    api_client.post(f'/v2/tasks/{task.id}/complete')

    # act
    response = api_client.get(f'/v2/tasks/{task.id}')

    # assert
    task.refresh_from_db()
    assert response.status_code == 200
    assert response.data['is_completed'] is True
    assert task.is_completed is False


def test_retrieve__revert_delayed_task__not_found(
    mocker,
    api_client,
):

    # arrange
    mocker.patch(
        'src.processes.tasks.webhooks.'
        'send_task_completed_webhook.delay',
    )
    mocker.patch(
        'src.processes.tasks.webhooks.'
        'send_task_returned_webhook.delay',
    )
    user = create_test_user()
    api_client.token_authenticate(user)
    workflow = create_test_workflow(
        user=user,
        tasks_count=2,
    )
    task_1 = workflow.tasks.get(number=1)
    task_2 = workflow.tasks.get(number=2)
    Delay.objects.create(
        task=task_2,
        duration=timedelta(hours=1),
        workflow=workflow,
    )

    response_complete_1 = api_client.post(f'/v2/tasks/{task_1.id}/complete')
    response_complete_2 = api_client.post(f'/v2/tasks/{task_2.id}/complete')
    response_revert = api_client.post(
        f'/v2/tasks/{task_2.id}/revert',
    )
    workflow.refresh_from_db()

    # act
    response4 = api_client.get(f'/v2/tasks/{task_2.id}')

    # assert
    assert response_complete_1.status_code == 200
    assert response_complete_2.status_code == 400
    assert response_revert.status_code == 400
    assert response4.status_code == 404
    task_1.refresh_from_db()
    assert task_1.status == TaskStatus.COMPLETED
    task_2.refresh_from_db()
    assert task_2.status == TaskStatus.DELAYED


def test_retrieve__reverted_task__ok(mocker, api_client):

    # arrange
    mocker.patch(
        'src.processes.tasks.webhooks.'
        'send_task_completed_webhook.delay',
    )
    mocker.patch(
        'src.processes.tasks.webhooks.'
        'send_task_returned_webhook.delay',
    )
    user = create_test_user()
    api_client.token_authenticate(user)
    workflow = create_test_workflow(
        user=user,
        tasks_count=2,
    )
    task_1 = workflow.tasks.get(number=1)
    api_client.post(f'/v2/tasks/{task_1.id}/complete')

    workflow.refresh_from_db()
    task_2 = workflow.tasks.get(number=2)
    response_revert = api_client.post(
        f'/v2/tasks/{task_2.id}/revert',
        data={
            'comment': 'text_comment',
        },
    )
    workflow.refresh_from_db()

    # act
    response = api_client.get(f'/v2/tasks/{task_2.id}')

    # assert
    assert response_revert.status_code == 204
    assert response.status_code == 200
    assert response.data['id'] == task_2.id
    assert response.data['date_started_tsp'] is None
    assert response.data['date_completed_tsp'] is None
    assert response.data['due_date_tsp'] is None
    workflow_data = response.data['workflow']
    assert workflow_data['id'] == workflow.id
    assert workflow_data['name'] == workflow.name
    assert workflow_data['status'] == workflow.status
    assert workflow_data['template_name'] == workflow.get_template_name()
    assert workflow_data['date_completed_tsp'] is None


def test_retrieve__deleted_performer__ok(api_client):

    # arrange
    user = create_test_user()
    user2 = create_test_user(email='t@t.t', account=user.account)
    api_client.token_authenticate(user)
    template = create_test_template(
        user=user,
        is_active=True,
        tasks_count=1,
    )
    workflow = create_test_workflow(user, template)
    task = workflow.tasks.get(number=1)
    TaskPerformersService.create_performer(
        request_user=user,
        user_key=user2.id,
        task=task,
        run_actions=False,
        current_url='/page',
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    TaskPerformersService.delete_performer(
        request_user=user,
        user_key=user2.id,
        task=task,
        run_actions=False,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )

    # act
    response = api_client.get(f'/v2/tasks/{task.id}')

    # assert
    assert response.status_code == 200
    assert response.data['id'] == task.id
    assert len(response.data['performers']) == 1
    assert response.data['performers'] == [
        {
            'source_id': user.id,
            'type': 'user',
            'is_completed': False,
            'date_completed_tsp': None,
        },
    ]


def test_retrieve__get_performers_type_field__ok(api_client):
    # arrange
    user = create_test_user()
    user2 = create_test_user(
        email='test2@pneumatic.app',
        account=user.account,
    )
    api_client.token_authenticate(user)

    template = create_test_template(
        user=user,
        tasks_count=2,
        is_active=True,
    )

    field_template = FieldTemplate.objects.create(
        name='First task performer',
        type=FieldType.USER,
        is_required=True,
        kickoff=template.kickoff_instance,
        template=template,
    )

    template_first_task = template.tasks.order_by(
        'number',
    ).first()
    template_first_task.delete_raw_performers()
    template_first_task.add_raw_performer(
        performer_type=PerformerType.FIELD,
        field=field_template,
    )
    response = api_client.post(
        f'/templates/{template.id}/run',
        data={
            'name': 'Test template',
            'kickoff': {
                field_template.api_name: user2.email,
            },
        },
    )
    workflow_id = response.data['id']
    workflow = Workflow.objects.get(pk=workflow_id)
    task = workflow.tasks.get(number=1)

    # act
    response = api_client.get(f'/v2/tasks/{task.id}')
    performers = response.data['performers']

    # assert
    assert len(performers) == 1
    assert performers == [
        {
            'source_id': user2.id,
            'type': 'user',
            'is_completed': False,
            'date_completed_tsp': None,
        },
    ]


def test_retrieve__is_urgent__ok(api_client):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)
    workflow = create_test_workflow(
        user=user,
        is_urgent=True,
        tasks_count=1,
    )
    task = workflow.tasks.get(number=1)

    # act
    response = api_client.get(f'/v2/tasks/{task.id}')

    # assert
    assert response.status_code == 200
    assert response.data['id'] == task.id
    assert response.data['is_urgent'] is True


def test_retrieve__field_user__ok(api_client):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)
    template = create_test_template(
        user=user,
        is_active=True,
        tasks_count=1,
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
        },
    )
    workflow = Workflow.objects.get(id=response.data['id'])
    task = workflow.tasks.get(number=1)

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
    assert field_data['value'] == user.get_full_name()  # user.get_full_name()
    assert field_data['selections'] == []
    assert field_data['attachments'] == []
    assert field_data['order'] == field.order
    assert field_data['user_id'] == user.id


def test_retrieve__field_date__ok(api_client):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)
    template = create_test_template(
        user=user,
        is_active=True,
        tasks_count=1,
    )
    template_task = template.tasks.first()
    FieldTemplate.objects.create(
        name='Date Field',
        order=1,
        type=FieldType.DATE,
        is_required=True,
        task=template_task,
        template=template,
    )
    response = api_client.post(
        path=f'/templates/{template.id}/run',
        data={
            'name': 'Test name',
        },
    )
    workflow = Workflow.objects.get(id=response.data['id'])
    task = workflow.tasks.get(number=1)

    field = task.output.first()
    field.value = 321321321
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
    assert field_data['value'] == str(321321321)
    assert field_data['selections'] == []
    assert field_data['attachments'] == []
    assert field_data['order'] == field.order


def test_retrieve__field_url__ok(api_client):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)
    template = create_test_template(
        user=user,
        is_active=True,
        tasks_count=1,
    )
    template_task = template.tasks.first()
    FieldTemplate.objects.create(
        name='URL Field',
        order=1,
        type=FieldType.URL,
        is_required=True,
        task=template_task,
        template=template,
    )
    response = api_client.post(
        path=f'/templates/{template.id}/run',
        data={
            'name': 'Test name',
        },
    )
    workflow = Workflow.objects.get(id=response.data['id'])
    task = workflow.tasks.get(number=1)

    field = task.output.first()
    field.value = 321321321
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
    assert field_data['value'] == str(321321321)
    assert field_data['selections'] == []
    assert field_data['attachments'] == []
    assert field_data['order'] == field.order


def test_retrieve__field_with_selections__ok(api_client):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)
    template = create_test_template(
        user=user,
        is_active=True,
        tasks_count=1,
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
            'name': 'Test name',
        },
    )

    workflow = Workflow.objects.get(id=response.data['id'])
    task = workflow.tasks.get(number=1)
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


def test_retrieve__field_with_attachments__ok(api_client):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)
    template = create_test_template(
        user=user,
        is_active=True,
        tasks_count=1,
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
            'name': 'Test name',
        },
    )

    workflow = Workflow.objects.get(id=response.data['id'])
    task = workflow.tasks.get(number=1)
    field = task.output.first()
    attachment = create_test_attachment(
        account=user.account,
        file_id='task_retrieve_file.png',
        task=task,
        workflow=workflow,
    )
    field.value = 'File: task_retrieve_file.png'
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


def test_retrieve__fields_ordering__ok(api_client):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)
    template = create_test_template(
        user=user,
        is_active=True,
        tasks_count=1,
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
            'name': 'Test name',
        },
    )

    workflow = Workflow.objects.get(id=response.data['id'])
    task = workflow.tasks.get(number=1)

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


def test_retrieve__guest__ok(api_client, mocker):

    # arrange
    account = create_test_account()
    account_owner = create_test_user(
        account=account,
        email='owner@test.test',
        is_account_owner=True,
    )
    guest = create_test_guest(account=account)
    workflow = create_test_workflow(account_owner, tasks_count=1)
    task = workflow.tasks.get(number=1)
    TaskPerformer.objects.create(
        task_id=task.id,
        user_id=guest.id,
    )

    str_token = GuestJWTAuthService.get_str_token(
        task_id=task.id,
        user_id=guest.id,
        account_id=account.id,
    )
    identify_mock = mocker.patch(
        'src.processes.views.task.TaskViewSet.'
        'identify',
    )
    group_mock = mocker.patch(
        'src.processes.views.task.TaskViewSet.'
        'group',
    )

    # act
    response = api_client.get(
        f'/v2/tasks/{task.id}',
        **{'X-Guest-Authorization': str_token},
    )

    # assert
    assert response.status_code == 200
    performer = [item['source_id'] for item in response.data['performers']]
    assert guest.id in performer
    identify_mock.assert_called_once_with(guest)
    group_mock.assert_called_once_with(guest)


def test_retrieve__guest_from_another_task__permission_denied(
    mocker,
    api_client,
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
        user_id=guest_1.id,
    )
    GuestJWTAuthService.get_str_token(
        task_id=task_1.id,
        user_id=guest_1.id,
        account_id=account.id,
    )

    workflow_2 = create_test_workflow(account_owner, tasks_count=1)
    task_2 = workflow_2.tasks.get(number=1)
    guest_2 = create_test_guest(
        account=account,
        email='guest2@test.test',
    )
    TaskPerformer.objects.create(
        task_id=task_2.id,
        user_id=guest_2.id,
    )
    str_token_2 = GuestJWTAuthService.get_str_token(
        task_id=task_2.id,
        user_id=guest_2.id,
        account_id=account.id,
    )
    mocker.patch(
        'src.processes.views.task.TaskViewSet.'
        'identify',
    )
    mocker.patch(
        'src.processes.views.task.TaskViewSet.'
        'group',
    )

    # act
    response = api_client.get(
        f'/v2/tasks/{task_1.id}',
        **{'X-Guest-Authorization': str_token_2},
    )

    # assert
    assert response.status_code == 403


# TODO tmp
def test_retrieve__checklists__ok(api_client, mocker):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)
    template = create_test_template(
        user=user,
        is_active=True,
        tasks_count=1,
    )
    template_task = template.tasks.first()
    checklist_template = ChecklistTemplate.objects.create(
        template=template,
        task=template_task,
        api_name='checklist-1',
    )
    (
        ChecklistTemplateSelection.objects.create(
            checklist=checklist_template,
            template=template,
            value='some value',
            api_name='cl-selection-1',
        )
    )

    response = api_client.post(
        path=f'/templates/{template.id}/run',
        data={'name': 'Test name'},
    )
    workflow = Workflow.objects.get(id=response.data['id'])
    task = workflow.tasks.get(number=1)
    mocker.patch(
        'src.processes.views.task.TaskViewSet.'
        'identify',
    )
    mocker.patch(
        'src.processes.views.task.TaskViewSet.'
        'group',
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
        api_name='cl-selection-1',
    )
    assert checklist_data['id'] == checklist.id
    assert checklist_data['api_name'] == checklist.api_name
    selection_data = checklist_data['selections'][0]
    assert selection_data['id'] == selection.id
    assert selection_data['api_name'] == selection.api_name
    assert selection_data['is_selected'] == selection.is_selected
    assert selection_data['value'] == selection.value


def test_retrieve__with_comment__ok(api_client, mocker):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)
    workflow = create_test_workflow(user=user, tasks_count=1)
    task = workflow.tasks.get(number=1)

    mocker.patch(
        'src.processes.views.task.TaskViewSet.'
        'identify',
    )
    mocker.patch(
        'src.processes.views.task.TaskViewSet.'
        'group',
    )
    WorkflowEventService.workflow_run_event(workflow)
    WorkflowEventService.comment_created_event(
        user=user,
        task=task,
        text='Some text',
        after_create_actions=False,
    )

    # act
    response = api_client.get(f'/v2/tasks/{task.id}')

    # assert
    assert response.status_code == 200
    assert response.data['id'] == task.id


def test_retrieve__sub_workflows_ordering__ok(api_client, mocker):

    # arrange
    mocker.patch(
        'src.processes.views.task.TaskViewSet.'
        'identify',
    )
    mocker.patch(
        'src.processes.views.task.TaskViewSet.'
        'group',
    )
    user = create_test_user()
    api_client.token_authenticate(user)
    workflow = create_test_workflow(user=user, tasks_count=1)
    ancestor_task = workflow.tasks.get(number=1)
    sub_wf_1 = create_test_workflow(
        user=user,
        tasks_count=1,
        ancestor_task=ancestor_task,
    )
    sub_wf_2 = create_test_workflow(
        user=user,
        tasks_count=1,
        ancestor_task=ancestor_task,
    )

    # act
    response = api_client.get(f'/v2/tasks/{ancestor_task.id}')

    # assert
    assert response.status_code == 200
    data = response.data['sub_workflows']
    assert len(data) == 2
    assert data[0]['id'] == sub_wf_2.id
    assert data[1]['id'] == sub_wf_1.id


def test_retrieve__sub_workflows__ok(api_client, mocker):
    # arrange
    mocker.patch(
        'src.processes.views.task.TaskViewSet.'
        'identify',
    )
    mocker.patch(
        'src.processes.views.task.TaskViewSet.'
        'group',
    )
    user = create_test_user()
    api_client.token_authenticate(user)
    workflow = create_test_workflow(user=user, tasks_count=1)
    ancestor_task = workflow.tasks.get(number=1)
    sub_wf = create_test_workflow(
        name='Lovely sub workflow',
        user=user,
        tasks_count=1,
        ancestor_task=ancestor_task,
        due_date=timezone.now() + timedelta(days=3),
        is_urgent=True,
        status=WorkflowStatus.DELAYED,
    )
    task_1 = sub_wf.tasks.get(number=1)
    task_1.due_date = timezone.now() + timedelta(hours=8)
    task_1.save()
    delay = Delay.objects.create(
        duration=timedelta(days=2),
        task=task_1,
        start_date=timezone.now(),
        workflow=workflow,
    )
    # act
    response = api_client.get(f'/v2/tasks/{ancestor_task.id}')

    # assert
    assert response.status_code == 200
    data = response.data['sub_workflows'][0]
    assert data['id'] == sub_wf.id
    assert data['name'] == sub_wf.name
    assert data['status'] == sub_wf.status
    assert data['description'] == sub_wf.description
    assert data['date_created_tsp'] == sub_wf.date_created.timestamp()
    assert data['due_date_tsp'] == sub_wf.due_date.timestamp()
    assert data['is_external'] is False
    assert data['is_urgent'] is True
    assert data['finalizable'] == sub_wf.finalizable
    assert data['workflow_starter'] == user.id
    assert data['ancestor_task_id'] == ancestor_task.id
    assert data['is_legacy_template'] is False
    assert data['legacy_template_name'] is None

    assert data['template']['id'] == sub_wf.template.id
    assert data['template']['name'] == sub_wf.template.name
    assert data['template']['is_active'] == sub_wf.template.is_active
    assert data['owners'] == [user.id]

    assert data['tasks'][0]['id'] == task_1.id
    assert data['tasks'][0]['name'] == task_1.name
    assert data['tasks'][0]['number'] == 1
    assert data['tasks'][0]['due_date_tsp'] == task_1.due_date.timestamp()
    assert data['tasks'][0]['date_started_tsp'] == (
        task_1.date_started.timestamp()
    )
    assert data['tasks'][0]['performers'] == [
        {
            'source_id': user.id,
            'type': 'user',
            'is_completed': False,
            'date_completed_tsp': None,
        },
    ]
    assert data['tasks'][0]['checklists_total'] == 0
    assert data['tasks'][0]['checklists_marked'] == 0
    assert data['tasks'][0]['status'] == TaskStatus.ACTIVE

    delay_data = data['tasks'][0]['delay']
    assert delay_data['id'] == delay.id
    assert delay_data['duration'] == '2 00:00:00'
    assert delay_data['start_date_tsp'] == delay.start_date.timestamp()
    assert delay_data['estimated_end_date'] == (
        delay.estimated_end_date.strftime(date_format)
    )
    assert delay_data['estimated_end_date_tsp'] == (
        delay.estimated_end_date.timestamp()
    )
    assert delay_data['end_date_tsp'] is None


def test_retrieve__sub_workflows_multiple_tasks__ok(api_client, mocker):

    # arrange
    mocker.patch(
        'src.processes.views.task.TaskViewSet.'
        'identify',
    )
    mocker.patch(
        'src.processes.views.task.TaskViewSet.'
        'group',
    )
    user = create_test_user()
    api_client.token_authenticate(user)
    workflow = create_test_workflow(user=user, tasks_count=1)
    ancestor_task = workflow.tasks.get(number=1)
    workflow = create_test_workflow(
        name='Lovely sub workflow',
        user=user,
        tasks_count=2,
        ancestor_task=ancestor_task,
        due_date=timezone.now() + timedelta(days=3),
        is_urgent=True,
        status=WorkflowStatus.DELAYED,
    )
    task_1 = workflow.tasks.get(number=1)
    task_2 = workflow.tasks.get(number=2)

    # act
    response = api_client.get(f'/v2/tasks/{ancestor_task.id}')

    # assert
    assert response.status_code == 200
    data = response.data['sub_workflows'][0]
    assert len(data['tasks']) == 2
    task_1_data = data['tasks'][0]
    assert task_1_data['id'] == task_1.id
    assert task_1_data['status'] == TaskStatus.ACTIVE
    task_2_data = data['tasks'][1]
    assert task_2_data['id'] == task_2.id
    assert task_2_data['status'] == TaskStatus.PENDING


def test_retrieve__sub_workflows_not_return_skipped_tasks__ok(
    api_client,
    mocker,
):

    # arrange
    mocker.patch(
        'src.processes.views.task.TaskViewSet.'
        'identify',
    )
    mocker.patch(
        'src.processes.views.task.TaskViewSet.'
        'group',
    )
    user = create_test_user()
    api_client.token_authenticate(user)
    workflow = create_test_workflow(user=user, tasks_count=1)
    ancestor_task = workflow.tasks.get(number=1)
    workflow = create_test_workflow(
        name='Lovely sub workflow',
        user=user,
        tasks_count=2,
        ancestor_task=ancestor_task,
        due_date=timezone.now() + timedelta(days=3),
        is_urgent=True,
        status=WorkflowStatus.DELAYED,
        active_task_number=2,
    )
    task_1 = workflow.tasks.get(number=1)
    task_1.status = TaskStatus.SKIPPED
    task_1.save()
    task_2 = workflow.tasks.get(number=2)

    # act
    response = api_client.get(f'/v2/tasks/{ancestor_task.id}')

    # assert
    assert response.status_code == 200
    data = response.data['sub_workflows'][0]
    assert len(data['tasks']) == 1
    task_1_data = data['tasks'][0]
    assert task_1_data['id'] == task_2.id
    assert task_1_data['status'] == TaskStatus.ACTIVE


def test_retrieve__non_existent_task__not_found(api_client):

    # arrange
    user = create_test_owner()
    non_task = 991651
    api_client.token_authenticate(user)

    # act
    response = api_client.get(f'/v2/tasks/{non_task}')

    # assert
    assert response.status_code == 404


def test_retrieve__user_in_group_task_performer__ok(api_client, mocker):

    # arrange
    identify_mock = mocker.patch(
        'src.processes.views.task.TaskViewSet.'
        'identify',
    )
    group_mock = mocker.patch(
        'src.processes.views.task.TaskViewSet.'
        'group',
    )
    account = create_test_account()
    owner = create_test_owner(account=account)
    group_user = create_test_admin(account=account)
    group = create_test_group(account, users=[group_user])
    workflow = create_test_workflow(user=owner, tasks_count=1)
    workflow.members.add(group_user)
    task = workflow.tasks.get(number=1)
    TaskPerformer.objects.create(
        task_id=task.id,
        type=PerformerType.GROUP,
        group_id=group.id,
    )
    api_client.token_authenticate(group_user)

    # act
    response = api_client.get(f'/v2/tasks/{task.id}')

    # assert
    assert response.status_code == 200
    assert response.data['id'] == task.id
    assert response.data['workflow']['id'] == workflow.id
    identify_mock.assert_not_called()
    group_mock.assert_not_called()


def test_retrieve__user_is_member_in_deleted_task__not_found(api_client):

    # arrange
    user = create_test_owner()
    admin = create_test_admin(account=user.account)
    api_client.token_authenticate(admin)
    workflow = create_test_workflow(user, tasks_count=1)
    workflow.members.add(admin)
    task = workflow.tasks.get(number=1)
    task.delete()

    # act
    response = api_client.get(f'/v2/tasks/{task.id}')

    # assert
    assert response.status_code == 404


def test_retrieve__user_is_not_member_in_deleted_task__not_found(api_client):

    # arrange
    user = create_test_owner()
    admin = create_test_admin(account=user.account)
    workflow = create_test_workflow(user, tasks_count=1)
    task = workflow.tasks.get(number=1)
    task.delete()
    api_client.token_authenticate(admin)

    # act
    response = api_client.get(f'/v2/tasks/{task.id}')

    # assert
    assert response.status_code == 404


def test_retrieve__default_revert_tasks__ok(api_client, mocker):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)
    workflow = create_test_workflow(
        user=user,
        tasks_count=3,
        active_task_number=2,
    )
    task_1 = workflow.tasks.get(number=1)
    task_2 = workflow.tasks.get(number=2)
    mocker.patch(
        'src.processes.views.task.TaskViewSet.'
        'identify',
    )
    mocker.patch(
        'src.processes.views.task.TaskViewSet.'
        'group',
    )

    # act
    response = api_client.get(f'/v2/tasks/{task_2.id}')

    # assert
    assert response.status_code == 200
    assert response.data['id'] == task_2.id
    assert response.data['revert_tasks'] == [
        {
            'id': task_1.id,
            'name': task_1.name,
            'api_name': task_1.api_name,
        },
    ]


def test_retrieve__custom_revert_tasks__ok(api_client, mocker):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)
    workflow = create_test_workflow(
        user=user,
        tasks_count=3,
        active_task_number=2,
    )
    task_3 = workflow.tasks.get(number=3)
    task_2 = workflow.tasks.get(number=2)
    task_2.revert_task = task_3.api_name
    task_2.save()

    mocker.patch(
        'src.processes.views.task.TaskViewSet.'
        'identify',
    )
    mocker.patch(
        'src.processes.views.task.TaskViewSet.'
        'group',
    )

    # act
    response = api_client.get(f'/v2/tasks/{task_2.id}')

    # assert
    assert response.status_code == 200
    assert response.data['id'] == task_2.id
    assert response.data['revert_tasks'] == [
        {
            'id': task_3.id,
            'name': task_3.name,
            'api_name': task_3.api_name,
        },
    ]
