import json

import pytest
from django.contrib.admin.models import (
    ADDITION,
    CHANGE,
    DELETION,
    LogEntry,
)
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.forms import MultiWidget
from django.urls import reverse
from django.utils import timezone

from src.accounts.models import (
    Account,
    APIKey,
    SystemMessage,
    UserGroup,
    UserInvite,
)
from src.logs.enums import LogsBackend
from src.logs.events.admin_site import publish_log_entry
from src.logs.events.enums import (
    ActorType,
    EventCategory,
    EventName,
    EventObjectType,
)
from src.logs.events.schema import Actor, EventObject
from src.processes.tests.fixtures import (
    create_invited_user,
    create_test_account,
    create_test_admin,
    create_test_api_key,
    create_test_group,
    create_test_owner,
)

UserModel = get_user_model()
pytestmark = pytest.mark.django_db


def test_publish_log_entry__user_changed__admin_update_event(
    fake_stream,
):

    # arrange
    staff = create_test_owner()
    client_account = create_test_account(name='Client')
    user = create_test_admin(account=client_account)

    # act
    LogEntry.objects.log_action(
        user_id=staff.id,
        content_type_id=ContentType.objects.get_for_model(
            model=UserModel,
        ).pk,
        object_id=user.id,
        object_repr=str(user),
        action_flag=CHANGE,
        change_message=json.dumps([{'changed': {'fields': ['is_admin']}}]),
    )

    # assert
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    assert event.type == EventName.ADMIN_UPDATE
    assert event.category == EventCategory.AUDIT
    assert event.account_id == client_account.id
    assert event.actor == Actor(
        type=ActorType.USER,
        id=staff.id,
        email=staff.email,
    )
    assert event.object == EventObject(
        type=EventObjectType.USER,
        id=user.id,
    )
    assert event.payload == {
        'model': 'accounts.user',
        'changed_fields': ['is_admin'],
    }
    assert event.pii == ('actor.email',)


def test_publish_log_entry__password_form__one_password_field(
    fake_stream,
):

    # arrange
    staff = create_test_owner()
    client_account = create_test_account(name='Client')
    user = create_test_admin(account=client_account)
    message = [{'changed': {'fields': ['password1', 'password2']}}]

    # act
    LogEntry.objects.log_action(
        user_id=staff.id,
        content_type_id=ContentType.objects.get_for_model(
            model=UserModel,
        ).pk,
        object_id=user.id,
        object_repr=str(user),
        action_flag=CHANGE,
        change_message=json.dumps(message),
    )

    # assert
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    assert event.type == EventName.ADMIN_UPDATE
    assert event.category == EventCategory.AUDIT
    assert event.account_id == client_account.id
    assert event.actor == Actor(
        type=ActorType.USER,
        id=staff.id,
        email=staff.email,
    )
    assert event.object == EventObject(
        type=EventObjectType.USER,
        id=user.id,
    )
    assert event.payload == {
        'model': 'accounts.user',
        'changed_fields': ['password'],
    }


