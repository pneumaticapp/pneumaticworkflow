from hashlib import sha256

import pytest

from src.accounts.models import UserInvite
from src.authentication.enums import AuthTokenType
from src.logs.events.emitter import NO_ACCOUNT
from src.logs.events.enums import (
    ActorType,
    EventCategory,
    EventName,
    EventObjectType,
)
from src.logs.events.schema import Actor, EventObject
from src.logs.events.services import AuditEventService
from src.processes.tests.fixtures import (
    create_invited_user,
    create_test_account,
    create_test_owner,
    create_test_template,
)

pytestmark = pytest.mark.django_db


def test_user_logged_in__request__login_event(
    events_enabled,
    run_on_commit,
    fake_stream,
    request_factory,
):

    # arrange
    user = create_test_owner()
    request = request_factory.post(
        '/auth/signin',
        HTTP_X_REAL_IP='1.2.3.4',
        HTTP_USER_AGENT='Firefox',
    )
    request.user = user
    request.token_type = AuthTokenType.USER

    # act
    AuditEventService.user_logged_in(
        user=user,
        source='email',
        request=request,
    )

    # assert
    event = fake_stream.last_event()
    assert len(fake_stream.events) == 1
    assert event.type == EventName.USER_LOGIN
    assert event.category == EventCategory.AUDIT
    assert event.account_id == user.account_id
    assert event.actor == Actor(
        type=ActorType.USER,
        id=user.id,
        email=user.email,
    )
    assert event.object == EventObject(type=EventObjectType.USER, id=user.id)
    assert event.payload == {'source': 'email'}
    assert event.ip == '1.2.3.4'
    assert event.user_agent == 'Firefox'
    assert event.pii == ('actor.email', 'ip', 'user_agent')


def test_user_signed_up__no_request__signup_event(
    events_enabled,
    run_on_commit,
    fake_stream,
):

    # arrange
    user = create_test_owner()

    # act
    AuditEventService.user_signed_up(user=user, source='google')

    # assert
    event = fake_stream.last_event()
    assert len(fake_stream.events) == 1
    assert event.type == EventName.USER_SIGNUP
    assert event.category == EventCategory.AUDIT
    assert event.account_id == user.account_id
    assert event.actor == Actor(
        type=ActorType.USER,
        id=user.id,
        email=user.email,
    )
    assert event.object == EventObject(type=EventObjectType.USER, id=user.id)
    assert event.payload == {'source': 'google'}
    assert event.ip is None
    assert event.pii == ('actor.email',)


def test_login_failed__request__hashed_email_and_no_account(
    events_enabled,
    run_on_commit,
    fake_stream,
    request_factory,
):

    """ The address is stored as a hash only and the event belongs
        to no account: a failed sign in is the bucket an alert on a
        brute force burst is built on. """

    # arrange
    request = request_factory.post('/auth/signin', HTTP_X_REAL_IP='1.2.3.4')
    request.data = {'username': ' Ann@Test.test '}

    # act
    AuditEventService.login_failed(request=request, reason='invalid')

    # assert
    event = fake_stream.last_event()
    assert len(fake_stream.events) == 1
    assert event.type == EventName.USER_LOGIN_FAILED
    assert event.category == EventCategory.AUDIT
    assert event.account_id == NO_ACCOUNT
    assert event.actor == Actor(type=ActorType.GUEST)
    assert event.object == EventObject(type=EventObjectType.USER)
    assert event.payload == {
        'email_hash': sha256(b'ann@test.test').hexdigest(),
        'reason': 'invalid',
    }
    assert event.ip == '1.2.3.4'
    assert event.pii == ('ip',)


def test_login_failed__no_username__hash_of_the_empty_string(
    events_enabled,
    run_on_commit,
    fake_stream,
    request_factory,
):

    # arrange
    request = request_factory.post('/auth/signin')
    request.data = {}

    # act
    AuditEventService.login_failed(request=request, reason='invalid')

    # assert
    event = fake_stream.last_event()
    assert event.payload == {
        'email_hash': sha256(b'').hexdigest(),
        'reason': 'invalid',
    }


def test_user_logged_out__request__logout_event_with_the_auth_type(
    events_enabled,
    run_on_commit,
    fake_stream,
    request_factory,
):

    # arrange
    user = create_test_owner()
    request = request_factory.post('/auth/signout')
    request.user = user
    request.token_type = AuthTokenType.API

    # act
    AuditEventService.user_logged_out(request=request)

    # assert
    event = fake_stream.last_event()
    assert len(fake_stream.events) == 1
    assert event.type == EventName.USER_LOGOUT
    assert event.account_id == user.account_id
    assert event.actor == Actor(
        type=ActorType.API_KEY,
        id=user.id,
        email=user.email,
    )
    assert event.object == EventObject(type=EventObjectType.USER, id=user.id)
    assert event.payload == {'auth_type': AuthTokenType.API}


