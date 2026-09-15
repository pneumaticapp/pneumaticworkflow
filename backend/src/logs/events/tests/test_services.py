from datetime import date

import pytest

from src.accounts.enums import (
    AbsenceStatus,
    BillingPlanType,
    UserStatus,
    UserType,
)
from src.authentication.enums import AuthTokenType
from src.logs.events.emitter import NO_ACCOUNT
from src.logs.events.enums import (
    AccountEvents,
    ApiKeyEvents,
    BillingEvents,
    DatasetEvents,
    EventCategory,
    EventObjectType,
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
from src.logs.events.schema import Actor, EventObject
from src.logs.events.services import AuditEventService
from src.processes.enums import WorkflowEventType
from src.processes.models.workflows.checklist import ChecklistSelection
from src.processes.tests.fixtures import (
    create_checklist_template,
    create_test_account,
    create_test_admin,
    create_test_api_key,
    create_test_dataset,
    create_test_event,
    create_test_group,
    create_test_not_admin,
    create_test_owner,
    create_test_shared_fieldset,
    create_test_system_template,
    create_test_template,
    create_test_template_preset,
    create_test_workflow,
)

pytestmark = pytest.mark.django_db


# Authentication


def test_user_logged_in__request_context__login_event_with_the_address(
    fake_stream,
    request_context,
):

    """ The address, the browser and the request id come from the
        context the middleware published; who acts and how they were
        authenticated come from the caller. """

    # arrange
    user = create_test_owner()

    # act
    AuditEventService.user_logged_in(user=user, source='email')

    # assert
    event = fake_stream.last_event()
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
    assert event.object == EventObject(type=EventObjectType.USER, id=user.id)
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
    AuditEventService.user_signed_up(user=user, source='google')

    # assert
    event = fake_stream.last_event()
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
    assert event.object == EventObject(type=EventObjectType.USER, id=user.id)
    assert event.payload == {'source': 'google'}
    assert event.ip is None
    assert event.user_agent is None
    assert event.request_id is None


def test_login_failed__email__normalized_email_and_no_account(
    fake_stream,
):

    """ The attempt is anonymous, no actor and no auth type, and the
        event belongs to no account: a failed sign in is the bucket
        an alert on a brute force burst is built on. """

    # arrange
    email = ' Ann@Test.test '

    # act
    AuditEventService.login_failed(
        reason=LoginFailedReason.BAD_CREDENTIALS,
        email=email,
    )

    # assert
    event = fake_stream.last_event()
    assert len(fake_stream.events) == 1
    assert event.type == UserEvents.LOGIN_FAILED
    assert event.category == EventCategory.USERS
    assert event.account_id == NO_ACCOUNT
    assert event.actor is None
    assert event.auth_type is None
    assert event.object == EventObject(type=EventObjectType.USER)
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

    # assert
    event = fake_stream.last_event()
    assert len(fake_stream.events) == 1
    assert event.payload == {
        'email': '',
        'reason': LoginFailedReason.SSO_REQUIRED,
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

    # assert
    event = fake_stream.last_event()
    assert len(fake_stream.events) == 1
    assert event.type == UserEvents.LOGOUT
    assert event.account_id == user.account_id
    assert event.actor == Actor(
        id=user.id,
        email=user.email,
        user_type=UserType.USER,
    )
    assert event.auth_type == AuthTokenType.API
    assert event.object == EventObject(type=EventObjectType.USER, id=user.id)
    assert event.payload == {'auth_type': AuthTokenType.API}


def test_user_logged_out_by_provider__target__no_actor(fake_stream):

    """ The identity provider ended the sessions, not the person. """

    # arrange
    target = create_test_owner()

    # act
    AuditEventService.user_logged_out_by_provider(
        target=target,
        source='okta',
    )

    # assert
    event = fake_stream.last_event()
    assert len(fake_stream.events) == 1
    assert event.type == UserEvents.LOGOUT
    assert event.account_id == target.account_id
    assert event.actor is None
    assert event.auth_type is None
    assert event.object == EventObject(
        type=EventObjectType.USER,
        id=target.id,
    )
    assert event.payload == {
        'source': 'okta',
        'reason': LogoutReason.IDENTITY_PROVIDER,
    }


def test_superuser_logged_in_as__target__target_account_and_email(
    fake_stream,
):

    # arrange
    staff = create_test_owner(email='staff@test.test')
    target = create_test_owner(email='target@test.test')

    # act
    AuditEventService.superuser_logged_in_as(
        user=staff,
        auth_type=AuthTokenType.USER,
        target=target,
    )

    # assert
    event = fake_stream.last_event()
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
        type=EventObjectType.USER,
        id=target.id,
    )
    assert event.payload == {'target_email': 'target@test.test'}


def test_tenant_logged_in_as__master_user__tenant_account_object(
    fake_stream,
):

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

    # assert
    event = fake_stream.last_event()
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
        type=EventObjectType.ACCOUNT,
        id=tenant_account.id,
    )
    assert event.payload == {'master_account_id': master.account_id}


def test_password_reset_requested__known_address__no_actor(fake_stream):

    # arrange
    target = create_test_owner()

    # act
    AuditEventService.password_reset_requested(target=target)

    # assert
    event = fake_stream.last_event()
    assert len(fake_stream.events) == 1
    assert event.type == UserEvents.PASSWORD_RESET_REQUEST
    assert event.category == EventCategory.USERS
    assert event.account_id == target.account_id
    assert event.actor is None
    assert event.auth_type is None
    assert event.object == EventObject(
        type=EventObjectType.USER,
        id=target.id,
    )
    assert event.payload == {'target_email': target.email}


def test_password_reset__user__user_of_the_link_acts(fake_stream):

    # arrange
    user = create_test_owner()

    # act
    AuditEventService.password_reset(user=user)

    # assert
    event = fake_stream.last_event()
    assert len(fake_stream.events) == 1
    assert event.type == UserEvents.PASSWORD_RESET
    assert event.account_id == user.account_id
    assert event.actor == Actor(
        id=user.id,
        email=user.email,
        user_type=UserType.USER,
    )
    assert event.auth_type is None
    assert event.object == EventObject(type=EventObjectType.USER, id=user.id)
    assert event.payload == {}


