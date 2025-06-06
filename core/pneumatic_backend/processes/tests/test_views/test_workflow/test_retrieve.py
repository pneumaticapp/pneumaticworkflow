import pytest
from datetime import timedelta
from django.utils import timezone
from pneumatic_backend.processes.models import (
    FieldTemplate,
    Workflow,
    FieldTemplateSelection,
    FileAttachment,
    Delay,
    TaskPerformer,
)
from pneumatic_backend.processes.tests.fixtures import (
    create_test_user,
    create_test_workflow,
    create_test_template,
    create_test_admin,
    create_test_group,
)
from pneumatic_backend.processes.enums import (
    FieldType,
    WorkflowStatus,
    TaskStatus,
    PerformerType,
)


pytestmark = pytest.mark.django_db


def test_retrieve__workflow_data__ok(api_client):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)
    workflow = create_test_workflow(user=user, tasks_count=1)
    task = workflow.tasks.first()

    # act
    response = api_client.get(f'/workflows/{workflow.id}')

    # assert
    assert response.status_code == 200

    assert response.data['id'] == workflow.id
    assert response.data['name'] == workflow.name
    assert response.data['is_external'] is False
    assert response.data['is_urgent'] is False
    assert response.data['due_date_tsp'] is None
    assert response.data['date_created_tsp'] == (
        workflow.date_created.timestamp()
    )
    assert response.data['date_completed_tsp'] is None
    assert response.data['workflow_starter'] == user.id
    assert response.data['is_legacy_template'] is False
    assert response.data['legacy_template_name'] is None
    assert response.data['ancestor_task_id'] is None
    assert response.data['active_tasks_count'] == 1
    assert response.data['active_current_task'] == 1

    task_data = response.data['tasks'][0]
    assert task_data['id'] == task.id
    assert task_data['name'] == task.name
    assert task_data['api_name'] == task.api_name
    assert task_data['description'] == task.description
    assert task_data['number'] == task.number
    assert task_data['delay'] is None
    assert task_data['due_date_tsp'] is None
    assert task_data['date_started_tsp'] == task.date_started.timestamp()
    assert task_data['performers'] == [
        {
            'source_id': user.id,
            'type': 'user',
            'is_completed': False,
            'date_completed_tsp': None,
        }
    ]
    assert task_data['checklists_total'] == 0
    assert task_data['checklists_marked'] == 0
    assert task_data['status'] == TaskStatus.ACTIVE

    template_data = response.data['template']
    assert template_data['id'] == workflow.template_id
    assert template_data['is_active'] == workflow.template.is_active
    assert template_data['name'] == workflow.template.name
    assert template_data['wf_name_template'] == (
        workflow.template.wf_name_template
    )
    assert response.data['owners'] == [user.id]


def test_retrieve__multiple_tasks__ok(api_client):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)
    workflow = create_test_workflow(user=user, tasks_count=2)
    task_1 = workflow.tasks.get(number=1)
    task_2 = workflow.tasks.get(number=2)

    # act
    response = api_client.get(f'/workflows/{workflow.id}')

    # assert
    assert response.status_code == 200
    assert len(response.data['tasks']) == 2
    task_1_data = response.data['tasks'][0]
    assert task_1_data['id'] == task_1.id
    assert task_1_data['status'] == TaskStatus.ACTIVE
    task_2_data = response.data['tasks'][1]
    assert task_2_data['id'] == task_2.id
    assert task_2_data['status'] == TaskStatus.PENDING


def test_retrieve__not_return_skipped_tasks__ok(api_client):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)
    workflow = create_test_workflow(user=user, tasks_count=2)
    task_1 = workflow.tasks.get(number=1)
    task_2 = workflow.tasks.get(number=2)
    task_2.status = TaskStatus.SKIPPED
    task_2.save()

    # act
    response = api_client.get(f'/workflows/{workflow.id}')

    # assert
    assert response.status_code == 200
    assert len(response.data['tasks']) == 1
    task_1_data = response.data['tasks'][0]
    assert task_1_data['id'] == task_1.id
    assert task_1_data['status'] == TaskStatus.ACTIVE


