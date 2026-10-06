from datetime import date, datetime, timezone

import pytest
from django.contrib.auth import get_user_model

from src.accounts.enums import AbsenceStatus, BillingPlanType, UserType
from src.authentication.enums import AuthTokenType
from src.logs.events.entities import Actor, EventObject
from src.logs.events.enums import (
    AccountEvents,
    AdminEvents,
    ApiKeyEvents,
    BillingEvents,
    DatasetEvents,
    EventCategory,
    GroupEvents,
    LoginFailedReason,
    LogoutReason,
    TaskEvents,
    TemplateEvents,
    TemplateSource,
    UserEvents,
    WebhookEvents,
    WorkflowEvents,
)
from src.logs.events.services import NO_ACCOUNT, AuditEventService
from src.processes.enums import FieldSetRuleType, PresetType, WorkflowEventType
from src.processes.models.templates.template import Template, TemplateDraft
from src.processes.models.workflows.checklist import ChecklistSelection
from src.processes.models.workflows.event import WorkflowEvent
from src.processes.models.workflows.task import Task
from src.processes.models.workflows.workflow import Workflow
from src.processes.tests.fixtures import (
    create_checklist_template,
    create_test_account,
    create_test_admin,
    create_test_api_key,
    create_test_dataset,
    create_test_event,
    create_test_group,
    create_test_kickoff_field,
    create_test_not_admin,
    create_test_owner,
    create_test_shared_fieldset,
    create_test_system_template,
    create_test_template,
    create_test_template_preset,
    create_test_workflow,
)

UserModel = get_user_model()
pytestmark = pytest.mark.django_db


@pytest.mark.parametrize('backend', [None, ''])
def test_user_logged_in__logs_disabled__no_queries(
    fake_stream,
    settings,
    django_assert_num_queries,
    backend,
):
    """An uncached account must not be loaded for a disabled event."""

    # arrange
    owner = create_test_owner()
    user = UserModel.objects.get(id=owner.id)
    settings.LOGS_BACKEND = backend

    # act
    with django_assert_num_queries(0):
        AuditEventService.user_logged_in(
            user=user,
            source='email',
        )

    # assert
    assert fake_stream.events == []


@pytest.mark.parametrize('backend', [None, ''])
def test_user_updated__logs_disabled__no_queries(
    fake_stream,
    settings,
    django_assert_num_queries,
    backend,
):
    """Groups and subordinate QuerySets remain unevaluated."""

    # arrange
    owner = create_test_owner()
    group = create_test_group(
        account=owner.account,
        users=[owner],
    )
    target = UserModel.objects.get(id=owner.id)
    subordinates = UserModel.objects.filter(id=owner.id)
    settings.LOGS_BACKEND = backend

    # act
    with django_assert_num_queries(0):
        AuditEventService.user_updated(
            user=owner,
            auth_type=None,
            target=target,
            update_kwargs={},
            user_groups=[group.id],
            subordinates=subordinates,
        )

    # assert
    assert fake_stream.events == []


@pytest.mark.parametrize('backend', [None, ''])
@pytest.mark.parametrize(
    'method',
    [
        'group_created',
        'group_updated',
        'group_deleted',
    ],
)
def test_group_events__logs_disabled__no_queries(
    fake_stream,
    settings,
    django_assert_num_queries,
    backend,
    method,
):
    """Neither members nor the uncached account are loaded."""

    # arrange
    owner = create_test_owner()
    group = create_test_group(
        account=owner.account,
        users=[owner],
    )
    group = type(group).objects.get(id=group.id)
    kwargs = {'users_ids': [owner.id]}
    if method == 'group_updated':
        kwargs['update_kwargs'] = {}
    settings.LOGS_BACKEND = backend

    # act
    with django_assert_num_queries(0):
        getattr(AuditEventService, method)(
            user=owner,
            auth_type=None,
            group=group,
            **kwargs,
        )

    # assert
    assert fake_stream.events == []


@pytest.mark.parametrize('backend', [None, ''])
@pytest.mark.parametrize('method', ['api_key_created', 'api_key_revoked'])
def test_api_key_events__logs_disabled__no_queries(
    fake_stream,
    settings,
    django_assert_num_queries,
    backend,
    method,
):
    """An uncached key must not load its user or account."""

    # arrange
    owner = create_test_owner()
    api_key = create_test_api_key(user=owner)
    api_key = type(api_key).objects.get(id=api_key.id)
    settings.LOGS_BACKEND = backend

    # act
    with django_assert_num_queries(0):
        getattr(AuditEventService, method)(
            user=owner,
            auth_type=None,
            api_key=api_key,
        )

    # assert
    assert fake_stream.events == []


@pytest.mark.parametrize('backend', [None, ''])
@pytest.mark.parametrize(
    'method',
    [
        'template_preset_created',
        'template_preset_updated',
        'template_preset_deleted',
        'template_preset_set_default',
    ],
)
def test_preset_events__logs_disabled__no_queries(
    fake_stream,
    settings,
    django_assert_num_queries,
    backend,
    method,
):
    """Precomputed preset metadata must not read the template."""

    # arrange
    owner = create_test_owner()
    template = create_test_template(user=owner)
    preset = create_test_template_preset(
        template=template,
        author=owner,
    )
    preset = type(preset).objects.get(id=preset.id)
    kwargs = {'update_kwargs': {}} if method.endswith('updated') else {}
    settings.LOGS_BACKEND = backend

    # act
    with django_assert_num_queries(0):
        getattr(AuditEventService, method)(
            user=owner,
            auth_type=None,
            preset=preset,
            **kwargs,
        )

    # assert
    assert fake_stream.events == []


@pytest.mark.parametrize('backend', [None, ''])
@pytest.mark.parametrize('method', ['workflow_run', 'workflow_updated'])
def test_workflow_events__logs_disabled__no_queries(
    fake_stream,
    settings,
    django_assert_num_queries,
    backend,
    method,
):
    """An uncached workflow must not load template or account metadata."""

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(
        user=owner,
        tasks_count=1,
    )
    workflow = Workflow.objects.get(id=workflow.id)
    kwargs = {'update_kwargs': {}} if method.endswith('updated') else {}
    settings.LOGS_BACKEND = backend

    # act
    with django_assert_num_queries(0):
        getattr(AuditEventService, method)(
            user=owner,
            auth_type=None,
            workflow=workflow,
            **kwargs,
        )

    # assert
    assert fake_stream.events == []


@pytest.mark.parametrize('backend', [None, ''])
def test_sub_workflow_run__logs_disabled__no_queries(
    fake_stream,
    settings,
    django_assert_num_queries,
    backend,
):
    """The whole ancestor relationship remains lazy."""

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(
        user=owner,
        tasks_count=1,
    )
    sub_workflow = create_test_workflow(
        user=owner,
        tasks_count=1,
        ancestor_task=workflow.tasks.get(number=1),
    )
    sub_workflow = Workflow.objects.get(id=sub_workflow.id)
    settings.LOGS_BACKEND = backend

    # act
    with django_assert_num_queries(0):
        AuditEventService.sub_workflow_run(
            user=owner,
            auth_type=None,
            sub_workflow=sub_workflow,
        )

    # assert
    assert fake_stream.events == []


@pytest.mark.parametrize('backend', [None, ''])
def test_task_start__logs_disabled__no_queries(
    fake_stream,
    settings,
    django_assert_num_queries,
    backend,
):
    """System events must not load workflow or account metadata."""

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(
        user=owner,
        tasks_count=1,
    )
    task = Task.objects.get(workflow=workflow, number=1)
    settings.LOGS_BACKEND = backend

    # act
    with django_assert_num_queries(0):
        AuditEventService.task_start(task=task)

    # assert
    assert fake_stream.events == []


@pytest.mark.parametrize('backend', [None, ''])
@pytest.mark.parametrize('method', ['comment_created', 'comment_updated'])
def test_comment_events__logs_disabled__no_queries(
    fake_stream,
    settings,
    django_assert_num_queries,
    backend,
    method,
):
    """Comment metadata must not load the related workflow or task."""

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(
        user=owner,
        tasks_count=1,
    )
    comment = create_test_event(
        workflow=workflow,
        user=owner,
        type_event=WorkflowEventType.COMMENT,
    )
    comment = WorkflowEvent.objects.get(id=comment.id)
    settings.LOGS_BACKEND = backend

    # act
    with django_assert_num_queries(0):
        getattr(AuditEventService, method)(
            user=owner,
            auth_type=None,
            comment=comment,
        )

    # assert
    assert fake_stream.events == []


@pytest.mark.parametrize('backend', [None, ''])
@pytest.mark.parametrize(
    'method',
    [
        'checklist_item_marked',
        'checklist_item_unmarked',
    ],
)
def test_checklist_events__logs_disabled__no_queries(
    fake_stream,
    settings,
    django_assert_num_queries,
    backend,
    method,
):
    """Deferred identifiers must not load checklist and task relations."""

    # arrange
    owner = create_test_owner()
    template = create_test_template(
        user=owner,
        tasks_count=1,
    )
    create_checklist_template(task_template=template.tasks.get(number=1))
    workflow = create_test_workflow(
        user=owner,
        template=template,
    )
    selection = ChecklistSelection.objects.get(
        checklist__task__workflow=workflow,
        api_name='cl-selection-1',
    )
    settings.LOGS_BACKEND = backend

    # act
    with django_assert_num_queries(0):
        getattr(AuditEventService, method)(
            user=owner,
            auth_type=None,
            selection=selection,
        )

    # assert
    assert fake_stream.events == []