def test_password_changed__api_key__api_auth_type(fake_stream):

    # arrange
    user = create_test_owner()

    # act
    AuditEventService.password_changed(
        user=user,
        auth_type=AuthTokenType.API,
    )

    # assert
    event = fake_stream.last_event()
    assert len(fake_stream.events) == 1
    assert event.type == UserEvents.PASSWORD_CHANGE
    assert event.account_id == user.account_id
    assert event.actor == Actor(
        id=user.id,
        email=user.email,
        user_type=UserType.USER,
    )
    assert event.auth_type == AuthTokenType.API
    assert event.object == EventObject(type=EventObjectType.USER, id=user.id)
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

    # assert
    event = fake_stream.last_event()
    assert len(fake_stream.events) == 1
    assert event.type == UserEvents.PASSWORD_CHANGE
    assert event.account_id == user.account_id
    assert event.actor == Actor(
        id=user.id,
        email=user.email,
        user_type=UserType.USER,
    )
    assert event.auth_type == AuthTokenType.USER
    assert event.object == EventObject(type=EventObjectType.USER, id=user.id)
    assert event.payload == {}


def test_password_set__another_person__password_set_event_with_target(
    fake_stream,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    target = create_test_not_admin(account=account, email='ann@test.test')

    # act
    AuditEventService.password_set(
        user=owner,
        auth_type=AuthTokenType.USER,
        target=target,
    )

    # assert
    event = fake_stream.last_event()
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
        type=EventObjectType.USER,
        id=target.id,
    )
    assert event.payload == {'target_email': 'ann@test.test'}


def test_password_set__no_user__no_actor_and_target_account(
    fake_stream,
):

    # arrange
    target = create_test_owner()

    # act
    AuditEventService.password_set(
        user=None,
        auth_type=None,
        target=target,
    )

    # assert
    event = fake_stream.last_event()
    assert len(fake_stream.events) == 1
    assert event.type == UserEvents.PASSWORD_SET
    assert event.account_id == target.account_id
    assert event.actor is None
    assert event.auth_type is None
    assert event.object == EventObject(
        type=EventObjectType.USER,
        id=target.id,
    )
    assert event.payload == {'target_email': target.email}


# Accounts, users, groups, invites and API keys


def test_user_created__admin__target_in_the_payload(fake_stream):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    target = create_test_not_admin(account=account, email='new@test.test')

    # act
    AuditEventService.user_created(
        user=owner,
        auth_type=AuthTokenType.USER,
        target=target,
    )

    # assert
    event = fake_stream.last_event()
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
        type=EventObjectType.USER,
        id=target.id,
    )
    assert event.payload == {
        'target_email': 'new@test.test',
        'is_admin': False,
    }


def test_user_updated__email_changed__previous_email_in_the_payload(
    fake_stream,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    target = create_test_not_admin(account=account, email='new@test.test')

    # act
    AuditEventService.user_updated(
        user=owner,
        auth_type=AuthTokenType.USER,
        target=target,
        changed_fields=['email', 'first_name'],
        previous_email='old@test.test',
        group_changes={},
    )

    # assert
    event = fake_stream.last_event()
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
        type=EventObjectType.USER,
        id=target.id,
    )
    assert event.payload == {
        'target_email': 'new@test.test',
        'changed_fields': ['email', 'first_name'],
        'previous_email': 'old@test.test',
    }


def test_user_updated__manager_and_groups_changed__ids_in_the_payload(
    fake_stream,
):

    """ The previous address is named only when the address changed;
        the manager by id, and the group changes as the caller counted
        them. """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    manager = create_test_admin(account=account)
    target = create_test_not_admin(account=account)
    target.manager = manager
    target.save()
    group = create_test_group(account=account)

    # act
    AuditEventService.user_updated(
        user=owner,
        auth_type=AuthTokenType.USER,
        target=target,
        changed_fields=['manager', 'groups'],
        previous_email=target.email,
        group_changes={
            'added_groups_ids': [group.id],
            'removed_groups_ids': [],
        },
    )

    # assert
    event = fake_stream.last_event()
    assert len(fake_stream.events) == 1
    assert event.type == UserEvents.UPDATE
    assert event.payload == {
        'target_email': target.email,
        'changed_fields': ['manager', 'groups'],
        'added_groups_ids': [group.id],
        'removed_groups_ids': [],
        'manager_id': manager.id,
    }


