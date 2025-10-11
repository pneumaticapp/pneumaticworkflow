import pytest
from src.accounts.enums import UserStatus
from src.accounts.models import (
    AccountSignupData,
)
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_user,
    create_invited_user,
    create_test_guest,
    create_test_group,
)
from src.analytics.tasks import (
    _identify_users,
    track_group_analytics,
)
from src.analytics.events import GroupsAnalyticsEvent
from src.authentication.enums import AuthTokenType


pytestmark = pytest.mark.django_db


def test_identify_users__ok(identify_mock):

    # arrange
    account = create_test_account()
    AccountSignupData.objects.create(account=account)
    user = create_test_user(account=account)
    invited_user = create_invited_user(
        user=user,
        email='invited@t.t',
    )
    inactive_user = create_test_user(
        account=account,
        status=UserStatus.INACTIVE,
    )
    guest = create_test_guest(account=account)

    # act
    _identify_users(user_ids=[
        user.id, invited_user.id, inactive_user.id, guest.id,
    ])

    # assert
    identify_mock.assert_called_once_with(user)


def test_track_group_analytics__create_group_all_fields__ok(
    mocker,
):
    # arrange
    user = create_test_user()
    group = create_test_group(user.account)
    is_superuser = False
    photo = 'photo.jpg'
    analytics_service_mock = mocker.patch(
        'src.analytics.tasks.AnalyticService',
    )

    # act
    track_group_analytics(
        event=GroupsAnalyticsEvent.created,
        user_id=user.id,
        user_email=user.email,
        user_first_name=user.first_name,
        user_last_name=user.last_name,
        group_photo=group.photo,
        group_users=[user.id],
        account_id=user.account.id,
        group_id=group.id,
        group_name=group.name,
        auth_type=AuthTokenType.USER,
        is_superuser=is_superuser,
        new_users_ids=[user.id],
        new_photo=photo,
    )

    # assert
    analytics_service_mock.groups_created.assert_called_once_with(
        text=f"{group.name} (id: {group.id}).",
        user_id=user.id,
        user_email=user.email,
        user_first_name=user.first_name,
        user_last_name=user.last_name,
        group_photo=group.photo,
        group_users=[user.id],
        account_id=user.account.id,
        group_id=group.id,
        group_name=group.name,
        auth_type=AuthTokenType.USER,
        is_superuser=is_superuser,
    )
    assert analytics_service_mock.groups_updated.call_count == 2
    analytics_service_mock.groups_updated.assert_has_calls([
        mocker.call(
            text=(
                f"{group.name} (id: {group.id}). "
                f"Added group photo (url: {photo})."
            ),
            user_id=user.id,
            user_email=user.email,
            user_first_name=user.first_name,
            user_last_name=user.last_name,
            group_photo=group.photo,
            group_users=[user.id],
            account_id=user.account.id,
            group_id=group.id,
            group_name=group.name,
            auth_type=AuthTokenType.USER,
            is_superuser=is_superuser,
        ),
        mocker.call(
            text=f"{group.name} (id: {group.id}). Added user: {user.email}.",
            user_id=user.id,
            user_email=user.email,
            user_first_name=user.first_name,
            user_last_name=user.last_name,
            group_photo=group.photo,
            group_users=[user.id],
            account_id=user.account.id,
            group_id=group.id,
            group_name=group.name,
            auth_type=AuthTokenType.USER,
            is_superuser=is_superuser,
        ),
    ])