def test_retrieve__task_due_date__ok(api_client):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)
    workflow = create_test_workflow(user=user, tasks_count=1)
    due_date = timezone.now() + timedelta(hours=24)
    due_date_tsp = due_date.timestamp()
    task = workflow.tasks.first()
    task.due_date = due_date
    task.save(update_fields=['due_date'])

    # act
    response = api_client.get(f'/workflows/{workflow.id}')

    # assert
    assert response.status_code == 200
    task_data = response.data['tasks'][0]
    assert task_data['id'] == task.id
    assert task_data['due_date_tsp'] == due_date_tsp


def test_retrieve__workflow_due_date__ok(api_client):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)
    due_date = timezone.now() + timedelta(hours=1)
    due_date_tsp = due_date.timestamp()
    workflow = create_test_workflow(
        user=user,
        tasks_count=1,
        due_date=due_date
    )

    # act
    response = api_client.get(f'/workflows/{workflow.id}')

    # assert
    assert response.status_code == 200
    assert response.data['id'] == workflow.id
    assert response.data['due_date_tsp'] == due_date_tsp
    assert response.data['date_created_tsp'] == (
        workflow.date_created.timestamp()
    )


def test_retrieve__status_completed__ok(api_client):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)
    workflow = create_test_workflow(
        user=user,
        tasks_count=1,
        status=WorkflowStatus.DONE,
    )
    date_completed_tsp = workflow.date_completed.timestamp()

    # act
    response = api_client.get(f'/workflows/{workflow.id}')

    # assert
    assert response.status_code == 200
    assert response.data['id'] == workflow.id
    assert response.data['date_completed_tsp'] == date_completed_tsp


def test_retrieve__status_snoozed__ok(api_client):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)
    workflow = create_test_workflow(
        user=user,
        tasks_count=1,
        status=WorkflowStatus.DELAYED,
    )
    task = workflow.tasks.first()
    delay = Delay.objects.create(
        task=task,
        start_date=timezone.now() - timedelta(hours=1),
        duration=timedelta(days=1)
    )

    # act
    response = api_client.get(f'/workflows/{workflow.id}')

    # assert
    assert response.status_code == 200
    delay_data = response.data['tasks'][0]['delay']
    assert delay_data['start_date_tsp'] == delay.start_date.timestamp()
    assert delay_data['end_date_tsp'] is None
    assert delay_data['duration'] == '1 00:00:00'
    assert delay_data['estimated_end_date_tsp'] == (
        delay.estimated_end_date.timestamp()
    )


def test_retrieve__kickoff_field_user__ok(api_client):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)
    template = create_test_template(
        user=user,
        is_active=True,
        tasks_count=1
    )
    field_template = FieldTemplate.objects.create(
        name='User',
        type=FieldType.USER,
        is_required=True,
        kickoff=template.kickoff_instance,
        order=1,
        template=template
    )

    response = api_client.post(
        path=f'/templates/{template.id}/run',
        data={
            'name': 'Workflow',
            'kickoff': {
                field_template.api_name: user.id
            }
        }
    )
    workflow = Workflow.objects.get(id=response.data['id'])
    field = workflow.kickoff_instance.output.first()

    # act
    response = api_client.get(f'/workflows/{workflow.id}')

    # assert
    assert response.status_code == 200
    field_data = response.data['kickoff']['output'][0]
    assert field_data['id'] == field.id
    assert field_data['type'] == field.type
    assert field_data['is_required'] == field.is_required
    assert field_data['name'] == field.name
    assert field_data['description'] == field.description
    assert field_data['api_name'] == field.api_name
    assert field_data['attachments'] == []
    assert field_data['selections'] == []
    assert field_data['order'] == field.order
    assert field_data['user_id'] == user.id
    # TODO Replace in https://my.pneumatic.app/workflows/18137/
    assert field_data['value'] == str(user.id)  # user.get_full_name()