def test_user_updated__is_admin_changed__update_and_admin_toggle_events(
    fake_stream,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    target = create_test_admin(account=account, email='ann@test.test')

    # act
    AuditEventService.user_updated(
        user=owner,
        auth_type=AuthTokenType.USER,
        target=target,
        changed_fields=['is_admin'],
        previous_email=target.email,
        group_changes={},
    )

    # assert
    assert len(fake_stream.events) == 2
    update = fake_stream.events[0][1]
    toggle = fake_stream.events[1][1]
    assert update.type == UserEvents.UPDATE
    assert update.payload == {
        'target_email': 'ann@test.test',
        'changed_fields': ['is_admin'],
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
        type=EventObjectType.USER,
        id=target.id,
    )
    assert toggle.payload == {
        'is_admin': True,
        'target_email': 'ann@test.test',
    }


def test_user_updated__password_changed__update_and_password_set_events(
    fake_stream,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    target = create_test_not_admin(account=account, email='ann@test.test')

    # act
    AuditEventService.user_updated(
        user=owner,
        auth_type=AuthTokenType.USER,
        target=target,
        changed_fields=['password'],
        previous_email=target.email,
        group_changes={},
    )

    # assert
    assert len(fake_stream.events) == 2
    update = fake_stream.events[0][1]
    password_set = fake_stream.events[1][1]
    assert update.type == UserEvents.UPDATE
    assert update.payload == {
        'target_email': 'ann@test.test',
        'changed_fields': ['password'],
    }
    assert password_set.type == UserEvents.PASSWORD_SET
    assert password_set.account_id == account.id
    assert password_set.object == EventObject(
        type=EventObjectType.USER,
        id=target.id,
    )
    assert password_set.payload == {'target_email': 'ann@test.test'}


def test_user_updated__no_changed_fields__no_event(fake_stream):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    target = create_test_not_admin(account=account)

    # act
    AuditEventService.user_updated(
        user=owner,
        auth_type=AuthTokenType.USER,
        target=target,
        changed_fields=[],
        previous_email=target.email,
        group_changes={},
    )

    # assert
    assert fake_stream.events == []


def test_user_admin_toggled__admin_revoked__is_admin_false_in_payload(
    fake_stream,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    target = create_test_not_admin(account=account, email='ann@test.test')

    # act
    AuditEventService.user_admin_toggled(
        user=owner,
        auth_type=AuthTokenType.API,
        target=target,
    )

    # assert
    event = fake_stream.last_event()
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
        type=EventObjectType.USER,
        id=target.id,
    )
    assert event.payload == {
        'is_admin': False,
        'target_email': 'ann@test.test',
    }


def test_user_deactivated__admin__status_before_in_the_payload(
    fake_stream,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    target = create_test_not_admin(account=account, email='ann@test.test')

    # act
    AuditEventService.user_deactivated(
        user=owner,
        auth_type=AuthTokenType.USER,
        target=target,
        status_before=UserStatus.ACTIVE,
    )

    # assert
    event = fake_stream.last_event()
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
        type=EventObjectType.USER,
        id=target.id,
    )
    assert event.payload == {
        'target_email': 'ann@test.test',
        'status_before': UserStatus.ACTIVE,
    }


def test_user_transferred__new_user__previous_account_in_the_payload(
    fake_stream,
):

    """ Into the journal of the account the person moved to. """

    # arrange
    prev_user = create_test_owner(email='prev@test.test')
    account = create_test_account()
    user = create_test_not_admin(account=account, email='ann@test.test')

    # act
    AuditEventService.user_transferred(
        user=user,
        auth_type=AuthTokenType.USER,
        prev_user=prev_user,
    )

    # assert
    event = fake_stream.last_event()
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
    assert event.object == EventObject(type=EventObjectType.USER, id=user.id)
    assert event.payload == {
        'prev_account_id': prev_user.account_id,
        'prev_user_id': prev_user.id,
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

    # assert
    event = fake_stream.last_event()
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
        type=EventObjectType.GROUP,
        id=group.id,
    )
    assert event.payload == {
        'old_user_id': None,
        'old_group_id': group.id,
        'new_user_id': new_user.id,
        'new_group_id': None,
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

    # assert
    event = fake_stream.last_event()
    assert len(fake_stream.events) == 1
    assert event.type == UserEvents.REASSIGN
    assert event.object == EventObject(
        type=EventObjectType.USER,
        id=old_user.id,
    )
    assert event.payload == {
        'old_user_id': old_user.id,
        'old_group_id': None,
        'new_user_id': None,
        'new_group_id': new_group.id,
    }


def test_user_unsubscribed__email_type__user_of_the_link_acts(fake_stream):

    # arrange
    user = create_test_owner()

    # act
    AuditEventService.user_unsubscribed(user=user, email_type='digest')

    # assert
    event = fake_stream.last_event()
    assert len(fake_stream.events) == 1
    assert event.type == UserEvents.UNSUBSCRIBE
    assert event.account_id == user.account_id
    assert event.actor == Actor(
        id=user.id,
        email=user.email,
        user_type=UserType.USER,
    )
    assert event.auth_type is None
    assert event.object == EventObject(type=EventObjectType.USER, id=user.id)
    assert event.payload == {'email_type': 'digest'}


def test_vacation_activated__scheduled__no_actor_sorted_substitutes(
    fake_stream,
):

    """ A scheduled task turns the vacation on: nobody acts, and the
        account is the one of the person on vacation. """

    # arrange
    target = create_test_owner(email='ann@test.test')

    # act
    AuditEventService.vacation_activated(
        user=None,
        auth_type=None,
        target=target,
        substitute_user_ids=[30, 10, 20],
        absence_status=AbsenceStatus.VACATION,
        start_date=date(2026, 9, 1),
        end_date=date(2026, 9, 14),
        delegated_tasks_count=3,
        is_update=False,
    )

    # assert
    event = fake_stream.last_event()
    assert len(fake_stream.events) == 1
    assert event.type == UserEvents.VACATION_ACTIVATE
    assert event.category == EventCategory.USERS
    assert event.account_id == target.account_id
    assert event.actor is None
    assert event.auth_type is None
    assert event.object == EventObject(
        type=EventObjectType.USER,
        id=target.id,
    )
    assert event.payload == {
        'target_email': 'ann@test.test',
        'substitute_user_ids': [10, 20, 30],
        'absence_status': AbsenceStatus.VACATION,
        'start_date': '2026-09-01',
        'end_date': '2026-09-14',
        'delegated_tasks_count': 3,
        'is_update': False,
    }


def test_vacation_deactivated__admin__target_in_the_payload(fake_stream):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    target = create_test_not_admin(account=account, email='ann@test.test')

    # act
    AuditEventService.vacation_deactivated(
        user=owner,
        auth_type=AuthTokenType.USER,
        target=target,
    )

    # assert
    event = fake_stream.last_event()
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
        type=EventObjectType.USER,
        id=target.id,
    )
    assert event.payload == {'target_email': 'ann@test.test'}


def test_account_updated__changed_fields__names_only(fake_stream):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)

    # act
    AuditEventService.account_updated(
        user=owner,
        auth_type=AuthTokenType.USER,
        account=account,
        changed_fields=['logo_lg', 'name'],
    )

    # assert
    event = fake_stream.last_event()
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
        type=EventObjectType.ACCOUNT,
        id=account.id,
    )
    assert event.payload == {'changed_fields': ['logo_lg', 'name']}


def test_account_verified__user__user_of_the_link_acts(fake_stream):

    # arrange
    user = create_test_owner()

    # act
    AuditEventService.account_verified(user=user)

    # assert
    event = fake_stream.last_event()
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
        type=EventObjectType.ACCOUNT,
        id=user.account_id,
    )
    assert event.payload == {}


