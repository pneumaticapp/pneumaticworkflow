from datetime import timedelta
from string import punctuation

import pytest
from django.utils import timezone

from src.accounts.enums import BillingPlanType
from src.authentication.enums import AuthTokenType
from src.processes.enums import (
    ConditionAction,
    DirectlyStatus,
    FieldType,
    OwnerType,
    PerformerType,
    PredicateOperator,
    PredicateType,
    TaskStatus,
    WorkflowApiStatus,
    WorkflowStatus,
)
from src.processes.messages import workflow as messages
from src.processes.models.templates.conditions import (
    ConditionTemplate,
    PredicateTemplate,
    RuleTemplate,
)
from src.processes.models.templates.owner import TemplateOwner
from src.processes.models.workflows.attachment import FileAttachment
from src.processes.models.workflows.fields import TaskField
from src.processes.models.workflows.task import (
    Delay,
    TaskPerformer,
)
from src.processes.services.events import (
    WorkflowEventService,
)
from src.processes.services.tasks.performers import (
    TaskPerformersService,
)
from src.processes.tests.fixtures import (
    create_invited_user,
    create_test_account,
    create_test_admin,
    create_test_group,
    create_test_guest,
    create_test_owner,
    create_test_template,
    create_test_user,
    create_test_workflow,
)
from src.services.markdown import MarkdownService
from src.utils.validation import ErrorCode

pytestmark = pytest.mark.django_db


def test_list__workflow_data__ok(api_client):

    # arrange
    user = create_test_user()
    due_date = timezone.now()
    workflow = create_test_workflow(
        user=user,
        tasks_count=1,
        due_date=due_date,
        status=WorkflowStatus.DONE,
        description='Some workflow description',
    )

    task = workflow.tasks.first()
    template = workflow.template
    create_test_workflow(user)
    api_client.token_authenticate(user)

    # act
    response = api_client.get('/workflows?ordering=date')

    # assert
    assert response.status_code == 200
    assert len(response.data['results']) == 2
    wf_data = response.data['results'][0]
    assert wf_data['id'] == workflow.id
    assert wf_data['name'] == workflow.name
    assert wf_data['status'] == workflow.status
    assert wf_data['description'] == workflow.description
    assert wf_data['is_external'] == workflow.is_external
    assert wf_data['workflow_starter'] == user.id
    assert wf_data['ancestor_task_id'] == workflow.ancestor_task_id
    assert wf_data['is_legacy_template'] == workflow.is_legacy_template
    assert wf_data['legacy_template_name'] == workflow.legacy_template_name
    assert wf_data['is_urgent'] == workflow.is_urgent
    assert wf_data['finalizable'] == workflow.finalizable
    assert wf_data['date_created_tsp'] == (
        workflow.date_created.timestamp()
    )
    assert wf_data['date_completed_tsp'] == (
        workflow.date_completed.timestamp()
    )
    assert wf_data['due_date_tsp'] == due_date.timestamp()
    assert wf_data['fields'] == []
    template_data = wf_data['template']
    assert template_data['id'] == template.id
    assert template_data['name'] == template.name
    assert wf_data['owners'] == [user.id]
    assert template_data['is_active'] == template.is_active

    task_data = wf_data['tasks'][0]
    assert task_data['id'] == task.id
    assert task_data['name'] == task.name
    assert task_data['api_name'] == task.api_name
    assert task_data['description'] == task.description
    assert task_data['date_started_tsp'] == task.date_started.timestamp()
    assert task_data['delay'] is None
    assert task_data['due_date_tsp'] is None
    assert task_data['status'] == TaskStatus.ACTIVE
    assert task_data['performers'] == [
        {
            'source_id': user.id,
            'type': 'user',
            'is_completed': False,
            'date_completed_tsp': None,
        },
    ]


def test_list__multiple_tasks__ok(api_client):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(
        user=user,
        tasks_count=2,
    )
    task_1 = workflow.tasks.get(number=1)
    task_2 = workflow.tasks.get(number=2)
    api_client.token_authenticate(user)

    # act
    response = api_client.get('/workflows?ordering=date')

    # assert
    assert response.status_code == 200
    assert len(response.data['results']) == 1
    workflow_data = response.data['results'][0]
    assert len(workflow_data['tasks']) == 2
    task_1_data = workflow_data['tasks'][0]
    assert task_1_data['id'] == task_1.id
    assert task_1_data['status'] == TaskStatus.ACTIVE
    task_2_data = workflow_data['tasks'][1]
    assert task_2_data['id'] == task_2.id
    assert task_2_data['status'] == TaskStatus.PENDING


def test_list__not_return_skipped_tasks__ok(api_client):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(
        user=user,
        tasks_count=2,
    )
    task_1 = workflow.tasks.get(number=1)
    task_1.status = TaskStatus.SKIPPED
    task_1.save()
    task_2 = workflow.tasks.get(number=2)
    task_2.status = TaskStatus.ACTIVE
    task_2.save()
    api_client.token_authenticate(user)

    # act
    response = api_client.get('/workflows?ordering=date')

    # assert
    assert response.status_code == 200
    assert len(response.data['results']) == 1
    workflow_data = response.data['results'][0]
    assert len(workflow_data['tasks']) == 1
    task_1_data = workflow_data['tasks'][0]
    assert task_1_data['id'] == task_2.id
    assert task_1_data['status'] == TaskStatus.ACTIVE


def test_list__pagination__ok(api_client):

    # arrange
    user = create_test_user()
    create_test_workflow(user=user, tasks_count=2)
    workflow_2 = create_test_workflow(user=user, tasks_count=2)
    create_test_workflow(user=user, tasks_count=2)
    api_client.token_authenticate(user)

    # act
    response = api_client.get('/workflows?limit=1&offset=1&ordering=date')

    # assert
    assert response.status_code == 200
    data = response.data
    assert data['count'] == 3
    assert data['previous'].split('?')[1] == 'limit=1&ordering=date'
    assert data['next'].split('?')[1] == 'limit=1&offset=2&ordering=date'
    assert len(data['results']) == 1
    assert data['results'][0]['id'] == workflow_2.id


def test_list__pagination_default_ordering__ok(api_client):

    # arrange
    user = create_test_user()
    create_test_workflow(user=user, tasks_count=2)
    create_test_workflow(user=user, tasks_count=2)
    workflow_3 = create_test_workflow(user=user, tasks_count=2)
    api_client.token_authenticate(user)

    # act
    response = api_client.get('/workflows?limit=1&offset=0')

    # assert
    assert response.status_code == 200
    data = response.data
    assert data['count'] == 3
    assert data['previous'] is None
    assert data['next']
    assert len(data['results']) == 1
    assert data['results'][0]['id'] == workflow_3.id


def test_list__workflow_active_task_delay__ok(api_client):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(
        user=user,
        tasks_count=1,
        status=WorkflowStatus.DELAYED,
    )
    task = workflow.tasks.get(number=1)
    delay = Delay.objects.create(
        task=task,
        start_date=timezone.now() - timedelta(hours=1),
        duration=timedelta(days=1),
        workflow=workflow,
    )
    task.status = TaskStatus.DELAYED
    task.save()
    api_client.token_authenticate(user)

    # act
    response = api_client.get('/workflows?ordering=date')

    # assert
    assert response.status_code == 200
    delay_data = response.data['results'][0]['tasks'][0]['delay']
    assert delay_data['start_date_tsp'] == delay.start_date.timestamp()
    assert delay_data['end_date_tsp'] is None
    assert delay_data['duration'] is not None


def test_list__not_template_owner__empty_list(api_client):

    # arrange
    account = create_test_account()
    user = create_test_user()
    user_2 = create_test_user(
        account=account,
        email='t@t.t',
        is_admin=True,
        is_account_owner=False,
    )
    create_test_workflow(user, tasks_count=1)
    api_client.token_authenticate(user_2)

    # act
    response = api_client.get('/workflows?ordering=date')

    # assert
    assert response.status_code == 200
    assert len(response.data['results']) == 0


def test_list__search__workflow_name__ok(api_client):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user)
    workflow.name = 'New search name'
    workflow.save()
    create_test_workflow(user)
    search_text = workflow.name
    api_client.token_authenticate(user)

    # act
    response = api_client.get(f'/workflows?search={search_text}')

    # assert
    assert response.status_code == 200
    assert len(response.data['results']) == 1
    assert response.data['results'][0]['id'] == workflow.id