def test_superuser_logged_in_as__request__target_and_reason(
    events_enabled,
    run_on_commit,
    fake_stream,
    request_factory,
):

    # arrange
    staff = create_test_owner(email='staff@test.test')
    target = create_test_owner(email='target@test.test')
    request = request_factory.post('/auth/superuser/token')
    request.user = staff
    request.token_type = AuthTokenType.USER

    # act
    AuditEventService.superuser_logged_in_as(
        request=request,
        user=target,
        reason='Ticket 42',
    )

    # assert
    event = fake_stream.last_event()
    assert len(fake_stream.events) == 1
    assert event.type == EventName.USER_LOGIN_AS
    assert event.account_id == target.account_id
    assert event.actor == Actor(
        type=ActorType.USER,
        id=staff.id,
        email=staff.email,
    )
    assert event.object == EventObject(
        type=EventObjectType.USER,
        id=target.id,
    )
    assert event.payload == {
        'target_email': target.email,
        'reason': 'Ticket 42',
    }
    assert event.pii == (
        'actor.email',
        'ip',
        'payload.target_email',
        'payload.reason',
    )


def test_tenant_logged_in_as__request__tenant_account_object(
    events_enabled,
    run_on_commit,
    fake_stream,
    request_factory,
):

    # arrange
    master = create_test_owner()
    tenant_account = create_test_account(
        name='Tenant',
        master_account=master.account,
    )
    request = request_factory.post('/tenants/token')
    request.user = master
    request.token_type = AuthTokenType.USER

    # act
    AuditEventService.tenant_logged_in_as(
        request=request,
        tenant_account=tenant_account,
    )

    # assert
    event = fake_stream.last_event()
    assert len(fake_stream.events) == 1
    assert event.type == EventName.TENANT_LOGIN_AS
    assert event.account_id == tenant_account.id
    assert event.actor == Actor(
        type=ActorType.USER,
        id=master.id,
        email=master.email,
    )
    assert event.object == EventObject(
        type=EventObjectType.ACCOUNT,
        id=tenant_account.id,
    )
    assert event.payload == {'master_account_id': master.account_id}


def test_user_admin_toggled__request__flag_and_target_email(
    events_enabled,
    run_on_commit,
    fake_stream,
    request_factory,
):

    # arrange
    owner = create_test_owner()
    target = create_test_owner(email='target@test.test')
    request = request_factory.post('/accounts/users/toggle-admin')
    request.user = owner
    request.token_type = AuthTokenType.USER

    # act
    AuditEventService.user_admin_toggled(request=request, user=target)

    # assert
    event = fake_stream.last_event()
    assert len(fake_stream.events) == 1
    assert event.type == EventName.USER_ADMIN_TOGGLE
    assert event.account_id == owner.account_id
    assert event.actor == Actor(
        type=ActorType.USER,
        id=owner.id,
        email=owner.email,
    )
    assert event.object == EventObject(
        type=EventObjectType.USER,
        id=target.id,
    )
    assert event.payload == {
        'is_admin': True,
        'target_email': target.email,
    }


def test_invite_accepted__anonymous_request__invited_user_is_the_actor(
    events_enabled,
    run_on_commit,
    fake_stream,
    request_factory,
    mocker,
):

    """ The endpoint is open and the request is not authenticated:
        the actor is the invited person, not request.user. """

    # arrange
    owner = create_test_owner()
    invited = create_invited_user(user=owner, email='invited@test.test')
    invite = UserInvite.objects.get(invited_user=invited)
    request = request_factory.post('/accounts/invites/token')
    request.user = mocker.Mock(is_authenticated=False)

    # act
    AuditEventService.invite_accepted(
        request=request,
        user=invited,
        invite=invite,
    )

    # assert
    event = fake_stream.last_event()
    assert len(fake_stream.events) == 1
    assert event.type == EventName.INVITE_ACCEPT
    assert event.account_id == owner.account_id
    assert event.actor == Actor(
        type=ActorType.USER,
        id=invited.id,
        email=invited.email,
    )
    assert event.object == EventObject(
        type=EventObjectType.INVITE,
        id=str(invite.id),
    )
    assert event.payload == {'invited_by_id': owner.id}


