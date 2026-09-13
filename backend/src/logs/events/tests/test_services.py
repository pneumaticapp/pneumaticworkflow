from hashlib import sha256

import pytest
from django.contrib.auth.models import AnonymousUser

from src.accounts.enums import BillingPlanType
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
from src.processes.enums import WorkflowEventType
from src.processes.models.workflows.checklist import ChecklistSelection
from src.processes.tests.fixtures import (
    create_checklist_template,
    create_test_account,
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


def test_superuser_logged_in_as__request__target_in_payload(
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
    assert event.payload == {'target_email': target.email}
    assert event.pii == (
        'actor.email',
        'ip',
        'payload.target_email',
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


def test_user_reassigned__old_user__user_object(
    mocker,
    events_enabled,
    request_factory,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    old_user = create_test_not_admin(account=account)
    new_group = create_test_group(account=account)
    request = request_factory.post(path='/accounts/users/reassign')
    request.user = owner
    request.token_type = AuthTokenType.USER
    emit_mock = mocker.patch('src.logs.events.services.emit')

    # act
    AuditEventService.user_reassigned(
        request=request,
        old_user=old_user,
        new_group=new_group,
    )

    # assert
    emit_mock.assert_called_once_with(
        EventName.USER_REASSIGN,
        account_id=account.id,
        actor=Actor(type=ActorType.USER, id=owner.id, email=owner.email),
        event_object=EventObject(type=EventObjectType.USER, id=old_user.id),
        payload={
            'old_user_id': old_user.id,
            'old_group_id': None,
            'new_user_id': None,
            'new_group_id': new_group.id,
        },
        workflow_id=None,
        task_id=None,
        request=request,
    )


def test_user_unsubscribed__anonymous_request__user_of_the_link_acts(
    mocker,
    events_enabled,
    request_factory,
):

    # arrange
    user = create_test_owner()
    request = request_factory.get(path='/accounts/emails/unsubscribe')
    request.user = AnonymousUser()
    emit_mock = mocker.patch('src.logs.events.services.emit')

    # act
    AuditEventService.user_unsubscribed(
        request=request,
        user=user,
        email_type='digest',
    )

    # assert
    emit_mock.assert_called_once_with(
        EventName.USER_UNSUBSCRIBE,
        account_id=user.account_id,
        actor=Actor(type=ActorType.USER, id=user.id, email=user.email),
        event_object=EventObject(type=EventObjectType.USER, id=user.id),
        payload={'email_type': 'digest'},
        request=request,
    )


def test_account_verified__anonymous_request__user_of_the_link_acts(
    mocker,
    events_enabled,
    request_factory,
):

    # arrange
    user = create_test_owner()
    request = request_factory.get(path='/auth/verification')
    request.user = AnonymousUser()
    emit_mock = mocker.patch('src.logs.events.services.emit')

    # act
    AuditEventService.account_verified(request=request, user=user)

    # assert
    emit_mock.assert_called_once_with(
        EventName.ACCOUNT_VERIFY,
        account_id=user.account_id,
        actor=Actor(type=ActorType.USER, id=user.id, email=user.email),
        event_object=EventObject(
            type=EventObjectType.ACCOUNT,
            id=user.account_id,
        ),
        request=request,
    )


def test_verification_resent__request__account_object_with_target(
    mocker,
    events_enabled,
    request_factory,
):

    # arrange
    owner = create_test_owner()
    request = request_factory.post(path='/auth/resend-verification')
    request.user = owner
    request.token_type = AuthTokenType.USER
    emit_mock = mocker.patch('src.logs.events.services.emit')

    # act
    AuditEventService.verification_resent(
        request=request,
        account_owner=owner,
    )

    # assert
    emit_mock.assert_called_once_with(
        EventName.ACCOUNT_VERIFICATION_RESEND,
        account_id=owner.account_id,
        actor=Actor(type=ActorType.USER, id=owner.id, email=owner.email),
        event_object=EventObject(
            type=EventObjectType.ACCOUNT,
            id=owner.account_id,
        ),
        payload={'target_email': owner.email},
        workflow_id=None,
        task_id=None,
        request=request,
    )


def test_tenant_created__request__tenant_in_master_account(
    mocker,
    events_enabled,
    request_factory,
):

    # arrange
    master = create_test_owner()
    tenant = create_test_account(
        master_account=master.account,
        tenant_name='Tenant',
        plan=BillingPlanType.PREMIUM,
    )
    request = request_factory.post(path='/tenants')
    request.user = master
    request.token_type = AuthTokenType.USER
    emit_mock = mocker.patch('src.logs.events.services.emit')

    # act
    AuditEventService.tenant_created(request=request, tenant=tenant)

    # assert
    emit_mock.assert_called_once_with(
        EventName.TENANT_CREATE,
        account_id=master.account_id,
        actor=Actor(type=ActorType.USER, id=master.id, email=master.email),
        event_object=EventObject(type=EventObjectType.ACCOUNT, id=tenant.id),
        payload={
            'name': 'Tenant',
            'billing_plan': BillingPlanType.PREMIUM,
        },
        workflow_id=None,
        task_id=None,
        request=request,
    )


def test_tenant_deleted__request__tenant_in_master_account(
    mocker,
    events_enabled,
    request_factory,
):

    # arrange
    master = create_test_owner()
    tenant = create_test_account(
        master_account=master.account,
        tenant_name='Tenant',
        plan=BillingPlanType.PREMIUM,
    )
    request = request_factory.delete(path='/tenants/1')
    request.user = master
    request.token_type = AuthTokenType.USER
    emit_mock = mocker.patch('src.logs.events.services.emit')

    # act
    AuditEventService.tenant_deleted(request=request, tenant=tenant)

    # assert
    emit_mock.assert_called_once_with(
        EventName.TENANT_DELETE,
        account_id=master.account_id,
        actor=Actor(type=ActorType.USER, id=master.id, email=master.email),
        event_object=EventObject(type=EventObjectType.ACCOUNT, id=tenant.id),
        payload={
            'name': 'Tenant',
            'billing_plan': BillingPlanType.PREMIUM,
        },
        workflow_id=None,
        task_id=None,
        request=request,
    )


def test_purchase_made__products__quantity_by_code(
    mocker,
    events_enabled,
    request_factory,
):

    # arrange
    owner = create_test_owner()
    request = request_factory.post(path='/payment/purchase')
    request.user = owner
    request.token_type = AuthTokenType.USER
    emit_mock = mocker.patch('src.logs.events.services.emit')

    # act
    AuditEventService.purchase_made(
        request=request,
        products=[
            {'code': 'unlimited_month', 'quantity': 1},
            {'code': 'extra_users', 'quantity': 2},
        ],
    )

    # assert
    emit_mock.assert_called_once_with(
        EventName.BILLING_PURCHASE,
        account_id=owner.account_id,
        actor=Actor(type=ActorType.USER, id=owner.id, email=owner.email),
        event_object=EventObject(
            type=EventObjectType.ACCOUNT,
            id=owner.account_id,
        ),
        payload={
            'products': {'unlimited_month': 1, 'extra_users': 2},
        },
        workflow_id=None,
        task_id=None,
        request=request,
    )


def test_purchase_made__repeated_code__quantity_summed(
    mocker,
    events_enabled,
    request_factory,
):

    # arrange
    owner = create_test_owner()
    request = request_factory.post(path='/payment/purchase')
    request.user = owner
    request.token_type = AuthTokenType.USER
    emit_mock = mocker.patch('src.logs.events.services.emit')

    # act
    AuditEventService.purchase_made(
        request=request,
        products=[
            {'code': 'extra_users', 'quantity': 2},
            {'code': 'extra_users', 'quantity': 3},
        ],
    )

    # assert
    emit_mock.assert_called_once_with(
        EventName.BILLING_PURCHASE,
        account_id=owner.account_id,
        actor=Actor(type=ActorType.USER, id=owner.id, email=owner.email),
        event_object=EventObject(
            type=EventObjectType.ACCOUNT,
            id=owner.account_id,
        ),
        payload={
            'products': {'extra_users': 5},
        },
        workflow_id=None,
        task_id=None,
        request=request,
    )


def test_subscription_cancelled__request__account_object(
    mocker,
    events_enabled,
    request_factory,
):

    # arrange
    owner = create_test_owner()
    request = request_factory.post(path='/payment/subscription/cancel')
    request.user = owner
    request.token_type = AuthTokenType.USER
    emit_mock = mocker.patch('src.logs.events.services.emit')

    # act
    AuditEventService.subscription_cancelled(request=request)

    # assert
    emit_mock.assert_called_once_with(
        EventName.BILLING_SUBSCRIPTION_CANCEL,
        account_id=owner.account_id,
        actor=Actor(type=ActorType.USER, id=owner.id, email=owner.email),
        event_object=EventObject(
            type=EventObjectType.ACCOUNT,
            id=owner.account_id,
        ),
        payload=None,
        workflow_id=None,
        task_id=None,
        request=request,
    )


def test_payment_confirmed__subscription_data__plan_in_payload(
    mocker,
    events_enabled,
    request_factory,
):

    # arrange
    user = create_test_owner()
    request = request_factory.get(path='/payment/confirm')
    request.user = AnonymousUser()
    emit_mock = mocker.patch('src.logs.events.services.emit')

    # act
    AuditEventService.payment_confirmed(
        request=request,
        user=user,
        auth_type=AuthTokenType.API,
        subscription_data={
            'billing_plan': BillingPlanType.PREMIUM,
            'max_users': 10,
            'trial_ended': True,
        },
    )

    # assert
    emit_mock.assert_called_once_with(
        EventName.BILLING_PAYMENT_CONFIRM,
        account_id=user.account_id,
        actor=Actor(type=ActorType.API_KEY, id=user.id, email=user.email),
        event_object=EventObject(
            type=EventObjectType.ACCOUNT,
            id=user.account_id,
        ),
        payload={
            'billing_plan': BillingPlanType.PREMIUM,
            'max_users': 10,
        },
        request=request,
    )


def test_template_draft_discarded__never_published__template_deleted(
    mocker,
    events_enabled,
    request_factory,
):

    # arrange
    owner = create_test_owner()
    template = create_test_template(
        user=owner,
        is_active=False,
        name='Onboarding',
    )
    request = request_factory.post(path='/templates/1/discard-changes')
    request.user = owner
    request.token_type = AuthTokenType.USER
    emit_mock = mocker.patch('src.logs.events.services.emit')

    # act
    AuditEventService.template_draft_discarded(
        request=request,
        template=template,
        template_deleted=True,
    )

    # assert
    emit_mock.assert_called_once_with(
        EventName.TEMPLATE_DRAFT_DISCARD,
        account_id=owner.account_id,
        actor=Actor(type=ActorType.USER, id=owner.id, email=owner.email),
        event_object=EventObject(
            type=EventObjectType.TEMPLATE,
            id=template.id,
        ),
        payload={
            'name': 'Onboarding',
            'version': template.version,
            'is_active': False,
            'template_deleted': True,
        },
        workflow_id=None,
        task_id=None,
        request=request,
    )


def test_template_generated_with_ai__request__no_object_id_no_payload(
    mocker,
    events_enabled,
    request_factory,
):

    # arrange
    owner = create_test_owner()
    request = request_factory.post(path='/templates/ai')
    request.user = owner
    request.token_type = AuthTokenType.USER
    emit_mock = mocker.patch('src.logs.events.services.emit')

    # act
    AuditEventService.template_generated_with_ai(request=request)

    # assert
    emit_mock.assert_called_once_with(
        EventName.TEMPLATE_AI_GENERATE,
        account_id=owner.account_id,
        actor=Actor(type=ActorType.USER, id=owner.id, email=owner.email),
        event_object=EventObject(type=EventObjectType.TEMPLATE, id=None),
        payload=None,
        workflow_id=None,
        task_id=None,
        request=request,
    )


def test_template_filled_from_library__request__system_template_object(
    mocker,
    events_enabled,
    request_factory,
):

    # arrange
    owner = create_test_owner()
    system_template = create_test_system_template(name='Hiring')
    request = request_factory.get(path='/templates/system/1/fill')
    request.user = owner
    request.token_type = AuthTokenType.USER
    emit_mock = mocker.patch('src.logs.events.services.emit')

    # act
    AuditEventService.template_filled_from_library(
        request=request,
        system_template=system_template,
    )

    # assert
    emit_mock.assert_called_once_with(
        EventName.TEMPLATE_LIBRARY_FILL,
        account_id=owner.account_id,
        actor=Actor(type=ActorType.USER, id=owner.id, email=owner.email),
        event_object=EventObject(
            type=EventObjectType.SYSTEM_TEMPLATE,
            id=system_template.id,
        ),
        payload={'name': 'Hiring'},
        workflow_id=None,
        task_id=None,
        request=request,
    )


def test_library_templates_imported__request__templates_count(
    mocker,
    events_enabled,
    request_factory,
):

    # arrange
    owner = create_test_owner()
    request = request_factory.post(path='/templates/system/import')
    request.user = owner
    request.token_type = AuthTokenType.USER
    emit_mock = mocker.patch('src.logs.events.services.emit')

    # act
    AuditEventService.library_templates_imported(
        request=request,
        templates_count=3,
    )

    # assert
    emit_mock.assert_called_once_with(
        EventName.TEMPLATE_LIBRARY_IMPORT,
        account_id=owner.account_id,
        actor=Actor(type=ActorType.USER, id=owner.id, email=owner.email),
        event_object=EventObject(
            type=EventObjectType.SYSTEM_TEMPLATE,
            id=None,
        ),
        payload={'templates_count': 3},
        workflow_id=None,
        task_id=None,
        request=request,
    )


def test_template_preset_created__request__preset_object(
    mocker,
    events_enabled,
    request_factory,
):

    # arrange
    owner = create_test_owner()
    template = create_test_template(user=owner, is_active=True)
    preset = create_test_template_preset(
        template=template,
        author=owner,
        name='Weekly',
    )
    request = request_factory.post(path='/templates/1/presets')
    request.user = owner
    request.token_type = AuthTokenType.USER
    emit_mock = mocker.patch('src.logs.events.services.emit')

    # act
    AuditEventService.template_preset_created(
        request=request,
        preset=preset,
    )

    # assert
    emit_mock.assert_called_once_with(
        EventName.TEMPLATE_PRESET_CREATE,
        account_id=owner.account_id,
        actor=Actor(type=ActorType.USER, id=owner.id, email=owner.email),
        event_object=EventObject(
            type=EventObjectType.TEMPLATE_PRESET,
            id=preset.id,
        ),
        payload={
            'name': 'Weekly',
            'template_id': template.id,
            'type': 'personal',
            'is_default': False,
        },
        workflow_id=None,
        task_id=None,
        request=request,
    )


def test_template_preset_updated__request__preset_object(
    mocker,
    events_enabled,
    request_factory,
):

    # arrange
    owner = create_test_owner()
    template = create_test_template(user=owner, is_active=True)
    preset = create_test_template_preset(
        template=template,
        author=owner,
        name='Weekly',
    )
    request = request_factory.put(path='/templates/presets/1')
    request.user = owner
    request.token_type = AuthTokenType.USER
    emit_mock = mocker.patch('src.logs.events.services.emit')

    # act
    AuditEventService.template_preset_updated(
        request=request,
        preset=preset,
    )

    # assert
    emit_mock.assert_called_once_with(
        EventName.TEMPLATE_PRESET_UPDATE,
        account_id=owner.account_id,
        actor=Actor(type=ActorType.USER, id=owner.id, email=owner.email),
        event_object=EventObject(
            type=EventObjectType.TEMPLATE_PRESET,
            id=preset.id,
        ),
        payload={
            'name': 'Weekly',
            'template_id': template.id,
            'type': 'personal',
            'is_default': False,
        },
        workflow_id=None,
        task_id=None,
        request=request,
    )


def test_template_preset_deleted__request__preset_object(
    mocker,
    events_enabled,
    request_factory,
):

    # arrange
    owner = create_test_owner()
    template = create_test_template(user=owner, is_active=True)
    preset = create_test_template_preset(
        template=template,
        author=owner,
        name='Weekly',
    )
    request = request_factory.delete(path='/templates/presets/1')
    request.user = owner
    request.token_type = AuthTokenType.USER
    emit_mock = mocker.patch('src.logs.events.services.emit')

    # act
    AuditEventService.template_preset_deleted(
        request=request,
        preset=preset,
    )

    # assert
    emit_mock.assert_called_once_with(
        EventName.TEMPLATE_PRESET_DELETE,
        account_id=owner.account_id,
        actor=Actor(type=ActorType.USER, id=owner.id, email=owner.email),
        event_object=EventObject(
            type=EventObjectType.TEMPLATE_PRESET,
            id=preset.id,
        ),
        payload={
            'name': 'Weekly',
            'template_id': template.id,
            'type': 'personal',
            'is_default': False,
        },
        workflow_id=None,
        task_id=None,
        request=request,
    )


def test_template_preset_set_default__default_preset__is_default_true(
    mocker,
    events_enabled,
    request_factory,
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
    request = request_factory.post(path='/templates/presets/1/default')
    request.user = owner
    request.token_type = AuthTokenType.USER
    emit_mock = mocker.patch('src.logs.events.services.emit')

    # act
    AuditEventService.template_preset_set_default(
        request=request,
        preset=preset,
    )

    # assert
    emit_mock.assert_called_once_with(
        EventName.TEMPLATE_PRESET_SET_DEFAULT,
        account_id=owner.account_id,
        actor=Actor(type=ActorType.USER, id=owner.id, email=owner.email),
        event_object=EventObject(
            type=EventObjectType.TEMPLATE_PRESET,
            id=preset.id,
        ),
        payload={
            'name': 'Weekly',
            'template_id': template.id,
            'type': 'personal',
            'is_default': True,
        },
        workflow_id=None,
        task_id=None,
        request=request,
    )


def test_fieldset_created__request__fieldset_object(
    mocker,
    events_enabled,
    request_factory,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    fieldset = create_test_shared_fieldset(account=account, name='Address')
    request = request_factory.post(path='/templates/fieldsets')
    request.user = owner
    request.token_type = AuthTokenType.USER
    emit_mock = mocker.patch('src.logs.events.services.emit')

    # act
    AuditEventService.fieldset_created(request=request, fieldset=fieldset)

    # assert
    emit_mock.assert_called_once_with(
        EventName.FIELDSET_CREATE,
        account_id=account.id,
        actor=Actor(type=ActorType.USER, id=owner.id, email=owner.email),
        event_object=EventObject(
            type=EventObjectType.FIELDSET,
            id=fieldset.id,
        ),
        payload={'name': 'Address'},
        workflow_id=None,
        task_id=None,
        request=request,
    )


def test_fieldset_updated__request__fieldset_object(
    mocker,
    events_enabled,
    request_factory,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    fieldset = create_test_shared_fieldset(account=account, name='Address')
    request = request_factory.put(path='/templates/fieldsets/1')
    request.user = owner
    request.token_type = AuthTokenType.USER
    emit_mock = mocker.patch('src.logs.events.services.emit')

    # act
    AuditEventService.fieldset_updated(request=request, fieldset=fieldset)

    # assert
    emit_mock.assert_called_once_with(
        EventName.FIELDSET_UPDATE,
        account_id=account.id,
        actor=Actor(type=ActorType.USER, id=owner.id, email=owner.email),
        event_object=EventObject(
            type=EventObjectType.FIELDSET,
            id=fieldset.id,
        ),
        payload={'name': 'Address'},
        workflow_id=None,
        task_id=None,
        request=request,
    )


def test_fieldset_cloned__request__source_fieldset_id_in_payload(
    mocker,
    events_enabled,
    request_factory,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    fieldset = create_test_shared_fieldset(account=account, name='Address')
    clone = create_test_shared_fieldset(
        account=account,
        name='Copy of Address',
    )
    request = request_factory.post(path='/templates/fieldsets/1/clone')
    request.user = owner
    request.token_type = AuthTokenType.USER
    emit_mock = mocker.patch('src.logs.events.services.emit')

    # act
    AuditEventService.fieldset_cloned(
        request=request,
        clone=clone,
        source_fieldset_id=fieldset.id,
    )

    # assert
    emit_mock.assert_called_once_with(
        EventName.FIELDSET_CLONE,
        account_id=account.id,
        actor=Actor(type=ActorType.USER, id=owner.id, email=owner.email),
        event_object=EventObject(type=EventObjectType.FIELDSET, id=clone.id),
        payload={
            'name': 'Copy of Address',
            'source_fieldset_id': fieldset.id,
        },
        workflow_id=None,
        task_id=None,
        request=request,
    )


def test_fieldset_deleted__request__fieldset_object(
    mocker,
    events_enabled,
    request_factory,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    fieldset = create_test_shared_fieldset(account=account, name='Address')
    request = request_factory.delete(path='/templates/fieldsets/1')
    request.user = owner
    request.token_type = AuthTokenType.USER
    emit_mock = mocker.patch('src.logs.events.services.emit')

    # act
    AuditEventService.fieldset_deleted(request=request, fieldset=fieldset)

    # assert
    emit_mock.assert_called_once_with(
        EventName.FIELDSET_DELETE,
        account_id=account.id,
        actor=Actor(type=ActorType.USER, id=owner.id, email=owner.email),
        event_object=EventObject(
            type=EventObjectType.FIELDSET,
            id=fieldset.id,
        ),
        payload={'name': 'Address'},
        workflow_id=None,
        task_id=None,
        request=request,
    )


def test_dataset_created__request__items_count_in_payload(
    mocker,
    events_enabled,
    request_factory,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    dataset = create_test_dataset(account=account, name='Cities')
    request = request_factory.post(path='/datasets')
    request.user = owner
    request.token_type = AuthTokenType.USER
    emit_mock = mocker.patch('src.logs.events.services.emit')

    # act
    AuditEventService.dataset_created(
        request=request,
        dataset=dataset,
        items_count=2,
    )

    # assert
    emit_mock.assert_called_once_with(
        EventName.DATASET_CREATE,
        account_id=account.id,
        actor=Actor(type=ActorType.USER, id=owner.id, email=owner.email),
        event_object=EventObject(type=EventObjectType.DATASET, id=dataset.id),
        payload={'name': 'Cities', 'items_count': 2},
        workflow_id=None,
        task_id=None,
        request=request,
    )


def test_dataset_updated__changed_fields__names_only(
    mocker,
    events_enabled,
    request_factory,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    dataset = create_test_dataset(account=account, name='Cities')
    request = request_factory.put(path='/datasets/1')
    request.user = owner
    request.token_type = AuthTokenType.USER
    emit_mock = mocker.patch('src.logs.events.services.emit')

    # act
    AuditEventService.dataset_updated(
        request=request,
        dataset=dataset,
        changed_fields=['description', 'name'],
    )

    # assert
    emit_mock.assert_called_once_with(
        EventName.DATASET_UPDATE,
        account_id=account.id,
        actor=Actor(type=ActorType.USER, id=owner.id, email=owner.email),
        event_object=EventObject(type=EventObjectType.DATASET, id=dataset.id),
        payload={
            'name': 'Cities',
            'changed_fields': ['description', 'name'],
        },
        workflow_id=None,
        task_id=None,
        request=request,
    )


def test_dataset_deleted__request__dataset_object(
    mocker,
    events_enabled,
    request_factory,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    dataset = create_test_dataset(account=account, name='Cities')
    request = request_factory.delete(path='/datasets/1')
    request.user = owner
    request.token_type = AuthTokenType.USER
    emit_mock = mocker.patch('src.logs.events.services.emit')

    # act
    AuditEventService.dataset_deleted(request=request, dataset=dataset)

    # assert
    emit_mock.assert_called_once_with(
        EventName.DATASET_DELETE,
        account_id=account.id,
        actor=Actor(type=ActorType.USER, id=owner.id, email=owner.email),
        event_object=EventObject(type=EventObjectType.DATASET, id=dataset.id),
        payload={'name': 'Cities'},
        workflow_id=None,
        task_id=None,
        request=request,
    )


def test_dataset_items_added__request__items_count_in_payload(
    mocker,
    events_enabled,
    request_factory,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    dataset = create_test_dataset(account=account, name='Cities')
    request = request_factory.post(path='/datasets/1/items')
    request.user = owner
    request.token_type = AuthTokenType.USER
    emit_mock = mocker.patch('src.logs.events.services.emit')

    # act
    AuditEventService.dataset_items_added(
        request=request,
        dataset=dataset,
        items_count=3,
    )

    # assert
    emit_mock.assert_called_once_with(
        EventName.DATASET_ITEMS_ADD,
        account_id=account.id,
        actor=Actor(type=ActorType.USER, id=owner.id, email=owner.email),
        event_object=EventObject(type=EventObjectType.DATASET, id=dataset.id),
        payload={'name': 'Cities', 'items_count': 3},
        workflow_id=None,
        task_id=None,
        request=request,
    )


def test_dataset_items_replaced__request__items_count_in_payload(
    mocker,
    events_enabled,
    request_factory,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    dataset = create_test_dataset(account=account, name='Cities')
    request = request_factory.put(path='/datasets/1/items')
    request.user = owner
    request.token_type = AuthTokenType.USER
    emit_mock = mocker.patch('src.logs.events.services.emit')

    # act
    AuditEventService.dataset_items_replaced(
        request=request,
        dataset=dataset,
        items_count=4,
    )

    # assert
    emit_mock.assert_called_once_with(
        EventName.DATASET_ITEMS_REPLACE,
        account_id=account.id,
        actor=Actor(type=ActorType.USER, id=owner.id, email=owner.email),
        event_object=EventObject(type=EventObjectType.DATASET, id=dataset.id),
        payload={'name': 'Cities', 'items_count': 4},
        workflow_id=None,
        task_id=None,
        request=request,
    )


def test_dataset_item_created__request__item_object(
    mocker,
    events_enabled,
    request_factory,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    dataset = create_test_dataset(account=account)
    item = dataset.items.get(order=1)
    request = request_factory.post(path='/datasets/1/items')
    request.user = owner
    request.token_type = AuthTokenType.USER
    emit_mock = mocker.patch('src.logs.events.services.emit')

    # act
    AuditEventService.dataset_item_created(request=request, item=item)

    # assert
    emit_mock.assert_called_once_with(
        EventName.DATASET_ITEM_CREATE,
        account_id=account.id,
        actor=Actor(type=ActorType.USER, id=owner.id, email=owner.email),
        event_object=EventObject(
            type=EventObjectType.DATASET_ITEM,
            id=item.id,
        ),
        payload={'dataset_id': dataset.id},
        workflow_id=None,
        task_id=None,
        request=request,
    )


def test_dataset_item_updated__changed_fields__names_only(
    mocker,
    events_enabled,
    request_factory,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    dataset = create_test_dataset(account=account)
    item = dataset.items.get(order=1)
    request = request_factory.put(path='/datasets/items/1')
    request.user = owner
    request.token_type = AuthTokenType.USER
    emit_mock = mocker.patch('src.logs.events.services.emit')

    # act
    AuditEventService.dataset_item_updated(
        request=request,
        item=item,
        changed_fields=['value'],
    )

    # assert
    emit_mock.assert_called_once_with(
        EventName.DATASET_ITEM_UPDATE,
        account_id=account.id,
        actor=Actor(type=ActorType.USER, id=owner.id, email=owner.email),
        event_object=EventObject(
            type=EventObjectType.DATASET_ITEM,
            id=item.id,
        ),
        payload={
            'dataset_id': dataset.id,
            'changed_fields': ['value'],
        },
        workflow_id=None,
        task_id=None,
        request=request,
    )


def test_dataset_item_deleted__request__item_object(
    mocker,
    events_enabled,
    request_factory,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    dataset = create_test_dataset(account=account)
    item = dataset.items.get(order=1)
    request = request_factory.delete(path='/datasets/items/1')
    request.user = owner
    request.token_type = AuthTokenType.USER
    emit_mock = mocker.patch('src.logs.events.services.emit')

    # act
    AuditEventService.dataset_item_deleted(request=request, item=item)

    # assert
    emit_mock.assert_called_once_with(
        EventName.DATASET_ITEM_DELETE,
        account_id=account.id,
        actor=Actor(type=ActorType.USER, id=owner.id, email=owner.email),
        event_object=EventObject(
            type=EventObjectType.DATASET_ITEM,
            id=item.id,
        ),
        payload={'dataset_id': dataset.id},
        workflow_id=None,
        task_id=None,
        request=request,
    )


def test_workflow_updated__kickoff_fields__kickoff_key(
    mocker,
    events_enabled,
    request_factory,
):

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(user=owner, tasks_count=1)
    request = request_factory.patch(path='/workflows/1')
    request.user = owner
    request.token_type = AuthTokenType.USER
    emit_mock = mocker.patch('src.logs.events.services.emit')

    # act
    AuditEventService.workflow_updated(
        request=request,
        workflow=workflow,
        changed_fields=['kickoff', 'name'],
        kickoff_fields=['field-1'],
    )

    # assert
    emit_mock.assert_called_once_with(
        EventName.WORKFLOW_UPDATE,
        account_id=owner.account_id,
        actor=Actor(type=ActorType.USER, id=owner.id, email=owner.email),
        event_object=EventObject(
            type=EventObjectType.WORKFLOW,
            id=workflow.id,
        ),
        payload={
            'workflow_name': workflow.name,
            'changed_fields': ['kickoff', 'name'],
            'kickoff_fields': ['field-1'],
        },
        workflow_id=workflow.id,
        task_id=None,
        request=request,
    )


def test_workflow_updated__no_kickoff_fields__no_kickoff_key(
    mocker,
    events_enabled,
    request_factory,
):

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(user=owner, tasks_count=1)
    request = request_factory.patch(path='/workflows/1')
    request.user = owner
    request.token_type = AuthTokenType.USER
    emit_mock = mocker.patch('src.logs.events.services.emit')

    # act
    AuditEventService.workflow_updated(
        request=request,
        workflow=workflow,
        changed_fields=['name'],
        kickoff_fields=[],
    )

    # assert
    emit_mock.assert_called_once_with(
        EventName.WORKFLOW_UPDATE,
        account_id=owner.account_id,
        actor=Actor(type=ActorType.USER, id=owner.id, email=owner.email),
        event_object=EventObject(
            type=EventObjectType.WORKFLOW,
            id=workflow.id,
        ),
        payload={
            'workflow_name': workflow.name,
            'changed_fields': ['name'],
        },
        workflow_id=workflow.id,
        task_id=None,
        request=request,
    )


def test_comment_updated__comment_with_task__task_name(
    mocker,
    events_enabled,
    request_factory,
):

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(user=owner, tasks_count=1)
    task = workflow.tasks.get(number=1)
    comment = create_test_event(
        workflow=workflow,
        user=owner,
        type_event=WorkflowEventType.COMMENT,
    )
    request = request_factory.put(path='/workflows/comments/1')
    request.user = owner
    request.token_type = AuthTokenType.USER
    emit_mock = mocker.patch('src.logs.events.services.emit')

    # act
    AuditEventService.comment_updated(request=request, comment=comment)

    # assert
    emit_mock.assert_called_once_with(
        EventName.TASK_COMMENT_UPDATE,
        account_id=owner.account_id,
        actor=Actor(type=ActorType.USER, id=owner.id, email=owner.email),
        event_object=EventObject(
            type=EventObjectType.COMMENT,
            id=comment.id,
        ),
        payload={
            'workflow_name': workflow.name,
            'task_name': task.name,
        },
        workflow_id=workflow.id,
        task_id=task.id,
        request=request,
    )


def test_comment_updated__comment_without_task__no_task_name(
    mocker,
    events_enabled,
    request_factory,
):

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(user=owner, tasks_count=1)
    comment = create_test_event(
        workflow=workflow,
        user=owner,
        type_event=WorkflowEventType.COMMENT,
    )
    comment.task = None
    request = request_factory.put(path='/workflows/comments/1')
    request.user = owner
    request.token_type = AuthTokenType.USER
    emit_mock = mocker.patch('src.logs.events.services.emit')

    # act
    AuditEventService.comment_updated(request=request, comment=comment)

    # assert
    emit_mock.assert_called_once_with(
        EventName.TASK_COMMENT_UPDATE,
        account_id=owner.account_id,
        actor=Actor(type=ActorType.USER, id=owner.id, email=owner.email),
        event_object=EventObject(
            type=EventObjectType.COMMENT,
            id=comment.id,
        ),
        payload={'workflow_name': workflow.name},
        workflow_id=workflow.id,
        task_id=None,
        request=request,
    )


def test_comment_deleted__request__comment_object(
    mocker,
    events_enabled,
    request_factory,
):

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(user=owner, tasks_count=1)
    task = workflow.tasks.get(number=1)
    comment = create_test_event(
        workflow=workflow,
        user=owner,
        type_event=WorkflowEventType.COMMENT,
    )
    request = request_factory.delete(path='/workflows/comments/1')
    request.user = owner
    request.token_type = AuthTokenType.USER
    emit_mock = mocker.patch('src.logs.events.services.emit')

    # act
    AuditEventService.comment_deleted(request=request, comment=comment)

    # assert
    emit_mock.assert_called_once_with(
        EventName.TASK_COMMENT_DELETE,
        account_id=owner.account_id,
        actor=Actor(type=ActorType.USER, id=owner.id, email=owner.email),
        event_object=EventObject(
            type=EventObjectType.COMMENT,
            id=comment.id,
        ),
        payload={
            'workflow_name': workflow.name,
            'task_name': task.name,
        },
        workflow_id=workflow.id,
        task_id=task.id,
        request=request,
    )


def test_checklist_item_marked__request__checklist_object(
    mocker,
    events_enabled,
    request_factory,
):

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
    request = request_factory.post(path='/v2/tasks/checklists/1/mark')
    request.user = owner
    request.token_type = AuthTokenType.USER
    emit_mock = mocker.patch('src.logs.events.services.emit')

    # act
    AuditEventService.checklist_item_marked(
        request=request,
        checklist=checklist,
        selection_id=selection.id,
    )

    # assert
    emit_mock.assert_called_once_with(
        EventName.TASK_CHECKLIST_MARK,
        account_id=owner.account_id,
        actor=Actor(type=ActorType.USER, id=owner.id, email=owner.email),
        event_object=EventObject(
            type=EventObjectType.CHECKLIST,
            id=checklist.id,
        ),
        payload={
            'workflow_name': workflow.name,
            'task_name': task.name,
            'checklist_api_name': 'checklist',
            'selection_id': selection.id,
        },
        workflow_id=workflow.id,
        task_id=task.id,
        request=request,
    )


def test_checklist_item_unmarked__request__checklist_object(
    mocker,
    events_enabled,
    request_factory,
):

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
    request = request_factory.post(path='/v2/tasks/checklists/1/unmark')
    request.user = owner
    request.token_type = AuthTokenType.USER
    emit_mock = mocker.patch('src.logs.events.services.emit')

    # act
    AuditEventService.checklist_item_unmarked(
        request=request,
        checklist=checklist,
        selection_id=selection.id,
    )

    # assert
    emit_mock.assert_called_once_with(
        EventName.TASK_CHECKLIST_UNMARK,
        account_id=owner.account_id,
        actor=Actor(type=ActorType.USER, id=owner.id, email=owner.email),
        event_object=EventObject(
            type=EventObjectType.CHECKLIST,
            id=checklist.id,
        ),
        payload={
            'workflow_name': workflow.name,
            'task_name': task.name,
            'checklist_api_name': 'checklist',
            'selection_id': selection.id,
        },
        workflow_id=workflow.id,
        task_id=task.id,
        request=request,
    )


def test_comment_updated__logs_disabled__no_event(
    mocker,
    request_factory,
):

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(user=owner, tasks_count=1)
    comment = create_test_event(
        workflow=workflow,
        user=owner,
        type_event=WorkflowEventType.COMMENT,
    )
    request = request_factory.put(path='/workflows/comments/1')
    request.user = owner
    request.token_type = AuthTokenType.USER
    emit_mock = mocker.patch('src.logs.events.services.emit')

    # act
    AuditEventService.comment_updated(request=request, comment=comment)

    # assert
    emit_mock.assert_not_called()


def test_checklist_item_marked__logs_disabled__no_event(
    mocker,
    request_factory,
):

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
    request = request_factory.post(path='/v2/tasks/checklists/1/mark')
    request.user = owner
    request.token_type = AuthTokenType.USER
    emit_mock = mocker.patch('src.logs.events.services.emit')

    # act
    AuditEventService.checklist_item_marked(
        request=request,
        checklist=checklist,
        selection_id=selection.id,
    )

    # assert
    emit_mock.assert_not_called()