def test_verification_resent__owner__account_object_with_target(
    fake_stream,
):

    # arrange
    owner = create_test_owner()

    # act
    AuditEventService.verification_resent(
        user=owner,
        auth_type=AuthTokenType.USER,
        account_owner=owner,
    )

    # assert
    event = fake_stream.last_event()
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
        type=EventObjectType.ACCOUNT,
        id=owner.account_id,
    )
    assert event.payload == {'target_email': owner.email}


def test_tenant_created__master_user__tenant_in_master_account(
    fake_stream,
):

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

    # assert
    event = fake_stream.last_event()
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
        type=EventObjectType.ACCOUNT,
        id=tenant.id,
    )
    assert event.payload == {
        'name': 'Tenant',
        'billing_plan': BillingPlanType.PREMIUM,
    }


def test_tenant_deleted__master_user__tenant_in_master_account(
    fake_stream,
):

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

    # assert
    event = fake_stream.last_event()
    assert len(fake_stream.events) == 1
    assert event.type == AccountEvents.TENANT_DELETE
    assert event.account_id == master.account_id
    assert event.object == EventObject(
        type=EventObjectType.ACCOUNT,
        id=tenant.id,
    )
    assert event.payload == {
        'name': 'Tenant',
        'billing_plan': BillingPlanType.PREMIUM,
    }


def test_invite_created__transfer__target_and_no_object_id(fake_stream):

    """ The id of an invite is the key that accepts it: it stays
        out of the journal. """

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

    # assert
    event = fake_stream.last_event()
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
    assert event.object == EventObject(type=EventObjectType.INVITE)
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

    # assert
    event = fake_stream.last_event()
    assert len(fake_stream.events) == 1
    assert event.type == UserEvents.INVITE_RESEND
    assert event.account_id == account.id
    assert event.actor == Actor(
        id=owner.id,
        email=owner.email,
        user_type=UserType.USER,
    )
    assert event.auth_type == AuthTokenType.API
    assert event.object == EventObject(type=EventObjectType.INVITE)
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
        invited_by_id=owner.id,
    )

    # assert
    event = fake_stream.last_event()
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
    assert event.object == EventObject(type=EventObjectType.INVITE)
    assert event.payload == {'invited_by_id': owner.id}


def test_group_created__users__name_and_users_ids(fake_stream):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    member = create_test_not_admin(account=account)
    group = create_test_group(account=account, name='Sales')

    # act
    AuditEventService.group_created(
        user=owner,
        auth_type=AuthTokenType.USER,
        group=group,
        users_ids=[member.id],
    )

    # assert
    event = fake_stream.last_event()
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
        type=EventObjectType.GROUP,
        id=group.id,
    )
    assert event.payload == {'name': 'Sales', 'users_ids': [member.id]}


def test_group_updated__changed_fields__sorted_fields_and_user_changes(
    fake_stream,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    added = create_test_not_admin(account=account, email='a@test.test')
    removed = create_test_not_admin(account=account, email='b@test.test')
    group = create_test_group(account=account, name='Sales')

    # act
    AuditEventService.group_updated(
        user=owner,
        auth_type=AuthTokenType.USER,
        group=group,
        changed_fields=['users', 'name'],
        added_users_ids=[added.id],
        removed_users_ids=[removed.id],
    )

    # assert
    event = fake_stream.last_event()
    assert len(fake_stream.events) == 1
    assert event.type == GroupEvents.UPDATE
    assert event.category == EventCategory.GROUPS
    assert event.account_id == account.id
    assert event.object == EventObject(
        type=EventObjectType.GROUP,
        id=group.id,
    )
    assert event.payload == {
        'changed_fields': ['name', 'users'],
        'added_users_ids': [added.id],
        'removed_users_ids': [removed.id],
    }


def test_group_updated__no_changed_fields__no_event(fake_stream):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    group = create_test_group(account=account)

    # act
    AuditEventService.group_updated(
        user=owner,
        auth_type=AuthTokenType.USER,
        group=group,
        changed_fields=[],
        added_users_ids=[],
        removed_users_ids=[],
    )

    # assert
    assert fake_stream.events == []


def test_group_deleted__users__name_and_users_ids(fake_stream):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    member = create_test_not_admin(account=account)
    group = create_test_group(account=account, name='Sales')

    # act
    AuditEventService.group_deleted(
        user=owner,
        auth_type=AuthTokenType.USER,
        group=group,
        users_ids=[member.id],
    )

    # assert
    event = fake_stream.last_event()
    assert len(fake_stream.events) == 1
    assert event.type == GroupEvents.DELETE
    assert event.category == EventCategory.GROUPS
    assert event.account_id == account.id
    assert event.object == EventObject(
        type=EventObjectType.GROUP,
        id=group.id,
    )
    assert event.payload == {'name': 'Sales', 'users_ids': [member.id]}


def test_api_key_created__api_key__name_and_owner_without_the_token(
    fake_stream,
):

    """ Neither the raw key nor the token row may reach the journal:
        the payload names the key and its owner and nothing else. """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    api_key = create_test_api_key(user=owner, name='CI')

    # act
    AuditEventService.api_key_created(
        user=owner,
        auth_type=AuthTokenType.USER,
        api_key=api_key,
    )

    # assert
    event = fake_stream.last_event()
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
        type=EventObjectType.API_KEY,
        id=api_key.id,
    )
    assert event.payload == {'name': 'CI', 'target_user_id': owner.id}


def test_api_key_revoked__api_key__name_and_owner_without_the_token(
    fake_stream,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    api_key = create_test_api_key(user=owner, name='CI')

    # act
    AuditEventService.api_key_revoked(
        user=owner,
        auth_type=AuthTokenType.USER,
        api_key=api_key,
    )

    # assert
    event = fake_stream.last_event()
    assert len(fake_stream.events) == 1
    assert event.type == ApiKeyEvents.REVOKE
    assert event.category == EventCategory.API_KEYS
    assert event.account_id == account.id
    assert event.object == EventObject(
        type=EventObjectType.API_KEY,
        id=api_key.id,
    )
    assert event.payload == {'name': 'CI', 'target_user_id': owner.id}


# Billing


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
    )

    # assert
    event = fake_stream.last_event()
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
        type=EventObjectType.ACCOUNT,
        id=owner.account_id,
    )
    assert event.payload == {
        'products': {'unlimited_month': 1, 'extra_users': 2},
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
    )

    # assert
    event = fake_stream.last_event()
    assert len(fake_stream.events) == 1
    assert event.payload == {'products': {'extra_users': 5}}