def test_list__search__kickoff_description__ok(api_client):

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
    api_client.token_authenticate(user)

    # act
    response = api_client.get(f'/workflows?search={search_text}')

    # assert
    assert response.status_code == 200
    assert len(response.data['results']) == 1
    assert response.data['results'][0]['id'] == workflow.id


def test_list__search__active_description__ok(api_client):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user)
    description = 'some [file.here](http://google.com/) value'
    task = workflow.tasks.get(number=1)
    task.description = description
    task.clear_description = MarkdownService.clear(description)
    task.save()
    create_test_workflow(user)
    search_text = 'file'
    api_client.token_authenticate(user)

    # act
    response = api_client.get(f'/workflows?search={search_text}')

    # assert
    assert response.status_code == 200
    assert len(response.data['results']) == 1
    assert response.data['results'][0]['id'] == workflow.id


def test_list__search__completed_task_description__ok(api_client):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(
        user=user,
        active_task_number=2,
        tasks_count=3,
    )
    description = 'some [file.here](http://google.com/) value'
    task_1 = workflow.tasks.get(number=1)
    task_1.description = description
    task_1.clear_description = MarkdownService.clear(description)
    task_1.save()
    create_test_workflow(user)
    search_text = 'file'
    api_client.token_authenticate(user)

    # act
    response = api_client.get(f'/workflows?search={search_text}')

    # assert
    assert response.status_code == 200
    assert len(response.data['results']) == 1
    assert response.data['results'][0]['id'] == workflow.id


def test_list__search__email_login__ok(api_client):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user, tasks_count=1)
    value = 'text fred@boy some'
    TaskField.objects.create(
        kickoff=workflow.kickoff_instance,
        api_name='api-name-1',
        type=FieldType.STRING,
        workflow=workflow,
        value=value,
        clear_value=MarkdownService.clear(value),
    )
    search_text = 'fred'
    create_test_workflow(user, tasks_count=1)
    api_client.token_authenticate(user)

    # act
    response = api_client.get(f'/workflows?search={search_text}')

    # assert
    assert response.status_code == 200
    assert len(response.data['results']) == 1
    assert response.data['results'][0]['id'] == workflow.id


def test_list__search__email_domain__ok(api_client):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user, tasks_count=1)
    value = 'text fred@boy some'
    TaskField.objects.create(
        kickoff=workflow.kickoff_instance,
        api_name='api-name-1',
        type=FieldType.STRING,
        workflow=workflow,
        value=value,
        clear_value=MarkdownService.clear(value),
    )
    search_text = 'boy'
    create_test_workflow(user, tasks_count=1)
    api_client.token_authenticate(user)

    # act
    response = api_client.get(f'/workflows?search={search_text}')

    # assert
    assert response.status_code == 200
    assert len(response.data['results']) == 1


def test_list__search__full_email__ok(api_client):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user, tasks_count=1)
    value = 'text fred@boy some'
    TaskField.objects.create(
        kickoff=workflow.kickoff_instance,
        api_name='api-name-1',
        type=FieldType.STRING,
        workflow=workflow,
        value=value,
        clear_value=MarkdownService.clear(value),
    )
    search_text = 'fred@boy'
    create_test_workflow(user, tasks_count=1)
    api_client.token_authenticate(user)

    # act
    response = api_client.get(f'/workflows?search={search_text}')

    # assert
    assert response.status_code == 200
    assert len(response.data['results']) == 1
    assert response.data['results'][0]['id'] == workflow.id


def test_list__search__safe_single_quote__ok(api_client):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(
        user,
        tasks_count=1,
        name='text fred@boy some',
    )
    search_text = "'fred@boy"
    create_test_workflow(user, tasks_count=1)
    api_client.token_authenticate(user)

    # act
    response = api_client.get(f'/workflows?search={search_text}')

    # assert
    assert response.status_code == 200
    assert len(response.data['results']) == 1
    assert response.data['results'][0]['id'] == workflow.id


def test_list__search__double_quote__ok(api_client):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(
        user,
        tasks_count=1,
        name='text fred@boy some',
    )
    search_text = '"fred@boy'
    create_test_workflow(user, tasks_count=1)
    api_client.token_authenticate(user)

    # act
    response = api_client.get(f'/workflows?search={search_text}')

    # assert
    assert response.status_code == 200
    assert len(response.data['results']) == 1
    assert response.data['results'][0]['id'] == workflow.id


def test_list__search__sql_injection__safe(api_client):

    # arrange
    user = create_test_user()
    create_test_workflow(
        user,
        tasks_count=1,
        name='text some',
    )
    search_text = 'SELECT * FROM accounts_user WHERE id = 105 OR 10=10;'
    create_test_workflow(user, tasks_count=1)
    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        '/workflows',
        data={'search': search_text},
    )

    # assert
    assert response.status_code == 200
    assert len(response.data['results']) == 0


def test_list__special_chars__ok(api_client):

    """ !"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~ """

    # arrange
    user = create_test_user()
    search_text = punctuation
    create_test_workflow(
        user,
        tasks_count=1,
        name=punctuation,
    )
    create_test_workflow(user, tasks_count=1)
    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        '/workflows',
        data={'search': search_text},
    )

    # assert
    assert response.status_code == 200
    assert len(response.data['results']) == 0


def test_list__search__strip_spaces__ok(api_client):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user, tasks_count=1)
    task = workflow.tasks.get(number=1)
    WorkflowEventService.comment_created_event(
        user=user,
        task=task,
        text='   some\noster@test.com   text',
        after_create_actions=False,
    )
    search_text = 'oster@test.com'
    api_client.token_authenticate(user)

    # act
    response = api_client.get(f'/workflows?search={search_text}')

    # assert
    assert response.status_code == 200
    assert len(response.data['results']) == 1


def test_list__search__comment__ok(api_client):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user, tasks_count=1)
    task = workflow.tasks.get(number=1)
    WorkflowEventService.comment_created_event(
        user=user,
        task=task,
        text='some comment text',
        after_create_actions=False,
    )
    search_text = 'comment text'
    api_client.token_authenticate(user)

    # act
    response = api_client.get(f'/workflows?search={search_text}')

    # assert
    assert response.status_code == 200
    assert len(response.data['results']) == 1


def test_list__search__comment__url_as_text__ok(api_client):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user, tasks_count=1)
    task = workflow.tasks.get(number=1)
    WorkflowEventService.comment_created_event(
        user=user,
        task=task,
        text='some https://www.pneumo.app text',
        after_create_actions=False,
    )
    search_text = 'pneumo.app'
    api_client.token_authenticate(user)

    # act
    response = api_client.get(f'/workflows?search={search_text}')

    # assert
    assert response.status_code == 200
    assert len(response.data['results']) == 1


def test_list__search__comment__email__ok(api_client):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user, tasks_count=1)
    task = workflow.tasks.get(number=1)
    WorkflowEventService.comment_created_event(
        user=user,
        task=task,
        text='some ster@test.com text',
        after_create_actions=False,
    )
    search_text = 'ster'
    api_client.token_authenticate(user)

    # act
    response = api_client.get(f'/workflows?search={search_text}')

    # assert
    assert response.status_code == 200
    assert len(response.data['results']) == 1


def test_list__search__comment__markdown__ok(api_client):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user, tasks_count=1)
    task = workflow.tasks.get(number=1)
    text = 'some **[file.here](http://google.com/) value**'
    WorkflowEventService.comment_created_event(
        user=user,
        task=task,
        text=text,
        clear_text=MarkdownService.clear(text),
        after_create_actions=False,
    )
    search_text = 'file.here'
    api_client.token_authenticate(user)

    # act
    response = api_client.get(f'/workflows?search={search_text}')

    # assert
    assert response.status_code == 200
    assert len(response.data['results']) == 1


def test_list__search__comment_attachment__ok(api_client):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user, tasks_count=1)
    task = workflow.tasks.get(number=1)
    event = WorkflowEventService.comment_created_event(
        user=user,
        task=task,
        text='comment',
    )
    FileAttachment.objects.create(
        name='fred.cena',
        url='https://jo.com/image.jpg',
        size=1488,
        account_id=user.account_id,
        workflow=workflow,
        event=event,
    )
    search_text = 'fred'
    api_client.token_authenticate(user)

    # act
    response = api_client.get(f'/workflows?search={search_text}')

    # assert
    assert response.status_code == 200
    assert len(response.data['results']) == 1


