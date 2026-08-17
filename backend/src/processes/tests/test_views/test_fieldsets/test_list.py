
import pytest
from datetime import timedelta

from django.utils import timezone

from src.accounts.enums import BillingPlanType
from src.accounts.messages import MSG_A_0035, MSG_A_0037, MSG_A_0041
from src.processes.enums import (
    FieldSetRuleOperator,
    FieldRuleType,
    FieldRuleOperator,
)
from src.processes.models.templates.fields import (
    FieldTemplateRuleSet,
    FieldTemplateRuleGroupOr,
    FieldTemplateRuleGroupAnd,
)
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_admin,
    create_test_shared_fieldset,
    create_test_fieldset_template,
    create_test_not_admin,
    create_test_owner,
    create_test_template,
)
from src.processes.models.templates.fieldset import FieldsetTemplate
from src.utils.validation import ErrorCode

pytestmark = pytest.mark.django_db


def test_list_fieldsets__all_data__ok(api_client):
    """ List fieldsets returning all fields including title and order """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    rule_operator = FieldSetRuleOperator.SUM_EQUAL
    rule_value = '10'
    fieldset = create_test_shared_fieldset(
        account=account,
        title='Fieldset Title',
        order=3,
        rule_operator=rule_operator,
        rule_value=rule_value,
    )
    field = fieldset.fields.get()
    rule = fieldset.rulesets.first()
    group_or = rule.groups_or.first()
    group_and = group_or.groups_and.first()

    field_rule_type = FieldRuleType.SHOW
    field_ruleset = FieldTemplateRuleSet.objects.create(
        field=field,
        account=account,
        api_name=f'{field.api_name}-ruleset-1',
        type=field_rule_type,
        order=0,
    )
    field_group_or = FieldTemplateRuleGroupOr.objects.create(
        field_rule=field_ruleset,
        account=account,
        api_name=f'{field.api_name}-group-or-1',
    )
    field_rule_value = 'some value'
    field_group_and = FieldTemplateRuleGroupAnd.objects.create(
        group_or=field_group_or,
        account=account,
        api_name=f'{field.api_name}-group-and-1',
        operator=FieldRuleOperator.EQUAL,
        value=field_rule_value,
        field=field.api_name,
    )

    api_client.token_authenticate(user=user)

    # act
    response = api_client.get('/fieldsets')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    fieldset_data = response.data[0]
    assert fieldset_data['id'] == fieldset.id
    assert fieldset_data['api_name'] == fieldset.api_name
    assert fieldset_data['name'] == fieldset.name
    assert fieldset_data['title'] == 'Fieldset Title'
    assert fieldset_data['order'] == 3
    assert fieldset_data['description'] == ''
    assert fieldset_data['layout'] == fieldset.layout
    assert fieldset_data['label_position'] == fieldset.label_position
    assert fieldset_data['usage'] == []

    assert len(fieldset_data['rulesets']) == 1
    rule_data = fieldset_data['rulesets'][0]
    assert rule_data['api_name'] == rule.api_name
    assert rule_data['message'] is None
    assert rule_data['order'] == 0
    assert rule_data['fields'] == []

    assert len(rule_data['groups_or']) == 1
    group_or_data = rule_data['groups_or'][0]
    assert group_or_data['api_name'] == group_or.api_name

    assert len(group_or_data['groups_and']) == 1
    group_and_data = group_or_data['groups_and'][0]
    assert group_and_data['api_name'] == group_and.api_name
    assert group_and_data['operator'] == rule_operator
    assert group_and_data['value'] == rule_value

    assert len(fieldset_data['fields']) == 1
    field_data = fieldset_data['fields'][0]
    assert field_data['name'] == field.name
    assert field_data['type'] == field.type
    assert field_data['api_name'] == field.api_name
    assert field_data['description'] == ''
    assert field_data['is_required'] is False
    assert field_data['is_hidden'] is False
    assert field_data['default'] == ''
    assert field_data['order'] == field.order
    assert 'dataset' not in field_data
    assert 'selections' not in field_data

    assert len(field_data['rulesets']) == 1
    field_rule_data = field_data['rulesets'][0]
    assert field_rule_data['api_name'] == field_ruleset.api_name
    assert field_rule_data['type'] == field_rule_type
    assert field_rule_data['message'] is None
    assert field_rule_data['order'] == 0

    assert len(field_rule_data['groups_or']) == 1
    field_group_or_data = field_rule_data['groups_or'][0]
    assert field_group_or_data['api_name'] == field_group_or.api_name

    assert len(field_group_or_data['groups_and']) == 1
    field_group_and_data = field_group_or_data['groups_and'][0]
    assert field_group_and_data['api_name'] == field_group_and.api_name
    assert field_group_and_data['field'] == field.api_name
    assert field_group_and_data['operator'] == FieldRuleOperator.EQUAL
    assert field_group_and_data['value'] == field_rule_value


