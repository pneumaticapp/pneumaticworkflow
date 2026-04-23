import pytest
from datetime import timedelta

from django.utils import timezone

from src.accounts.enums import BillingPlanType
from src.accounts.messages import MSG_A_0035, MSG_A_0037, MSG_A_0041
from src.processes.enums import (
    FieldSetRuleType,
)
from src.processes.messages import template as messages
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_admin,
    create_test_fieldset_template,
    create_test_not_admin,
    create_test_owner,
    create_test_template,
)

pytestmark = pytest.mark.django_db


def test_list_fieldsets__all_data__ok(api_client):
    """List fieldsets for existing template"""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(
        user=user,
        tasks_count=1,
    )
    kickoff = template.kickoff_instance
    rule_type = FieldSetRuleType.SUM_EQUAL
    rule_value = '10'
    fieldset = create_test_fieldset_template(
        account=account,
        template=template,
        kickoff=kickoff,
        name='Kickoff Fieldset',
        order=1,
        rule_type=rule_type,
        rule_value=rule_value,
    )
    field = fieldset.fields.get()
    rule = fieldset.rules.get()

    api_client.token_authenticate(user=user)

    # act
    response = api_client.get(
        f'/templates/{template.id}/fieldsets',
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    item_1 = response.data[0]
    assert item_1['id'] == fieldset.id
    assert item_1['api_name'] == fieldset.api_name
    assert item_1['name'] == fieldset.name
    assert item_1['description'] == ''
    assert item_1['order'] == fieldset.order
    assert item_1['layout'] == fieldset.layout
    assert item_1['label_position'] == fieldset.label_position
    assert item_1['task'] is None

    assert len(item_1['rules']) == 1
    rules_data = item_1['rules']
    assert rules_data[0]['id'] == rule.id
    assert rules_data[0]['type'] == rule_type
    assert rules_data[0]['value'] == rule_value
    assert rules_data[0]['api_name'] == rule.api_name

    assert len(item_1['fields']) == 1
    fields_data = item_1['fields']
    assert fields_data[0]['name'] == field.name
    assert fields_data[0]['type'] == field.type
    assert fields_data[0]['order'] == 1
    assert fields_data[0]['api_name'] == field.api_name
    assert fields_data[0]['description'] == ''
    assert fields_data[0]['is_required'] is False
    assert fields_data[0]['is_hidden'] is False
    assert fields_data[0]['default'] == ''
    assert 'dataset' not in fields_data[0]
    assert 'selections' not in fields_data[0]


def test_list_fieldsets__two_fieldsets__ok(api_client):
    """List fieldsets for existing template"""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(
        user=user,
        tasks_count=1,
    )
    kickoff = template.kickoff_instance
    fieldset_1 = create_test_fieldset_template(
        account=account,
        template=template,
        kickoff=kickoff,
        order=1,
    )
    template_task = template.tasks.first()
    fieldset_2 = create_test_fieldset_template(
        account=account,
        template=template,
        task=template_task,
        order=2,
    )

    api_client.token_authenticate(user=user)

    # act
    response = api_client.get(
        f'/templates/{template.id}/fieldsets',
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 2

    # ordered by -id (newest first)
    item_1 = response.data[0]
    assert item_1['id'] == fieldset_2.id
    assert item_1['task'] == template_task.api_name
    assert item_1['order'] == 2

    item_2 = response.data[1]
    assert item_2['id'] == fieldset_1.id
    assert item_2['task'] is None
    assert item_2['order'] == 1


def test_list_fieldsets__pagination__ok(api_client):
    """List fieldsets for existing template"""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(
        user=user,
        tasks_count=1,
    )
    template_task = template.tasks.first()
    fieldset_1 = create_test_fieldset_template(
        account=account,
        template=template,
        task=template_task,
        order=3,
    )
    fieldset_2 = create_test_fieldset_template(
        account=account,
        template=template,
        task=template_task,
        order=2,
    )
    create_test_fieldset_template(
        account=account,
        template=template,
        task=template_task,
        order=1,
    )

    api_client.token_authenticate(user=user)

    # act
    response = api_client.get(
        f'/templates/{template.id}/fieldsets',
        data={'limit': 2, 'offset': 1},
    )

    # assert
    assert response.status_code == 200
    assert response.data['count'] == 3
    assert len(response.data['results']) == 2

    item_1 = response.data['results'][0]
    assert item_1['id'] == fieldset_2.id
    assert item_1['task'] == template_task.api_name
    assert item_1['order'] == 2

    item_2 = response.data['results'][1]
    assert item_2['id'] == fieldset_1.id
    assert item_2['task'] == template_task.api_name
    assert item_2['order'] == 3


def test_list_fieldsets__different_accounts__ok(api_client):
    """List fieldsets filtered by account"""

    # arrange
    account_1 = create_test_account(name='Account 1')
    user_1 = create_test_owner(account=account_1)
    template_1 = create_test_template(
        user=user_1,
        tasks_count=1,
    )
    fieldset_1 = create_test_fieldset_template(
        account=account_1,
        template=template_1,
        kickoff=template_1.kickoff_instance,
        name='Account 1 Fieldset',
    )

    account_2 = create_test_account(name='Account 2')
    user_2 = create_test_owner(
        account=account_2,
        email='owner2@pneumatic.app',
    )
    template_2 = create_test_template(
        user=user_2,
        tasks_count=1,
    )
    create_test_fieldset_template(
        account=account_2,
        template=template_2,
        kickoff=template_2.kickoff_instance,
    )

    api_client.token_authenticate(user=user_1)

    # act
    response = api_client.get(
        f'/templates/{template_1.id}/fieldsets',
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == fieldset_1.id


def test_list_fieldsets__different_templates__ok(api_client):
    """List fieldsets filtered by template_id"""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template_1 = create_test_template(
        user=user,
        tasks_count=1,
    )
    fieldset_1 = create_test_fieldset_template(
        account=account,
        template=template_1,
        kickoff=template_1.kickoff_instance,
    )
    template_2 = create_test_template(
        user=user,
        tasks_count=1,
    )
    create_test_fieldset_template(
        account=account,
        template=template_2,
        kickoff=template_2.kickoff_instance,
    )

    api_client.token_authenticate(user=user)

    # act
    response = api_client.get(
        f'/templates/{template_1.id}/fieldsets',
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == fieldset_1.id


def test_list_fieldsets__rule_with_fields__ok(api_client):
    """List fieldsets for existing template returning rules mapping fields"""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(
        user=user,
        tasks_count=1,
    )
    kickoff = template.kickoff_instance
    rule_type = FieldSetRuleType.SUM_EQUAL
    rule_value = '10'
    fieldset = create_test_fieldset_template(
        account=account,
        template=template,
        kickoff=kickoff,
        name='Kickoff Fieldset',
        order=1,
        rule_type=rule_type,
        rule_value=rule_value,
    )
    field = fieldset.fields.get()
    rule = fieldset.rules.get()
    rule.fields.add(field)

    api_client.token_authenticate(user=user)

    # act
    response = api_client.get(
        f'/templates/{template.id}/fieldsets',
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    item_1 = response.data[0]

    assert len(item_1['rules']) == 1
    rules_data = item_1['rules']
    assert rules_data[0]['id'] == rule.id
    assert rules_data[0]['fields'] == [field.api_name]


def test_list_fieldsets__unauthenticated__unauthorized(api_client):
    """Unauthenticated request returns 401"""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(
        user=user,
        tasks_count=1,
    )

    # act
    response = api_client.get(f'/templates/{template.id}/fieldsets')

    # assert
    assert response.status_code == 401


def test_list_fieldsets__expired_sub__permission_denied(api_client):
    """Expired subscription returns 403"""

    # arrange
    account = create_test_account(
        plan=BillingPlanType.PREMIUM,
        plan_expiration=timezone.now() - timedelta(days=1),
    )
    user = create_test_owner(account=account)
    template = create_test_template(
        user=user,
        tasks_count=1,
    )

    api_client.token_authenticate(user=user)

    # act
    response = api_client.get(f'/templates/{template.id}/fieldsets')

    # assert
    assert response.status_code == 403
    assert response.data['detail'] == MSG_A_0035


def test_list_fieldsets__billing_plan__permission_denied(api_client):
    """Billing plan permission denied returns 403"""

    # arrange
    account = create_test_account(plan=None)
    user = create_test_owner(account=account)
    template = create_test_template(
        user=user,
        tasks_count=1,
    )

    api_client.token_authenticate(user=user)

    # act
    response = api_client.get(f'/templates/{template.id}/fieldsets')

    # assert
    assert response.status_code == 403
    assert response.data['detail'] == MSG_A_0041


def test_list_fieldsets__users_overlimit__permission_denied(api_client):
    """Users overlimited returns 403"""

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
    template = create_test_template(
        user=user,
        tasks_count=1,
    )

    api_client.token_authenticate(user=user)

    # act
    response = api_client.get(f'/templates/{template.id}/fieldsets')

    # assert
    assert response.status_code == 403
    assert response.data['detail'] == MSG_A_0037


def test_list_fieldsets__non_admin__permission_denied(api_client):
    """Non-admin non-owner user returns 403"""

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    template = create_test_template(
        user=owner,
        tasks_count=1,
    )
    user = create_test_not_admin(account=account)

    api_client.token_authenticate(user=user)

    # act
    response = api_client.get(f'/templates/{template.id}/fieldsets')

    # assert
    assert response.status_code == 403


def test_list_fieldsets__not_tpl_owner__permission_denied(api_client):
    """Template admin owner permission denied returns 403"""

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    template = create_test_template(
        user=owner,
        tasks_count=1,
    )
    user = create_test_admin(account=account)

    api_client.token_authenticate(user=user)

    # act
    response = api_client.get(f'/templates/{template.id}/fieldsets')

    # assert
    assert response.status_code == 403
    assert response.data['detail'] == messages.MSG_PT_0023


def test_list_fieldsets__not_existing_tpl__not_found(api_client):
    """Non-existent template returns 404"""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    nonexistent_id = 999999

    api_client.token_authenticate(user=user)

    # act
    response = api_client.get(f'/templates/{nonexistent_id}/fieldsets')

    # assert
    assert response.status_code == 404
