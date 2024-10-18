import pytest
from datetime import timedelta
from django.utils import timezone
from pneumatic_backend.processes.tests.fixtures import (
    create_test_user,
    create_test_workflow,
    create_test_template,
)
from pneumatic_backend.utils.validation import ErrorCode
from pneumatic_backend.processes.messages import workflow as messages
from pneumatic_backend.authentication.enums import AuthTokenType

from pneumatic_backend.processes.enums import (
    WorkflowStatus,
    FieldType,
)
from pneumatic_backend.processes.models import (
    FileAttachment,
    TaskField,
)
from pneumatic_backend.processes.services.workflow_action import (
    WorkflowActionService,
)
from pneumatic_backend.processes.api_v2.services import (
    WorkflowEventService
)
from pneumatic_backend.services.markdown import MarkdownService


pytestmark = pytest.mark.django_db
datetime_format = '%Y-%m-%dT%H:%M:%S.%fZ'


@pytest.fixture(autouse=True)
def replica_mock(mocker):
    mocker.patch('django.conf.settings.REPLICA', 'default')
    yield


def test_list__default_ordering__ok(api_client):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user=user)
    workflow_1 = create_test_workflow(user, tasks_count=1)
    task_11 = workflow_1.tasks.get(number=1)
    workflow_2 = create_test_workflow(
        user,
        name='Workflow 2',
        tasks_count=1
    )
    task_21 = workflow_2.tasks.get(number=1)
    task_11.due_date = task_11.date_first_started + timedelta(hours=1)
    task_11.save(update_fields=['due_date'])

    completed_workflow = create_test_workflow(user, tasks_count=1)
    api_client.post(
        f'/workflows/{completed_workflow.id}/task-complete',
        data={
            'task_id': completed_workflow.current_task_instance.id
        }
    )

    # act
    response = api_client.get('/v3/tasks')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 2

    task_21_data = response.data[0]
    assert task_21_data['id'] == task_21.id
    assert task_21_data['name'] == task_21.name
    assert task_21_data['due_date'] is None
    assert task_21_data['due_date_tsp'] is None
    assert task_21_data['date_started'] == task_21.date_started.strftime(
        datetime_format
    )
    assert task_21_data['date_started_tsp'] == task_21.date_started.timestamp()
    assert task_21_data['date_completed'] is None
    assert task_21_data['date_completed_tsp'] is None
    assert task_21_data['workflow_name'] == workflow_2.name
    assert task_21_data['template_id'] == workflow_2.template_id
    assert task_21_data['template_task_id'] == task_21.template_id

    task_11_data = response.data[1]
    assert task_11_data['id'] == task_11.id
    assert task_11_data['due_date'] == (
        task_11.due_date.strftime(datetime_format)
    )
    assert task_11_data['due_date_tsp'] == task_11.due_date.timestamp()


def test_list__urgent_tasks_first__ok(api_client):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user=user)
    workflow_1 = create_test_workflow(user, tasks_count=1)
    task_11 = workflow_1.tasks.get(number=1)
    workflow_2 = create_test_workflow(user, tasks_count=1, is_urgent=True)
    task_21 = workflow_2.tasks.get(number=1)
    workflow_3 = create_test_workflow(user, tasks_count=1)
    task_31 = workflow_3.tasks.get(number=1)

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

    api_client.token_authenticate(user)
    analytics_mock = mocker.patch(
        'pneumatic_backend.analytics.services.AnalyticService.'
        'search_search'
    )

    # act
    response = api_client.get(f'/v3/tasks?search={raw_search_text}')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == task.id

    analytics_mock.assert_called_once_with(
        user_id=user.id,
        page='tasks',
        search_text=clear_search_text,
        is_superuser=False,
        auth_type=AuthTokenType.USER
    )


def test_list__search__not_found__ok(api_client, mocker):

    """ Need more tests for search """

    # arrange
    user = create_test_user()
    create_test_workflow(user)
    api_client.token_authenticate(user)
    analytics_mock = mocker.patch(
        'pneumatic_backend.analytics.services.AnalyticService.'
        'search_search'
    )
    search_text = 'DROP TABLE accounts_account'

    # act
    response = api_client.get(f'/v3/tasks?search={search_text}')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 0

    analytics_mock.assert_called_once_with(
        user_id=user.id,
        page='tasks',
        search_text=search_text,
        is_superuser=False,
        auth_type=AuthTokenType.USER
    )


