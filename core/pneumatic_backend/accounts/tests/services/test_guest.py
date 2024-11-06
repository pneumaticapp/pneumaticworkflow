import pytest
import pytz
from django.conf import settings
from django.contrib.auth import get_user_model
from pneumatic_backend.accounts.enums import (
    UserType,
    UserStatus,
    Language,
    UserDateFormat,
    UserFirstDayWeek,
)
from pneumatic_backend.accounts.services.guests import (
    GuestService
)
from pneumatic_backend.processes.tests.fixtures import (
    create_test_account,
    create_test_user,
)

pytestmark = pytest.mark.django_db
UserModel = get_user_model()


class TestGuestsService:

    def test_create_ok(self):

        # arrange
        account = create_test_account()
        language = Language.de
        timezone = pytz.timezone('America/Anchorage')
        date_fmt = UserDateFormat.PY_EUROPE_24
        date_fdw = UserFirstDayWeek.THURSDAY
        account_owner = create_test_user(
            account=account,
            is_account_owner=True,
            email='owner@test.test',
            tz=timezone,
            language=language,
            date_fmt=date_fmt,
            date_fdw=date_fdw,
        )
        email = 'guest@test.test'

        # act
        user = GuestService.create(
            email=email,
            account_id=account.id
        )

        # assert
        assert user.email == email
        assert user.first_name == ''
        assert user.last_name == ''
        assert user.account_id == account.id
        assert user.type == UserType.GUEST
        assert user.status == UserStatus.ACTIVE
        assert user.is_admin is False
        assert user.is_account_owner is False
        assert user.notify_about_tasks is False
        assert user.is_digest_subscriber is False
        assert user.is_tasks_digest_subscriber is False
        assert user.is_special_offers_subscriber is False
        assert user.is_newsletters_subscriber is False
        assert user.is_new_tasks_subscriber is True
        assert user.is_complete_tasks_subscriber is True
        assert user.is_comments_mentions_subscriber is False
        assert user.password
        assert user.language == account_owner.language
        assert user.date_fmt == account_owner.date_fmt
        assert user.date_fdw == account_owner.date_fdw
        assert user.timezone == account_owner.timezone.__str__()

    def test_create__long_email__ok(self):

        # arrange
        account = create_test_account()
        create_test_user(
            account=account,
            is_account_owner=True,
            email='owner@test.test',
        )
        email_more_150_chars = (
            'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
            'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
            'aaaaaaaaaaaaaaaaaaaaaaaaaaaa@test.test'
        )
        # act
        user = GuestService.create(
            email=email_more_150_chars,
            account_id=account.id
        )

        # assert
        assert user.email == email_more_150_chars
        assert user.first_name == ''
        assert user.last_name == ''
        assert user.account_id == account.id
        assert user.type == UserType.GUEST
        assert user.status == UserStatus.ACTIVE
        assert user.is_admin is False
        assert user.is_account_owner is False
        assert user.notify_about_tasks is False
        assert user.is_digest_subscriber is False
        assert user.is_tasks_digest_subscriber is False
        assert user.is_special_offers_subscriber is False
        assert user.is_newsletters_subscriber is False
        assert user.is_new_tasks_subscriber is True
        assert user.is_complete_tasks_subscriber is True
        assert user.is_comments_mentions_subscriber is False
        assert user.password
        assert user.language == settings.LANGUAGE_CODE
        assert user.timezone == settings.TIME_ZONE

    def test_create__exist_inactive__ok(self):

        # arrange
        account = create_test_account()
        create_test_user(
            account=account,
            is_account_owner=True,
            email='owner@test.test',
        )
        email = 'guest@test.test'
        inactive_guest = UserModel(
            account_id=account.id,
            email=email,
            type=UserType.GUEST,
            status=UserStatus.INACTIVE,
        )

        # act
        user = GuestService.create(
            email=email,
            account_id=account.id
        )

        # assert
        assert user.email == inactive_guest.email
        assert user.id != inactive_guest.id

    def test_create__account_user_exist__ok(self):
        # arrange
        account = create_test_account()
        create_test_user(
            account=account,
            is_account_owner=True,
            email='owner@test.test',
        )
        email = 'guest@test.test'
        account_user = UserModel(
            account_id=account.id,
            email=email,
            type=UserType.USER,
            status=UserStatus.ACTIVE,
        )

        # act
        user = GuestService.create(
            email=email,
            account_id=account.id
        )

        # assert
        assert user.email == account_user.email
        assert user.id != account_user.id

    def test_get_or_create__get__ok(self):

        # arrange
        account = create_test_account()
        email = 'guest@test.test'
        guest = UserModel(
            account_id=account.id,
            email=email,
            type=UserType.GUEST,
            status=UserStatus.ACTIVE,
        )
        guest.set_unusable_password()
        guest.save()

        # act
        user = GuestService.get_or_create(
            email=email,
            account_id=account.id
        )

        # assert
        assert user.id == guest.id

    def test_get_or_create__account_user_exists__create_guest(self, mocker):

        # arrange
        account = create_test_account()
        email = 'guest@test.test'
        UserModel.objects.create(
            account_id=account.id,
            email=email,
            type=UserType.USER,
            status=UserStatus.ACTIVE,
            password='123'
        )

        create_guest_mock = mocker.patch(
            'pneumatic_backend.accounts.services.guests'
            '.GuestService.create'
        )

        # act
        GuestService.get_or_create(
            email=email,
            account_id=account.id
        )

        # assert
        create_guest_mock.assert_called_once_with(
            account_id=account.id,
            email=email
        )

    def test_get_or_create__guest_inactive__create_guest(self, mocker):

        # arrange
        account = create_test_account()
        email = 'guest@test.test'
        UserModel.objects.create(
            account_id=account.id,
            email=email,
            type=UserType.GUEST,
            status=UserStatus.INACTIVE,
            password='123'
        )
        create_guest_mock = mocker.patch(
            'pneumatic_backend.accounts.services.guests'
            '.GuestService.create'
        )

        # act
        GuestService.get_or_create(
            email=email,
            account_id=account.id
        )

        # assert
        create_guest_mock.assert_called_once_with(
            account_id=account.id,
            email=email
        )

    def test_get_or_create__guest_exists__not_create(self, mocker):

        # arrange
        account = create_test_account()
        email = 'guest@test.test'
        guest = UserModel.objects.create(
            account_id=account.id,
            email=email,
            type=UserType.GUEST,
            status=UserStatus.ACTIVE,
            password='123'
        )
        create_guest_mock = mocker.patch(
            'pneumatic_backend.accounts.services.guests'
            '.GuestService.create'
        )

        # act
        user = GuestService.get_or_create(
            email=email,
            account_id=account.id
        )

        # assert
        create_guest_mock.assert_not_called()
        assert user.id == guest.id
