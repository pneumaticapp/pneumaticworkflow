
import pytest
from datetime import timedelta

from django.utils import timezone

from src.accounts.enums import BillingPlanType
from src.accounts.messages import MSG_A_0035, MSG_A_0037, MSG_A_0041
from src.processes.enums import (
    FieldSetRuleType,
)
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_admin,
    create_test_shared_fieldset,
    create_test_not_admin,
    create_test_owner,
    create_test_template,
)
from src.processes.models.templates.fieldset import FieldsetTemplate
from src.utils.validation import ErrorCode

pytestmark = pytest.mark.django_db


def test_list_fieldsets__all_data__ok(api_client):
    """List fieldsets returning all fields including title and order"""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    create_test_template(
        user=user,
        tasks_count=1,
    )
    rule_type = FieldSetRuleType.SUM_EQUAL
    rule_value = '10'
    fieldset = create_test_shared_fieldset(
        account=account,
        title='Fieldset Title',
        order=3,
        rule_type=rule_type,
        rule_value=rule_value,
    )
    field = fieldset.fields.get()
    rule = fieldset.rules.get()

    api_client.token_authenticate(user=user)

    # act
    response = api_client.get('/fieldsets')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    item_1 = response.data[0]
    assert item_1['id'] == fieldset.id
    assert item_1['api_name'] == fieldset.api_name
    assert item_1['name'] == fieldset.name
    assert item_1['title'] == 'Fieldset Title'
    assert item_1['order'] == 3
    assert item_1['description'] == ''
    assert item_1['layout'] == fieldset.layout
    assert item_1['label_position'] == fieldset.label_position

    assert len(item_1['rules']) == 1
    rules_data = item_1['rules']
    assert rules_data[0]['type'] == rule_type
    assert rules_data[0]['value'] == rule_value
    assert rules_data[0]['api_name'] == rule.api_name

    assert len(item_1['fields']) == 1
    fields_data = item_1['fields']
    assert fields_data[0]['name'] == field.name
    assert fields_data[0]['type'] == field.type
    assert fields_data[0]['api_name'] == field.api_name
    assert fields_data[0]['description'] == ''
    assert fields_data[0]['is_required'] is False
    assert fields_data[0]['is_hidden'] is False
    assert fields_data[0]['default'] == ''
    assert 'dataset' not in fields_data[0]
    assert 'selections' not in fields_data[0]


def test_list_fieldsets__shared_fieldset_has_rules_and_fields__ok(api_client):

    """List shared fieldsets returns rules and fields"""

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
    rule = fieldset.rules.get()

    api_client.token_authenticate(user=user)

    # act
    response = api_client.get('/fieldsets')

    # assert
    assert response.status_code == 200
    data = response.data[0]
    assert data['id'] == fieldset.id
    assert len(data['rules']) == 1
    assert data['rules'][0]['api_name'] == rule.api_name
    assert len(data['fields']) == 1
    assert data['fields'][0]['api_name'] == field.api_name


def test_list_fieldsets__pagination__ok(api_client):
    """Paginated list returns correct count and slice"""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    create_test_template(
        user=user,
        tasks_count=1,
    )
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

    item_1 = response.data['results'][0]
    assert item_1['id'] == fieldset_2.id

    item_2 = response.data['results'][1]
    assert item_2['id'] == fieldset_1.id


def test_list_fieldsets__different_accounts__ok(api_client):
    """List fieldsets filtered by account — other accounts excluded"""

    # arrange
    account_1 = create_test_account(name='Account 1')
    user_1 = create_test_owner(account=account_1)
    create_test_template(
        user=user_1,
        tasks_count=1,
    )
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
    """List fieldsets returning rules mapping to fields"""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    create_test_template(
        user=user,
        tasks_count=1,
    )
    rule_type = FieldSetRuleType.SUM_EQUAL
    rule_value = '10'
    fieldset = create_test_shared_fieldset(
        account=account,
        rule_type=rule_type,
        rule_value=rule_value,
    )
    field = fieldset.fields.get()
    rule = fieldset.rules.get()
    rule.fields.add(field)

    api_client.token_authenticate(user=user)

    # act
    response = api_client.get('/fieldsets')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    item_1 = response.data[0]

    assert len(item_1['rules']) == 1
    rules_data = item_1['rules']
    assert rules_data[0]['fields'] == [field.api_name]


