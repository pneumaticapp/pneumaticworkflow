import pytest
from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.contrib.admin.models import (
    ADDITION,
    CHANGE,
    DELETION,
    LogEntry,
)
from django.contrib.auth import get_user_model
from django.forms import MultiWidget
from django.urls import reverse
from django.utils import timezone

from src.accounts.admin import (
    AccountAdmin,
    GroupAdmin,
    SystemMessageAdmin,
    UsersAdmin,
)
from src.accounts.models import (
    Account,
    SystemMessage,
    UserGroup,
    UserInvite,
)
from src.accounts.enums import UserType
from src.logs.events.admin_site import JournaledAdminMixin
from src.logs.events.enums import (
    AdminEvents,
    EventCategory,
    EventObjectType,
)
from src.logs.events.schema import Actor, EventObject
from src.processes.tests.fixtures import (
    create_invited_user,
    create_test_account,
    create_test_admin,
    create_test_group,
    create_test_owner,
)

UserModel = get_user_model()
pytestmark = pytest.mark.django_db


def test_log_change__user_changed__admin_update_event(
    fake_stream,
    request_factory,
):

    # arrange
    staff = create_test_owner()
    client_account = create_test_account(name='Client')
    user = create_test_admin(account=client_account)
    request = request_factory.get('/')
    request.user = staff
    users_admin = UsersAdmin(UserModel, admin.site)

    # act
    entry = users_admin.log_change(
        request=request,
        instance=user,
        message=[{'changed': {'fields': ['is_admin']}}],
    )

    # assert
    assert LogEntry.objects.get(id=entry.id).action_flag == CHANGE
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    assert event.type == AdminEvents.UPDATE
    assert event.category == EventCategory.ADMIN
    assert event.account_id == client_account.id
    assert event.actor == Actor(
        id=staff.id,
        email=staff.email,
        user_type=UserType.USER,
    )
    assert event.object == EventObject(
        type=EventObjectType.USER,
        id=user.id,
    )
    assert event.payload == {
        'model': 'accounts.user',
        'changed_fields': ['is_admin'],
    }
    assert event.auth_type is None


def test_log_change__password_form__one_password_field(
    fake_stream,
    request_factory,
):

    # arrange
    staff = create_test_owner()
    client_account = create_test_account(name='Client')
    user = create_test_admin(account=client_account)
    request = request_factory.get('/')
    request.user = staff
    users_admin = UsersAdmin(UserModel, admin.site)
    message = [{'changed': {'fields': ['password1', 'password2']}}]

    # act
    users_admin.log_change(
        request=request,
        instance=user,
        message=message,
    )

    # assert
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    assert event.type == AdminEvents.UPDATE
    assert event.category == EventCategory.ADMIN
    assert event.account_id == client_account.id
    assert event.actor == Actor(
        id=staff.id,
        email=staff.email,
        user_type=UserType.USER,
    )
    assert event.object == EventObject(
        type=EventObjectType.USER,
        id=user.id,
    )
    assert event.payload == {
        'model': 'accounts.user',
        'changed_fields': ['password'],
    }


def test_log_change__inline_changes__lines_without_object_text(
    fake_stream,
    request_factory,
):

    """ The inline object text is the e-mail of a contact as often as
        not: only the model and the field names may leave. """

    # arrange
    staff = create_test_owner()
    client_account = create_test_account(name='Client')
    user = create_test_admin(account=client_account)
    request = request_factory.get('/')
    request.user = staff
    users_admin = UsersAdmin(UserModel, admin.site)
    message = [
        {'changed': {'fields': ['last_name', 'first_name']}},
        {'added': {'name': 'Group', 'object': 'Support'}},
        {
            'changed': {
                'name': 'Contact',
                'object': 'ann@test.test',
                'fields': ['status', 'job_title'],
            },
        },
        {'deleted': {'name': 'Group', 'object': 'Sales'}},
    ]

    # act
    users_admin.log_change(
        request=request,
        instance=user,
        message=message,
    )

    # assert
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    assert event.type == AdminEvents.UPDATE
    assert event.category == EventCategory.ADMIN
    assert event.account_id == client_account.id
    assert event.actor == Actor(
        id=staff.id,
        email=staff.email,
        user_type=UserType.USER,
    )
    assert event.object == EventObject(
        type=EventObjectType.USER,
        id=user.id,
    )
    assert event.payload == {
        'model': 'accounts.user',
        'changed_fields': ['first_name', 'last_name'],
        'inline_changes': [
            'added Group',
            'changed Contact: job_title, status',
            'deleted Group',
        ],
    }