def test_list__search__task_field_attachment__ok(api_client):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user, tasks_count=1)
    task = workflow.tasks.get(number=1)
    field = TaskField.objects.create(
        task=task,
        api_name='api-name-1',
        type=FieldType.FILE,
        workflow=workflow,
    )
    FileAttachment.objects.create(
        name='fred.cena',
        url='https://jo.com/image.jpg',
        size=1488,
        account_id=user.account_id,
        workflow=workflow,
        output=field,
    )
    search_text = 'fred.ce'
    api_client.token_authenticate(user)

    # act
    response = api_client.get(f'/workflows?search={search_text}')

    # assert
    assert response.status_code == 200
    assert len(response.data['results']) == 1


def test_list__search__kickoff_field_attachment__ok(api_client):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user, tasks_count=1)
    field = TaskField.objects.create(
        kickoff=workflow.kickoff_instance,
        api_name='api-name-1',
        type=FieldType.FILE,
        workflow=workflow,
    )
    FileAttachment.objects.create(
        name='fred.cena',
        url='https://jo.com/image.jpg',
        size=1488,
        account_id=user.account_id,
        workflow=workflow,
        output=field,
    )
    search_text = 'fred.ce'
    api_client.token_authenticate(user)

    # act
    response = api_client.get(f'/workflows?search={search_text}')

    # assert
    assert response.status_code == 200
    assert len(response.data['results']) == 1


def test_list__search__not_comment_event__not_found(api_client):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user, tasks_count=1)
    task = workflow.tasks.get(number=1)
    event = WorkflowEventService.task_complete_event(
        user=user,
        task=task,
    )
    search_text = 'Elton fred'
    event.text = search_text
    event.save()
    api_client.token_authenticate(user)

    # act
    response = api_client.get(f'/workflows?search={search_text}')

    # assert
    assert response.status_code == 200
    assert len(response.data['results']) == 0


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
def test_list__search__in_kickoff_field_value__ok(
    api_client,
    field_type,
):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user, tasks_count=1)
    value = 'text *fred@boy* some'
    TaskField.objects.create(
        kickoff=workflow.kickoff_instance,
        api_name='api-name-1',
        type=field_type,
        workflow=workflow,
        value=value,
        clear_value=MarkdownService.clear(value),
    )
    search_text = 'fred@boy'
    create_test_workflow(user, tasks_count=1)
    api_client.token_authenticate(user)

    # act
    response = api_client.get(f'/workflows?search={search_text}')

    # assert
    assert response.status_code == 200
    assert len(response.data['results']) == 1
    assert response.data['results'][0]['id'] == workflow.id


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
    field_type,
):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user, tasks_count=1)
    task = workflow.tasks.get(number=1)
    value = 'text fred boy some'
    TaskField.objects.create(
        task=task,
        api_name='api-name-1',
        type=field_type,
        workflow=workflow,
        value=value,
        clear_value=MarkdownService.clear(value),
    )
    search_text = 'f boy'
    api_client.token_authenticate(user)

    # act
    response = api_client.get(f'/workflows?search={search_text}')

    # assert
    assert response.status_code == 200
    assert len(response.data['results']) == 1


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
def test_list__search__in_prev_task_fields_value__ok(
    api_client,
    field_type,
):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(
        user=user,
        tasks_count=2,
        active_task_number=2,
    )
    task_1 = workflow.tasks.get(number=1)
    value = 'boy@noway.com'
    TaskField.objects.create(
        task=task_1,
        api_name='api-name-1',
        type=field_type,
        workflow=workflow,
        value=value,
        clear_value=MarkdownService.clear(value),
    )
    search_text = 'a boy@noway.com'
    api_client.token_authenticate(user)

    # act
    response = api_client.get(f'/workflows?search={search_text}')

    # assert
    assert response.status_code == 200
    assert len(response.data['results']) == 1


@pytest.mark.parametrize(
    'field_type',
    (
        FieldType.FILE,
    ),
)
def test_list__search__in_excluded_field_value__ok(
    api_client,
    field_type,
):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user, tasks_count=1)
    task = workflow.tasks.get(number=1)
    value = 'text fred boy some'
    TaskField.objects.create(
        task=task,
        api_name='api-name-1',
        type=field_type,
        workflow=workflow,
        value=value,
        clear_value=MarkdownService.clear(value),
    )
    search_text = 'f boy'
    api_client.token_authenticate(user)

    # act
    response = api_client.get(f'/workflows?search={search_text}')

    # assert
    assert response.status_code == 200
    assert len(response.data['results']) == 0


def test_list__search__markdown_filename_in_text_field__ok(api_client):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user, tasks_count=1)
    task = workflow.tasks.get(number=1)
    value = (
        'Final version \n [somefile.txt]'
        '(https://storage.googleapis.com/file.txt '
        '"attachment_id:13152 entityType:file")'
    )
    TaskField.objects.create(
        task=task,
        api_name='api-name-1',
        type=FieldType.TEXT,
        workflow=workflow,
        value=value,
        clear_value=MarkdownService.clear(value),
    )
    search_text = 'somefile.txt'
    api_client.token_authenticate(user)

    # act
    response = api_client.get(f'/workflows?search={search_text}')

    # assert
    assert response.status_code == 200
    assert len(response.data['results']) == 1


def test_list__search__full_uri_in_field__ok(api_client):

    # arrange
    user = create_test_user()
    workflow_1 = create_test_workflow(user, tasks_count=1)
    task_1 = workflow_1.tasks.get(number=1)
    value_1 = 'https://translate.com/some-page?sl=ru&tl=ru&op=taranslate'
    TaskField.objects.create(
        task=task_1,
        api_name='api-name-1',
        type=FieldType.URL,
        workflow=workflow_1,
        value=value_1,
        clear_value=MarkdownService.clear(value_1),
    )

    workflow_2 = create_test_workflow(user, tasks_count=1)
    task_2 = workflow_2.tasks.get(number=1)
    value_2 = 'https://translate.com/some-page?sl=en&tl=ru&op=taranslate'
    TaskField.objects.create(
        task=task_2,
        api_name='api-name-1',
        type=FieldType.URL,
        workflow=workflow_2,
        value=value_2,
        clear_value=MarkdownService.clear(value_2),
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        '/workflows?',
        data={'search': value_1},
    )

    # assert
    assert response.status_code == 200
    assert len(response.data['results']) == 1
    assert response.data['results'][0]['id'] == workflow_1.id


def test_list__search__prefix_uri_in_field__ok(api_client):

    # arrange
    user = create_test_user()
    workflow_1 = create_test_workflow(user, tasks_count=1)
    task_1 = workflow_1.tasks.get(number=1)
    value_1 = 'https://translate.com/some-page?sl=ru&tl=ru&op=taranslate'
    TaskField.objects.create(
        task=task_1,
        api_name='api-name-1',
        type=FieldType.URL,
        workflow=workflow_1,
        value=value_1,
        clear_value=MarkdownService.clear(value_1),
    )

    workflow_2 = create_test_workflow(user, tasks_count=1)
    task_2 = workflow_2.tasks.get(number=1)
    value_2 = 'https://translate.com/some-page?sl=en&tl=ru&op=taranslate'
    TaskField.objects.create(
        task=task_2,
        api_name='api-name-1',
        type=FieldType.URL,
        workflow=workflow_2,
        value=value_2,
        clear_value=MarkdownService.clear(value_2),
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        '/workflows?',
        data={'search': value_1},
    )

    # assert
    assert response.status_code == 200
    assert len(response.data['results']) == 1
    assert response.data['results'][0]['id'] == workflow_1.id


def test_list__search_workflow_name_with_status__ok(api_client):

    # arrange
    search_text = 'New search name'
    user = create_test_user()
    api_client.token_authenticate(user)

    running_workflow = create_test_workflow(user)
    running_workflow.name = search_text
    running_workflow.save()

    done_workflow = create_test_workflow(user)
    done_workflow.name = search_text
    done_workflow.status = WorkflowStatus.DONE
    done_workflow.save()

    # act
    response = api_client.get(
        path='/workflows',
        data={
            'search': search_text,
            'status': WorkflowApiStatus.DONE,
        },
    )

    # assert
    assert response.status_code == 200
    assert len(response.data['results']) == 1
    assert response.data['results'][0]['id'] == done_workflow.id


def test_list__search__find_union_result__ok(api_client):

    # arrange
    user = create_test_user()
    workflow_1 = create_test_workflow(
        user=user,
        name='Accounts found',
        tasks_count=1,
    )
    workflow_2 = create_test_workflow(
        user=user,
        name='Info Payable',
        tasks_count=1,
    )
    api_client.token_authenticate(user)
    search_text = 'Payable Account'

    # act
    response = api_client.get(f'/workflows?search={search_text}')

    # assert
    assert response.status_code == 200
    assert len(response.data['results']) == 2
    assert response.data['results'][0]['id'] == workflow_2.id
    assert response.data['results'][1]['id'] == workflow_1.id