def test_list_fieldsets__unauthenticated__unauthorized(api_client):
    """Unauthenticated request returns 401"""

    # act
    response = api_client.get('/fieldsets')

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

    api_client.token_authenticate(user=user)

    # act
    response = api_client.get('/fieldsets')

    # assert
    assert response.status_code == 403
    assert response.data['detail'] == MSG_A_0035


def test_list_fieldsets__billing_plan__permission_denied(api_client):
    """Billing plan permission denied returns 403"""

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

    api_client.token_authenticate(user=user)

    # act
    response = api_client.get('/fieldsets')

    # assert
    assert response.status_code == 403
    assert response.data['detail'] == MSG_A_0037


def test_list_fieldsets__non_admin__permission_denied(api_client):
    """Non-admin non-owner user returns 403"""

    # arrange
    account = create_test_account()
    create_test_owner(account=account)
    user = create_test_not_admin(account=account)

    api_client.token_authenticate(user=user)

    # act
    response = api_client.get('/fieldsets')

    # assert
    assert response.status_code == 403


def test_list_fieldsets__admin__ok(api_client):
    """Admin (non-owner) user can list fieldsets"""

    # arrange
    account = create_test_account()
    create_test_owner(account=account)
    user = create_test_admin(account=account)
    create_test_template(
        user=user,
        tasks_count=1,
    )
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
    create_test_template(
        user=user,
        tasks_count=1,
    )
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
    item_1 = response.data[0]
    assert item_1['id'] == fieldset_3.id
    item_2 = response.data[1]
    assert item_2['id'] == fieldset_2.id
    item_3 = response.data[2]
    assert item_3['id'] == fieldset_1.id


def test_list_fieldsets__ordering_name_asc__ok(api_client):

    """ ordering=name — ascending by name """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    create_test_template(
        user=user,
        tasks_count=1,
    )
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
    item_1 = response.data[0]
    assert item_1['id'] == fieldset_1.id
    assert item_1['name'] == 'Alpha'
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
    create_test_template(
        user=user,
        tasks_count=1,
    )
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
    item_1 = response.data[0]
    assert item_1['id'] == fieldset_3.id
    assert item_1['name'] == 'Gamma'
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
    create_test_template(
        user=user,
        tasks_count=1,
    )
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
    item_1 = response.data[0]
    assert item_1['id'] == fieldset_1.id
    item_2 = response.data[1]
    assert item_2['id'] == fieldset_2.id
    item_3 = response.data[2]
    assert item_3['id'] == fieldset_3.id


def test_list_fieldsets__ordering_date_desc__ok(api_client):

    """ ordering=-date — descending by date_created """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    create_test_template(
        user=user,
        tasks_count=1,
    )
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
    item_1 = response.data[0]
    assert item_1['id'] == fieldset_3.id
    item_2 = response.data[1]
    assert item_2['id'] == fieldset_2.id
    item_3 = response.data[2]
    assert item_3['id'] == fieldset_1.id


def test_list_fieldsets__no_pagination__ok(api_client):

    """ No pagination params — flat list response """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    create_test_template(
        user=user,
        tasks_count=1,
    )
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
    create_test_template(
        user=user,
        tasks_count=1,
    )
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
    create_test_template(
        user=user,
        tasks_count=1,
    )
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
    item_1 = response.data[0]
    assert item_1['id'] == fieldset_2.id
    item_2 = response.data[1]
    assert item_2['id'] == fieldset_1.id


def test_list_fieldsets__soft_deleted__ok(api_client):

    """ Soft-deleted fieldsets are excluded """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    create_test_template(
        user=user,
        tasks_count=1,
    )
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
