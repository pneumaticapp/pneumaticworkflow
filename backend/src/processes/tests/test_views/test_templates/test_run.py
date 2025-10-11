import pytz
import pytest
from datetime import timedelta
from django.utils import timezone
from src.analytics.actions import WorkflowActions
from src.processes.models import (
    FieldTemplate,
    Workflow,
    Template,
    FieldTemplateSelection,
    ConditionTemplate,
    RuleTemplate,
    PredicateTemplate,
    TaskPerformer,
    RawDueDateTemplate,
    WorkflowEvent,
    KickoffValue,
    FileAttachment,
    TemplateOwner,
)
from src.processes.tests.fixtures import (
    create_test_user,
    create_test_template,
    create_test_account,
    create_test_workflow,
    create_test_guest,
    create_wf_created_webhook,
    create_wf_completed_webhook,
    create_test_group,
    create_test_owner,
    create_test_admin,
)
from src.processes.serializers.workflows.events import (
    TaskEventJsonSerializer,
)
from src.processes.enums import OwnerType
from src.utils.validation import ErrorCode
from src.processes.messages import workflow as messages
from src.processes.enums import (
    WorkflowStatus,
    PerformerType,
    FieldType,
    PredicateOperator,
    DueDateRule,
    WorkflowEventType,
    TaskStatus,
    ConditionAction,
)
from src.processes.services.workflow_action import (
    WorkflowActionService,
)
from src.accounts.services import (
    UserInviteService,
)
from src.accounts.enums import (
    SourceType,
    BillingPlanType,
)
from src.authentication.enums import AuthTokenType
from src.processes.enums import DirectlyStatus
from src.processes.services.templates.integrations import (
    TemplateIntegrationsService,
)
from src.authentication.services import GuestJWTAuthService
from src.accounts.messages import MSG_A_0037
from src.generics.messages import MSG_GE_0007
from src.processes.messages.workflow import (
    MSG_PW_0030,
    MSG_PW_0028,
    MSG_PW_0031,
)
from src.processes.consts import WORKFLOW_NAME_LENGTH
from src.utils.dates import date_format
from src.processes.services.workflows.workflow import (
    WorkflowService,
)

pytestmark = pytest.mark.django_db


