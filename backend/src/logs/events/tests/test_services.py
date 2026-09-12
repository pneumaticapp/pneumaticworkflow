from hashlib import sha256

import pytest
from django.contrib.auth.models import AnonymousUser

from src.authentication.enums import AuthTokenType
from src.logs.events.emitter import NO_ACCOUNT
from src.logs.events.enums import (
    ActorType,
    EventCategory,
    EventName,
    EventObjectType,
    TemplateSource,
)
from src.logs.events.schema import Actor, EventObject
from src.logs.events.services import AuditEventService
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_group,
    create_test_not_admin,
    create_test_owner,
    create_test_template,
)

pytestmark = pytest.mark.django_db


def test_user_logged_in__request__login_event(
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


def test_login_failed__explicit_email__hash_of_the_given_address(
    fake_stream,
    request_factory,
):

    """ An SSO callback carries the address in the provider profile
        and not in the request body, so the caller passes it. The
        body must not win over it, and the address must still reach
        the record as a hash only. """

    # arrange
    request = request_factory.get('/auth/okta/token')
    request.data = {'username': 'body@test.test'}

    # act
    AuditEventService.login_failed(
        request=request,
        reason='inactive',
        email=' Ann@Test.test ',
    )

    # assert
    event = fake_stream.last_event()
    assert len(fake_stream.events) == 1
    assert event.type == EventName.USER_LOGIN_FAILED
    assert event.account_id == NO_ACCOUNT
    assert event.payload == {
        'email_hash': sha256(b'ann@test.test').hexdigest(),
        'reason': 'inactive',
    }


def test_login_failed__no_username__hash_of_the_empty_string(
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
        master_user=master,
        tenant_account=tenant_account,
        auth_type=AuthTokenType.USER,
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


def test_template_saved__active_template__publish_event(
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

    # arrange
    email = ' Ann@Test.test '

    # act
    result = AuditEventService._email_hash(email)

    # assert
    assert result == sha256(b'ann@test.test').hexdigest()


def test_email_hash__none__hash_of_the_empty_string():

    # arrange
    email = None

    # act
    result = AuditEventService._email_hash(email)

    # assert
    assert result == sha256(b'').hexdigest()


def test_password_reset_requested__known_address__guest_actor(
    fake_stream,
    request_factory,
):

    # arrange
    user = create_test_owner()
    request = request_factory.post(
        '/auth/reset-password',
        HTTP_X_REAL_IP='1.2.3.4',
        HTTP_USER_AGENT='Firefox',
    )

    # act
    AuditEventService.password_reset_requested(request=request, user=user)

    # assert
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    assert event.type == EventName.USER_PASSWORD_RESET_REQUEST
    assert event.category == EventCategory.AUDIT
    assert event.account_id == user.account_id
    assert event.actor == Actor(type=ActorType.GUEST)
    assert event.object == EventObject(type=EventObjectType.USER, id=user.id)
    assert event.payload == {'target_email': user.email}
    assert event.ip == '1.2.3.4'
    assert event.pii == ('ip', 'user_agent', 'payload.target_email')


def test_password_reset__anonymous_request__user_of_the_link_acts(
    fake_stream,
    request_factory,
):

    # arrange
    user = create_test_owner()
    request = request_factory.post('/auth/reset-password/confirm')

    # act
    AuditEventService.password_reset(request=request, user=user)

    # assert
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    assert event.type == EventName.USER_PASSWORD_RESET
    assert event.account_id == user.account_id
    assert event.actor == Actor(
        type=ActorType.USER,
        id=user.id,
        email=user.email,
    )
    assert event.object == EventObject(type=EventObjectType.USER, id=user.id)
    assert event.payload == {}


def test_password_changed__api_key_request__api_key_actor(
    fake_stream,
    request_factory,
):

    # arrange
    user = create_test_owner()
    request = request_factory.post('/auth/change-password')
    request.user = user
    request.token_type = AuthTokenType.API

    # act
    AuditEventService.password_changed(request=request)

    # assert
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    assert event.type == EventName.USER_PASSWORD_CHANGE
    assert event.account_id == user.account_id
    assert event.actor == Actor(
        type=ActorType.API_KEY,
        id=user.id,
        email=user.email,
    )
    assert event.object == EventObject(type=EventObjectType.USER, id=user.id)
    assert event.payload == {}


def test_user_created__admin_request__target_in_the_payload(
    fake_stream,
    request_factory,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    user = create_test_not_admin(account=account, email='new@test.test')
    request = request_factory.post('/accounts/users')
    request.user = owner
    request.token_type = AuthTokenType.USER

    # act
    AuditEventService.user_created(request=request, user=user)

    # assert
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    assert event.type == EventName.USER_CREATE
    assert event.account_id == account.id
    assert event.actor == Actor(
        type=ActorType.USER,
        id=owner.id,
        email=owner.email,
    )
    assert event.object == EventObject(type=EventObjectType.USER, id=user.id)
    assert event.payload == {
        'target_email': 'new@test.test',
        'is_admin': False,
    }


def test_account_updated__changed_fields__names_only(
    fake_stream,
    request_factory,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    request = request_factory.put('/accounts/account')
    request.user = owner
    request.token_type = AuthTokenType.USER

    # act
    AuditEventService.account_updated(
        request=request,
        account=account,
        changed_fields=['logo_lg', 'name'],
    )

    # assert
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    assert event.type == EventName.ACCOUNT_UPDATE
    assert event.account_id == account.id
    assert event.actor == Actor(
        type=ActorType.USER,
        id=owner.id,
        email=owner.email,
    )
    assert event.object == EventObject(
        type=EventObjectType.ACCOUNT,
        id=account.id,
    )
    assert event.payload == {'changed_fields': ['logo_lg', 'name']}


def test_user_reassigned__old_group__group_object(
    fake_stream,
    request_factory,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    new_user = create_test_not_admin(account=account)
    group = create_test_group(account=account)
    request = request_factory.post(path='/accounts/users/reassign')
    request.user = owner
    request.token_type = AuthTokenType.USER

    # act
    AuditEventService.user_reassigned(
        request=request,
        old_group=group,
        new_user=new_user,
    )

    # assert
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    assert event.type == EventName.USER_REASSIGN
    assert event.category == EventCategory.AUDIT
    assert event.account_id == account.id
    assert event.actor == Actor(
        type=ActorType.USER,
        id=owner.id,
        email=owner.email,
    )
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


def test_payment_confirmed__no_subscription_data__empty_payload(
    fake_stream,
    request_factory,
):

    # arrange
    user = create_test_owner()
    request = request_factory.get(path='/payment/confirm')
    request.user = AnonymousUser()

    # act
    AuditEventService.payment_confirmed(
        request=request,
        user=user,
        auth_type=None,
        subscription_data=None,
    )

    # assert
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    assert event.type == EventName.BILLING_PAYMENT_CONFIRM
    assert event.category == EventCategory.AUDIT
    assert event.account_id == user.account_id
    assert event.actor == Actor(
        type=ActorType.USER,
        id=user.id,
        email=user.email,
    )
    assert event.object == EventObject(
        type=EventObjectType.ACCOUNT,
        id=user.account_id,
    )
    assert event.payload == {}


def test_template_saved__source__source_in_the_payload(
    fake_stream,
    request_factory,
):

    # arrange
    owner = create_test_owner()
    template = create_test_template(user=owner, is_active=True)
    request = request_factory.post(path='/templates/from-library')
    request.user = owner
    request.token_type = AuthTokenType.USER

    # act
    AuditEventService.template_saved(
        request=request,
        template=template,
        name='Onboarding',
        source=TemplateSource.LIBRARY,
    )

    # assert
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
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
        'source': TemplateSource.LIBRARY,
    }


def test_template_saved__empty_source__no_source_key(
    fake_stream,
    request_factory,
):

    # arrange
    owner = create_test_owner()
    template = create_test_template(user=owner, is_active=False)
    request = request_factory.put(path='/templates/1')
    request.user = owner
    request.token_type = AuthTokenType.USER

    # act
    AuditEventService.template_saved(
        request=request,
        template=template,
        name='Draft name',
        source='',
    )

    # assert
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    assert event.type == EventName.TEMPLATE_DRAFT_SAVE
    assert event.category == EventCategory.ACTIVITY
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
        'name': 'Draft name',
        'version': template.version,
        'is_active': False,
    }