def test_track_group_analytics__create_group_required_fields__ok(mocker):
    # arrange
    user = create_test_user()
    group = create_test_group(user.account)
    is_superuser = False

    analytics_service_mock = mocker.patch(
        'src.analytics.tasks.AnalyticService',
    )

    # act
    track_group_analytics(
        event=GroupsAnalyticsEvent.created,
        user_id=user.id,
        user_email=user.email,
        user_first_name=user.first_name,
        user_last_name=user.last_name,
        group_photo=group.photo,
        group_users=group.users,
        account_id=user.account.id,
        group_id=group.id,
        group_name=group.name,
        auth_type=AuthTokenType.USER,
        is_superuser=is_superuser,
    )

    # assert
    analytics_service_mock.groups_created.assert_called_once_with(
        text=f"{group.name} (id: {group.id}).",
        user_id=user.id,
        user_email=user.email,
        user_first_name=user.first_name,
        user_last_name=user.last_name,
        group_photo=group.photo,
        group_users=group.users,
        account_id=user.account.id,
        group_id=group.id,
        group_name=group.name,
        auth_type=AuthTokenType.USER,
        is_superuser=is_superuser,
    )


def test_track_group_analytics__create_group_with_photo__ok(mocker):
    # arrange
    user = create_test_user()
    group = create_test_group(user.account)
    is_superuser = False
    photo = 'photo.jpg'
    analytics_service_mock = mocker.patch(
        'src.analytics.tasks.AnalyticService',
    )

    # act
    track_group_analytics(
        event=GroupsAnalyticsEvent.created,
        user_id=user.id,
        user_email=user.email,
        user_first_name=user.first_name,
        user_last_name=user.last_name,
        group_photo=group.photo,
        group_users=[user.id],
        account_id=user.account.id,
        group_id=group.id,
        group_name=group.name,
        auth_type=AuthTokenType.USER,
        is_superuser=is_superuser,
        new_photo=photo,
    )

    # assert
    analytics_service_mock.groups_created.assert_called_once_with(
        text=f"{group.name} (id: {group.id}).",
        user_id=user.id,
        user_email=user.email,
        user_first_name=user.first_name,
        user_last_name=user.last_name,
        group_photo=group.photo,
        group_users=[user.id],
        account_id=user.account.id,
        group_id=group.id,
        group_name=group.name,
        auth_type=AuthTokenType.USER,
        is_superuser=is_superuser,
    )
    analytics_service_mock.groups_updated.assert_called_once_with(
        text=(
            f"{group.name} (id: {group.id}). Added group photo (url: {photo})."
        ),
        user_id=user.id,
        user_email=user.email,
        user_first_name=user.first_name,
        user_last_name=user.last_name,
        group_photo=group.photo,
        group_users=[user.id],
        account_id=user.account.id,
        group_id=group.id,
        group_name=group.name,
        auth_type=AuthTokenType.USER,
        is_superuser=is_superuser,
    )


def test_track_group_analytics__create_group_with_user__ok(
    mocker,
):
    # arrange
    user = create_test_user()
    group = create_test_group(user.account)
    is_superuser = False
    analytics_service_mock = mocker.patch(
        'src.analytics.tasks.AnalyticService',
    )

    # act
    track_group_analytics(
        event=GroupsAnalyticsEvent.created,
        user_id=user.id,
        user_email=user.email,
        user_first_name=user.first_name,
        user_last_name=user.last_name,
        group_photo=group.photo,
        group_users=[user.id],
        account_id=user.account.id,
        group_id=group.id,
        group_name=group.name,
        auth_type=AuthTokenType.USER,
        is_superuser=is_superuser,
        new_users_ids=[user.id],
    )

    # assert
    analytics_service_mock.groups_created.assert_called_once_with(
        text=f"{group.name} (id: {group.id}).",
        user_id=user.id,
        user_email=user.email,
        user_first_name=user.first_name,
        user_last_name=user.last_name,
        group_photo=group.photo,
        group_users=[user.id],
        account_id=user.account.id,
        group_id=group.id,
        group_name=group.name,
        auth_type=AuthTokenType.USER,
        is_superuser=is_superuser,
    )
    analytics_service_mock.groups_updated.assert_called_once_with(
        text=f"{group.name} (id: {group.id}). Added user: {user.email}.",
        user_id=user.id,
        user_email=user.email,
        user_first_name=user.first_name,
        user_last_name=user.last_name,
        group_photo=group.photo,
        group_users=[user.id],
        account_id=user.account.id,
        group_id=group.id,
        group_name=group.name,
        auth_type=AuthTokenType.USER,
        is_superuser=is_superuser,
    )