def test_list__search__by_search_find_union_by_prefix__ok(
    api_client,
    mocker,
):

    # arrange
    user = create_test_user()
    workflow_1 = create_test_workflow(
        user=user,
        name='Accounts found',
        tasks_count=1,
    )
    workflow_2 = create_test_workflow(
        user=user,
        name='Info Payable',
        tasks_count=1,
    )
    api_client.token_authenticate(user)
    search_text = 'fou pa'

    # act
    response = api_client.get(f'/workflows?search={search_text}')

    # assert
    assert response.status_code == 200
    assert len(response.data['results']) == 2
    assert response.data['results'][0]['id'] == workflow_2.id
    assert response.data['results'][1]['id'] == workflow_1.id


def test_list__search__by_search_by_prefix__ok(
    api_client,
    mocker,
):

    # arrange
    user = create_test_user()
    workflow_1 = create_test_workflow(
        user=user,
        name='Accounts found',
        tasks_count=1,
    )
    task_1 = workflow_1.tasks.get(number=1)
    task_1.description = "process is a critical business function"
    task_1.save()
    create_test_workflow(
        user=user,
        name='Info financial',
        tasks_count=1,
    )
    api_client.token_authenticate(user)
    search_text = 'fou content'

    # act
    response = api_client.get(f'/workflows?search={search_text}')

    # assert
    assert response.status_code == 200
    assert len(response.data['results']) == 1
    assert response.data['results'][0]['id'] == workflow_1.id


def test_list__search__by_part__ok(
    api_client,
    mocker,
):

    # arrange
    user = create_test_user()
    template = create_test_template(user=user, tasks_count=1)
    template.description = (
        "The Accounts Payable process is a critical business function"
    )
    workflow_1 = create_test_workflow(
        template=template,
        user=user,
        name='Account found',
        tasks_count=1,
    )
    create_test_workflow(
        user=user,
        name='Info Pay',
        tasks_count=1,
    )
    api_client.token_authenticate(user)
    search_text = 'Payab Accounts'

    # act
    response = api_client.get(f'/workflows?search={search_text}')

    # assert
    assert response.status_code == 200
    assert len(response.data['results']) == 1
    assert response.data['results'][0]['id'] == workflow_1.id


def test_list__task_due_date__ok(api_client):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)
    workflow = create_test_workflow(user=user, tasks_count=1)
    due_date = timezone.now() + timedelta(hours=1)
    due_date_tsp = due_date.timestamp()
    task = workflow.tasks.first()
    task.due_date = due_date
    task.save(update_fields=['due_date'])

    # act
    response = api_client.get(
        f'/workflows?template_id={workflow.template.id}',
    )

    # assert
    assert response.status_code == 200
    response_task = response.data['results'][0]['tasks'][0]
    assert response_task['due_date_tsp'] == due_date_tsp


def test_list__filter_status_running__ok(api_client):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)
    workflow_done = create_test_workflow(
        user,
        tasks_count=1,
        status=WorkflowStatus.DONE,
    )
    workflow_done.tasks.update(status=TaskStatus.COMPLETED)
    workflow = create_test_workflow(user, tasks_count=1)
    workflow_delayed = create_test_workflow(
        user=user,
        status=WorkflowStatus.DELAYED,
        tasks_count=1,
    )
    workflow_delayed.tasks.update(status=TaskStatus.DELAYED)

    # act
    response = api_client.get(
        f'/workflows?status={WorkflowApiStatus.RUNNING}',
    )

    # assert
    assert response.status_code == 200
    assert len(response.data['results']) == 1
    assert response.data['results'][0]['id'] == workflow.id


def test_list__filter_status_delayed__ok(api_client):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)
    workflow_done = create_test_workflow(
        user,
        tasks_count=1,
        status=WorkflowStatus.DONE,
    )
    workflow_done.tasks.update(status=TaskStatus.COMPLETED)
    create_test_workflow(user=user, tasks_count=1)
    workflow_delayed = create_test_workflow(
        user=user,
        status=WorkflowStatus.DELAYED,
        tasks_count=1,
    )
    workflow_delayed.tasks.update(status=TaskStatus.DELAYED)

    # act
    response = api_client.get(
        f'/workflows?status={WorkflowApiStatus.DELAYED}',
    )

    # assert
    assert response.status_code == 200
    assert len(response.data['results']) == 1
    assert response.data['results'][0]['id'] == workflow_delayed.id


def test_list__filter_status_delayed_and_active_tasks__not_found(api_client):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)

    template = create_test_template(user, tasks_count=2)
    template_task_1 = template.tasks.get(number=1)
    create_test_workflow(user, template=template)
    create_test_workflow(
        user,
        template=template,
        status=WorkflowStatus.DELAYED,
        active_task_number=2,
    )

    # act
    response = api_client.get(
        path='/workflows',
        data={
            'template_task_api_name': template_task_1.api_name,
            'status': WorkflowApiStatus.DELAYED,
        },
    )

    # assert
    assert response.status_code == 200
    assert len(response.data['results']) == 0


@pytest.mark.parametrize(
    'status', (
        TaskStatus.SKIPPED,
        TaskStatus.PENDING,
    ),
)
def test_list__filter_template_task_api_name__not_active_task__not_found(
    api_client,
    status,
):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)
    workflow = create_test_workflow(user, tasks_count=1)
    task = workflow.tasks.get(number=1)
    task.status = status
    task.save()

    # act
    response = api_client.get(
        path='/workflows',
        data={
            'template_task_api_name': task.api_name,
        },
    )

    # assert
    assert response.status_code == 200
    assert len(response.data['results']) == 0


@pytest.mark.parametrize(
    'status', (
        TaskStatus.ACTIVE,
        TaskStatus.DELAYED,
        TaskStatus.COMPLETED,
    ),
)
def test_list__filter_template_task_api_name__active_task__ok(
    api_client,
    status,
):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)
    workflow = create_test_workflow(user, tasks_count=1)
    task = workflow.tasks.get(number=1)
    task.status = status
    task.save()

    # act
    response = api_client.get(
        path='/workflows',
        data={
            'template_task_api_name': task.api_name,
        },
    )

    # assert
    assert response.status_code == 200
    assert len(response.data['results']) == 1


def test_list__filter_template_task__and__all_statuses__ok(
    api_client,
):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)
    template = create_test_template(
        user=user,
        tasks_count=3,
        is_active=True,
    )
    template_task_2 = template.tasks.get(number=2)
    create_test_workflow(
        user,
        template=template,
        active_task_number=3,
    )
    create_test_workflow(
        user,
        template=template,
        active_task_number=2,
    )

    # act
    response = api_client.get(
        path='/workflows',
        data={
            'template_task_api_name': template_task_2.api_name,
        },
    )

    # assert
    assert response.status_code == 200
    assert len(response.data['results']) == 2


def test_list__filter_status_done__ok(api_client):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)
    workflow_done = create_test_workflow(
        user,
        tasks_count=1,
        status=WorkflowStatus.DONE,
    )
    workflow_done.tasks.update(status=TaskStatus.COMPLETED)
    create_test_workflow(user=user, tasks_count=1)
    workflow_delayed = create_test_workflow(
        user=user,
        status=WorkflowStatus.DELAYED,
        tasks_count=1,
    )
    workflow_delayed.tasks.update(status=TaskStatus.DELAYED)

    # act
    response = api_client.get(
        f'/workflows?status={WorkflowApiStatus.DONE}',
    )

    # assert
    assert response.status_code == 200
    assert len(response.data['results']) == 1
    assert response.data['results'][0]['id'] == workflow_done.id


def test_list__filter_all_status__ok(api_client):

    # arrange
    user = create_test_user()

    workflow_done = create_test_workflow(user)
    workflow_done.status = WorkflowStatus.DONE
    workflow_done.save()

    running_workflow = create_test_workflow(user)

    workflow_delayed = create_test_workflow(user)
    workflow_delayed.status = WorkflowStatus.DELAYED
    workflow_delayed.save()

    api_client.token_authenticate(user)

    # act
    response = api_client.get('/workflows?status=')

    # assert
    assert response.status_code == 200
    assert len(response.data['results']) == 3
    assert response.data['results'][2]['id'] == workflow_done.id
    assert response.data['results'][1]['id'] == running_workflow.id
    assert response.data['results'][0]['id'] == workflow_delayed.id