def test_list__search__comment__ok(api_client, mocker):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user, tasks_count=1)
    WorkflowEventService.comment_created_event(
        user=user,
        workflow=workflow,
        text='some comment text'
    )
    search_text = 'com tex'
    workflow_2 = create_test_workflow(user=user, tasks_count=1)
    WorkflowEventService.comment_created_event(
        user=user,
        workflow=workflow_2,
        text='some camera retext'
    )

    api_client.token_authenticate(user)
    analytics_mock = mocker.patch(
        'pneumatic_backend.analytics.services.AnalyticService.'
        'search_search'
    )

    # act
    response = api_client.get(f'/v3/tasks?search={search_text}')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == workflow.current_task_instance.id
    analytics_mock.assert_called_once_with(
        user_id=user.id,
        page='tasks',
        search_text=search_text,
        is_superuser=False,
        auth_type=AuthTokenType.USER
    )


def test_list__search__comment__url_as_text__ok(api_client, mocker):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user, tasks_count=1)
    text = 'some **https://pneumo.app** text'
    WorkflowEventService.comment_created_event(
        user=user,
        workflow=workflow,
        text=text,
        clear_text=MarkdownService.clear(text)
    )
    search_text = 'pneumo.app'
    api_client.token_authenticate(user)
    analytics_mock = mocker.patch(
        'pneumatic_backend.analytics.services.AnalyticService.'
        'search_search'
    )

    # act
    response = api_client.get(f'/v3/tasks?search={search_text}')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == workflow.current_task_instance.id
    analytics_mock.assert_called_once_with(
        user_id=user.id,
        page='tasks',
        search_text=search_text,
        is_superuser=False,
        auth_type=AuthTokenType.USER
    )


def test_list__search__comment__markdown__ok(api_client, mocker):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user, tasks_count=1)
    text = 'some -  **[file.here](http://google.com/) value**'
    WorkflowEventService.comment_created_event(
        user=user,
        workflow=workflow,
        text=text,
        clear_text=MarkdownService.clear(text)
    )
    search_text = 'file'
    api_client.token_authenticate(user)
    analytics_mock = mocker.patch(
        'pneumatic_backend.analytics.services.AnalyticService.'
        'search_search'
    )

    # act
    response = api_client.get(f'/v3/tasks?search={search_text}')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == workflow.current_task_instance.id
    analytics_mock.assert_called_once_with(
        user_id=user.id,
        page='tasks',
        search_text=search_text,
        is_superuser=False,
        auth_type=AuthTokenType.USER
    )


def test_list__search__not_comment_event__not_found(api_client, mocker):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user, tasks_count=1)
    search_text = 'com tex'
    event = WorkflowEventService.task_complete_event(
        user=user,
        task=workflow.current_task_instance
    )
    event.text = search_text
    event.save()

    api_client.token_authenticate(user)
    analytics_mock = mocker.patch(
        'pneumatic_backend.analytics.services.AnalyticService.'
        'search_search'
    )

    # act
    response = api_client.get(f'/v3/tasks?search={search_text}')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 0
    analytics_mock.assert_called_once_with(
        user_id=user.id,
        page='tasks',
        search_text=search_text,
        is_superuser=False,
        auth_type=AuthTokenType.USER
    )


def test_list__search__another_task_comment__not_found(api_client, mocker):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user, tasks_count=2)
    text = 'some comment text'
    WorkflowEventService.comment_created_event(
        user=user,
        workflow=workflow,
        text=text,
        clear_text=MarkdownService.clear(text)
    )
    search_text = 'com tex'
    workflow.current_task = 2
    workflow.save()
    api_client.token_authenticate(user)
    analytics_mock = mocker.patch(
        'pneumatic_backend.analytics.services.AnalyticService.'
        'search_search'
    )

    # act
    response = api_client.get(f'/v3/tasks?search={search_text}')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 0
    analytics_mock.assert_called_once_with(
        user_id=user.id,
        page='tasks',
        search_text=search_text,
        is_superuser=False,
        auth_type=AuthTokenType.USER
    )


