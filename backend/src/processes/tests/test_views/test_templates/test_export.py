from datetime import timedelta

import pytest

from src.authentication.services.guest_auth import GuestJWTAuthService
from src.processes.enums import (
    ConditionAction,
    DueDateRule,
    FieldType,
    OwnerType,
    PredicateOperator,
)
from src.processes.models.templates.conditions import (
    ConditionTemplate,
    PredicateTemplate,
    RuleTemplate,
)
from src.processes.models.templates.fields import (
    FieldTemplate,
    FieldTemplateSelection,
)
from src.processes.models.templates.kickoff import Kickoff
from src.processes.models.templates.owner import TemplateOwner
from src.processes.models.templates.raw_due_date import RawDueDateTemplate
from src.processes.models.templates.task import TaskTemplate
from src.processes.models.workflows.task import TaskPerformer
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_admin,
    create_test_group,
    create_test_guest,
    create_test_not_admin,
    create_test_owner,
    create_test_template,
    create_test_user,
    create_test_workflow,
)
from src.utils.dates import date_format
from src.utils.validation import ErrorCode

pytestmark = pytest.mark.django_db


def test_export__response_format__ok(api_client):
    # arrange
    account_owner = create_test_owner()
    api_client.token_authenticate(account_owner)
    kickoff = Kickoff.objects.create(
        account=account_owner.account,
    )
    template = create_test_template(
        user=account_owner,
        kickoff=kickoff,
        tasks_count=0,
    )
    field_kickoff = FieldTemplate.objects.create(
        name='test_field',
        type=FieldType.TEXT,
        is_required=True,
        api_name='test_field',
        kickoff=kickoff,
        template=template,
        description='description',
        account=account_owner.account,
    )
    task = TaskTemplate.objects.create(
        name='Task №{number}',
        number=1,
        template=template,
        account=account_owner.account,
        description='description',
    )
    raw_due_date = RawDueDateTemplate.objects.create(
        task=task,
        template=template,
        duration=timedelta(hours=24),
        duration_months=0,
        rule=DueDateRule.AFTER_TASK_STARTED,
        source_id=task.api_name,
    )
    performer = task.add_raw_performer(account_owner)
    field_task = FieldTemplate.objects.create(
        description='Some description',
        order=11,
        is_required=True,
        task=task,
        type=FieldType.CHECKBOX,
        name='Checkbox field',
        template=template,
        api_name='api-name-1',
        account=account_owner.account,
    )
    selection_template = FieldTemplateSelection.objects.create(
        value='first',
        field_template=field_task,
        template=template,
    )
    condition_template = ConditionTemplate.objects.create(
        task=task,
        action=ConditionAction.SKIP_TASK,
        order=0,
        template=template,
    )
    rule = RuleTemplate.objects.create(
        condition=condition_template,
        template=template,
    )
    predicate = PredicateTemplate.objects.create(
        rule=rule,
        operator=PredicateOperator.EQUAL,
        field_type=FieldType.TEXT,
        field=field_kickoff.api_name,
        value='JOHN CENA',
        template=template,
    )

    owners = list(TemplateOwner.objects.filter(template=template))

    # act
    response = api_client.get('/templates/export')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    response_data = response.data[0]
    assert response_data['id'] == template.id
    assert response_data['name'] == template.name
    assert response_data['description'] == template.description
    assert response_data['is_active'] == template.is_active
    assert response_data['is_public'] == template.is_public
    assert response_data['public_url'] == template.public_url
    assert response_data['finalizable'] == template.finalizable
    assert response_data['updated_by'] == template.updated_by
    assert response_data['date_updated'] == (
        template.date_updated.strftime(date_format)
    )

    owners_template = response_data['owners'][0]
    assert owners_template['source_id'] == str(owners[0].user_id)
    assert owners_template['type'] == owners[0].type
    assert owners_template['api_name'] == owners[0].api_name

    kickoff_fields = response_data['kickoff']['fields'][0]
    assert kickoff_fields['order'] == field_kickoff.order
    assert kickoff_fields['name'] == field_kickoff.name
    assert kickoff_fields['is_required'] == field_kickoff.is_required
    assert kickoff_fields['description'] == field_kickoff.description
    assert kickoff_fields['default'] == field_kickoff.default
    assert kickoff_fields['api_name'] == field_kickoff.api_name

    tasks_template = response_data['tasks'][0]
    assert tasks_template['number'] == task.number
    assert tasks_template['name'] == task.name
    assert tasks_template['description'] == task.description
    assert (
        tasks_template['require_completion_by_all'] ==
        task.require_completion_by_all
    )
    assert tasks_template['delay'] == task.delay
    assert tasks_template['revert_task'] == task.revert_task

    raw_due_date_task = tasks_template['raw_due_date']
    assert raw_due_date_task['api_name'] == raw_due_date.api_name
    assert raw_due_date_task['duration'] == '1 00:00:00'
    assert raw_due_date_task['duration_months'] == raw_due_date.duration_months
    assert raw_due_date_task['rule'] == raw_due_date.rule
    assert raw_due_date_task['source_id'] == raw_due_date.source_id

    performers = tasks_template['raw_performers']
    assert performers[0]['api_name'] == performer.api_name
    assert performers[0]['type'] == performer.type
    assert performers[0]['source_id'] == str(performer.user_id)

    field_task_template = tasks_template['fields']
    assert field_task_template[0]['order'] == field_task.order
    assert field_task_template[0]['name'] == field_task.name
    assert field_task_template[0]['type'] == field_task.type
    assert field_task_template[0]['is_required'] == field_task.is_required
    assert field_task_template[0]['description'] == field_task.description
    assert field_task_template[0]['default'] == field_task.default
    assert field_task_template[0]['api_name'] == field_task.api_name

    selection = field_task_template[0]['selections']
    assert selection[0]['api_name'] == selection_template.api_name
    assert selection[0]['value'] == selection_template.value
    conditions_template = tasks_template['conditions']
    assert conditions_template[0]['action'] == condition_template.action
    assert conditions_template[0]['order'] == condition_template.order
    assert conditions_template[0]['api_name'] == condition_template.api_name

    rules_template = conditions_template[0]['rules']
    assert rules_template[0]['api_name'] == rule.api_name

    predicates_template = rules_template[0]['predicates']
    assert predicates_template[0]['field_type'] == predicate.field_type
    assert predicates_template[0]['value'] == predicate.value
    assert predicates_template[0]['api_name'] == predicate.api_name
    assert predicates_template[0]['field'] == predicate.field
    assert predicates_template[0]['operator'] == predicate.operator