def test_list_fieldsets__used_in_tasks__return_usage(
    api_client,
):

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    rule_operator = FieldSetRuleOperator.SUM_EQUAL
    rule_value = '10'
    shared_fieldset = create_test_shared_fieldset(
        account=account,
        title='Fieldset Title',
        order=3,
        rule_operator=rule_operator,
        rule_value=rule_value,
    )
    template_1 = create_test_template(
        user=user,
        tasks_count=1,
    )
    task_11 = template_1.tasks.get(number=1)
    create_test_fieldset_template(
        account=account,
        template=template_1,
        task=task_11,
        shared_fieldset=shared_fieldset,
    )
    template_2 = create_test_template(
        user=user,
        tasks_count=1,
    )
    task_21 = template_2.tasks.get(number=1)
    create_test_fieldset_template(
        account=account,
        template=template_2,
        task=task_21,
        shared_fieldset=shared_fieldset,
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.get('/fieldsets')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    shared_fieldset_data = response.data[0]
    assert shared_fieldset_data['id'] == shared_fieldset.id
    assert len(shared_fieldset_data['usage']) == 2
    assert shared_fieldset_data['usage'][0]['id'] == template_1.id
    assert shared_fieldset_data['usage'][0]['name'] == template_1.name
    assert shared_fieldset_data['usage'][1]['id'] == template_2.id
    assert shared_fieldset_data['usage'][1]['name'] == template_2.name


def test_list_fieldsets__used_in_kickoff_and_tasks__return_usage(
    api_client,
):

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    rule_operator = FieldSetRuleOperator.SUM_EQUAL
    rule_value = '10'
    shared_fieldset = create_test_shared_fieldset(
        account=account,
        title='Fieldset Title',
        order=3,
        rule_operator=rule_operator,
        rule_value=rule_value,
    )
    template_1 = create_test_template(
        user=user,
        tasks_count=1,
    )
    kickoff = template_1.kickoff_instance
    create_test_fieldset_template(
        account=account,
        template=template_1,
        kickoff=kickoff,
        shared_fieldset=shared_fieldset,
    )
    template_2 = create_test_template(
        user=user,
        tasks_count=1,
    )
    task_21 = template_2.tasks.get(number=1)
    create_test_fieldset_template(
        account=account,
        template=template_2,
        task=task_21,
        shared_fieldset=shared_fieldset,
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.get('/fieldsets')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    shared_fieldset_data = response.data[0]
    assert shared_fieldset_data['id'] == shared_fieldset.id
    assert len(shared_fieldset_data['usage']) == 2
    assert shared_fieldset_data['usage'][0]['id'] == template_1.id
    assert shared_fieldset_data['usage'][0]['name'] == template_1.name
    assert shared_fieldset_data['usage'][1]['id'] == template_2.id
    assert shared_fieldset_data['usage'][1]['name'] == template_2.name


def test_list_fieldsets__used_twice_in_one_template__return_usage(
    api_client,
):

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    rule_operator = FieldSetRuleOperator.SUM_EQUAL
    rule_value = '10'
    shared_fieldset = create_test_shared_fieldset(
        account=account,
        title='Fieldset Title',
        order=3,
        rule_operator=rule_operator,
        rule_value=rule_value,
    )
    template = create_test_template(
        user=user,
        tasks_count=1,
    )
    kickoff = template.kickoff_instance
    task = template.tasks.get(number=1)
    create_test_fieldset_template(
        account=account,
        template=template,
        task=task,
        shared_fieldset=shared_fieldset,
    )
    create_test_fieldset_template(
        account=account,
        template=template,
        kickoff=kickoff,
        shared_fieldset=shared_fieldset,
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.get('/fieldsets')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    shared_fieldset_data = response.data[0]
    assert shared_fieldset_data['id'] == shared_fieldset.id
    assert len(shared_fieldset_data['usage']) == 1
    assert shared_fieldset_data['usage'][0]['id'] == template.id
    assert shared_fieldset_data['usage'][0]['name'] == template.name


def test_list_fieldsets__shared_fieldset_has_rules_and_fields__ok(
    api_client,
):

    """ List shared fieldsets returns rules and fields """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    rule_operator = FieldSetRuleOperator.SUM_EQUAL
    rule_value = '10'
    fieldset = create_test_shared_fieldset(
        account=account,
        rule_operator=rule_operator,
        rule_value=rule_value,
    )
    field = fieldset.fields.get()
    rule = fieldset.rulesets.first()

    api_client.token_authenticate(user=user)

    # act
    response = api_client.get('/fieldsets')

    # assert
    assert response.status_code == 200
    data = response.data[0]
    assert data['id'] == fieldset.id
    assert len(data['rulesets']) == 1
    assert data['rulesets'][0]['api_name'] == rule.api_name
    assert len(data['fields']) == 1
    assert data['fields'][0]['api_name'] == field.api_name


def test_list_fieldsets__pagination__ok(api_client):
    """ Paginated list returns correct count and slice """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    fieldset_1 = create_test_shared_fieldset(
        account=account,
    )
    fieldset_2 = create_test_shared_fieldset(
        account=account,
    )
    create_test_shared_fieldset(
        account=account,
    )

    api_client.token_authenticate(user=user)

    # act
    response = api_client.get(
        '/fieldsets',
        data={'limit': 2, 'offset': 1},
    )

    # assert
    assert response.status_code == 200
    assert response.data['count'] == 3
    assert len(response.data['results']) == 2

    fieldset_data = response.data['results'][0]
    assert fieldset_data['id'] == fieldset_2.id

    item_2 = response.data['results'][1]
    assert item_2['id'] == fieldset_1.id


def test_list_fieldsets__different_accounts__ok(api_client):
    """ List fieldsets filtered by account — other accounts excluded """

    # arrange
    account_1 = create_test_account(name='Account 1')
    user_1 = create_test_owner(account=account_1)
    fieldset_1 = create_test_shared_fieldset(
        account=account_1,
    )

    account_2 = create_test_account(name='Account 2')
    create_test_owner(
        account=account_2,
        email='owner2@pneumatic.app',
    )
    create_test_shared_fieldset(
        account=account_2,
    )

    api_client.token_authenticate(user=user_1)

    # act
    response = api_client.get('/fieldsets')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == fieldset_1.id


def test_list_fieldsets__rule_with_fields__ok(api_client):
    """ List fieldsets returning rules mapping to fields """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    rule_operator = FieldSetRuleOperator.SUM_EQUAL
    rule_value = '10'
    fieldset = create_test_shared_fieldset(
        account=account,
        rule_operator=rule_operator,
        rule_value=rule_value,
    )
    field = fieldset.fields.get()
    rule = fieldset.rulesets.first()
    rule.fields.add(field)

    api_client.token_authenticate(user=user)

    # act
    response = api_client.get('/fieldsets')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    fieldset_data = response.data[0]

    assert len(fieldset_data['rulesets']) == 1
    rules_data = fieldset_data['rulesets']
    assert rules_data[0]['fields'] == [field.api_name]


def test_list_fieldsets__admin__ok(api_client):
    """ Admin (non-owner) user can list fieldsets """

    # arrange
    account = create_test_account()
    create_test_owner(account=account)
    user = create_test_admin(account=account)
    fieldset = create_test_shared_fieldset(
        account=account,
    )

    api_client.token_authenticate(user=user)

    # act
    response = api_client.get('/fieldsets')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == fieldset.id


def test_list_fieldsets__no_ordering__ok(api_client):

    """ No ordering param — default -date_created """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    now = timezone.now()
    fieldset_1 = create_test_shared_fieldset(
        account=account,
        name='Oldest',
    )
    FieldsetTemplate.objects.filter(id=fieldset_1.id).update(
        date_created=now - timedelta(days=2),
    )
    fieldset_2 = create_test_shared_fieldset(
        account=account,
        name='Middle',
    )
    FieldsetTemplate.objects.filter(id=fieldset_2.id).update(
        date_created=now - timedelta(days=1),
    )
    fieldset_3 = create_test_shared_fieldset(
        account=account,
        name='Newest',
    )
    FieldsetTemplate.objects.filter(id=fieldset_3.id).update(
        date_created=now,
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.get('/fieldsets')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 3
    fieldset_data = response.data[0]
    assert fieldset_data['id'] == fieldset_3.id
    item_2 = response.data[1]
    assert item_2['id'] == fieldset_2.id
    item_3 = response.data[2]
    assert item_3['id'] == fieldset_1.id


def test_list_fieldsets__ordering_name_asc__ok(api_client):

    """ ordering=name — ascending by name """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    fieldset_1 = create_test_shared_fieldset(
        account=account,
        name='Alpha',
    )
    fieldset_2 = create_test_shared_fieldset(
        account=account,
        name='Beta',
    )
    fieldset_3 = create_test_shared_fieldset(
        account=account,
        name='Gamma',
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.get(
        '/fieldsets',
        data={'ordering': 'name'},
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 3
    fieldset_data = response.data[0]
    assert fieldset_data['id'] == fieldset_1.id
    assert fieldset_data['name'] == 'Alpha'
    item_2 = response.data[1]
    assert item_2['id'] == fieldset_2.id
    assert item_2['name'] == 'Beta'
    item_3 = response.data[2]
    assert item_3['id'] == fieldset_3.id
    assert item_3['name'] == 'Gamma'


def test_list_fieldsets__ordering_name_desc__ok(api_client):

    """ ordering=-name — descending by name """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    fieldset_1 = create_test_shared_fieldset(
        account=account,
        name='Alpha',
    )
    fieldset_2 = create_test_shared_fieldset(
        account=account,
        name='Beta',
    )
    fieldset_3 = create_test_shared_fieldset(
        account=account,
        name='Gamma',
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.get(
        '/fieldsets',
        data={'ordering': '-name'},
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 3
    fieldset_data = response.data[0]
    assert fieldset_data['id'] == fieldset_3.id
    assert fieldset_data['name'] == 'Gamma'
    item_2 = response.data[1]
    assert item_2['id'] == fieldset_2.id
    assert item_2['name'] == 'Beta'
    item_3 = response.data[2]
    assert item_3['id'] == fieldset_1.id
    assert item_3['name'] == 'Alpha'


def test_list_fieldsets__ordering_date_asc__ok(api_client):

    """ ordering=date — ascending by date_created """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)

    now = timezone.now()
    fieldset_1 = create_test_shared_fieldset(
        account=account,
        name='Oldest',
    )
    FieldsetTemplate.objects.filter(id=fieldset_1.id).update(
        date_created=now - timedelta(days=2),
    )
    fieldset_2 = create_test_shared_fieldset(
        account=account,
        name='Middle',
    )
    FieldsetTemplate.objects.filter(id=fieldset_2.id).update(
        date_created=now - timedelta(days=1),
    )
    fieldset_3 = create_test_shared_fieldset(
        account=account,
        name='Newest',
    )
    FieldsetTemplate.objects.filter(id=fieldset_3.id).update(
        date_created=now,
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.get(
        '/fieldsets',
        data={'ordering': 'date'},
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 3
    fieldset_data = response.data[0]
    assert fieldset_data['id'] == fieldset_1.id
    item_2 = response.data[1]
    assert item_2['id'] == fieldset_2.id
    item_3 = response.data[2]
    assert item_3['id'] == fieldset_3.id


def test_list_fieldsets__ordering_date_desc__ok(api_client):

    """ ordering=-date — descending by date_created """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)

    now = timezone.now()
    fieldset_1 = create_test_shared_fieldset(
        account=account,
        name='Oldest',
    )
    FieldsetTemplate.objects.filter(id=fieldset_1.id).update(
        date_created=now - timedelta(days=2),
    )
    fieldset_2 = create_test_shared_fieldset(
        account=account,
        name='Middle',
    )
    FieldsetTemplate.objects.filter(id=fieldset_2.id).update(
        date_created=now - timedelta(days=1),
    )
    fieldset_3 = create_test_shared_fieldset(
        account=account,
        name='Newest',
    )
    FieldsetTemplate.objects.filter(id=fieldset_3.id).update(
        date_created=now,
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.get(
        '/fieldsets',
        data={'ordering': '-date'},
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 3
    fieldset_data = response.data[0]
    assert fieldset_data['id'] == fieldset_3.id
    item_2 = response.data[1]
    assert item_2['id'] == fieldset_2.id
    item_3 = response.data[2]
    assert item_3['id'] == fieldset_1.id


def test_list_fieldsets__no_pagination__ok(api_client):

    """ No pagination params — flat list response """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)

    create_test_shared_fieldset(
        account=account,
        name='First',
    )
    create_test_shared_fieldset(
        account=account,
        name='Second',
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.get('/fieldsets')

    # assert
    assert response.status_code == 200
    assert isinstance(response.data, list)
    assert len(response.data) == 2


def test_list_fieldsets__ordering_invalid__validation_error(api_client):

    """ Invalid ordering value returns validation error """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)

    create_test_shared_fieldset(
        account=account,
        name='First',
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.get(
        '/fieldsets',
        data={'ordering': 'foobar'},
    )

    # assert
    assert response.status_code == 400
    message = '"foobar" is not a valid choice.'
    assert response.data['message'] == message
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR


def test_list_fieldsets__ordering_empty__ok(api_client):

    """ Empty ordering value falls back to default """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)

    now = timezone.now()
    fieldset_1 = create_test_shared_fieldset(
        account=account,
        name='First',
    )
    FieldsetTemplate.objects.filter(id=fieldset_1.id).update(
        date_created=now - timedelta(days=1),
    )
    fieldset_2 = create_test_shared_fieldset(
        account=account,
        name='Second',
    )
    FieldsetTemplate.objects.filter(id=fieldset_2.id).update(
        date_created=now,
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.get(
        '/fieldsets',
        data={'ordering': ''},
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 2

    # default ordering is -date_created (newest first)
    fieldset_data = response.data[0]
    assert fieldset_data['id'] == fieldset_2.id
    item_2 = response.data[1]
    assert item_2['id'] == fieldset_1.id


def test_list_fieldsets__soft_deleted__ok(api_client):

    """ Soft-deleted fieldsets are excluded """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)

    fieldset = create_test_shared_fieldset(
        account=account,
        name='Deleted Fieldset',
    )
    FieldsetTemplate.objects.filter(id=fieldset.id).update(
        is_deleted=True,
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.get('/fieldsets')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 0


def test_list_fieldsets__not_shared__empty_list(api_client):

    """ Non-shared fieldset is excluded from the list """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    fieldset = create_test_shared_fieldset(
        account=account,
    )
    fieldset.is_shared = False
    fieldset.save()

    api_client.token_authenticate(user=user)

    # act
    response = api_client.get('/fieldsets')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 0


def test_list_fieldsets__unauthenticated__unauthorized(api_client):
    """ Unauthenticated request returns 401 """

    # act
    response = api_client.get('/fieldsets')

    # assert
    assert response.status_code == 401


def test_list_fieldsets__expired_sub__permission_denied(api_client):
    """ Expired subscription returns 403 """

    # arrange
    account = create_test_account(
        plan=BillingPlanType.PREMIUM,
        plan_expiration=timezone.now() - timedelta(days=1),
    )
    user = create_test_owner(account=account)

    api_client.token_authenticate(user=user)

    # act
    response = api_client.get('/fieldsets')

    # assert
    assert response.status_code == 403
    assert response.data['detail'] == MSG_A_0035


def test_list_fieldsets__billing_plan__permission_denied(api_client):
    """ Billing plan permission denied returns 403 """

    # arrange
    account = create_test_account(plan=None)
    user = create_test_owner(account=account)

    api_client.token_authenticate(user=user)

    # act
    response = api_client.get('/fieldsets')

    # assert
    assert response.status_code == 403
    assert response.data['detail'] == MSG_A_0041


def test_list_fieldsets__users_overlimit__permission_denied(api_client):
    """ Users overlimited returns 403 """

    # arrange
    account = create_test_account(
        plan=BillingPlanType.PREMIUM,
        max_users=1,
    )
    user = create_test_owner(account=account)
    create_test_not_admin(
        account=account,
        email='extra@pneumatic.app',
    )
    account.active_users = 2
    account.save()

    api_client.token_authenticate(user=user)

    # act
    response = api_client.get('/fieldsets')

    # assert
    assert response.status_code == 403
    assert response.data['detail'] == MSG_A_0037


def test_list_fieldsets__non_admin__permission_denied(api_client):
    """ Non-admin non-owner user returns 403 """

    # arrange
    account = create_test_account()
    create_test_owner(account=account)
    user = create_test_not_admin(account=account)

    api_client.token_authenticate(user=user)

    # act
    response = api_client.get('/fieldsets')

    # assert
    assert response.status_code == 403
