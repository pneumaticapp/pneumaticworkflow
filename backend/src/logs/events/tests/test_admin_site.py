import json

import pytest
from django import forms
from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.contrib.admin.models import (
    ADDITION,
    CHANGE,
    DELETION,
    LogEntry,
)
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.forms import MultiWidget, inlineformset_factory, modelform_factory
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
    UserEvents,
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


def test_log_change__form_data__admin_update_event(
    fake_stream,
    request_factory,
):

    """ The admin site builds its message from the form right before
        the hook: the record carries what the form cleaned. """

    # arrange
    staff = create_test_owner()
    client_account = create_test_account(name='Client')
    user = create_test_admin(account=client_account)
    request = request_factory.get('/')
    request.user = staff
    users_admin = UsersAdmin(UserModel, admin.site)
    form_class = modelform_factory(
        UserModel,
        fields=('first_name', 'is_admin'),
    )
    form = form_class(instance=user, data={'first_name': 'Ann'})
    form.is_valid()
    message = users_admin.construct_change_message(request, form, None)

    # act
    entry = users_admin.log_change(
        request=request,
        instance=user,
        message=message,
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
        'data': {'first_name': 'Ann', 'is_admin': False},
    }
    assert event.auth_type is None


def test_log_change__many_to_many_field__ids(
    fake_stream,
    request_factory,
):

    # arrange
    staff = create_test_owner()
    client_account = create_test_account(name='Client')
    user = create_test_admin(account=client_account)
    group = create_test_group(account=client_account)
    request = request_factory.get('/')
    request.user = staff
    group_admin = GroupAdmin(UserGroup, admin.site)
    form_class = modelform_factory(UserGroup, fields=('name', 'users'))
    form = form_class(
        instance=group,
        data={'name': 'Sales', 'users': [user.id]},
    )
    form.is_valid()
    message = group_admin.construct_change_message(request, form, None)

    # act
    group_admin.log_change(
        request=request,
        instance=group,
        message=message,
    )

    # assert
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    assert event.type == AdminEvents.UPDATE
    assert event.object == EventObject(
        type=EventObjectType.GROUP,
        id=group.id,
    )
    assert event.payload == {
        'model': 'accounts.usergroup',
        'data': {'name': 'Sales', 'users': f'[{user.id}]'},
    }