def test_export__not_auth__permission_denied(api_client):
    # act
    response = api_client.get('/templates/export')

    # assert
    assert response.status_code == 401


def test_export__guest__permission_denied(api_client):
    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user, tasks_count=1)
    task = workflow.tasks.get(number=1)
    guest = create_test_guest(account=user.account)
    TaskPerformer.objects.create(
        task_id=task.id,
        user_id=guest.id,
    )
    str_token = GuestJWTAuthService.get_str_token(
        task_id=task.id,
        user_id=guest.id,
        account_id=user.account.id,
    )

    # act
    response = api_client.get(
        path='/templates/export',
        **{'X-Guest-Authorization': str_token},
    )

    # assert
    assert response.status_code == 403


def test_export__public_token__permission_denied(api_client):
    # arrange
    user = create_test_user()
    template = create_test_template(
        user=user,
        is_active=True,
        is_public=True,
    )
    auth_header_value = f'Token {template.public_id}'
    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        '/templates/export',
        **{'X-Public-Authorization': auth_header_value},
    )

    # assert
    assert response.status_code == 403


def test_export__not_admin__permission_denied(api_client):
    # arrange
    account = create_test_account()
    user = create_test_not_admin(account=account)
    api_client.token_authenticate(user)

    # act
    response = api_client.get('/templates/export')

    # assert
    assert response.status_code == 403


def test_export__admin__permission_denied(api_client):
    # arrange
    account = create_test_account()
    user = create_test_admin(account=account)
    api_client.token_authenticate(user)

    # act
    response = api_client.get('/templates/export')

    # assert
    assert response.status_code == 403


def test_export__account_owner_from_another_acc__not_show(api_client):
    # arrange
    user = create_test_owner()
    owner_another_account = create_test_owner(email='test@bou.tr')
    create_test_template(user=user)
    api_client.token_authenticate(owner_another_account)

    # act
    response = api_client.get('/templates/export')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 0


def test_export__filter_is_active__ok(api_client):
    # arrange
    owner_account = create_test_owner()
    api_client.token_authenticate(owner_account)
    template = create_test_template(
        user=owner_account,
        is_active=True,
    )
    create_test_template(user=owner_account)

    # act
    response = api_client.get('/templates/export?is_active=true')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == template.id
    assert response.data[0]['is_active'] is True


def test_export__filter_is_public__ok(api_client):
    # arrange
    account_owner = create_test_owner()
    api_client.token_authenticate(account_owner)
    template = create_test_template(
        user=account_owner,
        is_public=True,
    )
    create_test_template(
        user=account_owner,
        is_public=False,
    )

    # act
    response = api_client.get('/templates/export?is_public=true')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == template.id
    assert response.data[0]['is_public'] is True


def test_export__ordering_name__ok(api_client):
    # arrange
    account_owner = create_test_owner()
    api_client.token_authenticate(account_owner)
    template_one = create_test_template(account_owner, name='one')
    template_two = create_test_template(account_owner, name='two')

    # act
    response = api_client.get('/templates/export?ordering=name')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 2
    assert response.data[0]['id'] == template_one.id
    assert response.data[1]['id'] == template_two.id