def test_list__search__comment_attachment__ok(api_client, mocker):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user)
    event = WorkflowEventService.comment_created_event(
        user=user,
        workflow=workflow,
        text='comment'
    )
    FileAttachment.objects.create(
        name='fred cena',
        url='https://fred.cena.com',
        size=1488,
        account_id=user.account_id,
        workflow=workflow,
        event=event
    )

    api_client.token_authenticate(user)
    mocker.patch(
        'pneumatic_backend.analytics.services.AnalyticService.'
        'search_search'
    )
    search_text = 'cena'

    # act
    response = api_client.get(f'/v3/tasks?search={search_text}')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == workflow.current_task_instance.id


def test_list__search__another_task_comment_attachment__not_found(
    api_client,
    mocker
):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user, tasks_count=2)
    event = WorkflowEventService.comment_created_event(
        user=user,
        workflow=workflow,
        text='comment'
    )
    FileAttachment.objects.create(
        name='fred.cena',
        url='https://fred.cena.com',
        size=1488,
        account_id=user.account_id,
        workflow=workflow,
        event=event
    )
    workflow.current_task = 2
    workflow.save()

    api_client.token_authenticate(user)
    mocker.patch(
        'pneumatic_backend.analytics.services.AnalyticService.'
        'search_search'
    )
    search_text = 'cen'

    # act
    response = api_client.get(f'/v3/tasks?search={search_text}')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 0


def test_list__search__completed_prev_task_output_attachment__not_found(
    api_client,
    mocker
):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user, tasks_count=2)
    task_1 = workflow.current_task_instance
    field = TaskField.objects.create(
        task=task_1,
        api_name='api-name-1',
        type=FieldType.FILE,
        workflow=workflow
    )
    FileAttachment.objects.create(
        name='fred.cena',
        url='https://test.com/test.txt',
        size=1488,
        account_id=user.account_id,
        workflow=workflow,
        output=field
    )
    task_1.is_completed = True
    task_1.date_completed = timezone.now()
    task_1.save()

    workflow.current_task = 2
    workflow.save()

    api_client.token_authenticate(user)
    mocker.patch(
        'pneumatic_backend.analytics.services.AnalyticService.'
        'search_search'
    )
    search_text = 'cena'

    # act
    response = api_client.get(f'/v3/tasks?search={search_text}')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 0


def test_list__search__current_task_field_attachment__ok(
    api_client,
    mocker
):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user, tasks_count=2)
    task_1 = workflow.current_task_instance
    field = TaskField.objects.create(
        task=task_1,
        api_name='api-name-1',
        type=FieldType.FILE,
        workflow=workflow
    )
    FileAttachment.objects.create(
        name='fred.cena',
        url='https://test.com/test.txt',
        size=1488,
        account_id=user.account_id,
        workflow=workflow,
        output=field
    )

    api_client.token_authenticate(user)
    mocker.patch(
        'pneumatic_backend.analytics.services.AnalyticService.'
        'search_search'
    )
    search_text = 'fred'

    # act
    response = api_client.get(f'/v3/tasks?search={search_text}')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == task_1.id


def test_list__search__current_description__ok(
    api_client,
    mocker
):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user, tasks_count=2)
    description = 'some [file.here](http://google.com/) value'
    task_1 = workflow.current_task_instance
    task_1.description = description
    task_1.clear_description = MarkdownService.clear(description)
    task_1.save()
    api_client.token_authenticate(user)
    mocker.patch(
        'pneumatic_backend.analytics.services.AnalyticService.search_search'
    )
    search_text = 'file.here'

    # act
    response = api_client.get(f'/v3/tasks?search={search_text}')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == task_1.id


def test_list__search__not_current_description__not_found(
    api_client,
    mocker
):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user, tasks_count=3)
    workflow.current_task = 2
    workflow.save(update_fields=['current_task'])
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
        'pneumatic_backend.analytics.services.AnalyticService.search_search'
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.get(f'/v3/tasks?search={search_text}')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 0