def test_track_group_analytics__update_group_name__ok(mocker):
    # arrange
    user = create_test_user()
    group = create_test_group(user.account)
    is_superuser = False
    new_name = "New Group Name"
    analytics_service_mock = mocker.patch(
        'src.analytics.tasks.AnalyticService',
    )

    # act
    track_group_analytics(
        event=GroupsAnalyticsEvent.updated,
        user_id=user.id,
        user_email=user.email,
        user_first_name=user.first_name,
        user_last_name=user.last_name,
        group_photo=group.photo,
        group_users=group.users,
        account_id=user.account.id,
        group_id=group.id,
        group_name=group.name,
        auth_type=AuthTokenType.USER,
        is_superuser=is_superuser,
        new_name=new_name,
    )

    # assert
    analytics_service_mock.groups_updated.assert_called_once_with(
        text=(
            f'{group.name} (id: {group.id}). '
            f'Changed the group name to "{new_name}".'
        ),
        user_id=user.id,
        user_email=user.email,
        user_first_name=user.first_name,
        user_last_name=user.last_name,
        group_photo=group.photo,
        group_users=group.users,
        account_id=user.account.id,
        group_id=group.id,
        group_name=group.name,
        auth_type=AuthTokenType.USER,
        is_superuser=is_superuser,
    )


def test_track_group_analytics__update_group_photo__ok(mocker):
    # arrange
    user = create_test_user()
    group = create_test_group(user.account)
    is_superuser = False
    new_photo = 'photo.jpg'
    analytics_service_mock = mocker.patch(
        'src.analytics.tasks.AnalyticService',
    )

    # act
    track_group_analytics(
        event=GroupsAnalyticsEvent.updated,
        user_id=user.id,
        user_email=user.email,
        user_first_name=user.first_name,
        user_last_name=user.last_name,
        group_photo=new_photo,
        group_users=group.users,
        account_id=user.account.id,
        group_id=group.id,
        group_name=group.name,
        auth_type=AuthTokenType.USER,
        is_superuser=is_superuser,
        new_photo=new_photo,
    )

    # assert
    analytics_service_mock.groups_updated.assert_called_once_with(
        text=(
            f'{group.name} (id: {group.id}). '
            f'Added group photo (url: {new_photo}).'
        ),
        user_id=user.id,
        user_email=user.email,
        user_first_name=user.first_name,
        user_last_name=user.last_name,
        group_photo=new_photo,
        group_users=group.users,
        account_id=user.account.id,
        group_id=group.id,
        group_name=group.name,
        auth_type=AuthTokenType.USER,
        is_superuser=is_superuser,
    )


def test_track_group_analytics__delete_group_photo__ok(mocker):
    # arrange
    user = create_test_user()
    group = create_test_group(user.account, photo='url')
    is_superuser = False
    analytics_service_mock = mocker.patch(
        'src.analytics.tasks.AnalyticService',
    )
    delete_photo = ''

    # act
    track_group_analytics(
        event=GroupsAnalyticsEvent.updated,
        user_id=user.id,
        user_email=user.email,
        user_first_name=user.first_name,
        user_last_name=user.last_name,
        group_photo=delete_photo,
        group_users=group.users,
        account_id=user.account.id,
        group_id=group.id,
        group_name=group.name,
        auth_type=AuthTokenType.USER,
        is_superuser=is_superuser,
        new_photo=delete_photo,
    )

    # assert
    analytics_service_mock.groups_updated.assert_called_once_with(
        text=(
            f'{group.name} (id: {group.id}). '
            f'Delete group photo.'
        ),
        user_id=user.id,
        user_email=user.email,
        user_first_name=user.first_name,
        user_last_name=user.last_name,
        group_photo=delete_photo,
        group_users=group.users,
        account_id=user.account.id,
        group_id=group.id,
        group_name=group.name,
        auth_type=AuthTokenType.USER,
        is_superuser=is_superuser,
    )


