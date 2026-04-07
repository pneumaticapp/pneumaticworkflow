import pytest

from src.accounts.enums import BillingPlanType
from src.processes.enums import OwnerRole, OwnerType, FieldType
from src.processes.models.templates.fields import FieldTemplate, \
    FieldTemplateSelection
from src.processes.models.templates.owner import TemplateOwner
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_group,
    create_test_template,
    create_test_owner,
    create_test_dataset,
    create_test_admin,
)

pytestmark = pytest.mark.django_db


def test_titles_by_owners__owner_user__ok(api_client):
    """
    User who is a direct owner (type=user) should see the template.
    """

    # arrange
    user = create_test_owner()
    template = create_test_template(
        user=user,
        is_active=True,
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.get('/templates/titles-by-owners')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == template.id


def test_titles_by_owners__owner_group__ok(api_client):
    """
    User who is an owner via group membership should see the template.
    """

    # arrange
    account = create_test_account(plan=BillingPlanType.PREMIUM)
    owner = create_test_owner(account=account)
    group_member = create_test_admin(account=account)
    group = create_test_group(
        account=account,
        users=[group_member],
    )
    template = create_test_template(
        user=owner,
        is_active=True,
    )
    TemplateOwner.objects.create(
        role=OwnerRole.OWNER,
        template=template,
        account=account,
        type=OwnerType.GROUP,
        group=group,
    )
    api_client.token_authenticate(group_member)

    # act
    response = api_client.get('/templates/titles-by-owners')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == template.id


def test_titles_by_owners__starter_user__not_in_list(api_client):
    """
    User who is only a starter (not owner) should NOT see the template.
    """

    # arrange
    account = create_test_account(plan=BillingPlanType.PREMIUM)
    owner = create_test_owner(account=account)
    starter_user = create_test_admin(account=account)
    template = create_test_template(
        user=owner,
        is_active=True,
    )
    TemplateOwner.objects.create(
        role=OwnerRole.STARTER,
        template=template,
        account=account,
        type=OwnerType.USER,
        user_id=starter_user.id,
    )
    api_client.token_authenticate(starter_user)

    # act
    response = api_client.get('/templates/titles-by-owners')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 0


def test_titles_by_owners__viewer_user__not_in_list(api_client):
    """
    User who is only a viewer (not owner) should NOT see the template.
    """

    # arrange
    account = create_test_account(plan=BillingPlanType.PREMIUM)
    owner = create_test_owner(
        account=account,
        is_account_owner=True,
    )
    viewer_user = create_test_owner(
        account=account,
        email='viewer@test.test',
        is_account_owner=False,
    )
    template = create_test_template(
        user=owner,
        is_active=True,
    )
    TemplateOwner.objects.create(
        role=OwnerRole.VIEWER,
        template=template,
        account=account,
        type=OwnerType.USER,
        user_id=viewer_user.id,
    )
    api_client.token_authenticate(viewer_user)

    # act
    response = api_client.get('/templates/titles-by-owners')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 0


def test_titles_by_owners__starter_group__not_in_list(api_client):
    """
    User who is a starter via group (not owner) should NOT see the
    template.
    """

    # arrange
    account = create_test_account(plan=BillingPlanType.PREMIUM)
    owner = create_test_owner(
        account=account,
        is_account_owner=True,
    )
    starter_user = create_test_owner(
        account=account,
        email='starter@test.test',
        is_account_owner=False,
    )
    group = create_test_group(
        account=account,
        users=[starter_user],
    )
    template = create_test_template(
        user=owner,
        is_active=True,
    )
    TemplateOwner.objects.create(
        role=OwnerRole.STARTER,
        template=template,
        account=account,
        type=OwnerType.GROUP,
        group=group,
    )
    api_client.token_authenticate(starter_user)

    # act
    response = api_client.get('/templates/titles-by-owners')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 0


def test_titles_by_owners__pagination__ok(api_client):
    """
    Pagination should work correctly.
    """

    # arrange
    user = create_test_owner()
    api_client.token_authenticate(user)
    create_test_template(user, is_active=True)
    create_test_template(user, is_active=True)
    template = create_test_template(user, is_active=True)
    create_test_template(user, is_active=True)

    # act
    response = api_client.get(
        path='/templates/titles-by-owners',
        data={
            'limit': 1,
            'offset': 2,
            'ordering': 'date',
        },
    )

    # assert
    assert response.status_code == 200
    assert response.data['count'] == 4
    assert len(response.data['results']) == 1
    assert response.data['results'][0]['id'] == template.id


def test_titles_by_owners__ordering__ok(api_client):
    """
    Ordering by name should work correctly.
    """

    # arrange
    user = create_test_owner()
    template_a = create_test_template(user, name='Aa1')
    template_b = create_test_template(user, name='Bb2')
    api_client.token_authenticate(user)

    # act
    response = api_client.get('/templates/titles-by-owners?ordering=name')

    # assert
    assert response.status_code == 200
    assert response.data[0]['id'] == template_a.id
    assert response.data[1]['id'] == template_b.id


def test_titles_by_owners__search__ok(api_client):
    """
    Search should work correctly.
    Uses full word matching as PostgreSQL tsquery requires exact words.
    """

    # arrange
    user = create_test_owner()
    template = create_test_template(user, name='Searchable Template')
    create_test_template(user, name='Other Template')
    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        '/templates/titles-by-owners?search=Searchable',
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == template.id


def test_titles_by_owners__filter_is_active__ok(api_client):
    """
    Filter by is_active should work correctly.
    """

    # arrange
    user = create_test_owner()
    active_template = create_test_template(user, is_active=True)
    create_test_template(user, is_active=False)
    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        '/templates/titles-by-owners?is_active=true',
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == active_template.id


def test_titles_by_owners__multiple_owners__no_duplicates(api_client):
    """
    When user is owner both directly and via group,
    template should appear only once.
    """

    # arrange
    account = create_test_account(plan=BillingPlanType.PREMIUM)
    user = create_test_owner(
        account=account,
        is_account_owner=True,
    )
    group = create_test_group(
        account=account,
        users=[user],
    )
    template = create_test_template(
        user=user,
        is_active=True,
    )
    TemplateOwner.objects.create(
        role=OwnerRole.OWNER,
        template=template,
        account=account,
        type=OwnerType.GROUP,
        group=group,
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.get('/templates/titles-by-owners')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == template.id


def test_titles_by_owners__other_account__not_visible(api_client):
    """
    Templates from other accounts should not be visible.
    """

    # arrange
    other_user = create_test_owner(email='other@test.test')
    create_test_template(
        user=other_user,
        is_active=True,
    )
    user = create_test_owner()
    api_client.token_authenticate(user)

    # act
    response = api_client.get('/templates/titles-by-owners')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 0


def test_titles_by_owners__deleted_owner__not_in_list(api_client):
    """
    If owner record is deleted (is_deleted=True),
    user should not see the template.
    """

    # arrange
    user = create_test_owner()
    template = create_test_template(
        user=user,
        is_active=True,
    )
    TemplateOwner.objects.filter(
        template=template,
        user_id=user.id,
    ).update(is_deleted=True)
    api_client.token_authenticate(user)

    # act
    response = api_client.get('/templates/titles-by-owners')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 0


def test_titles_by_owners__kickoff_field_with_dataset__ok(api_client):

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    api_client.token_authenticate(user)
    dataset = create_test_dataset(account=account, items_count=1)
    dataset_item = dataset.items.first()
    template = create_test_template(
        user=user,
        tasks_count=1,
        is_active=True,
    )
    kickoff = template.kickoff_instance
    FieldTemplate.objects.create(
        name='Dropdown with dataset',
        type=FieldType.DROPDOWN,
        kickoff=kickoff,
        template=template,
        order=1,
        api_name='dropdown-field-1',
        account=user.account,
        dataset=dataset,
    )

    # act
    response = api_client.get('/templates/titles-by-owners')

    # assert
    assert response.status_code == 200
    fields = response.data[0]['kickoff']['fields']
    assert len(fields) == 1
    field_data = fields[0]
    assert field_data['type'] == FieldType.DROPDOWN
    assert field_data['selections'][0] == dataset_item.value


def test_titles_by_owners__kickoff_field_with_dataset_and_selections__ok(
    api_client,
):

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    api_client.token_authenticate(user)
    dataset = create_test_dataset(account=account, items_count=1)
    dataset_item = dataset.items.first()
    template = create_test_template(
        user=user,
        tasks_count=1,
        is_active=True,
    )
    kickoff = template.kickoff_instance
    field_template = FieldTemplate.objects.create(
        name='Dropdown',
        type=FieldType.DROPDOWN,
        kickoff=kickoff,
        template=template,
        order=1,
        api_name='dropdown-field-1',
        account=user.account,
        dataset=dataset,
    )
    selection = FieldTemplateSelection.objects.create(
        field_template=field_template,
        value='Some value',
        template=template,
    )

    # act
    response = api_client.get('/templates/titles-by-owners')

    # assert
    assert response.status_code == 200
    field_data = response.data[0]['kickoff']['fields'][0]
    assert len(field_data['selections']) == 2
    assert field_data['selections'][0] == selection.value
    assert field_data['selections'][1] == dataset_item.value