def test_log_change__uploaded_file__file_name(
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
    form_class = type(
        'PhotoForm',
        (forms.Form,),
        {'photo_file': forms.FileField()},
    )
    form = form_class(
        data={},
        files={'photo_file': SimpleUploadedFile('ann.png', b'image')},
    )
    form.is_valid()
    message = users_admin.construct_change_message(request, form, None)

    # act
    users_admin.log_change(
        request=request,
        instance=user,
        message=message,
    )

    # assert
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    assert event.payload == {
        'model': 'accounts.user',
        'data': {'photo_file': 'ann.png'},
    }


def test_log_change__inline_rows__only_written_rows(
    fake_stream,
    request_factory,
):

    """ The admin site saves an inline row only when its form has
        changed: the rows left as they were are not in the record. """

    # arrange
    staff = create_test_owner()
    client_account = create_test_account(name='Client')
    user_1 = create_test_admin(
        account=client_account,
        email='first@test.test',
    )
    user_2 = create_test_admin(
        account=client_account,
        email='second@test.test',
    )
    request = request_factory.get('/')
    request.user = staff
    account_admin = AccountAdmin(Account, admin.site)
    form_class = modelform_factory(Account, fields=('name',))
    form = form_class(instance=client_account, data={'name': 'Client'})
    form.is_valid()
    formset_class = inlineformset_factory(
        Account,
        UserModel,
        fields=('first_name',),
        extra=0,
    )
    formset = formset_class(
        instance=client_account,
        queryset=UserModel.objects.filter(
            id__in=[user_1.id, user_2.id],
        ).order_by('id'),
        data={
            'users-TOTAL_FORMS': '2',
            'users-INITIAL_FORMS': '2',
            'users-0-id': str(user_1.id),
            'users-0-first_name': 'Renamed',
            'users-1-id': str(user_2.id),
            'users-1-first_name': user_2.first_name,
        },
    )
    formset.is_valid()
    formset.save()
    message = account_admin.construct_change_message(
        request,
        form,
        [formset],
    )

    # act
    account_admin.log_change(
        request=request,
        instance=client_account,
        message=message,
    )

    # assert
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    assert event.type == AdminEvents.UPDATE
    assert set(event.payload) == {'model', 'data', 'inlines'}
    assert event.payload['model'] == 'accounts.account'
    assert event.payload['data'] == {'name': 'Client'}
    assert set(event.payload['inlines']) == {'accounts.user'}
    assert json.loads(event.payload['inlines']['accounts.user']) == [
        {
            'first_name': 'Renamed',
            'id': user_1.id,
            'account': client_account.id,
            'DELETE': False,
        },
    ]


def test_log_change__inline_rows_unchanged__no_inlines_key(
    fake_stream,
    request_factory,
):

    """ No inline row was written: the record has no inlines at all
        rather than an empty list per inline. """

    # arrange
    staff = create_test_owner()
    client_account = create_test_account(name='Client')
    user = create_test_admin(account=client_account)
    request = request_factory.get('/')
    request.user = staff
    account_admin = AccountAdmin(Account, admin.site)
    form_class = modelform_factory(Account, fields=('name',))
    form = form_class(instance=client_account, data={'name': 'Client'})
    form.is_valid()
    formset_class = inlineformset_factory(
        Account,
        UserModel,
        fields=('first_name',),
        extra=0,
    )
    formset = formset_class(
        instance=client_account,
        queryset=UserModel.objects.filter(id=user.id),
        data={
            'users-TOTAL_FORMS': '1',
            'users-INITIAL_FORMS': '1',
            'users-0-id': str(user.id),
            'users-0-first_name': user.first_name,
        },
    )
    formset.is_valid()
    formset.save()
    message = account_admin.construct_change_message(
        request,
        form,
        [formset],
    )

    # act
    account_admin.log_change(
        request=request,
        instance=client_account,
        message=message,
    )

    # assert
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    assert event.type == AdminEvents.UPDATE
    assert event.payload == {
        'model': 'accounts.account',
        'data': {'name': 'Client'},
    }


def test_log_change__logs_disabled__form_data_not_collected(
    mocker,
    request_factory,
):

    """ With the journal off the form is not read: the ids of a
        many-to-many field and the inline rows would cost a query
        each, for a payload nobody writes. """

    # arrange
    staff = create_test_owner()
    client_account = create_test_account(name='Client')
    user = create_test_admin(account=client_account)
    group = create_test_group(account=client_account)
    request = request_factory.get('/')
    request.user = staff
    group_admin = GroupAdmin(UserGroup, admin.site)
    form_class = modelform_factory(UserGroup, fields=('name', 'users'))
    form = form_class(
        instance=group,
        data={'name': 'Sales', 'users': [user.id]},
    )
    form.is_valid()
    message = group_admin.construct_change_message(request, form, None)
    admin_updated_mock = mocker.patch(
        'src.logs.events.admin_site.AuditEventService.admin_updated',
    )

    # act
    group_admin.log_change(
        request=request,
        instance=group,
        message=message,
    )

    # assert
    admin_updated_mock.assert_called_once_with(
        user=staff,
        target=group,
        model='accounts.usergroup',
        form_data=None,
        is_password_set=False,
    )


def test_log_addition__logs_disabled__form_data_not_collected(
    mocker,
    request_factory,
):

    # arrange
    staff = create_test_owner()
    client_account = create_test_account(name='Client')
    group = create_test_group(account=client_account)
    request = request_factory.get('/')
    request.user = staff
    group_admin = GroupAdmin(UserGroup, admin.site)
    form_class = modelform_factory(UserGroup, fields=('name',))
    form = form_class(instance=group, data={'name': 'Sales'})
    form.is_valid()
    message = group_admin.construct_change_message(
        request,
        form,
        None,
        add=True,
    )
    admin_created_mock = mocker.patch(
        'src.logs.events.admin_site.AuditEventService.admin_created',
    )

    # act
    group_admin.log_addition(
        request=request,
        instance=group,
        message=message,
    )

    # assert
    admin_created_mock.assert_called_once_with(
        user=staff,
        target=group,
        model='accounts.usergroup',
        form_data=None,
    )


def test_log_change__no_form__model_only(
    fake_stream,
    request_factory,
):

    """ A hook the admin site calls without building a message from a
        form (a custom action) has nothing but the row to name. """

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
    assert event.object == EventObject(
        type=EventObjectType.USER,
        id=user.id,
    )
    assert event.payload == {'model': 'accounts.user'}


def test_log_change__next_row_without_form__data_not_carried_over(
    fake_stream,
    request_factory,
):

    """ The rows of the changelist are saved on one request: the data
        of a form goes into the record of its own row only. """

    # arrange
    staff = create_test_owner()
    client_account = create_test_account(name='Client')
    user_1 = create_test_admin(
        account=client_account,
        email='first@test.test',
    )
    user_2 = create_test_admin(
        account=client_account,
        email='second@test.test',
    )
    request = request_factory.get('/')
    request.user = staff
    users_admin = UsersAdmin(UserModel, admin.site)
    form_class = modelform_factory(UserModel, fields=('first_name',))
    form = form_class(instance=user_1, data={'first_name': 'Ann'})
    form.is_valid()
    message = users_admin.construct_change_message(request, form, None)
    users_admin.log_change(
        request=request,
        instance=user_1,
        message=message,
    )

    # act
    users_admin.log_change(
        request=request,
        instance=user_2,
        message='Changed first_name.',
    )

    # assert
    assert len(fake_stream.events) == 2
    assert fake_stream.events[0][1].payload == {
        'model': 'accounts.user',
        'data': {'first_name': 'Ann'},
    }
    assert fake_stream.events[1][1].payload == {'model': 'accounts.user'}


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
    assert event.payload == {'model': 'accounts.userinvite'}


def test_log_change__logs_disabled__entry_written_no_event(
    mocker,
    request_factory,
    run_on_commit,
):

    """ LOGS_BACKEND is not set in tests: the admin site still keeps
        its own history, the journal is not reached. """

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


def test_log_change__admin_change_form__form_data_without_password(
    fake_stream,
    client,
):

    """ The admin site writes the row itself: the change form of a
        user reaches the hook with the data it cleaned, the hash of
        the password left out. """

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
    assert set(event.payload) == {'model', 'data'}
    assert event.payload['model'] == 'accounts.user'
    assert event.payload['data']['is_admin'] is False
    assert event.payload['data']['email'] == user.email
    assert 'password' not in event.payload['data']


def test_log_addition__admin_add_user_form__created_user_named(
    fake_stream,
    client,
):

    """ The add form of a user signs up a new account: the addition
        names the owner the sign up created, in the account of that
        owner, not an unsaved row in the account of the superuser. The
        password typed into the form is not in the record. """

    # arrange
    staff = create_test_owner()
    staff.is_superuser = True
    staff.save(update_fields=['is_superuser'])
    client.force_login(user=staff)
    url = reverse(viewname='admin:accounts_user_add')
    page = client.get(path=url)
    data = {
        'email': 'new@client.test',
        'first_name': 'New',
        'last_name': 'Client',
        'language': 'en',
        'timezone': 'UTC',
        'password1': 'Qwerty-12345!',
        'password2': 'Qwerty-12345!',
    }
    for inline in page.context['inline_admin_formsets']:
        management_form = inline.formset.management_form
        for name, value in management_form.initial.items():
            data[management_form.add_prefix(name)] = value

    # act
    response = client.post(path=url, data=data)

    # assert
    owner = UserModel.objects.get(email='new@client.test')
    assert response.status_code == 302
    assert response['Location'] == reverse(
        viewname='admin:accounts_user_change',
        args=[owner.id],
    )
    assert LogEntry.objects.get(action_flag=ADDITION).object_id == str(
        owner.id,
    )
    assert len(fake_stream.events) == 2
    assert fake_stream.events[0][1].type == UserEvents.SIGNUP
    event = fake_stream.events[1][1]
    assert event.type == AdminEvents.CREATE
    assert event.category == EventCategory.ADMIN
    assert event.account_id == owner.account_id
    assert event.actor == Actor(
        id=staff.id,
        email=staff.email,
        user_type=UserType.USER,
    )
    assert event.object == EventObject(
        type=EventObjectType.USER,
        id=owner.id,
    )
    assert set(event.payload) == {'model', 'data'}
    assert event.payload['model'] == 'accounts.user'
    assert event.payload['data']['email'] == 'new@client.test'
    assert event.payload['data']['first_name'] == 'New'
    assert 'password1' not in event.payload['data']
    assert 'password2' not in event.payload['data']
    assert 'Qwerty-12345!' not in json.dumps(event.to_dict())


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


def test_log_change__admin_password_form__password_set_event(
    fake_stream,
    client,
):

    """ The password form of a user leaves the change of the row and
        user.password_set, the record an alert watches; the password
        itself is in neither. """

    # arrange
    staff = create_test_owner()
    staff.is_superuser = True
    staff.save(update_fields=['is_superuser'])
    client_account = create_test_account(name='Client')
    user = create_test_admin(account=client_account)
    client.force_login(user=staff)
    url = reverse(
        viewname='admin:auth_user_password_change',
        args=[user.id],
    )
    data = {
        'password1': 'Qwerty-12345!',
        'password2': 'Qwerty-12345!',
    }

    # act
    response = client.post(path=url, data=data)

    # assert
    assert response.status_code == 302
    user.refresh_from_db()
    assert user.check_password('Qwerty-12345!')
    assert len(fake_stream.events) == 2
    admin_event = fake_stream.events[0][1]
    assert admin_event.type == AdminEvents.UPDATE
    assert admin_event.account_id == client_account.id
    assert admin_event.object == EventObject(
        type=EventObjectType.USER,
        id=user.id,
    )
    assert admin_event.payload == {'model': 'accounts.user', 'data': {}}
    password_event = fake_stream.events[1][1]
    assert password_event.type == UserEvents.PASSWORD_SET
    assert password_event.account_id == client_account.id
    assert password_event.actor == Actor(
        id=staff.id,
        email=staff.email,
        user_type=UserType.USER,
    )
    assert password_event.auth_type is None
    assert password_event.object == EventObject(
        type=EventObjectType.USER,
        id=user.id,
    )
    assert password_event.payload == {'target_email': user.email}
    assert 'Qwerty-12345!' not in json.dumps(admin_event.to_dict())
    assert 'Qwerty-12345!' not in json.dumps(password_event.to_dict())