def test_list__filter_template__ok(api_client):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)
    template_1 = create_test_template(user=user, is_active=True)
    template_2 = create_test_template(user=user, is_active=True)
    template_3 = create_test_template(user=user, is_active=True)
    workflow_1 = create_test_workflow(user=user, template=template_1)
    workflow_2 = create_test_workflow(user=user, template=template_2)
    create_test_workflow(user=user, template=template_3)

    # act
    response = api_client.get(
        f'/workflows?template_id={template_1.id},{template_2.id}',
    )

    # assert
    assert response.status_code == 200
    assert len(response.data['results']) == 2
    assert (
        {
            response.data['results'][0]['id'],
            response.data['results'][1]['id'],
        }
    ) == {workflow_1.id, workflow_2.id}


def test_list__filter_invalid_template__validation_error(api_client):
    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)
    create_test_workflow(user)

    # act
    response = api_client.get('/workflows?template_id=undefined')

    # assert
    message = 'Value should be a list of integers.'
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    assert response.data['details']['reason'] == message
    assert response.data['details']['name'] == 'template_id'


def test_list__filter_is_external__ok(api_client):

    # arrange
    account = create_test_account()
    user = create_test_user(account=account)
    api_client.token_authenticate(user)
    create_test_workflow(user=user)
    workflow = create_test_workflow(user=user, is_external=True)

    # act
    response = api_client.get(
        '/workflows?is_external=true',
    )

    # assert
    assert response.status_code == 200
    assert len(response.data['results']) == 1
    assert response.data['results'][0]['id'] == workflow.id
    assert response.data['results'][0]['workflow_starter'] is None


def test_list__filter_is_external__default_ordering__ok(api_client):

    # arrange
    account = create_test_account()
    user = create_test_user(account=account)
    api_client.token_authenticate(user)
    workflow_2 = create_test_workflow(user=user, is_external=True)
    workflow_1 = create_test_workflow(user=user, is_external=True)
    workflow_1.date_created = timezone.now() + timedelta(hours=1)
    workflow_1.save(update_fields=['date_created'])

    # act
    response = api_client.get(
        '/workflows?is_external=true',
    )

    # assert
    assert response.status_code == 200
    assert response.data['results'][0]['id'] == workflow_1.id
    assert response.data['results'][1]['id'] == workflow_2.id


def test_list__filter_is_not_external__ok(api_client):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)
    workflow = create_test_workflow(user, is_external=False)
    create_test_workflow(user, is_external=True)

    # act
    response = api_client.get('/workflows?is_external=false')

    # assert
    assert response.status_code == 200
    assert len(response.data['results']) == 1
    assert response.data['results'][0]['id'] == workflow.id
    assert response.data['results'][0]['is_external'] is False


def test_list__filter_invalid_is_external__validation_error(api_client):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)
    create_test_workflow(user, is_external=True)
    value = 'DROP OWNED BY CURRENT USER'

    # act
    response = api_client.get(
        path=f'/workflows?is_external={value}',
    )

    # assert
    message = 'Must be a valid boolean.'
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    assert response.data['details']['reason'] == message
    assert response.data['details']['name'] == 'is_external'
    assert 'api_name' not in response.data['details']


@pytest.mark.parametrize(
    'status', (
        TaskStatus.ACTIVE,
        TaskStatus.DELAYED,
        TaskStatus.COMPLETED,
    ),
)
def test_list__filter_current_performer__active_task__ok(
    api_client,
    status,
):
    # arrange
    account = create_test_account()
    user = create_test_user(account=account)
    api_client.token_authenticate(user)
    workflow = create_test_workflow(user=user)
    task = workflow.tasks.get(number=1)
    task.status = status
    task.save()

    # act
    response = api_client.get(
        f'/workflows?current_performer={user.id}',
    )

    # assert
    assert response.status_code == 200
    assert len(response.data['results']) == 1
    assert response.data['results'][0]['id'] == workflow.id


@pytest.mark.parametrize(
    'status', (
        TaskStatus.SKIPPED,
        TaskStatus.PENDING,
    ),
)
def test_list__filter_current_performer__not_active_task__not_found(
    api_client,
    status,
):
    # arrange
    account = create_test_account()
    user = create_test_user(account=account)
    api_client.token_authenticate(user)
    workflow = create_test_workflow(user=user)
    task = workflow.tasks.get(number=1)
    task.status = status
    task.save()

    # act
    response = api_client.get(
        f'/workflows?current_performer={user.id}',
    )

    # assert
    assert response.status_code == 200
    assert len(response.data['results']) == 0


def test_list__filter_current_performer_user_in_group__ok(api_client):
    # arrange
    account = create_test_account()
    user = create_test_user(account=account)
    api_client.token_authenticate(user)
    workflow = create_test_workflow(user=user)
    group = create_test_group(account, users=[user])
    task = workflow.tasks.get(number=1)
    TaskPerformer.objects.filter(
        task=task,
    ).update(directly_status=DirectlyStatus.DELETED)
    TaskPerformer.objects.create(
        task_id=task.id,
        type=PerformerType.GROUP,
        group_id=group.id,
        directly_status=DirectlyStatus.CREATED,
    )
    # act
    response = api_client.get(
        f'/workflows?current_performer={user.id}',
    )

    # assert
    assert response.status_code == 200
    assert len(response.data['results']) == 1
    assert response.data['results'][0]['id'] == workflow.id


def test_list__filter_current_performer_group_ids_in_group__ok(api_client):
    # arrange
    account = create_test_account()
    user = create_test_user(account=account)
    api_client.token_authenticate(user)
    workflow = create_test_workflow(user=user)
    group = create_test_group(account, users=[user])
    task = workflow.tasks.get(number=1)
    TaskPerformer.objects.filter(
        task=task,
    ).update(directly_status=DirectlyStatus.DELETED)
    TaskPerformer.objects.create(
        task_id=task.id,
        type=PerformerType.GROUP,
        group_id=group.id,
        directly_status=DirectlyStatus.CREATED,
    )
    # act
    response = api_client.get(
        f'/workflows?current_performer_group_ids={group.id}',
    )

    # assert
    assert response.status_code == 200
    assert len(response.data['results']) == 1
    assert response.data['results'][0]['id'] == workflow.id


def test_list__filter_current_performer_group_ids_in_user__ok(api_client):
    # arrange
    account = create_test_account()
    user = create_test_user(account=account)
    api_client.token_authenticate(user)
    create_test_workflow(user=user)
    group = create_test_group(account, users=[user])

    # act
    response = api_client.get(
        f'/workflows?current_performer_group_ids={group.id}',
    )

    # assert
    assert response.status_code == 200
    assert len(response.data['results']) == 0


def test_list__filter__multiple_current_performer_group_ids__ok(api_client):
    # arrange
    account = create_test_account(plan=BillingPlanType.PREMIUM)
    user = create_test_user(account=account)
    another_user = create_test_user(
        account=account,
        email='another@pneumatic.app',
    )
    api_client.token_authenticate(another_user)
    template = create_test_template(user=user, tasks_count=2)
    TemplateOwner.objects.create(
        template=template,
        account=account,
        type=OwnerType.USER,
        user_id=another_user.id,
    )
    workflow = create_test_workflow(user=user, template=template)
    group1 = create_test_group(account, users=[user])
    group2 = create_test_group(account, users=[another_user])
    task = workflow.tasks.get(number=1)
    TaskPerformer.objects.filter(
        task=task,
    ).update(directly_status=DirectlyStatus.DELETED)
    TaskPerformer.objects.create(
        task_id=task.id,
        type=PerformerType.GROUP,
        group_id=group1.id,
        directly_status=DirectlyStatus.CREATED,
    )
    workflow_2 = create_test_workflow(user=user, template=template)
    task_2 = workflow_2.tasks.get(number=1)
    TaskPerformer.objects.create(
        task_id=task_2.id,
        type=PerformerType.GROUP,
        group_id=group2.id,
        directly_status=DirectlyStatus.CREATED,
    )

    # act
    response = api_client.get(
        f'/workflows?current_performer_group_ids={group1.id},{group2.id}',
    )

    # assert
    assert response.status_code == 200
    assert len(response.data['results']) == 2
    assert response.data['results'][1]['id'] == workflow.id
    assert response.data['results'][0]['id'] == workflow_2.id