def test_subscription_cancelled__owner__account_object(fake_stream):

    # arrange
    owner = create_test_owner()

    # act
    AuditEventService.subscription_cancelled(
        user=owner,
        auth_type=AuthTokenType.USER,
    )

    # assert
    event = fake_stream.last_event()
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
        type=EventObjectType.ACCOUNT,
        id=owner.account_id,
    )
    assert event.payload == {}


def test_payment_confirmed__no_subscription_data__empty_payload(
    fake_stream,
):

    # arrange
    user = create_test_owner()

    # act
    AuditEventService.payment_confirmed(
        user=user,
        auth_type=None,
        subscription_data=None,
    )

    # assert
    event = fake_stream.last_event()
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
        type=EventObjectType.ACCOUNT,
        id=user.account_id,
    )
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

    # assert
    event = fake_stream.last_event()
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


# Webhooks


def test_webhook_subscribed__url__url_and_event_in_the_payload(
    fake_stream,
):

    # arrange
    owner = create_test_owner()

    # act
    AuditEventService.webhook_subscribed(
        user=owner,
        auth_type=AuthTokenType.API,
        url='https://hooks.test/in',
        event='workflow_completed',
    )

    # assert
    event = fake_stream.last_event()
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
    assert event.object == EventObject(type=EventObjectType.WEBHOOK)
    assert event.payload == {
        'url': 'https://hooks.test/in',
        'event': 'workflow_completed',
    }


def test_webhook_unsubscribed__url__url_and_event_in_the_payload(
    fake_stream,
):

    # arrange
    owner = create_test_owner()

    # act
    AuditEventService.webhook_unsubscribed(
        user=owner,
        auth_type=AuthTokenType.USER,
        url='https://hooks.test/in',
        event='task_completed_v2',
    )

    # assert
    event = fake_stream.last_event()
    assert len(fake_stream.events) == 1
    assert event.type == WebhookEvents.UNSUBSCRIBE
    assert event.category == EventCategory.WEBHOOKS
    assert event.account_id == owner.account_id
    assert event.object == EventObject(type=EventObjectType.WEBHOOK)
    assert event.payload == {
        'url': 'https://hooks.test/in',
        'event': 'task_completed_v2',
    }


# Templates


def test_template_saved__active_template__publish_event(fake_stream):

    # arrange
    owner = create_test_owner()
    template = create_test_template(user=owner, is_active=True)

    # act
    AuditEventService.template_saved(
        user=owner,
        auth_type=AuthTokenType.USER,
        template=template,
        name='Onboarding',
    )

    # assert
    event = fake_stream.last_event()
    assert len(fake_stream.events) == 1
    assert event.type == TemplateEvents.PUBLISH
    assert event.category == EventCategory.TEMPLATES
    assert event.account_id == owner.account_id
    assert event.actor == Actor(
        id=owner.id,
        email=owner.email,
        user_type=UserType.USER,
    )
    assert event.auth_type == AuthTokenType.USER
    assert event.object == EventObject(
        type=EventObjectType.TEMPLATE,
        id=template.id,
    )
    assert event.payload == {
        'name': 'Onboarding',
        'version': template.version,
        'is_active': True,
    }


def test_template_saved__draft__draft_save_event(fake_stream):

    """ A published template and a draft are two different types. """

    # arrange
    owner = create_test_owner()
    template = create_test_template(user=owner, is_active=False)

    # act
    AuditEventService.template_saved(
        user=owner,
        auth_type=AuthTokenType.USER,
        template=template,
        name='Draft name',
    )

    # assert
    event = fake_stream.last_event()
    assert len(fake_stream.events) == 1
    assert event.type == TemplateEvents.DRAFT_SAVE
    assert event.category == EventCategory.TEMPLATES
    assert event.payload == {
        'name': 'Draft name',
        'version': template.version,
        'is_active': False,
    }


def test_template_saved__source__source_in_the_payload(fake_stream):

    # arrange
    owner = create_test_owner()
    template = create_test_template(user=owner, is_active=True)

    # act
    AuditEventService.template_saved(
        user=owner,
        auth_type=AuthTokenType.USER,
        template=template,
        name='Onboarding',
        source=TemplateSource.LIBRARY,
    )

    # assert
    event = fake_stream.last_event()
    assert len(fake_stream.events) == 1
    assert event.type == TemplateEvents.PUBLISH
    assert event.payload == {
        'name': 'Onboarding',
        'version': template.version,
        'is_active': True,
        'source': TemplateSource.LIBRARY,
    }


def test_template_saved__empty_source__no_source_key(fake_stream):

    # arrange
    owner = create_test_owner()
    template = create_test_template(user=owner, is_active=False)

    # act
    AuditEventService.template_saved(
        user=owner,
        auth_type=AuthTokenType.USER,
        template=template,
        name='Draft name',
        source='',
    )

    # assert
    event = fake_stream.last_event()
    assert len(fake_stream.events) == 1
    assert event.type == TemplateEvents.DRAFT_SAVE
    assert event.payload == {
        'name': 'Draft name',
        'version': template.version,
        'is_active': False,
    }


def test_template_cloned__template__clone_event(fake_stream):

    # arrange
    owner = create_test_owner()
    template = create_test_template(user=owner, is_active=False)

    # act
    AuditEventService.template_cloned(
        user=owner,
        auth_type=AuthTokenType.USER,
        template=template,
        name='Copy of Onboarding',
    )

    # assert
    event = fake_stream.last_event()
    assert len(fake_stream.events) == 1
    assert event.type == TemplateEvents.CLONE
    assert event.category == EventCategory.TEMPLATES
    assert event.object == EventObject(
        type=EventObjectType.TEMPLATE,
        id=template.id,
    )
    assert event.payload == {
        'name': 'Copy of Onboarding',
        'version': template.version,
        'is_active': False,
    }