def test_retrieve__kickoff_field_date__ok(api_client):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)
    template = create_test_template(
        user=user,
        is_active=True,
        tasks_count=1
    )
    field_template = FieldTemplate.objects.create(
        name='Date',
        type=FieldType.DATE,
        is_required=True,
        kickoff=template.kickoff_instance,
        order=1,
        template=template
    )

    response = api_client.post(
        path=f'/templates/{template.id}/run',
        data={
            'name': 'Workflow',
            'kickoff': {
                field_template.api_name: 321651
            }
        }
    )
    workflow = Workflow.objects.get(id=response.data['id'])
    field = workflow.kickoff_instance.output.first()

    # act
    response = api_client.get(f'/workflows/{workflow.id}')

    # assert
    assert response.status_code == 200
    field_data = response.data['kickoff']['output'][0]
    assert field_data['id'] == field.id
    assert field_data['type'] == field.type
    assert field_data['is_required'] == field.is_required
    assert field_data['name'] == field.name
    assert field_data['description'] == field.description
    assert field_data['api_name'] == field.api_name
    assert field_data['attachments'] == []
    assert field_data['selections'] == []
    assert field_data['order'] == field.order
    assert field_data['value'] == str(321651)


def test_retrieve__kickoff_field_with_selections__ok(api_client):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)
    template = create_test_template(
        user=user,
        is_active=True,
        tasks_count=1
    )
    field_template = FieldTemplate.objects.create(
        name='Selections',
        type=FieldType.CHECKBOX,
        is_required=True,
        kickoff=template.kickoff_instance,
        order=1,
        template=template
    )
    selection_template = FieldTemplateSelection.objects.create(
        field_template=field_template,
        value='some value',
        template=template,
    )

    response = api_client.post(
        path=f'/templates/{template.id}/run',
        data={
            'name': 'Workflow',
            'kickoff': {
                field_template.api_name: [selection_template.api_name]
            }
        }
    )
    workflow = Workflow.objects.get(id=response.data['id'])
    field = workflow.kickoff_instance.output.first()
    selection = field.selections.first()

    # act
    response = api_client.get(f'/workflows/{workflow.id}')

    # assert
    assert response.status_code == 200
    field_data = response.data['kickoff']['output'][0]
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


def test_retrieve__kickoff_field_with_attachments__ok(api_client):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)
    template = create_test_template(
        user=user,
        is_active=True,
        tasks_count=1
    )
    field_template = FieldTemplate.objects.create(
        name='Selections',
        type=FieldType.FILE,
        is_required=True,
        kickoff=template.kickoff_instance,
        order=1,
        template=template
    )
    attachment = FileAttachment.objects.create(
        name='john.cena',
        url='https://john.cena/john.cena',
        account_id=user.account_id,
        size=1488,
    )

    response = api_client.post(
        path=f'/templates/{template.id}/run',
        data={
            'name': 'Workflow',
            'kickoff': {
                field_template.api_name: [attachment.id]
            }
        }
    )
    workflow = Workflow.objects.get(id=response.data['id'])
    field = workflow.kickoff_instance.output.first()

    # act
    response = api_client.get(f'/workflows/{workflow.id}')

    # assert
    assert response.status_code == 200
    field_data = response.data['kickoff']['output'][0]
    assert field_data['id'] == field.id
    assert field_data['type'] == field.type
    assert field_data['is_required'] == field.is_required
    assert field_data['name'] == field.name
    assert field_data['description'] == field.description
    assert field_data['api_name'] == field.api_name
    assert field_data['selections'] == []
    assert field_data['order'] == field.order
    assert field_data['user_id'] is None
    assert field_data['value'] == attachment.url
    attachment_data = field_data['attachments'][0]
    assert attachment_data['id'] == attachment.id
    assert attachment_data['name'] == attachment.name
    assert attachment_data['url'] == attachment.url


def test_retrieve__not_admin_user_workflow_member__ok(api_client):
    # arrange
    user = create_test_user()
    not_admin_user = create_test_user(
        account=user.account,
        email='not_admin@test.test',
        is_admin=False,
        is_account_owner=False
    )
    workflow = create_test_workflow(user, tasks_count=1)
    workflow.members.add(not_admin_user)
    api_client.token_authenticate(user=not_admin_user)

    # act
    response = api_client.get(f'/workflows/{workflow.id}')

    # assert
    assert response.status_code == 200
    assert response.data['id'] == workflow.id