def test_list__filter_multiple_current_performer_group_user__ok(api_client):
    # arrange
    account = create_test_account(plan=BillingPlanType.PREMIUM)
    user = create_test_user(account=account)
    another_user = create_test_user(
        account=account,
        email='another@pneumatic.app',
    )
    api_client.token_authenticate(another_user)
    template = create_test_template(user=user, tasks_count=2)
    TemplateOwner.objects.create(
        template=template,
        account=account,
        type=OwnerType.USER,
        user_id=another_user.id,
    )
    workflow = create_test_workflow(user=user, template=template)
    group = create_test_group(account, users=[user])
    task = workflow.tasks.get(number=1)
    TaskPerformer.objects.filter(
        task=task,
    ).update(directly_status=DirectlyStatus.DELETED)
    TaskPerformer.objects.create(
        task_id=task.id,
        type=PerformerType.GROUP,
        group_id=group.id,
        directly_status=DirectlyStatus.CREATED,
    )
    workflow_2 = create_test_workflow(user=user, template=template)
    workflow_3 = create_test_workflow(user=another_user, template=template)

    # act
    response = api_client.get(
        f'/workflows?'
        f'current_performer_group_ids={group.id}&'
        f'current_performer={user.id}',
    )

    # assert
    assert response.status_code == 200
    assert len(response.data['results']) == 3
    assert response.data['results'][2]['id'] == workflow.id
    assert response.data['results'][1]['id'] == workflow_2.id
    assert response.data['results'][0]['id'] == workflow_3.id


def test_list__filter_current_performer__not_found(api_client):
    # arrange
    account = create_test_account()
    user = create_test_user(account=account)
    user2 = create_test_user(account=account, email='test2@pneumatic.app')
    api_client.token_authenticate(user)

    template = create_test_template(user=user, tasks_count=2)
    template_task = template.tasks.get(number=1)
    template_task.raw_performers.all().delete()
    template_task.add_raw_performer(user2)
    create_test_workflow(user=user, template=template)

    # act
    response = api_client.get(
        f'/workflows?current_performer={user.id}',
    )

    # assert
    assert response.status_code == 200
    assert len(response.data['results']) == 0


def test_list__filter_multiple_current_performer__ok(api_client):

    # arrange
    account = create_test_account()
    user1 = create_test_user(account=account)
    user2 = create_test_user(account=account, email='test2@pneumatic.app')

    workflow1 = create_test_workflow(user=user1)
    workflow2 = create_test_workflow(user=user2)
    workflow2.owners.add(user1)
    api_client.token_authenticate(user1)

    # act
    response = api_client.get(
        f'/workflows?current_performer={user2.id},{user1.id}',
    )

    # assert
    assert response.status_code == 200
    assert len(response.data['results']) == 2
    assert {
        response.data['results'][0]['id'],
        response.data['results'][1]['id'],
    } == {
        workflow1.id,
        workflow2.id,
    }


@pytest.mark.parametrize('status', WorkflowApiStatus.NOT_RUNNING)
def test_list__filter_current_performer_not_running__validation_error(
    status,
    api_client,
):
    # arrange
    account = create_test_account()
    user = create_test_user(account=account)
    api_client.token_authenticate(user)
    create_test_workflow(user=user)

    # act
    response = api_client.get(
        f'/workflows?current_performer={user.id}&status={status}',
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == messages.MSG_PW_0067
    assert 'details' not in response.data


@pytest.mark.parametrize('status', WorkflowApiStatus.NOT_RUNNING)
def test_list__filter_current_performer_group_not_running__validation_error(
    status,
    api_client,
):
    # arrange
    account = create_test_account()
    user = create_test_user(account=account)
    api_client.token_authenticate(user)
    create_test_workflow(user=user)
    group = create_test_group(account, users=[user])

    # act
    response = api_client.get(
        f'/workflows?current_performer_group_ids={group.id}&status={status}',
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == messages.MSG_PW_0067
    assert 'details' not in response.data


def test_list__filter_invalid_current_performer__validation_error(api_client):
    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)
    create_test_workflow(user)

    # act
    response = api_client.get('/workflows?current_performer=undefined')

    # assert
    message = 'Value should be a list of integers.'
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    assert response.data['details']['reason'] == message
    assert response.data['details']['name'] == 'current_performer'


def test_list__filter_workflow_starter__ok(api_client):

    # arrange
    account = create_test_account()
    user = create_test_user(account=account)
    user1 = create_test_user(account=account, email='test2@pneumatic.app')
    api_client.token_authenticate(user)
    workflow = create_test_workflow(user=user)
    create_test_workflow(user=user1)
    # act
    response = api_client.get(
        f'/workflows?workflow_starter={user.id}',
    )

    # assert
    assert response.status_code == 200
    assert len(response.data['results']) == 1
    assert response.data['results'][0]['id'] == workflow.id


def test_list__filter_multiple_workflow_starter__ok(api_client):

    # arrange
    account = create_test_account()
    user = create_test_user(account=account)
    user1 = create_test_user(account=account, email='test2@pneumatic.app')
    user2 = create_test_user(account=account, email='test3@pneumatic.app')
    create_test_workflow(user=user)
    workflow1 = create_test_workflow(user=user1)
    workflow1.owners.add(user)
    workflow2 = create_test_workflow(user=user2)
    workflow2.owners.add(user)
    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        f'/workflows?workflow_starter={user1.id},{user2.id}',
    )

    # assert
    assert response.status_code == 200
    assert len(response.data['results']) == 2
    assert {
        response.data['results'][0]['id'],
        response.data['results'][1]['id'],
    } == {
        workflow1.id, workflow2.id,
    }


def test_list__filter_external_multiple_workflow_starter__ok(api_client):
    # arrange
    account = create_test_account()
    user = create_test_user(account=account)
    user2 = create_test_user(account=account, email='test2@pneumatic.app')
    workflow1 = create_test_workflow(user=user)
    workflow2 = create_test_workflow(user=user, is_external=True)
    create_test_workflow(user=user2)
    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        f'/workflows?is_external=true&workflow_starter={user.id}',
    )

    # assert
    assert response.status_code == 200
    assert len(response.data['results']) == 2
    assert {
       response.data['results'][0]['id'],
       response.data['results'][1]['id'],
    } == {
        workflow1.id, workflow2.id,
    }


def test_list__filter_invalid_workflow_starter__validation_error(api_client):
    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)
    create_test_workflow(user)

    # act
    response = api_client.get(
        '/workflows?workflow_starter=undefined',
    )

    # assert
    message = 'Value should be a list of integers.'
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    assert response.data['details']['reason'] == message
    assert response.data['details']['name'] == 'workflow_starter'