def test_publish_log_entry__inline_changes__lines_without_object_text(
    fake_stream,
):

    """ The inline object text is the e-mail of a contact as often as
        not: only the model and the field names may leave. """

    # arrange
    staff = create_test_owner()
    client_account = create_test_account(name='Client')
    user = create_test_admin(account=client_account)
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
    LogEntry.objects.log_action(
        user_id=staff.id,
        content_type_id=ContentType.objects.get_for_model(
            model=UserModel,
        ).pk,
        object_id=user.id,
        object_repr=str(user),
        action_flag=CHANGE,
        change_message=json.dumps(message),
    )

    # assert
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    assert event.type == EventName.ADMIN_UPDATE
    assert event.category == EventCategory.AUDIT
    assert event.account_id == client_account.id
    assert event.actor == Actor(
        type=ActorType.USER,
        id=staff.id,
        email=staff.email,
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


def test_publish_log_entry__not_a_dict_line__line_skipped(
    fake_stream,
):

    """ A row written by hand may hold a list of anything: a line that
        is not an object of the admin site says nothing about the
        fields and is left out. """

    # arrange
    staff = create_test_owner()
    client_account = create_test_account(name='Client')
    user = create_test_admin(account=client_account)
    message = ['dropped', {'changed': {'fields': ['is_admin']}}]

    # act
    LogEntry.objects.log_action(
        user_id=staff.id,
        content_type_id=ContentType.objects.get_for_model(
            model=UserModel,
        ).pk,
        object_id=user.id,
        object_repr=str(user),
        action_flag=CHANGE,
        change_message=json.dumps(message),
    )

    # assert
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    assert event.type == EventName.ADMIN_UPDATE
    assert event.account_id == client_account.id
    assert event.object == EventObject(
        type=EventObjectType.USER,
        id=user.id,
    )
    assert event.payload == {
        'model': 'accounts.user',
        'changed_fields': ['is_admin'],
    }


def test_publish_log_entry__account_added__own_account_id(
    fake_stream,
):

    # arrange
    staff = create_test_owner()
    client_account = create_test_account(name='Client')

    # act
    LogEntry.objects.log_action(
        user_id=staff.id,
        content_type_id=ContentType.objects.get_for_model(
            model=Account,
        ).pk,
        object_id=client_account.id,
        object_repr=str(client_account),
        action_flag=ADDITION,
        change_message=json.dumps([{'added': {}}]),
    )

    # assert
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    assert event.type == EventName.ADMIN_CREATE
    assert event.category == EventCategory.AUDIT
    assert event.account_id == client_account.id
    assert event.actor == Actor(
        type=ActorType.USER,
        id=staff.id,
        email=staff.email,
    )
    assert event.object == EventObject(
        type=EventObjectType.ACCOUNT,
        id=client_account.id,
    )
    assert event.payload == {'model': 'accounts.account'}


def test_publish_log_entry__account_without_object_id__superuser_account(
    fake_stream,
):

    """ log_action always stores the id as text, only a row written by
        hand has none: created directly for that reason. """

    # arrange
    staff = create_test_owner()

    # act
    LogEntry.objects.create(
        user=staff,
        content_type_id=ContentType.objects.get_for_model(
            model=Account,
        ).pk,
        object_id=None,
        object_repr='Client',
        action_flag=CHANGE,
        change_message='',
    )

    # assert
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    assert event.type == EventName.ADMIN_UPDATE
    assert event.category == EventCategory.AUDIT
    assert event.account_id == staff.account_id
    assert event.actor == Actor(
        type=ActorType.USER,
        id=staff.id,
        email=staff.email,
    )
    assert event.object == EventObject(
        type=EventObjectType.ACCOUNT,
        id=None,
    )
    assert event.payload == {'model': 'accounts.account'}


def test_publish_log_entry__without_content_type__other_object(
    fake_stream,
):

    """ The content type of a row is nullable and a deleted model
        leaves none behind: the label stays empty and the object is
        typed as any other one. """

    # arrange
    staff = create_test_owner()

    # act
    LogEntry.objects.create(
        user=staff,
        content_type_id=None,
        object_id='1',
        object_repr='Gone',
        action_flag=DELETION,
        change_message='',
    )

    # assert
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    assert event.type == EventName.ADMIN_DELETE
    assert event.category == EventCategory.AUDIT
    assert event.account_id == staff.account_id
    assert event.actor == Actor(
        type=ActorType.USER,
        id=staff.id,
        email=staff.email,
    )
    assert event.object == EventObject(
        type=EventObjectType.OTHER,
        id=1,
    )
    assert event.payload == {'model': ''}


def test_publish_log_entry__group_deleted__account_of_the_group(
    fake_stream,
):

    # arrange
    staff = create_test_owner()
    client_account = create_test_account(name='Client')
    group = create_test_group(account=client_account)

    # act
    LogEntry.objects.log_action(
        user_id=staff.id,
        content_type_id=ContentType.objects.get_for_model(
            model=UserGroup,
        ).pk,
        object_id=group.id,
        object_repr=str(group),
        action_flag=DELETION,
        change_message='',
    )

    # assert
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    assert event.type == EventName.ADMIN_DELETE
    assert event.category == EventCategory.AUDIT
    assert event.account_id == client_account.id
    assert event.actor == Actor(
        type=ActorType.USER,
        id=staff.id,
        email=staff.email,
    )
    assert event.object == EventObject(
        type=EventObjectType.GROUP,
        id=group.id,
    )
    assert event.payload == {'model': 'accounts.usergroup'}


def test_publish_log_entry__api_key_changed__api_key_object(
    fake_stream,
):

    # arrange
    staff = create_test_owner()
    client_account = create_test_account(name='Client')
    user = create_test_admin(account=client_account)
    api_key = create_test_api_key(user=user)

    # act
    LogEntry.objects.log_action(
        user_id=staff.id,
        content_type_id=ContentType.objects.get_for_model(
            model=APIKey,
        ).pk,
        object_id=api_key.id,
        object_repr=str(api_key),
        action_flag=CHANGE,
        change_message=json.dumps([{'changed': {'fields': ['name']}}]),
    )

    # assert
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    assert event.type == EventName.ADMIN_UPDATE
    assert event.category == EventCategory.AUDIT
    assert event.account_id == client_account.id
    assert event.actor == Actor(
        type=ActorType.USER,
        id=staff.id,
        email=staff.email,
    )
    assert event.object == EventObject(
        type=EventObjectType.API_KEY,
        id=api_key.id,
    )
    assert event.payload == {
        'model': 'accounts.apikey',
        'changed_fields': ['name'],
    }


def test_publish_log_entry__model_without_account__superuser_account(
    fake_stream,
):

    # arrange
    staff = create_test_owner()
    system_message = SystemMessage.objects.create(
        title='Maintenance',
        text='Tonight',
        publication_date=timezone.now(),
    )

    # act
    LogEntry.objects.log_action(
        user_id=staff.id,
        content_type_id=ContentType.objects.get_for_model(
            model=SystemMessage,
        ).pk,
        object_id=system_message.id,
        object_repr=str(system_message),
        action_flag=ADDITION,
        change_message=json.dumps([{'added': {}}]),
    )

    # assert
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    assert event.type == EventName.ADMIN_CREATE
    assert event.category == EventCategory.AUDIT
    assert event.account_id == staff.account_id
    assert event.actor == Actor(
        type=ActorType.USER,
        id=staff.id,
        email=staff.email,
    )
    assert event.object == EventObject(
        type=EventObjectType.OTHER,
        id=system_message.id,
    )
    assert event.payload == {'model': 'accounts.systemmessage'}


def test_publish_log_entry__missing_row__superuser_account(
    fake_stream,
):

    # arrange
    staff = create_test_owner()

    # act
    LogEntry.objects.log_action(
        user_id=staff.id,
        content_type_id=ContentType.objects.get_for_model(
            model=UserModel,
        ).pk,
        object_id='987654',
        object_repr='gone@test.test',
        action_flag=CHANGE,
        change_message=json.dumps([{'changed': {'fields': ['is_admin']}}]),
    )

    # assert
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    assert event.type == EventName.ADMIN_UPDATE
    assert event.category == EventCategory.AUDIT
    assert event.account_id == staff.account_id
    assert event.actor == Actor(
        type=ActorType.USER,
        id=staff.id,
        email=staff.email,
    )
    assert event.object == EventObject(
        type=EventObjectType.USER,
        id=987654,
    )
    assert event.payload == {
        'model': 'accounts.user',
        'changed_fields': ['is_admin'],
    }


def test_publish_log_entry__not_digit_object_id__string_id(
    fake_stream,
):

    # arrange
    staff = create_test_owner()

    # act
    LogEntry.objects.log_action(
        user_id=staff.id,
        content_type_id=ContentType.objects.get_for_model(
            model=UserModel,
        ).pk,
        object_id='abc',
        object_repr='abc',
        action_flag=DELETION,
        change_message='',
    )

    # assert
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    assert event.type == EventName.ADMIN_DELETE
    assert event.category == EventCategory.AUDIT
    assert event.account_id == staff.account_id
    assert event.actor == Actor(
        type=ActorType.USER,
        id=staff.id,
        email=staff.email,
    )
    assert event.object == EventObject(
        type=EventObjectType.USER,
        id='abc',
    )
    assert event.payload == {'model': 'accounts.user'}


def test_publish_log_entry__plain_text_message__model_only(
    fake_stream,
):

    # arrange
    staff = create_test_owner()
    client_account = create_test_account(name='Client')
    user = create_test_admin(account=client_account)

    # act
    LogEntry.objects.log_action(
        user_id=staff.id,
        content_type_id=ContentType.objects.get_for_model(
            model=UserModel,
        ).pk,
        object_id=user.id,
        object_repr=str(user),
        action_flag=CHANGE,
        change_message='Changed is_admin.',
    )

    # assert
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    assert event.type == EventName.ADMIN_UPDATE
    assert event.category == EventCategory.AUDIT
    assert event.account_id == client_account.id
    assert event.actor == Actor(
        type=ActorType.USER,
        id=staff.id,
        email=staff.email,
    )
    assert event.object == EventObject(
        type=EventObjectType.USER,
        id=user.id,
    )
    assert event.payload == {'model': 'accounts.user'}


def test_publish_log_entry__entry_saved_again__no_new_event(
    fake_stream,
):

    # arrange
    staff = create_test_owner()
    client_account = create_test_account(name='Client')
    user = create_test_admin(account=client_account)
    entry = LogEntry.objects.log_action(
        user_id=staff.id,
        content_type_id=ContentType.objects.get_for_model(
            model=UserModel,
        ).pk,
        object_id=user.id,
        object_repr=str(user),
        action_flag=CHANGE,
        change_message=json.dumps([{'changed': {'fields': ['is_admin']}}]),
    )
    entry.change_message = json.dumps([{'changed': {'fields': ['email']}}])

    # act
    entry.save()

    # assert
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    assert event.type == EventName.ADMIN_UPDATE
    assert event.payload == {
        'model': 'accounts.user',
        'changed_fields': ['is_admin'],
    }


def test_publish_log_entry__unknown_action_flag__no_event(
    fake_stream,
):

    # arrange
    staff = create_test_owner()
    client_account = create_test_account(name='Client')
    user = create_test_admin(account=client_account)

    # act
    LogEntry.objects.log_action(
        user_id=staff.id,
        content_type_id=ContentType.objects.get_for_model(
            model=UserModel,
        ).pk,
        object_id=user.id,
        object_repr=str(user),
        action_flag=4,
        change_message='',
    )

    # assert
    assert fake_stream.events == []


def test_publish_log_entry__admin_change_form__is_admin_in_changed_fields(
    fake_stream,
    client,
):

    """ The admin site writes the row itself: the change form of a
        user reaches the receiver with the message Django builds. """

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
    assert event.type == EventName.ADMIN_UPDATE
    assert event.category == EventCategory.AUDIT
    assert event.account_id == client_account.id
    assert event.actor == Actor(
        type=ActorType.USER,
        id=staff.id,
        email=staff.email,
    )
    assert event.object == EventObject(
        type=EventObjectType.USER,
        id=user.id,
    )
    assert event.payload == {
        'model': 'accounts.user',
        'changed_fields': ['is_admin'],
    }


def test_publish_log_entry__user_invite__no_object_id(fake_stream):

    """ The id of an invite is the key that accepts it: anybody who
        reads the journal could join the account with it. """

    # arrange
    staff = create_test_owner()
    client_account = create_test_account(name='Client')
    admin = create_test_admin(account=client_account)
    invited_user = create_invited_user(
        user=admin,
        email='invited@test.test',
    )
    invite = UserInvite.objects.get(invited_user=invited_user)

    # act
    LogEntry.objects.log_action(
        user_id=staff.id,
        content_type_id=ContentType.objects.get_for_model(
            model=UserInvite,
        ).pk,
        object_id=invite.id,
        object_repr='Invite',
        action_flag=CHANGE,
        change_message=json.dumps([{'changed': {'fields': ['status']}}]),
    )

    # assert
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    assert event.type == EventName.ADMIN_UPDATE
    assert event.account_id == client_account.id
    assert event.actor == Actor(
        type=ActorType.USER,
        id=staff.id,
        email=staff.email,
    )
    assert event.object == EventObject(
        type=EventObjectType.INVITE,
        id=None,
    )
    assert event.payload == {
        'model': 'accounts.userinvite',
        'changed_fields': ['status'],
    }


def test_publish_log_entry__logs_disabled__not_emitted(
    mocker,
    settings,
    django_assert_num_queries,
):

    """ With the journal off the receiver reads nothing: the content
        type, the edited row and the superuser each cost a query. """

    # arrange
    settings.LOGS_BACKEND = LogsBackend.NONE
    emit_mock = mocker.patch('src.logs.events.admin_site.emit')
    staff = create_test_owner()
    client_account = create_test_account(name='Client')
    user = create_test_admin(account=client_account)
    entry = LogEntry.objects.log_action(
        user_id=staff.id,
        content_type_id=ContentType.objects.get_for_model(
            model=UserModel,
        ).pk,
        object_id=user.id,
        object_repr=str(user),
        action_flag=CHANGE,
        change_message=json.dumps([{'changed': {'fields': ['is_admin']}}]),
    )

    # act
    with django_assert_num_queries(0):
        publish_log_entry(sender=LogEntry, instance=entry, created=True)

    # assert
    emit_mock.assert_not_called()