def test_user_logged_in__request_context__login_event_with_the_address(
    fake_stream,
    request_context,
):
    """The address, the browser and the request id come from the
    context the middleware published; who acts and how they were
    authenticated come from the caller."""

    # arrange
    user = create_test_owner()

    # act
    AuditEventService.user_logged_in(
        user=user,
        source='email',
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.type == UserEvents.LOGIN
    assert event.category == EventCategory.USERS
    assert event.account_id == user.account_id
    assert event.actor == Actor(
        id=user.id,
        email=user.email,
        user_type=UserType.USER,
    )
    assert event.auth_type == AuthTokenType.USER
    assert event.object == EventObject(
        type=EventCategory.USERS,
        id=user.id,
        name=user.email,
    )
    assert event.payload == {'source': 'email'}
    assert event.ip == '9.9.9.9'
    assert event.user_agent == 'Chrome'
    assert event.request_id == 'ctx-request'


def test_user_signed_up__no_context__signup_event_without_the_address(
    fake_stream,
):

    # arrange
    user = create_test_owner()

    # act
    AuditEventService.user_signed_up(
        user=user,
        source='google',
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.type == UserEvents.SIGNUP
    assert event.category == EventCategory.USERS
    assert event.account_id == user.account_id
    assert event.actor == Actor(
        id=user.id,
        email=user.email,
        user_type=UserType.USER,
    )
    assert event.auth_type == AuthTokenType.USER
    assert event.object == EventObject(
        type=EventCategory.USERS,
        id=user.id,
        name=user.email,
    )
    assert event.payload == {'source': 'google'}
    assert event.ip is None
    assert event.user_agent is None
    assert event.request_id is None


def test_login_failed__email__normalized_email_and_no_account(fake_stream):
    """The attempt is anonymous, no actor and no auth type, and the
    event belongs to no account: a failed sign in is the bucket
    an alert on a brute force burst is built on."""

    # arrange
    email = ' Ann@Test.test '

    # act
    AuditEventService.login_failed(
        reason=LoginFailedReason.BAD_CREDENTIALS,
        email=email,
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.type == UserEvents.LOGIN_FAILED
    assert event.category == EventCategory.USERS
    assert event.account_id == NO_ACCOUNT
    assert event.actor is None
    assert event.auth_type is None
    assert event.object == EventObject(
        type=EventCategory.USERS,
        name=str(email or '').strip().lower(),
    )
    assert event.payload == {
        'email': 'ann@test.test',
        'reason': LoginFailedReason.BAD_CREDENTIALS,
    }


def test_login_failed__no_email__empty_string(fake_stream):

    # arrange
    email = None

    # act
    AuditEventService.login_failed(
        reason=LoginFailedReason.SSO_REQUIRED,
        email=email,
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.payload == {
        'email': '',
        'reason': LoginFailedReason.SSO_REQUIRED,
    }


def test_login_failed__email_not_a_string__string_in_the_payload(fake_stream):
    """The sign in form hands over whatever the client sent as the
    username, a number included: the event keeps it as text
    instead of breaking the answer."""

    # arrange
    email = 1

    # act
    AuditEventService.login_failed(
        reason=LoginFailedReason.BAD_CREDENTIALS,
        email=email,
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.payload == {
        'email': '1',
        'reason': LoginFailedReason.BAD_CREDENTIALS,
    }


def test_user_logged_out__api_key__logout_event_with_the_auth_type(
    fake_stream,
):

    # arrange
    user = create_test_owner()

    # act
    AuditEventService.user_logged_out(
        user=user,
        auth_type=AuthTokenType.API,
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.type == UserEvents.LOGOUT
    assert event.account_id == user.account_id
    assert event.actor == Actor(
        id=user.id,
        email=user.email,
        user_type=UserType.USER,
    )
    assert event.auth_type == AuthTokenType.API
    assert event.object == EventObject(
        type=EventCategory.USERS,
        id=user.id,
        name=user.email,
    )
    assert event.payload == {}


def test_user_logged_out_by_provider__target__no_actor(fake_stream):
    """The identity provider ended the sessions, not the person."""

    # arrange
    target = create_test_owner()

    # act
    AuditEventService.user_logged_out_by_provider(
        target=target,
        source='okta',
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.type == UserEvents.LOGOUT
    assert event.account_id == target.account_id
    assert event.actor is None
    assert event.auth_type is None
    assert event.object == EventObject(
        type=EventCategory.USERS,
        id=target.id,
        name=target.email,
    )
    assert event.payload == {
        'source': 'okta',
        'reason': LogoutReason.IDENTITY_PROVIDER,
    }


def test_user_logged_out_by_provider__no_target__no_account_bucket(
    fake_stream,
):
    """Auth0 calls the logout from the browser without a token."""

    # arrange
    target = None

    # act
    AuditEventService.user_logged_out_by_provider(
        target=target,
        source='auth0',
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.type == UserEvents.LOGOUT
    assert event.account_id == NO_ACCOUNT
    assert event.actor is None
    assert event.auth_type is None
    assert event.object == EventObject(
        type=EventCategory.USERS,
        id=None,
    )
    assert event.payload == {
        'source': 'auth0',
        'reason': LogoutReason.IDENTITY_PROVIDER,
    }


def test_superuser_logged_in_as__target__target_account_and_email(fake_stream):

    # arrange
    staff = create_test_owner(email='staff@test.test')
    target = create_test_owner(email='target@test.test')

    # act
    AuditEventService.superuser_logged_in_as(
        user=staff,
        auth_type=AuthTokenType.USER,
        target=target,
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.type == UserEvents.LOGIN_AS
    assert event.account_id == target.account_id
    assert event.actor == Actor(
        id=staff.id,
        email=staff.email,
        user_type=UserType.USER,
    )
    assert event.auth_type == AuthTokenType.USER
    assert event.object == EventObject(
        type=EventCategory.USERS,
        id=target.id,
        name=target.email,
    )
    assert event.payload == {'target_email': 'target@test.test'}


def test_tenant_logged_in_as__master_user__tenant_account_object(fake_stream):

    # arrange
    master = create_test_owner()
    tenant_account = create_test_account(
        name='Tenant',
        master_account=master.account,
    )

    # act
    AuditEventService.tenant_logged_in_as(
        user=master,
        auth_type=AuthTokenType.USER,
        tenant_account=tenant_account,
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.type == AccountEvents.TENANT_LOGIN_AS
    assert event.account_id == tenant_account.id
    assert event.actor == Actor(
        id=master.id,
        email=master.email,
        user_type=UserType.USER,
    )
    assert event.auth_type == AuthTokenType.USER
    assert event.object == EventObject(
        type=EventCategory.ACCOUNTS,
        id=tenant_account.id,
        name=tenant_account.tenant_name or tenant_account.name,
    )
    assert event.payload == {
        'master_account_id': master.account_id,
        'master_account_name': master.account.name,
        'tenant_name': tenant_account.tenant_name,
    }


def test_password_reset_requested__known_address__no_actor(fake_stream):

    # arrange
    target = create_test_owner()

    # act
    AuditEventService.password_reset_requested(target=target)
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.type == UserEvents.PASSWORD_RESET_REQUEST
    assert event.category == EventCategory.USERS
    assert event.account_id == target.account_id
    assert event.actor is None
    assert event.auth_type is None
    assert event.object == EventObject(
        type=EventCategory.USERS,
        id=target.id,
        name=target.email,
    )
    assert event.payload == {'target_email': target.email}


def test_password_reset__user__user_of_the_link_acts(fake_stream):

    # arrange
    user = create_test_owner()

    # act
    AuditEventService.password_reset(user=user)
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.type == UserEvents.PASSWORD_RESET
    assert event.account_id == user.account_id
    assert event.actor == Actor(
        id=user.id,
        email=user.email,
        user_type=UserType.USER,
    )
    assert event.auth_type is None
    assert event.object == EventObject(
        type=EventCategory.USERS,
        id=user.id,
        name=user.email,
    )
    assert event.payload == {}


def test_password_changed__api_key__api_auth_type(fake_stream):

    # arrange
    user = create_test_owner()

    # act
    AuditEventService.password_changed(
        user=user,
        auth_type=AuthTokenType.API,
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.type == UserEvents.PASSWORD_CHANGE
    assert event.account_id == user.account_id
    assert event.actor == Actor(
        id=user.id,
        email=user.email,
        user_type=UserType.USER,
    )
    assert event.auth_type == AuthTokenType.API
    assert event.object == EventObject(
        type=EventCategory.USERS,
        id=user.id,
        name=user.email,
    )
    assert event.payload == {}


def test_password_set__own_password__password_change_event(fake_stream):

    # arrange
    user = create_test_owner()

    # act
    AuditEventService.password_set(
        user=user,
        auth_type=AuthTokenType.USER,
        target=user,
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.type == UserEvents.PASSWORD_CHANGE
    assert event.account_id == user.account_id
    assert event.actor == Actor(
        id=user.id,
        email=user.email,
        user_type=UserType.USER,
    )
    assert event.auth_type == AuthTokenType.USER
    assert event.object == EventObject(
        type=EventCategory.USERS,
        id=user.id,
        name=user.email,
    )
    assert event.payload == {}


def test_password_set__another_person__password_set_event_with_target(
    fake_stream,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    target = create_test_not_admin(
        account=account,
        email='ann@test.test',
    )

    # act
    AuditEventService.password_set(
        user=owner,
        auth_type=AuthTokenType.USER,
        target=target,
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.type == UserEvents.PASSWORD_SET
    assert event.category == EventCategory.USERS
    assert event.account_id == account.id
    assert event.actor == Actor(
        id=owner.id,
        email=owner.email,
        user_type=UserType.USER,
    )
    assert event.auth_type == AuthTokenType.USER
    assert event.object == EventObject(
        type=EventCategory.USERS,
        id=target.id,
        name=target.email,
    )
    assert event.payload == {'target_email': 'ann@test.test'}


def test_password_set__no_user__no_actor_and_target_account(fake_stream):

    # arrange
    target = create_test_owner()

    # act
    AuditEventService.password_set(
        user=None,
        auth_type=None,
        target=target,
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.type == UserEvents.PASSWORD_SET
    assert event.account_id == target.account_id
    assert event.actor is None
    assert event.auth_type is None
    assert event.object == EventObject(
        type=EventCategory.USERS,
        id=target.id,
        name=target.email,
    )
    assert event.payload == {'target_email': target.email}


def test_user_created__admin__target_in_the_payload(fake_stream):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    target = create_test_not_admin(
        account=account,
        email='new@test.test',
    )

    # act
    AuditEventService.user_created(
        user=owner,
        auth_type=AuthTokenType.USER,
        target=target,
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.type == UserEvents.CREATE
    assert event.category == EventCategory.USERS
    assert event.account_id == account.id
    assert event.actor == Actor(
        id=owner.id,
        email=owner.email,
        user_type=UserType.USER,
    )
    assert event.auth_type == AuthTokenType.USER
    assert event.object == EventObject(
        type=EventCategory.USERS,
        id=target.id,
        name=target.email,
    )
    assert event.payload == {
        'target_email': 'new@test.test',
        'is_admin': False,
    }


def test_user_updated__update_kwargs__kwargs_in_the_payload(fake_stream):
    """The record holds what the request sent, next to the address
    of the person it was sent for."""

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    target = create_test_not_admin(
        account=account,
        email='new@test.test',
    )

    # act
    AuditEventService.user_updated(
        user=owner,
        auth_type=AuthTokenType.USER,
        target=target,
        update_kwargs={'email': 'new@test.test', 'first_name': 'Ann'},
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.type == UserEvents.UPDATE
    assert event.category == EventCategory.USERS
    assert event.account_id == account.id
    assert event.actor == Actor(
        id=owner.id,
        email=owner.email,
        user_type=UserType.USER,
    )
    assert event.auth_type == AuthTokenType.USER
    assert event.object == EventObject(
        type=EventCategory.USERS,
        id=target.id,
        name=target.email,
    )
    assert event.payload == {
        'target_email': 'new@test.test',
        'email': 'new@test.test',
        'first_name': 'Ann',
    }


def test_user_updated__target_of_another_account__target_account(fake_stream):
    """The record goes into the account of the person edited, not
    into the one of whoever edits them."""

    # arrange
    owner = create_test_owner(email='owner@test.test')
    target_account = create_test_account(name='Other')
    target = create_test_not_admin(
        account=target_account,
        email='ann@test.test',
    )

    # act
    AuditEventService.user_updated(
        user=owner,
        auth_type=AuthTokenType.USER,
        target=target,
        update_kwargs={'first_name': 'Ann'},
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.type == UserEvents.UPDATE
    assert event.account_id == target_account.id
    assert event.actor == Actor(
        id=owner.id,
        email=owner.email,
        user_type=UserType.USER,
    )
    assert event.object == EventObject(
        type=EventCategory.USERS,
        id=target.id,
        name=target.email,
    )


@pytest.mark.parametrize('use_objects', (True, False))
def test_user_updated__manager_and_groups_sent__ids_in_the_payload(
    fake_stream,
    use_objects,
):
    """Related rows keep their identifiers and readable names."""

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    manager = create_test_admin(account=account)
    subordinate = create_test_not_admin(
        account=account,
        email='sub@test.test',
    )
    target = create_test_not_admin(account=account)
    group = create_test_group(account=account)
    target.user_groups.set([group.id])
    groups = [group] if use_objects else [group.id]

    # act
    AuditEventService.user_updated(
        user=owner,
        auth_type=AuthTokenType.USER,
        target=target,
        update_kwargs={'manager': manager},
        user_groups=groups,
        subordinates=[subordinate],
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.type == UserEvents.UPDATE
    assert event.payload == {
        'target_email': target.email,
        'manager': {'id': manager.id, 'name': str(manager)},
        'user_groups': [group.id],
        'subordinates': [subordinate.id],
        'groups': {str(group.id): group.name},
        'subordinate_users': {str(subordinate.id): subordinate.email},
    }


def test_user_updated__empty_groups_and_subordinates__empty_lists(fake_stream):
    """An empty list is a request that took every group away: it is
    named, unlike a list the request did not send at all."""

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    target = create_test_not_admin(account=account)
    target.user_groups.set([])

    # act
    AuditEventService.user_updated(
        user=owner,
        auth_type=AuthTokenType.USER,
        target=target,
        update_kwargs={},
        user_groups=[],
        subordinates=[],
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.payload == {
        'target_email': target.email,
        'user_groups': [],
        'subordinates': [],
        'groups': {},
        'subordinate_users': {},
    }


def test_user_updated__nothing_sent__update_event_with_the_target(fake_stream):
    """The service writes what it was asked to save, even when the
    request sent nothing: no admin permission and no password
    either, so the update is the only record."""

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    target = create_test_not_admin(
        account=account,
        email='ann@test.test',
    )

    # act
    AuditEventService.user_updated(
        user=owner,
        auth_type=AuthTokenType.USER,
        target=target,
        update_kwargs={},
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.type == UserEvents.UPDATE
    assert event.object == EventObject(
        type=EventCategory.USERS,
        id=target.id,
        name=target.email,
    )
    assert event.payload == {'target_email': 'ann@test.test'}


def test_user_updated__is_admin_sent__update_and_admin_toggle_events(
    fake_stream,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    target = create_test_admin(
        account=account,
        email='ann@test.test',
    )

    # act
    AuditEventService.user_updated(
        user=owner,
        auth_type=AuthTokenType.USER,
        target=target,
        update_kwargs={'is_admin': True},
    )

    # assert
    assert len(fake_stream.events) == 2
    update = fake_stream.events[0][1]
    toggle = fake_stream.events[1][1]
    assert update.type == UserEvents.UPDATE
    assert update.payload == {
        'target_email': 'ann@test.test',
        'is_admin': True,
    }
    assert toggle.type == UserEvents.ADMIN_TOGGLE
    assert toggle.account_id == account.id
    assert toggle.actor == Actor(
        id=owner.id,
        email=owner.email,
        user_type=UserType.USER,
    )
    assert toggle.auth_type == AuthTokenType.USER
    assert toggle.object == EventObject(
        type=EventCategory.USERS,
        id=target.id,
        name=target.email,
    )
    assert toggle.payload == {
        'is_admin': True,
        'target_email': 'ann@test.test',
    }


def test_user_updated__password_set__update_and_password_set_events(
    fake_stream,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    target = create_test_not_admin(
        account=account,
        email='ann@test.test',
    )

    # act
    AuditEventService.user_updated(
        user=owner,
        auth_type=AuthTokenType.USER,
        target=target,
        update_kwargs={},
        is_password_set=True,
    )

    # assert
    assert len(fake_stream.events) == 2
    update = fake_stream.events[0][1]
    password_set = fake_stream.events[1][1]
    assert update.type == UserEvents.UPDATE
    assert update.payload == {'target_email': 'ann@test.test'}
    assert password_set.type == UserEvents.PASSWORD_SET
    assert password_set.account_id == account.id
    assert password_set.object == EventObject(
        type=EventCategory.USERS,
        id=target.id,
        name=target.email,
    )
    assert password_set.payload == {'target_email': 'ann@test.test'}


def test_user_updated__is_admin_revoked__admin_toggle_event(fake_stream):
    """The key sent is what counts, not its value: taking the admin
    permission away is watched as closely as granting it."""

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    target = create_test_not_admin(
        account=account,
        email='ann@test.test',
    )

    # act
    AuditEventService.user_updated(
        user=owner,
        auth_type=AuthTokenType.API,
        target=target,
        update_kwargs={'is_admin': False},
    )

    # assert
    assert len(fake_stream.events) == 2
    update = fake_stream.events[0][1]
    toggle = fake_stream.events[1][1]
    assert update.type == UserEvents.UPDATE
    assert update.payload == {
        'target_email': 'ann@test.test',
        'is_admin': False,
    }
    assert toggle.type == UserEvents.ADMIN_TOGGLE
    assert toggle.auth_type == AuthTokenType.API
    assert toggle.payload == {
        'is_admin': False,
        'target_email': 'ann@test.test',
    }


def test_user_updated__is_admin_differs_from_target__toggle_of_target(
    fake_stream,
):
    """The update names what the request sent, the admin toggle what
    the user holds: the service calls it after the save, so the
    two agree there. A target not saved yet shows which one each
    record reads."""

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    target = create_test_admin(
        account=account,
        email='ann@test.test',
    )

    # act
    AuditEventService.user_updated(
        user=owner,
        auth_type=AuthTokenType.USER,
        target=target,
        update_kwargs={'is_admin': False},
    )

    # assert
    assert len(fake_stream.events) == 2
    update = fake_stream.events[0][1]
    toggle = fake_stream.events[1][1]
    assert update.type == UserEvents.UPDATE
    assert update.payload == {
        'target_email': 'ann@test.test',
        'is_admin': False,
    }
    assert toggle.type == UserEvents.ADMIN_TOGGLE
    assert toggle.payload == {
        'is_admin': True,
        'target_email': 'ann@test.test',
    }


def test_user_updated__is_admin_and_password__three_events(fake_stream):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    target = create_test_admin(
        account=account,
        email='ann@test.test',
    )

    # act
    AuditEventService.user_updated(
        user=owner,
        auth_type=AuthTokenType.USER,
        target=target,
        update_kwargs={'is_admin': True},
        is_password_set=True,
    )

    # assert
    assert len(fake_stream.events) == 3
    assert fake_stream.events[0][1].type == UserEvents.UPDATE
    assert fake_stream.events[1][1].type == UserEvents.ADMIN_TOGGLE
    assert fake_stream.events[2][1].type == UserEvents.PASSWORD_SET


def test_user_updated__own_password__password_change_event(fake_stream):
    """A person editing their own profile changes their own password:
    that is not the record an alert watches for."""

    # arrange
    owner = create_test_owner(email='ann@test.test')

    # act
    AuditEventService.user_updated(
        user=owner,
        auth_type=AuthTokenType.USER,
        target=owner,
        update_kwargs={},
        is_password_set=True,
    )

    # assert
    assert len(fake_stream.events) == 2
    update = fake_stream.events[0][1]
    password_change = fake_stream.events[1][1]
    assert update.type == UserEvents.UPDATE
    assert password_change.type == UserEvents.PASSWORD_CHANGE
    assert password_change.object == EventObject(
        type=EventCategory.USERS,
        id=owner.id,
        name=owner.email,
    )
    assert password_change.payload == {}


def test_user_admin_toggled__admin_revoked__is_admin_false_in_payload(
    fake_stream,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    target = create_test_not_admin(
        account=account,
        email='ann@test.test',
    )

    # act
    AuditEventService.user_admin_toggled(
        user=owner,
        auth_type=AuthTokenType.API,
        target=target,
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.type == UserEvents.ADMIN_TOGGLE
    assert event.category == EventCategory.USERS
    assert event.account_id == account.id
    assert event.actor == Actor(
        id=owner.id,
        email=owner.email,
        user_type=UserType.USER,
    )
    assert event.auth_type == AuthTokenType.API
    assert event.object == EventObject(
        type=EventCategory.USERS,
        id=target.id,
        name=target.email,
    )
    assert event.payload == {
        'is_admin': False,
        'target_email': 'ann@test.test',
    }


def test_user_admin_toggled__target_of_another_account__target_account(
    fake_stream,
):

    # arrange
    owner = create_test_owner(email='owner@test.test')
    target_account = create_test_account(name='Other')
    target = create_test_admin(
        account=target_account,
        email='ann@test.test',
    )

    # act
    AuditEventService.user_admin_toggled(
        user=owner,
        auth_type=AuthTokenType.USER,
        target=target,
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.type == UserEvents.ADMIN_TOGGLE
    assert event.account_id == target_account.id
    assert event.actor == Actor(
        id=owner.id,
        email=owner.email,
        user_type=UserType.USER,
    )
    assert event.object == EventObject(
        type=EventCategory.USERS,
        id=target.id,
        name=target.email,
    )


def test_user_deactivated__admin__target_in_the_payload(fake_stream):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    target = create_test_not_admin(
        account=account,
        email='ann@test.test',
    )

    # act
    AuditEventService.user_deactivated(
        user=owner,
        auth_type=AuthTokenType.USER,
        target=target,
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.type == UserEvents.DEACTIVATE
    assert event.category == EventCategory.USERS
    assert event.account_id == account.id
    assert event.actor == Actor(
        id=owner.id,
        email=owner.email,
        user_type=UserType.USER,
    )
    assert event.auth_type == AuthTokenType.USER
    assert event.object == EventObject(
        type=EventCategory.USERS,
        id=target.id,
        name=target.email,
    )
    assert event.payload == {'target_email': 'ann@test.test'}


def test_user_deactivated__person_themselves__person_acts(fake_stream):
    """A declined invite and a transfer to another account: the
    person is the actor and the object at once."""

    # arrange
    target = create_test_owner(email='ann@test.test')

    # act
    AuditEventService.user_deactivated(
        user=target,
        auth_type=None,
        target=target,
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.type == UserEvents.DEACTIVATE
    assert event.account_id == target.account_id
    assert event.actor == Actor(
        id=target.id,
        email='ann@test.test',
        user_type=UserType.USER,
    )
    assert event.auth_type is None
    assert event.object == EventObject(
        type=EventCategory.USERS,
        id=target.id,
        name=target.email,
    )
    assert event.payload == {'target_email': 'ann@test.test'}


def test_user_deactivated__target_of_another_account__target_account(
    fake_stream,
):

    # arrange
    owner = create_test_owner(email='owner@test.test')
    target_account = create_test_account(name='Other')
    target = create_test_not_admin(
        account=target_account,
        email='ann@test.test',
    )

    # act
    AuditEventService.user_deactivated(
        user=owner,
        auth_type=AuthTokenType.USER,
        target=target,
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.type == UserEvents.DEACTIVATE
    assert event.account_id == target_account.id
    assert event.actor == Actor(
        id=owner.id,
        email=owner.email,
        user_type=UserType.USER,
    )
    assert event.object == EventObject(
        type=EventCategory.USERS,
        id=target.id,
        name=target.email,
    )


def test_user_transferred__new_user__previous_account_in_the_payload(
    fake_stream,
):
    """Into the journal of the account the person moved to."""

    # arrange
    prev_user = create_test_owner(email='prev@test.test')
    account = create_test_account()
    user = create_test_not_admin(
        account=account,
        email='ann@test.test',
    )

    # act
    AuditEventService.user_transferred(
        user=user,
        auth_type=AuthTokenType.USER,
        prev_user=prev_user,
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.type == UserEvents.TRANSFER
    assert event.category == EventCategory.USERS
    assert event.account_id == account.id
    assert event.actor == Actor(
        id=user.id,
        email=user.email,
        user_type=UserType.USER,
    )
    assert event.auth_type == AuthTokenType.USER
    assert event.object == EventObject(
        type=EventCategory.USERS,
        id=user.id,
        name=user.email,
    )
    assert event.payload == {
        'prev_account_id': prev_user.account_id,
        'prev_user_id': prev_user.id,
        'prev_account_name': prev_user.account.name,
        'prev_user_email': prev_user.email,
    }


def test_user_reassigned__old_group__group_object(fake_stream):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    new_user = create_test_not_admin(account=account)
    group = create_test_group(account=account)

    # act
    AuditEventService.user_reassigned(
        user=owner,
        auth_type=AuthTokenType.USER,
        old_group=group,
        new_user=new_user,
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.type == UserEvents.REASSIGN
    assert event.category == EventCategory.USERS
    assert event.account_id == account.id
    assert event.actor == Actor(
        id=owner.id,
        email=owner.email,
        user_type=UserType.USER,
    )
    assert event.auth_type == AuthTokenType.USER
    assert event.object == EventObject(
        type=EventCategory.USERS,
        id=group.id,
        name=group.name,
    )
    assert event.payload == {
        'old_user_id': None,
        'old_group_id': group.id,
        'new_user_id': new_user.id,
        'new_group_id': None,
        'old_user_email': None,
        'new_user_email': new_user.email,
        'old_group_name': group.name,
        'new_group_name': None,
    }


def test_user_reassigned__old_user__user_object(fake_stream):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    old_user = create_test_not_admin(account=account)
    new_group = create_test_group(account=account)

    # act
    AuditEventService.user_reassigned(
        user=owner,
        auth_type=AuthTokenType.USER,
        old_user=old_user,
        new_group=new_group,
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.type == UserEvents.REASSIGN
    assert event.object == EventObject(
        type=EventCategory.USERS,
        id=old_user.id,
        name=old_user.email,
    )
    assert event.payload == {
        'old_user_id': old_user.id,
        'old_group_id': None,
        'new_user_id': None,
        'new_group_id': new_group.id,
        'old_user_email': old_user.email,
        'new_user_email': None,
        'old_group_name': None,
        'new_group_name': new_group.name,
    }


def test_user_unsubscribed__email_type__user_of_the_link_acts(fake_stream):

    # arrange
    user = create_test_owner()

    # act
    AuditEventService.user_unsubscribed(
        user=user,
        email_type='digest',
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.type == UserEvents.UNSUBSCRIBE
    assert event.account_id == user.account_id
    assert event.actor == Actor(
        id=user.id,
        email=user.email,
        user_type=UserType.USER,
    )
    assert event.auth_type is None
    assert event.object == EventObject(
        type=EventCategory.USERS,
        id=user.id,
        name=user.email,
    )
    assert event.payload == {'email_type': 'digest'}


def test_vacation_activated__scheduled__no_actor_sorted_substitutes(
    fake_stream,
):
    """A scheduled task turns the vacation on: nobody acts, and the
    account is the one of the person on vacation."""

    # arrange
    target = create_test_owner(email='ann@test.test')
    substitute_1 = create_test_not_admin(
        account=target.account,
        email='substitute-1@test.test',
    )
    substitute_2 = create_test_not_admin(
        account=target.account,
        email='substitute-2@test.test',
    )
    substitute_3 = create_test_not_admin(
        account=target.account,
        email='substitute-3@test.test',
    )

    # act
    AuditEventService.vacation_activated(
        user=None,
        auth_type=None,
        target=target,
        substitute_users=[substitute_3, substitute_2, substitute_1],
        absence_status=AbsenceStatus.VACATION,
        start_date=date(2026, 9, 1),
        end_date=date(2026, 9, 14),
        delegated_tasks_count=3,
        is_update=False,
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.type == UserEvents.VACATION_ACTIVATE
    assert event.category == EventCategory.USERS
    assert event.account_id == target.account_id
    assert event.actor is None
    assert event.auth_type is None
    assert event.object == EventObject(
        type=EventCategory.USERS,
        id=target.id,
        name=target.email,
    )
    assert event.payload == {
        'target_email': 'ann@test.test',
        'substitute_user_ids': [
            substitute_1.id,
            substitute_2.id,
            substitute_3.id,
        ],
        'absence_status': AbsenceStatus.VACATION,
        'start_date': '2026-09-01',
        'end_date': '2026-09-14',
        'delegated_tasks_count': 3,
        'is_update': False,
        'substitute_users': {
            str(substitute_1.id): 'substitute-1@test.test',
            str(substitute_2.id): 'substitute-2@test.test',
            str(substitute_3.id): 'substitute-3@test.test',
        },
    }


def test_vacation_activated__admin__actor_and_target_account(fake_stream):
    """An admin turns the vacation of somebody else on: the admin
    acts, the record goes to the account of the person on
    vacation."""

    # arrange
    account = create_test_account()
    admin = create_test_admin(account=account)
    target = create_test_not_admin(
        account=account,
        email='ann@test.test',
    )

    # act
    AuditEventService.vacation_activated(
        user=admin,
        auth_type=AuthTokenType.USER,
        target=target,
        substitute_users=[admin],
        absence_status=AbsenceStatus.SICK_LEAVE,
        start_date=None,
        end_date=None,
        delegated_tasks_count=0,
        is_update=False,
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.type == UserEvents.VACATION_ACTIVATE
    assert event.account_id == target.account_id
    assert event.actor == Actor(
        id=admin.id,
        email=admin.email,
        user_type=UserType.USER,
    )
    assert event.auth_type == AuthTokenType.USER
    assert event.object == EventObject(
        type=EventCategory.USERS,
        id=target.id,
        name=target.email,
    )
    assert event.payload == {
        'target_email': 'ann@test.test',
        'substitute_user_ids': [admin.id],
        'absence_status': AbsenceStatus.SICK_LEAVE,
        'start_date': None,
        'end_date': None,
        'delegated_tasks_count': 0,
        'is_update': False,
        'substitute_users': {str(admin.id): admin.email},
    }


def test_vacation_activated__is_update__is_update_true_in_the_payload(
    fake_stream,
):
    """The dates or the substitutes of a vacation already on were
    changed: the same record, marked as an update."""

    # arrange
    target = create_test_owner(email='ann@test.test')
    substitute = create_test_not_admin(account=target.account)

    # act
    AuditEventService.vacation_activated(
        user=target,
        auth_type=AuthTokenType.USER,
        target=target,
        substitute_users=[substitute],
        absence_status=AbsenceStatus.VACATION,
        start_date=date(2026, 9, 1),
        end_date=date(2026, 9, 21),
        delegated_tasks_count=2,
        is_update=True,
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.type == UserEvents.VACATION_ACTIVATE
    assert event.payload == {
        'target_email': 'ann@test.test',
        'substitute_user_ids': [substitute.id],
        'absence_status': AbsenceStatus.VACATION,
        'start_date': '2026-09-01',
        'end_date': '2026-09-21',
        'delegated_tasks_count': 2,
        'is_update': True,
        'substitute_users': {str(substitute.id): substitute.email},
    }


def test_vacation_deactivated__admin__target_in_the_payload(fake_stream):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    target = create_test_not_admin(
        account=account,
        email='ann@test.test',
    )

    # act
    AuditEventService.vacation_deactivated(
        user=owner,
        auth_type=AuthTokenType.USER,
        target=target,
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.type == UserEvents.VACATION_DEACTIVATE
    assert event.category == EventCategory.USERS
    assert event.account_id == account.id
    assert event.actor == Actor(
        id=owner.id,
        email=owner.email,
        user_type=UserType.USER,
    )
    assert event.auth_type == AuthTokenType.USER
    assert event.object == EventObject(
        type=EventCategory.USERS,
        id=target.id,
        name=target.email,
    )
    assert event.payload == {'target_email': 'ann@test.test'}


def test_vacation_deactivated__target_of_another_account__target_account(
    fake_stream,
):

    # arrange
    owner = create_test_owner(email='owner@test.test')
    target_account = create_test_account(name='Other')
    target = create_test_not_admin(
        account=target_account,
        email='ann@test.test',
    )

    # act
    AuditEventService.vacation_deactivated(
        user=owner,
        auth_type=AuthTokenType.USER,
        target=target,
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.type == UserEvents.VACATION_DEACTIVATE
    assert event.account_id == target_account.id
    assert event.actor == Actor(
        id=owner.id,
        email=owner.email,
        user_type=UserType.USER,
    )
    assert event.object == EventObject(
        type=EventCategory.USERS,
        id=target.id,
        name=target.email,
    )


def test_account_updated__update_kwargs__kwargs_are_the_payload(fake_stream):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)

    # act
    AuditEventService.account_updated(
        user=owner,
        auth_type=AuthTokenType.USER,
        account=account,
        update_kwargs={'name': 'Acme', 'log_api_requests': True},
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.type == AccountEvents.UPDATE
    assert event.account_id == account.id
    assert event.actor == Actor(
        id=owner.id,
        email=owner.email,
        user_type=UserType.USER,
    )
    assert event.auth_type == AuthTokenType.USER
    assert event.object == EventObject(
        type=EventCategory.ACCOUNTS,
        id=account.id,
        name=account.name,
    )
    assert event.payload == {'name': 'Acme', 'log_api_requests': True}


def test_account_updated__nothing_sent__event_with_empty_payload(fake_stream):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)

    # act
    AuditEventService.account_updated(
        user=owner,
        auth_type=AuthTokenType.API,
        account=account,
        update_kwargs={},
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.type == AccountEvents.UPDATE
    assert event.auth_type == AuthTokenType.API
    assert event.payload == {}


def test_account_verified__user__user_of_the_link_acts(fake_stream):

    # arrange
    user = create_test_owner()

    # act
    AuditEventService.account_verified(user=user)
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.type == AccountEvents.VERIFY
    assert event.account_id == user.account_id
    assert event.actor == Actor(
        id=user.id,
        email=user.email,
        user_type=UserType.USER,
    )
    assert event.auth_type is None
    assert event.object == EventObject(
        type=EventCategory.ACCOUNTS,
        id=user.account_id,
        name=user.account.name,
    )
    assert event.payload == {}


def test_verification_resent__owner__account_object_with_target(fake_stream):

    # arrange
    owner = create_test_owner()

    # act
    AuditEventService.verification_resent(
        user=owner,
        auth_type=AuthTokenType.USER,
        account_owner=owner,
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.type == AccountEvents.VERIFICATION_RESEND
    assert event.category == EventCategory.ACCOUNTS
    assert event.account_id == owner.account_id
    assert event.actor == Actor(
        id=owner.id,
        email=owner.email,
        user_type=UserType.USER,
    )
    assert event.auth_type == AuthTokenType.USER
    assert event.object == EventObject(
        type=EventCategory.ACCOUNTS,
        id=owner.account_id,
        name=owner.account.name,
    )
    assert event.payload == {'target_email': owner.email}


def test_tenant_created__master_user__tenant_in_master_account(fake_stream):

    # arrange
    master = create_test_owner()
    tenant = create_test_account(
        master_account=master.account,
        tenant_name='Tenant',
        plan=BillingPlanType.PREMIUM,
    )

    # act
    AuditEventService.tenant_created(
        user=master,
        auth_type=AuthTokenType.USER,
        tenant=tenant,
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.type == AccountEvents.TENANT_CREATE
    assert event.account_id == master.account_id
    assert event.actor == Actor(
        id=master.id,
        email=master.email,
        user_type=UserType.USER,
    )
    assert event.auth_type == AuthTokenType.USER
    assert event.object == EventObject(
        type=EventCategory.ACCOUNTS,
        id=tenant.id,
        name=tenant.tenant_name or tenant.name,
    )
    assert event.payload == {
        'name': 'Tenant',
        'billing_plan': BillingPlanType.PREMIUM,
    }


def test_tenant_deleted__master_user__tenant_in_master_account(fake_stream):

    # arrange
    master = create_test_owner()
    tenant = create_test_account(
        master_account=master.account,
        tenant_name='Tenant',
        plan=BillingPlanType.PREMIUM,
    )

    # act
    AuditEventService.tenant_deleted(
        user=master,
        auth_type=AuthTokenType.USER,
        tenant=tenant,
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.type == AccountEvents.TENANT_DELETE
    assert event.account_id == master.account_id
    assert event.object == EventObject(
        type=EventCategory.ACCOUNTS,
        id=tenant.id,
        name=tenant.tenant_name or tenant.name,
    )
    assert event.payload == {
        'name': 'Tenant',
        'billing_plan': BillingPlanType.PREMIUM,
    }


def test_invite_created__transfer__target_and_no_object_id(fake_stream):
    """The id of an invite is the key that accepts it: it stays
    out of the journal."""

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    invited_user = create_test_not_admin(
        account=account,
        email='ann@test.test',
    )

    # act
    AuditEventService.invite_created(
        user=owner,
        auth_type=AuthTokenType.USER,
        invited_user=invited_user,
        is_transfer=True,
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.type == UserEvents.INVITE_CREATE
    assert event.category == EventCategory.USERS
    assert event.account_id == account.id
    assert event.actor == Actor(
        id=owner.id,
        email=owner.email,
        user_type=UserType.USER,
    )
    assert event.auth_type == AuthTokenType.USER
    assert event.object == EventObject(
        type=EventCategory.USERS,
        name=invited_user.email,
    )
    assert event.payload == {
        'target_email': 'ann@test.test',
        'invited_user_id': invited_user.id,
        'is_transfer': True,
    }


def test_invite_resent__api_key__target_and_no_object_id(fake_stream):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    invited_user = create_test_not_admin(
        account=account,
        email='ann@test.test',
    )

    # act
    AuditEventService.invite_resent(
        user=owner,
        auth_type=AuthTokenType.API,
        invited_user=invited_user,
        is_transfer=False,
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.type == UserEvents.INVITE_RESEND
    assert event.account_id == account.id
    assert event.actor == Actor(
        id=owner.id,
        email=owner.email,
        user_type=UserType.USER,
    )
    assert event.auth_type == AuthTokenType.API
    assert event.object == EventObject(
        type=EventCategory.USERS,
        name=invited_user.email,
    )
    assert event.payload == {
        'target_email': 'ann@test.test',
        'invited_user_id': invited_user.id,
        'is_transfer': False,
    }


def test_invite_accepted__invited_user__invited_person_acts(fake_stream):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    invited_user = create_test_not_admin(account=account)

    # act
    AuditEventService.invite_accepted(
        invited_user=invited_user,
        invited_by=owner,
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.type == UserEvents.INVITE_ACCEPT
    assert event.category == EventCategory.USERS
    assert event.account_id == account.id
    assert event.actor == Actor(
        id=invited_user.id,
        email=invited_user.email,
        user_type=UserType.USER,
    )
    assert event.auth_type is None
    assert event.object == EventObject(
        type=EventCategory.USERS,
        name=invited_user.email,
    )
    assert event.payload == {
        'invited_by_id': owner.id,
        'invited_by_email': owner.email,
    }


def test_group_created__users__name_and_users_ids(fake_stream):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    member = create_test_not_admin(account=account)
    group = create_test_group(
        account=account,
        name='Sales',
    )
    group.users.set([member.id])

    # act
    AuditEventService.group_created(
        user=owner,
        auth_type=AuthTokenType.USER,
        group=group,
        users_ids=[member.id],
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.type == GroupEvents.CREATE
    assert event.category == EventCategory.GROUPS
    assert event.account_id == account.id
    assert event.actor == Actor(
        id=owner.id,
        email=owner.email,
        user_type=UserType.USER,
    )
    assert event.auth_type == AuthTokenType.USER
    assert event.object == EventObject(
        type=EventCategory.GROUPS,
        id=group.id,
        name=group.name,
    )
    assert event.payload == {
        'name': 'Sales',
        'users_ids': [member.id],
        'users': {str(member.id): member.email},
    }


def test_group_created__no_users__users_ids_none(fake_stream):
    """A group created without members: the request sent none."""

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    group = create_test_group(
        account=account,
        name='Sales',
    )

    # act
    AuditEventService.group_created(
        user=owner,
        auth_type=AuthTokenType.USER,
        group=group,
        users_ids=None,
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.type == GroupEvents.CREATE
    assert event.payload == {'name': 'Sales', 'users_ids': None, 'users': {}}


def test_group_updated__users__kwargs_and_users_in_the_payload(fake_stream):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    member = create_test_not_admin(
        account=account,
        email='a@test.test',
    )
    group = create_test_group(
        account=account,
        name='Sales',
    )
    group.users.set([member.id])

    # act
    AuditEventService.group_updated(
        user=owner,
        auth_type=AuthTokenType.USER,
        group=group,
        update_kwargs={'name': 'Sales team'},
        users_ids=[member.id],
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.type == GroupEvents.UPDATE
    assert event.category == EventCategory.GROUPS
    assert event.account_id == account.id
    assert event.actor == Actor(
        id=owner.id,
        email=owner.email,
        user_type=UserType.USER,
    )
    assert event.auth_type == AuthTokenType.USER
    assert event.object == EventObject(
        type=EventCategory.GROUPS,
        id=group.id,
        name=group.name,
    )
    assert event.payload == {
        'name': 'Sales team',
        'users_ids': [member.id],
        'users': {str(member.id): member.email},
    }


def test_group_updated__no_users__users_ids_key_absent(fake_stream):
    """The members are named only when the request sent them."""

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    group = create_test_group(account=account)

    # act
    AuditEventService.group_updated(
        user=owner,
        auth_type=AuthTokenType.USER,
        group=group,
        update_kwargs={'photo': 'https://photos.test/sales.png'},
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.type == GroupEvents.UPDATE
    assert event.payload == {
        'photo': 'https://photos.test/sales.png',
        'name': group.name,
    }


def test_group_updated__empty_users__empty_list_named(fake_stream):
    """An empty list took every member away: it is named, unlike a
    list the request did not send."""

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    group = create_test_group(account=account)

    # act
    AuditEventService.group_updated(
        user=owner,
        auth_type=AuthTokenType.USER,
        group=group,
        update_kwargs={},
        users_ids=[],
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.type == GroupEvents.UPDATE
    assert event.payload == {'users_ids': [], 'users': {}, 'name': group.name}


def test_group_deleted__users__name_and_users_ids(fake_stream):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    member = create_test_not_admin(account=account)
    group = create_test_group(
        account=account,
        name='Sales',
    )
    group.users.set([member.id])

    # act
    AuditEventService.group_deleted(
        user=owner,
        auth_type=AuthTokenType.USER,
        group=group,
        users_ids=[member.id],
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.type == GroupEvents.DELETE
    assert event.category == EventCategory.GROUPS
    assert event.account_id == account.id
    assert event.object == EventObject(
        type=EventCategory.GROUPS,
        id=group.id,
        name=group.name,
    )
    assert event.payload == {
        'name': 'Sales',
        'users_ids': [member.id],
        'users': {str(member.id): member.email},
    }


def test_group_deleted__group_of_another_account__group_account(fake_stream):
    """The record goes into the account of the group, not into the
    one of whoever deletes it."""

    # arrange
    owner = create_test_owner(email='owner@test.test')
    group_account = create_test_account(name='Other')
    group = create_test_group(
        account=group_account,
        name='Sales',
    )

    # act
    AuditEventService.group_deleted(
        user=owner,
        auth_type=AuthTokenType.USER,
        group=group,
        users_ids=[],
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.type == GroupEvents.DELETE
    assert event.account_id == group_account.id
    assert event.actor == Actor(
        id=owner.id,
        email=owner.email,
        user_type=UserType.USER,
    )
    assert event.object == EventObject(
        type=EventCategory.GROUPS,
        id=group.id,
        name=group.name,
    )


def test_api_key_created__api_key__name_and_owner_without_the_token(
    fake_stream,
):
    """Neither the raw key nor the token row may reach the journal:
    the payload names the key and its owner and nothing else."""

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    api_key = create_test_api_key(
        user=owner,
        name='CI',
    )

    # act
    AuditEventService.api_key_created(
        user=owner,
        auth_type=AuthTokenType.USER,
        api_key=api_key,
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.type == ApiKeyEvents.CREATE
    assert event.category == EventCategory.API_KEYS
    assert event.account_id == account.id
    assert event.actor == Actor(
        id=owner.id,
        email=owner.email,
        user_type=UserType.USER,
    )
    assert event.auth_type == AuthTokenType.USER
    assert event.object == EventObject(
        type=EventCategory.API_KEYS,
        id=api_key.id,
        name=api_key.name,
    )
    assert event.payload == {
        'name': 'CI',
        'target_user_id': owner.id,
        'target_email': api_key.user.email,
    }


def test_api_key_revoked__api_key__name_and_owner_without_the_token(
    fake_stream,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    api_key = create_test_api_key(
        user=owner,
        name='CI',
    )

    # act
    AuditEventService.api_key_revoked(
        user=owner,
        auth_type=AuthTokenType.USER,
        api_key=api_key,
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.type == ApiKeyEvents.REVOKE
    assert event.category == EventCategory.API_KEYS
    assert event.account_id == account.id
    assert event.object == EventObject(
        type=EventCategory.API_KEYS,
        id=api_key.id,
        name=api_key.name,
    )
    assert event.payload == {
        'name': 'CI',
        'target_user_id': owner.id,
        'target_email': api_key.user.email,
    }


def test_api_key_revoked__key_of_another_account__key_account(fake_stream):
    """The record goes into the account of the key, not into the one
    of whoever revokes it."""

    # arrange
    owner = create_test_owner(email='owner@test.test')
    key_owner = create_test_owner(
        account=create_test_account(name='Other'),
        email='ann@test.test',
    )
    api_key = create_test_api_key(
        user=key_owner,
        name='CI',
    )

    # act
    AuditEventService.api_key_revoked(
        user=owner,
        auth_type=AuthTokenType.USER,
        api_key=api_key,
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.type == ApiKeyEvents.REVOKE
    assert event.account_id == key_owner.account_id
    assert event.actor == Actor(
        id=owner.id,
        email=owner.email,
        user_type=UserType.USER,
    )
    assert event.object == EventObject(
        type=EventCategory.API_KEYS,
        id=api_key.id,
        name=api_key.name,
    )
    assert event.payload == {
        'name': 'CI',
        'target_user_id': key_owner.id,
        'target_email': api_key.user.email,
    }


def test_admin_created__form_data__row_account_and_form_in_the_payload(
    fake_stream,
):
    """The record goes into the account the row belongs to, with the
    form the superuser submitted."""

    # arrange
    superuser = create_test_owner(email='super@test.test')
    target_account = create_test_account(name='Other')
    target = create_test_not_admin(
        account=target_account,
        email='ann@test.test',
    )

    # act
    AuditEventService.admin_created(
        user=superuser,
        target=target,
        model='accounts.user',
        form_data={'data': {'email': 'ann@test.test'}},
        object_id=target.pk,
        account_id=getattr(target, 'account_id', None) or superuser.account_id,
        account_name=target.account.name,
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.type == AdminEvents.CREATE
    assert event.category == EventCategory.ADMIN
    assert event.account_id == target_account.id
    assert event.actor == Actor(
        id=superuser.id,
        email=superuser.email,
        user_type=UserType.USER,
    )
    assert event.auth_type is None
    assert event.object == EventObject(
        type=EventCategory.ADMIN,
        id=target.id,
        name=str(target),
    )
    assert event.payload == {
        'model': 'accounts.user',
        'data': {'email': 'ann@test.test'},
    }


def test_admin_created__no_form__model_only_in_the_payload(fake_stream):
    """A row saved without a form the admin site kept: the payload
    names the model and nothing else."""

    # arrange
    superuser = create_test_owner(email='super@test.test')
    target_account = create_test_account(name='Other')

    # act
    AuditEventService.admin_created(
        user=superuser,
        target=target_account,
        model='accounts.account',
        form_data=None,
        object_id=target_account.pk,
        account_id=target_account.id,
        account_name=target_account.name,
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.type == AdminEvents.CREATE
    assert event.account_id == target_account.id
    assert event.object == EventObject(
        type=EventCategory.ADMIN,
        id=target_account.id,
        name=str(target_account),
    )
    assert event.payload == {'model': 'accounts.account'}


def test_admin_updated__password_set__update_and_password_set_events(
    fake_stream,
):
    """A password set on the admin site is the record an alert
    watches, the same as one set through the API."""

    # arrange
    superuser = create_test_owner(email='super@test.test')
    target_account = create_test_account(name='Other')
    target = create_test_not_admin(
        account=target_account,
        email='ann@test.test',
    )

    # act
    AuditEventService.admin_updated(
        user=superuser,
        target=target,
        model='accounts.user',
        form_data={'data': {'first_name': 'Ann'}},
        is_password_set=True,
        object_id=target.pk,
        account_id=getattr(target, 'account_id', None) or superuser.account_id,
        account_name=target.account.name,
    )

    # assert
    assert len(fake_stream.events) == 2
    update = fake_stream.events[0][1]
    password_set = fake_stream.events[1][1]
    assert update.type == AdminEvents.UPDATE
    assert update.account_id == target_account.id
    assert update.object == EventObject(
        type=EventCategory.ADMIN,
        id=target.id,
        name=str(target),
    )
    assert update.payload == {
        'model': 'accounts.user',
        'data': {'first_name': 'Ann'},
    }
    assert password_set.type == UserEvents.PASSWORD_SET
    assert password_set.account_id == target_account.id
    assert password_set.actor == Actor(
        id=superuser.id,
        email=superuser.email,
        user_type=UserType.USER,
    )
    assert password_set.auth_type is None
    assert password_set.object == EventObject(
        type=EventCategory.USERS,
        id=target.id,
        name=target.email,
    )
    assert password_set.payload == {'target_email': 'ann@test.test'}


def test_admin_updated__password_not_set__update_event_only(fake_stream):

    # arrange
    superuser = create_test_owner(email='super@test.test')
    target_account = create_test_account(name='Other')
    target = create_test_not_admin(
        account=target_account,
        email='ann@test.test',
    )

    # act
    AuditEventService.admin_updated(
        user=superuser,
        target=target,
        model='accounts.user',
        form_data={'data': {'first_name': 'Ann'}},
        is_password_set=False,
        object_id=target.pk,
        account_id=getattr(target, 'account_id', None) or superuser.account_id,
        account_name=target.account.name,
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.type == AdminEvents.UPDATE
    assert event.account_id == target_account.id
    assert event.payload == {
        'model': 'accounts.user',
        'data': {'first_name': 'Ann'},
    }


def test_purchase_made__products__quantity_by_code(fake_stream):

    # arrange
    owner = create_test_owner()

    # act
    AuditEventService.purchase_made(
        user=owner,
        auth_type=AuthTokenType.USER,
        products=[
            {'code': 'unlimited_month', 'quantity': 1},
            {'code': 'extra_users', 'quantity': 2},
        ],
        product_names={'credits': 'Credits', 'users': 'Users'},
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.type == BillingEvents.PURCHASE
    assert event.account_id == owner.account_id
    assert event.actor == Actor(
        id=owner.id,
        email=owner.email,
        user_type=UserType.USER,
    )
    assert event.auth_type == AuthTokenType.USER
    assert event.object == EventObject(
        type=EventCategory.BILLING,
        id=owner.account_id,
        name=owner.account.name,
    )
    assert event.payload == {
        'products': {'unlimited_month': 1, 'extra_users': 2},
        'product_names': {'credits': 'Credits', 'users': 'Users'},
    }


def test_purchase_made__repeated_code__quantity_summed(fake_stream):

    # arrange
    owner = create_test_owner()

    # act
    AuditEventService.purchase_made(
        user=owner,
        auth_type=AuthTokenType.USER,
        products=[
            {'code': 'extra_users', 'quantity': 2},
            {'code': 'extra_users', 'quantity': 3},
        ],
        product_names={'credits': 'Credits', 'users': 'Users'},
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.payload == {
        'products': {'extra_users': 5},
        'product_names': {'credits': 'Credits', 'users': 'Users'},
    }


def test_subscription_cancelled__owner__account_object(fake_stream):

    # arrange
    owner = create_test_owner()

    # act
    AuditEventService.subscription_cancelled(
        user=owner,
        auth_type=AuthTokenType.USER,
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.type == BillingEvents.SUBSCRIPTION_CANCEL
    assert event.account_id == owner.account_id
    assert event.actor == Actor(
        id=owner.id,
        email=owner.email,
        user_type=UserType.USER,
    )
    assert event.auth_type == AuthTokenType.USER
    assert event.object == EventObject(
        type=EventCategory.BILLING,
        id=owner.account_id,
        name=owner.account.name,
    )
    assert event.payload == {}


def test_payment_confirmed__no_subscription_data__empty_payload(fake_stream):

    # arrange
    user = create_test_owner()

    # act
    AuditEventService.payment_confirmed(
        user=user,
        auth_type=None,
        subscription_data=None,
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.type == BillingEvents.PAYMENT_CONFIRM
    assert event.category == EventCategory.BILLING
    assert event.account_id == user.account_id
    assert event.actor == Actor(
        id=user.id,
        email=user.email,
        user_type=UserType.USER,
    )
    assert event.auth_type is None
    assert event.object == EventObject(
        type=EventCategory.BILLING,
        id=user.account_id,
        name=user.account.name,
    )
    assert event.payload == {}


def test_payment_confirmed__empty_subscription_data__empty_payload(
    fake_stream,
):

    # arrange
    user = create_test_owner()

    # act
    AuditEventService.payment_confirmed(
        user=user,
        auth_type=AuthTokenType.USER,
        subscription_data={},
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.type == BillingEvents.PAYMENT_CONFIRM
    assert event.payload == {}


def test_payment_confirmed__subscription_data__plan_in_the_payload(
    fake_stream,
):

    # arrange
    user = create_test_owner()

    # act
    AuditEventService.payment_confirmed(
        user=user,
        auth_type=AuthTokenType.API,
        subscription_data={
            'billing_plan': BillingPlanType.PREMIUM,
            'max_users': 10,
            'trial_ended': True,
        },
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.type == BillingEvents.PAYMENT_CONFIRM
    assert event.actor == Actor(
        id=user.id,
        email=user.email,
        user_type=UserType.USER,
    )
    assert event.auth_type == AuthTokenType.API
    assert event.payload == {
        'billing_plan': BillingPlanType.PREMIUM,
        'max_users': 10,
    }


def test_webhook_subscribed__url__url_and_event_in_the_payload(fake_stream):

    # arrange
    owner = create_test_owner()

    # act
    AuditEventService.webhook_subscribed(
        user=owner,
        auth_type=AuthTokenType.API,
        url='https://hooks.test/in',
        event='workflow_completed',
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.type == WebhookEvents.SUBSCRIBE
    assert event.category == EventCategory.WEBHOOKS
    assert event.account_id == owner.account_id
    assert event.actor == Actor(
        id=owner.id,
        email=owner.email,
        user_type=UserType.USER,
    )
    assert event.auth_type == AuthTokenType.API
    assert event.object == EventObject(type=EventCategory.WEBHOOKS)
    assert event.payload == {
        'url': 'https://hooks.test/in',
        'event': 'workflow_completed',
    }


def test_webhook_unsubscribed__event__event_in_the_payload(fake_stream):

    # arrange
    owner = create_test_owner()

    # act
    AuditEventService.webhook_unsubscribed(
        user=owner,
        auth_type=AuthTokenType.USER,
        event='task_completed_v2',
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.type == WebhookEvents.UNSUBSCRIBE
    assert event.category == EventCategory.WEBHOOKS
    assert event.account_id == owner.account_id
    assert event.object == EventObject(type=EventCategory.WEBHOOKS)
    assert event.payload == {'event': 'task_completed_v2'}


def test_template_created__draft__whole_template_in_the_payload(fake_stream):
    """The draft holds the template the way the API returns it after
    any save, and the name of a draft lives only there."""

    # arrange
    owner = create_test_owner()
    template = create_test_template(
        user=owner,
        is_active=True,
        name='Onboarding',
    )
    TemplateDraft.objects.update_or_create(
        template=template,
        defaults={'draft': {'name': 'Draft name', 'description': 'Desc'}},
    )
    template.refresh_from_db()

    # act
    AuditEventService.template_created(
        user=owner,
        auth_type=AuthTokenType.USER,
        template=template,
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.type == TemplateEvents.CREATE
    assert event.category == EventCategory.TEMPLATES
    assert event.account_id == owner.account_id
    assert event.actor == Actor(
        id=owner.id,
        email=owner.email,
        user_type=UserType.USER,
    )
    assert event.auth_type == AuthTokenType.USER
    assert event.object == EventObject(
        type=EventCategory.TEMPLATES,
        id=template.id,
        name='Draft name',
    )
    assert event.payload == {
        'name': 'Draft name',
        'version': template.version,
        'is_active': True,
        'template': {'name': 'Draft name', 'description': 'Desc'},
    }


def test_template_created__source__source_in_the_payload(fake_stream):

    # arrange
    owner = create_test_owner()
    template = create_test_template(
        user=owner,
        is_active=False,
    )
    TemplateDraft.objects.update_or_create(
        template=template,
        defaults={'draft': {'name': 'Hiring'}},
    )
    template.refresh_from_db()

    # act
    AuditEventService.template_created(
        user=owner,
        auth_type=AuthTokenType.USER,
        template=template,
        source=TemplateSource.LIBRARY,
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.type == TemplateEvents.CREATE
    assert event.payload == {
        'name': 'Hiring',
        'version': template.version,
        'is_active': False,
        'template': {'name': 'Hiring'},
        'source': TemplateSource.LIBRARY,
    }


def test_template_created__empty_source__no_source_key(fake_stream):

    # arrange
    owner = create_test_owner()
    template = create_test_template(
        user=owner,
        is_active=False,
    )
    TemplateDraft.objects.update_or_create(
        template=template,
        defaults={'draft': {'name': 'Hiring'}},
    )
    template.refresh_from_db()

    # act
    AuditEventService.template_created(
        user=owner,
        auth_type=AuthTokenType.USER,
        template=template,
        source='',
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.payload == {
        'name': 'Hiring',
        'version': template.version,
        'is_active': False,
        'template': {'name': 'Hiring'},
    }


def test_template_created__null_draft__name_of_the_template(fake_stream):

    # arrange
    owner = create_test_owner()
    template = create_test_template(
        user=owner,
        is_active=True,
        name='Onboarding',
    )
    TemplateDraft.objects.update_or_create(
        template=template,
        defaults={'draft': None},
    )
    template.refresh_from_db()

    # act
    AuditEventService.template_created(
        user=owner,
        auth_type=AuthTokenType.USER,
        template=template,
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.type == TemplateEvents.CREATE
    assert event.payload == {
        'name': 'Onboarding',
        'version': template.version,
        'is_active': True,
        'template': {},
    }


def test_template_created__draft_without_name__name_of_the_template(
    fake_stream,
):

    # arrange
    owner = create_test_owner()
    template = create_test_template(
        user=owner,
        is_active=True,
        name='Onboarding',
    )
    TemplateDraft.objects.update_or_create(
        template=template,
        defaults={'draft': {'description': 'Desc'}},
    )
    template.refresh_from_db()

    # act
    AuditEventService.template_created(
        user=owner,
        auth_type=AuthTokenType.USER,
        template=template,
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.payload == {
        'name': 'Onboarding',
        'version': template.version,
        'is_active': True,
        'template': {'description': 'Desc'},
    }


@pytest.mark.parametrize('method', ['template_created', 'template_updated'])
@pytest.mark.parametrize('backend', [None, ''])
def test_template_saved__logs_disabled__no_queries(
    fake_stream,
    settings,
    django_assert_num_queries,
    method,
    backend,
):

    # arrange
    owner = create_test_owner()
    template = create_test_template(
        user=owner,
        is_active=True,
    )
    stored = Template.objects.get(id=template.id)
    settings.LOGS_BACKEND = backend

    # act
    with django_assert_num_queries(0):
        getattr(AuditEventService, method)(
            user=owner,
            auth_type=AuthTokenType.USER,
            template=stored,
        )

    # assert
    assert fake_stream.events == []


def test_template_updated__draft__update_event(fake_stream):

    # arrange
    owner = create_test_owner()
    template = create_test_template(
        user=owner,
        is_active=True,
    )
    TemplateDraft.objects.update_or_create(
        template=template,
        defaults={'draft': {'name': 'Onboarding v2'}},
    )
    template.refresh_from_db()

    # act
    AuditEventService.template_updated(
        user=owner,
        auth_type=AuthTokenType.API,
        template=template,
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.type == TemplateEvents.UPDATE
    assert event.category == EventCategory.TEMPLATES
    assert event.account_id == owner.account_id
    assert event.actor == Actor(
        id=owner.id,
        email=owner.email,
        user_type=UserType.USER,
    )
    assert event.auth_type == AuthTokenType.API
    assert event.object == EventObject(
        type=EventCategory.TEMPLATES,
        id=template.id,
        name='Onboarding v2',
    )
    assert event.payload == {
        'name': 'Onboarding v2',
        'version': template.version,
        'is_active': True,
        'template': {'name': 'Onboarding v2'},
    }


def test_template_updated__logs_disabled__nothing_emitted(
    fake_stream,
    settings,
):

    # arrange
    owner = create_test_owner()
    template = create_test_template(
        user=owner,
        is_active=True,
    )
    stored = Template.objects.get(id=template.id)
    settings.LOGS_BACKEND = None

    # act
    AuditEventService.template_updated(
        user=owner,
        auth_type=AuthTokenType.USER,
        template=stored,
    )

    # assert
    assert fake_stream.events == []


def test_template_cloned__template__clone_event(fake_stream):

    # arrange
    owner = create_test_owner()
    template = create_test_template(
        user=owner,
        is_active=False,
    )

    # act
    AuditEventService.template_cloned(
        user=owner,
        auth_type=AuthTokenType.USER,
        template=template,
        name='Copy of Onboarding',
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.type == TemplateEvents.CLONE
    assert event.category == EventCategory.TEMPLATES
    assert event.object == EventObject(
        type=EventCategory.TEMPLATES,
        id=template.id,
        name='Copy of Onboarding',
    )
    assert event.payload == {
        'name': 'Copy of Onboarding',
        'version': template.version,
        'is_active': False,
    }


def test_template_deleted__template__delete_event_with_the_name(fake_stream):

    # arrange
    owner = create_test_owner()
    template = create_test_template(
        user=owner,
        is_active=True,
        name='Offboarding',
    )

    # act
    AuditEventService.template_deleted(
        user=owner,
        auth_type=AuthTokenType.USER,
        template=template,
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.type == TemplateEvents.DELETE
    assert event.category == EventCategory.TEMPLATES
    assert event.object == EventObject(
        type=EventCategory.TEMPLATES,
        id=template.id,
        name=template.name,
    )
    assert event.payload == {
        'name': 'Offboarding',
        'version': template.version,
        'is_active': True,
    }


def test_templates_export__api_key__filters_and_no_object_id(fake_stream):
    """The export is a bulk read: the filters say what left."""

    # arrange
    owner = create_test_owner()

    # act
    AuditEventService.templates_export(
        user=owner,
        auth_type=AuthTokenType.API,
        filters={'is_active': True, 'ordering': 'name'},
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.type == TemplateEvents.EXPORT
    assert event.category == EventCategory.TEMPLATES
    assert event.account_id == owner.account_id
    assert event.actor == Actor(
        id=owner.id,
        email=owner.email,
        user_type=UserType.USER,
    )
    assert event.auth_type == AuthTokenType.API
    assert event.object == EventObject(type=EventCategory.TEMPLATES)
    assert event.payload == {
        'filters': {'is_active': True, 'ordering': 'name'},
    }


def test_template_discarded_changes__never_published__template_deleted(
    fake_stream,
):

    # arrange
    owner = create_test_owner()
    template = create_test_template(
        user=owner,
        is_active=False,
        name='Onboarding',
    )

    # act
    AuditEventService.template_discarded_changes(
        user=owner,
        auth_type=AuthTokenType.USER,
        template=template,
        template_deleted=True,
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.type == TemplateEvents.DRAFT_DISCARD
    assert event.category == EventCategory.TEMPLATES
    assert event.account_id == owner.account_id
    assert event.actor == Actor(
        id=owner.id,
        email=owner.email,
        user_type=UserType.USER,
    )
    assert event.auth_type == AuthTokenType.USER
    assert event.object == EventObject(
        type=EventCategory.TEMPLATES,
        id=template.id,
        name=template.name,
    )
    assert event.payload == {
        'name': 'Onboarding',
        'version': template.version,
        'is_active': False,
        'template_deleted': True,
    }


def test_template_discarded_changes__published__template_kept(fake_stream):

    # arrange
    owner = create_test_owner()
    template = create_test_template(
        user=owner,
        is_active=True,
        name='Onboarding',
    )

    # act
    AuditEventService.template_discarded_changes(
        user=owner,
        auth_type=AuthTokenType.USER,
        template=template,
        template_deleted=False,
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.type == TemplateEvents.DRAFT_DISCARD
    assert event.payload == {
        'name': 'Onboarding',
        'version': template.version,
        'is_active': True,
        'template_deleted': False,
    }


def test_template_generated_with_ai__owner__no_object_id_no_payload(
    fake_stream,
):

    # arrange
    owner = create_test_owner()

    # act
    AuditEventService.template_generated_with_ai(
        user=owner,
        auth_type=AuthTokenType.USER,
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.type == TemplateEvents.AI_GENERATE
    assert event.account_id == owner.account_id
    assert event.actor == Actor(
        id=owner.id,
        email=owner.email,
        user_type=UserType.USER,
    )
    assert event.auth_type == AuthTokenType.USER
    assert event.object == EventObject(type=EventCategory.TEMPLATES)
    assert event.payload == {}


def test_template_filled_from_library__owner__system_template_object(
    fake_stream,
):

    # arrange
    owner = create_test_owner()
    system_template = create_test_system_template(name='Hiring')

    # act
    AuditEventService.template_filled_from_library(
        user=owner,
        auth_type=AuthTokenType.USER,
        system_template=system_template,
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.type == TemplateEvents.LIBRARY_FILL
    assert event.account_id == owner.account_id
    assert event.object == EventObject(
        type=EventCategory.TEMPLATES,
        id=system_template.id,
        name=system_template.name,
    )
    assert event.payload == {'name': 'Hiring'}


def test_library_templates_imported__owner__templates_count(fake_stream):

    # arrange
    owner = create_test_owner()

    # act
    AuditEventService.library_templates_imported(
        user=owner,
        auth_type=AuthTokenType.USER,
        templates_count=3,
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.type == TemplateEvents.LIBRARY_IMPORT
    assert event.account_id == owner.account_id
    assert event.object == EventObject(type=EventCategory.TEMPLATES)
    assert event.payload == {'templates_count': 3}


def test_template_preset_created__preset__preset_object(fake_stream):

    # arrange
    owner = create_test_owner()
    template = create_test_template(
        user=owner,
        is_active=True,
    )
    preset = create_test_template_preset(
        template=template,
        author=owner,
        name='Weekly',
    )

    # act
    AuditEventService.template_preset_created(
        user=owner,
        auth_type=AuthTokenType.USER,
        preset=preset,
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.type == TemplateEvents.PRESET_CREATE
    assert event.account_id == owner.account_id
    assert event.actor == Actor(
        id=owner.id,
        email=owner.email,
        user_type=UserType.USER,
    )
    assert event.auth_type == AuthTokenType.USER
    assert event.object == EventObject(
        type=EventCategory.TEMPLATES,
        id=preset.id,
        name=preset.name,
    )
    assert event.payload == {
        'name': 'Weekly',
        'template_id': template.id,
        'type': PresetType.PERSONAL,
        'is_default': False,
        'template_name': template.name,
    }


def test_template_preset_updated__kwargs_and_fields__both_in_the_payload(
    fake_stream,
):
    """The kwargs come after the preset itself: a renamed preset is
    written under the name the request sent."""

    # arrange
    owner = create_test_owner()
    template = create_test_template(
        user=owner,
        is_active=True,
    )
    preset = create_test_template_preset(
        template=template,
        author=owner,
        name='Weekly',
    )

    # act
    AuditEventService.template_preset_updated(
        user=owner,
        auth_type=AuthTokenType.USER,
        preset=preset,
        update_kwargs={'name': 'Monthly'},
        fields=[{'api_name': 'field-1', 'order': 1, 'width': 100}],
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.type == TemplateEvents.PRESET_UPDATE
    assert event.object == EventObject(
        type=EventCategory.TEMPLATES,
        id=preset.id,
        name=preset.name,
    )
    assert event.payload == {
        'name': 'Monthly',
        'template_id': template.id,
        'type': PresetType.PERSONAL,
        'is_default': False,
        'fields': ['{"api_name": "field-1", "order": 1, "width": 100}'],
        'template_name': template.name,
    }


def test_template_preset_updated__no_fields__fields_key_absent(fake_stream):
    """The fields are named only when the request sent them."""

    # arrange
    owner = create_test_owner()
    template = create_test_template(
        user=owner,
        is_active=True,
    )
    preset = create_test_template_preset(
        template=template,
        author=owner,
        name='Weekly',
    )

    # act
    AuditEventService.template_preset_updated(
        user=owner,
        auth_type=AuthTokenType.USER,
        preset=preset,
        update_kwargs={},
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.type == TemplateEvents.PRESET_UPDATE
    assert event.payload == {
        'name': 'Weekly',
        'template_id': template.id,
        'type': PresetType.PERSONAL,
        'is_default': False,
        'template_name': template.name,
    }


def test_template_preset_deleted__preset__preset_object(fake_stream):

    # arrange
    owner = create_test_owner()
    template = create_test_template(
        user=owner,
        is_active=True,
    )
    preset = create_test_template_preset(
        template=template,
        author=owner,
        name='Weekly',
    )

    # act
    AuditEventService.template_preset_deleted(
        user=owner,
        auth_type=AuthTokenType.USER,
        preset=preset,
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.type == TemplateEvents.PRESET_DELETE
    assert event.object == EventObject(
        type=EventCategory.TEMPLATES,
        id=preset.id,
        name=preset.name,
    )
    assert event.payload == {
        'name': 'Weekly',
        'template_id': template.id,
        'type': PresetType.PERSONAL,
        'is_default': False,
        'template_name': template.name,
    }


def test_template_preset_set_default__default_preset__is_default_true(
    fake_stream,
):

    # arrange
    owner = create_test_owner()
    template = create_test_template(
        user=owner,
        is_active=True,
    )
    preset = create_test_template_preset(
        template=template,
        author=owner,
        name='Weekly',
        is_default=True,
    )

    # act
    AuditEventService.template_preset_set_default(
        user=owner,
        auth_type=AuthTokenType.USER,
        preset=preset,
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.type == TemplateEvents.PRESET_SET_DEFAULT
    assert event.object == EventObject(
        type=EventCategory.TEMPLATES,
        id=preset.id,
        name=preset.name,
    )
    assert event.payload == {
        'name': 'Weekly',
        'template_id': template.id,
        'type': PresetType.PERSONAL,
        'is_default': True,
        'template_name': template.name,
    }


def test_fieldset_created__fieldset__fieldset_object(fake_stream):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    fieldset = create_test_shared_fieldset(
        account=account,
        name='Address',
    )

    # act
    AuditEventService.fieldset_created(
        user=owner,
        auth_type=AuthTokenType.USER,
        fieldset=fieldset,
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.type == TemplateEvents.FIELDSET_CREATE
    assert event.account_id == account.id
    assert event.actor == Actor(
        id=owner.id,
        email=owner.email,
        user_type=UserType.USER,
    )
    assert event.auth_type == AuthTokenType.USER
    assert event.object == EventObject(
        type=EventCategory.TEMPLATES,
        id=fieldset.id,
        name=fieldset.name,
    )
    assert event.payload == {'name': 'Address'}


def test_fieldset_updated__kwargs_fields_and_rules__all_in_the_payload(
    fake_stream,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    fieldset = create_test_shared_fieldset(
        account=account,
        name='Address',
    )

    # act
    AuditEventService.fieldset_updated(
        user=owner,
        auth_type=AuthTokenType.USER,
        fieldset=fieldset,
        update_kwargs={'description': 'Home'},
        fields=[{'api_name': 'street', 'order': 1}],
        rules=[{'type': FieldSetRuleType.SUM_EQUAL, 'value': '10'}],
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.type == TemplateEvents.FIELDSET_UPDATE
    assert event.object == EventObject(
        type=EventCategory.TEMPLATES,
        id=fieldset.id,
        name=fieldset.name,
    )
    assert event.payload == {
        'name': 'Address',
        'description': 'Home',
        'fields': ['{"api_name": "street", "order": 1}'],
        'rules': ['{"type": "sum_equal", "value": "10"}'],
    }


def test_fieldset_updated__only_fields__rules_key_absent(fake_stream):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    fieldset = create_test_shared_fieldset(
        account=account,
        name='Address',
    )

    # act
    AuditEventService.fieldset_updated(
        user=owner,
        auth_type=AuthTokenType.USER,
        fieldset=fieldset,
        update_kwargs={},
        fields=[{'api_name': 'street', 'order': 1}],
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.type == TemplateEvents.FIELDSET_UPDATE
    assert event.payload == {
        'name': 'Address',
        'fields': ['{"api_name": "street", "order": 1}'],
    }


def test_fieldset_updated__only_rules__fields_key_absent(fake_stream):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    fieldset = create_test_shared_fieldset(
        account=account,
        name='Address',
    )

    # act
    AuditEventService.fieldset_updated(
        user=owner,
        auth_type=AuthTokenType.USER,
        fieldset=fieldset,
        update_kwargs={},
        rules=[{'type': FieldSetRuleType.SUM_EQUAL, 'value': '10'}],
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.type == TemplateEvents.FIELDSET_UPDATE
    assert event.payload == {
        'name': 'Address',
        'rules': ['{"type": "sum_equal", "value": "10"}'],
    }


def test_fieldset_updated__nothing_sent__name_only(fake_stream):
    """The fields and the rules are named only when the request sent
    them."""

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    fieldset = create_test_shared_fieldset(
        account=account,
        name='Address',
    )

    # act
    AuditEventService.fieldset_updated(
        user=owner,
        auth_type=AuthTokenType.USER,
        fieldset=fieldset,
        update_kwargs={},
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.type == TemplateEvents.FIELDSET_UPDATE
    assert event.payload == {'name': 'Address'}


def test_fieldset_cloned__clone__source_fieldset_id_in_the_payload(
    fake_stream,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    fieldset = create_test_shared_fieldset(
        account=account,
        name='Address',
    )
    clone = create_test_shared_fieldset(
        account=account,
        name='Copy of Address',
    )

    # act
    AuditEventService.fieldset_cloned(
        user=owner,
        auth_type=AuthTokenType.USER,
        clone=clone,
        source_fieldset=fieldset,
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.type == TemplateEvents.FIELDSET_CLONE
    assert event.object == EventObject(
        type=EventCategory.TEMPLATES,
        id=clone.id,
        name=clone.name,
    )
    assert event.payload == {
        'name': 'Copy of Address',
        'source_fieldset_id': fieldset.id,
        'source_fieldset_name': fieldset.name,
    }


def test_fieldset_deleted__fieldset__fieldset_object(fake_stream):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    fieldset = create_test_shared_fieldset(
        account=account,
        name='Address',
    )

    # act
    AuditEventService.fieldset_deleted(
        user=owner,
        auth_type=AuthTokenType.USER,
        fieldset=fieldset,
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.type == TemplateEvents.FIELDSET_DELETE
    assert event.object == EventObject(
        type=EventCategory.TEMPLATES,
        id=fieldset.id,
        name=fieldset.name,
    )
    assert event.payload == {'name': 'Address'}


def test_dataset_created__dataset__items_count_in_the_payload(fake_stream):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    dataset = create_test_dataset(
        account=account,
        name='Cities',
    )

    # act
    AuditEventService.dataset_created(
        user=owner,
        auth_type=AuthTokenType.USER,
        dataset=dataset,
        items_count=2,
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.type == DatasetEvents.CREATE
    assert event.account_id == account.id
    assert event.actor == Actor(
        id=owner.id,
        email=owner.email,
        user_type=UserType.USER,
    )
    assert event.auth_type == AuthTokenType.USER
    assert event.object == EventObject(
        type=EventCategory.DATASETS,
        id=dataset.id,
        name=dataset.name,
    )
    assert event.payload == {'name': 'Cities', 'items_count': 2}


def test_dataset_updated__update_kwargs__kwargs_in_the_payload(fake_stream):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    dataset = create_test_dataset(
        account=account,
        name='Cities',
    )

    # act
    AuditEventService.dataset_updated(
        user=owner,
        auth_type=AuthTokenType.USER,
        dataset=dataset,
        update_kwargs={'description': 'Big cities'},
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.type == DatasetEvents.UPDATE
    assert event.category == EventCategory.DATASETS
    assert event.account_id == account.id
    assert event.actor == Actor(
        id=owner.id,
        email=owner.email,
        user_type=UserType.USER,
    )
    assert event.auth_type == AuthTokenType.USER
    assert event.object == EventObject(
        type=EventCategory.DATASETS,
        id=dataset.id,
        name=dataset.name,
    )
    assert event.payload == {'name': 'Cities', 'description': 'Big cities'}


def test_dataset_updated__new_name__name_sent_wins(fake_stream):
    """The kwargs come after the name of the dataset: a renamed one
    is written under the name the request sent."""

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    dataset = create_test_dataset(
        account=account,
        name='Cities',
    )

    # act
    AuditEventService.dataset_updated(
        user=owner,
        auth_type=AuthTokenType.USER,
        dataset=dataset,
        update_kwargs={'name': 'Towns'},
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.payload == {'name': 'Towns'}


def test_dataset_updated__items__rows_as_json_strings(fake_stream):
    """The rows of a dataset are a list of objects: each of them is
    one attribute of the record, not a tree the log backend would
    index field by field."""

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    dataset = create_test_dataset(
        account=account,
        name='Cities',
    )

    # act
    AuditEventService.dataset_updated(
        user=owner,
        auth_type=AuthTokenType.USER,
        dataset=dataset,
        update_kwargs={'items': [{'value': 'Paris', 'order': 1}]},
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.payload == {
        'name': 'Cities',
        'items': ['{"value": "Paris", "order": 1}'],
    }


def test_dataset_deleted__dataset__dataset_object(fake_stream):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    dataset = create_test_dataset(
        account=account,
        name='Cities',
    )

    # act
    AuditEventService.dataset_deleted(
        user=owner,
        auth_type=AuthTokenType.USER,
        dataset=dataset,
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.type == DatasetEvents.DELETE
    assert event.object == EventObject(
        type=EventCategory.DATASETS,
        id=dataset.id,
        name=dataset.name,
    )
    assert event.payload == {'name': 'Cities'}


def test_dataset_item_created__item__item_object(fake_stream):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    dataset = create_test_dataset(account=account)
    item = dataset.items.get(order=1)

    # act
    AuditEventService.dataset_item_created(
        user=owner,
        auth_type=AuthTokenType.USER,
        item=item,
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.type == DatasetEvents.ITEM_CREATE
    assert event.account_id == account.id
    assert event.object == EventObject(
        type=EventCategory.DATASETS,
        id=item.id,
        name=item.value,
    )
    assert event.payload == {
        'dataset_id': dataset.id,
        'dataset_name': dataset.name,
        'value': item.value,
    }


def test_dataset_item_updated__update_kwargs__kwargs_in_the_payload(
    fake_stream,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    dataset = create_test_dataset(account=account)
    item = dataset.items.get(order=1)
    item.value = 'Paris'

    # act
    AuditEventService.dataset_item_updated(
        user=owner,
        auth_type=AuthTokenType.USER,
        item=item,
        update_kwargs={'value': 'Paris', 'order': 3},
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.type == DatasetEvents.ITEM_UPDATE
    assert event.category == EventCategory.DATASETS
    assert event.account_id == account.id
    assert event.actor == Actor(
        id=owner.id,
        email=owner.email,
        user_type=UserType.USER,
    )
    assert event.auth_type == AuthTokenType.USER
    assert event.object == EventObject(
        type=EventCategory.DATASETS,
        id=item.id,
        name=item.value,
    )
    assert event.payload == {
        'dataset_id': dataset.id,
        'value': 'Paris',
        'order': 3,
        'dataset_name': dataset.name,
    }


def test_dataset_item_updated__nothing_sent__dataset_only(fake_stream):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    dataset = create_test_dataset(account=account)
    item = dataset.items.get(order=1)

    # act
    AuditEventService.dataset_item_updated(
        user=owner,
        auth_type=AuthTokenType.USER,
        item=item,
        update_kwargs={},
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.type == DatasetEvents.ITEM_UPDATE
    assert event.payload == {
        'dataset_id': dataset.id,
        'dataset_name': dataset.name,
        'value': item.value,
    }


def test_dataset_item_deleted__item__item_object(fake_stream):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    dataset = create_test_dataset(account=account)
    item = dataset.items.get(order=1)

    # act
    AuditEventService.dataset_item_deleted(
        user=owner,
        auth_type=AuthTokenType.USER,
        item=item,
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.type == DatasetEvents.ITEM_DELETE
    assert event.object == EventObject(
        type=EventCategory.DATASETS,
        id=item.id,
        name=item.value,
    )
    assert event.payload == {
        'dataset_id': dataset.id,
        'dataset_name': dataset.name,
        'value': item.value,
    }


def test_workflow_run__user__run_event_of_the_workflow(fake_stream):

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(
        user=owner,
        tasks_count=1,
    )

    # act
    AuditEventService.workflow_run(
        user=owner,
        auth_type=AuthTokenType.API,
        workflow=workflow,
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.type == WorkflowEvents.RUN
    assert event.category == EventCategory.WORKFLOWS
    assert event.account_id == workflow.account_id
    assert event.actor == Actor(
        id=owner.id,
        email=owner.email,
        user_type=UserType.USER,
    )
    assert event.auth_type == AuthTokenType.API
    assert event.object == EventObject(
        type=EventCategory.WORKFLOWS,
        id=workflow.id,
        name=workflow.name,
    )
    assert event.payload == {
        'workflow_name': workflow.name,
        'template_id': workflow.template_id,
        'template_name': workflow.template.name
        if workflow.template_id
        else None,
    }
    assert event.workflow_id == workflow.id
    assert event.task_id is None


def test_workflow_run__no_user__engine_acts_without_auth_type(fake_stream):
    """A user of None is the workflow engine: no actor, and the auth
    type the caller carries says nothing about who acted. The
    account is the one of the workflow."""

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(
        user=owner,
        tasks_count=1,
    )

    # act
    AuditEventService.workflow_run(
        user=None,
        auth_type=AuthTokenType.USER,
        workflow=workflow,
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.type == WorkflowEvents.RUN
    assert event.account_id == workflow.account_id
    assert event.actor is None
    assert event.auth_type is None


def test_sub_workflow_run__sub_workflow__parent_at_the_ancestor_task(
    fake_stream,
):
    """Into the parent workflow, at the task that started the sub
    workflow: the sub workflow is named in the payload."""

    # arrange
    owner = create_test_owner()
    parent = create_test_workflow(
        user=owner,
        tasks_count=1,
        name='Parent',
    )
    ancestor_task = parent.tasks.get(number=1)
    sub_workflow = create_test_workflow(
        user=owner,
        tasks_count=1,
        name='Child',
        ancestor_task=ancestor_task,
    )

    # act
    AuditEventService.sub_workflow_run(
        user=owner,
        auth_type=AuthTokenType.USER,
        sub_workflow=sub_workflow,
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.type == WorkflowEvents.SUB_WORKFLOW_RUN
    assert event.category == EventCategory.WORKFLOWS
    assert event.account_id == parent.account_id
    assert event.actor == Actor(
        id=owner.id,
        email=owner.email,
        user_type=UserType.USER,
    )
    assert event.auth_type == AuthTokenType.USER
    assert event.object == EventObject(
        type=EventCategory.WORKFLOWS,
        id=parent.id,
        name=parent.name,
    )
    assert event.payload == {
        'workflow_name': 'Parent',
        'template_id': parent.template_id,
        'task_name': ancestor_task.name,
        'sub_workflow_id': sub_workflow.id,
        'sub_workflow_name': 'Child',
        'template_name': parent.template.name if parent.template_id else None,
    }
    assert event.workflow_id == parent.id
    assert event.task_id == ancestor_task.id


def test_workflow_updated__update_kwargs__kwargs_in_the_payload(fake_stream):

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(
        user=owner,
        tasks_count=1,
    )

    # act
    AuditEventService.workflow_updated(
        user=owner,
        auth_type=AuthTokenType.USER,
        workflow=workflow,
        update_kwargs={'name': 'New name', 'is_urgent': True},
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.type == WorkflowEvents.UPDATE
    assert event.category == EventCategory.WORKFLOWS
    assert event.account_id == owner.account_id
    assert event.actor == Actor(
        id=owner.id,
        email=owner.email,
        user_type=UserType.USER,
    )
    assert event.auth_type == AuthTokenType.USER
    assert event.object == EventObject(
        type=EventCategory.WORKFLOWS,
        id=workflow.id,
        name=workflow.name,
    )
    assert event.payload == {
        'workflow_name': workflow.name,
        'template_id': workflow.template_id,
        'name': 'New name',
        'is_urgent': True,
        'template_name': workflow.template.name
        if workflow.template_id
        else None,
    }
    assert event.workflow_id == workflow.id
    assert event.task_id is None


def test_workflow_updated__kickoff__field_names_in_the_payload(fake_stream):

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(
        user=owner,
        tasks_count=1,
    )
    create_test_kickoff_field(
        workflow=workflow,
        name='Client',
        api_name='client',
    )
    create_test_kickoff_field(
        workflow=workflow,
        name='Budget',
        api_name='budget',
    )

    # act
    AuditEventService.workflow_updated(
        user=owner,
        auth_type=AuthTokenType.USER,
        workflow=workflow,
        update_kwargs={'kickoff': {'client': 'Acme'}},
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.payload == {
        'workflow_name': workflow.name,
        'template_id': workflow.template_id,
        'template_name': workflow.template.name
        if workflow.template_id
        else None,
        'kickoff': {'client': 'Acme'},
        'kickoff_fields': {'client': 'Client'},
    }


def test_workflow_updated__nothing_sent__workflow_only(fake_stream):

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(
        user=owner,
        tasks_count=1,
    )

    # act
    AuditEventService.workflow_updated(
        user=owner,
        auth_type=AuthTokenType.USER,
        workflow=workflow,
        update_kwargs={},
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.type == WorkflowEvents.UPDATE
    assert event.payload == {
        'workflow_name': workflow.name,
        'template_id': workflow.template_id,
        'template_name': workflow.template.name
        if workflow.template_id
        else None,
    }


def test_workflow_snooze__date__force_delay_event_with_the_date(fake_stream):

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(
        user=owner,
        tasks_count=1,
    )
    snooze_date = datetime(2026, 9, 30, 10, 0, tzinfo=timezone.utc)

    # act
    AuditEventService.workflow_snooze(
        user=owner,
        auth_type=AuthTokenType.USER,
        workflow=workflow,
        snooze_until=snooze_date,
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.type == WorkflowEvents.FORCE_DELAY
    assert event.category == EventCategory.WORKFLOWS
    assert event.actor == Actor(
        id=owner.id,
        email=owner.email,
        user_type=UserType.USER,
    )
    assert event.object == EventObject(
        type=EventCategory.WORKFLOWS,
        id=workflow.id,
        name=workflow.name,
    )
    assert event.payload == {
        'workflow_name': workflow.name,
        'template_id': workflow.template_id,
        'date': '2026-09-30T10:00:00Z',
        'template_name': workflow.template.name
        if workflow.template_id
        else None,
    }
    assert event.workflow_id == workflow.id
    assert event.task_id is None


def test_workflow_resume__workflow__force_resume_event(fake_stream):

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(
        user=owner,
        tasks_count=1,
    )

    # act
    AuditEventService.workflow_resume(
        user=owner,
        auth_type=AuthTokenType.USER,
        workflow=workflow,
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.type == WorkflowEvents.FORCE_RESUME
    assert event.category == EventCategory.WORKFLOWS
    assert event.auth_type == AuthTokenType.USER
    assert event.object == EventObject(
        type=EventCategory.WORKFLOWS,
        id=workflow.id,
        name=workflow.name,
    )
    assert event.payload == {
        'workflow_name': workflow.name,
        'template_id': workflow.template_id,
        'template_name': workflow.template.name
        if workflow.template_id
        else None,
    }
    assert event.task_id is None


def test_workflow_finish__user__ended_event(fake_stream):

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(
        user=owner,
        tasks_count=1,
    )

    # act
    AuditEventService.workflow_finish(
        user=owner,
        auth_type=AuthTokenType.API,
        workflow=workflow,
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.type == WorkflowEvents.ENDED
    assert event.category == EventCategory.WORKFLOWS
    assert event.actor == Actor(
        id=owner.id,
        email=owner.email,
        user_type=UserType.USER,
    )
    assert event.auth_type == AuthTokenType.API
    assert event.payload == {
        'workflow_name': workflow.name,
        'template_id': workflow.template_id,
        'template_name': workflow.template.name
        if workflow.template_id
        else None,
    }
    assert event.workflow_id == workflow.id
    assert event.task_id is None


def test_workflow_complete__last_task__complete_event_at_the_task(fake_stream):
    """The completion of the last task completed the workflow: the
    record names that task."""

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(
        user=owner,
        tasks_count=1,
    )
    task = workflow.tasks.get(number=1)

    # act
    AuditEventService.workflow_complete(
        user=owner,
        auth_type=AuthTokenType.USER,
        workflow=workflow,
        task=task,
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.type == WorkflowEvents.COMPLETE
    assert event.category == EventCategory.WORKFLOWS
    assert event.object == EventObject(
        type=EventCategory.WORKFLOWS,
        id=workflow.id,
        name=workflow.name,
    )
    assert event.payload == {
        'workflow_name': workflow.name,
        'template_id': workflow.template_id,
        'task_name': task.name,
        'template_name': workflow.template.name
        if workflow.template_id
        else None,
    }
    assert event.workflow_id == workflow.id
    assert event.task_id == task.id


def test_workflow_ended_by_condition__engine__no_actor_at_the_task(
    fake_stream,
):

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(
        user=owner,
        tasks_count=1,
    )
    task = workflow.tasks.get(number=1)

    # act
    AuditEventService.workflow_ended_by_condition(
        user=None,
        auth_type=None,
        workflow=workflow,
        task=task,
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.type == WorkflowEvents.ENDED_BY_CONDITION
    assert event.category == EventCategory.WORKFLOWS
    assert event.account_id == workflow.account_id
    assert event.actor is None
    assert event.auth_type is None
    assert event.payload == {
        'workflow_name': workflow.name,
        'template_id': workflow.template_id,
        'task_name': task.name,
        'template_name': workflow.template.name
        if workflow.template_id
        else None,
    }
    assert event.workflow_id == workflow.id
    assert event.task_id == task.id


def test_workflow_return__task__revert_event_at_the_task(fake_stream):
    """The task is the one the workflow went back to, the workflow
    is the one of that task."""

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(
        user=owner,
        tasks_count=2,
        active_task_number=2,
    )
    task = workflow.tasks.get(number=1)

    # act
    AuditEventService.workflow_return(
        user=owner,
        auth_type=AuthTokenType.USER,
        task=task,
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.type == WorkflowEvents.REVERT
    assert event.category == EventCategory.WORKFLOWS
    assert event.actor == Actor(
        id=owner.id,
        email=owner.email,
        user_type=UserType.USER,
    )
    assert event.object == EventObject(
        type=EventCategory.WORKFLOWS,
        id=workflow.id,
        name=workflow.name,
    )
    assert event.payload == {
        'workflow_name': workflow.name,
        'template_id': workflow.template_id,
        'task_name': task.name,
        'template_name': workflow.template.name
        if workflow.template_id
        else None,
    }
    assert event.workflow_id == workflow.id
    assert event.task_id == task.id


def test_workflow_urgent__urgent_workflow__urgent_event(fake_stream):

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(
        user=owner,
        tasks_count=1,
        is_urgent=True,
    )

    # act
    AuditEventService.workflow_urgent(
        user=owner,
        auth_type=AuthTokenType.API,
        workflow=workflow,
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.type == WorkflowEvents.URGENT
    assert event.category == EventCategory.WORKFLOWS
    assert event.account_id == workflow.account_id
    assert event.actor == Actor(
        id=owner.id,
        email=owner.email,
        user_type=UserType.USER,
    )
    assert event.auth_type == AuthTokenType.API
    assert event.object == EventObject(
        type=EventCategory.WORKFLOWS,
        id=workflow.id,
        name=workflow.name,
    )
    assert event.payload == {
        'workflow_name': workflow.name,
        'template_id': workflow.template_id,
        'template_name': workflow.template.name
        if workflow.template_id
        else None,
    }


def test_workflow_urgent__not_urgent_workflow__not_urgent_event(fake_stream):

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(
        user=owner,
        tasks_count=1,
        is_urgent=False,
    )

    # act
    AuditEventService.workflow_urgent(
        user=owner,
        auth_type=AuthTokenType.USER,
        workflow=workflow,
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.type == WorkflowEvents.NOT_URGENT
    assert event.auth_type == AuthTokenType.USER
    assert event.object == EventObject(
        type=EventCategory.WORKFLOWS,
        id=workflow.id,
        name=workflow.name,
    )


def test_workflow_urgent__no_user__no_actor_and_no_auth_type(fake_stream):
    """Without a user the record is the system's: an auth type passed
    along is not written."""

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(
        user=owner,
        tasks_count=1,
        is_urgent=True,
    )

    # act
    AuditEventService.workflow_urgent(
        user=None,
        auth_type=AuthTokenType.USER,
        workflow=workflow,
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.type == WorkflowEvents.URGENT
    assert event.account_id == workflow.account_id
    assert event.actor is None
    assert event.auth_type is None


def test_workflow_terminated__workflow__name_and_template_in_payload(
    fake_stream,
):

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(
        user=owner,
        tasks_count=1,
    )

    # act
    AuditEventService.workflow_terminated(
        user=owner,
        auth_type=AuthTokenType.API,
        workflow=workflow,
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.type == WorkflowEvents.TERMINATE
    assert event.category == EventCategory.WORKFLOWS
    assert event.account_id == owner.account_id
    assert event.actor == Actor(
        id=owner.id,
        email=owner.email,
        user_type=UserType.USER,
    )
    assert event.auth_type == AuthTokenType.API
    assert event.object == EventObject(
        type=EventCategory.WORKFLOWS,
        id=workflow.id,
        name=workflow.name,
    )
    assert event.payload == {
        'workflow_name': workflow.name,
        'template_id': workflow.template_id,
        'template_name': workflow.template.name
        if workflow.template_id
        else None,
    }
    assert event.workflow_id == workflow.id
    assert event.task_id is None


def test_task_start__task__start_event_of_the_engine(fake_stream):
    """The engine starts a task: no actor and no auth type, the
    account is the one of the task."""

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(
        user=owner,
        tasks_count=1,
    )
    task = workflow.tasks.get(number=1)

    # act
    AuditEventService.task_start(task=task)
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.type == TaskEvents.START
    assert event.category == EventCategory.TASKS
    assert event.account_id == task.account_id
    assert event.actor is None
    assert event.auth_type is None
    assert event.object == EventObject(
        type=EventCategory.TASKS,
        id=task.id,
        name=task.name,
    )
    assert event.payload == {
        'workflow_name': workflow.name,
        'task_number': 1,
        'task_name': task.name,
    }
    assert event.workflow_id == workflow.id
    assert event.task_id == task.id


def test_task_complete__user__complete_event_with_the_actor(fake_stream):

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(
        user=owner,
        tasks_count=1,
    )
    task = workflow.tasks.get(number=1)

    # act
    AuditEventService.task_complete(
        user=owner,
        auth_type=AuthTokenType.API,
        task=task,
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.type == TaskEvents.COMPLETE
    assert event.category == EventCategory.TASKS
    assert event.account_id == task.account_id
    assert event.actor == Actor(
        id=owner.id,
        email=owner.email,
        user_type=UserType.USER,
    )
    assert event.auth_type == AuthTokenType.API
    assert event.object == EventObject(
        type=EventCategory.TASKS,
        id=task.id,
        name=task.name,
    )
    assert event.payload == {
        'workflow_name': workflow.name,
        'task_number': 1,
        'task_name': task.name,
    }
    assert event.workflow_id == workflow.id
    assert event.task_id == task.id


def test_task_complete__logs_disabled__nothing_emitted(fake_stream, settings):

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(
        user=owner,
        tasks_count=1,
    )
    stored = Task.objects.get(id=workflow.tasks.get(number=1).id)
    settings.LOGS_BACKEND = None

    # act
    AuditEventService.task_complete(
        user=owner,
        auth_type=AuthTokenType.USER,
        task=stored,
    )

    # assert
    assert fake_stream.events == []


def test_task_complete__not_cached_workflow__read_when_enabled(fake_stream):
    """The other side of the guard: with the journal on the workflow
    of the task is read, whether it was cached or not."""

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(
        user=owner,
        tasks_count=1,
        name='Onboarding',
    )
    stored = Task.objects.get(id=workflow.tasks.get(number=1).id)

    # act
    AuditEventService.task_complete(
        user=owner,
        auth_type=AuthTokenType.USER,
        task=stored,
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.payload['workflow_name'] == 'Onboarding'


def test_task_revert__user__revert_event(fake_stream):

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(
        user=owner,
        tasks_count=1,
    )
    task = workflow.tasks.get(number=1)

    # act
    AuditEventService.task_revert(
        user=owner,
        auth_type=AuthTokenType.USER,
        task=task,
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.type == TaskEvents.REVERT
    assert event.category == EventCategory.TASKS
    assert event.actor == Actor(
        id=owner.id,
        email=owner.email,
        user_type=UserType.USER,
    )
    assert event.auth_type == AuthTokenType.USER
    assert event.object == EventObject(
        type=EventCategory.TASKS,
        id=task.id,
        name=task.name,
    )
    assert event.payload == {
        'workflow_name': workflow.name,
        'task_number': 1,
        'task_name': task.name,
    }


def test_task_skip__task__skip_event_of_the_engine(fake_stream):

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(
        user=owner,
        tasks_count=1,
    )
    task = workflow.tasks.get(number=1)

    # act
    AuditEventService.task_skip(task=task)
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.type == TaskEvents.SKIP
    assert event.category == EventCategory.TASKS
    assert event.account_id == task.account_id
    assert event.actor is None
    assert event.auth_type is None
    assert event.object == EventObject(
        type=EventCategory.TASKS,
        id=task.id,
        name=task.name,
    )
    assert event.workflow_id == workflow.id
    assert event.task_id == task.id


def test_task_skip_no_performers__task__skip_no_performers_event(fake_stream):

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(
        user=owner,
        tasks_count=1,
    )
    task = workflow.tasks.get(number=1)

    # act
    AuditEventService.task_skip_no_performers(task=task)
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.type == TaskEvents.SKIP_NO_PERFORMERS
    assert event.category == EventCategory.TASKS
    assert event.actor is None
    assert event.auth_type is None
    assert event.object == EventObject(
        type=EventCategory.TASKS,
        id=task.id,
        name=task.name,
    )
    assert event.payload == {
        'workflow_name': workflow.name,
        'task_number': 1,
        'task_name': task.name,
    }


def test_task_delay__task__delay_event_of_the_engine(fake_stream):

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(
        user=owner,
        tasks_count=1,
    )
    task = workflow.tasks.get(number=1)

    # act
    AuditEventService.task_delay(task=task)
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.type == TaskEvents.DELAY
    assert event.category == EventCategory.TASKS
    assert event.actor is None
    assert event.auth_type is None
    assert event.object == EventObject(
        type=EventCategory.TASKS,
        id=task.id,
        name=task.name,
    )
    assert event.payload == {
        'workflow_name': workflow.name,
        'task_number': 1,
        'task_name': task.name,
    }


def test_task_due_date_changed__due_date__due_date_in_the_payload(fake_stream):

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(
        user=owner,
        tasks_count=1,
    )
    task = workflow.tasks.get(number=1)
    task.due_date = datetime(2026, 10, 1, 9, 30, tzinfo=timezone.utc)

    # act
    AuditEventService.task_due_date_changed(
        user=owner,
        auth_type=AuthTokenType.USER,
        task=task,
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.type == TaskEvents.DUE_DATE_CHANGED
    assert event.category == EventCategory.TASKS
    assert event.actor == Actor(
        id=owner.id,
        email=owner.email,
        user_type=UserType.USER,
    )
    assert event.auth_type == AuthTokenType.USER
    assert event.object == EventObject(
        type=EventCategory.TASKS,
        id=task.id,
        name=task.name,
    )
    assert event.payload == {
        'workflow_name': workflow.name,
        'task_number': 1,
        'task_name': task.name,
        'due_date': '2026-10-01T09:30:00Z',
    }


def test_task_due_date_changed__no_due_date__none_in_the_payload(fake_stream):

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(
        user=owner,
        tasks_count=1,
    )
    task = workflow.tasks.get(number=1)

    # act
    AuditEventService.task_due_date_changed(
        user=owner,
        auth_type=AuthTokenType.USER,
        task=task,
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.type == TaskEvents.DUE_DATE_CHANGED
    assert event.payload == {
        'workflow_name': workflow.name,
        'task_number': 1,
        'task_name': task.name,
        'due_date': None,
    }


def test_task_performer_created__performer__target_in_the_payload(fake_stream):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    performer = create_test_not_admin(
        account=account,
        email='ann@test.test',
    )
    workflow = create_test_workflow(
        user=owner,
        tasks_count=1,
    )
    task = workflow.tasks.get(number=1)

    # act
    AuditEventService.task_performer_created(
        user=owner,
        auth_type=AuthTokenType.USER,
        task=task,
        performer=performer,
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.type == TaskEvents.PERFORMER_CREATED
    assert event.category == EventCategory.TASKS
    assert event.account_id == account.id
    assert event.actor == Actor(
        id=owner.id,
        email=owner.email,
        user_type=UserType.USER,
    )
    assert event.auth_type == AuthTokenType.USER
    assert event.object == EventObject(
        type=EventCategory.TASKS,
        id=task.id,
        name=task.name,
    )
    assert event.payload == {
        'workflow_name': workflow.name,
        'task_number': 1,
        'task_name': task.name,
        'target_user_id': performer.id,
        'target_email': 'ann@test.test',
    }
    assert event.workflow_id == workflow.id
    assert event.task_id == task.id


def test_task_performer_deleted__performer__target_in_the_payload(fake_stream):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    performer = create_test_not_admin(
        account=account,
        email='ann@test.test',
    )
    workflow = create_test_workflow(
        user=owner,
        tasks_count=1,
    )
    task = workflow.tasks.get(number=1)

    # act
    AuditEventService.task_performer_deleted(
        user=owner,
        auth_type=AuthTokenType.API,
        task=task,
        performer=performer,
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.type == TaskEvents.PERFORMER_DELETED
    assert event.category == EventCategory.TASKS
    assert event.auth_type == AuthTokenType.API
    assert event.object == EventObject(
        type=EventCategory.TASKS,
        id=task.id,
        name=task.name,
    )
    assert event.payload == {
        'workflow_name': workflow.name,
        'task_number': 1,
        'task_name': task.name,
        'target_user_id': performer.id,
        'target_email': 'ann@test.test',
    }


def test_task_performer_group_created__group__group_in_the_payload(
    fake_stream,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    group = create_test_group(
        account=account,
        name='Sales',
    )
    workflow = create_test_workflow(
        user=owner,
        tasks_count=1,
    )
    task = workflow.tasks.get(number=1)

    # act
    AuditEventService.task_performer_group_created(
        user=owner,
        auth_type=AuthTokenType.USER,
        task=task,
        group=group,
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.type == TaskEvents.PERFORMER_GROUP_CREATED
    assert event.category == EventCategory.TASKS
    assert event.actor == Actor(
        id=owner.id,
        email=owner.email,
        user_type=UserType.USER,
    )
    assert event.auth_type == AuthTokenType.USER
    assert event.object == EventObject(
        type=EventCategory.TASKS,
        id=task.id,
        name=task.name,
    )
    assert event.payload == {
        'workflow_name': workflow.name,
        'task_number': 1,
        'task_name': task.name,
        'target_group_id': group.id,
        'group_name': 'Sales',
    }


def test_task_performer_group_deleted__group__group_in_the_payload(
    fake_stream,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    group = create_test_group(
        account=account,
        name='Sales',
    )
    workflow = create_test_workflow(
        user=owner,
        tasks_count=1,
    )
    task = workflow.tasks.get(number=1)

    # act
    AuditEventService.task_performer_group_deleted(
        user=owner,
        auth_type=AuthTokenType.USER,
        task=task,
        group=group,
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.type == TaskEvents.PERFORMER_GROUP_DELETED
    assert event.category == EventCategory.TASKS
    assert event.object == EventObject(
        type=EventCategory.TASKS,
        id=task.id,
        name=task.name,
    )
    assert event.payload == {
        'workflow_name': workflow.name,
        'task_number': 1,
        'task_name': task.name,
        'target_group_id': group.id,
        'group_name': 'Sales',
    }


def test_task_delegation__vacation__substitute_group_and_no_actor(fake_stream):
    """The vacation handed the task over, not a person: the record
    names whose vacation it was and the group of the substitutes."""

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    target = create_test_not_admin(account=account)
    substitute_group = create_test_group(account=account)
    workflow = create_test_workflow(
        user=owner,
        tasks_count=1,
    )
    task = workflow.tasks.get(number=1)

    # act
    AuditEventService.task_delegation(
        task=task,
        target=target,
        substitute_group=substitute_group,
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.type == TaskEvents.DELEGATION
    assert event.category == EventCategory.TASKS
    assert event.account_id == account.id
    assert event.actor is None
    assert event.auth_type is None
    assert event.object == EventObject(
        type=EventCategory.TASKS,
        id=task.id,
        name=task.name,
    )
    assert event.payload == {
        'workflow_name': workflow.name,
        'task_number': 1,
        'task_name': task.name,
        'vacation_user_id': target.id,
        'substitute_group_id': substitute_group.id,
        'vacation_user_email': target.email,
        'substitute_group_name': substitute_group.name,
    }
    assert event.workflow_id == workflow.id
    assert event.task_id == task.id


def test_comment_created__comment_with_task__comment_event(fake_stream):

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(
        user=owner,
        tasks_count=1,
    )
    task = workflow.tasks.get(number=1)
    comment = create_test_event(
        workflow=workflow,
        user=owner,
        type_event=WorkflowEventType.COMMENT,
    )

    # act
    AuditEventService.comment_created(
        user=owner,
        auth_type=AuthTokenType.USER,
        comment=comment,
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.type == TaskEvents.COMMENT
    assert event.category == EventCategory.TASKS
    assert event.account_id == owner.account_id
    assert event.actor == Actor(
        id=owner.id,
        email=owner.email,
        user_type=UserType.USER,
    )
    assert event.auth_type == AuthTokenType.USER
    assert event.object == EventObject(
        type=EventCategory.TASKS,
        id=comment.id,
        name=comment.text,
    )
    assert event.payload == {
        'workflow_name': workflow.name,
        'task_name': task.name,
    }
    assert event.workflow_id == workflow.id
    assert event.task_id == task.id


def test_comment_created__logs_disabled__nothing_emitted(
    fake_stream,
    settings,
):

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(
        user=owner,
        tasks_count=1,
    )
    comment = create_test_event(
        workflow=workflow,
        user=owner,
        type_event=WorkflowEventType.COMMENT,
    )
    stored = WorkflowEvent.objects.get(id=comment.id)
    settings.LOGS_BACKEND = None

    # act
    AuditEventService.comment_created(
        user=owner,
        auth_type=AuthTokenType.USER,
        comment=stored,
    )

    # assert
    assert fake_stream.events == []


def test_create_reaction__value__reaction_in_the_payload(fake_stream):
    """The reaction is named, the text of the comment is not: it is
    the content of the customer."""

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(
        user=owner,
        tasks_count=1,
    )
    task = workflow.tasks.get(number=1)
    comment = create_test_event(
        workflow=workflow,
        user=owner,
        type_event=WorkflowEventType.COMMENT,
    )

    # act
    AuditEventService.create_reaction(
        user=owner,
        auth_type=AuthTokenType.USER,
        comment=comment,
        value=':thumbsup:',
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.type == TaskEvents.REACTION_CREATE
    assert event.category == EventCategory.TASKS
    assert event.account_id == owner.account_id
    assert event.actor == Actor(
        id=owner.id,
        email=owner.email,
        user_type=UserType.USER,
    )
    assert event.auth_type == AuthTokenType.USER
    assert event.object == EventObject(
        type=EventCategory.TASKS,
        id=comment.id,
        name=comment.text,
    )
    assert event.payload == {
        'workflow_name': workflow.name,
        'task_name': task.name,
        'reaction': ':thumbsup:',
    }
    assert event.workflow_id == workflow.id
    assert event.task_id == task.id


def test_delete_reaction__value__reaction_in_the_payload(fake_stream):

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(
        user=owner,
        tasks_count=1,
    )
    task = workflow.tasks.get(number=1)
    comment = create_test_event(
        workflow=workflow,
        user=owner,
        type_event=WorkflowEventType.COMMENT,
    )

    # act
    AuditEventService.delete_reaction(
        user=owner,
        auth_type=AuthTokenType.API,
        comment=comment,
        value=':thumbsup:',
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.type == TaskEvents.REACTION_DELETE
    assert event.category == EventCategory.TASKS
    assert event.auth_type == AuthTokenType.API
    assert event.object == EventObject(
        type=EventCategory.TASKS,
        id=comment.id,
        name=comment.text,
    )
    assert event.payload == {
        'workflow_name': workflow.name,
        'task_name': task.name,
        'reaction': ':thumbsup:',
    }


def test_comment_updated__comment_with_task__task_name(fake_stream):

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(
        user=owner,
        tasks_count=1,
    )
    task = workflow.tasks.get(number=1)
    comment = create_test_event(
        workflow=workflow,
        user=owner,
        type_event=WorkflowEventType.COMMENT,
    )

    # act
    AuditEventService.comment_updated(
        user=owner,
        auth_type=AuthTokenType.USER,
        comment=comment,
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.type == TaskEvents.COMMENT_UPDATE
    assert event.account_id == owner.account_id
    assert event.actor == Actor(
        id=owner.id,
        email=owner.email,
        user_type=UserType.USER,
    )
    assert event.auth_type == AuthTokenType.USER
    assert event.object == EventObject(
        type=EventCategory.TASKS,
        id=comment.id,
        name=comment.text,
    )
    assert event.payload == {
        'workflow_name': workflow.name,
        'task_name': task.name,
    }
    assert event.workflow_id == workflow.id
    assert event.task_id == task.id


def test_comment_updated__comment_without_task__task_name_none(fake_stream):

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(
        user=owner,
        tasks_count=1,
    )
    comment = WorkflowEvent.objects.create(
        type=WorkflowEventType.COMMENT,
        account=workflow.account,
        workflow=workflow,
        user=owner,
        task=None,
    )

    # act
    AuditEventService.comment_updated(
        user=owner,
        auth_type=AuthTokenType.USER,
        comment=comment,
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.type == TaskEvents.COMMENT_UPDATE
    assert event.payload == {
        'workflow_name': workflow.name,
        'task_name': None,
    }
    assert event.workflow_id == workflow.id
    assert event.task_id is None


def test_comment_deleted__comment__comment_object(fake_stream):

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(
        user=owner,
        tasks_count=1,
    )
    task = workflow.tasks.get(number=1)
    comment = create_test_event(
        workflow=workflow,
        user=owner,
        type_event=WorkflowEventType.COMMENT,
    )

    # act
    AuditEventService.comment_deleted(
        user=owner,
        auth_type=AuthTokenType.USER,
        comment=comment,
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.type == TaskEvents.COMMENT_DELETE
    assert event.object == EventObject(
        type=EventCategory.TASKS,
        id=comment.id,
        name=comment.text,
    )
    assert event.payload == {
        'workflow_name': workflow.name,
        'task_name': task.name,
    }
    assert event.workflow_id == workflow.id
    assert event.task_id == task.id


def test_checklist_item_marked__checklist__checklist_object(fake_stream):

    # arrange
    owner = create_test_owner()
    template = create_test_template(
        user=owner,
        is_active=True,
        tasks_count=1,
    )
    create_checklist_template(task_template=template.tasks.get(number=1))
    workflow = create_test_workflow(
        user=owner,
        template=template,
    )
    task = workflow.tasks.get(number=1)
    checklist = task.checklists.get()
    selection = ChecklistSelection.objects.get(
        checklist=checklist,
        api_name='cl-selection-1',
    )

    # act
    AuditEventService.checklist_item_marked(
        user=owner,
        auth_type=AuthTokenType.USER,
        selection=selection,
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.type == TaskEvents.CHECKLIST_MARK
    assert event.account_id == owner.account_id
    assert event.actor == Actor(
        id=owner.id,
        email=owner.email,
        user_type=UserType.USER,
    )
    assert event.auth_type == AuthTokenType.USER
    assert event.object == EventObject(
        type=EventCategory.TASKS,
        id=checklist.id,
        name=selection.value,
    )
    assert event.payload == {
        'workflow_name': workflow.name,
        'task_name': task.name,
        'checklist_api_name': 'checklist',
        'selection_id': selection.id,
        'workflow_id': workflow.id,
        'task_id': task.id,
        'checklist_id': checklist.id,
        'selection_api_name': selection.api_name,
        'selection_value': selection.value,
    }
    assert event.workflow_id == workflow.id
    assert event.task_id == task.id


def test_checklist_item_unmarked__checklist__checklist_object(fake_stream):

    # arrange
    owner = create_test_owner()
    template = create_test_template(
        user=owner,
        is_active=True,
        tasks_count=1,
    )
    create_checklist_template(task_template=template.tasks.get(number=1))
    workflow = create_test_workflow(
        user=owner,
        template=template,
    )
    task = workflow.tasks.get(number=1)
    checklist = task.checklists.get()
    selection = ChecklistSelection.objects.get(
        checklist=checklist,
        api_name='cl-selection-1',
    )

    # act
    AuditEventService.checklist_item_unmarked(
        user=owner,
        auth_type=AuthTokenType.USER,
        selection=selection,
    )
    event = fake_stream.last_event()

    # assert
    assert len(fake_stream.events) == 1
    assert event.type == TaskEvents.CHECKLIST_UNMARK
    assert event.object == EventObject(
        type=EventCategory.TASKS,
        id=checklist.id,
        name=selection.value,
    )
    assert event.payload == {
        'workflow_name': workflow.name,
        'task_name': task.name,
        'checklist_api_name': 'checklist',
        'selection_id': selection.id,
        'workflow_id': workflow.id,
        'task_id': task.id,
        'checklist_id': checklist.id,
        'selection_api_name': selection.api_name,
        'selection_value': selection.value,
    }
    assert event.workflow_id == workflow.id
    assert event.task_id == task.id


def test_checklist_item_marked__logs_disabled__nothing_emitted(
    fake_stream,
    settings,
):

    # arrange
    owner = create_test_owner()
    template = create_test_template(
        user=owner,
        is_active=True,
        tasks_count=1,
    )
    create_checklist_template(task_template=template.tasks.get(number=1))
    workflow = create_test_workflow(
        user=owner,
        template=template,
    )
    checklist = workflow.tasks.get(number=1).checklists.get()
    selection = ChecklistSelection.objects.get(
        checklist=checklist,
        api_name='cl-selection-1',
    )
    settings.LOGS_BACKEND = None

    # act
    AuditEventService.checklist_item_marked(
        user=owner,
        auth_type=AuthTokenType.USER,
        selection=selection,
    )

    # assert
    assert fake_stream.events == []


@pytest.mark.parametrize('backend', [None, ''])
def test_vacation_activated__logs_disabled__no_queries(
    fake_stream,
    settings,
    django_assert_num_queries,
    backend,
):
    """Disabled audit must not evaluate substitutes or read the account."""

    # arrange
    owner = create_test_owner()
    substitute = create_test_admin(account=owner.account)
    target = UserModel.objects.get(id=owner.id)
    substitutes = UserModel.objects.filter(id=substitute.id)
    settings.LOGS_BACKEND = backend

    # act
    with django_assert_num_queries(0):
        AuditEventService.vacation_activated(
            user=None,
            auth_type=None,
            target=target,
            substitute_users=substitutes,
            absence_status=AbsenceStatus.VACATION,
            start_date=None,
            end_date=None,
            delegated_tasks_count=0,
            is_update=False,
        )

    # assert
    assert fake_stream.events == []