def test_log_change__not_a_dict_line__line_skipped(
    fake_stream,
    request_factory,
):

    """ A line that is not an object of the admin site says nothing
        about the fields and is left out. """

    # arrange
    staff = create_test_owner()
    client_account = create_test_account(name='Client')
    user = create_test_admin(account=client_account)
    request = request_factory.get('/')
    request.user = staff
    users_admin = UsersAdmin(UserModel, admin.site)
    message = ['dropped', {'changed': {'fields': ['is_admin']}}]

    # act
    users_admin.log_change(
        request=request,
        instance=user,
        message=message,
    )

    # assert
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    assert event.type == AdminEvents.UPDATE
    assert event.account_id == client_account.id
    assert event.object == EventObject(
        type=EventObjectType.USER,
        id=user.id,
    )
    assert event.payload == {
        'model': 'accounts.user',
        'changed_fields': ['is_admin'],
    }


def test_log_change__plain_text_message__model_only(
    fake_stream,
    request_factory,
):

    # arrange
    staff = create_test_owner()
    client_account = create_test_account(name='Client')
    user = create_test_admin(account=client_account)
    request = request_factory.get('/')
    request.user = staff
    users_admin = UsersAdmin(UserModel, admin.site)

    # act
    users_admin.log_change(
        request=request,
        instance=user,
        message='Changed is_admin.',
    )

    # assert
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    assert event.type == AdminEvents.UPDATE
    assert event.category == EventCategory.ADMIN
    assert event.account_id == client_account.id
    assert event.actor == Actor(
        id=staff.id,
        email=staff.email,
        user_type=UserType.USER,
    )
    assert event.object == EventObject(
        type=EventObjectType.USER,
        id=user.id,
    )
    assert event.payload == {'model': 'accounts.user'}


def test_log_addition__account_added__own_account_id(
    fake_stream,
    request_factory,
):

    # arrange
    staff = create_test_owner()
    client_account = create_test_account(name='Client')
    request = request_factory.get('/')
    request.user = staff
    account_admin = AccountAdmin(Account, admin.site)

    # act
    entry = account_admin.log_addition(
        request=request,
        instance=client_account,
        message=[{'added': {}}],
    )

    # assert
    assert LogEntry.objects.get(id=entry.id).action_flag == ADDITION
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    assert event.type == AdminEvents.CREATE
    assert event.category == EventCategory.ADMIN
    assert event.account_id == client_account.id
    assert event.actor == Actor(
        id=staff.id,
        email=staff.email,
        user_type=UserType.USER,
    )
    assert event.object == EventObject(
        type=EventObjectType.ACCOUNT,
        id=client_account.id,
    )
    assert event.payload == {'model': 'accounts.account'}


def test_log_deletion__group_deleted__account_of_the_group(
    fake_stream,
    request_factory,
):

    # arrange
    staff = create_test_owner()
    client_account = create_test_account(name='Client')
    group = create_test_group(account=client_account)
    request = request_factory.get('/')
    request.user = staff
    group_admin = GroupAdmin(UserGroup, admin.site)

    # act
    entry = group_admin.log_deletion(
        request=request,
        instance=group,
        object_repr=str(group),
    )

    # assert
    assert LogEntry.objects.get(id=entry.id).action_flag == DELETION
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    assert event.type == AdminEvents.DELETE
    assert event.category == EventCategory.ADMIN
    assert event.account_id == client_account.id
    assert event.actor == Actor(
        id=staff.id,
        email=staff.email,
        user_type=UserType.USER,
    )
    assert event.object == EventObject(
        type=EventObjectType.GROUP,
        id=group.id,
    )
    assert event.payload == {'model': 'accounts.usergroup'}