def test_list__filter_fields_kickoff_field__ok(api_client):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user, tasks_count=1)
    TaskField.objects.create(
        kickoff=workflow.kickoff_instance,
        api_name='api-name-1',
        type=FieldType.STRING,
        workflow=workflow,
        value='value',
    )
    field_api_name = 'api-name-2'
    field = TaskField.objects.create(
        kickoff=workflow.kickoff_instance,
        api_name=field_api_name,
        type=FieldType.STRING,
        workflow=workflow,
        value='raw value',
        clear_value='clear value',
        markdown_value='**bold** value',
        order=2,
        description='desc',
        is_required=True,
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.get(f'/workflows?fields={field_api_name}')

    # assert
    assert response.status_code == 200
    assert len(response.data['results']) == 1
    assert response.data['results'][0]['id'] == workflow.id
    assert len(response.data['results'][0]['fields']) == 1
    field_data = response.data['results'][0]['fields'][0]
    assert field_data['id'] == field.id
    assert field_data['order'] == field.order
    assert field_data['is_required'] == field.is_required
    assert field_data['task_id'] is None
    assert field_data['kickoff_id'] == workflow.kickoff_instance.id
    assert field_data['type'] == field.type
    assert field_data['api_name'] == field.api_name
    assert field_data['name'] == field.name
    assert field_data['description'] == field.description
    assert field_data['value'] == field.value
    assert field_data['markdown_value'] == field.markdown_value
    assert field_data['clear_value'] == field.clear_value
    assert field_data['user_id'] is None
    assert field_data['group_id'] is None


def test_list__filter_fields_task_field__ok(api_client):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user, tasks_count=1)
    task = workflow.tasks.first()
    TaskField.objects.create(
        task=task,
        api_name='api-name-1',
        type=FieldType.STRING,
        workflow=workflow,
        value='value',
    )
    field_api_name = 'api-name-2'
    field = TaskField.objects.create(
        task=task,
        api_name=field_api_name,
        type=FieldType.STRING,
        workflow=workflow,
        value='raw value',
        clear_value='clear value',
        markdown_value='**bold** value',
        order=2,
        description='desc',
        is_required=True,
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.get(f'/workflows?fields={field_api_name}')

    # assert
    assert response.status_code == 200
    assert len(response.data['results']) == 1
    assert response.data['results'][0]['id'] == workflow.id
    assert len(response.data['results'][0]['fields']) == 1
    field_data = response.data['results'][0]['fields'][0]
    assert field_data['id'] == field.id
    assert field_data['order'] == field.order
    assert field_data['is_required'] == field.is_required
    assert field_data['task_id'] == task.id
    assert field_data['kickoff_id'] is None
    assert field_data['type'] == field.type
    assert field_data['api_name'] == field.api_name
    assert field_data['name'] == field.name
    assert field_data['description'] == field.description
    assert field_data['value'] == field.value
    assert field_data['markdown_value'] == field.markdown_value
    assert field_data['clear_value'] == field.clear_value
    assert field_data['user_id'] is None
    assert field_data['group_id'] is None


def test_list__filter_fields__fields_ordering__ok(api_client):

    # arrange
    user = create_test_owner()
    workflow = create_test_workflow(user, tasks_count=2)
    task_1 = workflow.tasks.get(number=1)
    field_4 = TaskField.objects.create(
        task=task_1,
        type=FieldType.STRING,
        workflow=workflow,
        value='value',
        order=3,
        api_name='field-2',
    )
    task_2 = workflow.tasks.get(number=2)
    field_3 = TaskField.objects.create(
        task=task_2,
        type=FieldType.STRING,
        workflow=workflow,
        value='value',
        order=2,
        api_name='field-3',
    )
    field_2 = TaskField.objects.create(
        task=task_2,
        type=FieldType.STRING,
        workflow=workflow,
        value='value',
        order=1,
        api_name='field-1',
    )

    kickoff = workflow.kickoff_instance
    field_1 = TaskField.objects.create(
        kickoff=kickoff,
        type=FieldType.STRING,
        workflow=workflow,
        value='value',
        order=5,
        api_name='field-4',
    )
    task_1.number = 3
    task_1.save()
    task_2.number = 1
    task_2.save()

    api_client.token_authenticate(user)
    fields_filter = (
        f'{field_4.api_name},'
        f'{field_3.api_name},'
        f'{field_2.api_name},'
        f'{field_1.api_name}'
    )

    # act
    response = api_client.get(f'/workflows?fields={fields_filter}')

    # assert
    assert response.status_code == 200
    fields_data = response.data['results'][0]['fields']
    assert len(fields_data) == 4
    assert fields_data[0]['id'] == field_1.id
    assert fields_data[1]['id'] == field_3.id
    assert fields_data[2]['id'] == field_2.id
    assert fields_data[3]['id'] == field_4.id


def test_list__filter_fields_multiple_values__ok(api_client):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user, tasks_count=1)
    task = workflow.tasks.first()
    field_1 = TaskField.objects.create(
        task=task,
        api_name='api-name-1',
        type=FieldType.STRING,
        workflow=workflow,
        value='value',
        order=3,
    )
    field_2 = TaskField.objects.create(
        task=task,
        api_name='api-name-2',
        type=FieldType.NUMBER,
        workflow=workflow,
        value='2.13',
        order=2,
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        f'/workflows?fields={field_1.api_name},{field_2.api_name}',
    )

    # assert
    assert response.status_code == 200
    assert len(response.data['results']) == 1
    assert response.data['results'][0]['id'] == workflow.id
    assert len(response.data['results'][0]['fields']) == 2
    field_1_data = response.data['results'][0]['fields'][0]
    assert field_1_data['id'] == field_1.id
    field_2_data = response.data['results'][0]['fields'][1]
    assert field_2_data['id'] == field_2.id


def test_list__filter_fields_blank__empty_list(api_client):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user, tasks_count=1)
    task = workflow.tasks.first()
    TaskField.objects.create(
        task=task,
        api_name='api-name-1',
        type=FieldType.STRING,
        workflow=workflow,
        value='value',
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.get('/workflows?fields=')

    # assert
    assert response.status_code == 200
    assert len(response.data['results']) == 1
    assert response.data['results'][0]['id'] == workflow.id
    assert len(response.data['results'][0]['fields']) == 0


def test_list__filter_fields_not_existent_field__empty_list(api_client):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user, tasks_count=1)
    task = workflow.tasks.first()
    TaskField.objects.create(
        task=task,
        api_name='api-name-1',
        type=FieldType.STRING,
        workflow=workflow,
        value='value',
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.get('/workflows?fields=not-existent')

    # assert
    assert response.status_code == 200
    assert len(response.data['results']) == 1
    assert response.data['results'][0]['id'] == workflow.id
    assert len(response.data['results'][0]['fields']) == 0


def test_list__filter_fields__another_account_field__empty_list(api_client):

    # arrange
    another_user = create_test_user()
    workflow = create_test_workflow(another_user, tasks_count=1)
    task = workflow.tasks.first()
    field_api_name = 'api-name-1'
    TaskField.objects.create(
        task=task,
        api_name=field_api_name,
        type=FieldType.STRING,
        workflow=workflow,
        value='value',
    )
    user = create_test_owner()
    workflow_2 = create_test_workflow(user=user, tasks_count=1)
    api_client.token_authenticate(user)

    # act
    response = api_client.get(f'/workflows?fields={field_api_name}')

    # assert
    assert response.status_code == 200
    assert len(response.data['results']) == 1
    assert response.data['results'][0]['id'] == workflow_2.id
    assert len(response.data['results'][0]['fields']) == 0


def test_list__filter_fields__another_workflow_field__empty_list(api_client):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(owner, tasks_count=1)
    task = workflow.tasks.first()
    field_api_name = 'api-name-1'
    TaskField.objects.create(
        task=task,
        api_name=field_api_name,
        type=FieldType.STRING,
        workflow=workflow,
        value='value',
    )
    user = create_test_admin(account=account)
    workflow_2 = create_test_workflow(user, tasks_count=1)
    api_client.token_authenticate(user)

    # act
    response = api_client.get(f'/workflows?fields={field_api_name}')

    # assert
    assert response.status_code == 200
    assert len(response.data['results']) == 1
    assert response.data['results'][0]['id'] == workflow_2.id
    assert len(response.data['results'][0]['fields']) == 0


def test_list__filter_fields_and_template__ok(api_client):

    # arrange
    user = create_test_owner()
    template_1 = create_test_template(
        user=user,
        is_active=True,
        tasks_count=1,
    )
    workflow = create_test_workflow(
        user=user,
        template=template_1,
    )
    task = workflow.tasks.first()
    field_api_name = 'api-name-1'
    field = TaskField.objects.create(
        task=task,
        api_name=field_api_name,
        type=FieldType.STRING,
        workflow=workflow,
        value='value',
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        f'/workflows?fields={field_api_name};template_id={template_1.id}',
    )

    # assert
    assert response.status_code == 200
    assert len(response.data['results']) == 1
    assert response.data['results'][0]['id'] == workflow.id
    assert len(response.data['results'][0]['fields']) == 1
    field_data = response.data['results'][0]['fields'][0]
    assert field_data['id'] == field.id


def test_list__filter_fields_and_another_template_id__empty_list(api_client):

    # arrange
    user = create_test_owner()
    template_1 = create_test_template(
        user=user,
        is_active=True,
        tasks_count=1,
    )
    workflow = create_test_workflow(
        user=user,
        template=template_1,
    )
    task = workflow.tasks.first()
    field_api_name = 'api-name-1'
    TaskField.objects.create(
        task=task,
        api_name=field_api_name,
        type=FieldType.STRING,
        workflow=workflow,
        value='value',
    )

    another_template = create_test_template(user=user, tasks_count=1)
    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        f'/workflows?fields={field_api_name};'
        f'template_id={another_template.id}',
    )

    # assert
    assert response.status_code == 200
    assert len(response.data['results']) == 0


def test_list__ordering_oldest__ok(api_client):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)
    oldest_workflow = create_test_workflow(user=user)
    newest_workflow = create_test_workflow(user=user)

    # act
    response = api_client.get('/workflows?ordering=date')

    # assert
    assert response.status_code == 200
    assert len(response.data['results']) == 2
    assert response.data['results'][0]['id'] == oldest_workflow.id
    assert response.data['results'][1]['id'] == newest_workflow.id