def test_list__search__kickoff_description__ok(api_client, mocker):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user)
    task = workflow.current_task_instance
    kickoff = workflow.kickoff_instance
    description = 'some [file.here](http://google.com/) value'
    kickoff.description = description
    kickoff.clear_description = MarkdownService.clear(description)
    kickoff.save()
    create_test_workflow(user)
    search_text = 'file'
    api_client.token_authenticate(user)
    mocker.patch(
        'pneumatic_backend.analytics.services.AnalyticService.search_search'
    )
    # act
    response = api_client.get(f'/v3/tasks?search={search_text}')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == task.id


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
    )
)
def test_list__search__in_current_task_field_value__ok(
    api_client,
    mocker,
    field_type,
):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user, tasks_count=2)
    task_1 = workflow.current_task_instance
    value = 'text fred boy some'
    TaskField.objects.create(
        task=task_1,
        api_name='api-name-1',
        type=field_type,
        workflow=workflow,
        value=value,
        clear_value=MarkdownService.clear(value)
    )
    api_client.token_authenticate(user)
    mocker.patch(
        'pneumatic_backend.analytics.services.AnalyticService.'
        'search_search'
    )
    search_text = 'fred'

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
    )
)
def test_list__search__in_kickoff_field_value__ok(
    api_client,
    mocker,
    field_type,
):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user, tasks_count=2)
    task_1 = workflow.current_task_instance
    value = 'text <fred@boy.com> some'
    TaskField.objects.create(
        kickoff=workflow.kickoff_instance,
        api_name='api-name-1',
        type=field_type,
        workflow=workflow,
        value=value,
        clear_value=MarkdownService.clear(value)
    )
    api_client.token_authenticate(user)
    mocker.patch(
        'pneumatic_backend.analytics.services.AnalyticService.'
        'search_search'
    )
    search_text = 'fred'

    # act
    response = api_client.get(f'/v3/tasks?search={search_text}')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == task_1.id


@pytest.mark.parametrize(
    'field_type',
    (
        FieldType.FILE,
    )
)
def test_list__search__in_excluded_field_value__not_found(
    api_client,
    mocker,
    field_type,
):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user, tasks_count=2)
    task_1 = workflow.current_task_instance
    value = 'text fredy boy some'
    TaskField.objects.create(
        task=task_1,
        api_name='api-name-1',
        type=field_type,
        workflow=workflow,
        value=value,
        clear_value=MarkdownService.clear(value)
    )
    api_client.token_authenticate(user)
    mocker.patch(
        'pneumatic_backend.analytics.services.AnalyticService.'
        'search_search'
    )
    search_text = 'fred'

    # act
    response = api_client.get(f'/v3/tasks?search={search_text}')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 0


def test_list__search___full_uri_in_field___ok(
    api_client,
    mocker,
):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user, tasks_count=2)
    task_1 = workflow.current_task_instance
    value = 'https://translate.com/some-page?sl=ru&tl=ru&op=taranslate'
    TaskField.objects.create(
        kickoff=workflow.kickoff_instance,
        api_name='api-name-1',
        type=FieldType.URL,
        workflow=workflow,
        value=value,
        clear_value=MarkdownService.clear(value)
    )
    api_client.token_authenticate(user)
    mocker.patch(
        'pneumatic_backend.analytics.services.AnalyticService.'
        'search_search'
    )

    # act
    response = api_client.get(
        '/v3/tasks',
        data={'search': value}
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == task_1.id


def test_list__search___partional_uri_in_field___ok(
    api_client,
    mocker,
):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user, tasks_count=1)
    task_1 = workflow.current_task_instance
    value = 'https://translate.com/some-page?sl=ru&tl=ru&op=taranslate'
    TaskField.objects.create(
        kickoff=workflow.kickoff_instance,
        api_name='api-name-1',
        type=FieldType.URL,
        workflow=workflow,
        value=value,
        clear_value=MarkdownService.clear(value)
    )
    api_client.token_authenticate(user)
    mocker.patch(
        'pneumatic_backend.analytics.services.AnalyticService.'
        'search_search'
    )
    search_text = 'https://translate.com/some-page'

    # act
    response = api_client.get(f'/v3/tasks?search={search_text}')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == task_1.id


def test_list__search__markdown_filename_in_text_field__ok(
    api_client,
    mocker
):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user, tasks_count=2)
    task_1 = workflow.current_task_instance
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
        clear_value=MarkdownService.clear(value)
    )

    api_client.token_authenticate(user)
    mocker.patch(
        'pneumatic_backend.analytics.services.AnalyticService.'
        'search_search'
    )
    search_text = 'somefile'

    # act
    response = api_client.get(f'/v3/tasks?search={search_text}')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == task_1.id