def test_template_saved__active_template__publish_event(
    events_enabled,
    run_on_commit,
    fake_stream,
    request_factory,
):

    # arrange
    owner = create_test_owner()
    template = create_test_template(user=owner, is_active=True)
    request = request_factory.put('/templates/1')
    request.user = owner
    request.token_type = AuthTokenType.USER

    # act
    AuditEventService.template_saved(
        request=request,
        template=template,
        name='Onboarding',
    )

    # assert
    event = fake_stream.last_event()
    assert len(fake_stream.events) == 1
    assert event.type == EventName.TEMPLATE_PUBLISH
    assert event.category == EventCategory.AUDIT
    assert event.account_id == owner.account_id
    assert event.actor == Actor(
        type=ActorType.USER,
        id=owner.id,
        email=owner.email,
    )
    assert event.object == EventObject(
        type=EventObjectType.TEMPLATE,
        id=template.id,
    )
    assert event.payload == {
        'name': 'Onboarding',
        'version': template.version,
        'is_active': True,
    }
    assert event.pii == ('actor.email', 'ip', 'payload.name')


def test_template_saved__draft__draft_save_event(
    events_enabled,
    run_on_commit,
    fake_stream,
    request_factory,
):

    """ A published template is an audit record, a draft is not. """

    # arrange
    owner = create_test_owner()
    template = create_test_template(user=owner, is_active=False)
    request = request_factory.put('/templates/1')
    request.user = owner
    request.token_type = AuthTokenType.USER

    # act
    AuditEventService.template_saved(
        request=request,
        template=template,
        name='Draft name',
    )

    # assert
    event = fake_stream.last_event()
    assert len(fake_stream.events) == 1
    assert event.type == EventName.TEMPLATE_DRAFT_SAVE
    assert event.category == EventCategory.ACTIVITY
    assert event.payload == {
        'name': 'Draft name',
        'version': template.version,
        'is_active': False,
    }


def test_template_cloned__request__clone_event(
    events_enabled,
    run_on_commit,
    fake_stream,
    request_factory,
):

    # arrange
    owner = create_test_owner()
    template = create_test_template(user=owner, is_active=False)
    request = request_factory.post('/templates/1/clone')
    request.user = owner
    request.token_type = AuthTokenType.USER

    # act
    AuditEventService.template_cloned(
        request=request,
        template=template,
        name='Copy of Onboarding',
    )

    # assert
    event = fake_stream.last_event()
    assert len(fake_stream.events) == 1
    assert event.type == EventName.TEMPLATE_CLONE
    assert event.category == EventCategory.ACTIVITY
    assert event.object == EventObject(
        type=EventObjectType.TEMPLATE,
        id=template.id,
    )
    assert event.payload == {
        'name': 'Copy of Onboarding',
        'version': template.version,
        'is_active': False,
    }


def test_template_deleted__request__delete_event_with_the_name(
    events_enabled,
    run_on_commit,
    fake_stream,
    request_factory,
):

    # arrange
    owner = create_test_owner()
    template = create_test_template(
        user=owner,
        is_active=True,
        name='Offboarding',
    )
    request = request_factory.delete('/templates/1')
    request.user = owner
    request.token_type = AuthTokenType.USER

    # act
    AuditEventService.template_deleted(request=request, template=template)

    # assert
    event = fake_stream.last_event()
    assert len(fake_stream.events) == 1
    assert event.type == EventName.TEMPLATE_DELETE
    assert event.category == EventCategory.AUDIT
    assert event.object == EventObject(
        type=EventObjectType.TEMPLATE,
        id=template.id,
    )
    assert event.payload == {
        'name': 'Offboarding',
        'version': template.version,
        'is_active': True,
    }


def test_templates_exported__request__filters_and_no_object_id(
    events_enabled,
    run_on_commit,
    fake_stream,
    request_factory,
):

    """ The export is a bulk read: the filters say what left. """

    # arrange
    owner = create_test_owner()
    request = request_factory.get('/templates/export')
    request.user = owner
    request.token_type = AuthTokenType.API

    # act
    AuditEventService.templates_exported(
        request=request,
        filters={'is_active': True, 'ordering': 'name'},
    )

    # assert
    event = fake_stream.last_event()
    assert len(fake_stream.events) == 1
    assert event.type == EventName.TEMPLATE_EXPORT
    assert event.category == EventCategory.AUDIT
    assert event.account_id == owner.account_id
    assert event.actor == Actor(
        type=ActorType.API_KEY,
        id=owner.id,
        email=owner.email,
    )
    assert event.object == EventObject(type=EventObjectType.TEMPLATE)
    assert event.payload == {
        'filters': {'is_active': True, 'ordering': 'name'},
    }


def test_email_hash__mixed_case_with_spaces__hash_of_the_normalized():

    # act
    result = AuditEventService._email_hash(' Ann@Test.test ')

    # assert
    assert result == sha256(b'ann@test.test').hexdigest()


def test_email_hash__none__hash_of_the_empty_string():

    # act
    result = AuditEventService._email_hash(None)

    # assert
    assert result == sha256(b'').hexdigest()
