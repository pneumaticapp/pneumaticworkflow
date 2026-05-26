import pytest
import pytz

from src.accounts.enums import (
    BillingPlanType,
    Language,
    LeaseLevel,
    UserDateFormat,
    UserFirstDayWeek,
    UserType,
)
from src.accounts.models import UserGroup
from src.processes.enums import OwnerType
from src.processes.models.templates.owner import TemplateOwner
from src.authentication.services.guest_auth import GuestJWTAuthService
from src.payment.enums import BillingPeriod
from src.processes.models.workflows.task import TaskPerformer
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_guest,
    create_test_template,
    create_test_user,
    create_test_workflow,
)
from src.utils.dates import date_format

pytestmark = pytest.mark.django_db


def test_context__ok(api_client):

    # arrange
    timezone = pytz.timezone('America/Anchorage')
    logo_lg = 'https://some-site/lg.jpg'
    plan = BillingPlanType.UNLIMITED
    period = BillingPeriod.WEEKLY
    tenant_name = 'Some tenant'
    account = create_test_account(
        logo_lg=logo_lg,
        plan=plan,
        period=period,
        tenant_name=tenant_name,
    )
    user = create_test_user(
        account=account,
        tz=str(timezone),
        language=Language.de,
        date_fmt=UserDateFormat.PY_USA_24,
        date_fdw=UserFirstDayWeek.FRIDAY,
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.get('/auth/context')

    # assert
    assert response.status_code == 200
    data = response.data
    assert data['id'] == user.id
    assert data['type'] == UserType.USER
    assert data['email'] == user.email
    assert data['first_name'] == user.first_name
    assert data['last_name'] == user.last_name
    assert data['email'] == user.email
    assert data['phone'] == user.phone
    assert data['photo'] == user.photo
    assert data['date_joined'] == user.date_joined.strftime(date_format)
    assert data['date_joined_tsp'] == user.date_joined.timestamp()
    assert data['is_admin'] == user.is_admin
    assert data['is_account_owner'] == user.is_account_owner
    assert data['is_digest_subscriber'] == user.is_digest_subscriber
    is_tasks_digest_subscriber = user.is_tasks_digest_subscriber
    assert data['is_tasks_digest_subscriber'] == is_tasks_digest_subscriber
    is_newsletters_subscriber = user.is_newsletters_subscriber
    assert data['is_newsletters_subscriber'] == is_newsletters_subscriber
    is_offers_subscriber = user.is_special_offers_subscriber
    assert data['is_special_offers_subscriber'] == is_offers_subscriber
    is_cm_subscriber = user.is_comments_mentions_subscriber
    assert data['is_comments_mentions_subscriber'] == is_cm_subscriber
    assert data['is_new_tasks_subscriber'] == user.is_new_tasks_subscriber
    assert data['is_complete_tasks_subscriber'] == (
        user.is_complete_tasks_subscriber
    )
    assert data['is_supermode'] is False
    assert data['language'] == user.language
    assert data['timezone'] == user.timezone
    assert data['date_fmt'] == UserDateFormat.MAP_TO_API[user.date_fmt]
    assert data['date_fdw'] == user.date_fdw

    assert data['account']['id'] == account.id
    assert data['account']['name'] == account.name
    assert data['account']['tenant_name'] == account.tenant_name
    assert data['account']['date_joined'] == (
        account.date_joined.strftime(date_format)
    )
    assert data['account']['date_joined_tsp'] == (
        account.date_joined.timestamp()
    )
    assert data['account']['is_verified'] == account.is_verified
    assert data['account']['lease_level'] == LeaseLevel.STANDARD
    assert data['account']['logo_lg'] == logo_lg
    assert data['account']['logo_sm'] is None
    assert data['account']['active_users'] == 1
    assert data['account']['tenants_active_users'] == 0
    assert data['account']['max_users'] == account.max_users
    assert data['account']['is_subscribed'] is True
    assert data['account']['billing_plan'] == plan
    assert data['account']['billing_sync'] is True
    assert data['account']['billing_period'] == period
    assert data['account']['plan_expiration'] == (
        account.plan_expiration.strftime(date_format)
    )
    assert data['account']['plan_expiration_tsp'] == (
        account.plan_expiration.timestamp()
    )
    assert data['account']['trial_is_active'] == account.trial_is_active
    assert data['account']['trial_ended'] == account.trial_ended
    assert data['has_workflow_viewer_access'] is False
    assert data['has_workflow_starter_access'] is False


def test_context__guest__ok(api_client):

    # arrange
    owner_timezone = pytz.timezone('America/Anchorage')
    account = create_test_account()
    owner = create_test_user(
        account=account,
        email='owner@test.test',
        is_account_owner=True,
        tz=str(owner_timezone),
        date_fmt=UserDateFormat.PY_USA_24,
        date_fdw=UserFirstDayWeek.FRIDAY,
    )
    guest = create_test_guest(account=account)
    workflow = create_test_workflow(
        owner,
        tasks_count=1,
    )
    task = workflow.tasks.first()
    TaskPerformer.objects.create(
        task_id=task.id,
        user_id=guest.id,
    )
    str_token = GuestJWTAuthService.get_str_token(
        task_id=task.id,
        user_id=guest.id,
        account_id=account.id,
    )

    # act
    response = api_client.get(
        '/auth/context',
        **{'X-Guest-Authorization': str_token},
    )

    # assert
    assert response.status_code == 200
    data = response.data
    assert data['id'] == guest.id
    assert data['type'] == UserType.GUEST
    assert data['language'] == owner.language
    assert data['timezone'] == owner.timezone
    assert data['date_fmt'] == UserDateFormat.MAP_TO_API[owner.date_fmt]
    assert data['date_fdw'] == owner.date_fdw
    assert data['has_workflow_viewer_access'] is False
    assert data['has_workflow_starter_access'] is False


def test_context__disable_billing_sync__ok(api_client):

    # arrange
    account = create_test_account(billing_sync=False)
    user = create_test_user(account=account)
    api_client.token_authenticate(user)

    # act
    response = api_client.get('/auth/context')

    # assert
    assert response.status_code == 200
    assert response.data['account']['billing_sync'] is False


def test_context__user_has_workflow_viewer_access_as_owner__ok(api_client):

    # arrange
    account = create_test_account()
    user = create_test_user(account=account)
    create_test_template(user, tasks_count=0)
    api_client.token_authenticate(user)

    # act
    response = api_client.get('/auth/context')

    # assert
    assert response.status_code == 200
    data = response.data
    assert data['has_workflow_viewer_access'] is True
    assert data['has_workflow_starter_access'] is True


def test_context__user_has_workflow_viewer_access_as_viewer__ok(api_client):

    # arrange
    account = create_test_account()
    owner = create_test_user(
        account=account,
        email='owner@test.test',
        is_account_owner=True,
    )
    user = create_test_user(
        account=account,
        email='user@test.test',
    )
    template = create_test_template(owner, tasks_count=0)
    TemplateOwner.objects.create(
        role='viewer',
        template=template,
        account=account,
        type=OwnerType.USER,
        user_id=user.id,
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.get('/auth/context')

    # assert
    assert response.status_code == 200
    data = response.data
    assert data['has_workflow_viewer_access'] is True
    assert data['has_workflow_starter_access'] is True


def test_context__user_has_workflow_starter_access_only__ok(api_client):

    # arrange
    account = create_test_account()
    owner = create_test_user(
        account=account,
        email='owner@test.test',
        is_account_owner=True,
    )
    user = create_test_user(
        account=account,
        email='user@test.test',
    )
    template = create_test_template(owner, tasks_count=0)
    TemplateOwner.objects.create(
        role='starter',
        template=template,
        account=account,
        type=OwnerType.USER,
        user_id=user.id,
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.get('/auth/context')

    # assert
    assert response.status_code == 200
    data = response.data
    assert data['has_workflow_viewer_access'] is False
    assert data['has_workflow_starter_access'] is True


def test_context__user_has_no_workflow_access__ok(api_client):

    # arrange
    account = create_test_account()
    owner = create_test_user(
        account=account,
        email='owner@test.test',
        is_account_owner=True,
    )
    user = create_test_user(
        account=account,
        email='user@test.test',
    )
    create_test_template(owner, tasks_count=0)
    api_client.token_authenticate(user)

    # act
    response = api_client.get('/auth/context')

    # assert
    assert response.status_code == 200
    data = response.data
    assert data['has_workflow_viewer_access'] is False
    assert data['has_workflow_starter_access'] is False


def test_context__user_has_workflow_access_via_group_as_owner__ok(
    api_client,
):
    # arrange
    account = create_test_account()
    owner = create_test_user(
        account=account,
        email='owner@test.test',
        is_account_owner=True,
    )
    user = create_test_user(
        account=account,
        email='user@test.test',
    )
    group = UserGroup.objects.create(
        name='Test Group',
        account=account,
    )
    group.users.add(user)
    template = create_test_template(owner, tasks_count=0)
    TemplateOwner.objects.create(
        template=template,
        account=account,
        type=OwnerType.GROUP,
        group_id=group.id,
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.get('/auth/context')

    # assert
    assert response.status_code == 200
    data = response.data
    assert data['has_workflow_viewer_access'] is True
    assert data['has_workflow_starter_access'] is True


def test_context__user_has_workflow_access_via_group_as_viewer__ok(
    api_client,
):

    # arrange
    account = create_test_account()
    owner = create_test_user(
        account=account,
        email='owner@test.test',
        is_account_owner=True,
    )
    user = create_test_user(
        account=account,
        email='user@test.test',
    )
    group = UserGroup.objects.create(
        name='Test Group',
        account=account,
    )
    group.users.add(user)
    template = create_test_template(owner, tasks_count=0)
    TemplateOwner.objects.create(
        role='viewer',
        template=template,
        account=account,
        type=OwnerType.GROUP,
        group_id=group.id,
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.get('/auth/context')

    # assert
    assert response.status_code == 200
    data = response.data
    assert data['has_workflow_viewer_access'] is True
    assert data['has_workflow_starter_access'] is True


def test_context__user_has_workflow_access_via_group_as_starter__ok(
    api_client,
):

    # arrange
    account = create_test_account()
    owner = create_test_user(
        account=account,
        email='owner@test.test',
        is_account_owner=True,
    )
    user = create_test_user(
        account=account,
        email='user@test.test',
    )
    group = UserGroup.objects.create(
        name='Test Group',
        account=account,
    )
    group.users.add(user)
    template = create_test_template(owner, tasks_count=0)
    TemplateOwner.objects.create(
        role='starter',
        template=template,
        account=account,
        type=OwnerType.GROUP,
        group_id=group.id,
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.get('/auth/context')

    # assert
    assert response.status_code == 200
    data = response.data
    assert data['has_workflow_viewer_access'] is False
    assert data['has_workflow_starter_access'] is True


def test_context__user_multiple_templates_mixed_access__ok(api_client):

    # arrange
    account = create_test_account()
    owner = create_test_user(
        account=account,
        email='owner@test.test',
        is_account_owner=True,
    )
    user = create_test_user(
        account=account,
        email='user@test.test',
    )
    template1 = create_test_template(owner, tasks_count=0)
    template2 = create_test_template(owner, tasks_count=0)
    create_test_template(owner, tasks_count=0)
    TemplateOwner.objects.create(
        role='viewer',
        template=template1,
        account=account,
        type=OwnerType.USER,
        user_id=user.id,
    )
    TemplateOwner.objects.create(
        role='starter',
        template=template2,
        account=account,
        type=OwnerType.USER,
        user_id=user.id,
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.get('/auth/context')

    # assert
    assert response.status_code == 200
    data = response.data
    assert data['has_workflow_viewer_access'] is True
    assert data['has_workflow_starter_access'] is True


def test_context__template_access_cache_works__ok(api_client):

    # arrange
    account = create_test_account()
    user = create_test_user(account=account)
    create_test_template(user, tasks_count=0)
    api_client.token_authenticate(user)

    # act
    response = api_client.get('/auth/context')

    # assert
    assert response.status_code == 200
    data = response.data
    assert data['has_workflow_viewer_access'] is True
    assert data['has_workflow_starter_access'] is True