def test_list__search__url_in_text_field__ok(
    api_client,
    mocker
):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user, tasks_count=2)
    task_1 = workflow.current_task_instance
    value = (
        'Final version \n-  **https://www.search.com/file.txt** here'
    )
    TaskField.objects.create(
        workflow=workflow,
        task=task_1,
        api_name='api-name-1',
        type=FieldType.TEXT,
        value=value,
        clear_value=MarkdownService.clear(value)
    )

    api_client.token_authenticate(user)
    mocker.patch(
        'pneumatic_backend.analytics.services.AnalyticService.'
        'search_search'
    )
    search_text = 'search'

    # act
    response = api_client.get(f'/v3/tasks?search={search_text}')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == task_1.id


def test_list__search__email_in_text_field__ok(
    api_client,
    mocker
):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user, tasks_count=2)
    task_1 = workflow.current_task_instance
    value = (
        'Final version \n-  **master@test.com** here'
    )
    TaskField.objects.create(
        workflow=workflow,
        task=task_1,
        api_name='api-name-1',
        type=FieldType.TEXT,
        value=value,
        clear_value=MarkdownService.clear(value)
    )

    api_client.token_authenticate(user)
    mocker.patch(
        'pneumatic_backend.analytics.services.AnalyticService.'
        'search_search'
    )
    search_text = 'master'

    # act
    response = api_client.get(f'/v3/tasks?search={search_text}')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == task_1.id


def test_list__search__prev_task_markdown_filename_in_text__not_found(
    api_client,
    mocker
):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user, tasks_count=2)
    task_1 = workflow.current_task_instance
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
        clear_value=MarkdownService.clear(value)
    )
    workflow.current_task = 2
    workflow.save()

    api_client.token_authenticate(user)
    mocker.patch(
        'pneumatic_backend.analytics.services.AnalyticService.'
        'search_search'
    )
    search_text = 'somefile.txt'

    # act
    response = api_client.get(f'/v3/tasks?search={search_text}')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 0


def test_list__ordering_by_date__ok(api_client):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user=user)
    workflow_1 = create_test_workflow(user, tasks_count=2)
    task_11 = workflow_1.tasks.get(number=1)
    workflow_2 = create_test_workflow(user, tasks_count=2)
    task_21 = workflow_2.tasks.get(number=1)

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
    api_client.token_authenticate(user=user)
    workflow_1 = create_test_workflow(user, tasks_count=1)
    task_11 = workflow_1.tasks.get(number=1)
    workflow_2 = create_test_workflow(user, tasks_count=1)
    task_21 = workflow_2.tasks.get(number=1)

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
    api_client.token_authenticate(user=user)
    workflow_1 = create_test_workflow(user, tasks_count=1)
    task_11 = workflow_1.tasks.get(number=1)
    complete_response_1 = api_client.post(
        f'/workflows/{workflow_1.id}/task-complete',
        data={'task_id': task_11.id}
    )
    workflow_2 = create_test_workflow(user, tasks_count=1)
    task_21 = workflow_2.tasks.get(number=1)
    complete_response_2 = api_client.post(
        f'/workflows/{workflow_2.id}/task-complete',
        data={'task_id': task_21.id}
    )
    create_test_workflow(user, tasks_count=1)

    # act
    response = api_client.get(
        '/v3/tasks?ordering=completed&is_completed=true'
    )

    # assert
    assert complete_response_1.status_code == 204
    assert complete_response_2.status_code == 204
    assert response.status_code == 200
    assert len(response.data) == 2
    task_11.refresh_from_db()
    assert response.data[0]['id'] == task_11.id
    assert response.data[0]['date_started'] == (
        task_11.date_started.strftime(datetime_format)
    )
    assert response.data[0]['date_started_tsp'] == (
        task_11.date_started.timestamp()
    )
    # assert response.data[0]['date_completed'] == (
    #     task_11.date_completed.strftime(datetime_format)
    # )
    assert response.data[0]['date_completed_tsp'] == (
        task_11.date_completed.timestamp()
    )
    assert response.data[1]['id'] == task_21.id
    assert response.data[1]['date_started'] is not None
    assert response.data[1]['date_completed'] is not None