def test_run__all__ok(api_client, mocker):
    # arrange
    webhook_payload = mocker.Mock()
    mocker.patch(
        'src.processes.models.workflows.workflow.Workflow'
        '.webhook_payload',
        return_value=webhook_payload,
    )
    mocker.patch(
        'src.processes.services.workflow_action.'
        'WorkflowEventService.workflow_run_event',
    )
    user = create_test_user()
    create_wf_created_webhook(user)
    finalizable = True
    template_name = 'Some template'
    is_active = True
    template = create_test_template(
        user=user,
        name=template_name,
        is_active=is_active,
        finalizable=finalizable,
    )
    kickoff_field = FieldTemplate.objects.create(
        name='User name',
        type=FieldType.STRING,
        is_required=True,
        kickoff=template.kickoff_instance,
        template=template,
        order=4,
    )
    kickoff_field_2 = FieldTemplate.objects.create(
        name='User url',
        type=FieldType.URL,
        is_required=False,
        kickoff=template.kickoff_instance,
        template=template,
        order=3,
    )
    kickoff_field_3 = FieldTemplate.objects.create(
        name='User date',
        type=FieldType.DATE,
        is_required=False,
        kickoff=template.kickoff_instance,
        template=template,
        order=2,
    )
    kickoff_field_4 = FieldTemplate.objects.create(
        name='User file',
        type=FieldType.FILE,
        is_required=False,
        kickoff=template.kickoff_instance,
        template=template,
        order=1,
    )
    kickoff_field_5 = FieldTemplate.objects.create(
        name='Checkbox',
        type=FieldType.CHECKBOX,
        is_required=False,
        kickoff=template.kickoff_instance,
        template=template,
        order=0,
    )
    selection_1 = FieldTemplateSelection.objects.create(
        value='selection 1',
        field_template=kickoff_field_5,
        template=template,
    )
    selection_2 = FieldTemplateSelection.objects.create(
        value='selection 2',
        field_template=kickoff_field_5,
        template=template,
    )
    attach_1 = FileAttachment.objects.create(
        name='first_file.png',
        url='https://link.to/first_file.png',
        size=15392,
        account_id=user.account_id,
    )
    attach_2 = FileAttachment.objects.create(
        name='sec_file.docx',
        url='https://link.to/sec_file.docx',
        size=15392,
        account_id=user.account_id,
    )
    task = template.tasks.order_by('number').first()
    task.name = 'Test name {{ %s }}' % kickoff_field.api_name
    task.description = (
        '{{%s}}His name is... {{%s}} {{%s}} link {{%s}}.{{%s}}' %
        (
            kickoff_field_2.api_name,
            kickoff_field.api_name,
            kickoff_field_3.api_name,
            kickoff_field_4.api_name,
            kickoff_field_5.api_name,
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
    task_2 = template.tasks.order_by('number')[1]
    task_2_description_template = (
        '{{%s}}His name is... {{%s}}!!!' %
        (
            output_field.api_name,
            kickoff_field.api_name,
        )
    )
    task_2.description = task_2_description_template
    task_2.save()
    due_date = timezone.now() + timedelta(days=1)
    due_date_tsp = due_date.timestamp()
    analytics_mock = mocker.patch(
        'src.analytics.services.AnalyticService.'
        'workflows_started',
    )
    send_workflow_started_webhook_mock = mocker.patch(
        'src.processes.tasks.webhooks.'
        'send_workflow_started_webhook.delay',
    )
    workflow_name = 'Test name'
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        path=f'/templates/{template.id}/run',
        data={
            'is_urgent': True,
            'name': workflow_name,
            'due_date_tsp': due_date_tsp,
            'kickoff': {
                kickoff_field.api_name: 'JOHN CENA',
                kickoff_field_2.api_name: None,
                kickoff_field_3.api_name: 6351521536,
                kickoff_field_4.api_name: [str(attach_1.id), str(attach_2.id)],
                kickoff_field_5.api_name: [
                    str(selection_1.api_name),
                    str(selection_2.api_name),
                ],
            },
        },
    )

    # assert
    assert response.status_code == 200
    data = response.data
    workflow = Workflow.objects.get(id=data['id'])
    assert data['id'] == workflow.id
    assert data['name'] == workflow_name
    assert data['description'] == 'Test desc'
    assert data['date_created_tsp'] == workflow.date_created.timestamp()
    assert data['date_completed_tsp'] is None
    assert data['due_date_tsp'] == due_date.timestamp()
    assert data['is_external'] is False
    assert data['is_urgent'] is True
    assert data['finalizable'] == finalizable
    assert data['is_legacy_template'] is False
    assert data['legacy_template_name'] is None
    assert data['status'] == WorkflowStatus.RUNNING
    assert data['workflow_starter'] == user.id
    assert data['ancestor_task_id'] is None

    assert data['template']['id'] == template.id
    assert data['template']['name'] == template_name
    assert data['template']['is_active'] == is_active
    assert data['owners'] == [user.id]
    assert data['template']['wf_name_template'] is None

    task_data = data['tasks'][0]
    task = workflow.tasks.get(number=1)
    assert task_data['id'] == task.id
    assert task_data['number'] == 1
    assert task_data['name'] == 'Test name JOHN CENA'
    assert task_data['delay'] is None
    assert task_data['due_date_tsp'] is None
    assert task_data['date_started_tsp'] == task.date_started.timestamp()
    assert task_data['performers'] == [
        {
            'source_id': user.id,
            'type': 'user',
            'is_completed': False,
            'date_completed_tsp': None,
        },
    ]
    assert task_data['checklists_total'] == 0
    assert task_data['checklists_marked'] == 0

    kickoff = workflow.kickoff_instance
    assert data['kickoff']['id'] == kickoff.id
    assert len(data['kickoff']['output']) == 5
    kickoff_field_data = data['kickoff']['output'][0]
    assert kickoff_field_data['id']
    assert kickoff_field_data['type'] == kickoff_field.type
    assert kickoff_field_data['api_name'] == kickoff_field.api_name
    assert kickoff_field_data['name'] == kickoff_field.name
    assert kickoff_field_data['value'] == 'JOHN CENA'
    assert kickoff_field_data['user_id'] is None
    assert kickoff_field_data['attachments'] == []
    assert kickoff_field_data['selections'] == []

    kickoff_field_4_data = data['kickoff']['output'][3]
    assert len(kickoff_field_4_data['attachments']) == 2
    attach_1_data = kickoff_field_4_data['attachments'][0]
    assert attach_1_data['id'] == attach_1.id
    assert attach_1_data['name'] == attach_1.name
    assert attach_1_data['url'] == attach_1.url
    assert attach_1_data['size'] == attach_1.size

    kickoff_field_5_data = data['kickoff']['output'][4]
    assert len(kickoff_field_5_data['selections']) == 2
    selection_1_data = kickoff_field_5_data['selections'][0]
    assert selection_1_data['id']
    assert selection_1_data['api_name'] == selection_1.api_name
    assert selection_1_data['value'] == selection_1.value
    assert selection_1_data['is_selected'] is True
    assert data['id'] == workflow.id
    assert data['tasks'][0]['performers'] == [
        {
            'source_id': user.id,
            'type': 'user',
            'is_completed': False,
            'date_completed_tsp': None,
        },
    ]

    # Check created workflow
    assert workflow.name == workflow_name
    assert workflow.due_date == due_date
    task_1 = workflow.tasks.get(number=1)
    assert task_1.name == 'Test name JOHN CENA'
    assert task_1.description == (
        'His name is... JOHN CENA '
        'Apr 09, 2171, 11:32PM link '
        f'[{attach_1.name}]({attach_1.url}), '
        f'[{attach_2.name}]({attach_2.url}).'
        'selection 1, selection 2'
    )
    assert task_1.description_template == (
        '{{%s}}His name is... {{%s}} {{%s}} link {{%s}}.{{%s}}' %
        (
            kickoff_field_2.api_name,
            kickoff_field.api_name,
            kickoff_field_3.api_name,
            kickoff_field_4.api_name,
            kickoff_field_5.api_name,
        )
    )

    task_2 = workflow.tasks.order_by('number')[1]
    assert task_2.description == task_2_description_template
    assert task_2.description_template == (
        task_2_description_template
    )

    kickoff_value = KickoffValue.objects.get(workflow=workflow)
    assert kickoff_value.output.count() == 5
    kv_selections = kickoff_value.output.get(
        api_name=kickoff_field_5.api_name,
    ).selections

    kv_selection_1 = kv_selections.get(api_name=selection_1.api_name)
    kv_selection_2 = kv_selections.get(api_name=selection_2.api_name)
    assert kv_selection_1.value == selection_1.value
    assert kv_selection_1.is_selected
    assert kv_selection_2.value == selection_2.value
    assert kv_selection_2.is_selected

    analytics_mock.assert_called_once_with(
        workflow=workflow,
        auth_type=AuthTokenType.USER,
        is_superuser=False,
        user=user,
    )
    send_workflow_started_webhook_mock.assert_called_once_with(
        user_id=user.id,
        account_id=user.account_id,
        payload=webhook_payload,
    )


def test_run__task_due_date__ok(mocker, api_client):

    # arrange

    mocker.patch(
        'src.notifications.tasks'
        '.send_new_task_notification.delay',
    )
    mocker.patch(
        'src.processes.services.workflow_action.'
        'WorkflowEventService.workflow_run_event',
    )
    mocker.patch(
        'src.processes.services.workflow_action.'
        'WorkflowEventService.sub_workflow_run_event',
    )
    user = create_test_user()
    api_client.token_authenticate(user)
    template = create_test_template(
        user=user,
        is_active=True,
        tasks_count=1,
    )
    template_task = template.tasks.first()
    RawDueDateTemplate.objects.create(
        task=template_task,
        template=template,
        duration=timedelta(hours=24),
        duration_months=0,
        rule=DueDateRule.AFTER_TASK_STARTED,
        source_id=template_task.api_name,
    )
    mocker.patch(
        'src.analytics.services.AnalyticService.'
        'workflows_started',
    )
    mocker.patch(
        'src.processes.services.templates.'
        'integrations.TemplateIntegrationsService.api_request',
    )

    # act
    response = api_client.post(f'/templates/{template.id}/run')

    # assert
    assert response.status_code == 200
    data = response.data
    workflow = Workflow.objects.get(id=response.data['id'])
    task = workflow.tasks.get(number=1)
    task_due_date = task.date_first_started + timedelta(hours=24)
    assert data['tasks'][0]['due_date_tsp'] == task_due_date.timestamp()
    assert task.due_date == task_due_date


def test_run__task_description_with_markdown__ok(
    mocker,
    api_client,
):

    # arrange

    mocker.patch(
        'src.notifications.tasks'
        '.send_new_task_notification.delay',
    )
    mocker.patch(
        'src.processes.services.workflow_action.'
        'WorkflowEventService.workflow_run_event',
    )
    user = create_test_user()
    api_client.token_authenticate(user)
    template = create_test_template(
        user=user,
        is_active=True,
        tasks_count=1,
    )
    field = FieldTemplate.objects.create(
        name='Text',
        type=FieldType.TEXT,
        is_required=False,
        kickoff=template.kickoff_instance,
        template=template,
    )
    task_template = template.tasks.get(number=1)
    task_template.description = '**Bold {{ %s }} text**' % field.api_name
    task_template.save()
    mocker.patch(
        'src.analytics.services.AnalyticService.'
        'workflows_started',
    )
    mocker.patch(
        'src.processes.services.templates.'
        'integrations.TemplateIntegrationsService.api_request',
    )

    # act
    response = api_client.post(
        path=f'/templates/{template.id}/run',
        data={
            'kickoff': {
                field.api_name: 'some **[file.here](http://google.com/) val**',
            },
        },
    )

    # assert
    assert response.status_code == 200
    workflow = Workflow.objects.get(id=response.data['id'])
    task = workflow.tasks.get(number=1)
    assert task.description == (
        '**Bold some **[file.here](http://google.com/) val** text**'
    )
    assert task.clear_description == 'Bold some file.here val text'


def test_run__not_required_task_field__ok(mocker, api_client):

    # arrange
    mocker.patch(
        'src.processes.services.workflow_action.'
        'WorkflowEventService.workflow_run_event',
    )
    user = create_test_user()
    template = create_test_template(
        user=user,
        is_active=True,
    )
    task_1 = template.tasks.get(number=1)
    field_template = FieldTemplate.objects.create(
        task=task_1,
        name='String field',
        description='Pass here some string',
        is_required=False,
        type=FieldType.STRING,
        template=template,
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.post(f'/templates/{template.id}/run')
    assert response.status_code == 200

    workflow = Workflow.objects.get(id=response.data['id'])
    task = workflow.tasks.get(number=1)
    field = task.output.first()
    assert field.workflow_id == workflow.id
    assert field.name == field_template.name
    assert field.type == field_template.type
    assert field.description == field_template.description
    assert field.is_required is False
    assert field.value == ''


def test_run_empty_name__ok(mocker, api_client):

    # arrange
    mocker.patch(
        'src.processes.services.workflow_action.'
        'WorkflowEventService.workflow_run_event',
    )
    mocker.patch(
        'src.analytics.services.AnalyticService.'
        'workflows_started',
    )
    user = create_test_user()
    template = create_test_template(
        user=user,
        is_active=True,
    )
    date = timezone.datetime(
        year=2024,
        month=8,
        day=28,
        hour=10,
        minute=41,
        tzinfo=pytz.timezone('UTC'),
    )
    mocker.patch('django.utils.timezone.now', return_value=date)

    api_client.token_authenticate(user)

    # act
    response = api_client.post(f'/templates/{template.id}/run')

    # assert
    assert response.status_code == 200
    workflow = Workflow.objects.get(id=response.data['id'])
    formatted_date = 'Aug 28, 2024, 10:41AM'
    default_workflow_name = f'{formatted_date} — {template.name}'
    assert response.data['name'] == default_workflow_name
    assert workflow.name == default_workflow_name


def test_run__users_overlimit__permission_denied(mocker, api_client):

    # arrange
    mocker.patch(
        'src.processes.services.workflow_action.'
        'WorkflowEventService.workflow_run_event',
    )
    account = create_test_account(plan=BillingPlanType.PREMIUM)
    user = create_test_user(account=account)
    account.active_users = account.max_users + 1
    account.save()
    template = create_test_template(
        user=user,
        is_active=True,
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.post(f'/templates/{template.id}/run')

    # assert
    assert response.status_code == 403
    assert response.data['detail'] == MSG_A_0037


def test_run__performer_type_field_not_reused__ok(mocker, api_client):

    # arrange
    mocker.patch(
        'src.processes.services.workflow_action.'
        'WorkflowEventService.workflow_run_event',
    )
    user1 = create_test_user()
    user2 = create_test_user(
        account=user1.account,
        email="user2@pneumatic.app",
    )
    api_client.token_authenticate(user1)
    template = create_test_template(
        user=user1,
        tasks_count=1,
        is_active=True,
    )
    field_template = FieldTemplate.objects.create(
        name='Performer',
        is_required=True,
        type=FieldType.USER,
        kickoff=template.kickoff_instance,
        template=template,
    )
    template.tasks.first().delete_raw_performers()
    template.tasks.first().add_raw_performer(
        performer_type=PerformerType.FIELD,
        field=field_template,
    )

    # act
    api_client.post(
        f'/templates/{template.id}/run',
        data={
            'name': 'Test name',
            'kickoff': {
                field_template.api_name: user1.id,
            },
        },
    )
    api_client.post(
        f'/templates/{template.id}/run',
        data={
            'name': 'Test name',
            'kickoff': {
                field_template.api_name: user2.id,
            },
        },
    )
    template.refresh_from_db()
    workflows = template.workflows.order_by('date_created')
    workflow1 = workflows.first()
    workflow2 = workflows.last()

    # assert
    assert len(workflows) == 2
    performers1 = workflow1.tasks.first().performers
    assert performers1.count() == 1
    assert performers1.first().id == user1.id
    performers2 = workflow2.tasks.first().performers
    assert performers2.count() == 1
    assert performers2.first().id == user2.id


def test_run__create_fields__ok(mocker, api_client):

    # arrange
    mocker.patch(
        'src.processes.services.workflow_action.'
        'WorkflowEventService.workflow_run_event',
    )
    user = create_test_user()
    api_client.token_authenticate(user)

    template = create_test_template(
        user=user,
        is_active=True,
    )

    FieldTemplate.objects.create(
        name='Task performer',
        type=FieldType.USER,
        is_required=True,
        task=template.tasks.first(),
        template=template,
    )

    # act
    response = api_client.post(
        f'/templates/{template.id}/run',
        data={
            'name': 'test workflow',
        },
    )
    # assert
    assert response.status_code == 200
    workflow = Workflow.objects.get(id=response.data['id'])
    task_1 = workflow.tasks.get(number=1)
    assert task_1.output.count() == 1


def test_run__skip_task_condition_by_two_predicates__ok(api_client, mocker):

    # arrange
    mocker.patch(
        'src.processes.services.workflow_action.'
        'WorkflowEventService.workflow_run_event',
    )
    user = create_test_user()
    api_client.token_authenticate(user)

    template = create_test_template(
        user=user,
        is_active=True,
    )
    kickoff_field = FieldTemplate.objects.create(
        name='User name',
        type=FieldType.STRING,
        is_required=True,
        kickoff=template.kickoff_instance,
        template=template,
    )
    second_kickoff_field = FieldTemplate.objects.create(
        name='Second name',
        type=FieldType.STRING,
        is_required=True,
        kickoff=template.kickoff_instance,
        template=template,
    )
    template_task_1 = template.tasks.get(number=1)
    condition_template = ConditionTemplate.objects.create(
        task=template_task_1,
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
        operator=PredicateOperator.EQUAL,
        field_type=FieldType.STRING,
        field=kickoff_field.api_name,
        value='123',
        template=template,
    )
    PredicateTemplate.objects.create(
        rule=rule,
        operator=PredicateOperator.EQUAL,
        field_type=FieldType.STRING,
        field=second_kickoff_field.api_name,
        value='456',
        template=template,
    )

    send_new_task_notification_mock = mocker.patch(
        'src.processes.services.workflow_action.'
        'send_new_task_notification.delay',
    )

    # act
    response = api_client.post(
        f'/templates/{template.id}/run',
        data={
            'name': 'test workflow',
            'kickoff': {
                kickoff_field.api_name: '123',
                second_kickoff_field.api_name: '456',
            },
        },
    )

    # assert
    assert response.status_code == 200
    workflow = Workflow.objects.get(id=response.data['id'])
    task_1 = workflow.tasks.get(number=1)
    task_2 = workflow.tasks.get(number=2)
    assert task_1.is_skipped
    assert task_2.is_active
    send_new_task_notification_mock.assert_called_once()


def test_run__conditions_end_workflow_and_skip_task__has_higher_priority(
    api_client,
    mocker,
):

    # arrange
    mocker.patch(
        'src.processes.services.workflow_action.'
        'WorkflowEventService.workflow_run_event',
    )
    user = create_test_user()
    api_client.token_authenticate(user)

    template = create_test_template(
        user=user,
        is_active=True,
        tasks_count=2,
    )
    kickoff_field = FieldTemplate.objects.create(
        name='Condition field',
        type=FieldType.STRING,
        is_required=True,
        kickoff=template.kickoff_instance,
        template=template,
    )
    template_task_1 = template.tasks.get(number=1)
    condition_template = ConditionTemplate.objects.create(
        task=template_task_1,
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
        operator=PredicateOperator.EQUAL,
        field_type=FieldType.STRING,
        field=kickoff_field.api_name,
        value='skip or end',
        template=template,
    )

    condition_template_2 = ConditionTemplate.objects.create(
        task=template_task_1,
        action=ConditionAction.END_WORKFLOW,
        order=1,
        template=template,
    )
    rule_2 = RuleTemplate.objects.create(
        condition=condition_template_2,
        template=template,
    )
    PredicateTemplate.objects.create(
        rule=rule_2,
        operator=PredicateOperator.EQUAL,
        field_type=FieldType.STRING,
        field=kickoff_field.api_name,
        value='skip or end',
        template=template,
    )

    send_new_task_notification_mock = mocker.patch(
        'src.processes.services.workflow_action.'
        'send_new_task_notification.delay',
    )

    # act
    response = api_client.post(
        f'/templates/{template.id}/run',
        data={
            'kickoff': {
                kickoff_field.api_name: 'skip or end',
            },
        },
    )

    # assert
    assert response.status_code == 200
    workflow = Workflow.objects.get(id=response.data['id'])
    task_1 = workflow.tasks.get(number=1)
    task_2 = workflow.tasks.get(number=2)
    assert workflow.status == WorkflowStatus.DONE
    assert task_1.is_pending
    assert task_2.is_pending
    send_new_task_notification_mock.assert_not_called()


def test_run__skip_task__fields_is_empty(api_client, mocker):

    """ More about the case in the https://trello.com/c/LxXWlXWl """

    # arrange
    mocker.patch(
        'src.processes.services.workflow_action.'
        'WorkflowEventService.workflow_run_event',
    )
    account = create_test_account(plan=BillingPlanType.PREMIUM)
    user = create_test_user(account=account)
    api_client.token_authenticate(user)

    api_name_skip_field = 'skip-field'
    api_name_skip_selection = 'skip-selection'
    api_name_file = 'file-field-1'
    api_name_url = 'url-field-1'
    api_name_str = 'str-field-1'
    api_name_text = 'text-field-1'
    api_name_checkbox = 'box-field-1'
    api_name_radio = 'radio-field-1'
    api_name_dropdown = 'drop-field-1'

    task_2_name = 'Second {{%s}}step' % api_name_str
    task_2_description = '{{%s}}{{%s}}{{%s}}{{%s}}{{%s}}{{%s}}{{%s}}' % (
        api_name_file,
        api_name_url,
        api_name_str,
        api_name_text,
        api_name_checkbox,
        api_name_radio,
        api_name_dropdown,
    )

    template = create_test_template(
        user=user,
        is_active=True,
        tasks_count=2,
    )
    template_task_1 = template.tasks.get(number=1)
    template_task_2 = template.tasks.get(number=2)
    template_task_2.name = task_2_name
    template_task_2.description = task_2_description
    template_task_2.save()

    checkbox_field = FieldTemplate.objects.create(
        order=1,
        name='Skip first task',
        type=FieldType.CHECKBOX,
        is_required=False,
        kickoff=template.kickoff_instance,
        template=template,
        api_name=api_name_skip_field,
    )
    selection = FieldTemplateSelection.objects.create(
        value='Click to skip first step',
        field_template=checkbox_field,
        api_name=api_name_skip_selection,
        template=template,
    )

    FieldTemplate.objects.create(
        order=1,
        name='Attached file',
        type=FieldType.FILE,
        is_required=False,
        task=template_task_1,
        template=template,
        api_name=api_name_file,
    )
    FieldTemplate.objects.create(
        order=2,
        name='Attached URL',
        type=FieldType.URL,
        is_required=False,
        task=template_task_1,
        template=template,
        api_name=api_name_url,
    )
    FieldTemplate.objects.create(
        order=3,
        name='String field',
        type=FieldType.STRING,
        is_required=False,
        task=template_task_1,
        template=template,
        api_name=api_name_str,
    )
    FieldTemplate.objects.create(
        order=4,
        name='Text field',
        type=FieldType.TEXT,
        is_required=False,
        task=template_task_1,
        template=template,
        api_name=api_name_text,
    )
    checkbox_field = FieldTemplate.objects.create(
        order=5,
        name='Checkbox field',
        type=FieldType.CHECKBOX,
        is_required=False,
        task=template_task_1,
        template=template,
        api_name=api_name_checkbox,
    )
    FieldTemplateSelection.objects.create(
        value='First checkbox',
        field_template=checkbox_field,
        template=template,
    )
    FieldTemplateSelection.objects.create(
        value='Second checkbox',
        field_template=checkbox_field,
        template=template,
    )

    radio_field = FieldTemplate.objects.create(
        order=6,
        name='Radio field',
        type=FieldType.RADIO,
        is_required=False,
        task=template_task_1,
        template=template,
        api_name=api_name_radio,
    )
    FieldTemplateSelection.objects.create(
        value='First radio',
        field_template=radio_field,
        template=template,
    )
    FieldTemplateSelection.objects.create(
        value='Second radio',
        field_template=radio_field,
        template=template,
    )

    dropdown_field = FieldTemplate.objects.create(
        order=7,
        name='Dropdown field',
        type=FieldType.DROPDOWN,
        is_required=False,
        task=template_task_1,
        template=template,
        api_name=api_name_dropdown,
    )
    FieldTemplateSelection.objects.create(
        value='First selection',
        field_template=dropdown_field,
        template=template,
    )
    FieldTemplateSelection.objects.create(
        value='Second selection',
        field_template=dropdown_field,
        template=template,
    )

    condition_template = ConditionTemplate.objects.create(
        task=template_task_1,
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
        operator=PredicateOperator.EQUAL,
        field_type=FieldType.CHECKBOX,
        field=api_name_skip_field,
        value=api_name_skip_selection,
        template=template,
    )

    # act
    response = api_client.post(
        f'/templates/{template.id}/run',
        data={
            'kickoff': {
                api_name_skip_field: [selection.api_name],
            },
        },
    )
    workflow = Workflow.objects.get(id=response.data['id'])

    # assert
    assert response.status_code == 200
    task_1 = workflow.tasks.get(number=1)
    assert task_1.is_skipped
    task_2 = workflow.tasks.get(number=2)
    assert task_2.status == TaskStatus.ACTIVE
    assert task_2.name == 'Second step'
    assert task_2.description == ''


def test_skip_delayed_task__fields_is_empty(mocker, api_client):

    """ More about the case in the https://trello.com/c/LxXWlXWl """

    # arrange
    mocker.patch(
        'src.processes.services.workflow_action.'
        'WorkflowEventService.workflow_run_event',
    )
    account = create_test_account(plan=BillingPlanType.PREMIUM)
    user = create_test_user(account=account)
    api_client.token_authenticate(user)

    mocker.patch(
        'src.notifications.tasks'
        '.send_new_task_notification.delay',
    )
    mocker.patch(
        'src.processes.services.workflow_action.'
        'send_new_task_notification.delay',
    )

    api_name_skip_field = 'skip-field'
    api_name_skip_selection = 'skip-selection'
    api_name_file = 'file-field-1'
    api_name_url = 'url-field-1'
    api_name_str = 'str-field-1'
    api_name_text = 'text-field-1'
    api_name_checkbox = 'box-field-1'
    api_name_radio = 'radio-field-1'
    api_name_dropdown = 'drop-field-1'

    task_2_name = 'Second {{%s}}step' % api_name_str
    task_2_result_name = 'Second step'
    task_2_description = '{{%s}}{{%s}}{{%s}}{{%s}}{{%s}}{{%s}}{{%s}}' % (
        api_name_file,
        api_name_url,
        api_name_str,
        api_name_text,
        api_name_checkbox,
        api_name_radio,
        api_name_dropdown,
    )
    task_2_result_description = ''

    fields_data = [
        {
            'order': 1,
            'name': 'Attached file',
            'type': FieldType.FILE,
            'is_required': False,
            'api_name': api_name_file,
        },
        {
            'order': 2,
            'name': 'Attached URL',
            'type': FieldType.URL,
            'is_required': False,
            'api_name': api_name_url,
        },
        {
            'order': 3,
            'name': 'String field',
            'type': FieldType.STRING,
            'is_required': False,
            'api_name': api_name_str,
        },
        {
            'order': 4,
            'name': 'Text field',
            'type': FieldType.TEXT,
            'is_required': False,
            'api_name': api_name_text,
        },
        {
            'order': 5,
            'name': 'Checkbox field',
            'type': FieldType.CHECKBOX,
            'is_required': False,
            'api_name': api_name_checkbox,
            'selections': [
                {'value': 'First checkbox'},
                {'value': 'Second checkbox'},
            ],
        },
        {
            'order': 6,
            'name': 'Radio field',
            'type': FieldType.RADIO,
            'is_required': False,
            'api_name': api_name_radio,
            'selections': [
                {'value': 'First radio'},
                {'value': 'Second radio'},
            ],
        },
        {
            'order': 7,
            'type': FieldType.DROPDOWN,
            'name': 'Dropdown field',
            'is_required': False,
            'api_name': api_name_dropdown,
            'selections': [
                {'value': 'First selection'},
                {'value': 'Second selection'},
            ],
        },

    ]

    conditions_data = [
        {
            'order': 1,
            'action': 'skip_task',
            'api_name': 'condition-1',
            'rules': [
                {
                    'predicates': [
                        {
                            'field': api_name_skip_field,
                            'field_type': FieldType.CHECKBOX,
                            'operator': PredicateOperator.EQUAL,
                            'value': api_name_skip_selection,
                        },
                    ],
                },
            ],
        },
    ]

    response_create = api_client.post(
        path='/templates',
        data={
            'name': 'Template',
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
                        'order': 1,
                        'name': 'Skip first task',
                        'api_name': api_name_skip_field,
                        'type': FieldType.CHECKBOX,
                        'is_required': False,
                        'selections': [
                            {
                                'api_name': api_name_skip_selection,
                                'value': 'Click to skip first step',
                            },
                        ],
                    },
                ],
            },
            'tasks': [
                {
                    'number': 1,
                    'name': 'Skipped step',
                    'api_name': 'task-1',
                    'fields': fields_data,
                    'raw_performers': [
                        {
                            'type': PerformerType.USER,
                            'source_id': user.id,
                        },
                    ],
                    'conditions': conditions_data,
                },
                {
                    'number': 2,
                    'name': task_2_name,
                    'description': task_2_description,
                    'api_name': 'task-2',
                    'delay': '00:10:00',
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
    template = Template.objects.get(id=response_create.data['id'])
    selection = FieldTemplateSelection.objects.get(
        api_name=api_name_skip_selection,
    )
    response = api_client.post(
        f'/templates/{template.id}/run',
        data={
            'name': 'test workflow',
            'kickoff': {
                api_name_skip_field: [selection.api_name],
            },
        },
    )
    workflow = Workflow.objects.get(id=response.data['id'])
    service = WorkflowActionService(user=user, workflow=workflow)
    task_2 = workflow.tasks.get(number=2)

    # act
    service.resume_task(task_2)

    # assert
    assert response_create.status_code == 200
    assert response.status_code == 200
    assert task_2.status == TaskStatus.ACTIVE
    assert task_2.name == task_2_result_name
    assert task_2.description == task_2_result_description


def test_run__end_workflow_condition_true__end_workflow(api_client, mocker):

    # arrange
    webhook_payload = mocker.Mock()
    mocker.patch(
        'src.processes.models.workflows.workflow.Workflow'
        '.webhook_payload',
        return_value=webhook_payload,
    )
    send_workflow_started_webhook_mock = mocker.patch(
        'src.processes.tasks.webhooks.'
        'send_workflow_started_webhook.delay',
    )
    send_workflow_completed_webhook_mock = mocker.patch(
        'src.processes.services.workflow_action.'
        'send_workflow_completed_webhook.delay',
    )
    mocker.patch(
        'src.processes.services.workflow_action.'
        'WorkflowEventService.workflow_run_event',
    )
    user = create_test_user()
    create_wf_created_webhook(user)
    create_wf_completed_webhook(user)
    api_client.token_authenticate(user)

    template = create_test_template(
        user=user,
        is_active=True,
    )
    kickoff_field = FieldTemplate.objects.create(
        name='User name',
        type=FieldType.STRING,
        is_required=True,
        kickoff=template.kickoff_instance,
        template=template,
    )
    second_kickoff_field = FieldTemplate.objects.create(
        name='Second name',
        type=FieldType.STRING,
        is_required=True,
        kickoff=template.kickoff_instance,
        template=template,
    )

    condition_template = ConditionTemplate.objects.create(
        task=template.tasks.first(),
        action=ConditionAction.END_WORKFLOW,
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
        field=kickoff_field.api_name,
        value='123',
        template=template,
    )
    PredicateTemplate.objects.create(
        rule=rule_1,
        operator=PredicateOperator.EQUAL,
        field_type=FieldType.STRING,
        field=second_kickoff_field.api_name,
        value='456',
        template=template,
    )

    # act
    response = api_client.post(
        f'/templates/{template.id}/run',
        data={
            'name': 'test workflow',
            'kickoff': {
                kickoff_field.api_name: '123',
                second_kickoff_field.api_name: '456',
            },
        },
    )

    # assert
    assert response.status_code == 200
    workflow = Workflow.objects.get(id=response.data['id'])
    assert workflow.status == WorkflowStatus.DONE
    send_workflow_started_webhook_mock.assert_called_once_with(
        user_id=user.id,
        account_id=user.account_id,
        payload=webhook_payload,
    )
    send_workflow_completed_webhook_mock.assert_called_once_with(
        user_id=user.id,
        account_id=user.account_id,
        payload=webhook_payload,
    )


def test_run__skip_task_condition_by_one_of_predicates__ok(
    api_client,
    mocker,
):

    # arrange
    mocker.patch(
        'src.processes.tasks.webhooks.'
        'send_workflow_started_webhook.delay',
    )
    mocker.patch(
        'src.processes.services.workflow_action.'
        'WorkflowEventService.workflow_run_event',
    )
    user = create_test_user()
    create_wf_created_webhook(user)
    api_client.token_authenticate(user)

    template = create_test_template(
        user=user,
        is_active=True,
    )
    template_task_1 = template.tasks.get(number=1)
    kickoff_field = FieldTemplate.objects.create(
        name='User name',
        type=FieldType.STRING,
        is_required=True,
        kickoff=template.kickoff_instance,
        template=template,
    )
    second_kickoff_field = FieldTemplate.objects.create(
        name='Second name',
        type=FieldType.STRING,
        is_required=True,
        kickoff=template.kickoff_instance,
        template=template,
    )

    condition_template = ConditionTemplate.objects.create(
        task=template_task_1,
        action=ConditionAction.SKIP_TASK,
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
        field=kickoff_field.api_name,
        value='123',
        template=template,
    )
    rule_2 = RuleTemplate.objects.create(
        condition=condition_template,
        template=template,
    )
    PredicateTemplate.objects.create(
        rule=rule_2,
        operator=PredicateOperator.EQUAL,
        field_type=FieldType.STRING,
        field=second_kickoff_field.api_name,
        value='456',
        template=template,
    )

    # act
    response = api_client.post(
        f'/templates/{template.id}/run',
        data={
            'name': 'test workflow',
            'kickoff': {
                kickoff_field.api_name: '123',
                second_kickoff_field.api_name: 'invalid',
            },
        },
    )

    # assert
    assert response.status_code == 200
    workflow = Workflow.objects.get(id=response.data['id'])
    task_1 = workflow.tasks.get(number=1)
    task_2 = workflow.tasks.get(number=2)
    assert task_1.is_skipped
    assert task_2.is_active


def test_run__cancel_delay__ok(api_client, mocker):

    # arrange
    mocker.patch(
        'src.processes.services.workflow_action.'
        'WorkflowEventService.workflow_run_event',
    )
    user = create_test_user()
    api_client.token_authenticate(user)
    response = api_client.post(
        path='/templates',
        data={
            'name': 'Template',
            'description': 'Desc',
            'owners': [
                {
                    'type': OwnerType.USER,
                    'source_id': user.id,
                },
            ],
            'is_active': True,
            'finalizable': True,
            'kickoff': {
                'fields': [],
            },
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
                    'delay': '10:00:00',
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
    template = Template.objects.get(id=response.data['id'])
    template_task_1 = template.tasks.get(number=1)
    template_task_2 = template.tasks.get(number=2)

    response = api_client.post(
        path=f'/templates/{template.id}/run',
        data={},
    )

    workflow = Workflow.objects.get(pk=response.data['id'])
    task = workflow.tasks.get(number=1)
    response_complete = api_client.post(f'/v2/tasks/{task.id}/complete')

    mocker.patch(
        'src.processes.services.templates.'
        'integrations.TemplateIntegrationsService.template_updated',
    )

    # act
    response = api_client.put(
        path=f'/templates/{template.id}',
        data={
            'name': 'Template',
            'description': 'Desc',
            'owners': [
                {
                    'type': OwnerType.USER,
                    'source_id': user.id,
                },
            ],
            'is_active': True,
            'finalizable': True,
            'kickoff': {
                'fields': [],
            },
            'tasks': [
                {
                    'id': template_task_1.id,
                    'number': 1,
                    'name': 'First step',
                    'api_name': template_task_1.api_name,
                    'raw_performers': [
                        {
                            'type': PerformerType.USER,
                            'source_id': user.id,
                        },
                    ],
                },
                {
                    'id': template_task_2.id,
                    'number': 2,
                    'name': 'Second step',
                    'api_name': template_task_2.api_name,
                    'raw_performers': [
                        {
                            'type': PerformerType.USER,
                            'source_id': user.id,
                        },
                    ],
                    'delay': '',
                },
            ],
        },
    )

    # assert
    assert response_complete.status_code == 200
    assert response.status_code == 200
    template_task_2.refresh_from_db()
    assert template_task_2.delay is None
    workflow.refresh_from_db()
    task2 = workflow.tasks.get(number=2)
    assert task2.get_active_delay() is None
    assert workflow.status == WorkflowStatus.RUNNING


@pytest.mark.parametrize(
    'value',
    [
        '192.168.0.1',
        'https://192.168.0.1',
        'https://192.168.0.1/templates?param=12;param2=',
        'https://my.pneumatic.app',
        'https://my.pneumatic.app/templates?param=12;param2=',
        'http://my.pneumatic.app',
        'my.pneumatic.app',
        'my.pneumatic.app/templates?param=12;param2=',
    ],
)
def test_run__type_url__ok(mocker, value, api_client):

    # arrange
    mocker.patch(
        'src.processes.services.workflow_action.'
        'WorkflowEventService.workflow_run_event',
    )
    user = create_test_user()
    api_client.token_authenticate(user)
    template = create_test_template(
        user=user,
        is_active=True,
    )
    field_template = FieldTemplate.objects.create(
        name='Absolute URL',
        type=FieldType.URL,
        is_required=True,
        kickoff=template.kickoff_instance,
        template=template,
    )

    # act
    response = api_client.post(
        path=f'/templates/{template.id}/run',
        data={
            'name': 'Test name',
            'kickoff': {
                field_template.api_name: value,
            },
        },
    )

    # assert
    assert response.status_code == 200
    workflow = Workflow.objects.get(id=response.data['id'])
    field = workflow.kickoff_instance.output.first()
    assert field.value == value


def test_run__type_number__ok(mocker, api_client):

    # arrange
    mocker.patch(
        'src.processes.services.workflow_action.'
        'WorkflowEventService.workflow_run_event',
    )
    user = create_test_user()
    api_client.token_authenticate(user)
    template = create_test_template(
        user=user,
        is_active=True,
    )
    field_template = FieldTemplate.objects.create(
        name='Price',
        type=FieldType.NUMBER,
        is_required=True,
        kickoff=template.kickoff_instance,
        template=template,
    )
    value = '30.01'

    # act
    response = api_client.post(
        path=f'/templates/{template.id}/run',
        data={
            'name': 'Test name',
            'kickoff': {
                field_template.api_name: value,
            },
        },
    )

    # assert
    assert response.status_code == 200
    workflow = Workflow.objects.get(id=response.data['id'])
    field = workflow.kickoff_instance.output.first()
    assert field.value == value


@pytest.mark.parametrize(
    'value',
    [
        'https://my.pneumatic.app/broken space/here',
        'my.pneumatic.app/broken space/here',
        'ssh://my.pneumatic.app',
        'my.pneumatic.app http://my.pneumatic.app',
        'relative/path/to',
        'relative/path',
        '/relative/path/',
        '://my.pneumatic.app',
    ],
)
def test_run__type_url_invalid_url__validation_error(
    mocker,
    value,
    api_client,
):
    # arrange
    workflow_run_event_mock = mocker.patch(
        'src.processes.services.workflow_action.'
        'WorkflowEventService.workflow_run_event',
    )
    user = create_test_user()
    api_client.token_authenticate(user)
    template = create_test_template(
        user=user,
        is_active=True,
    )
    field_template = FieldTemplate.objects.create(
        name='Absolute URL',
        type=FieldType.URL,
        is_required=True,
        kickoff=template.kickoff_instance,
        template=template,
    )

    # act
    response = api_client.post(
        path=f'/templates/{template.id}/run',
        data={
            'name': 'Test name',
            'kickoff': {
                field_template.api_name: value,
            },
        },
    )

    # assert
    assert response.status_code == 400
    workflow_run_event_mock.assert_not_called()


def test_run__skip_task_1_event__ok(
    mocker,
    api_client,
):
    # arrange
    mocker.patch(
        'src.processes.services.workflow_action.'
        'WorkflowEventService.workflow_run_event',
    )
    user = create_test_user()
    api_client.token_authenticate(user=user)
    template = create_test_template(
        user=user,
        is_active=True,
        tasks_count=2,
    )
    output_field = FieldTemplate.objects.create(
        type=FieldType.TEXT,
        name='Past name',
        description='Last description',
        kickoff=template.kickoff_instance,
        template=template,
    )
    task_template_1 = template.tasks.get(number=1)
    condition_template = ConditionTemplate.objects.create(
        task=task_template_1,
        action=ConditionAction.SKIP_TASK,
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
        field_type=FieldType.TEXT,
        field=output_field.api_name,
        value='JOHN CENA',
        template=template,
    )

    # act
    response = api_client.post(
        f'/templates/{template.id}/run',
        data={
            'kickoff': {
                output_field.api_name: 'JOHN CENA',
            },
        },
    )
    workflow = Workflow.objects.get(id=response.data['id'])

    # assert
    assert response.status_code == 200
    task_1 = workflow.tasks.get(number=1)
    assert task_1.is_skipped
    task_2 = workflow.tasks.get(number=2)
    assert task_2.is_active
    assert WorkflowEvent.objects.filter(
        workflow=workflow,
        account=user.account,
        type=WorkflowEventType.TASK_SKIP,
        task_json=TaskEventJsonSerializer(
            instance=task_1,
            context={
                'event_type': WorkflowEventType.TASK_SKIP,
            },
        ).data,
    ).count() == 1

    assert WorkflowEvent.objects.filter(
        workflow=workflow,
        account=user.account,
        type=WorkflowEventType.TASK_START,
        task_json=TaskEventJsonSerializer(
            instance=task_1,
            context={
                'event_type': WorkflowEventType.TASK_START,
            },
        ).data,
    ).count() == 0


@pytest.mark.parametrize('value', ('undefined', ['undefined']))
def test_run__field_type_radio_invalid__validation_error(
    mocker,
    value,
    api_client,
):

    # arrange
    workflow_run_event_mock = mocker.patch(
        'src.processes.services.workflow_action.'
        'WorkflowEventService.workflow_run_event',
    )
    user = create_test_user()
    api_client.token_authenticate(user)

    template = create_test_template(
        user=user,
        is_active=True,
        tasks_count=1,
    )

    field_template = FieldTemplate.objects.create(
        name='Radio',
        type=FieldType.RADIO,
        is_required=True,
        kickoff=template.kickoff_instance,
        template=template,
    )
    FieldTemplateSelection.objects.create(
        value='radio selection',
        field_template=field_template,
        template=template,
    )

    # act
    response = api_client.post(
        f'/templates/{template.id}/run',
        data={
            'name': 'test process',
            'kickoff': {
                field_template.api_name: value,
            },
        },
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == MSG_PW_0028
    assert response.data['details']['api_name'] == field_template.api_name
    assert response.data['details']['reason'] == MSG_PW_0028
    workflow_run_event_mock.assert_not_called()


@pytest.mark.parametrize('value', ('undefined', ['undefined']))
def test_run__field_type_dropdown_invalid__validation_error(
    value,
    mocker,
    api_client,
):

    # arrange
    workflow_run_event_mock = mocker.patch(
        'src.processes.services.workflow_action.'
        'WorkflowEventService.workflow_run_event',
    )
    user = create_test_user()
    api_client.token_authenticate(user)

    template = create_test_template(
        user=user,
        is_active=True,
        tasks_count=1,
    )

    field_template = FieldTemplate.objects.create(
        name='Radio',
        type=FieldType.DROPDOWN,
        is_required=True,
        kickoff=template.kickoff_instance,
        template=template,
    )
    FieldTemplateSelection.objects.create(
        value='dropdown selection',
        field_template=field_template,
        template=template,
    )

    # act
    response = api_client.post(
        f'/templates/{template.id}/run',
        data={
            'name': 'test process',
            'kickoff': {
                field_template.api_name: value,
            },
        },
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == MSG_PW_0028
    assert response.data['details']['reason'] == MSG_PW_0028
    assert response.data['details']['api_name'] == field_template.api_name
    workflow_run_event_mock.assert_not_called()


def test_run__field_type_checkbox_invalid__validation_error(
    mocker,
    api_client,
):

    # arrange
    value = [None]
    workflow_run_event_mock = mocker.patch(
        'src.processes.services.workflow_action.'
        'WorkflowEventService.workflow_run_event',
    )
    user = create_test_user()
    api_client.token_authenticate(user)

    template = create_test_template(
        user=user,
        is_active=True,
        tasks_count=1,
    )

    field_template = FieldTemplate.objects.create(
        name='Checkbox',
        type=FieldType.CHECKBOX,
        is_required=True,
        kickoff=template.kickoff_instance,
        template=template,
    )
    FieldTemplateSelection.objects.create(
        value='checkbox selection',
        field_template=field_template,
        template=template,
    )

    # act
    response = api_client.post(
        f'/templates/{template.id}/run',
        data={
            'name': 'test process',
            'kickoff': {
                field_template.api_name: value,
            },
        },
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == MSG_PW_0030
    assert response.data['details']['reason'] == MSG_PW_0030
    assert response.data['details']['api_name'] == field_template.api_name
    workflow_run_event_mock.assert_not_called()


def test_run__field_type_checkbox_non_existent__validation_error(
    mocker,
    api_client,
):

    # arrange
    value = ['undefined']
    workflow_run_event_mock = mocker.patch(
        'src.processes.services.workflow_action.'
        'WorkflowEventService.workflow_run_event',
    )
    user = create_test_user()
    api_client.token_authenticate(user)

    template = create_test_template(
        user=user,
        is_active=True,
        tasks_count=1,
    )

    field_template = FieldTemplate.objects.create(
        name='Checkbox',
        type=FieldType.CHECKBOX,
        is_required=True,
        kickoff=template.kickoff_instance,
        template=template,
    )
    FieldTemplateSelection.objects.create(
        value='checkbox selection',
        field_template=field_template,
        template=template,
    )

    # act
    response = api_client.post(
        f'/templates/{template.id}/run',
        data={
            'name': 'test process',
            'kickoff': {
                field_template.api_name: value,
            },
        },
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == MSG_PW_0031
    assert response.data['details']['reason'] == MSG_PW_0031
    assert response.data['details']['api_name'] == field_template.api_name
    workflow_run_event_mock.assert_not_called()


def test_run__is_urgent__ok(mocker, api_client):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    user = create_test_admin(account=account)
    template = create_test_template(owner, is_active=True, tasks_count=1)
    template_task_1 = template.tasks.get(number=1)
    template_task_1.raw_performers.all().delete()
    template_task_1.add_raw_performer(user)
    send_new_task_notification_mock = mocker.patch(
        'src.notifications.tasks'
        '.send_new_task_notification.delay',
    )
    analytics_mock = mocker.patch(
        'src.analytics.services.AnalyticService.'
        'workflows_started',
    )
    analytics_urgent_mock = mocker.patch(
        'src.analytics.services.AnalyticService.'
        'workflows_urgent',
    )
    mocker.patch(
        'src.processes.services.workflow_action.'
        'WorkflowEventService.workflow_run_event',
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.post(
        path=f'/templates/{template.id}/run',
        data={'is_urgent': True},
    )

    # assert
    assert response.status_code == 200
    workflow = Workflow.objects.get(id=response.data['id'])
    assert workflow.is_urgent is True
    task = workflow.tasks.get(number=1)
    assert task.is_urgent is True
    analytics_mock.assert_called_once_with(
        workflow=workflow,
        auth_type=AuthTokenType.USER,
        is_superuser=False,
        user=owner,
    )
    analytics_urgent_mock.assert_called_once_with(
        workflow=workflow,
        auth_type=AuthTokenType.USER,
        is_superuser=False,
        user=owner,
        action=WorkflowActions.marked,
    )
    send_new_task_notification_mock.assert_called_once()


@pytest.mark.parametrize('value', ('', None, [], 'undefined'))
def test_run__invalid_is_urgent__validation_error(
    value,
    mocker,
    api_client,
):

    # arrange
    send_new_task_notification_mock = mocker.patch(
        'src.notifications.tasks'
        '.send_new_task_notification.delay',
    )
    mocker.patch(
        'src.processes.services.workflow_action.'
        'send_new_task_notification.delay',
    )
    mocker.patch(
        'src.processes.services.workflow_action.'
        'WorkflowEventService.workflow_run_event',
    )
    user = create_test_user()
    api_client.token_authenticate(user)
    template = create_test_template(
        user=user,
        is_active=True,
        tasks_count=1,
    )
    # act
    response = api_client.post(
        path=f'/templates/{template.id}/run',
        data={'is_urgent': value},
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    send_new_task_notification_mock.assert_not_called()


def test_run__skip_task_no_performers__ok(
    mocker,
    api_client,
):
    # arrange
    user = create_test_user()
    api_client.token_authenticate(user=user)

    mocker.patch(
        'src.notifications.tasks'
        '.send_new_task_notification.delay',
    )
    mocker.patch(
        'src.processes.services.workflow_action.'
        'send_new_task_notification.delay',
    )
    mocker.patch(
        'src.processes.services.workflow_action.'
        'WorkflowEventService.workflow_run_event',
    )
    template = create_test_template(
        user=user,
        is_active=True,
    )
    # Create condition for skipping first task
    kickoff_field_template = FieldTemplate.objects.create(
        type=FieldType.TEXT,
        name='Skip first task',
        kickoff=template.kickoff_instance,
        template=template,
    )
    task_template_1 = template.tasks.get(number=1)
    condition_template = ConditionTemplate.objects.create(
        task=task_template_1,
        action=ConditionAction.SKIP_TASK,
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
        field_type=FieldType.TEXT,
        field=kickoff_field_template.api_name,
        template=template,
        value='skip',
    )

    # Create user-field for first task
    user_field_template = FieldTemplate.objects.create(
        type=FieldType.USER,
        name='Second task performer',
        description='Last description',
        task=task_template_1,
        template=template,
    )

    # Set performer from first task field for second task
    task_template_2 = template.tasks.get(number=2)
    task_template_2.delete_raw_performers()
    task_template_2.add_raw_performer(
        field=user_field_template,
        performer_type=PerformerType.FIELD,
    )

    # act
    response = api_client.post(
        f'/templates/{template.id}/run',
        data={
            'name': 'Workflow',
            'kickoff': {
                kickoff_field_template.api_name: 'skip',
            },
        },
    )

    # assert
    workflow = Workflow.objects.get(id=response.data['id'])
    task_1 = workflow.tasks.get(number=1)
    task_2 = workflow.tasks.get(number=2)
    task_3 = workflow.tasks.get(number=3)
    assert response.status_code == 200
    assert task_1.is_skipped
    assert task_2.is_skipped
    assert task_3.status == TaskStatus.ACTIVE
    assert WorkflowEvent.objects.filter(
        workflow=workflow,
        account=user.account,
        type=WorkflowEventType.TASK_SKIP,
        task_json=TaskEventJsonSerializer(
            instance=task_1,
            context={
                'event_type': WorkflowEventType.TASK_SKIP,
            },
        ).data,

    ).count() == 1
    assert WorkflowEvent.objects.filter(
        workflow=workflow,
        account=user.account,
        type=WorkflowEventType.TASK_START,
        task_json=TaskEventJsonSerializer(
            instance=task_2,
            context={
                'event_type': WorkflowEventType.TASK_START,
            },
        ).data,
    ).count() == 0
    assert WorkflowEvent.objects.filter(
        workflow=workflow,
        account=user.account,
        type=WorkflowEventType.TASK_SKIP_NO_PERFORMERS,
        task_json=TaskEventJsonSerializer(
            instance=task_2,
            context={
                'event_type': WorkflowEventType.TASK_SKIP_NO_PERFORMERS,
            },
        ).data,
    ).count() == 1
    assert WorkflowEvent.objects.filter(
        workflow=workflow,
        account=user.account,
        type=WorkflowEventType.TASK_START,
        task_json=TaskEventJsonSerializer(
            instance=task_3,
            context={
                'event_type': WorkflowEventType.TASK_SKIP_NO_PERFORMERS,
            },
        ).data,
    ).count() == 1


def test_run__user_field_invited_transfer__ok(
    mocker,
    api_client,
):

    # arrange
    mocker.patch(
        'src.processes.services.workflow_action.'
        'WorkflowEventService.workflow_run_event',
    )
    account_1 = create_test_account(name='transfer from')
    account_2 = create_test_account(name='transfer to')
    user_to_transfer = create_test_user(
        account=account_1,
        email='trnsfer@test.test',
        is_account_owner=False,
    )
    account_2_owner = create_test_user(
        account=account_2,
        is_account_owner=True,
    )
    current_url = 'some_url'
    service = UserInviteService(
        request_user=account_2_owner,
        current_url=current_url,
    )
    service.invite_user(
        email=user_to_transfer.email,
        invited_from=SourceType.EMAIL,
    )
    account_2_new_user = account_2.users.get(email=user_to_transfer.email)
    api_client.token_authenticate(account_2_owner)

    # act
    response_template = api_client.post(
        path='/templates',
        data={
            'name': 'Template',
            'is_active': True,
            'owners': [
                {
                    'type': OwnerType.USER,
                    'source_id': account_2_owner.id,
                },
                {
                    'type': OwnerType.USER,
                    'source_id': account_2_new_user.id,
                },
            ],
            'kickoff': {
                'fields': [
                    {
                        'type': FieldType.USER,
                        'order': 1,
                        'name': 'First task performer',
                        'is_required': True,
                        'api_name': 'user-field-1',
                    },
                ],
            },
            'tasks': [
                {
                    'number': 1,
                    'name': 'First step',
                    'raw_performers': [
                        {
                            'type': PerformerType.FIELD,
                            'source_id': 'user-field-1',
                        },
                    ],
                },
            ],
        },
    )
    template_id = response_template.data['id']

    # act
    response = api_client.post(
        path=f'/templates/{template_id}/run',
        data={
            'name': 'Wf',
            'kickoff': {
                'user-field-1': str(account_2_new_user.id),
            },
        },
    )

    # assert
    assert response_template.status_code == 200
    assert response.status_code == 200
    workflow = Workflow.objects.get(id=response.data['id'])
    task = workflow.tasks.get(number=1)
    assert TaskPerformer.objects.filter(
        user_id=account_2_new_user.id,
        task_id=task.id,
    ).exclude_directly_deleted().exists()


def test_run__not_admin__ok(
    mocker,
    api_client,
):

    # arrange

    mocker.patch(
        'src.processes.services.workflow_action.'
        'WorkflowEventService.workflow_run_event',
    )
    account = create_test_account()
    owner = create_test_user(
        email='owner@test.test',
        account=account,
        is_account_owner=True,
    )
    not_admin = create_test_user(
        account=account,
        is_account_owner=False,
        is_admin=False,
    )
    template = create_test_template(
        user=owner,
        is_active=True,
        tasks_count=1,
    )
    TemplateOwner.objects.create(
        template=template,
        account=account,
        type=OwnerType.USER,
        user_id=not_admin.id,
    )
    api_client.token_authenticate(not_admin)

    # act
    response = api_client.post(
        path=f'/templates/{template.id}/run',
        data={'name': 'Test name'},
    )

    # assert
    assert response.status_code == 200
    workflow = Workflow.objects.get(id=response.data['id'])
    assert workflow.workflow_starter.id == not_admin.id


def test_run__api_request__ok(mocker, api_client):

    # arrange
    mocker.patch(
        'src.processes.services.workflow_action.'
        'WorkflowEventService.workflow_run_event',
    )
    account = create_test_account()
    owner = create_test_owner(account=account)
    user = create_test_admin(account=account)
    template = create_test_template(owner, is_active=True, tasks_count=1)
    template_task_1 = template.tasks.get(number=1)
    template_task_1.raw_performers.all().delete()
    template_task_1.add_raw_performer(user)

    send_new_task_notification_mock = mocker.patch(
        'src.notifications.tasks'
        '.send_new_task_notification.delay',
    )
    user_agent = 'Mozilla'
    get_user_agent_mock = mocker.patch(
        'src.processes.views.template.get_user_agent',
        return_value=user_agent,
    )
    service_init_mock = mocker.patch.object(
        TemplateIntegrationsService,
        attribute='__init__',
        return_value=None,
    )
    api_request_mock = mocker.patch(
        'src.processes.services.templates.'
        'integrations.TemplateIntegrationsService.api_request',
    )
    analytics_mock = mocker.patch(
        'src.analytics.services.AnalyticService.'
        'workflows_started',
    )
    task_data_mock = mocker.Mock()
    mocker.patch(
        'src.processes.models.workflows.task.Task.'
        'get_data_for_list',
        return_value=task_data_mock,
    )
    api_client.token_authenticate(
        user=owner,
        token_type=AuthTokenType.API,
    )

    # act
    response = api_client.post(
        path=f'/templates/{template.id}/run',
        data={'name': 'Test name'},
    )

    # assert
    assert response.status_code == 200
    workflow = Workflow.objects.get(id=response.data['id'])
    task = workflow.tasks.get(number=1)
    send_new_task_notification_mock.assert_called_once_with(
        logging=account.log_api_requests,
        account_id=account.id,
        recipients=[(
            user.id,
            user.email,
            user.is_new_tasks_subscriber,
        )],
        task_id=task.id,
        task_name=task.name,
        task_description=task.description,
        workflow_name=workflow.name,
        template_name=workflow.get_template_name(),
        workflow_starter_name=owner.name,
        workflow_starter_photo=owner.photo,
        due_date_timestamp=None,
        logo_lg=account.logo_lg,
        is_returned=False,
        task_data=task_data_mock,
    )
    get_user_agent_mock.assert_called_once()
    api_request_mock.assert_called_once_with(
        template=template,
        user_agent=user_agent,
    )
    workflow = Workflow.objects.get(id=response.data['id'])
    analytics_mock.assert_called_once_with(
        workflow=workflow,
        auth_type=AuthTokenType.API,
        is_superuser=False,
        user=owner,
    )
    service_init_mock.assert_called_once_with(
        account=user.account,
        is_superuser=False,
        user=owner,
    )


def test_run__due_date_more_than_current__ok(api_client, mocker):

    # arrange
    mocker.patch(
        'src.analytics.services.AnalyticService.'
        'workflows_started',
    )
    mocker.patch(
        'src.processes.services.workflow_action.'
        'WorkflowEventService.workflow_run_event',
    )
    user = create_test_user()
    api_client.token_authenticate(user)
    template = create_test_template(
        user=user,
        is_active=True,
    )
    due_date = timezone.now() + timedelta(days=1)

    # act
    response = api_client.post(
        path=f'/templates/{template.id}/run',
        data={
            'name': 'Test name',
            'due_date_tsp': due_date.timestamp(),
        },
    )

    # assert
    assert response.status_code == 200
    assert response.data['due_date_tsp'] == due_date.timestamp()
    workflow = Workflow.objects.get(id=response.data['id'])
    assert workflow.due_date == due_date


def test_run__due_date__is_null__remove_due_date(api_client, mocker):

    # arrange
    mocker.patch(
        'src.analytics.services.AnalyticService.'
        'workflows_started',
    )
    mocker.patch(
        'src.processes.services.workflow_action.'
        'WorkflowEventService.workflow_run_event',
    )
    user = create_test_user()
    api_client.token_authenticate(user)
    template = create_test_template(
        user=user,
        is_active=True,
    )

    # act
    response = api_client.post(
        path=f'/templates/{template.id}/run',
        data={
            'name': 'Test name',
            'due_date_tsp': None,
        },
    )

    # assert
    assert response.status_code == 200
    workflow = Workflow.objects.get(id=response.data['id'])
    assert workflow.due_date is None


def test_run__due_date_less_then_current__validation_error(
    mocker,
    api_client,
):

    # arrange
    send_new_task_notification_ws_mock = mocker.patch(
        'src.notifications.tasks'
        '.send_new_task_notification.delay',
    )
    send_new_task_notification_mock = mocker.patch(
        'src.processes.services.workflow_action.'
        'send_new_task_notification.delay',
    )
    mocker.patch(
        'src.processes.services.workflow_action.'
        'WorkflowEventService.workflow_run_event',
    )
    user = create_test_user()
    api_client.token_authenticate(user)
    template = create_test_template(
        user=user,
        is_active=True,
        tasks_count=1,
    )
    due_date = timezone.now() - timedelta(hours=1)

    # act
    response = api_client.post(
        path=f'/templates/{template.id}/run',
        data={
            'due_date_tsp': due_date.timestamp(),
        },
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == messages.MSG_PW_0051
    assert response.data['details']['name'] == 'due_date_tsp'
    assert response.data['details']['reason'] == messages.MSG_PW_0051
    send_new_task_notification_ws_mock.assert_not_called()
    send_new_task_notification_mock.assert_not_called()


def test_run__due_date_tsp_less_than_current__validation_error(
    api_client,
    mocker,
):

    # arrange
    send_new_task_notification_ws_mock = mocker.patch(
        'src.notifications.tasks'
        '.send_new_task_notification.delay',
    )
    send_new_task_notification_mock = mocker.patch(
        'src.processes.services.workflow_action.'
        'send_new_task_notification.delay',
    )
    mocker.patch(
        'src.processes.services.workflow_action.'
        'WorkflowEventService.workflow_run_event',
    )
    user = create_test_user()
    api_client.token_authenticate(user)
    template = create_test_template(
        user=user,
        is_active=True,
    )
    due_date = timezone.now() - timedelta(days=1)
    due_date_tsp = due_date.timestamp()

    # act
    response = api_client.post(
        path=f'/templates/{template.id}/run',
        data={
            'name': 'Test name',
            'due_date_tsp': due_date_tsp,
        },
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == messages.MSG_PW_0051
    assert response.data['details']['name'] == 'due_date_tsp'
    assert response.data['details']['reason'] == messages.MSG_PW_0051
    send_new_task_notification_ws_mock.assert_not_called()
    send_new_task_notification_mock.assert_not_called()


def test_run__due_date_tsp_invalid_type__validation_error(
    api_client,
    mocker,
):

    # arrange
    send_new_task_notification_ws_mock = mocker.patch(
        'src.notifications.tasks'
        '.send_new_task_notification.delay',
    )
    send_new_task_notification_mock = mocker.patch(
        'src.processes.services.workflow_action.'
        'send_new_task_notification.delay',
    )
    mocker.patch(
        'src.processes.services.workflow_action.'
        'WorkflowEventService.workflow_run_event',
    )
    user = create_test_user()
    api_client.token_authenticate(user)
    template = create_test_template(
        user=user,
        is_active=True,
    )
    due_date = timezone.now() + timedelta(days=1)
    due_date_str = due_date.strftime(format=date_format)

    # act
    response = api_client.post(
        path=f'/templates/{template.id}/run',
        data={
            'name': 'Test name',
            'due_date_tsp': due_date_str,
        },
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == MSG_GE_0007
    assert response.data['details']['name'] == 'due_date_tsp'
    assert response.data['details']['reason'] == MSG_GE_0007
    send_new_task_notification_ws_mock.assert_not_called()
    send_new_task_notification_mock.assert_not_called()


@pytest.mark.parametrize('is_admin', (True, False))
def test_run__not_template_owner__permission_denied(
    mocker,
    is_admin,
    api_client,
):

    # arrange
    mocker.patch(
        'src.processes.services.workflow_action.'
        'WorkflowEventService.workflow_run_event',
    )
    account = create_test_account()
    owner = create_test_user(
        email='owner@test.test',
        account=account,
        is_account_owner=True,
    )
    template = create_test_template(
        user=owner,
        is_active=True,
        tasks_count=1,
    )
    user = create_test_user(
        account=account,
        is_account_owner=False,
        is_admin=is_admin,
    )

    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        path=f'/templates/{template.id}/run',
        data={'name': 'Test name'},
    )

    # assert
    assert response.status_code == 403


def test_run__task_name_with_field__ok(mocker, api_client):

    # arrange
    mocker.patch(
        'src.notifications.tasks'
        '.send_new_task_notification.delay',
    )
    mocker.patch(
        'src.processes.services.workflow_action.'
        'WorkflowEventService.workflow_run_event',
    )
    user = create_test_user()
    api_client.token_authenticate(user)

    # act
    response_create = api_client.post(
        path='/templates',
        data={
            'name': 'Template',
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
                        'order': 1,
                        'name': 'String field',
                        'type': FieldType.STRING,
                        'is_required': True,
                        'api_name': 'string-field-1',
                    },
                    {
                        'order': 2,
                        'name': 'String field 2',
                        'type': FieldType.STRING,
                        'is_required': True,
                        'api_name': 'string-field-2',
                    },
                ],
            },
            'tasks': [
                {
                    'number': 1,
                    'name': 'Text {{string-field-1}} - {{string-field-2}}',
                    'api_name': 'task-1',
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
    template_id = response_create.data['id']

    mocker.patch(
        'src.analytics.services.AnalyticService.'
        'workflows_started',
    )
    mocker.patch(
        'src.processes.services.templates.'
        'integrations.TemplateIntegrationsService.api_request',
    )
    value_1 = 'First name'
    value_2 = 'Last'

    # act
    response = api_client.post(
        path=f'/templates/{template_id}/run',
        data={
            'kickoff': {
                'string-field-1': value_1,
                'string-field-2': value_2,
            },
        },
    )

    # assert
    assert response_create.status_code == 200
    assert response.status_code == 200
    workflow = Workflow.objects.get(id=response.data['id'])
    task = workflow.tasks.get(number=1)
    assert task.name == f'Text {value_1} - {value_2}'


def test_run__task_name_with_kickoff_data_value_int__ok(mocker, api_client):

    # arrange
    mocker.patch(
        'src.notifications.tasks'
        '.send_new_task_notification.delay',
    )
    mocker.patch(
        'src.processes.services.workflow_action.'
        'WorkflowEventService.workflow_run_event',
    )
    user = create_test_user()
    api_client.token_authenticate(user)
    api_name = 'date-field-1'
    kickoff_data = 1726012800
    task_name = '{{%s}} - test name' % api_name

    # act
    response_create = api_client.post(
        path='/templates',
        data={
            'name': 'Template',
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
                        'order': 1,
                        'name': 'Date field',
                        'type': FieldType.DATE,
                        'is_required': False,
                        'api_name': api_name,
                    },
                ],
            },
            'tasks': [
                {
                    'number': 1,
                    'name': task_name,
                    'api_name': 'task-1',
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
    template = Template.objects.get(id=response_create.data['id'])

    mocker.patch(
        'src.analytics.services.AnalyticService.'
        'workflows_started',
    )
    mocker.patch(
        'src.processes.services.templates.'
        'integrations.TemplateIntegrationsService.api_request',
    )

    # act
    response = api_client.post(
        path=f'/templates/{template.id}/run',
        data={
            'kickoff': {
                api_name: kickoff_data,
            },
        },
    )

    # assert
    assert response_create.status_code == 200
    assert response.status_code == 200
    assert response.data['kickoff']['output'][0]['value'] == str(kickoff_data)
    workflow = Workflow.objects.get(id=response.data['id'])
    task = workflow.tasks.get(number=1)
    assert task.name == 'Sep 11, 2024, 12:00AM - test name'


def test_run__task_name_with_kickoff_data_value_float__ok(mocker, api_client):

    # arrange
    mocker.patch(
        'src.notifications.tasks'
        '.send_new_task_notification.delay',
    )
    mocker.patch(
        'src.processes.services.workflow_action.'
        'WorkflowEventService.workflow_run_event',
    )
    user = create_test_user()
    api_client.token_authenticate(user)
    api_name = 'date-field-1'
    kickoff_data = 1726012800.21
    task_name = '{{%s}} - test name' % api_name

    # act
    response_create = api_client.post(
        path='/templates',
        data={
            'name': 'Template',
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
                        'order': 1,
                        'name': 'Date field',
                        'type': FieldType.DATE,
                        'is_required': False,
                        'api_name': api_name,
                    },
                ],
            },
            'tasks': [
                {
                    'number': 1,
                    'name': task_name,
                    'api_name': 'task-1',
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
    template = Template.objects.get(id=response_create.data['id'])

    mocker.patch(
        'src.analytics.services.AnalyticService.'
        'workflows_started',
    )
    mocker.patch(
        'src.processes.services.templates.'
        'integrations.TemplateIntegrationsService.api_request',
    )

    # act
    response = api_client.post(
        path=f'/templates/{template.id}/run',
        data={
            'kickoff': {
                api_name: kickoff_data,
            },
        },
    )

    # assert
    assert response_create.status_code == 200
    assert response.status_code == 200
    assert response.data['kickoff']['output'][0]['value'] == str(kickoff_data)
    workflow = Workflow.objects.get(id=response.data['id'])
    task = workflow.tasks.get(number=1)
    assert task.name == 'Sep 11, 2024, 12:00AM - test name'


@pytest.mark.parametrize('kickoff_data', (' ', '136166546'))
def test_run__task_name_with_invalid_kickoff_data_value__validation_error(
    mocker, api_client, kickoff_data,
):

    # arrange
    mocker.patch(
        'src.notifications.tasks'
        '.send_new_task_notification.delay',
    )
    mocker.patch(
        'src.processes.services.workflow_action.'
        'WorkflowEventService.workflow_run_event',
    )
    user = create_test_user()
    api_client.token_authenticate(user)
    api_name = 'date-field-1'
    task_name = '{{%s}} - test name' % api_name

    # act
    response_create = api_client.post(
        path='/templates',
        data={
            'name': 'Template',
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
                        'order': 1,
                        'name': 'Date field',
                        'type': FieldType.DATE,
                        'is_required': False,
                        'api_name': api_name,
                    },
                ],
            },
            'tasks': [
                {
                    'number': 1,
                    'name': task_name,
                    'api_name': 'task-1',
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
    template = Template.objects.get(id=response_create.data['id'])

    mocker.patch(
        'src.analytics.services.AnalyticService.'
        'workflows_started',
    )
    mocker.patch(
        'src.processes.services.templates.'
        'integrations.TemplateIntegrationsService.api_request',
    )

    # act
    response = api_client.post(
        path=f'/templates/{template.id}/run',
        data={
            'kickoff': {
                api_name: kickoff_data,
            },
        },
    )

    # assert
    assert response_create.status_code == 200
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == messages.MSG_PW_0032
    assert response.data['details']['reason'] == messages.MSG_PW_0032
    assert response.data['details']['api_name'] == api_name


def test_run__task_name_with_field_2__ok(mocker, api_client):

    # arrange
    mocker.patch(
        'src.notifications.tasks'
        '.send_new_task_notification.delay',
    )
    mocker.patch(
        'src.processes.services.workflow_action.'
        'WorkflowEventService.workflow_run_event',
    )
    user = create_test_user()
    api_client.token_authenticate(user)
    api_name_1 = 'checkbox-field-1'
    api_name_2 = 'date-field-2'
    api_name_3 = 'user-field-3'

    task_name = '{{%s}}:{{%s}} [{{%s}}]' % (api_name_1, api_name_2, api_name_3)

    # act
    response_create = api_client.post(
        path='/templates',
        data={
            'name': 'Template',
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
                        'order': 1,
                        'name': 'Checkbox field',
                        'type': FieldType.CHECKBOX,
                        'is_required': True,
                        'api_name': api_name_1,
                        'selections': [
                            {
                                'api_name': 'selection-1',
                                'value': 'Frontend',
                            },
                            {
                                'api_name': 'selection-2',
                                'value': 'Fast track',
                            },
                        ],
                    },
                    {
                        'order': 2,
                        'name': 'Date field',
                        'type': FieldType.DATE,
                        'is_required': False,
                        'api_name': api_name_2,
                    },
                    {
                        'order': 3,
                        'name': 'User field',
                        'type': FieldType.USER,
                        'is_required': True,
                        'api_name': api_name_3,
                    },
                ],
            },
            'tasks': [
                {
                    'number': 1,
                    'name': task_name,
                    'api_name': 'task-1',
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
    template = Template.objects.get(id=response_create.data['id'])
    selection_1 = template.kickoff_instance.fields.get(
        api_name=api_name_1,
    ).selections.get(api_name='selection-1')
    selection_2 = template.kickoff_instance.fields.get(
        api_name=api_name_1,
    ).selections.get(api_name='selection-2')

    mocker.patch(
        'src.analytics.services.AnalyticService.'
        'workflows_started',
    )
    mocker.patch(
        'src.processes.services.templates.'
        'integrations.TemplateIntegrationsService.api_request',
    )

    # act
    response = api_client.post(
        path=f'/templates/{template.id}/run',
        data={
            'kickoff': {
                api_name_1: [
                    str(selection_1.api_name),
                    str(selection_2.api_name),
                ],
                api_name_2: 1726012800,
                api_name_3: str(user.id),
            },
        },
    )

    # assert
    assert response_create.status_code == 200
    assert response.status_code == 200
    workflow = Workflow.objects.get(id=response.data['id'])
    task = workflow.tasks.get(number=1)
    assert task.name == (
        f'Frontend, Fast track:Sep 11, 2024, 12:00AM [{user.name}]'
    )


def test_run__wf_name_template_with_system_vars__only__ok(
    mocker,
    api_client,
):

    # arrange
    mocker.patch(
        'src.notifications.tasks'
        '.send_new_task_notification.delay',
    )
    mocker.patch(
        'src.analytics.services.AnalyticService.'
        'workflows_started',
    )
    mocker.patch(
        'src.processes.services.workflow_action.'
        'WorkflowEventService.workflow_run_event',
    )
    user = create_test_user()
    api_client.token_authenticate(user)
    template_name = 'New'
    wf_name_template = '{{ template-name }} {{ date }}'
    template = create_test_template(
        user=user,
        is_active=True,
        tasks_count=1,
        name=template_name,
        wf_name_template=wf_name_template,
    )
    date = timezone.datetime(
        year=2024,
        month=8,
        day=28,
        hour=10,
        minute=41,
        tzinfo=pytz.timezone('UTC'),
    )
    mocker.patch('django.utils.timezone.now', return_value=date)

    # act
    response = api_client.post(
        path=f'/templates/{template.id}/run',
    )

    # assert
    assert response.status_code == 200
    workflow = Workflow.objects.get(id=response.data['id'])
    formatted_date = 'Aug 28, 2024, 10:41AM'
    assert workflow.name == f'{template_name} {formatted_date}'
    assert workflow.name_template == f'{template_name} {formatted_date}'


def test_run__wf_name_template_with_system_and_kickoff_vars__ok(
    mocker,
    api_client,
):

    # arrange
    mocker.patch(
        'src.notifications.tasks'
        '.send_new_task_notification.delay',
    )
    mocker.patch(
        'src.analytics.services.AnalyticService.'
        'workflows_started',
    )
    mocker.patch(
        'src.processes.services.workflow_action.'
        'WorkflowEventService.workflow_run_event',
    )
    user = create_test_user()
    api_client.token_authenticate(user)
    template = create_test_template(
        user=user,
        is_active=True,
        tasks_count=1,
    )
    field_api_name = 'field-123'
    FieldTemplate.objects.create(
        name='User',
        type=FieldType.USER,
        is_required=True,
        kickoff=template.kickoff_instance,
        template=template,
        api_name=field_api_name,
    )
    wf_name_template = 'Feedback from {{%s}} {{ date }}' % field_api_name
    template.wf_name_template = wf_name_template
    template.save()

    date = timezone.datetime(
        year=2024,
        month=8,
        day=28,
        hour=10,
        minute=41,
        tzinfo=pytz.timezone('UTC'),
    )
    mocker.patch('django.utils.timezone.now', return_value=date)

    # act
    response = api_client.post(
        path=f'/templates/{template.id}/run',
        data={
            'kickoff': {
                field_api_name: str(user.id),
            },
        },
    )

    # assert
    assert response.status_code == 200
    workflow = Workflow.objects.get(id=response.data['id'])
    formatted_date = 'Aug 28, 2024, 10:41AM'
    assert workflow.name == f'Feedback from {user.name} {formatted_date}'
    assert workflow.name_template == (
        'Feedback from {{%s}} %s'
    ) % (field_api_name, formatted_date)


def test_run__name_with_kickoff_vars_only__ok(
    mocker,
    api_client,
):

    # arrange
    mocker.patch(
        'src.notifications.tasks'
        '.send_new_task_notification.delay',
    )
    mocker.patch(
        'src.analytics.services.AnalyticService.'
        'workflows_started',
    )
    mocker.patch(
        'src.processes.services.workflow_action.'
        'WorkflowEventService.workflow_run_event',
    )
    user = create_test_user()
    api_client.token_authenticate(user)
    template = create_test_template(
        user=user,
        is_active=True,
        tasks_count=1,
    )
    field_api_name_1 = 'field-1'
    field_api_name_2 = 'field-2'
    field_api_name_3 = 'field-3'
    FieldTemplate.objects.create(
        name='Text',
        type=FieldType.TEXT,
        is_required=True,
        kickoff=template.kickoff_instance,
        template=template,
        api_name=field_api_name_1,
    )
    FieldTemplate.objects.create(
        name='User',
        type=FieldType.USER,
        is_required=True,
        kickoff=template.kickoff_instance,
        template=template,
        api_name=field_api_name_2,
    )
    FieldTemplate.objects.create(
        name='Url',
        type=FieldType.URL,
        is_required=False,
        kickoff=template.kickoff_instance,
        template=template,
        api_name=field_api_name_3,
    )
    wf_name_template = 'Feedback: {{%s}} from {{ %s }} Url: {{%s}}' % (
        field_api_name_1,
        field_api_name_2,
        field_api_name_3,
    )
    template.wf_name_template = wf_name_template
    template.save()

    feedback = 'Some shit!'

    # act
    response = api_client.post(
        path=f'/templates/{template.id}/run',
        data={
            'kickoff': {
                field_api_name_1: feedback,
                field_api_name_2: str(user.id),
            },
        },
    )

    # assert
    assert response.status_code == 200
    workflow = Workflow.objects.get(id=response.data['id'])
    assert workflow.name == f'Feedback: {feedback} from {user.name} Url: '
    assert workflow.name_template == wf_name_template


def test_run__string_abbreviation_after_insert_fields_vars__ok(
    mocker,
    api_client,
):

    # arrange
    mocker.patch(
        'src.notifications.tasks'
        '.send_new_task_notification.delay',
    )
    mocker.patch(
        'src.analytics.services.AnalyticService.'
        'workflows_started',
    )
    mocker.patch(
        'src.processes.services.workflow_action.'
        'WorkflowEventService.workflow_run_event',
    )
    user = create_test_user()
    api_client.token_authenticate(user)
    template = create_test_template(
        user=user,
        is_active=True,
        tasks_count=1,
    )
    field_api_name = 'field-1'
    FieldTemplate.objects.create(
        name='Text',
        type=FieldType.TEXT,
        is_required=True,
        kickoff=template.kickoff_instance,
        template=template,
        api_name=field_api_name,
    )
    wf_name_template = 'a' * (WORKFLOW_NAME_LENGTH - 4)
    wf_name_template += '{{%s}}' % field_api_name
    template.wf_name_template = wf_name_template
    template.save()

    # act
    response = api_client.post(
        path=f'/templates/{template.id}/run',
        data={
            'kickoff': {
                field_api_name:  'Some shit!',
            },
        },
    )

    # assert
    assert response.status_code == 200
    name = (
        'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
        'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaSom…'
    )
    assert response.data['name'] == name
    workflow = Workflow.objects.get(id=response.data['id'])
    assert workflow.name == name
    assert workflow.name_template == wf_name_template


def test_run__user_provided_name__ok(
    mocker,
    api_client,
):

    # arrange
    mocker.patch(
        'src.notifications.tasks'
        '.send_new_task_notification.delay',
    )
    mocker.patch(
        'src.analytics.services.AnalyticService.'
        'workflows_started',
    )
    mocker.patch(
        'src.processes.services.workflow_action.'
        'WorkflowEventService.workflow_run_event',
    )
    user = create_test_user()
    api_client.token_authenticate(user)
    template = create_test_template(
        user=user,
        is_active=True,
        tasks_count=1,
        wf_name_template='',
    )
    field_api_name = 'field-1'
    FieldTemplate.objects.create(
        name='Text',
        type=FieldType.TEXT,
        is_required=True,
        kickoff=template.kickoff_instance,
        template=template,
        api_name=field_api_name,
    )
    user_provided_wf_name = 'User provided workflow name'

    # act
    response = api_client.post(
        path=f'/templates/{template.id}/run',
        data={
            'name': user_provided_wf_name,
            'kickoff': {
                field_api_name: 'Some shit!',
            },
        },
    )

    # assert
    assert response.status_code == 200
    workflow = Workflow.objects.get(id=response.data['id'])
    assert workflow.name == user_provided_wf_name
    assert workflow.name_template == user_provided_wf_name


def test_run__workflow_name_is_null__use_template_name(
    mocker,
    api_client,
):

    # arrange
    mocker.patch(
        'src.notifications.tasks'
        '.send_new_task_notification.delay',
    )
    mocker.patch(
        'src.analytics.services.AnalyticService.'
        'workflows_started',
    )
    mocker.patch(
        'src.processes.services.workflow_action.'
        'WorkflowEventService.workflow_run_event',
    )
    user = create_test_user()
    api_client.token_authenticate(user)
    template_name = 'Template name'
    template = create_test_template(
        name=template_name,
        user=user,
        is_active=True,
        tasks_count=1,
    )
    wf_name_template = 'Feedback: {{ template-name }}'
    template.wf_name_template = wf_name_template
    template.save()

    # act
    response = api_client.post(
        path=f'/templates/{template.id}/run',
        data={
            'name': None,
        },
    )

    # assert
    assert response.status_code == 200
    workflow = Workflow.objects.get(id=response.data['id'])
    assert workflow.name == f'Feedback: {template_name}'
    assert workflow.name_template == f'Feedback: {template_name}'


def test_run__ancestor_task_id__ok(mocker, api_client):

    # arrange
    mocker.patch(
        'src.notifications.tasks'
        '.send_new_task_notification.delay',
    )
    mocker.patch(
        'src.analytics.services.AnalyticService.'
        'workflows_started',
    )
    mocker.patch(
        'src.processes.services.templates.'
        'integrations.TemplateIntegrationsService.api_request',
    )
    workflow_run_event_mock = mocker.patch(
        'src.processes.services.workflow_action.'
        'WorkflowEventService.workflow_run_event',
    )
    sub_workflow_run_event_mock = mocker.patch(
        'src.processes.services.workflow_action.'
        'WorkflowEventService.sub_workflow_run_event',
    )
    user = create_test_user()
    template = create_test_template(
        user=user,
        is_active=True,
        tasks_count=1,
    )
    parent_workflow = create_test_workflow(
        user=user,
        tasks_count=1,
    )
    ancestor_task = parent_workflow.tasks.get(number=1)
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        path=f'/templates/{template.id}/run',
        data={
            'name': 'Test name',
            'ancestor_task_id': ancestor_task.id,
        },
    )

    # assert
    assert response.status_code == 200
    workflow = Workflow.objects.get(id=response.data['id'])
    assert workflow.ancestor_task_id == ancestor_task.id
    workflow_run_event_mock.assert_called_once_with(
        workflow=workflow,
        user=user,
    )
    sub_workflow_run_event_mock.assert_called_once_with(
        workflow=parent_workflow,
        sub_workflow=workflow,
        user=user,
    )


def test_run__ancestor_task_id_user_in_group__ok(mocker, api_client):

    # arrange
    mocker.patch(
        'src.notifications.tasks'
        '.send_new_task_notification.delay',
    )
    mocker.patch(
        'src.analytics.services.AnalyticService.'
        'workflows_started',
    )
    mocker.patch(
        'src.processes.services.templates.'
        'integrations.TemplateIntegrationsService.api_request',
    )
    workflow_run_event_mock = mocker.patch(
        'src.processes.services.workflow_action.'
        'WorkflowEventService.workflow_run_event',
    )
    sub_workflow_run_event_mock = mocker.patch(
        'src.processes.services.workflow_action.'
        'WorkflowEventService.sub_workflow_run_event',
    )
    user = create_test_user()
    performer = create_test_user(
        account=user.account,
        email='test@test.test',
        is_account_owner=False,
    )
    group = create_test_group(user.account, users=[performer])
    template = create_test_template(
        user=user,
        is_active=True,
        tasks_count=1,
    )
    TemplateOwner.objects.create(
        template=template,
        account=performer.account,
        type=OwnerType.USER,
        user_id=performer.id,
    )
    parent_workflow = create_test_workflow(
        user=user,
        tasks_count=1,
    )
    ancestor_task = parent_workflow.tasks.get(number=1)
    TaskPerformer.objects.create(
        task_id=ancestor_task.id,
        type=PerformerType.GROUP,
        group_id=group.id,
        directly_status=DirectlyStatus.CREATED,
    )
    api_client.token_authenticate(performer)

    # act
    response = api_client.post(
        path=f'/templates/{template.id}/run',
        data={
            'name': 'Test name',
            'ancestor_task_id': ancestor_task.id,
        },
    )

    # assert
    assert response.status_code == 200
    workflow = Workflow.objects.get(id=response.data['id'])
    assert workflow.ancestor_task_id == ancestor_task.id
    workflow_run_event_mock.assert_called_once_with(
        workflow=workflow,
        user=performer,
    )
    sub_workflow_run_event_mock.assert_called_once_with(
        workflow=parent_workflow,
        sub_workflow=workflow,
        user=performer,
    )


def test_run__ancestor_task__is_null__validation_error(mocker, api_client):

    # arrange
    mocker.patch(
        'src.notifications.tasks'
        '.send_new_task_notification.delay',
    )
    mocker.patch(
        'src.analytics.services.AnalyticService.'
        'workflows_started',
    )
    mocker.patch(
        'src.processes.services.templates.'
        'integrations.TemplateIntegrationsService.api_request',
    )
    workflow_run_event_mock = mocker.patch(
        'src.processes.services.workflow_action.'
        'WorkflowEventService.workflow_run_event',
    )
    sub_workflow_run_event_mock = mocker.patch(
        'src.processes.services.workflow_action.'
        'WorkflowEventService.sub_workflow_run_event',
    )
    user = create_test_user()
    api_client.token_authenticate(user)
    template = create_test_template(
        user=user,
        is_active=True,
        tasks_count=1,
    )

    # act
    response = api_client.post(
        path=f'/templates/{template.id}/run',
        data={
            'name': 'Test name',
            'ancestor_task_id': None,
        },
    )

    # assert
    assert response.status_code == 400
    message = 'This field may not be null.'
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    assert response.data['details']['name'] == 'ancestor_task_id'
    assert response.data['details']['reason'] == message
    workflow_run_event_mock.assert_not_called()
    sub_workflow_run_event_mock.assert_not_called()


def test_run__ancestor_task__is_blank__validation_error(mocker, api_client):

    # arrange
    mocker.patch(
        'src.notifications.tasks'
        '.send_new_task_notification.delay',
    )
    mocker.patch(
        'src.analytics.services.AnalyticService.'
        'workflows_started',
    )
    mocker.patch(
        'src.processes.services.templates.'
        'integrations.TemplateIntegrationsService.api_request',
    )
    workflow_run_event_mock = mocker.patch(
        'src.processes.services.workflow_action.'
        'WorkflowEventService.workflow_run_event',
    )
    sub_workflow_run_event_mock = mocker.patch(
        'src.processes.services.workflow_action.'
        'WorkflowEventService.sub_workflow_run_event',
    )
    user = create_test_user()
    api_client.token_authenticate(user)
    template = create_test_template(
        user=user,
        is_active=True,
        tasks_count=1,
    )

    # act
    response = api_client.post(
        path=f'/templates/{template.id}/run',
        data={
            'name': 'Test name',
            'ancestor_task_id': '',
        },
    )

    # assert
    assert response.status_code == 400
    message = 'This field may not be null.'
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    assert response.data['details']['name'] == 'ancestor_task_id'
    assert response.data['details']['reason'] == message
    workflow_run_event_mock.assert_not_called()
    sub_workflow_run_event_mock.assert_not_called()


def test_run__ancestor_task__invalid__validation_error(mocker, api_client):

    # arrange
    mocker.patch(
        'src.notifications.tasks'
        '.send_new_task_notification.delay',
    )
    mocker.patch(
        'src.analytics.services.AnalyticService.'
        'workflows_started',
    )
    mocker.patch(
        'src.processes.services.templates.'
        'integrations.TemplateIntegrationsService.api_request',
    )
    workflow_run_event_mock = mocker.patch(
        'src.processes.services.workflow_action.'
        'WorkflowEventService.workflow_run_event',
    )
    sub_workflow_run_event_mock = mocker.patch(
        'src.processes.services.workflow_action.'
        'WorkflowEventService.sub_workflow_run_event',
    )
    user = create_test_user()
    api_client.token_authenticate(user)
    template = create_test_template(
        user=user,
        is_active=True,
        tasks_count=1,
    )

    # act
    response = api_client.post(
        path=f'/templates/{template.id}/run',
        data={
            'name': 'Test name',
            'ancestor_task_id': 'Undefined',
        },
    )

    # assert
    assert response.status_code == 400
    message = 'Incorrect type. Expected pk value, received str.'
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    assert response.data['details']['name'] == 'ancestor_task_id'
    assert response.data['details']['reason'] == message
    workflow_run_event_mock.assert_not_called()
    sub_workflow_run_event_mock.assert_not_called()


def test_run__ancestor_task__another_account__validation_error(
    mocker,
    api_client,
):

    # arrange
    mocker.patch(
        'src.notifications.tasks'
        '.send_new_task_notification.delay',
    )
    mocker.patch(
        'src.analytics.services.AnalyticService.'
        'workflows_started',
    )
    mocker.patch(
        'src.processes.services.templates.'
        'integrations.TemplateIntegrationsService.api_request',
    )
    workflow_run_event_mock = mocker.patch(
        'src.processes.services.workflow_action.'
        'WorkflowEventService.workflow_run_event',
    )
    sub_workflow_run_event_mock = mocker.patch(
        'src.processes.services.workflow_action.'
        'WorkflowEventService.sub_workflow_run_event',
    )
    another_account_user = create_test_user(
        email='another@test.test',
    )
    parent_workflow = create_test_workflow(
        user=another_account_user,
        tasks_count=1,
    )
    ancestor_task = parent_workflow.tasks.get(number=1)

    user = create_test_user()
    template = create_test_template(
        user=user,
        is_active=True,
        tasks_count=1,
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        path=f'/templates/{template.id}/run',
        data={
            'name': 'Test name',
            'ancestor_task_id': ancestor_task.id,
        },
    )

    # assert
    assert response.status_code == 400
    message = f'Invalid pk "{ancestor_task.id}" - object does not exist.'
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    assert response.data['details']['name'] == 'ancestor_task_id'
    assert response.data['details']['reason'] == message
    workflow_run_event_mock.assert_not_called()
    sub_workflow_run_event_mock.assert_not_called()


def test_run__ancestor_task__from_snoozed_workflow__validation_error(
    mocker,
    api_client,
):

    # arrange
    mocker.patch(
        'src.notifications.tasks'
        '.send_new_task_notification.delay',
    )
    mocker.patch(
        'src.analytics.services.AnalyticService.'
        'workflows_started',
    )
    mocker.patch(
        'src.processes.services.templates.'
        'integrations.TemplateIntegrationsService.api_request',
    )
    mocker.patch(
        'src.processes.services.workflow_action.'
        'WorkflowEventService.workflow_run_event',
    )
    mocker.patch(
        'src.processes.services.workflow_action.'
        'WorkflowEventService.sub_workflow_run_event',
    )
    account = create_test_account()
    owner = create_test_user(account=account)
    user = create_test_user(
        account=account,
        is_account_owner=False,
        email='user2@test.test',
    )
    parent_workflow = create_test_workflow(
        user=owner,
        tasks_count=1,
        status=WorkflowStatus.DELAYED,
    )
    ancestor_task = parent_workflow.tasks.get(number=1)
    ancestor_task.performers.add(user)
    template = create_test_template(
        user=user,
        is_active=True,
        tasks_count=1,
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        path=f'/templates/{template.id}/run',
        data={
            'name': 'Test name',
            'ancestor_task_id': ancestor_task.id,
        },
    )

    # assert
    assert response.status_code == 400
    message = messages.MSG_PW_0072
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    assert response.data['details']['name'] == 'ancestor_task_id'
    assert response.data['details']['reason'] == message


def test_run__ancestor_task_not_active__validation_error(
    mocker,
    api_client,
):

    # arrange
    mocker.patch(
        'src.notifications.tasks'
        '.send_new_task_notification.delay',
    )
    mocker.patch(
        'src.analytics.services.AnalyticService.'
        'workflows_started',
    )
    mocker.patch(
        'src.processes.services.templates.'
        'integrations.TemplateIntegrationsService.api_request',
    )
    mocker.patch(
        'src.processes.services.workflow_action.'
        'WorkflowEventService.workflow_run_event',
    )
    mocker.patch(
        'src.processes.services.workflow_action.'
        'WorkflowEventService.sub_workflow_run_event',
    )
    account = create_test_account()
    owner = create_test_owner(account=account)
    user = create_test_admin(account=account)
    parent_workflow = create_test_workflow(
        user=owner,
        tasks_count=2,
        active_task_number=2,
    )
    ancestor_task = parent_workflow.tasks.get(number=1)
    ancestor_task.performers.add(user)

    template = create_test_template(
        user=user,
        is_active=True,
        tasks_count=1,
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        path=f'/templates/{template.id}/run',
        data={
            'name': 'Test name',
            'ancestor_task_id': ancestor_task.id,
        },
    )

    # assert
    assert response.status_code == 400
    message = messages.MSG_PW_0074
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    assert response.data['details']['name'] == 'ancestor_task_id'
    assert response.data['details']['reason'] == message


def test_run__not_performer_in_ancestor_task___validation_error(
    mocker,
    api_client,
):

    # arrange
    mocker.patch(
        'src.notifications.tasks'
        '.send_new_task_notification.delay',
    )
    mocker.patch(
        'src.analytics.services.AnalyticService.'
        'workflows_started',
    )
    mocker.patch(
        'src.processes.services.templates.'
        'integrations.TemplateIntegrationsService.api_request',
    )
    mocker.patch(
        'src.processes.services.workflow_action.'
        'WorkflowEventService.workflow_run_event',
    )
    mocker.patch(
        'src.processes.services.workflow_action.'
        'WorkflowEventService.sub_workflow_run_event',
    )
    account = create_test_account()
    owner = create_test_user(account=account)
    user = create_test_user(
        account=account,
        is_account_owner=False,
        email='user2@test.test',
    )
    parent_workflow = create_test_workflow(
        user=owner,
        tasks_count=1,
    )
    ancestor_task = parent_workflow.tasks.get(number=1)

    template = create_test_template(
        user=user,
        is_active=True,
        tasks_count=1,
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        path=f'/templates/{template.id}/run',
        data={
            'name': 'Test name',
            'ancestor_task_id': ancestor_task.id,
        },
    )

    # assert
    assert response.status_code == 400
    message = messages.MSG_PW_0075
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    assert response.data['details']['name'] == 'ancestor_task_id'
    assert response.data['details']['reason'] == message


def test_run__deleted_performer_in_ancestor_task___validation_error(
    mocker,
    api_client,
):

    # arrange
    mocker.patch(
        'src.notifications.tasks'
        '.send_new_task_notification.delay',
    )
    mocker.patch(
        'src.analytics.services.AnalyticService.'
        'workflows_started',
    )
    mocker.patch(
        'src.processes.services.templates.'
        'integrations.TemplateIntegrationsService.api_request',
    )
    mocker.patch(
        'src.processes.services.workflow_action.'
        'WorkflowEventService.workflow_run_event',
    )
    mocker.patch(
        'src.processes.services.workflow_action.'
        'WorkflowEventService.sub_workflow_run_event',
    )
    account = create_test_account()
    create_test_user(account=account)
    user = create_test_user(
        account=account,
        is_account_owner=False,
        email='user2@test.test',
    )
    parent_workflow = create_test_workflow(
        user=user,
        tasks_count=1,
    )
    ancestor_task = parent_workflow.tasks.get(number=1)
    ancestor_task.taskperformer_set.update(
        directly_status=DirectlyStatus.DELETED,
    )

    template = create_test_template(
        user=user,
        is_active=True,
        tasks_count=1,
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        path=f'/templates/{template.id}/run',
        data={
            'name': 'Test name',
            'ancestor_task_id': ancestor_task.id,
        },
    )

    # assert
    assert response.status_code == 400
    message = messages.MSG_PW_0075
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    assert response.data['details']['name'] == 'ancestor_task_id'
    assert response.data['details']['reason'] == message


def test_run__account_owner_not_performer_in_ancestor_task__ok(
    mocker,
    api_client,
):

    # arrange
    mocker.patch(
        'src.notifications.tasks'
        '.send_new_task_notification.delay',
    )
    mocker.patch(
        'src.analytics.services.AnalyticService.'
        'workflows_started',
    )
    mocker.patch(
        'src.processes.services.templates.'
        'integrations.TemplateIntegrationsService.api_request',
    )
    mocker.patch(
        'src.processes.services.workflow_action.'
        'WorkflowEventService.workflow_run_event',
    )
    mocker.patch(
        'src.processes.services.workflow_action.'
        'WorkflowEventService.sub_workflow_run_event',
    )
    account = create_test_account()
    owner = create_test_user(account=account)
    user = create_test_user(
        account=account,
        is_account_owner=False,
        email='user2@test.test',
    )
    parent_workflow = create_test_workflow(
        user=user,
        tasks_count=1,
    )
    ancestor_task = parent_workflow.tasks.get(number=1)
    TaskPerformer.objects.create(
        user_id=owner.id,
        task_id=ancestor_task.id,
        directly_status=DirectlyStatus.DELETED,
    )

    template = create_test_template(
        user=user,
        is_active=True,
        tasks_count=1,
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        path=f'/templates/{template.id}/run',
        data={
            'name': 'Test name',
            'ancestor_task_id': ancestor_task.id,
        },
    )

    # assert
    assert response.status_code == 200
    Workflow.objects.filter(
        id=response.data['id'],
        ancestor_task=ancestor_task,
    ).exists()


def test_run__guest_performer_in_ancestor_task__permission_denied(
    mocker,
    api_client,
):

    # arrange
    mocker.patch(
        'src.notifications.tasks'
        '.send_new_task_notification.delay',
    )
    mocker.patch(
        'src.analytics.services.AnalyticService.'
        'workflows_started',
    )
    mocker.patch(
        'src.processes.services.templates.'
        'integrations.TemplateIntegrationsService.api_request',
    )
    mocker.patch(
        'src.processes.services.workflow_action.'
        'WorkflowEventService.workflow_run_event',
    )
    mocker.patch(
        'src.processes.services.workflow_action.'
        'WorkflowEventService.sub_workflow_run_event',
    )
    account = create_test_account()
    owner = create_test_user(account=account)
    user = create_test_user(
        account=account,
        is_account_owner=False,
        email='user2@test.test',
    )
    parent_workflow = create_test_workflow(
        user=owner,
        tasks_count=2,
    )
    ancestor_task = parent_workflow.tasks.get(number=1)
    guest = create_test_guest(account=account)
    TaskPerformer.objects.create(
        task_id=ancestor_task.id,
        user_id=guest.id,
    )
    str_token = GuestJWTAuthService.get_str_token(
        task_id=ancestor_task.id,
        user_id=guest.id,
        account_id=account.id,
    )

    template = create_test_template(
        user=user,
        is_active=True,
        tasks_count=1,
    )

    # act
    response = api_client.post(
        path=f'/templates/{template.id}/run',
        data={
            'name': 'Test name',
            'ancestor_task_id': ancestor_task.id,
        },
        **{'X-Guest-Authorization': str_token},

    )

    # assert
    assert response.status_code == 403


# New style tests


def test_run__inactive_template__validation_error(
    mocker,
    api_client,
):
    # arrange
    user = create_test_user()
    template = create_test_template(user, is_active=False)
    wf_service_init_mock = mocker.patch.object(
        WorkflowService,
        attribute='__init__',
        return_value=None,
    )
    wf_service_create_mock = mocker.patch(
        'src.processes.services.workflows.workflow.'
        'WorkflowService.create',
    )
    action_service_init_mock = mocker.patch.object(
        WorkflowActionService,
        attribute='__init__',
        return_value=None,
    )
    start_workflow_mock = mocker.patch(
        'src.processes.services.'
        'workflow_action.WorkflowActionService.start_workflow',
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.post(f'/templates/{template.id}/run')

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == messages.MSG_PW_0066
    wf_service_init_mock.assert_not_called()
    wf_service_create_mock.assert_not_called()
    action_service_init_mock.assert_not_called()
    start_workflow_mock.assert_not_called()


def test_run__all_fields__ok(
    mocker,
    api_client,
):
    # arrange
    user = create_test_user()
    template = create_test_template(user, is_active=True)
    kickoff_field = FieldTemplate.objects.create(
        name='User name',
        type=FieldType.STRING,
        is_required=True,
        kickoff=template.kickoff_instance,
        template=template,
    )
    kickoff_field_value = 'Some name'
    workflow = create_test_workflow(user=user, tasks_count=1)
    ancestor_workflow = create_test_workflow(user=user, tasks_count=1)
    ancestor_task = ancestor_workflow.tasks.get(number=1)
    wf_service_init_mock = mocker.patch.object(
        WorkflowService,
        attribute='__init__',
        return_value=None,
    )
    wf_service_create_mock = mocker.patch(
        'src.processes.services.workflows.workflow.'
        'WorkflowService.create',
        return_value=workflow,
    )
    action_service_init_mock = mocker.patch.object(
        WorkflowActionService,
        attribute='__init__',
        return_value=None,
    )
    start_workflow_mock = mocker.patch(
        'src.processes.services.'
        'workflow_action.WorkflowActionService.start_workflow',
    )
    user_provided_name = 'Some workflow'
    due_date = timezone.now() + timedelta(hours=1)

    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        f'/templates/{template.id}/run',
        data={
            'name': user_provided_name,
            'due_date_tsp': due_date.timestamp(),
            'ancestor_task_id': ancestor_task.id,
            'is_urgent': True,
            'kickoff': {
                kickoff_field.api_name: kickoff_field_value,
            },
        },
    )

    # assert
    assert response.status_code == 200
    wf_service_init_mock.assert_called_once_with(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    wf_service_create_mock.assert_called_once_with(
        instance_template=template,
        kickoff_fields_data={kickoff_field.api_name: kickoff_field_value},
        workflow_starter=user,
        user_provided_name=user_provided_name,
        is_external=False,
        is_urgent=True,
        due_date=due_date,
        ancestor_task=ancestor_task,
        user_agent='Firefox',
    )
    action_service_init_mock.assert_called_once_with(
        workflow=workflow,
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    start_workflow_mock.assert_called_once_with()


def test_run__not_conditions_run_all_tasks__ok(mocker, api_client):

    # arrange
    mocker.patch(
        'src.processes.services.workflow_action.'
        'WorkflowEventService.workflow_run_event',
    )
    mocker.patch(
        'src.analytics.services.AnalyticService.'
        'workflows_started',
    )
    user = create_test_user()
    template = create_test_template(
        user=user,
        is_active=True,
        tasks_count=2,
    )
    template_task_2 = template.tasks.get(number=2)
    template_task_2.conditions.all().delete()
    template_task_2.parents = []
    template_task_2.save()
    api_client.token_authenticate(user)

    # act
    response = api_client.post(f'/templates/{template.id}/run')

    # assert
    assert response.status_code == 200
    workflow = Workflow.objects.get(id=response.data['id'])
    task_1 = workflow.tasks.get(number=1)
    assert task_1.is_active
    task_2 = workflow.tasks.get(number=2)
    assert task_2.is_active


def test_run__skip_and_start_condition_not_passed__not_start_task(
    mocker,
    api_client,
):

    # arrange
    mocker.patch(
        'src.processes.services.workflow_action.'
        'WorkflowEventService.workflow_run_event',
    )
    mocker.patch(
        'src.analytics.services.AnalyticService.'
        'workflows_started',
    )
    user = create_test_owner()
    template = create_test_template(
        user=user,
        is_active=True,
        tasks_count=3,
    )
    template_task_3 = template.tasks.get(number=3)
    kickoff_field = FieldTemplate.objects.create(
        name='Skip third task',
        type=FieldType.STRING,
        is_required=True,
        kickoff=template.kickoff_instance,
        template=template,
    )
    condition_template = ConditionTemplate.objects.create(
        task=template_task_3,
        action=ConditionAction.SKIP_TASK,
        order=2,
        template=template,
    )
    rule = RuleTemplate.objects.create(
        condition=condition_template,
        template=template,
    )
    PredicateTemplate.objects.create(
        rule=rule,
        operator=PredicateOperator.EQUAL,
        field_type=FieldType.STRING,
        field=kickoff_field.api_name,
        value='Yes',
        template=template,
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        f'/templates/{template.id}/run',
        data={
            'kickoff': {
                kickoff_field.api_name: 'No',
            },
        },
    )

    # assert
    assert response.status_code == 200
    workflow = Workflow.objects.get(id=response.data['id'])
    assert workflow.tasks.get(number=1).is_active
    assert workflow.tasks.get(number=2).is_pending
    assert workflow.tasks.get(number=3).is_pending