def test_template_deleted__template__delete_event_with_the_name(
    fake_stream,
):

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

    # assert
    event = fake_stream.last_event()
    assert len(fake_stream.events) == 1
    assert event.type == TemplateEvents.DELETE
    assert event.category == EventCategory.TEMPLATES
    assert event.object == EventObject(
        type=EventObjectType.TEMPLATE,
        id=template.id,
    )
    assert event.payload == {
        'name': 'Offboarding',
        'version': template.version,
        'is_active': True,
    }


def test_templates_exported__api_key__filters_and_no_object_id(
    fake_stream,
):

    """ The export is a bulk read: the filters say what left. """

    # arrange
    owner = create_test_owner()

    # act
    AuditEventService.templates_exported(
        user=owner,
        auth_type=AuthTokenType.API,
        filters={'is_active': True, 'ordering': 'name'},
    )

    # assert
    event = fake_stream.last_event()
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
    assert event.object == EventObject(type=EventObjectType.TEMPLATE)
    assert event.payload == {
        'filters': {'is_active': True, 'ordering': 'name'},
    }


def test_template_draft_discarded__never_published__template_deleted(
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
    AuditEventService.template_draft_discarded(
        user=owner,
        auth_type=AuthTokenType.USER,
        template=template,
        template_deleted=True,
    )

    # assert
    event = fake_stream.last_event()
    assert len(fake_stream.events) == 1
    assert event.type == TemplateEvents.DRAFT_DISCARD
    assert event.object == EventObject(
        type=EventObjectType.TEMPLATE,
        id=template.id,
    )
    assert event.payload == {
        'name': 'Onboarding',
        'version': template.version,
        'is_active': False,
        'template_deleted': True,
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

    # assert
    event = fake_stream.last_event()
    assert len(fake_stream.events) == 1
    assert event.type == TemplateEvents.AI_GENERATE
    assert event.account_id == owner.account_id
    assert event.actor == Actor(
        id=owner.id,
        email=owner.email,
        user_type=UserType.USER,
    )
    assert event.auth_type == AuthTokenType.USER
    assert event.object == EventObject(type=EventObjectType.TEMPLATE)
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

    # assert
    event = fake_stream.last_event()
    assert len(fake_stream.events) == 1
    assert event.type == TemplateEvents.LIBRARY_FILL
    assert event.account_id == owner.account_id
    assert event.object == EventObject(
        type=EventObjectType.SYSTEM_TEMPLATE,
        id=system_template.id,
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

    # assert
    event = fake_stream.last_event()
    assert len(fake_stream.events) == 1
    assert event.type == TemplateEvents.LIBRARY_IMPORT
    assert event.account_id == owner.account_id
    assert event.object == EventObject(type=EventObjectType.SYSTEM_TEMPLATE)
    assert event.payload == {'templates_count': 3}


def test_template_preset_created__preset__preset_object(fake_stream):

    # arrange
    owner = create_test_owner()
    template = create_test_template(user=owner, is_active=True)
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

    # assert
    event = fake_stream.last_event()
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
        type=EventObjectType.TEMPLATE_PRESET,
        id=preset.id,
    )
    assert event.payload == {
        'name': 'Weekly',
        'template_id': template.id,
        'type': preset.type,
        'is_default': False,
    }


def test_template_preset_updated__preset__preset_object(fake_stream):

    # arrange
    owner = create_test_owner()
    template = create_test_template(user=owner, is_active=True)
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
    )

    # assert
    event = fake_stream.last_event()
    assert len(fake_stream.events) == 1
    assert event.type == TemplateEvents.PRESET_UPDATE
    assert event.object == EventObject(
        type=EventObjectType.TEMPLATE_PRESET,
        id=preset.id,
    )
    assert event.payload == {
        'name': 'Weekly',
        'template_id': template.id,
        'type': preset.type,
        'is_default': False,
    }


def test_template_preset_deleted__preset__preset_object(fake_stream):

    # arrange
    owner = create_test_owner()
    template = create_test_template(user=owner, is_active=True)
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

    # assert
    event = fake_stream.last_event()
    assert len(fake_stream.events) == 1
    assert event.type == TemplateEvents.PRESET_DELETE
    assert event.object == EventObject(
        type=EventObjectType.TEMPLATE_PRESET,
        id=preset.id,
    )
    assert event.payload == {
        'name': 'Weekly',
        'template_id': template.id,
        'type': preset.type,
        'is_default': False,
    }


def test_template_preset_set_default__default_preset__is_default_true(
    fake_stream,
):

    # arrange
    owner = create_test_owner()
    template = create_test_template(user=owner, is_active=True)
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

    # assert
    event = fake_stream.last_event()
    assert len(fake_stream.events) == 1
    assert event.type == TemplateEvents.PRESET_SET_DEFAULT
    assert event.object == EventObject(
        type=EventObjectType.TEMPLATE_PRESET,
        id=preset.id,
    )
    assert event.payload == {
        'name': 'Weekly',
        'template_id': template.id,
        'type': preset.type,
        'is_default': True,
    }


# Fieldsets and datasets


def test_fieldset_created__fieldset__fieldset_object(fake_stream):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    fieldset = create_test_shared_fieldset(account=account, name='Address')

    # act
    AuditEventService.fieldset_created(
        user=owner,
        auth_type=AuthTokenType.USER,
        fieldset=fieldset,
    )

    # assert
    event = fake_stream.last_event()
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
        type=EventObjectType.FIELDSET,
        id=fieldset.id,
    )
    assert event.payload == {'name': 'Address'}