def test_track_group_analytics__update_group_add_users__ok(mocker):
    # arrange
    user = create_test_user()
    group = create_test_group(user.account)
    is_superuser = False
    new_users_ids = [user.id]

    analytics_service_mock = mocker.patch(
        'src.analytics.tasks.AnalyticService',
    )

    # act
    track_group_analytics(
        event=GroupsAnalyticsEvent.updated,
        user_id=user.id,
        user_email=user.email,
        user_first_name=user.first_name,
        user_last_name=user.last_name,
        group_photo=group.photo,
        group_users=new_users_ids,
        account_id=user.account.id,
        group_id=group.id,
        group_name=group.name,
        auth_type=AuthTokenType.USER,
        is_superuser=is_superuser,
        new_users_ids=new_users_ids,
    )

    # assert
    analytics_service_mock.groups_updated.assert_called_once_with(
        text=f"{group.name} (id: {group.id}). Added user: {user.email}.",
        user_id=user.id,
        user_email=user.email,
        user_first_name=user.first_name,
        user_last_name=user.last_name,
        group_photo=group.photo,
        group_users=new_users_ids,
        account_id=user.account.id,
        group_id=group.id,
        group_name=group.name,
        auth_type=AuthTokenType.USER,
        is_superuser=is_superuser,
    )


def test_track_group_analytics__remove_users__ok(mocker):
    # arrange
    user = create_test_user()
    group = create_test_group(user.account)
    is_superuser = False
    removed_users_ids = [user.id]

    analytics_service_mock = mocker.patch(
        'src.analytics.tasks.AnalyticService',
    )

    # act
    track_group_analytics(
        event=GroupsAnalyticsEvent.updated,
        user_id=user.id,
        user_email=user.email,
        user_first_name=user.first_name,
        user_last_name=user.last_name,
        group_photo=group.photo,
        group_users=[],
        account_id=user.account.id,
        group_id=group.id,
        group_name=group.name,
        auth_type=AuthTokenType.USER,
        is_superuser=is_superuser,
        removed_users_ids=removed_users_ids,
    )

    # assert
    analytics_service_mock.groups_updated.assert_called_once_with(
        text=f"{group.name} (id: {group.id}). Remove user: {user.email}.",
        user_id=user.id,
        user_email=user.email,
        user_first_name=user.first_name,
        user_last_name=user.last_name,
        group_photo=group.photo,
        group_users=[],
        account_id=user.account.id,
        group_id=group.id,
        group_name=group.name,
        auth_type=AuthTokenType.USER,
        is_superuser=is_superuser,
    )


def test_track_group_analytics__delete_group__ok(mocker):
    # arrange
    user = create_test_user()
    group = create_test_group(user.account)
    is_superuser = False
    analytics_service_mock = mocker.patch(
        'src.analytics.tasks.AnalyticService',
    )

    # act
    track_group_analytics(
        event=GroupsAnalyticsEvent.deleted,
        user_id=user.id,
        user_email=user.email,
        user_first_name=user.first_name,
        user_last_name=user.last_name,
        group_photo=group.photo,
        group_users=group.users,
        account_id=user.account.id,
        group_id=group.id,
        group_name=group.name,
        auth_type=AuthTokenType.USER,
        is_superuser=is_superuser,
    )

    # assert
    analytics_service_mock.groups_deleted.assert_called_once_with(
        text=f"{group.name} (id: {group.id}).",
        user_id=user.id,
        user_email=user.email,
        user_first_name=user.first_name,
        user_last_name=user.last_name,
        group_photo=group.photo,
        group_users=group.users,
        account_id=user.account.id,
        group_id=group.id,
        group_name=group.name,
        auth_type=AuthTokenType.USER,
        is_superuser=is_superuser,
    )