def test_list__ordering_newest_first__ok(api_client):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)
    oldest_workflow = create_test_workflow(user=user)
    newest_workflow = create_test_workflow(user=user)

    # act
    response = api_client.get('/workflows?ordering=-date')

    # assert
    assert response.status_code == 200
    assert len(response.data['results']) == 2
    assert response.data['results'][0]['id'] == newest_workflow.id
    assert response.data['results'][1]['id'] == oldest_workflow.id


def test_list__ordering_overdue_first__ok(api_client):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)
    due_workflow_2 = create_test_workflow(user=user)
    due_task_2 = due_workflow_2.tasks.get(number=1)
    due_task_2.due_date = (
        due_task_2.date_first_started + timedelta(hours=24)
    )
    due_task_2.save(update_fields=['due_date'])

    due_workflow_1 = create_test_workflow(user=user)
    due_task_1 = due_workflow_1.tasks.get(number=1)
    due_task_1.due_date = (
        due_task_1.date_first_started + timedelta(hours=1)
    )
    due_task_1.save(update_fields=['due_date'])

    due_workflow_0 = create_test_workflow(user=user)
    due_task_0 = due_workflow_0.tasks.get(number=1)
    due_task_0.due_date = (
        due_task_0.date_first_started + timedelta(minutes=1)
    )
    due_task_0.save(update_fields=['due_date'])

    workflow = create_test_workflow(user=user)

    # act
    response = api_client.get('/workflows?ordering=overdue')

    # assert
    assert response.status_code == 200
    assert len(response.data['results']) == 4
    assert response.data['results'][0]['id'] == due_workflow_0.id
    assert response.data['results'][1]['id'] == due_workflow_1.id
    assert response.data['results'][2]['id'] == due_workflow_2.id
    assert response.data['results'][3]['id'] == workflow.id


def test_list__ordering_urgent_first__ok(api_client):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)

    workflow_1 = create_test_workflow(user=user)
    workflow_2 = create_test_workflow(user=user, is_urgent=True)
    workflow_3 = create_test_workflow(user=user)
    workflow_3.date_created = timezone.now() + timedelta(days=1)
    workflow_3.save(update_fields=['date_created'])

    # act
    response = api_client.get('/workflows?ordering=-urgent')

    # assert
    assert response.status_code == 200
    assert len(response.data['results']) == 3
    assert response.data['results'][0]['id'] == workflow_2.id
    assert response.data['results'][1]['id'] == workflow_3.id
    assert response.data['results'][2]['id'] == workflow_1.id


@pytest.mark.parametrize('value', ('undefined', None, []))
def test_list__invalid_ordering__validation_error(value, api_client):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)
    create_test_workflow(user=user)

    # act
    response = api_client.get(f'/workflows?ordering={value}')

    # assert
    message = f'"{value}" is not a valid choice.'
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    assert response.data['details']['reason'] == message
    assert response.data['details']['name'] == 'ordering'
    assert 'api_name' not in response.data['details']


def test_list__legacy_template_on_freemium__ok(api_client):

    # arrange
    user = create_test_user()
    another_user = create_invited_user(user)
    workflow_1 = create_test_workflow(user)
    workflow_2 = create_test_workflow(another_user)
    workflow_2.owners.add(user)
    api_client.token_authenticate(user)
    api_client.delete(f'/templates/{workflow_1.template.id}')

    # act
    response = api_client.get('/workflows')

    # assert
    assert response.status_code == 200
    assert len(response.data['results']) == 2


def test_list__legacy_template_on_premium__ok(api_client):
    # arrange
    account = create_test_account(plan=BillingPlanType.PREMIUM)
    user = create_test_user(account=account)
    another_user = create_invited_user(user)
    workflow = create_test_workflow(user)
    create_test_workflow(another_user)
    api_client.token_authenticate(user)
    api_client.delete(f'/templates/{workflow.template.id}')

    # act
    response = api_client.get('/workflows')

    # assert
    assert response.status_code == 200
    assert len(response.data['results']) == 1


def test_list__active_task_deleted_performer__ok(api_client):

    # arrange
    user = create_test_user()
    deleted_user = create_test_user(
        email='t@t.t',
        account=user.account,
    )
    workflow = create_test_workflow(user, tasks_count=1)
    task = workflow.tasks.get(number=1)
    TaskPerformersService.create_performer(
        request_user=user,
        user_key=deleted_user.id,
        task=task,
        run_actions=False,
        current_url='/page',
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    TaskPerformersService.delete_performer(
        request_user=user,
        user_key=deleted_user.id,
        task=task,
        run_actions=False,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.get('/workflows')

    # assert
    assert response.status_code == 200
    task_data = response.data['results'][0]['tasks'][0]
    assert task_data['id'] == task.id
    assert len(task_data['performers']) == 1
    assert task_data['performers'] == [
        {
            'source_id': user.id,
            'type': 'user',
            'is_completed': False,
            'date_completed_tsp': None,
        },
    ]


def test_list__guest_performer__ok(
    api_client,
):

    # arrange
    account_owner = create_test_user(is_account_owner=True)
    guest = create_test_guest(account=account_owner.account)

    workflow = create_test_workflow(account_owner, tasks_count=1)
    task = workflow.tasks.first()
    TaskPerformer.objects.create(
        task_id=task.id,
        user_id=guest.id,
    )
    TaskPerformer.objects.by_task(
        task.id,
    ).by_user(
        account_owner.id,
    ).update(directly_status=DirectlyStatus.DELETED)
    api_client.token_authenticate(account_owner)

    # act
    response = api_client.get('/workflows')

    # assert
    assert response.status_code == 200
    task_data = response.data['results'][0]['tasks'][0]
    assert task_data['id'] == task.id
    assert len(task_data['performers']) == 1
    assert task_data['performers'] == [
        {
            'source_id': guest.id,
            'type': 'user',
            'is_completed': False,
            'date_completed_tsp': None,
        },
    ]


def test_list__sub_workflow__ok(api_client):

    # arrange
    account_owner = create_test_owner()
    workflow = create_test_workflow(user=account_owner, tasks_count=1)
    ancestor_task = workflow.tasks.get(number=1)
    user = create_test_admin(account=account_owner.account)
    sub_workflow = create_test_workflow(
        user=user,
        tasks_count=1,
        ancestor_task=ancestor_task,
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.get('/workflows')

    # assert
    assert response.status_code == 200
    data = response.data['results'][0]
    assert data['id'] == sub_workflow.id
    assert data['ancestor_task_id'] == ancestor_task.id


def test_list__skip_all_tasks__found(api_client):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    template = create_test_template(
        user=owner,
        tasks_count=1,
        is_active=True,
    )
    template_task = template.tasks.get(number=1)
    condition_template = ConditionTemplate.objects.create(
        task=template_task,
        action=ConditionAction.SKIP_TASK,
        order=0,
        template=template,
    )
    rule = RuleTemplate.objects.create(
        condition=condition_template,
        template=template,
    )
    PredicateTemplate.objects.create(
        rule=rule,
        operator=PredicateOperator.COMPLETED,
        field_type=PredicateType.KICKOFF,
        template=template,
    )
    api_client.token_authenticate(owner)
    response_create = api_client.post(f'/templates/{template.id}/run')
    workflow_id = response_create.data['id']

    # act
    response = api_client.get('/workflows')

    # assert
    assert response_create.status_code == 200
    assert response.status_code == 200
    assert len(response.data['results']) == 1
    wf_data = response.data['results'][0]
    assert wf_data['id'] == workflow_id


def test_list__first_task_end_workflow__found(api_client):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    template = create_test_template(
        user=owner,
        tasks_count=1,
        is_active=True,
    )
    template_task = template.tasks.get(number=1)
    condition_template = ConditionTemplate.objects.create(
        task=template_task,
        action=ConditionAction.END_WORKFLOW,
        order=0,
        template=template,
    )
    rule = RuleTemplate.objects.create(
        condition=condition_template,
        template=template,
    )
    PredicateTemplate.objects.create(
        rule=rule,
        operator=PredicateOperator.COMPLETED,
        field_type=PredicateType.KICKOFF,
        template=template,
    )
    api_client.token_authenticate(owner)
    response_create = api_client.post(f'/templates/{template.id}/run')
    workflow_id = response_create.data['id']

    # act
    response = api_client.get('/workflows')

    # assert
    assert response_create.status_code == 200
    assert response.status_code == 200
    assert len(response.data['results']) == 1
    wf_data = response.data['results'][0]
    assert wf_data['id'] == workflow_id