def test_export__ordering_invert_name__ok(api_client):
    # arrange
    account_owner = create_test_owner()
    api_client.token_authenticate(account_owner)
    template_one = create_test_template(account_owner, name='one')
    template_two = create_test_template(account_owner, name='two')

    # act
    response = api_client.get('/templates/export?ordering=-name')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 2
    assert response.data[0]['id'] == template_two.id
    assert response.data[1]['id'] == template_one.id


def test_export__ordering_date__ok(api_client):
    # arrange
    account_owner = create_test_owner()
    api_client.token_authenticate(account_owner)
    template_one = create_test_template(account_owner)
    template_two = create_test_template(account_owner)

    # act
    response = api_client.get('/templates/export?ordering=date')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 2
    assert response.data[0]['id'] == template_one.id
    assert response.data[1]['id'] == template_two.id


def test_export__ordering_invert_date__ok(api_client):
    # arrange
    account_owner = create_test_owner()
    api_client.token_authenticate(account_owner)
    template_one = create_test_template(account_owner)
    template_two = create_test_template(account_owner)

    # act
    response = api_client.get('/templates/export?ordering=-date')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 2
    assert response.data[0]['id'] == template_two.id
    assert response.data[1]['id'] == template_one.id


def test_export__invalid_filter_is_public__validation_error(api_client):
    # arrange
    owner_account = create_test_owner()
    api_client.token_authenticate(owner_account)
    create_test_template(user=owner_account)

    # act
    response = api_client.get(path='/templates?is_public=ERROR')

    # assert
    message = 'Must be a valid boolean.'
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['details']['name'] == 'is_public'
    assert response.data['message'] == message
    assert response.data['details']['reason'] == message


def test_export__invalid_filter_is_active__validation_error(api_client):
    # arrange
    owner_account = create_test_owner()
    api_client.token_authenticate(owner_account)
    create_test_template(user=owner_account)

    # act
    response = api_client.get(path='/templates?is_active=ERROR')

    # assert
    message = 'Must be a valid boolean.'
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['details']['name'] == 'is_active'
    assert response.data['message'] == message
    assert response.data['details']['reason'] == message


def test_export__invalid_ordering__validation_error(api_client):
    # arrange
    owner_account = create_test_owner()
    api_client.token_authenticate(owner_account)
    create_test_template(user=owner_account)

    # act
    response = api_client.get(path='/templates?ordering=ERROR')

    # assert
    message = '"ERROR" is not a valid choice.'
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['details']['name'] == 'ordering'
    assert response.data['message'] == message
    assert response.data['details']['reason'] == message


def test_export__filter_owners_ids__ok(api_client):
    # arrange
    account = create_test_account()
    owner_account = create_test_owner(account=account)
    user = create_test_user(
        email='test@bou.tr',
        account=account,
    )
    api_client.token_authenticate(owner_account)
    template = create_test_template(user=owner_account)
    create_test_template(user=user)

    # act
    response = api_client.get(
        f'/templates/export?owners_ids={owner_account.id}',
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == template.id


def test_export__filter_owners_ids_user_in_group__ok(api_client):
    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    group = create_test_group(account, users=[user])
    template = create_test_template(user=user)
    create_test_template(user=user)
    TemplateOwner.objects.all().delete()
    TemplateOwner.objects.create(
        template=template,
        account=account,
        type=OwnerType.GROUP,
        group_id=group.id,
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        f'/templates/export?owners_ids={user.id}',
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == template.id


def test_export__filter_owners_group_ids__ok(api_client):
    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    group = create_test_group(account, users=[user])
    template = create_test_template(user=user)
    TemplateOwner.objects.all().delete()
    TemplateOwner.objects.create(
        template=template,
        account=account,
        type=OwnerType.GROUP,
        group_id=group.id,
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        f'/templates/export?owners_group_ids={group.id}',
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == template.id


def test_export__mix_filter__ok(api_client):
    # arrange
    account = create_test_account()
    user1 = create_test_owner(account=account)
    user2 = create_test_admin(
        email='test@bou.tr',
        account=account,
    )
    group = create_test_group(account, users=[user1])
    api_client.token_authenticate(user1)
    template1 = create_test_template(user=user1)
    template2 = create_test_template(user=user2)
    TemplateOwner.objects.create(
        template=template2,
        account=account,
        type=OwnerType.GROUP,
        group_id=group.id,
    )

    # act
    response = api_client.get(
        '/templates/export'
        f'?owners_ids={user1.id}'
        f'&owners_group_ids={group.id}',
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 2
    assert response.data[0]['id'] == template1.id
    assert response.data[1]['id'] == template2.id


def test_export__pagination__ok(api_client):
    # arrange
    owner_account = create_test_owner()
    create_test_template(owner_account)
    create_test_template(owner_account)
    template = create_test_template(owner_account)
    create_test_template(owner_account)
    api_client.token_authenticate(owner_account)

    # act
    response = api_client.get(
        '/templates/export',
        data={
            'limit': 1,
            'offset': 2,
        },
    )

    # assert
    assert response.status_code == 200
    assert response.data['count'] == 4
    assert len(response.data['results']) == 1
    assert response.data['results'][0]['id'] == template.id