def test_log_addition__model_without_account__superuser_account(
    fake_stream,
    request_factory,
):

    """ A row of no account is journaled into the account of the
        superuser, typed as any other object. """

    # arrange
    staff = create_test_owner()
    system_message = SystemMessage.objects.create(
        title='Maintenance',
        text='Tonight',
        publication_date=timezone.now(),
    )
    request = request_factory.get('/')
    request.user = staff
    journaled_admin = type(
        'JournaledSystemMessageAdmin',
        (JournaledAdminMixin, ModelAdmin),
        {},
    )(SystemMessage, admin.site)

    # act
    journaled_admin.log_addition(
        request=request,
        instance=system_message,
        message=[{'added': {}}],
    )

    # assert
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    assert event.type == AdminEvents.CREATE
    assert event.category == EventCategory.ADMIN
    assert event.account_id == staff.account_id
    assert event.actor == Actor(
        id=staff.id,
        email=staff.email,
        user_type=UserType.USER,
    )
    assert event.object == EventObject(
        type=EventObjectType.OTHER,
        id=system_message.id,
    )
    assert event.payload == {'model': 'accounts.systemmessage'}


def test_log_change__user_invite__no_object_id(
    fake_stream,
    request_factory,
):

    """ The id of an invite is the key that accepts it: anybody who
        reads the journal could join the account with it. """

    # arrange
    staff = create_test_owner()
    client_account = create_test_account(name='Client')
    account_admin = create_test_admin(account=client_account)
    invited_user = create_invited_user(
        user=account_admin,
        email='invited@test.test',
    )
    invite = UserInvite.objects.get(invited_user=invited_user)
    request = request_factory.get('/')
    request.user = staff
    journaled_admin = type(
        'JournaledInviteAdmin',
        (JournaledAdminMixin, ModelAdmin),
        {},
    )(UserInvite, admin.site)

    # act
    journaled_admin.log_change(
        request=request,
        instance=invite,
        message=[{'changed': {'fields': ['status']}}],
    )

    # assert
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    assert event.type == AdminEvents.UPDATE
    assert event.category == EventCategory.ADMIN
    assert event.account_id == client_account.id
    assert event.actor == Actor(
        id=staff.id,
        email=staff.email,
        user_type=UserType.USER,
    )
    assert event.object == EventObject(
        type=EventObjectType.INVITE,
        id=None,
    )
    assert event.payload == {
        'model': 'accounts.userinvite',
        'changed_fields': ['status'],
    }


def test_log_change__logs_disabled__entry_written_no_event(
    mocker,
    request_factory,
    run_on_commit,
):

    """ LOGS_BACKEND is none by default in tests: the admin site still
        keeps its own history, the journal is not reached. """

    # arrange
    get_stream_mock = mocker.patch('src.logs.events.emitter.get_stream')
    staff = create_test_owner()
    client_account = create_test_account(name='Client')
    user = create_test_admin(account=client_account)
    request = request_factory.get('/')
    request.user = staff
    users_admin = UsersAdmin(UserModel, admin.site)

    # act
    entry = users_admin.log_change(
        request=request,
        instance=user,
        message=[{'changed': {'fields': ['is_admin']}}],
    )

    # assert
    assert LogEntry.objects.get(id=entry.id).action_flag == CHANGE
    get_stream_mock.assert_not_called()


def test_log_change__admin_without_mixin__no_event(
    fake_stream,
    request_factory,
):

    # arrange
    staff = create_test_owner()
    system_message = SystemMessage.objects.create(
        title='Maintenance',
        text='Tonight',
        publication_date=timezone.now(),
    )
    request = request_factory.get('/')
    request.user = staff
    system_message_admin = SystemMessageAdmin(SystemMessage, admin.site)

    # act
    entry = system_message_admin.log_change(
        request=request,
        object=system_message,
        message=[{'changed': {'fields': ['title']}}],
    )

    # assert
    assert LogEntry.objects.get(id=entry.id).action_flag == CHANGE
    assert fake_stream.events == []