def test_list__ordering_by_reversed_completed__ok(api_client):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user=user)
    workflow_1 = create_test_workflow(user, tasks_count=1)
    task_11 = workflow_1.tasks.get(number=1)
    api_client.post(
        f'/workflows/{workflow_1.id}/task-complete',
        data={'task_id': task_11.id}
    )
    workflow_2 = create_test_workflow(user, tasks_count=1)
    task_21 = workflow_2.tasks.get(number=1)
    api_client.post(
        f'/workflows/{workflow_2.id}/task-complete',
        data={'task_id': task_21.id}
    )
    create_test_workflow(user, tasks_count=1)

    # act
    response = api_client.get(
        '/v3/tasks?ordering=-completed&is_completed=true'
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 2
    assert response.data[0]['id'] == task_21.id
    assert response.data[1]['id'] == task_11.id


def test_list__ordering_by_completed_required_completion_by_all__ok(
    api_client
):

    # arrange
    user = create_test_user()
    user_2 = create_test_user(account=user.account, email='user2@test.test')
    template = create_test_template(
        user=user,
        tasks_count=1
    )
    template_task = template.tasks.get(number=1)
    template_task.require_completion_by_all = True
    template_task.save()
    template_task.add_raw_performer(user_2)

    workflow_1 = create_test_workflow(user, template=template)
    task_11 = workflow_1.tasks.get(number=1)
    api_client.token_authenticate(user=user)
    api_client.post(
        f'/workflows/{workflow_1.id}/task-complete',
        data={'task_id': task_11.id}
    )
    workflow_2 = create_test_workflow(user, tasks_count=1)
    task_21 = workflow_2.tasks.get(number=1)
    api_client.post(
        f'/workflows/{workflow_2.id}/task-complete',
        data={'task_id': task_21.id}
    )
    create_test_workflow(user, tasks_count=1)

    # act
    response = api_client.get(
        '/v3/tasks?ordering=completed&is_completed=true'
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
    api_client
):

    # arrange
    user = create_test_user()
    user_2 = create_test_user(account=user.account, email='user2@test.test')
    template = create_test_template(
        user=user,
        tasks_count=1
    )
    template_task = template.tasks.get(number=1)
    template_task.require_completion_by_all = True
    template_task.add_raw_performer(user_2)

    workflow_1 = create_test_workflow(user, template=template)
    task_11 = workflow_1.tasks.get(number=1)
    api_client.token_authenticate(user=user)
    api_client.post(
        f'/workflows/{workflow_1.id}/task-complete',
        data={'task_id': task_11.id}
    )
    workflow_2 = create_test_workflow(user, tasks_count=1)
    task_21 = workflow_2.tasks.get(number=1)
    api_client.post(
        f'/workflows/{workflow_2.id}/task-complete',
        data={'task_id': task_21.id}
    )
    create_test_workflow(user, tasks_count=1)

    # act
    response = api_client.get(
        '/v3/tasks?ordering=-completed&is_completed=true'
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 2
    assert response.data[0]['id'] == task_21.id
    assert response.data[1]['id'] == task_11.id


def test_list__completed__non_completed_performers__not_view_in_list(
    api_client
):

    # arrange
    user = create_test_user(is_account_owner=True)
    user_2 = create_test_user(
        email='test@test.test',
        account=user.account,
        is_account_owner=False
    )
    template = create_test_template(user=user, tasks_count=2, is_active=True)
    template_task_1 = template.tasks.get(number=1)
    template_task_1.add_raw_performer(user_2)
    workflow = create_test_workflow(user, template=template)

    api_client.token_authenticate(user=user)
    api_client.post(
        f'/workflows/{workflow.id}/task-complete',
        data={
            'task_id': workflow.current_task_instance.id
        }
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
    api_client.token_authenticate(user=user)
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

    # act
    response = api_client.get('/v3/tasks?ordering=overdue')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 3
    assert response.data[0]['id'] == task_11.id
    assert response.data[0]['due_date'] == (
        task_11.due_date.strftime(datetime_format)
    )
    assert response.data[0]['due_date_tsp'] == task_11.due_date.timestamp()
    assert response.data[1]['id'] == task_21.id
    assert response.data[1]['due_date'] == (
        task_21.due_date.strftime(datetime_format)
    )
    assert response.data[1]['due_date_tsp'] == task_21.due_date.timestamp()
    assert response.data[2]['id'] == task_31.id
    assert response.data[2]['due_date'] is None
    assert response.data[2]['due_date_tsp'] is None


def test_list__ordering_by_reversed_overdue__ok(api_client):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user=user)
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

    # act
    response = api_client.get('/v3/tasks?ordering=-overdue')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 3
    assert response.data[0]['id'] == task_31.id
    assert response.data[1]['id'] == task_21.id
    assert response.data[2]['id'] == task_11.id


def test_list__invalid_ordering__validation_error(api_client):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user=user)
    create_test_workflow(user, tasks_count=1)
    invalid_ordering = '<script href="load.some.xss"></script>'

    # act
    response = api_client.get(
        f'/v3/tasks?ordering={invalid_ordering}'
    )

    # assert
    assert response.status_code == 400
    message = f'"{invalid_ordering}" is not a valid choice.'
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    assert response.data['details']['reason'] == message
    assert response.data['details']['name'] == 'ordering'


def test_list__filter_assigned_to__ok(api_client):

    # arrange
    user = create_test_user(is_admin=True)
    user2 = create_test_user(account=user.account, email='test@test.test')
    api_client.token_authenticate(user=user)
    create_test_workflow(user, tasks_count=1)
    workflow = create_test_workflow(user2, tasks_count=1)
    task = workflow.tasks.get(number=1)

    # act
    response = api_client.get(f'/v3/tasks?assigned_to={user2.id}')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == task.id


def test_list__filter_assigned_to_not_number__validation_error(api_client):

    # arrange
    user = create_test_user(is_admin=True)
    api_client.token_authenticate(user=user)

    # act
    response = api_client.get(f'/v3/tasks?assigned_to=DROP DATABASE')

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
    api_client.token_authenticate(user=user)
    create_test_workflow(user, tasks_count=1)

    # act
    response = api_client.get(f'/v3/tasks?assigned_to={user2.id}')

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == messages.MSG_PW_0057
    assert response.data['details']['reason'] == messages.MSG_PW_0057
    assert response.data['details']['name'] == 'assigned_to'


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
    api_client
):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(
        name='Workflow with completed task',
        user=user,
        tasks_count=2
    )
    api_client.token_authenticate(user)
    api_client.post(
        f'/workflows/{workflow.id}/task-complete',
        data={'task_id': workflow.current_task_instance.id}
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
    api_client
):

    # arrange
    user = create_test_user()
    user_2 = create_test_user(email='test@test.test')
    create_test_workflow(
        name='Another user running task',
        user=user_2,
        tasks_count=1
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
    api_client.token_authenticate(user)
    api_client.post(
        f'/workflows/{workflow.id}/task-complete',
        data={'task_id': workflow.current_task_instance.id}
    )

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
    )
    api_client.token_authenticate(user)
    api_client.post(
        f'/workflows/{workflow.id}/task-complete',
        data={'task_id': workflow.current_task_instance.id}
    )
    workflow.status = WorkflowStatus.DELAYED
    workflow.save(update_fields=['status'])

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
    )
    api_client.post(
        f'/workflows/{workflow.id}/task-complete',
        data={'task_id': workflow.current_task_instance.id}
    )
    workflow.refresh_from_db()
    service = WorkflowActionService(user=user)
    service.terminate_workflow(workflow)
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
    )
    api_client.token_authenticate(user)
    api_client.post(
        f'/workflows/{workflow.id}/task-complete',
        data={'task_id': workflow.current_task_instance.id}
    )
    workflow.refresh_from_db()
    WorkflowActionService().end_process(
        workflow=workflow,
        user=user,
        by_condition=False,
    )

    # act
    response = api_client.get('/v3/tasks?is_completed=false')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 0


