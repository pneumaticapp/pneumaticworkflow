import pytest
from datetime import timedelta

from django.utils import timezone

from src.accounts.enums import BillingPlanType
from src.accounts.messages import MSG_A_0035, MSG_A_0037, MSG_A_0041
from src.processes.enums import (
    FieldSetLayout,
    FieldType,
    LabelPosition,
)
from src.processes.messages import template as messages
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_admin,
    create_test_fieldset,
    create_test_not_admin,
    create_test_owner,
    create_test_template,
)

pytestmark = pytest.mark.django_db


def test_list_fieldsets__unauthenticated__unauthorized(api_client):

    """

    Unauthenticated request returns 401

    """

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

    """

    Expired subscription returns 403

    """

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

    """

    Billing plan permission denied returns 403

    """

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

    """

    Users overlimited returns 403

    """

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

    """

    Non-admin non-owner user returns 403

    """

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

    """

    Template admin owner permission denied returns 403

    """

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


def test_list_fieldsets__ok(api_client):

    """

    List fieldsets for existing template

    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(
        user=user,
        tasks_count=1,
    )
    kickoff = template.kickoff_instance
    fieldset_1 = create_test_fieldset(
        account=account,
        template=template,
        kickoff=kickoff,
        name='Kickoff Fieldset',
        order=1,
    )
    task = template.tasks.first()
    fieldset_2 = create_test_fieldset(
        account=account,
        template=template,
        task=task,
        name='Task Fieldset',
        order=2,
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.get(
        f'/templates/{template.id}/fieldsets',
        data={'limit': 100},
    )

    # assert
    assert response.status_code == 200
    assert response.data['count'] == 2

    # ordered by -id (newest first)
    item_1 = response.data['results'][0]
    assert item_1['id'] == fieldset_2.id
    assert item_1['name'] == 'Task Fieldset'
    assert item_1['order'] == 2
    assert item_1['layout'] == FieldSetLayout.VERTICAL
    assert item_1['label_position'] == LabelPosition.TOP
    assert item_1['api_name'] == fieldset_2.api_name
    assert len(item_1['fields']) == 1
    assert item_1['fields'][0]['name'] == 'Fieldset field'
    assert item_1['fields'][0]['type'] == FieldType.STRING

    item_2 = response.data['results'][1]
    assert item_2['id'] == fieldset_1.id
    assert item_2['name'] == 'Kickoff Fieldset'
    assert item_2['order'] == 1
    assert item_2['layout'] == FieldSetLayout.VERTICAL
    assert item_2['label_position'] == LabelPosition.TOP
    assert item_2['api_name'] == fieldset_1.api_name
    assert len(item_2['fields']) == 1
    assert item_2['fields'][0]['name'] == 'Fieldset field'
    assert item_2['fields'][0]['type'] == FieldType.STRING


def test_list_fieldsets__filter_by_account__ok(api_client):

    """

    List fieldsets filtered by account

    """

    # arrange
    account_1 = create_test_account(name='Account 1')
    user_1 = create_test_owner(account=account_1)
    template_1 = create_test_template(
        user=user_1,
        tasks_count=1,
    )
    fieldset_1 = create_test_fieldset(
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
    create_test_fieldset(
        account=account_2,
        template=template_2,
        kickoff=template_2.kickoff_instance,
        name='Account 2 Fieldset',
    )
    api_client.token_authenticate(user=user_1)

    # act
    response = api_client.get(
        f'/templates/{template_1.id}/fieldsets',
        data={'limit': 100},
    )

    # assert
    assert response.status_code == 200
    assert response.data['count'] == 1
    assert response.data['results'][0]['id'] == fieldset_1.id
    assert response.data['results'][0]['name'] == 'Account 1 Fieldset'


def test_list_fieldsets__filter_by_template__ok(api_client):

    """

    List fieldsets filtered by template_id

    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template_1 = create_test_template(
        user=user,
        tasks_count=1,
        name='Template 1',
    )
    fieldset_1 = create_test_fieldset(
        account=account,
        template=template_1,
        kickoff=template_1.kickoff_instance,
        name='Template 1 Fieldset',
    )
    template_2 = create_test_template(
        user=user,
        tasks_count=1,
        name='Template 2',
    )
    create_test_fieldset(
        account=account,
        template=template_2,
        kickoff=template_2.kickoff_instance,
        name='Template 2 Fieldset',
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.get(
        f'/templates/{template_1.id}/fieldsets',
        data={'limit': 100},
    )

    # assert
    assert response.status_code == 200
    assert response.data['count'] == 1
    assert response.data['results'][0]['id'] == fieldset_1.id
    assert response.data['results'][0]['name'] == 'Template 1 Fieldset'


def test_list_fieldsets__not_existing_tpl__not_found(api_client):

    """

    Non-existent template returns 404

    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    api_client.token_authenticate(user=user)
    nonexistent_id = 999999

    # act
    response = api_client.get(f'/templates/{nonexistent_id}/fieldsets')

    # assert
    assert response.status_code == 404