def test_log_change__admin_change_form__is_admin_in_changed_fields(
    fake_stream,
    client,
):

    """ The admin site writes the row itself: the change form of a
        user reaches the hook with the message Django builds. """

    # arrange
    staff = create_test_owner()
    staff.is_superuser = True
    staff.save(update_fields=['is_superuser'])
    client_account = create_test_account(name='Client')
    user = create_test_admin(account=client_account)

    # The change form requires both digest times, a new user has none;
    # the split widgets drop microseconds and would report a change.
    moment = timezone.now().replace(microsecond=0)
    user.last_digest_send_time = moment
    user.last_tasks_digest_send_time = moment
    user.save(
        update_fields=[
            'last_digest_send_time',
            'last_tasks_digest_send_time',
        ],
    )
    client.force_login(user=staff)
    url = reverse(
        viewname='admin:accounts_user_change',
        args=[user.id],
    )
    page = client.get(path=url)

    # What a browser posts back without touching a field: every
    # initial value in the format of its widget, the hidden initial
    # inputs of date_joined and the management forms of the inlines.
    form = page.context['adminform'].form
    data = {}
    for name, form_field in form.fields.items():
        value = form.initial.get(name)
        if isinstance(form_field.widget, MultiWidget):
            parts = form_field.widget.decompress(value)
            data[f'{name}_0'] = parts[0] or ''
            data[f'{name}_1'] = parts[1] or ''
        elif value is True:
            data[name] = 'on'
        elif value is not None and value is not False:
            data[name] = value
    data['initial-date_joined_0'] = data['date_joined_0']
    data['initial-date_joined_1'] = data['date_joined_1']
    for inline in page.context['inline_admin_formsets']:
        management_form = inline.formset.management_form
        for name, value in management_form.initial.items():
            data[management_form.add_prefix(name)] = value
    del data['is_admin']

    # act
    response = client.post(path=url, data=data)

    # assert
    assert response.status_code == 302
    user.refresh_from_db()
    assert user.is_admin is False
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    assert event.type == AdminEvents.UPDATE
    assert event.category == EventCategory.ADMIN
    assert event.account_id == client_account.id
    assert event.actor == Actor(
        id=staff.id,
        email=staff.email,
        user_type=UserType.USER,
    )
    assert event.object == EventObject(
        type=EventObjectType.USER,
        id=user.id,
    )
    assert event.payload == {
        'model': 'accounts.user',
        'changed_fields': ['is_admin'],
    }


def test_log_deletion__delete_selected_action__event_per_row(
    fake_stream,
    client,
):

    """ The "delete selected" action of the changelist reports every
        row to the hook before it deletes them: one event per user,
        in the order of the changelist (newest first). """

    # arrange
    staff = create_test_owner()
    staff.is_superuser = True
    staff.save(update_fields=['is_superuser'])
    client_account = create_test_account(name='Client')
    user_1 = create_test_admin(
        account=client_account,
        email='first@test.test',
    )
    user_2 = create_test_admin(
        account=client_account,
        email='second@test.test',
    )
    client.force_login(user=staff)
    url = reverse(viewname='admin:accounts_user_changelist')
    data = {
        'action': 'delete_selected',
        '_selected_action': [user_1.id, user_2.id],
        'post': 'yes',
    }

    # act
    response = client.post(path=url, data=data)

    # assert
    assert response.status_code == 302
    assert not UserModel.objects.filter(id__in=[user_1.id, user_2.id])
    assert LogEntry.objects.filter(action_flag=DELETION).count() == 2
    assert len(fake_stream.events) == 2
    event_1 = fake_stream.events[0][1]
    assert event_1.type == AdminEvents.DELETE
    assert event_1.category == EventCategory.ADMIN
    assert event_1.account_id == client_account.id
    assert event_1.actor == Actor(
        id=staff.id,
        email=staff.email,
        user_type=UserType.USER,
    )
    assert event_1.object == EventObject(
        type=EventObjectType.USER,
        id=user_2.id,
    )
    assert event_1.payload == {'model': 'accounts.user'}
    event_2 = fake_stream.events[1][1]
    assert event_2.type == AdminEvents.DELETE
    assert event_2.object == EventObject(
        type=EventObjectType.USER,
        id=user_1.id,
    )
    assert event_2.payload == {'model': 'accounts.user'}