def test_list__filter_is_completed_not_bool__validation_error(api_client):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user=user)

    # act
    response = api_client.get(
        '/v3/tasks?is_completed=<script src="some.xss"></script>'
    )

    # assert
    message = 'Must be a valid boolean.'
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    assert response.data['details']['reason'] == message
    assert response.data['details']['name'] == 'is_completed'


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
    api_client
):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(
        name='Workflow with completed task',
        user=user,
        tasks_count=2
    )
    api_client.token_authenticate(user)
    api_client.post(
        f'/workflows/{workflow.id}/task-complete',
        data={'task_id': workflow.current_task_instance.id}
    )
    task = workflow.tasks.get(number=1)

    # act
    response = api_client.get('/v3/tasks?is_completed=true')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == task.id


def test_list__filter_is_completed_true__another_user_task__not_found(
    api_client
):

    # arrange
    user = create_test_user()
    user_2 = create_test_user(email='test@test.test')
    workflow = create_test_workflow(
        name='Another user running task',
        user=user_2,
        tasks_count=1
    )
    api_client.token_authenticate(user_2)
    api_client.post(
        f'/workflows/{workflow.id}/task-complete',
        data={'task_id': workflow.current_task_instance.id}
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
    api_client.token_authenticate(user)
    api_client.post(
        f'/workflows/{workflow.id}/task-complete',
        data={'task_id': workflow.current_task_instance.id}
    )
    task = workflow.tasks.get(number=1)

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
    )
    api_client.token_authenticate(user)
    api_client.post(
        f'/workflows/{workflow.id}/task-complete',
        data={'task_id': workflow.current_task_instance.id}
    )
    workflow.status = WorkflowStatus.DELAYED
    workflow.save(update_fields=['status'])
    workflow.refresh_from_db()
    task = workflow.tasks.get(number=1)

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
    )
    api_client.token_authenticate(user)
    api_client.post(
        f'/workflows/{workflow.id}/task-complete',
        data={'task_id': workflow.current_task_instance.id}
    )
    workflow.refresh_from_db()
    service = WorkflowActionService(user=user)
    service.terminate_workflow(workflow)

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
    )
    api_client.token_authenticate(user)
    api_client.post(
        f'/workflows/{workflow.id}/task-complete',
        data={'task_id': workflow.current_task_instance.id}
    )
    workflow.refresh_from_db()
    WorkflowActionService().end_process(
        workflow=workflow,
        user=user,
        by_condition=False,
    )
    task = workflow.tasks.get(number=1)

    # act
    response = api_client.get('/v3/tasks?is_completed=true')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == task.id