def test_retrieve__with_kickoff(api_client):

    # arrange
    user = create_test_user()
    template = create_test_template(
        user=user,
        is_active=True
    )
    kickoff_field = FieldTemplate.objects.create(
        name='User name',
        type=FieldType.STRING,
        is_required=True,
        kickoff=template.kickoff_instance,
        order=1,
        template=template,
    )
    kickoff_field_2 = FieldTemplate.objects.create(
        name='User url',
        type=FieldType.URL,
        is_required=False,
        kickoff=template.kickoff_instance,
        order=2,
        template=template,
    )
    kickoff_field_3 = FieldTemplate.objects.create(
        name='User date',
        type=FieldType.DATE,
        is_required=False,
        kickoff=template.kickoff_instance,
        order=3,
        template=template,
    )
    task = template.tasks.order_by('number').first()
    task.description = (
        '{{ %s }}His name is... {{%s}}{{%s}}!!!' %
        (
            kickoff_field_2.api_name,
            kickoff_field.api_name,
            kickoff_field_3.api_name,
        )
    )
    task.save()
    output_field = FieldTemplate.objects.create(
        type=FieldType.TEXT,
        name='Past name',
        description='Last description',
        task=task,
        template=template,
    )
    second_task = template.tasks.order_by('number')[1]
    second_task.description = (
        '{{ %s }}His name is... {{%s}}!!!' %
        (
            output_field.api_name,
            kickoff_field.api_name,
        )
    )
    second_task.save()
    data = {
        'name': 'Test name',
        'kickoff': {
            kickoff_field.api_name: 'JOHN CENA',
            kickoff_field_2.api_name: None,
        }
    }

    api_client.token_authenticate(user)
    response = api_client.post(
        f'/templates/{template.id}/run',
        data=data,
    )
    workflow_id = response.data['id']

    # act
    response = api_client.get(f'/workflows/{workflow_id}')

    # assert
    assert len(response.data['kickoff']['output']) == 3
    first_output = response.data['kickoff']['output'][0]
    second_output = response.data['kickoff']['output'][1]
    third_output = response.data['kickoff']['output'][2]
    assert first_output['type'] == FieldType.DATE
    assert second_output['type'] == FieldType.URL
    assert third_output['type'] == FieldType.STRING


def test_retrieve__is_external__ok(api_client):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)

    workflow = create_test_workflow(
        user=user,
        is_external=True,
    )

    # act
    response = api_client.get(f'/workflows/{workflow.id}')

    # assert
    assert response.status_code == 200
    assert response.data['is_external'] is True
    assert response.data['workflow_starter'] is None


def test_retrieve__is_urgent__ok(api_client):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)
    template = create_test_template(
        user=user,
        is_active=True,
        tasks_count=1
    )
    workflow = create_test_workflow(
        user=user,
        is_urgent=True,
        template=template
    )

    # act
    response = api_client.get(f'/workflows/{workflow.id}')

    # assert
    assert response.status_code == 200
    assert response.data['id'] == workflow.id
    assert response.data['is_urgent'] is True


def test_retrieve__subprocess__ok(api_client):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)
    template = create_test_template(user=user, tasks_count=1)
    parent_workflow = create_test_workflow(
        user=user,
        template=template
    )
    ancestor_task = parent_workflow.current_task_instance
    sub_workflow = create_test_workflow(
        name='Subworkflow',
        user=user,
        ancestor_task=ancestor_task,
        template=template
    )

    # act
    response = api_client.get(f'/workflows/{sub_workflow.id}')

    # assert
    assert response.status_code == 200
    assert response.data['id'] == sub_workflow.id
    assert response.data['ancestor_task_id'] == ancestor_task.id


def test_retrieve__user_in_group_task_performer__ok(api_client):
    # arrange
    user = create_test_user()
    group_user = create_test_admin(
        account=user.account,
        email='group_user@test.test',
    )
    group = create_test_group(account=user.account, users=[group_user])
    workflow = create_test_workflow(user=user, tasks_count=1)
    task = workflow.tasks.first()
    TaskPerformer.objects.create(
        task_id=task.id,
        type=PerformerType.GROUP,
        group_id=group.id,
    )
    api_client.token_authenticate(group_user)

    # act
    response = api_client.get(f'/workflows/{workflow.id}')

    # assert
    assert response.status_code == 200
    assert response.data['id'] == workflow.id