def test_fieldset_updated__fieldset__fieldset_object(fake_stream):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    fieldset = create_test_shared_fieldset(account=account, name='Address')

    # act
    AuditEventService.fieldset_updated(
        user=owner,
        auth_type=AuthTokenType.USER,
        fieldset=fieldset,
    )

    # assert
    event = fake_stream.last_event()
    assert len(fake_stream.events) == 1
    assert event.type == TemplateEvents.FIELDSET_UPDATE
    assert event.object == EventObject(
        type=EventObjectType.FIELDSET,
        id=fieldset.id,
    )
    assert event.payload == {'name': 'Address'}


def test_fieldset_cloned__clone__source_fieldset_id_in_the_payload(
    fake_stream,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    fieldset = create_test_shared_fieldset(account=account, name='Address')
    clone = create_test_shared_fieldset(
        account=account,
        name='Copy of Address',
    )

    # act
    AuditEventService.fieldset_cloned(
        user=owner,
        auth_type=AuthTokenType.USER,
        clone=clone,
        source_fieldset_id=fieldset.id,
    )

    # assert
    event = fake_stream.last_event()
    assert len(fake_stream.events) == 1
    assert event.type == TemplateEvents.FIELDSET_CLONE
    assert event.object == EventObject(
        type=EventObjectType.FIELDSET,
        id=clone.id,
    )
    assert event.payload == {
        'name': 'Copy of Address',
        'source_fieldset_id': fieldset.id,
    }


def test_fieldset_deleted__fieldset__fieldset_object(fake_stream):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    fieldset = create_test_shared_fieldset(account=account, name='Address')

    # act
    AuditEventService.fieldset_deleted(
        user=owner,
        auth_type=AuthTokenType.USER,
        fieldset=fieldset,
    )

    # assert
    event = fake_stream.last_event()
    assert len(fake_stream.events) == 1
    assert event.type == TemplateEvents.FIELDSET_DELETE
    assert event.object == EventObject(
        type=EventObjectType.FIELDSET,
        id=fieldset.id,
    )
    assert event.payload == {'name': 'Address'}


def test_dataset_created__dataset__items_count_in_the_payload(fake_stream):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    dataset = create_test_dataset(account=account, name='Cities')

    # act
    AuditEventService.dataset_created(
        user=owner,
        auth_type=AuthTokenType.USER,
        dataset=dataset,
        items_count=2,
    )

    # assert
    event = fake_stream.last_event()
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
        type=EventObjectType.DATASET,
        id=dataset.id,
    )
    assert event.payload == {'name': 'Cities', 'items_count': 2}


def test_dataset_updated__changed_fields__names_only(fake_stream):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    dataset = create_test_dataset(account=account, name='Cities')

    # act
    AuditEventService.dataset_updated(
        user=owner,
        auth_type=AuthTokenType.USER,
        dataset=dataset,
        changed_fields=['description', 'name'],
    )

    # assert
    event = fake_stream.last_event()
    assert len(fake_stream.events) == 1
    assert event.type == DatasetEvents.UPDATE
    assert event.object == EventObject(
        type=EventObjectType.DATASET,
        id=dataset.id,
    )
    assert event.payload == {
        'name': 'Cities',
        'changed_fields': ['description', 'name'],
    }


def test_dataset_deleted__dataset__dataset_object(fake_stream):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    dataset = create_test_dataset(account=account, name='Cities')

    # act
    AuditEventService.dataset_deleted(
        user=owner,
        auth_type=AuthTokenType.USER,
        dataset=dataset,
    )

    # assert
    event = fake_stream.last_event()
    assert len(fake_stream.events) == 1
    assert event.type == DatasetEvents.DELETE
    assert event.object == EventObject(
        type=EventObjectType.DATASET,
        id=dataset.id,
    )
    assert event.payload == {'name': 'Cities'}