def test_list__filter_template_id__ok(api_client):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user=user)
    template_1 = create_test_template(user, is_active=True)
    template_2 = create_test_template(user, is_active=True)

    workflow_1 = create_test_workflow(user, template=template_1, tasks_count=1)
    task_11 = workflow_1.tasks.get(number=1)
    workflow_2 = create_test_workflow(user, template=template_1, tasks_count=1)
    task_21 = workflow_2.tasks.get(number=1)
    create_test_workflow(user, template=template_2, tasks_count=1)

    # act
    response = api_client.get(f'/v3/tasks?template_id={template_1.id}')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 2
    assert response.data[0]['id'] == task_21.id
    assert response.data[1]['id'] == task_11.id


def test_list__filter_template_id_not_number__validation_error(api_client):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user=user)

    # act
    response = api_client.get(f"/v3/tasks?template_id=' OR 1='1")

    # assert
    message = 'A valid integer is required.'
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    assert response.data['details']['reason'] == message
    assert response.data['details']['name'] == 'template_id'


def test_list__filter_template_task_id__ok(api_client):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user=user)
    template = create_test_template(user, is_active=True)
    template_task = template.tasks.get(number=1)
    template_2 = create_test_template(user, is_active=True)

    workflow = create_test_workflow(user, template=template, tasks_count=1)
    task = workflow.tasks.get(number=1)
    create_test_workflow(user, template=template_2, tasks_count=1)

    # act
    response = api_client.get(f'/v3/tasks?template_task_id={template_task.id}')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == task.id


def test_list__filter_template_task_id_not_number__validation_error(
    api_client
):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user=user)

    # act
    response = api_client.get(f'/v3/tasks?template_task_id=null')

    # assert
    message = 'A valid integer is required.'
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    assert response.data['details']['reason'] == message
    assert response.data['details']['name'] == 'template_task_id'


def test_list__pagination__ok(api_client):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user=user)
    create_test_workflow(user, tasks_count=1)
    workflow_2 = create_test_workflow(user, tasks_count=1)
    task_21 = workflow_2.tasks.get(number=1)
    create_test_workflow(user, tasks_count=1)

    # act
    response = api_client.get('/v3/tasks?limit=1&offset=1')

    # assert
    assert response.status_code == 200
    assert len(response.data['results']) == 1
    assert response.data['results'][0]['id'] == task_21.id


def test_list__exclude_delayed_tasks__ok(api_client):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user=user)
    delayed_workflow = create_test_workflow(
        user=user,
        tasks_count=2,
        with_delay=True
    )

    api_client.post(
        f'/workflows/{delayed_workflow.id}/task-complete',
        data={'task_id': delayed_workflow.current_task_instance.id}
    )

    # act
    response = api_client.get('/v3/tasks')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 0
