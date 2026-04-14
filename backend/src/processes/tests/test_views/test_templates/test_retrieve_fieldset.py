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
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_fieldset_template,
    create_test_not_admin,
    create_test_owner,
    create_test_template,
)

pytestmark = pytest.mark.django_db


def test_retrieve__unauthenticated__unauthorized(api_client):

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
    fieldset = create_test_fieldset_template(
        account=account,
        template=template,
        kickoff=template.kickoff_instance,
    )

    # act
    response = api_client.get(f'/templates/fieldsets/{fieldset.id}')

    # assert
    assert response.status_code == 401


def test_retrieve__expired_sub__permission_denied(api_client):

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
    fieldset = create_test_fieldset_template(
        account=account,
        template=template,
        kickoff=template.kickoff_instance,
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.get(f'/templates/fieldsets/{fieldset.id}')

    # assert
    assert response.status_code == 403
    assert response.data['detail'] == MSG_A_0035


def test_retrieve__billing_plan__permission_denied(api_client):

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
    fieldset = create_test_fieldset_template(
        account=account,
        template=template,
        kickoff=template.kickoff_instance,
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.get(f'/templates/fieldsets/{fieldset.id}')

    # assert
    assert response.status_code == 403
    assert response.data['detail'] == MSG_A_0041


def test_retrieve__users_overlimit__permission_denied(api_client):

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
    fieldset = create_test_fieldset_template(
        account=account,
        template=template,
        kickoff=template.kickoff_instance,
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.get(f'/templates/fieldsets/{fieldset.id}')

    # assert
    assert response.status_code == 403
    assert response.data['detail'] == MSG_A_0037


def test_retrieve__non_admin__permission_denied(api_client):

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
    fieldset = create_test_fieldset_template(
        account=account,
        template=template,
        kickoff=template.kickoff_instance,
    )
    user = create_test_not_admin(account=account)
    api_client.token_authenticate(user=user)

    # act
    response = api_client.get(f'/templates/fieldsets/{fieldset.id}')

    # assert
    assert response.status_code == 403


def test_retrieve__ok(api_client):

    """

    Retrieve existing fieldset

    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(
        user=user,
        tasks_count=1,
    )
    fieldset = create_test_fieldset_template(
        account=account,
        template=template,
        kickoff=template.kickoff_instance,
        name='My Fieldset',
        description='Fieldset description',
        order=3,
        layout=FieldSetLayout.HORIZONTAL,
        label_position=LabelPosition.LEFT,
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.get(f'/templates/fieldsets/{fieldset.id}')

    # assert
    assert response.status_code == 200
    assert response.data['id'] == fieldset.id
    assert response.data['name'] == 'My Fieldset'
    assert response.data['description'] == 'Fieldset description'
    assert response.data['order'] == 3
    assert response.data['layout'] == FieldSetLayout.HORIZONTAL
    assert response.data['label_position'] == LabelPosition.LEFT
    assert response.data['api_name'] == fieldset.api_name
    assert len(response.data['fields']) == 1
    assert response.data['fields'][0]['name'] == 'Fieldset field'
    assert response.data['fields'][0]['type'] == FieldType.STRING


def test_retrieve__not_existing__not_found(api_client):

    """

    Non-existent fieldset returns 404

    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    api_client.token_authenticate(user=user)
    nonexistent_id = 999999

    # act
    response = api_client.get(f'/templates/fieldsets/{nonexistent_id}')

    # assert
    assert response.status_code == 404


def test_retrieve__another_account__not_found(api_client):

    """

    Fieldset from another account returns 404

    """

    # arrange
    account_1 = create_test_account(name='Account 1')
    owner_1 = create_test_owner(account=account_1)
    template_1 = create_test_template(
        user=owner_1,
        tasks_count=1,
    )
    fieldset = create_test_fieldset_template(
        account=account_1,
        template=template_1,
        kickoff=template_1.kickoff_instance,
    )

    account_2 = create_test_account(name='Account 2')
    user_2 = create_test_owner(
        account=account_2,
        email='owner2@pneumatic.app',
    )
    api_client.token_authenticate(user=user_2)

    # act
    response = api_client.get(f'/templates/fieldsets/{fieldset.id}')

    # assert
    assert response.status_code == 404
