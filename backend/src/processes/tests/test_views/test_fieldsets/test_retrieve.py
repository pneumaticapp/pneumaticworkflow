import pytest
from datetime import timedelta

from django.utils import timezone

from src.accounts.enums import BillingPlanType
from src.accounts.messages import MSG_A_0035, MSG_A_0037, MSG_A_0041
from src.processes.enums import FieldSetRuleOperator, FieldSetRuleType
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_shared_fieldset,
    create_test_not_admin,
    create_test_owner,
)

pytestmark = pytest.mark.django_db


def test_retrieve__fieldset_all_data__ok(api_client):
    """Retrieve existing fieldset"""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    rule_type = FieldSetRuleType.SUM_EQUAL
    rule_value = '10'
    fieldset = create_test_shared_fieldset(
        account=account,
        rule_type=rule_type,
        rule_value=rule_value,
    )
    field = fieldset.fields.get()
    ruleset = fieldset.rulesets.get()
    ruleset.fields.add(field)
    group_or = ruleset.groups_or.first()
    group_and = group_or.groups_and.first()
    api_client.token_authenticate(user=user)

    # act
    response = api_client.get(f'/fieldsets/{fieldset.id}')

    # assert
    assert response.status_code == 200
    assert response.data['id'] == fieldset.id
    assert response.data['api_name'] == fieldset.api_name
    assert response.data['name'] == fieldset.name
    assert response.data['title'] == fieldset.title
    assert response.data['description'] == fieldset.description
    assert response.data['order'] == fieldset.order
    assert response.data['layout'] == fieldset.layout
    assert response.data['label_position'] == fieldset.label_position

    assert len(response.data['rules']) == 1
    rule_resp = response.data['rules'][0]
    assert rule_resp['type'] == ruleset.type
    assert rule_resp['api_name'] == ruleset.api_name
    assert rule_resp['fields'] == [field.api_name]
    assert len(rule_resp['group_or']) == 1
    assert rule_resp['group_or'][0]['api_name'] == group_or.api_name
    assert len(rule_resp['group_or'][0]['group_and']) == 1
    group_and_resp = rule_resp['group_or'][0]['group_and'][0]
    assert group_and_resp['api_name'] == group_and.api_name
    assert group_and_resp['operator'] == FieldSetRuleOperator.SUM_EQUAL
    assert group_and_resp['value'] == rule_value

    assert len(response.data['fields']) == 1
    assert response.data['fields'][0]['name'] == field.name
    assert response.data['fields'][0]['description'] == ''
    assert response.data['fields'][0]['type'] == field.type
    assert response.data['fields'][0]['is_required'] == field.is_required
    assert response.data['fields'][0]['is_hidden'] == field.is_hidden
    assert response.data['fields'][0]['api_name'] == field.api_name
    assert response.data['fields'][0]['default'] == field.default
    assert response.data['fields'][0]['order'] == field.order


def test_retrieve__fieldset_rule_with_fields__ok(api_client):

    # arrange
    account_1 = create_test_account(name='Account 1')
    user_1 = create_test_owner(account=account_1)
    fieldset = create_test_shared_fieldset(
        account=account_1,
        rule_type=FieldSetRuleType.SUM_EQUAL,
        rule_value='10',
    )
    field = fieldset.fields.get()
    ruleset = fieldset.rulesets.get()
    ruleset.fields.add(field)
    group_and = ruleset.groups_or.first().groups_and.first()

    api_client.token_authenticate(user=user_1)

    # act
    response = api_client.get(f'/fieldsets/{fieldset.id}')

    # assert
    assert response.status_code == 200
    assert response.data['id'] == fieldset.id
    assert len(response.data['rules']) == 1
    rule_resp = response.data['rules'][0]
    assert rule_resp['type'] == ruleset.type
    assert rule_resp['api_name'] == ruleset.api_name
    assert rule_resp['fields'] == [field.api_name]
    assert rule_resp['group_or'][0]['group_and'][0]['operator'] == (
        group_and.operator
    )
    assert rule_resp['group_or'][0]['group_and'][0]['value'] == group_and.value


def test_retrieve__unauthenticated__unauthorized(api_client):
    """Unauthenticated request returns 401"""

    # arrange
    account = create_test_account()
    create_test_owner(account=account)
    fieldset = create_test_shared_fieldset(
        account=account,
    )

    # act
    response = api_client.get(f'/fieldsets/{fieldset.id}')

    # assert
    assert response.status_code == 401


def test_retrieve__expired_sub__permission_denied(api_client):
    """Expired subscription returns 403"""

    # arrange
    account = create_test_account(
        plan=BillingPlanType.PREMIUM,
        plan_expiration=timezone.now() - timedelta(days=1),
    )
    user = create_test_owner(account=account)
    fieldset = create_test_shared_fieldset(
        account=account,
    )

    api_client.token_authenticate(user=user)

    # act
    response = api_client.get(f'/fieldsets/{fieldset.id}')

    # assert
    assert response.status_code == 403
    assert response.data['detail'] == MSG_A_0035


def test_retrieve__billing_plan__permission_denied(api_client):
    """Billing plan permission denied returns 403"""

    # arrange
    account = create_test_account(plan=None)
    user = create_test_owner(account=account)
    fieldset = create_test_shared_fieldset(
        account=account,
    )

    api_client.token_authenticate(user=user)

    # act
    response = api_client.get(f'/fieldsets/{fieldset.id}')

    # assert
    assert response.status_code == 403
    assert response.data['detail'] == MSG_A_0041


def test_retrieve__users_overlimit__permission_denied(api_client):
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
    fieldset = create_test_shared_fieldset(
        account=account,
    )

    api_client.token_authenticate(user=user)

    # act
    response = api_client.get(f'/fieldsets/{fieldset.id}')

    # assert
    assert response.status_code == 403
    assert response.data['detail'] == MSG_A_0037


def test_retrieve__non_admin__permission_denied(api_client):
    """Non-admin non-owner user returns 403"""

    # arrange
    account = create_test_account()
    create_test_owner(account=account)
    fieldset = create_test_shared_fieldset(
        account=account,
    )
    user = create_test_not_admin(account=account)

    api_client.token_authenticate(user=user)

    # act
    response = api_client.get(f'/fieldsets/{fieldset.id}')

    # assert
    assert response.status_code == 403


def test_retrieve__not_existing__not_found(api_client):
    """Non-existent fieldset returns 404"""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    nonexistent_id = 999999

    api_client.token_authenticate(user=user)

    # act
    response = api_client.get(f'/fieldsets/{nonexistent_id}')

    # assert
    assert response.status_code == 404


def test_retrieve__another_account__not_found(api_client):

    """Fieldset from another account returns 404"""

    # arrange
    account_1 = create_test_account(name='Account 1')
    create_test_owner(account=account_1)
    fieldset = create_test_shared_fieldset(
        account=account_1,
    )

    account_2 = create_test_account(name='Account 2')
    user_2 = create_test_owner(
        account=account_2,
        email='owner2@pneumatic.app',
    )

    api_client.token_authenticate(user=user_2)

    # act
    response = api_client.get(f'/fieldsets/{fieldset.id}')

    # assert
    assert response.status_code == 404


def test_retrieve__not_shared__not_found(api_client):

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    fieldset = create_test_shared_fieldset(
        account=account,
        rule_type=FieldSetRuleType.SUM_EQUAL,
        rule_value='10',
    )
    fieldset.is_shared = False
    fieldset.save()

    api_client.token_authenticate(user=user)

    # act
    response = api_client.get(f'/fieldsets/{fieldset.id}')

    # assert
    assert response.status_code == 404
