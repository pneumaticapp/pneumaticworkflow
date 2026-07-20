from datetime import timedelta

import pytest
from django.utils import timezone

from src.authentication.enums import AuthTokenType
from src.processes.enums import (
    DirectlyStatus,
    FieldType,
    PerformerType,
    TaskStatus,
    WorkflowStatus,
)
from src.processes.messages import workflow as messages
from src.processes.models.workflows.fields import TaskField
from src.processes.models.workflows.task import TaskPerformer
from src.processes.services.events import (
    WorkflowEventService,
)
from src.processes.services.workflow_action import (
    WorkflowActionService,
)
from src.processes.tests.fixtures import (
    create_test_attachment,
    create_test_attachment_for_event,
    create_test_group,
    create_test_owner,
    create_test_template,
    create_test_user,
    create_test_workflow, create_test_account, create_test_admin,
    create_test_not_admin,
)
from src.services.markdown import MarkdownService
from src.utils.validation import ErrorCode

pytestmark = pytest.mark.django_db
datetime_format = '%Y-%m-%dT%H:%M:%S.%fZ'


def test_list__default_ordering__ok(api_client):

    # arrange
    user = create_test_user()
    workflow_1 = create_test_workflow(user, tasks_count=1)
    task_11 = workflow_1.tasks.get(number=1)
    workflow_2 = create_test_workflow(
        user,
        name='Workflow 2',
        tasks_count=1,
    )
    task_21 = workflow_2.tasks.get(number=1)
    task_11.due_date = task_11.date_first_started + timedelta(hours=1)
    task_11.save(update_fields=['due_date'])

    completed_workflow = create_test_workflow(user, tasks_count=1)
    task = completed_workflow.tasks.get(number=1)
    task.status = TaskStatus.COMPLETED
    task.date_completed = timezone.now()
    task.save(update_fields=['status', 'date_completed'])
    TaskPerformer.objects.filter(task_id=task.id, user_id=user.id).update(
        is_completed=True,
        date_completed=task.date_completed,
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.get('/v3/tasks')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 2

    task_21_data = response.data[0]
    assert task_21_data['id'] == task_21.id
    assert task_21_data['name'] == task_21.name
    assert task_21_data['api_name'] == task_21.api_name
    assert task_21_data['workflow_name'] == workflow_2.name
    assert task_21_data['due_date_tsp'] is None
    assert task_21_data['date_started_tsp'] == task_21.date_started.timestamp()
    assert task_21_data['date_completed_tsp'] is None
    assert task_21_data['template_id'] == workflow_2.template_id
    assert task_21_data['template_task_api_name'] == task_21.api_name
    assert task_21_data['is_urgent'] is False
    assert task_21_data['status'] == TaskStatus.ACTIVE

    task_11_data = response.data[1]
    assert task_11_data['id'] == task_11.id
    assert task_11_data['due_date_tsp'] == task_11.due_date.timestamp()
    assert task_11_data['status'] == TaskStatus.ACTIVE


def test_list__user_in_group__ok(api_client):

    # arrange
    user = create_test_user()
    another_user = create_test_user(
        account=user.account,
        email='another@pneumatic.app',
    )
    group = create_test_group(user.account, users=[another_user])
    workflow_1 = create_test_workflow(user, tasks_count=1)
    task_11 = workflow_1.tasks.get(number=1)
    TaskPerformer.objects.filter(
        task=task_11,
    ).update(directly_status=DirectlyStatus.DELETED)
    TaskPerformer.objects.create(
        task_id=task_11.id,
        type=PerformerType.GROUP,
        group_id=group.id,
        directly_status=DirectlyStatus.CREATED,
    )
    workflow_2 = create_test_workflow(user, tasks_count=1, is_urgent=True)
    task_21 = workflow_2.tasks.get(number=1)
    TaskPerformer.objects.create(
        task_id=task_21.id,
        type=PerformerType.GROUP,
        group_id=group.id,
        directly_status=DirectlyStatus.CREATED,
    )
    create_test_workflow(user, tasks_count=1)
    api_client.token_authenticate(user=another_user)

    # act
    response = api_client.get('/v3/tasks')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 2
    assert response.data[0]['id'] == task_21.id
    assert response.data[1]['id'] == task_11.id


def test_list__task_performer_group_empty__ok(api_client):

    # arrange
    user = create_test_user()
    another_user = create_test_user(
        account=user.account,
        email='another@pneumatic.app',
    )
    group = create_test_group(user.account, users=[another_user])
    create_test_group(user.account, name='group 2')
    workflow_1 = create_test_workflow(user, tasks_count=1)
    task_11 = workflow_1.tasks.get(number=1)
    TaskPerformer.objects.filter(
        task=task_11,
    ).update(directly_status=DirectlyStatus.DELETED)
    TaskPerformer.objects.create(
        task_id=task_11.id,
        type=PerformerType.GROUP,
        group_id=group.id,
        directly_status=DirectlyStatus.CREATED,
    )
    workflow_2 = create_test_workflow(user, tasks_count=1, is_urgent=True)
    task_21 = workflow_2.tasks.get(number=1)
    TaskPerformer.objects.create(
        task_id=task_21.id,
        type=PerformerType.GROUP,
        group_id=group.id,
        directly_status=DirectlyStatus.CREATED,
    )
    create_test_workflow(user, tasks_count=1)
    api_client.token_authenticate(user=another_user)

    # act
    response = api_client.get('/v3/tasks')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 2
    assert response.data[0]['id'] == task_21.id
    assert response.data[1]['id'] == task_11.id


def test_list__user_performer_completed__skip(api_client):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    user = create_test_admin(account=account)
    template = create_test_template(user=owner, tasks_count=2, is_active=True)
    workflow = create_test_workflow(user, template=template)
    task = workflow.tasks.get(number=1)
    task.taskperformer_set.all().delete()
    TaskPerformer.objects.create(
        task_id=task.id,
        type=PerformerType.USER,
        user=user,
        is_completed=True,
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.get('/v3/tasks')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 0


def test_list__group_performer_completed__skip(api_client):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    user = create_test_admin(account=account)
    template = create_test_template(user=owner, tasks_count=2, is_active=True)
    workflow = create_test_workflow(user, template=template)
    task = workflow.tasks.get(number=1)
    task.taskperformer_set.all().delete()
    group = create_test_group(account, users=[user])
    TaskPerformer.objects.create(
        task_id=task.id,
        type=PerformerType.GROUP,
        group=group,
        is_completed=True,
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.get('/v3/tasks')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 0


def test_list__group_performer_partitional_completed__skip(api_client):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    user = create_test_admin(account=account)
    user_2 = create_test_not_admin(account=account)
    template = create_test_template(user=owner, tasks_count=2, is_active=True)
    workflow = create_test_workflow(user, template=template)
    task = workflow.tasks.get(number=1)
    task.taskperformer_set.all().delete()
    group = create_test_group(account, users=[user, user_2])
    TaskPerformer.objects.create(
        task_id=task.id,
        type=PerformerType.GROUP,
        group=group,
        completed_users=[user.id],
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.get('/v3/tasks')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 0


def test_list__group_performer_and_user_performer__skip(api_client):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    user = create_test_admin(account=account)
    template = create_test_template(user=owner, tasks_count=2, is_active=True)
    workflow = create_test_workflow(user, template=template)
    task = workflow.tasks.get(number=1)
    task.taskperformer_set.all().delete()
    group = create_test_group(account, users=[user])
    TaskPerformer.objects.create(
        task_id=task.id,
        type=PerformerType.GROUP,
        group=group,
    )
    TaskPerformer.objects.create(
        task_id=task.id,
        type=PerformerType.USER,
        user=user,
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.get('/v3/tasks')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1


def test_list__group_performer_partitional_completed_and_user_performer__skip(
    api_client,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    user = create_test_admin(account=account)
    template = create_test_template(user=owner, tasks_count=2, is_active=True)
    workflow = create_test_workflow(user, template=template)
    task = workflow.tasks.get(number=1)
    task.taskperformer_set.all().delete()
    group = create_test_group(account, users=[user])
    TaskPerformer.objects.create(
        task_id=task.id,
        type=PerformerType.GROUP,
        group=group,
        completed_users=[user.id],
    )
    TaskPerformer.objects.create(
        task_id=task.id,
        type=PerformerType.USER,
        user=user,
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.get('/v3/tasks')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1


def test_list__filter_is_completed_and_group_performer_part_completed__skip(
    api_client,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    user = create_test_admin(account=account)
    user_2 = create_test_not_admin(account=account)
    template = create_test_template(user=owner, tasks_count=2, is_active=True)
    workflow = create_test_workflow(user, template=template)
    task = workflow.tasks.get(number=1)
    task.taskperformer_set.all().delete()
    group = create_test_group(account, users=[user, user_2])
    TaskPerformer.objects.create(
        task_id=task.id,
        type=PerformerType.GROUP,
        group=group,
        completed_users=[user.id],
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.get('/v3/tasks?is_completed=true')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1


def test_list__urgent_tasks_first__ok(api_client):

    # arrange
    user = create_test_user()
    workflow_1 = create_test_workflow(user, tasks_count=1)
    task_11 = workflow_1.tasks.get(number=1)
    workflow_2 = create_test_workflow(user, tasks_count=1, is_urgent=True)
    task_21 = workflow_2.tasks.get(number=1)
    workflow_3 = create_test_workflow(user, tasks_count=1)
    task_31 = workflow_3.tasks.get(number=1)
    api_client.token_authenticate(user=user)

    # act
    response = api_client.get('/v3/tasks')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 3
    assert response.data[0]['id'] == task_21.id
    assert response.data[1]['id'] == task_31.id
    assert response.data[2]['id'] == task_11.id


def test_list__search__ok(api_client, mocker):

    """ Need more tests for search """

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user)
    create_test_workflow(user)

    clear_search_text = 'New search name'
    raw_search_text = f' \r {clear_search_text}\n '
    task = workflow.tasks.get(number=1)
    task.name = clear_search_text
    task.save(update_fields=['name'])

    analysis_mock = mocker.patch(
        'src.analysis.services.AnalyticService.'
        'search_search',
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.get(f'/v3/tasks?search={raw_search_text}')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == task.id

    analysis_mock.assert_called_once_with(
        user=user,
        page='tasks',
        search_text=clear_search_text,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )


def test_list__search__user_performer_twice__remove_duplicate(
    api_client,
    mocker,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    user = create_test_admin(account=account)
    group = create_test_group(account=account, users=[user])
    workflow = create_test_workflow(owner, tasks_count=1)
    task = workflow.tasks.get(number=1)
    TaskPerformer.objects.create(
        task_id=task.id,
        type=PerformerType.GROUP,
        group_id=group.id,
    )
    TaskPerformer.objects.create(
        task_id=task.id,
        type=PerformerType.USER,
        user_id=user.id,
    )

    search_text = 'search'
    task.name = search_text
    task.save(update_fields=['name'])

    mocker.patch('src.analysis.services.AnalyticService.search_search')
    api_client.token_authenticate(user)

    # act
    response = api_client.get(f'/v3/tasks?search={search_text}')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == task.id


def test_list__search__not_found__ok(api_client, mocker):

    """ Need more tests for search """

    # arrange
    user = create_test_user()
    create_test_workflow(user)
    analysis_mock = mocker.patch(
        'src.analysis.services.AnalyticService.'
        'search_search',
    )
    search_text = 'DROP TABLE accounts_account'
    api_client.token_authenticate(user)

    # act
    response = api_client.get(f'/v3/tasks?search={search_text}')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 0

    analysis_mock.assert_called_once_with(
        user=user,
        page='tasks',
        search_text=search_text,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )


def test_list__search__comment__ok(api_client, mocker):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user, tasks_count=1)
    task = workflow.tasks.get(number=1)
    WorkflowEventService.comment_created_event(
        user=user,
        task=task,
        text='some comment text',
    )
    search_text = 'come text'
    workflow_2 = create_test_workflow(user=user, tasks_count=1)
    task_2 = workflow_2.tasks.get(number=1)
    WorkflowEventService.comment_created_event(
        user=user,
        task=task_2,
        text='some camera retext',
    )

    analysis_mock = mocker.patch(
        'src.analysis.services.AnalyticService.'
        'search_search',
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.get(f'/v3/tasks?search={search_text}')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    task = workflow.tasks.get(number=1)
    assert response.data[0]['id'] == task.id
    analysis_mock.assert_called_once_with(
        user=user,
        page='tasks',
        search_text=search_text,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )


def test_list__search__comment__url_as_text__ok(api_client, mocker):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user, tasks_count=1)
    task = workflow.tasks.get(number=1)
    text = 'some **https://pneumo.app** text'
    WorkflowEventService.comment_created_event(
        user=user,
        task=task,
        text=text,
        clear_text=MarkdownService.clear(text),
    )
    search_text = 'pneumo.app'
    analysis_mock = mocker.patch(
        'src.analysis.services.AnalyticService.'
        'search_search',
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.get(f'/v3/tasks?search={search_text}')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    task = workflow.tasks.get(number=1)
    assert response.data[0]['id'] == task.id
    analysis_mock.assert_called_once_with(
        user=user,
        page='tasks',
        search_text=search_text,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )


def test_list__search__comment__markdown__ok(api_client, mocker):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user, tasks_count=1)
    text = 'some -  **[file.here](http://google.com/) value**'
    task = workflow.tasks.get(number=1)
    WorkflowEventService.comment_created_event(
        user=user,
        task=task,
        text=text,
        clear_text=MarkdownService.clear(text),
    )
    search_text = 'file.here'
    analysis_mock = mocker.patch(
        'src.analysis.services.AnalyticService.'
        'search_search',
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.get(f'/v3/tasks?search={search_text}')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    task = workflow.tasks.get(number=1)
    assert response.data[0]['id'] == task.id
    analysis_mock.assert_called_once_with(
        user=user,
        page='tasks',
        search_text=search_text,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )


def test_list__search__not_comment_event__not_found(api_client, mocker):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user, tasks_count=1)
    search_text = 'com tex'
    task = workflow.tasks.get(number=1)
    event = WorkflowEventService.task_complete_event(
        user=user,
        task=task,
    )
    event.text = search_text
    event.save()

    analysis_mock = mocker.patch(
        'src.analysis.services.AnalyticService.'
        'search_search',
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.get(f'/v3/tasks?search={search_text}')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 0
    analysis_mock.assert_called_once_with(
        user=user,
        page='tasks',
        search_text=search_text,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )


def test_list__search__another_task_comment__not_found(api_client, mocker):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(
        user=user,
        tasks_count=2,
        active_task_number=2,
    )
    text = 'some comment text'
    task = workflow.tasks.get(number=1)
    WorkflowEventService.comment_created_event(
        user=user,
        task=task,
        text=text,
        clear_text=MarkdownService.clear(text),
    )
    search_text = 'com tex'
    analysis_mock = mocker.patch(
        'src.analysis.services.AnalyticService.'
        'search_search',
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.get(f'/v3/tasks?search={search_text}')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 0
    analysis_mock.assert_called_once_with(
        user=user,
        page='tasks',
        search_text=search_text,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )


def test_list__search__comment_attachment__not_found(api_client, mocker):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user)
    task = workflow.tasks.get(number=1)
    event = WorkflowEventService.comment_created_event(
        user=user,
        task=task,
        text='comment',
    )
    create_test_attachment_for_event(
        account=user.account,
        event=event,
        file_id='fred_cena_task_list.png',
    )

    mocker.patch(
        'src.analysis.services.AnalyticService.'
        'search_search',
    )
    search_text = 'cena'
    api_client.token_authenticate(user)

    # act
    response = api_client.get(f'/v3/tasks?search={search_text}')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 0


def test_list__search__another_task_comment_attachment__not_found(
    api_client,
    mocker,
):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(
        user=user,
        tasks_count=2,
        active_task_number=2,
    )
    task = workflow.tasks.get(number=1)
    event = WorkflowEventService.comment_created_event(
        user=user,
        task=task,
        text='comment',
    )
    create_test_attachment_for_event(
        account=user.account,
        event=event,
        file_id='fred_cena_another_task.png',
    )

    mocker.patch(
        'src.analysis.services.AnalyticService.'
        'search_search',
    )
    search_text = 'cen'
    api_client.token_authenticate(user)

    # act
    response = api_client.get(f'/v3/tasks?search={search_text}')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 0


def test_list__search__completed_prev_task_output_attachment__not_found(
    api_client,
    mocker,
):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(
        user=user,
        tasks_count=2,
        active_task_number=2,
    )
    task_1 = workflow.tasks.get(number=1)
    TaskField.objects.create(
        task=task_1,
        api_name='api-name-1',
        type=FieldType.FILE,
        workflow=workflow,
        account=user.account,
    )
    create_test_attachment(
        account=user.account,
        file_id='fred_cena_prev_task.txt',
        task=task_1,
        workflow=workflow,
    )

    mocker.patch(
        'src.analysis.services.AnalyticService.'
        'search_search',
    )
    search_text = 'cena'
    api_client.token_authenticate(user)

    # act
    response = api_client.get(f'/v3/tasks?search={search_text}')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 0


def test_list__search__active_task_field_attachment__not_found(
    api_client,
    mocker,
):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user, tasks_count=2)
    task_1 = workflow.tasks.get(number=1)
    TaskField.objects.create(
        task=task_1,
        api_name='api-name-1',
        type=FieldType.FILE,
        workflow=workflow,
        account=user.account,
    )
    create_test_attachment(
        account=user.account,
        file_id='fred_cena_active_task.txt',
        task=task_1,
        workflow=workflow,
    )

    mocker.patch(
        'src.analysis.services.AnalyticService.'
        'search_search',
    )
    search_text = 'https://test.com/test.txt'
    api_client.token_authenticate(user)

    # act
    response = api_client.get(f'/v3/tasks?search={search_text}')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 0


def test_list__search__active_task_description__ok(
    api_client,
    mocker,
):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user, tasks_count=2)
    description = 'some [file.here](http://google.com/) value'
    task_1 = workflow.tasks.get(number=1)
    task_1.description = description
    task_1.clear_description = MarkdownService.clear(description)
    task_1.save()
    mocker.patch(
        'src.analysis.services.AnalyticService.search_search',
    )
    search_text = 'file.here'
    api_client.token_authenticate(user)

    # act
    response = api_client.get(f'/v3/tasks?search={search_text}')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == task_1.id


def test_list__search__not_active_task_description__not_found(
    api_client,
    mocker,
):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(
        user=user,
        tasks_count=3,
        active_task_number=2,
    )
    description = 'some [file.here](http://google.com/) value'
    task_1 = workflow.tasks.get(number=1)
    task_1.description = description
    task_1.clear_description = MarkdownService.clear(description)
    task_1.save()
    task_3 = workflow.tasks.get(number=3)
    task_3.description = description
    task_3.clear_description = MarkdownService.clear(description)
    task_3.save()
    create_test_workflow(user)
    search_text = 'file'
    mocker.patch(
        'src.analysis.services.AnalyticService.search_search',
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.get(f'/v3/tasks?search={search_text}')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 0


def test_list__search__kickoff_description__not_found(api_client, mocker):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user)
    kickoff = workflow.kickoff_instance
    description = 'some [file.here](http://google.com/) value'
    kickoff.description = description
    kickoff.clear_description = MarkdownService.clear(description)
    kickoff.save()
    create_test_workflow(user)
    search_text = 'file'
    mocker.patch(
        'src.analysis.services.AnalyticService.search_search',
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.get(f'/v3/tasks?search={search_text}')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 0


def test_list__search_priority_1__ok(api_client, mocker):

    """ Search priority:
        1. Task description (weight B);
        3. Task TaskField value (weight C);
        4. WorkflowEvent comment text (weight D);
    """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    search_text = 'search'

    workflow_2 = create_test_workflow(owner, tasks_count=1)
    task_2 = workflow_2.tasks.get(number=1)
    TaskField.objects.create(
        task=task_2,
        type=FieldType.STRING,
        workflow=workflow_2,
        account=account,
        value=search_text,
    )

    workflow_1 = create_test_workflow(owner, tasks_count=1)
    task_1 = workflow_1.tasks.get(number=1)
    task_1.description = search_text
    task_1.save()

    workflow_3 = create_test_workflow(owner, tasks_count=1)
    task_3 = workflow_3.tasks.get(number=1)
    WorkflowEventService.comment_created_event(
        user=owner,
        task=task_3,
        text=search_text,
        after_create_actions=False,
    )
    create_test_workflow(owner, tasks_count=1)

    mocker.patch('src.analysis.services.AnalyticService.search_search')
    api_client.token_authenticate(owner)

    # act
    response = api_client.get(f'/v3/tasks?search={search_text}')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 3
    assert response.data[0]['id'] == task_1.id
    assert response.data[1]['id'] == task_2.id
    assert response.data[2]['id'] == task_3.id


def test_list__search_priority_2__ok(api_client, mocker):

    """ Search priority:
        1. Workflow name (weight A)
        2. Task TaskField value (weight C);
        3. Task name (weight D);
    """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    search_text = 'search'

    # workflow_1 = create_test_workflow(owner, tasks_count=1)

    workflow_2 = create_test_workflow(owner, tasks_count=1)
    task_2 = workflow_2.tasks.get(number=1)
    TaskField.objects.create(
        task=task_2,
        type=FieldType.URL,
        workflow=workflow_2,
        account=account,
        value=search_text,
    )

    workflow_1 = create_test_workflow(owner, tasks_count=1, name=search_text)
    task_1 = workflow_1.tasks.get(number=1)

    workflow_3 = create_test_workflow(owner, tasks_count=1)
    task_3 = workflow_3.tasks.get(number=1)
    task_3.name = search_text
    task_3.save()

    mocker.patch('src.analysis.services.AnalyticService.search_search')
    api_client.token_authenticate(owner)

    # act
    response = api_client.get(f'/v3/tasks?search={search_text}')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 3
    assert response.data[0]['id'] == task_1.id
    assert response.data[1]['id'] == task_2.id
    assert response.data[2]['id'] == task_3.id


@pytest.mark.parametrize(
    'field_type',
    (
        FieldType.TEXT,
        FieldType.STRING,
        FieldType.RADIO,
        FieldType.CHECKBOX,
        FieldType.DROPDOWN,
        FieldType.DATE,
        FieldType.USER,
        FieldType.URL,
    ),
)
def test_list__search__in_active_task_field_value__ok(
    api_client,
    mocker,
    field_type,
):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user, tasks_count=2)
    task_1 = workflow.tasks.get(number=1)
    value = 'text fred boy some'
    TaskField.objects.create(
        task=task_1,
        api_name='api-name-1',
        type=field_type,
        workflow=workflow,
        value=value,
        clear_value=MarkdownService.clear(value),
        account=user.account,
    )
    mocker.patch(
        'src.analysis.services.AnalyticService.'
        'search_search',
    )
    search_text = 'fred'
    api_client.token_authenticate(user)

    # act
    response = api_client.get(f'/v3/tasks?search={search_text}')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == task_1.id


@pytest.mark.parametrize(
    'field_type',
    (
        FieldType.TEXT,
        FieldType.STRING,
        FieldType.RADIO,
        FieldType.CHECKBOX,
        FieldType.DROPDOWN,
        FieldType.DATE,
        FieldType.USER,
        FieldType.URL,
    ),
)
def test_list__search__in_kickoff_field_value__not_found(
    api_client,
    mocker,
    field_type,
):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user, tasks_count=2)
    workflow.tasks.get(number=1)
    value = 'text <fred@boy.com> some'
    TaskField.objects.create(
        kickoff=workflow.kickoff_instance,
        api_name='api-name-1',
        type=field_type,
        workflow=workflow,
        value=value,
        clear_value=MarkdownService.clear(value),
        account=user.account,
    )
    mocker.patch(
        'src.analysis.services.AnalyticService.'
        'search_search',
    )
    search_text = 'fred@boy.com'
    api_client.token_authenticate(user)

    # act
    response = api_client.get(f'/v3/tasks?search={search_text}')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 0


@pytest.mark.parametrize(
    'field_type',
    (
        FieldType.FILE,
    ),
)
def test_list__search__in_excluded_field_value__not_found(
    api_client,
    mocker,
    field_type,
):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user, tasks_count=2)
    task_1 = workflow.tasks.get(number=1)
    value = 'text fredy boy some'
    TaskField.objects.create(
        task=task_1,
        api_name='api-name-1',
        type=field_type,
        workflow=workflow,
        value=value,
        clear_value=MarkdownService.clear(value),
        account=user.account,
    )
    mocker.patch(
        'src.analysis.services.AnalyticService.'
        'search_search',
    )
    search_text = 'fred'
    api_client.token_authenticate(user)

    # act
    response = api_client.get(f'/v3/tasks?search={search_text}')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 0


def test_list__search__full_uri_in_field__ok(
    api_client,
    mocker,
):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user, tasks_count=2)
    task_1 = workflow.tasks.get(number=1)
    value = 'https://translate.com/some-page?sl=ru&tl=ru&op=taranslate'
    TaskField.objects.create(
        task=task_1,
        api_name='api-name-1',
        type=FieldType.URL,
        workflow=workflow,
        value=value,
        clear_value=MarkdownService.clear(value),
        account=user.account,
    )
    mocker.patch(
        'src.analysis.services.AnalyticService.'
        'search_search',
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        '/v3/tasks',
        data={'search': value},
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == task_1.id


def test_list__search__domain__ok(
    api_client,
    mocker,
):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user, tasks_count=1)
    task_1 = workflow.tasks.get(number=1)
    value = 'https://translate.com/some-page?sl=ru&tl=ru&op=taranslate'
    TaskField.objects.create(
        task=task_1,
        api_name='api-name-1',
        type=FieldType.URL,
        workflow=workflow,
        value=value,
        clear_value=MarkdownService.clear(value),
        account=user.account,
    )
    mocker.patch(
        'src.analysis.services.AnalyticService.'
        'search_search',
    )
    search_text = 'translate.com'
    api_client.token_authenticate(user)

    # act
    response = api_client.get(f'/v3/tasks?search={search_text}')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == task_1.id


def test_list__search__markdown_filename_in_text_field__ok(
    api_client,
    mocker,
):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user, tasks_count=2)
    task_1 = workflow.tasks.get(number=1)
    value = (
        'Final version \n *[somefile.txt]'
        '(https://storage.googleapis.com/file.txt '
        '"attachment_id:13152 entityType:file")*'
    )
    TaskField.objects.create(
        workflow=workflow,
        task=task_1,
        api_name='api-name-1',
        type=FieldType.TEXT,
        value=value,
        clear_value=MarkdownService.clear(value),
        account=user.account,
    )

    mocker.patch(
        'src.analysis.services.AnalyticService.'
        'search_search',
    )
    search_text = 'somefile.txt'
    api_client.token_authenticate(user)

    # act
    response = api_client.get(f'/v3/tasks?search={search_text}')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == task_1.id


def test_list__search__url_in_text_field__ok(
    api_client,
    mocker,
):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user, tasks_count=2)
    task_1 = workflow.tasks.get(number=1)
    value = (
        'Final version \n-  **https://www.search.com/file.txt** here'
    )
    TaskField.objects.create(
        workflow=workflow,
        task=task_1,
        api_name='api-name-1',
        type=FieldType.TEXT,
        value=value,
        clear_value=MarkdownService.clear(value),
        account=user.account,
    )
    mocker.patch(
        'src.analysis.services.AnalyticService.'
        'search_search',
    )
    search_text = 'search.com/file.txt'
    api_client.token_authenticate(user)

    # act
    response = api_client.get(f'/v3/tasks?search={search_text}')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == task_1.id


def test_list__search__email_in_text_field__ok(
    api_client,
    mocker,
):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user, tasks_count=2)
    task_1 = workflow.tasks.get(number=1)
    value = (
        'Final version \n-  **master@test.com** here'
    )
    TaskField.objects.create(
        workflow=workflow,
        task=task_1,
        api_name='api-name-1',
        type=FieldType.TEXT,
        value=value,
        clear_value=MarkdownService.clear(value),
        account=user.account,
    )

    mocker.patch(
        'src.analysis.services.AnalyticService.'
        'search_search',
    )
    search_text = 'master@test.com'
    api_client.token_authenticate(user)

    # act
    response = api_client.get(f'/v3/tasks?search={search_text}')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == task_1.id


def test_list__search__prev_task_markdown_filename_in_text__not_found(
    api_client,
    mocker,
):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(
        user=user,
        tasks_count=2,
        active_task_number=2,
    )
    task_1 = workflow.tasks.get(number=1)
    value = (
        'Final version \n [result: somefile.txt]'
        '(https://storage.googleapis.com/file.txt '
        '"attachment_id:13152 entityType:file")'
    )
    TaskField.objects.create(
        workflow=workflow,
        task=task_1,
        api_name='api-name-1',
        type=FieldType.TEXT,
        value=value,
        clear_value=MarkdownService.clear(value),
        account=user.account,
    )

    mocker.patch(
        'src.analysis.services.AnalyticService.'
        'search_search',
    )
    search_text = 'somefile.txt'
    api_client.token_authenticate(user)

    # act
    response = api_client.get(f'/v3/tasks?search={search_text}')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 0


def test_list__search__kickoff_field__not_found(
    api_client,
    mocker,
):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user, tasks_count=1)
    value = 'https://translate.com/some-page?sl=ru&tl=ru&op=taranslate'
    TaskField.objects.create(
        kickoff=workflow.kickoff_instance,
        api_name='api-name-1',
        type=FieldType.URL,
        workflow=workflow,
        value=value,
        clear_value=MarkdownService.clear(value),
        account=user.account,
    )
    mocker.patch(
        'src.analysis.services.AnalyticService.'
        'search_search',
    )
    search_text = 'translate.com'
    api_client.token_authenticate(user)

    # act
    response = api_client.get(f'/v3/tasks?search={search_text}')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 0


def test_list__ordering_by_date__ok(api_client):

    # arrange
    user = create_test_user()
    workflow_1 = create_test_workflow(user, tasks_count=2)
    task_11 = workflow_1.tasks.get(number=1)
    workflow_2 = create_test_workflow(user, tasks_count=2)
    task_21 = workflow_2.tasks.get(number=1)
    api_client.token_authenticate(user=user)

    # act
    response = api_client.get('/v3/tasks?ordering=date')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 2
    assert response.data[0]['id'] == task_11.id
    assert response.data[1]['id'] == task_21.id


def test_list__ordering_by_reversed_date__ok(api_client):

    # arrange
    user = create_test_user()
    workflow_1 = create_test_workflow(user, tasks_count=1)
    task_11 = workflow_1.tasks.get(number=1)
    workflow_2 = create_test_workflow(user, tasks_count=1)
    task_21 = workflow_2.tasks.get(number=1)
    api_client.token_authenticate(user=user)

    # act
    response = api_client.get('/v3/tasks?ordering=-date')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 2
    assert response.data[0]['id'] == task_21.id
    assert response.data[1]['id'] == task_11.id


def test_list__ordering_by_completed__ok(api_client):

    # arrange
    user = create_test_user()
    date_completed_1 = timezone.now()
    date_completed_2 = date_completed_1 + timedelta(hours=1)
    workflow_1 = create_test_workflow(user, tasks_count=1)
    task_11 = workflow_1.tasks.get(number=1)
    task_11.status = TaskStatus.COMPLETED
    task_11.date_completed = date_completed_1
    task_11.save(update_fields=['status', 'date_completed'])
    TaskPerformer.objects.filter(task_id=task_11.id, user_id=user.id).update(
        is_completed=True,
        date_completed=date_completed_1,
    )
    workflow_2 = create_test_workflow(user, tasks_count=1)
    task_21 = workflow_2.tasks.get(number=1)
    task_21.status = TaskStatus.COMPLETED
    task_21.date_completed = date_completed_2
    task_21.save(update_fields=['status', 'date_completed'])
    TaskPerformer.objects.filter(task_id=task_21.id, user_id=user.id).update(
        is_completed=True,
        date_completed=date_completed_2,
    )
    create_test_workflow(user, tasks_count=1)
    api_client.token_authenticate(user=user)

    # act
    response = api_client.get(
        '/v3/tasks?ordering=completed&is_completed=true',
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 2
    task_11.refresh_from_db()
    assert response.data[0]['id'] == task_11.id
    assert response.data[0]['date_started_tsp'] == (
        task_11.date_started.timestamp()
    )
    assert response.data[0]['date_completed_tsp'] == (
        task_11.date_completed.timestamp()
    )
    assert response.data[0]['status'] == TaskStatus.COMPLETED
    assert response.data[1]['id'] == task_21.id
    assert response.data[1]['date_started_tsp'] is not None
    assert response.data[1]['date_completed_tsp'] is not None
    assert response.data[1]['status'] == TaskStatus.COMPLETED


def test_list__ordering_by_reversed_completed__ok(api_client):

    # arrange
    user = create_test_user()
    date_completed_1 = timezone.now()
    date_completed_2 = date_completed_1 + timedelta(hours=1)
    workflow_1 = create_test_workflow(user, tasks_count=1)
    task_11 = workflow_1.tasks.get(number=1)
    task_11.status = TaskStatus.COMPLETED
    task_11.date_completed = date_completed_1
    task_11.save(update_fields=['status', 'date_completed'])
    TaskPerformer.objects.filter(task_id=task_11.id, user_id=user.id).update(
        is_completed=True,
        date_completed=date_completed_1,
    )
    workflow_2 = create_test_workflow(user, tasks_count=1)
    task_21 = workflow_2.tasks.get(number=1)
    task_21.status = TaskStatus.COMPLETED
    task_21.date_completed = date_completed_2
    task_21.save(update_fields=['status', 'date_completed'])
    TaskPerformer.objects.filter(task_id=task_21.id, user_id=user.id).update(
        is_completed=True,
        date_completed=date_completed_2,
    )
    create_test_workflow(user, tasks_count=1)
    api_client.token_authenticate(user=user)

    # act
    response = api_client.get(
        '/v3/tasks?ordering=-completed&is_completed=true',
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 2
    assert response.data[0]['id'] == task_21.id
    assert response.data[1]['id'] == task_11.id


def test_list__ordering_by_completed_required_completion_by_all__ok(
    api_client,
):

    # arrange
    user = create_test_user()
    user_2 = create_test_user(account=user.account, email='user2@test.test')
    template = create_test_template(
        user=user,
        tasks_count=1,
    )
    template_task = template.tasks.get(number=1)
    template_task.require_completion_by_all = True
    template_task.save()
    template_task.add_raw_performer(user_2)

    date_completed_1 = timezone.now()
    date_completed_2 = date_completed_1 + timedelta(hours=1)
    workflow_1 = create_test_workflow(user, template=template)
    task_11 = workflow_1.tasks.get(number=1)
    TaskPerformer.objects.filter(task_id=task_11.id, user_id=user.id).update(
        is_completed=True,
        date_completed=date_completed_1,
    )
    workflow_2 = create_test_workflow(user, tasks_count=1)
    task_21 = workflow_2.tasks.get(number=1)
    task_21.status = TaskStatus.COMPLETED
    task_21.date_completed = date_completed_2
    task_21.save(update_fields=['status', 'date_completed'])
    TaskPerformer.objects.filter(task_id=task_21.id, user_id=user.id).update(
        is_completed=True,
        date_completed=date_completed_2,
    )
    create_test_workflow(user, tasks_count=1)
    api_client.token_authenticate(user=user)

    # act
    response = api_client.get(
        '/v3/tasks?ordering=completed&is_completed=true',
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 2
    assert response.data[0]['id'] == task_11.id
    assert response.data[1]['id'] == task_21.id

    task_11.refresh_from_db()
    assert task_11.is_completed is False
    assert task_11.date_completed is None
    task_performer_1 = task_11.taskperformer_set.get(user_id=user.id)
    assert task_performer_1.is_completed is True
    assert task_performer_1.date_completed is not None
    task_performer_2 = task_11.taskperformer_set.get(user_id=user_2.id)
    assert task_performer_2.is_completed is False
    assert task_performer_2.date_completed is None

    task_21.refresh_from_db()
    assert task_21.is_completed is True
    assert task_21.date_completed is not None
    task_performer_3 = task_21.taskperformer_set.get(user_id=user.id)
    assert task_performer_3.is_completed is True
    assert task_performer_3.date_completed is not None

    assert task_performer_3.date_completed > task_performer_1.date_completed


def test_list__ordering_by_completed_reversed_required_completion_by_all__ok(
    api_client,
):

    # arrange
    user = create_test_user()
    user_2 = create_test_user(account=user.account, email='user2@test.test')
    template = create_test_template(
        user=user,
        tasks_count=1,
    )
    template_task = template.tasks.get(number=1)
    template_task.require_completion_by_all = True
    template_task.save()
    template_task.add_raw_performer(user_2)

    date_completed_1 = timezone.now()
    date_completed_2 = date_completed_1 + timedelta(hours=1)
    workflow_1 = create_test_workflow(user, template=template)
    task_11 = workflow_1.tasks.get(number=1)
    TaskPerformer.objects.filter(task_id=task_11.id, user_id=user.id).update(
        is_completed=True,
        date_completed=date_completed_1,
    )
    workflow_2 = create_test_workflow(user, tasks_count=1)
    task_21 = workflow_2.tasks.get(number=1)
    task_21.status = TaskStatus.COMPLETED
    task_21.date_completed = date_completed_2
    task_21.save(update_fields=['status', 'date_completed'])
    TaskPerformer.objects.filter(task_id=task_21.id, user_id=user.id).update(
        is_completed=True,
        date_completed=date_completed_2,
    )
    create_test_workflow(user, tasks_count=1)
    api_client.token_authenticate(user=user)

    # act
    response = api_client.get(
        '/v3/tasks?ordering=-completed&is_completed=true',
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 2
    assert response.data[0]['id'] == task_21.id
    assert response.data[1]['id'] == task_11.id


def test_list__completed__non_completed_performers__not_view_in_list(
    api_client,
):

    # arrange
    user = create_test_user(is_account_owner=True)
    user_2 = create_test_user(
        email='test@test.test',
        account=user.account,
        is_account_owner=False,
    )
    template = create_test_template(user=user, tasks_count=2, is_active=True)
    template_task_1 = template.tasks.get(number=1)
    template_task_1.add_raw_performer(user_2)
    workflow = create_test_workflow(user, template=template)
    task = workflow.tasks.get(number=1)
    date_completed = timezone.now()
    task.status = TaskStatus.COMPLETED
    task.date_completed = date_completed
    task.save(update_fields=['status', 'date_completed'])
    task.taskperformer_set.update(
        is_completed=True,
        date_completed=date_completed,
    )
    api_client.token_authenticate(user=user_2)

    # act
    response = api_client.get('/v3/tasks?is_completed=true')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1


def test_list__ordering_by_overdue__ok(api_client):

    # arrange
    user = create_test_user()
    workflow_1 = create_test_workflow(user, tasks_count=1)
    task_11 = workflow_1.tasks.get(number=1)
    task_11.due_date = task_11.date_first_started + timedelta(hours=1)
    task_11.save(update_fields=['due_date'])

    workflow_2 = create_test_workflow(user, tasks_count=1)
    task_21 = workflow_2.tasks.get(number=1)
    task_21.due_date = task_21.date_first_started + timedelta(hours=2)
    task_21.save(update_fields=['due_date'])

    workflow_3 = create_test_workflow(user, tasks_count=1)
    task_31 = workflow_3.tasks.get(number=1)
    api_client.token_authenticate(user=user)

    # act
    response = api_client.get('/v3/tasks?ordering=overdue')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 3
    assert response.data[0]['id'] == task_11.id
    assert response.data[0]['due_date_tsp'] == task_11.due_date.timestamp()
    assert response.data[1]['id'] == task_21.id
    assert response.data[1]['due_date_tsp'] == task_21.due_date.timestamp()
    assert response.data[2]['id'] == task_31.id
    assert response.data[2]['due_date_tsp'] is None


def test_list__ordering_by_reversed_overdue__ok(api_client):

    # arrange
    user = create_test_user()
    workflow_1 = create_test_workflow(user, tasks_count=1)
    task_11 = workflow_1.tasks.get(number=1)
    task_11.due_date = task_11.date_first_started + timedelta(hours=1)
    task_11.save(update_fields=['due_date'])

    workflow_2 = create_test_workflow(user, tasks_count=1)
    task_21 = workflow_2.tasks.get(number=1)
    task_21.due_date = task_21.date_first_started + timedelta(hours=2)
    task_21.save(update_fields=['due_date'])

    workflow_3 = create_test_workflow(user, tasks_count=1)
    task_31 = workflow_3.tasks.get(number=1)
    api_client.token_authenticate(user=user)

    # act
    response = api_client.get('/v3/tasks?ordering=-overdue')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 3
    assert response.data[0]['id'] == task_31.id
    assert response.data[1]['id'] == task_21.id
    assert response.data[2]['id'] == task_11.id


def test_list__filter_assigned_to__ok(api_client):

    # arrange
    user = create_test_user(is_admin=True)
    user2 = create_test_user(account=user.account, email='test@test.test')
    create_test_workflow(user, tasks_count=1)
    workflow = create_test_workflow(user2, tasks_count=1)
    task = workflow.tasks.get(number=1)
    api_client.token_authenticate(user=user)

    # act
    response = api_client.get(f'/v3/tasks?assigned_to={user2.id}')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == task.id


def test_list__filter_is_completed_false__running_wf__ok(api_client):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(
        name='Workflow with running task',
        user=user,
        tasks_count=1,
    )
    task = workflow.tasks.get(number=1)
    api_client.token_authenticate(user)

    # act
    response = api_client.get('/v3/tasks?is_completed=false')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == task.id


def test_list__filter_is_completed_false__running_wf_completed_task__ok(
    api_client,
):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(
        name='Workflow with completed task',
        user=user,
        tasks_count=2,
        active_task_number=2,
    )
    task = workflow.tasks.get(number=2)
    api_client.token_authenticate(user)

    # act
    response = api_client.get('/v3/tasks?is_completed=false')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == task.id


def test_list__filter_is_completed_false__another_user_task__not_found(
    api_client,
):

    # arrange
    user = create_test_user()
    user_2 = create_test_user(email='test@test.test')
    create_test_workflow(
        name='Another user running task',
        user=user_2,
        tasks_count=1,
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.get('/v3/tasks?is_completed=false')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 0


def test_list__filter_is_completed_false__done_wf__not_found(api_client):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(
        name='Completed workflow',
        user=user,
        tasks_count=1,
    )
    task = workflow.tasks.get(number=1)
    date_completed = timezone.now()
    task.status = TaskStatus.COMPLETED
    task.date_completed = date_completed
    task.save(update_fields=['status', 'date_completed'])
    TaskPerformer.objects.filter(task_id=task.id, user_id=user.id).update(
        is_completed=True,
        date_completed=date_completed,
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.get('/v3/tasks?is_completed=false')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 0


def test_list__filter_is_completed_false_delayed_wf__not_found(api_client):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(
        name='Delayed workflow',
        user=user,
        tasks_count=2,
        active_task_number=2,
    )
    workflow.status = WorkflowStatus.DELAYED
    workflow.save(update_fields=['status'])
    api_client.token_authenticate(user)

    # act
    response = api_client.get('/v3/tasks?is_completed=false')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 0


def test_list__filter_is_completed_false_terminated_wf__not_found(api_client):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(
        name='Terminated workflow',
        user=user,
        tasks_count=2,
        active_task_number=2,
    )
    service = WorkflowActionService(workflow=workflow, user=user)
    service.terminate_workflow()
    api_client.token_authenticate(user)

    # act
    response = api_client.get('/v3/tasks?is_completed=false')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 0


def test_list__filter_is_completed_false_ended_wf__not_found(api_client):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(
        name='Ended workflow',
        user=user,
        tasks_count=2,
        active_task_number=2,
    )
    workflow.status = WorkflowStatus.DONE
    workflow.save()
    api_client.token_authenticate(user)

    # act
    response = api_client.get('/v3/tasks?is_completed=false')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 0


def test_list__filter_is_completed_true__running_wf__not_found(api_client):

    # arrange
    user = create_test_user()
    create_test_workflow(
        name='Workflow with running task',
        user=user,
        tasks_count=1,
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.get('/v3/tasks?is_completed=true')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 0


def test_list__filter_is_completed_true__running_wf_completed_task__ok(
    api_client,
):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(
        name='Workflow with completed task',
        user=user,
        tasks_count=2,
        active_task_number=2,
    )
    task = workflow.tasks.get(number=1)
    api_client.token_authenticate(user)

    # act
    response = api_client.get('/v3/tasks?is_completed=true')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == task.id


def test_list__filter_is_completed_true__another_user_task__not_found(
    api_client,
):

    # arrange
    user = create_test_user()
    user_2 = create_test_user(email='test@test.test')
    workflow = create_test_workflow(
        name='Another user running task',
        user=user_2,
        tasks_count=1,
    )
    task = workflow.tasks.get(number=1)
    date_completed = timezone.now()
    task.status = TaskStatus.COMPLETED
    task.date_completed = date_completed
    task.save(update_fields=['status', 'date_completed'])
    TaskPerformer.objects.filter(task_id=task.id, user_id=user_2.id).update(
        is_completed=True,
        date_completed=date_completed,
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.get('/v3/tasks?is_completed=true')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 0


def test_list__filter_is_completed_true__done_wf__ok(api_client):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(
        name='Completed workflow',
        user=user,
        tasks_count=1,
    )
    task = workflow.tasks.get(number=1)
    date_completed = timezone.now()
    task.status = TaskStatus.COMPLETED
    task.date_completed = date_completed
    task.save(update_fields=['status', 'date_completed'])
    TaskPerformer.objects.filter(task_id=task.id, user_id=user.id).update(
        is_completed=True,
        date_completed=date_completed,
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.get('/v3/tasks?is_completed=true')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == task.id


def test_list__filter_is_completed_true__delayed_wf__ok(api_client):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(
        name='Delayed workflow',
        user=user,
        tasks_count=2,
        active_task_number=2,
    )
    workflow.status = WorkflowStatus.DELAYED
    workflow.save(update_fields=['status'])
    task = workflow.tasks.get(number=1)
    api_client.token_authenticate(user)

    # act
    response = api_client.get('/v3/tasks?is_completed=true')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == task.id


def test_list__filter_is_completed_true_terminated_wf__not_found(api_client):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(
        name='Terminated workflow',
        user=user,
        tasks_count=2,
        active_task_number=2,
    )
    service = WorkflowActionService(workflow=workflow, user=user)
    service.terminate_workflow()
    api_client.token_authenticate(user)

    # act
    response = api_client.get('/v3/tasks?is_completed=true')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 0


def test_list__filter_is_completed_true_ended_wf__ok(api_client):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(
        name='Ended workflow',
        user=user,
        tasks_count=2,
        active_task_number=2,
    )
    workflow.status = WorkflowStatus.DONE
    workflow.save()
    task = workflow.tasks.get(number=1)
    api_client.token_authenticate(user)

    # act
    response = api_client.get('/v3/tasks?is_completed=true')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == task.id


def test_list__filter_template_id__ok(api_client):

    # arrange
    user = create_test_user()
    template_1 = create_test_template(user, is_active=True)
    template_2 = create_test_template(user, is_active=True)

    workflow_1 = create_test_workflow(user, template=template_1, tasks_count=1)
    task_11 = workflow_1.tasks.get(number=1)
    workflow_2 = create_test_workflow(user, template=template_1, tasks_count=1)
    task_21 = workflow_2.tasks.get(number=1)
    create_test_workflow(user, template=template_2, tasks_count=1)
    api_client.token_authenticate(user=user)

    # act
    response = api_client.get(f'/v3/tasks?template_id={template_1.id}')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 2
    assert response.data[0]['id'] == task_21.id
    assert response.data[1]['id'] == task_11.id


def test_list__filter_template_task_api_name__ok(api_client):

    # arrange
    user = create_test_user()
    template_1 = create_test_template(user, is_active=True)
    template_2 = create_test_template(user, is_active=True)

    workflow_1 = create_test_workflow(user, template=template_1, tasks_count=1)
    task_11 = workflow_1.tasks.get(number=1)
    workflow_2 = create_test_workflow(user, template=template_1, tasks_count=1)
    task_21 = workflow_2.tasks.get(number=1)
    create_test_workflow(user, template=template_2, tasks_count=1)
    api_client.token_authenticate(user=user)

    # act
    response = api_client.get(
        path='/v3/tasks',
        data={
            'template_task_api_name': task_11.api_name,
        },
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 2
    assert response.data[0]['id'] == task_21.id
    assert response.data[1]['id'] == task_11.id


def test_list__filter_template_task_api_name__not_found(api_client):

    # arrange
    user = create_test_user()
    template_1 = create_test_template(user, is_active=True)
    create_test_workflow(user, template=template_1, tasks_count=1)
    api_client.token_authenticate(user=user)

    # act
    response = api_client.get(
        path='/v3/tasks',
        data={
            'template_task_api_name': 'not_found',
        },
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 0


def test_list__pagination__ok(api_client):

    # arrange
    user = create_test_user()
    workflow_1 = create_test_workflow(user, tasks_count=1)
    task_11 = workflow_1.tasks.get(number=1)
    workflow_2 = create_test_workflow(user, tasks_count=1)
    task_21 = workflow_2.tasks.get(number=1)
    create_test_workflow(user, tasks_count=1)
    api_client.token_authenticate(user=user)

    # act
    response = api_client.get('/v3/tasks?limit=2&offset=1')

    # assert
    assert response.status_code == 200
    assert response.data['count'] == 3
    assert len(response.data['results']) == 2
    assert response.data['results'][0]['id'] == task_21.id
    assert response.data['results'][1]['id'] == task_11.id


def test_list__exclude_delayed_tasks__ok(api_client):

    # arrange
    user = create_test_user()
    delayed_workflow = create_test_workflow(
        user=user,
        tasks_count=2,
        with_delay=True,
        active_task_number=2,
    )
    task = delayed_workflow.tasks.get(number=2)
    task.status = TaskStatus.DELAYED
    task.save(update_fields=['status'])
    api_client.token_authenticate(user=user)

    # act
    response = api_client.get('/v3/tasks')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 0


def test_list__uml_backslash_search__ok(api_client):

    # arrange
    user = create_test_owner()
    workflow = create_test_workflow(
        user=user,
        tasks_count=1,
        name='UML Project',
    )
    task = workflow.tasks.first()
    task.name = 'Create UML diagrams'
    task.save()
    WorkflowEventService.comment_created_event(
        user=user,
        task=task,
        text='create UML class',
        after_create_actions=False,
    )
    other_workflow = create_test_workflow(
        user=user,
        tasks_count=1,
    )
    other_task = other_workflow.tasks.first()
    WorkflowEventService.comment_created_event(
        user=user,
        task=other_task,
        text='task',
        after_create_actions=False,
    )
    search_query = "'uml\\':"
    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        '/v3/tasks',
        data={
            'search': search_query,
            'ordering': 'date',
        },
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == task.id


@pytest.mark.parametrize(
    "injection", [
        "'; DROP 'test\\': users & --",
        "1' OR '1'='1 test",
        "test'--",
        "test ' UNION SELECT * FROM accounts_user --",
        "\\'; DELETE FROM processes_task; -- test",
        "test'); INSERT INTO users VALUES ('hack'); --",
    ],
)
def test_list__sql_injection_in_search__ok(api_client, injection):

    # arrange
    user = create_test_owner()
    workflow = create_test_workflow(user=user, tasks_count=1)
    task = workflow.tasks.first()
    task.name = 'Test task'
    task.save()
    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        '/v3/tasks',
        data={
            'search': injection,
            'ordering': 'date',
        },
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1


def test_list__invalid_ordering__validation_error(api_client):

    # arrange
    user = create_test_user()
    create_test_workflow(user, tasks_count=1)
    invalid_ordering = '<script href="load.some.xss"></script>'
    api_client.token_authenticate(user=user)

    # act
    response = api_client.get(
        f'/v3/tasks?ordering={invalid_ordering}',
    )

    # assert
    assert response.status_code == 400
    message = f'"{invalid_ordering}" is not a valid choice.'
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    assert response.data['details']['reason'] == message
    assert response.data['details']['name'] == 'ordering'


def test_list__filter_assigned_to_not_number__validation_error(api_client):

    # arrange
    user = create_test_user(is_admin=True)
    api_client.token_authenticate(user=user)

    # act
    response = api_client.get('/v3/tasks?assigned_to=DROP DATABASE')

    # assert
    message = 'A valid integer is required.'
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    assert response.data['details']['reason'] == message
    assert response.data['details']['name'] == 'assigned_to'


def test_list__filter_assigned_to_not_admin__validation_error(api_client):

    # arrange
    user = create_test_user(is_admin=False)
    user2 = create_test_user(account=user.account, email='test@test.test')
    create_test_workflow(user, tasks_count=1)
    api_client.token_authenticate(user=user)

    # act
    response = api_client.get(f'/v3/tasks?assigned_to={user2.id}')

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == messages.MSG_PW_0057
    assert response.data['details']['reason'] == messages.MSG_PW_0057
    assert response.data['details']['name'] == 'assigned_to'


def test_list__filter_is_completed_not_bool__validation_error(api_client):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user=user)

    # act
    response = api_client.get(
        '/v3/tasks?is_completed=<script src="some.xss"></script>',
    )

    # assert
    message = 'Must be a valid boolean.'
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    assert response.data['details']['reason'] == message
    assert response.data['details']['name'] == 'is_completed'


def test_list__filter_template_id_not_number__validation_error(api_client):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user=user)

    # act
    response = api_client.get("/v3/tasks?template_id=' OR 1='1")

    # assert
    message = 'A valid integer is required.'
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    assert response.data['details']['reason'] == message
    assert response.data['details']['name'] == 'template_id'