def test_dataset_items_added__dataset__items_count_in_the_payload(
    fake_stream,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    dataset = create_test_dataset(account=account, name='Cities')

    # act
    AuditEventService.dataset_items_added(
        user=owner,
        auth_type=AuthTokenType.USER,
        dataset=dataset,
        items_count=3,
    )

    # assert
    event = fake_stream.last_event()
    assert len(fake_stream.events) == 1
    assert event.type == DatasetEvents.ITEMS_ADD
    assert event.object == EventObject(
        type=EventObjectType.DATASET,
        id=dataset.id,
    )
    assert event.payload == {'name': 'Cities', 'items_count': 3}


def test_dataset_items_replaced__dataset__items_count_in_the_payload(
    fake_stream,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    dataset = create_test_dataset(account=account, name='Cities')

    # act
    AuditEventService.dataset_items_replaced(
        user=owner,
        auth_type=AuthTokenType.USER,
        dataset=dataset,
        items_count=4,
    )

    # assert
    event = fake_stream.last_event()
    assert len(fake_stream.events) == 1
    assert event.type == DatasetEvents.ITEMS_REPLACE
    assert event.object == EventObject(
        type=EventObjectType.DATASET,
        id=dataset.id,
    )
    assert event.payload == {'name': 'Cities', 'items_count': 4}


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

    # assert
    event = fake_stream.last_event()
    assert len(fake_stream.events) == 1
    assert event.type == DatasetEvents.ITEM_CREATE
    assert event.account_id == account.id
    assert event.object == EventObject(
        type=EventObjectType.DATASET_ITEM,
        id=item.id,
    )
    assert event.payload == {'dataset_id': dataset.id}


def test_dataset_item_updated__changed_fields__names_only(fake_stream):

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
        changed_fields=['value'],
    )

    # assert
    event = fake_stream.last_event()
    assert len(fake_stream.events) == 1
    assert event.type == DatasetEvents.ITEM_UPDATE
    assert event.object == EventObject(
        type=EventObjectType.DATASET_ITEM,
        id=item.id,
    )
    assert event.payload == {
        'dataset_id': dataset.id,
        'changed_fields': ['value'],
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

    # assert
    event = fake_stream.last_event()
    assert len(fake_stream.events) == 1
    assert event.type == DatasetEvents.ITEM_DELETE
    assert event.object == EventObject(
        type=EventObjectType.DATASET_ITEM,
        id=item.id,
    )
    assert event.payload == {'dataset_id': dataset.id}


# Workflows and tasks changed in place


def test_workflow_updated__kickoff_fields__kickoff_key(fake_stream):

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(user=owner, tasks_count=1)

    # act
    AuditEventService.workflow_updated(
        user=owner,
        auth_type=AuthTokenType.USER,
        workflow=workflow,
        changed_fields=['kickoff', 'name'],
        kickoff_fields=['field-1'],
    )

    # assert
    event = fake_stream.last_event()
    assert len(fake_stream.events) == 1
    assert event.type == WorkflowEvents.UPDATE
    assert event.account_id == owner.account_id
    assert event.actor == Actor(
        id=owner.id,
        email=owner.email,
        user_type=UserType.USER,
    )
    assert event.auth_type == AuthTokenType.USER
    assert event.object == EventObject(
        type=EventObjectType.WORKFLOW,
        id=workflow.id,
    )
    assert event.payload == {
        'workflow_name': workflow.name,
        'changed_fields': ['kickoff', 'name'],
        'kickoff_fields': ['field-1'],
    }
    assert event.workflow_id == workflow.id
    assert event.task_id is None


def test_workflow_updated__no_kickoff_fields__no_kickoff_key(fake_stream):

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(user=owner, tasks_count=1)

    # act
    AuditEventService.workflow_updated(
        user=owner,
        auth_type=AuthTokenType.USER,
        workflow=workflow,
        changed_fields=['name'],
        kickoff_fields=[],
    )

    # assert
    event = fake_stream.last_event()
    assert len(fake_stream.events) == 1
    assert event.type == WorkflowEvents.UPDATE
    assert event.payload == {
        'workflow_name': workflow.name,
        'changed_fields': ['name'],
    }


def test_workflow_terminated__workflow__name_and_template_in_payload(
    fake_stream,
):

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(user=owner, tasks_count=1)

    # act
    AuditEventService.workflow_terminated(
        user=owner,
        auth_type=AuthTokenType.API,
        workflow=workflow,
    )

    # assert
    event = fake_stream.last_event()
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
        type=EventObjectType.WORKFLOW,
        id=workflow.id,
    )
    assert event.payload == {
        'workflow_name': workflow.name,
        'template_id': workflow.template_id,
    }
    assert event.workflow_id == workflow.id
    assert event.task_id is None


def test_comment_updated__comment_with_task__task_name(fake_stream):

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(user=owner, tasks_count=1)
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

    # assert
    event = fake_stream.last_event()
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
        type=EventObjectType.COMMENT,
        id=comment.id,
    )
    assert event.payload == {
        'workflow_name': workflow.name,
        'task_name': task.name,
    }
    assert event.workflow_id == workflow.id
    assert event.task_id == task.id


def test_comment_updated__comment_without_task__no_task_name(fake_stream):

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(user=owner, tasks_count=1)
    comment = create_test_event(
        workflow=workflow,
        user=owner,
        type_event=WorkflowEventType.COMMENT,
    )
    comment.task = None

    # act
    AuditEventService.comment_updated(
        user=owner,
        auth_type=AuthTokenType.USER,
        comment=comment,
    )

    # assert
    event = fake_stream.last_event()
    assert len(fake_stream.events) == 1
    assert event.type == TaskEvents.COMMENT_UPDATE
    assert event.payload == {'workflow_name': workflow.name}
    assert event.workflow_id == workflow.id
    assert event.task_id is None


def test_comment_deleted__comment__comment_object(fake_stream):

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(user=owner, tasks_count=1)
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

    # assert
    event = fake_stream.last_event()
    assert len(fake_stream.events) == 1
    assert event.type == TaskEvents.COMMENT_DELETE
    assert event.object == EventObject(
        type=EventObjectType.COMMENT,
        id=comment.id,
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
    workflow = create_test_workflow(user=owner, template=template)
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
        checklist=checklist,
        selection_id=selection.id,
    )

    # assert
    event = fake_stream.last_event()
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
        type=EventObjectType.CHECKLIST,
        id=checklist.id,
    )
    assert event.payload == {
        'workflow_name': workflow.name,
        'task_name': task.name,
        'checklist_api_name': 'checklist',
        'selection_id': selection.id,
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
    workflow = create_test_workflow(user=owner, template=template)
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
        checklist=checklist,
        selection_id=selection.id,
    )

    # assert
    event = fake_stream.last_event()
    assert len(fake_stream.events) == 1
    assert event.type == TaskEvents.CHECKLIST_UNMARK
    assert event.object == EventObject(
        type=EventObjectType.CHECKLIST,
        id=checklist.id,
    )
    assert event.payload == {
        'workflow_name': workflow.name,
        'task_name': task.name,
        'checklist_api_name': 'checklist',
        'selection_id': selection.id,
    }
    assert event.workflow_id == workflow.id
    assert event.task_id == task.id


def test_comment_updated__logs_disabled__no_event(mocker):

    """ With the journal off nothing is read and nothing is built:
        the workflow and the task each cost a query. """

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(user=owner, tasks_count=1)
    comment = create_test_event(
        workflow=workflow,
        user=owner,
        type_event=WorkflowEventType.COMMENT,
    )
    emit_mock = mocker.patch('src.logs.events.services.emit')

    # act
    AuditEventService.comment_updated(
        user=owner,
        auth_type=AuthTokenType.USER,
        comment=comment,
    )

    # assert
    emit_mock.assert_not_called()


def test_checklist_item_marked__logs_disabled__no_event(mocker):

    # arrange
    owner = create_test_owner()
    template = create_test_template(
        user=owner,
        is_active=True,
        tasks_count=1,
    )
    create_checklist_template(task_template=template.tasks.get(number=1))
    workflow = create_test_workflow(user=owner, template=template)
    checklist = workflow.tasks.get(number=1).checklists.get()
    selection = ChecklistSelection.objects.get(
        checklist=checklist,
        api_name='cl-selection-1',
    )
    emit_mock = mocker.patch('src.logs.events.services.emit')

    # act
    AuditEventService.checklist_item_marked(
        user=owner,
        auth_type=AuthTokenType.USER,
        checklist=checklist,
        selection_id=selection.id,
    )

    # assert
    emit_mock.assert_not_called()
