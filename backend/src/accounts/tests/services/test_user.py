import pytest
from django.contrib.auth.hashers import check_password

from src.accounts.enums import (
    Language,
    LeaseLevel,
    SourceType,
    UserDateFormat,
    UserFirstDayWeek,
    UserStatus,
)
from src.accounts import messages
from src.accounts.models import (
    APIKey,
    Contact,
    UserInvite,
)
from src.accounts.serializers.user import UserWebsocketSerializer
from src.accounts.services.exceptions import (
    AlreadyRegisteredException,
    UserIsPerformerException,
    UserServiceException,
    PreventSelfDeletion,
    PreventAccountOwnerDeletion,
)
from src.accounts.services.user import UserService
from src.authentication.enums import AuthTokenType
from src.payment.stripe.exceptions import StripeServiceException
from src.payment.stripe.service import StripeService
from src.processes.enums import FieldType
from src.processes.models.workflows.fields import TaskField
from src.processes.tests.fixtures import (
    create_invited_user,
    create_test_account,
    create_test_guest,
    create_test_user,
    create_test_owner,
    create_test_admin,
    create_test_not_admin,
    create_test_workflow,
    create_test_group,
)

pytestmark = pytest.mark.django_db


def test_create_instance__all_fields__ok(mocker):
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    status = UserStatus.INVITED
    email = 'test@test.test'
    first_name = 'some first'
    last_name = 'some last'
    photo = 'https://test.test/photo.jpg'
    phone = '+79541231212'
    raw_password = '213123'
    is_admin = False
    is_account_owner = True
    language = Language.fr
    tz = 'Atlantic/Faeroe'
    date_fmt = UserDateFormat.PY_EUROPE_24
    date_fdw = UserFirstDayWeek.FRIDAY

    safe_password = 'some safe password'
    make_password_mock = mocker.patch(
        'src.accounts.services.user.make_password',
        return_value=safe_password,
    )
    service = UserService(user=owner)

    # act
    user = service._create_instance(
        account=account,
        email=email,
        first_name=first_name,
        last_name=last_name,
        raw_password=raw_password,
        photo=photo,
        phone=phone,
        is_admin=is_admin,
        is_account_owner=is_account_owner,
        status=status,
        language=language,
        timezone=tz,
        date_fmt=date_fmt,
        date_fdw=date_fdw,
    )

    # assert
    assert user.account == account
    assert user.timezone == tz
    assert user.language == language
    assert user.email == email
    assert user.phone == phone
    assert user.status == status
    assert user.first_name == first_name
    assert user.last_name == last_name
    assert user.photo == photo
    assert user.password == safe_password
    assert user.is_admin == is_admin
    assert user.is_account_owner == is_account_owner
    assert user.date_fmt == UserDateFormat.PY_EUROPE_24
    assert user.date_fdw == UserFirstDayWeek.FRIDAY
    assert user.password == safe_password
    make_password_mock.assert_called_once_with(raw_password)


def test_create_instance__only_required_fields__set_defaults(mocker):
    # arrange
    language = Language.fr
    tz = 'Atlantic/Faeroe'
    date_fmt = UserDateFormat.PY_EUROPE_24
    date_fdw = UserFirstDayWeek.SATURDAY
    account = create_test_account()
    create_test_user(
        account=account,
        is_account_owner=True,
        language=language,
        tz=tz,
        date_fmt=date_fmt,
        date_fdw=date_fdw,
    )
    email = 'test@test.test'
    random_password = '12123'
    random_password_mock = mocker.patch(
        'src.accounts.services.user.UserModel.objects.make_random_password',
        return_value=random_password,
    )
    safe_password = 'some safe password'
    make_password_mock = mocker.patch(
        'src.accounts.services.user.make_password',
        return_value=safe_password,
    )
    service = UserService()

    # act
    user = service._create_instance(
        account=account,
        email=email,
    )

    # assert
    assert user.account == account
    assert user.email == email
    assert user.status == UserStatus.ACTIVE
    assert user.first_name == ''
    assert user.last_name == ''
    assert user.photo is None
    assert user.phone is None
    assert user.password == safe_password
    assert user.is_admin is True
    assert user.is_account_owner is False
    assert user.language == language
    assert user.timezone == tz
    assert user.date_fmt == UserDateFormat.PY_EUROPE_24
    assert user.date_fdw == UserFirstDayWeek.SATURDAY
    random_password_mock.assert_called_once()
    make_password_mock.assert_called_once_with(random_password)


def test_create_instance__first_account_owner__is_superuser(mocker):
    # arrange
    account = create_test_account()
    email = 'test@test.com'
    random_password = '12123'
    random_password_mock = mocker.patch(
        'src.accounts.services.user.UserModel.objects.make_random_password',
        return_value=random_password,
    )
    safe_password = 'some safe password'
    make_password_mock = mocker.patch(
        'src.accounts.services.user.make_password',
        return_value=safe_password,
    )
    service = UserService()

    # act
    user = service._create_instance(
        account=account,
        email=email,
        is_account_owner=True,
    )

    # assert
    assert user.account == account
    assert user.email == email
    assert user.is_superuser is True
    assert user.is_staff is True
    random_password_mock.assert_called_once()
    make_password_mock.assert_called_once_with(random_password)


def test_create_instance__not_first_account_owner__is_not_superuser(mocker):
    # arrange
    account = create_test_account()
    create_test_owner(account=account)
    email = 'test@test.com'
    random_password = '12123'
    random_password_mock = mocker.patch(
        'src.accounts.services.user.UserModel.objects.make_random_password',
        return_value=random_password,
    )
    safe_password = 'some safe password'
    make_password_mock = mocker.patch(
        'src.accounts.services.user.make_password',
        return_value=safe_password,
    )
    service = UserService()

    # act
    user = service._create_instance(
        account=account,
        email=email,
    )

    # assert
    assert user.account == account
    assert user.email == email
    assert user.is_superuser is False
    assert user.is_staff is False
    random_password_mock.assert_called_once()
    make_password_mock.assert_called_once_with(random_password)


def test_create_instance__not_first_db_user__is_not_superuser(mocker):
    # arrange
    account = create_test_account()
    create_test_owner()
    email = 'test@test.com'
    random_password = '12123'
    random_password_mock = mocker.patch(
        'src.accounts.services.user.UserModel.objects.make_random_password',
        return_value=random_password,
    )
    safe_password = 'some safe password'
    make_password_mock = mocker.patch(
        'src.accounts.services.user.make_password',
        return_value=safe_password,
    )
    service = UserService()

    # act
    user = service._create_instance(
        account=account,
        email=email,
        is_account_owner=True,
    )

    # assert
    assert user.account == account
    assert user.email == email
    assert user.is_superuser is False
    assert user.is_staff is False
    random_password_mock.assert_called_once()
    make_password_mock.assert_called_once_with(random_password)


def test_create_instance__not_account_owner___ok(mocker):
    # arrange
    account = create_test_account()
    language_owner = Language.fr
    tz_owner = 'Atlantic/Faeroe'
    date_fmt_owner = UserDateFormat.PY_EUROPE_24
    date_fdw_owner = UserFirstDayWeek.SATURDAY
    safe_password = 'some safe password'
    make_password_mock = mocker.patch(
        'src.accounts.services.user.make_password',
        return_value=safe_password,
    )
    account_owner = create_test_user(
        account=account,
        is_account_owner=True,
        email='owner@test.test',
        tz=tz_owner,
        language=language_owner,
        date_fmt=date_fmt_owner,
        date_fdw=date_fdw_owner,
    )
    status = UserStatus.INVITED
    email = 'user@test.test'
    first_name = 'some first'
    last_name = 'some last'
    photo = 'https://test.test/photo.jpg'
    phone = '+79541231212'
    raw_password = '213123'
    is_admin = True
    is_account_owner = False
    service = UserService()

    # act
    user = service._create_instance(
        account=account,
        email=email,
        phone=phone,
        status=status,
        first_name=first_name,
        last_name=last_name,
        photo=photo,
        raw_password=raw_password,
        is_admin=is_admin,
        is_account_owner=is_account_owner,
    )

    # assert
    assert user.account == account
    assert user.email == email
    assert user.status == UserStatus.INVITED
    assert user.first_name == first_name
    assert user.last_name == last_name
    assert user.photo == photo
    assert user.phone == phone
    assert user.password == safe_password
    assert user.is_admin == is_admin
    assert user.is_account_owner == is_account_owner
    assert user.timezone == account_owner.timezone
    assert user.language == account_owner.language
    assert user.date_fmt == account_owner.date_fmt
    assert user.date_fdw == account_owner.date_fdw
    make_password_mock.assert_called_once_with(raw_password)


def test_create_instance__password_provided__ok(mocker):
    # arrange
    account = create_test_account()
    create_test_user(account=account, is_account_owner=True)
    email = 'test@test.test'
    password = '12112323'
    random_password_mock = mocker.patch(
        'src.accounts.services.user.UserModel.objects.make_random_password',
    )
    make_password_mock = mocker.patch(
        'src.accounts.services.user.make_password',
    )
    service = UserService()

    # act
    user = service._create_instance(
        account=account,
        email=email,
        password=password,
    )

    # assert
    assert user.password == password
    random_password_mock.assert_not_called()
    make_password_mock.assert_not_called()


def test_create_instance__email_already_exists__raise_exception(mocker):
    # arrange
    account = create_test_account()
    create_test_user(account=account, is_account_owner=True)
    email = 'test@test.test'
    password = '12112323'
    mocker.patch(
        'src.accounts.services.user.UserModel.objects.make_random_password',
    )
    mocker.patch(
        'src.accounts.services.user.make_password',
    )
    create_test_user(
        email=email,
        status=UserStatus.ACTIVE,
    )
    service = UserService()

    # act
    with pytest.raises(AlreadyRegisteredException) as ex:
        service._create_instance(
            account=account,
            email=email,
            password=password,
        )

    # assert
    assert ex.value.message == messages.MSG_A_0005


def test_create_instance__invited_email_exists__ok(mocker):
    # arrange
    account = create_test_account()
    create_test_user(account=account, is_account_owner=True)
    email = 'test@test.test'
    password = '12112323'
    mocker.patch(
        'src.accounts.services.user.UserModel.objects.make_random_password',
    )
    mocker.patch(
        'src.accounts.services.user.make_password',
    )
    create_test_user(
        email=email,
        status=UserStatus.INVITED,
    )
    service = UserService()

    # act
    user = service._create_instance(
        account=account,
        email=email,
        password=password,
    )

    # assert
    assert user.email == email


def test_create_instance__inactive_email_exists__ok(mocker):
    # arrange
    account = create_test_account()
    create_test_user(account=account, is_account_owner=True)
    email = 'test@test.test'
    password = '12112323'
    mocker.patch(
        'src.accounts.services.user.UserModel.objects.make_random_password',
    )
    mocker.patch(
        'src.accounts.services.user.make_password',
    )
    create_test_user(
        email=email,
        status=UserStatus.INACTIVE,
    )
    service = UserService()

    # act
    user = service._create_instance(
        account=account,
        email=email,
        password=password,
    )

    # assert
    assert user.email == email


def test_create_instance__deleted_email_exists__ok(mocker):
    # arrange
    account = create_test_account()
    create_test_user(account=account, is_account_owner=True)
    email = 'test@test.test'
    password = '12112323'
    mocker.patch(
        'src.accounts.services.user.UserModel.objects.make_random_password',
    )
    mocker.patch(
        'src.accounts.services.user.make_password',
    )
    existent_user = create_test_user(email=email)
    existent_user.delete()
    service = UserService()

    # act
    user = service._create_instance(
        account=account,
        email=email,
        password=password,
    )

    # assert
    assert user.email == email


def test_create_instance__guest_email_exists__ok(mocker):
    # arrange
    account = create_test_account()
    create_test_user(
        is_account_owner=True,
        email='owner@test.test',
        account=account,
    )
    email = 'test@test.test'
    password = '12112323'
    mocker.patch(
        'src.accounts.services.user.UserModel.objects.make_random_password',
    )
    mocker.patch(
        'src.accounts.services.user.make_password',
    )
    create_test_guest(
        email=email,
        account=account,
    )
    service = UserService()

    # act
    user = service._create_instance(
        account=account,
        email=email,
        password=password,
    )

    # assert
    assert user.email == email


def test_create_instance__owner__set_default_language(mocker):
    # arrange
    account = create_test_account()
    email = 'test@test.test'
    password = '12123'
    service = UserService()
    settings_mock = mocker.patch(
        'src.accounts.services.user.settings',
    )
    language = Language.fr
    settings_mock.LANGUAGE_CODE = language
    settings_mock.TIME_ZONE = 'UTC'

    # act
    user = service._create_instance(
        is_account_owner=True,
        account=account,
        email=email,
        password=password,
    )

    # assert
    assert user.account == account
    assert user.email == email
    assert user.language == language


def test_create_instance__not_owner__inherit_owner_language():
    # arrange
    account = create_test_account()
    language = Language.fr
    create_test_user(
        account=account,
        is_account_owner=True,
        language=language,
    )
    email = 'test@test.test'
    password = '12123'
    service = UserService()

    # act
    user = service._create_instance(
        is_account_owner=False,
        account=account,
        email=email,
        password=password,
    )

    # assert
    assert user.account == account
    assert user.email == email
    assert user.language == language


def test_create_instance__owner__set_default_timezone(mocker):
    # arrange
    account = create_test_account()
    email = 'test@test.test'
    password = '12123'
    service = UserService()
    settings_mock = mocker.patch(
        'src.accounts.services.user.settings',
    )
    tz = 'Atlantic/Faeroe'
    settings_mock.LANGUAGE_CODE = Language.fr
    settings_mock.TIME_ZONE = tz

    # act
    user = service._create_instance(
        is_account_owner=True,
        account=account,
        email=email,
        password=password,
    )

    # assert
    assert user.account == account
    assert user.email == email
    assert user.timezone == tz


def test_create_instance__not_owner__inherit_owner_timezone():
    # arrange
    account = create_test_account()
    tz = 'Atlantic/Faeroe'
    create_test_user(
        account=account,
        is_account_owner=True,
        tz=tz,
    )
    email = 'test@test.test'
    password = '12123'
    service = UserService()

    # act
    user = service._create_instance(
        is_account_owner=False,
        account=account,
        email=email,
        password=password,
    )

    # assert
    assert user.account == account
    assert user.email == email
    assert user.timezone == tz


def test_create_related__no_groups__ok(mocker):
    # arrange
    user = create_test_user()
    user.account.accountsignupdata_set.get().delete()
    key = '!@#q2qwe'
    create_token_mock = mocker.patch(
        'src.accounts.services.user.PneumaticToken.create',
        return_value=key,
    )
    user_data = {'key': 'value'}
    service = UserService(instance=user)

    # act
    service._create_related(**user_data)

    # arrange
    assert APIKey.objects.get(
        user=user,
        name=user.get_full_name(),
        account=user.account,
        key=key,
    )
    create_token_mock.assert_called_once_with(
        user=user,
        for_api_key=True,
    )


def test_create_related__groups__ok(mocker):
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    user = create_test_admin(account=account)
    group = create_test_group(account=account, users=[owner])

    account.accountsignupdata_set.get().delete()
    key = '!@#q2qwe'
    create_token_mock = mocker.patch(
        'src.accounts.services.user.PneumaticToken.create',
        return_value=key,
    )

    user_data = {'key': 'value', 'user_groups': [group]}
    service = UserService(instance=user)

    # act
    service._create_related(**user_data)

    # arrange
    assert APIKey.objects.get(
        user=user,
        name=user.get_full_name(),
        account=user.account,
        key=key,
    )
    create_token_mock.assert_called_once_with(
        user=user,
        for_api_key=True,
    )
    assert user.user_groups.count() == 1
    assert user.user_groups.first().id == group.id


def test_create_actions__account_owner__ok(
    mocker,
    identify_mock,
    group_mock,
):
    # arrange
    account = create_test_account()
    account.is_verified = True
    account.save()
    user = create_test_user(account=account)
    UserInvite.objects.create(
        email=user.email,
        account=user.account,
        invited_by=user,
        invited_user=user,
    )
    is_superuser = True
    auth_type = AuthTokenType.API
    account_created_mock = mocker.patch(
        'src.accounts.services.user.AnalyticService.account_created',
    )
    account_verified_mock = mocker.patch(
        'src.accounts.services.user.AnalyticService.account_verified',
    )

    service = UserService(
        instance=user,
        auth_type=auth_type,
        is_superuser=is_superuser,
    )

    # act
    service._create_actions()

    # assert
    assert user.incoming_invites.count() == 0
    identify_mock.assert_called_once_with(user)
    group_mock.assert_called_once_with(user=user, account=account)
    account_created_mock.assert_called_once_with(
        user=user,
        is_superuser=is_superuser,
        auth_type=auth_type,
    )
    account_verified_mock.assert_called_once_with(
        user=user,
        is_superuser=is_superuser,
        auth_type=auth_type,
    )


def test_create_actions__account_owner__not_verified__ok(
    mocker,
    identify_mock,
    group_mock,
):
    # arrange
    account = create_test_account()
    account.is_verified = False
    account.save()
    user = create_test_user(account=account)
    is_superuser = True
    auth_type = AuthTokenType.API
    account_created_mock = mocker.patch(
        'src.accounts.services.user.AnalyticService.account_created',
    )
    account_verified_mock = mocker.patch(
        'src.accounts.services.user.AnalyticService.account_verified',
    )

    service = UserService(
        instance=user,
        auth_type=auth_type,
        is_superuser=is_superuser,
    )

    # act
    service._create_actions()

    # assert
    account_created_mock.assert_called_once_with(
        user=user,
        is_superuser=is_superuser,
        auth_type=auth_type,
    )
    account_verified_mock.assert_not_called()


def test_get_free_email__free__ok():
    # arrange
    user = create_test_user()
    local = 'admin'
    number = 1
    domain = 'test.com'
    service = UserService(instance=user)

    # act
    email = service._get_free_email(
        local=local,
        number=number,
        domain=domain,
    )

    # assert
    assert email == f'{local}+{number}@{domain}'


def test_get_free_email__active_user_already_exist__increment_number():
    # arrange
    local = 'admin'
    number = 1
    domain = 'test.com'
    user = create_test_user(email=f'{local}+{number}@{domain}')
    service = UserService(instance=user)

    # act
    email = service._get_free_email(
        local=local,
        number=number,
        domain=domain,
    )

    # assert
    assert email == f'{local}+{number + 1}@{domain}'


def test_get_free_email__invited_user_already_exist__increment_number():
    # arrange
    local = 'admin'
    number = 1
    domain = 'test.com'
    create_test_user(
        status=UserStatus.INVITED,
        email=f'{local}+{number}@{domain}',
    )
    user = create_test_user()
    service = UserService(instance=user)

    # act
    email = service._get_free_email(
        local=local,
        number=number,
        domain=domain,
    )

    # assert
    assert email == f'{local}+{number + 1}@{domain}'


def test_get_free_email__multiple_objects_returned__increment_number():
    # arrange
    local = 'admin'
    number = 1
    domain = 'test.com'
    create_test_user(
        status=UserStatus.INVITED,
        email=f'{local}+{number}@{domain}',
    )
    create_test_user(
        status=UserStatus.INACTIVE,
        email=f'{local}+{number}@{domain}',
    )
    user = create_test_user()
    service = UserService(instance=user)

    # act
    email = service._get_free_email(
        local=local,
        number=number,
        domain=domain,
    )

    # assert
    assert email == f'{local}+{number + 1}@{domain}'


def test_get_free_email__inactive_user_already_exist__increment_number():
    # arrange
    local = 'admin'
    number = 1
    domain = 'test.com'
    create_test_user(
        status=UserStatus.INACTIVE,
        email=f'{local}+{number}@{domain}',
    )
    user = create_test_user()
    service = UserService(instance=user)

    # act
    email = service._get_free_email(
        local=local,
        number=number,
        domain=domain,
    )

    # assert
    assert email == f'{local}+{number + 1}@{domain}'


def test_get_free_email__deleted_user_already_exist__not_increment_number():
    # arrange
    local = 'admin'
    number = 1
    domain = 'test.com'
    deleted_user = create_test_user(
        email=f'{local}+{number}@{domain}',
    )
    deleted_user.delete()
    user = create_test_user()
    service = UserService(instance=user)

    # act
    email = service._get_free_email(
        local=local,
        number=number,
        domain=domain,
    )

    # assert
    assert email == f'{local}+{number}@{domain}'


def test_get_free_email__guest_already_exist__increment_number():
    # arrange
    local = 'admin'
    number = 1
    domain = 'test.com'
    user = create_test_user()
    create_test_guest(
        account=user.account,
        email=f'{local}+{number}@{domain}',
    )
    service = UserService(instance=user)

    # act
    email = service._get_free_email(
        local=local,
        number=number,
        domain=domain,
    )

    # assert
    assert email == f'{local}+{number + 1}@{domain}'


def test_get_incremented_email__free__ok(mocker):
    # arrange
    local = 'local'
    number = 1
    domain = 'domain.com'
    email = f'{local}@{domain}'
    incremented_email = f'{local}+{number}@{domain}'
    user = create_test_user(email=email)
    get_free_email_mock = mocker.patch(
        'src.accounts.services.user.UserService._get_free_email',
        return_value=incremented_email,
    )

    service = UserService(instance=user)

    # act
    result = service._get_incremented_email(user=user)

    # assert
    assert result == incremented_email
    get_free_email_mock.assert_called_once_with(
        local=local,
        number=number,
        domain=domain,
    )


def test_get_incremented_email__already_incremented__ok(mocker):
    # arrange
    local = 'local'
    number = 2
    domain = 'domain.com'
    email = f'{local}+{1}@{domain}'
    incremented_email = f'{local}+{number}@{domain}'
    user = create_test_user(email=email)
    get_free_email_mock = mocker.patch(
        'src.accounts.services.user.UserService._get_free_email',
        return_value=incremented_email,
    )

    service = UserService(instance=user)

    # act
    result = service._get_incremented_email(user=user)

    # assert
    assert result == incremented_email
    get_free_email_mock.assert_called_once_with(
        local=local,
        number=number,
        domain=domain,
    )


def test_get_incremented_email__email_format__ok(mocker):
    # arrange
    local = 'local.n_a+m-e+'
    number = 2
    domain = 'domain.com'
    email = f'{local}+{1}@{domain}'
    incremented_email = f'{local}+{number}@{domain}'
    user = create_test_user(email=email)
    get_free_email_mock = mocker.patch(
        'src.accounts.services.user.UserService._get_free_email',
        return_value=incremented_email,
    )

    service = UserService(instance=user)

    # act
    result = service._get_incremented_email(user=user)

    # assert
    assert result == incremented_email
    get_free_email_mock.assert_called_once_with(
        local=local,
        number=number,
        domain=domain,
    )


def test_create_tenant_account_owner__ok(mocker):
    # arrange
    first_name = 'some first name'
    last_name = 'some last name'
    photo = 'https://test.com/image.jpg'
    phone = '+79541231212'
    master_account_owner = create_test_user(
        photo=photo,
        first_name=first_name,
        last_name=last_name,
        phone=phone,
    )
    tenant_account = create_test_account(
        master_account=master_account_owner.account,
        lease_level=LeaseLevel.TENANT,
    )
    tenant_account_owner = mocker.Mock()
    create_mock = mocker.patch(
        'src.accounts.services.user.UserService.create',
        return_value=tenant_account_owner,
    )
    incremented_email = 'test+1@test.com'
    get_incremented_email_mock = mocker.patch(
        'src.accounts.services.user.UserService._get_incremented_email',
        return_value=incremented_email,
    )
    service = UserService()

    # act
    result = service.create_tenant_account_owner(
        tenant_account=tenant_account,
        master_account=master_account_owner.account,
    )

    # assert
    assert result == tenant_account_owner
    create_mock.assert_called_once_with(
        account=tenant_account,
        email=incremented_email,
        status=UserStatus.ACTIVE,
        first_name=first_name,
        last_name=last_name,
        password=master_account_owner.password,
        photo=photo,
        phone=phone,
        is_admin=True,
        is_account_owner=True,
    )
    get_incremented_email_mock.assert_called_once_with(master_account_owner)


def test_validate_deactivate__user_is_performer__raise_exception(mocker):
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    deleted_user = create_test_admin(account=account)
    user_is_performer_mock = mocker.patch(
        'src.accounts.services.user.user_is_last_performer',
        return_value=True,
    )
    service = UserService(instance=deleted_user, user=owner)

    # act
    with pytest.raises(UserIsPerformerException):
        service._validate_deactivate()

    # assert
    user_is_performer_mock.assert_called_once_with(deleted_user)


def test_validate_deactivate__user_is_not_performer__ok(mocker):
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    deleted_user = create_test_admin(account=account)
    user_is_performer_mock = mocker.patch(
        'src.accounts.services.user.user_is_last_performer',
        return_value=False,
    )
    service = UserService(instance=deleted_user, user=owner)

    # act
    service._validate_deactivate()

    # assert
    user_is_performer_mock.assert_called_once_with(deleted_user)


def test_validate_deactivate__delete_yourself_raise_exception(mocker):
    # arrange
    account = create_test_account()
    create_test_owner(account=account)
    deleted_user = create_test_admin(account=account)
    user_is_performer_mock = mocker.patch(
        'src.accounts.services.user.user_is_last_performer',
        return_value=False,
    )

    service = UserService(instance=deleted_user, user=deleted_user)

    # act
    with pytest.raises(PreventSelfDeletion) as ex:
        service._validate_deactivate()

    # assert
    assert ex.value.message == str(messages.MSG_A_0047)
    user_is_performer_mock.assert_not_called()


def test_validate_deactivate__delete_account_owner_raise_exception(mocker):
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    user = create_test_admin(account=account)
    user_is_performer_mock = mocker.patch(
        'src.accounts.services.user.user_is_last_performer',
        return_value=False,
    )

    service = UserService(instance=owner, user=user)

    # act
    with pytest.raises(PreventAccountOwnerDeletion) as ex:
        service._validate_deactivate()

    # assert
    assert ex.value.message == str(messages.MSG_A_0048)
    user_is_performer_mock.assert_not_called()


def test_deactivate__ok(mocker):
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    deleted_user = create_test_admin(account=account)

    deactivate_mock = mocker.patch(
        'src.accounts.services.user.UserService._deactivate',
    )
    deactivate_actions_mock = mocker.patch(
        'src.accounts.services.user.UserService._deactivate_actions',
    )
    validate_deactivate_mock = mocker.patch(
        'src.accounts.services.user.UserService._validate_deactivate',
    )
    send_user_deleted_mock = mocker.patch(
        'src.notifications.tasks.send_user_deleted_notification.delay',
    )
    service = UserService(instance=deleted_user, user=owner)

    # act
    service.deactivate()

    # assert
    validate_deactivate_mock.assert_called_once_with()
    deactivate_mock.assert_called_once_with()
    deactivate_actions_mock.assert_called_once_with()
    send_user_deleted_mock.assert_called_once_with(
        logging=account.log_api_requests,
        account_id=account.id,
        user_data={
            'id': deleted_user.id,
            'first_name': deleted_user.first_name,
            'last_name': deleted_user.last_name,
            'email': deleted_user.email,
            'photo': deleted_user.photo,
            'is_admin': deleted_user.is_admin,
            'is_account_owner': deleted_user.is_account_owner,
            'manager_id': None,
            'subordinates_ids': [],
        },
    )


def test_deactivate__skip_validation__ok(mocker):
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    deleted_user = create_test_admin(account=account)

    deactivate_mock = mocker.patch(
        'src.accounts.services.user.UserService._deactivate',
    )
    deactivate_actions_mock = mocker.patch(
        'src.accounts.services.user.UserService._deactivate_actions',
    )
    validate_deactivate_mock = mocker.patch(
        'src.accounts.services.user.UserService._validate_deactivate',
    )
    send_user_deleted_mock = mocker.patch(
        'src.notifications.tasks.send_user_deleted_notification.delay',
    )
    service = UserService(instance=deleted_user, user=owner)

    # act
    service.deactivate(skip_validation=True)

    # assert
    validate_deactivate_mock.assert_not_called()
    deactivate_mock.assert_called_once_with()
    deactivate_actions_mock.assert_called_once_with()
    send_user_deleted_mock.assert_called_once_with(
        logging=account.log_api_requests,
        account_id=account.id,
        user_data={
            'id': deleted_user.id,
            'first_name': deleted_user.first_name,
            'last_name': deleted_user.last_name,
            'email': deleted_user.email,
            'photo': deleted_user.photo,
            'is_admin': deleted_user.is_admin,
            'is_account_owner': deleted_user.is_account_owner,
            'manager_id': None,
            'subordinates_ids': [],
        },
    )


def test_deactivate__not_call_actions_for_invited_user__ok(mocker):
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    invited_user = create_invited_user(owner)
    validate_deactivate_mock = mocker.patch(
        'src.accounts.services.user.UserService._validate_deactivate',
    )
    deactivate_mock = mocker.patch(
        'src.accounts.services.user.UserService._deactivate',
    )
    deactivate_actions_mock = mocker.patch(
        'src.accounts.services.user.UserService._deactivate_actions',
    )
    send_user_deleted_mock = mocker.patch(
        'src.notifications.tasks.send_user_deleted_notification.delay',
    )
    service = UserService(instance=invited_user, user=owner)

    # act
    service.deactivate()

    # assert
    validate_deactivate_mock.assert_called_once_with()
    deactivate_mock.assert_called_once_with()
    deactivate_actions_mock.assert_not_called()
    send_user_deleted_mock.assert_called_once_with(
        logging=account.log_api_requests,
        account_id=account.id,
        user_data={
            'id': invited_user.id,
            'first_name': invited_user.first_name,
            'last_name': invited_user.last_name,
            'email': invited_user.email,
            'photo': invited_user.photo,
            'is_admin': invited_user.is_admin,
            'is_account_owner': invited_user.is_account_owner,
            'manager_id': None,
            'subordinates_ids': [],
        },
    )


def test_private_deactivate__ok(mocker):
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    deleted_user = create_test_admin(account=account)
    remove_user_from_draft_mock = mocker.patch(
        'src.accounts.services.user.remove_user_from_draft',
    )
    update_users_counts_mock = mocker.patch(
        'src.accounts.services.account.AccountService.update_users_counts',
    )
    identify_mock = mocker.patch(
        'src.accounts.services.user.UserService.identify',
    )
    service = UserService(instance=deleted_user, user=owner)

    # act
    service._deactivate()

    # assert
    deleted_user.refresh_from_db()
    assert not deleted_user.incoming_invites.exists()
    assert deleted_user.status == UserStatus.INACTIVE
    assert deleted_user.is_active is False
    remove_user_from_draft_mock.assert_called_once_with(
        user_id=deleted_user.id,
        account_id=account.id,
    )
    update_users_counts_mock.assert_called_once()
    identify_mock.assert_called_once_with(deleted_user)


def test_private_deactivate__activate_contacts__ok(mocker):
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    invited_user = create_invited_user(owner)
    another_user = create_test_admin(account=account)
    another_account_user = create_test_owner(
        email='anotheraccount@email.com',
    )
    mocker.patch(
        'src.accounts.services.user.remove_user_from_draft',
    )
    mocker.patch(
        'src.accounts.services.account.AccountService.update_users_counts',
    )
    mocker.patch(
        'src.accounts.services.user.UserService.identify',
    )
    google_contact = Contact.objects.create(
        account=account,
        user_id=owner.id,
        source=SourceType.GOOGLE,
        email=invited_user.email,
    )
    ms_contact = Contact.objects.create(
        account=account,
        user_id=owner.id,
        source=SourceType.MICROSOFT,
        email=invited_user.email,
    )
    another_user_contact = Contact.objects.create(
        account=account,
        user_id=another_user.id,
        source=SourceType.MICROSOFT,
        email=invited_user.email,
    )
    another_account_contact = Contact.objects.create(
        account=another_account_user.account,
        user_id=another_account_user.id,
        source=SourceType.GOOGLE,
        email=invited_user.email,
    )
    another_contact = Contact.objects.create(
        account=account,
        user_id=owner.id,
        source=SourceType.MICROSOFT,
        email='another@email.com',
    )
    service = UserService(instance=invited_user, user=owner)

    # act
    service._deactivate()

    # assert
    google_contact.refresh_from_db()
    assert google_contact.status == UserStatus.INVITED

    ms_contact.refresh_from_db()
    assert ms_contact.status == UserStatus.INVITED

    another_user_contact.refresh_from_db()
    assert another_user_contact.status == UserStatus.INVITED

    another_account_contact.refresh_from_db()
    assert another_account_contact.status == UserStatus.ACTIVE

    another_contact.refresh_from_db()
    assert another_contact.status == UserStatus.ACTIVE


def test_deactivate_actions__ok(mocker):
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    user = create_test_user(account=account)
    send_user_deactivated_notification_mock = mocker.patch(
        'src.notifications.tasks.send_user_deactivated_notification.delay',
    )
    service = UserService(instance=user, user=owner)

    # act
    service._deactivate_actions()

    # assert
    send_user_deactivated_notification_mock.assert_called_once_with(
        user_id=user.id,
        user_email=user.email,
        account_id=user.account_id,
        logo_lg=user.account.logo_lg,
    )


def test_change_password__ok():
    # arrange
    user = create_test_user()
    new_password = '<PASSWORD>'
    service = UserService(user=user)

    # act
    service.change_password(password=new_password)

    # assert
    user.refresh_from_db()
    assert check_password(new_password, user.password)
    assert new_password != user.password


def test_update_related_user_fields__name_changed__ok():
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    user = create_test_admin(account=account)
    old_name = 'Old name'

    workflow = create_test_workflow(user=owner, tasks_count=1)
    task = workflow.tasks.get(number=1)
    user_field = TaskField.objects.create(
        task=task,
        type=FieldType.USER,
        workflow=workflow,
        value=old_name,
        user_id=user.id,
        account=account,
    )
    service = UserService(instance=user, user=owner)

    # act
    service._update_related_user_fields(old_name=old_name)

    # assert
    user_field.refresh_from_db()
    assert user_field.value == user.name


def test_update_related_user_fields__name_changed__qst_updated(mocker):
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    user = create_test_admin(account=account)
    old_name = 'Old name'

    service = UserService(instance=user, user=owner)
    qst_mock = mocker.Mock(update=mocker.Mock(return_value=None))
    filter_mock = mocker.patch(
        'src.accounts.services.user.TaskField.objects.filter',
        return_value=qst_mock,
    )

    # act
    service._update_related_user_fields(old_name=old_name)

    # assert
    filter_mock.assert_called_once_with(
        type=FieldType.USER,
        user_id=user.id,
    )
    qst_mock.update.assert_called_once_with(value=user.name)


def test_update_related_user_fields__name_not_changed__skip_update(mocker):
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    user = create_test_admin(account=account)
    old_name = user.name

    service = UserService(instance=user, user=owner)
    qst_mock = mocker.Mock(update=mocker.Mock(return_value=None))
    filter_mock = mocker.patch(
        'src.accounts.services.user.TaskField.objects.filter',
        return_value=qst_mock,
    )

    # act
    service._update_related_user_fields(old_name=old_name)

    # assert
    filter_mock.assert_not_called()
    qst_mock.update.assert_not_called()


def test_update_related_user_fields__another_account_field__not_changed():
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    user = create_test_admin(account=account)
    old_name = 'Old name'

    another_user = create_test_owner(email='another@test.test')
    workflow = create_test_workflow(user=another_user, tasks_count=1)
    task = workflow.tasks.get(number=1)
    user_field = TaskField.objects.create(
        task=task,
        type=FieldType.USER,
        workflow=workflow,
        value=old_name,
        user_id=another_user.id,
        account=another_user.account,
    )
    service = UserService(instance=user, user=owner)

    # act
    service._update_related_user_fields(old_name=old_name)

    # assert
    user_field.refresh_from_db()
    assert user_field.value == old_name


def test_update_related_stripe_account__account_owner__ok(mocker):
    # arrange
    account = create_test_account(
        lease_level=LeaseLevel.STANDARD,
        billing_sync=True,
    )
    owner = create_test_owner(account=account)
    stripe_service_init_mock = mocker.patch.object(
        StripeService,
        attribute='__init__',
        return_value=None,
    )
    update_customer_mock = mocker.patch(
        'src.payment.stripe.service.StripeService.update_customer',
    )
    is_superuser = False
    auth_type = AuthTokenType.API
    service = UserService(
        instance=owner,
        user=owner,
        is_superuser=is_superuser,
        auth_type=auth_type,
    )
    service.instance = owner

    # act
    service._update_related_stripe_account()

    # assert
    stripe_service_init_mock.assert_called_once_with(
        user=owner,
        auth_type=auth_type,
        is_superuser=is_superuser,
    )
    update_customer_mock.assert_called_once_with()


def test_update_related_stripe_account__stripe_raises__raise_exception(mocker):
    # arrange
    account = create_test_account(
        lease_level=LeaseLevel.STANDARD,
        billing_sync=True,
    )
    owner = create_test_owner(account=account)
    stripe_service_init_mock = mocker.patch.object(
        StripeService,
        attribute='__init__',
        return_value=None,
    )
    message = 'Stripe error'
    update_customer_mock = mocker.patch(
        'src.payment.stripe.service.StripeService.update_customer',
        side_effect=StripeServiceException(message=message),
    )
    is_superuser = False
    auth_type = AuthTokenType.API
    service = UserService(
        instance=owner,
        user=owner,
        is_superuser=is_superuser,
        auth_type=auth_type,
    )

    # act
    with pytest.raises(UserServiceException) as ex:
        service._update_related_stripe_account()

    # assert
    assert ex.value.message == message
    stripe_service_init_mock.assert_called_once_with(
        user=owner,
        auth_type=auth_type,
        is_superuser=is_superuser,
    )
    update_customer_mock.assert_called_once_with()


def test_update_related_stripe_account__tenant_account__skip(mocker):
    # arrange
    account = create_test_account(
        lease_level=LeaseLevel.TENANT,
        billing_sync=True,
    )
    owner = create_test_owner(account=account)
    stripe_service_init_mock = mocker.patch.object(
        StripeService,
        attribute='__init__',
        return_value=None,
    )
    update_customer_mock = mocker.patch(
        'src.payment.stripe.service.StripeService.update_customer',
    )
    is_superuser = False
    auth_type = AuthTokenType.API
    service = UserService(
        instance=owner,
        user=owner,
        is_superuser=is_superuser,
        auth_type=auth_type,
    )

    # act
    service._update_related_stripe_account()

    # assert
    stripe_service_init_mock.assert_not_called()
    update_customer_mock.assert_not_called()


def test_update_related_stripe_account__not_owner__skip(mocker):
    # arrange
    account = create_test_account(
        lease_level=LeaseLevel.STANDARD,
        billing_sync=True,
    )
    owner = create_test_owner(account=account)
    user = create_test_admin(account=account)
    stripe_service_init_mock = mocker.patch.object(
        StripeService,
        attribute='__init__',
        return_value=None,
    )
    update_customer_mock = mocker.patch(
        'src.payment.stripe.service.StripeService.update_customer',
    )
    is_superuser = False
    auth_type = AuthTokenType.API
    service = UserService(
        instance=user,
        user=owner,
        is_superuser=is_superuser,
        auth_type=auth_type,
    )

    # act
    service._update_related_stripe_account()

    # assert
    stripe_service_init_mock.assert_not_called()
    update_customer_mock.assert_not_called()


def test_update_related_stripe_account__billing_sync_off__skip(mocker):
    # arrange
    account = create_test_account(
        lease_level=LeaseLevel.STANDARD,
        billing_sync=False,
    )
    owner = create_test_owner(account=account)
    stripe_service_init_mock = mocker.patch.object(
        StripeService,
        attribute='__init__',
        return_value=None,
    )
    update_customer_mock = mocker.patch(
        'src.payment.stripe.service.StripeService.update_customer',
    )
    is_superuser = False
    auth_type = AuthTokenType.API
    service = UserService(
        instance=owner,
        user=owner,
        is_superuser=is_superuser,
        auth_type=auth_type,
    )

    # act
    service._update_related_stripe_account()

    # assert
    stripe_service_init_mock.assert_not_called()
    update_customer_mock.assert_not_called()


def test_update_analytics__disable_digest_subscriber__sent_analytics(
    mocker,
    identify_mock,
):
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    user = create_test_admin(account=account)
    users_digest_mock = mocker.patch(
        'src.analysis.services.AnalyticService.users_digest',
    )
    is_superuser = False
    auth_type = AuthTokenType.API
    update_kwargs = {
        'is_digest_subscriber': False,
    }
    service = UserService(
        instance=user,
        user=owner,
        is_superuser=is_superuser,
        auth_type=auth_type,
    )

    # act
    service._update_analytics(**update_kwargs)

    # assert
    users_digest_mock.assert_called_once_with(
        user=user,
        auth_type=auth_type,
        is_superuser=is_superuser,
    )
    identify_mock.assert_called_once_with(user)


def test_update_analytics__enable_digest_subscriber__not_sent_analytics(
    mocker,
    identify_mock,
):
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    user = create_test_admin(account=account)
    users_digest_mock = mocker.patch(
        'src.analysis.services.AnalyticService.users_digest',
    )
    is_superuser = False
    auth_type = AuthTokenType.API
    update_kwargs = {
        'is_digest_subscriber': True,
    }
    service = UserService(
        instance=user,
        user=owner,
        is_superuser=is_superuser,
        auth_type=auth_type,
    )

    # act
    service._update_analytics(**update_kwargs)

    # assert
    users_digest_mock.assert_not_called()
    identify_mock.assert_called_once_with(user)


def test_update_analytics__digest_subscriber_not_changed__not_sent_analytics(
    mocker,
    identify_mock,
):
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    user = create_test_admin(account=account)
    users_digest_mock = mocker.patch(
        'src.analysis.services.AnalyticService.users_digest',
    )
    is_superuser = False
    auth_type = AuthTokenType.API
    update_kwargs = {
        'another_value': True,
    }
    service = UserService(
        instance=user,
        user=owner,
        is_superuser=is_superuser,
        auth_type=auth_type,
    )

    # act
    service._update_analytics(**update_kwargs)

    # assert
    users_digest_mock.assert_not_called()
    identify_mock.assert_called_once_with(user)


def test_partial_update__all_fields_end_to_end__ok(
    mocker,
    identify_mock,
):
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    user = create_test_admin(account=account)
    old_name = user.name
    create_test_group(
        account=account,
        users=[user],
        name='old group',
    )
    new_group = create_test_group(account=account, users=[owner])
    user_data = {
        'email': 'some@email.com',
        'first_name': 'First',
        'last_name': 'Last',
        'photo': 'https://my.lovely.photo.jpg',
        'phone': '79999999990',
        'is_tasks_digest_subscriber': False,
        'is_digest_subscriber': False,
        'is_comments_mentions_subscriber': False,
        'is_new_tasks_subscriber': False,
        'is_complete_tasks_subscriber': False,
        'is_newsletters_subscriber': False,
        'is_special_offers_subscriber': False,
        'language': 'en',
        'timezone': 'America/Anchorage',
        'date_fmt': UserDateFormat.API_USA_24,
        'date_fdw': UserFirstDayWeek.THURSDAY,
        'is_admin': False,
    }
    raw_password = 'new password 123'
    update_kwargs = {
        'user_groups': [new_group.id],
        'raw_password': raw_password,
        **user_data,
    }
    safe_password = 'some safe password'
    make_password_mock = mocker.patch(
        'src.accounts.services.user.make_password',
        return_value=safe_password,
    )
    update_related_user_fields_mock = mocker.patch(
        'src.accounts.services.user.UserService._update_related_user_fields',
    )
    update_related_stripe_account_mock = mocker.patch(
        'src.accounts.services.user.UserService.'
        '_update_related_stripe_account',
    )
    update_analytics_mock = mocker.patch(
        'src.accounts.services.user.UserService._update_analytics',
    )
    send_user_updated_notification_mock = mocker.patch(
        'src.notifications.tasks.send_user_updated_notification.delay',
    )
    service = UserService(
        instance=user,
        user=owner,
    )
    # act
    result = service.partial_update(**update_kwargs, force_save=True)

    # assert
    assert result is user
    update_related_user_fields_mock.assert_called_once_with(
        old_name=old_name,
    )
    update_related_stripe_account_mock.assert_called_once_with()
    update_analytics_mock.assert_called_once_with(**user_data)
    send_user_updated_notification_mock.assert_called_once_with(
        logging=account.log_api_requests,
        account_id=account.id,
        user_data=UserWebsocketSerializer(user).data,
    )
    user.refresh_from_db()
    assert user_data['email'] == user.email
    assert user_data['phone'] == user.phone
    assert user_data['photo'] == user.photo
    assert user_data['first_name'] == user.first_name
    assert user_data['last_name'] == user.last_name
    assert user_data['is_admin'] == user.is_admin
    assert user_data['language'] == user.language
    assert user_data['timezone'] == user.timezone
    assert user_data['date_fmt'] == UserDateFormat.API_USA_24
    assert user_data['date_fdw'] == user.date_fdw
    assert user_data['is_tasks_digest_subscriber'] == (
        user.is_tasks_digest_subscriber
    )
    assert user_data['is_digest_subscriber'] == (user.is_digest_subscriber)
    assert user_data['is_newsletters_subscriber'] == (
        user.is_newsletters_subscriber
    )
    assert user_data['is_special_offers_subscriber'] == (
        user.is_special_offers_subscriber
    )
    assert user_data['is_new_tasks_subscriber'] == (
        user.is_new_tasks_subscriber
    )
    assert user_data['is_complete_tasks_subscriber'] == (
        user.is_complete_tasks_subscriber
    )
    assert user_data['is_comments_mentions_subscriber'] == (
        user.is_comments_mentions_subscriber
    )
    assert user.user_groups.count() == 1
    assert user.user_groups.first().id == update_kwargs['user_groups'][0]
    assert user.password == safe_password
    make_password_mock.assert_called_once_with(raw_password)


def test_partial_update__default_force_save__ok(
    mocker,
    identify_mock,
):
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    user = create_test_admin(account=account)
    update_kwargs = {
        'some_property': 'value',
    }
    make_password_mock = mocker.patch(
        'src.accounts.services.user.make_password',
    )
    partial_update_mock = mocker.patch(
        'src.generics.base.service.BaseModelService.partial_update',
    )
    update_related_user_fields_mock = mocker.patch(
        'src.accounts.services.user.UserService._update_related_user_fields',
    )
    update_related_stripe_account_mock = mocker.patch(
        'src.accounts.services.user.UserService.'
        '_update_related_stripe_account',
    )
    update_analytics_mock = mocker.patch(
        'src.accounts.services.user.UserService._update_analytics',
    )
    send_user_updated_notification_mock = mocker.patch(
        'src.notifications.tasks.send_user_updated_notification.delay',
    )
    service = UserService(
        instance=user,
        user=owner,
    )
    # act
    result = service.partial_update(**update_kwargs)

    # assert
    assert result is user
    partial_update_mock.assert_called_once_with(
        force_save=True,
        **update_kwargs,
    )
    update_related_user_fields_mock.assert_called_once_with(
        old_name=user.name,
    )
    update_related_stripe_account_mock.assert_called_once_with()
    update_analytics_mock.assert_called_once_with(**update_kwargs)
    send_user_updated_notification_mock.assert_called_once_with(
        logging=account.log_api_requests,
        account_id=account.id,
        user_data=UserWebsocketSerializer(user).data,
    )
    make_password_mock.assert_not_called()


def test_partial_update__force_save_true__ok(
    mocker,
    identify_mock,
):
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    user = create_test_admin(account=account)
    update_kwargs = {
        'some_property': 'value',
    }
    partial_update_mock = mocker.patch(
        'src.generics.base.service.BaseModelService.partial_update',
    )
    update_related_user_fields_mock = mocker.patch(
        'src.accounts.services.user.UserService._update_related_user_fields',
    )
    update_related_stripe_account_mock = mocker.patch(
        'src.accounts.services.user.UserService.'
        '_update_related_stripe_account',
    )
    update_analytics_mock = mocker.patch(
        'src.accounts.services.user.UserService._update_analytics',
    )
    send_user_updated_notification_mock = mocker.patch(
        'src.notifications.tasks.send_user_updated_notification.delay',
    )
    service = UserService(
        instance=user,
        user=owner,
    )
    # act
    result = service.partial_update(**update_kwargs, force_save=True)

    # assert
    assert result is user
    partial_update_mock.assert_called_once_with(
        force_save=True,
        **update_kwargs,
    )
    update_related_user_fields_mock.assert_called_once_with(
        old_name=user.name,
    )
    update_related_stripe_account_mock.assert_called_once_with()
    update_analytics_mock.assert_called_once_with(**update_kwargs)
    send_user_updated_notification_mock.assert_called_once_with(
        logging=account.log_api_requests,
        account_id=account.id,
        user_data=UserWebsocketSerializer(user).data,
    )


def test_partial_update__remove_all_groups__ok(
    mocker,
    identify_mock,
):
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    user = create_test_admin(account=account)
    create_test_group(account=account, users=[owner, user])
    update_kwargs = {
        'user_groups': [],
    }
    partial_update_mock = mocker.patch(
        'src.generics.base.service.BaseModelService.partial_update',
    )
    update_related_user_fields_mock = mocker.patch(
        'src.accounts.services.user.UserService._update_related_user_fields',
    )
    update_related_stripe_account_mock = mocker.patch(
        'src.accounts.services.user.UserService.'
        '_update_related_stripe_account',
    )
    update_analytics_mock = mocker.patch(
        'src.accounts.services.user.UserService._update_analytics',
    )
    send_user_updated_notification_mock = mocker.patch(
        'src.notifications.tasks.send_user_updated_notification.delay',
    )
    service = UserService(
        instance=user,
        user=owner,
    )
    # act
    result = service.partial_update(**update_kwargs, force_save=True)

    # assert
    assert result is user
    assert user.user_groups.count() == 0
    partial_update_mock.assert_called_once_with(
        force_save=True,
    )
    update_related_user_fields_mock.assert_called_once_with(
        old_name=user.name,
    )
    update_related_stripe_account_mock.assert_called_once_with()
    update_analytics_mock.assert_called_once_with()
    send_user_updated_notification_mock.assert_called_once_with(
        logging=account.log_api_requests,
        account_id=account.id,
        user_data=UserWebsocketSerializer(user).data,
    )


def test_create_instance__photo_url_longer_than_1024_chars__ok(mocker):
    # arrange
    account = create_test_account()
    create_test_owner(account=account)
    email = 'google.user@test.test'
    password = 'somepassword'
    long_photo_url = (
        'https://lh3.googleusercontent.com/a-/ALV-UjWKVqsz6krMJcnaNuFH'
        'WiZtnxWb4FtOnjXtR5FWJCLmC4BNRr8sL3SJnHC1fvMMJARBLV-1n0MQs5xe'
        'bNR6HPYkC-zhOakqc9WLeI0M-522lIZNzZ5WNB0H3AUT_XGR7fGhAmaO8y24'
        'DSnoyES8Ovb57eq-LdiW76LV6ki9NQwB5HdNoLb9emGGa6jNNP9qEAEip03sb'
        '4PXejO4rdS_3DaeT3BpGTYE3sbl0GhxrFi7mH_64kE1iLyNNz55s9bUPETriQ'
        'SDSIaINGOeQmFP5U_WfEFaZ-wT8kADHm2kirRNGIstCh0uKTHOnQCKmzKCx_D'
        'Xfsco_ADXd8KyVOA-S7jmpsp3-e_rfp93JTi8hOQvnYB2OPA0t7G-NFbfFEeA'
        'o5HWW9Hzf3psxtmkrds3Qix0lDh-tfUchtp4NdVAkXut0vI-axgVAgiuM7F2W'
        'dzijaTVw6Ecwz7Nb7m_O4' + 'X' * 800 + '=s96-c'
    )
    mocker.patch(
        'src.accounts.services.user.make_password',
        return_value='hashed_password',
    )
    service = UserService()

    # act
    user = service._create_instance(
        account=account,
        email=email,
        password=password,
        photo=long_photo_url,
    )

    # assert
    assert user.photo == long_photo_url
    assert len(user.photo) > 1024


def test_update_subordinates__changed_users__ok(mocker):
    # arrange
    account = create_test_account()
    account.log_api_requests = True
    account.save()
    manager = create_test_not_admin(account=account)
    old_report = create_test_not_admin(account=account, email='old@test.test')
    new_report = create_test_not_admin(account=account, email='new@test.test')
    manager.subordinates.set([old_report])

    owner = create_test_owner(account=account)
    service = UserService(instance=manager, user=owner)
    send_user_updated_notification_delay_mock = mocker.patch(
        'src.accounts.services.user.send_user_updated_notification.delay',
    )
    mocker.patch(
        'src.accounts.services.user.transaction.on_commit',
        side_effect=lambda f: f(),
    )

    # act
    result = service.partial_update(subordinates=[new_report])

    # assert
    assert result == manager
    assert list(manager.subordinates.all()) == [new_report]
    # partial_update user notification + _update_subordinates (2 changed)
    assert send_user_updated_notification_delay_mock.call_count == 3


def test_update_subordinates__no_changed_users__ok(mocker):
    # arrange
    account = create_test_account()
    account.log_api_requests = True
    account.save()
    manager = create_test_not_admin(account=account)
    report = create_test_not_admin(account=account, email='rep@test.test')
    manager.subordinates.set([report])

    owner = create_test_owner(account=account)
    service = UserService(instance=manager, user=owner)
    send_user_updated_notification_delay_mock = mocker.patch(
        'src.accounts.services.user.send_user_updated_notification.delay',
    )
    mocker.patch(
        'src.accounts.services.user.transaction.on_commit',
        side_effect=lambda f: f(),
    )

    # act
    result = service.partial_update(subordinates=[report])

    # assert
    assert result == manager
    assert list(manager.subordinates.all()) == [report]
    # partial_update user notification only (no changed subordinates)
    assert send_user_updated_notification_delay_mock.call_count == 1


def test_deactivate__manager__subordinates_notified_and_cleared(mocker):
    # arrange
    account = create_test_account()
    account.log_api_requests = True
    account.save()
    manager = create_test_not_admin(account=account)
    report = create_test_not_admin(account=account, email='rep@test.test')
    manager.subordinates.set([report])

    owner = create_test_owner(account=account)
    service = UserService(instance=manager, user=owner)
    send_updated_mock = mocker.patch(
        'src.accounts.services.user.send_user_updated_notification.delay',
    )
    send_deleted_mock = mocker.patch(
        'src.accounts.services.user.send_user_deleted_notification.delay',
    )
    mocker.patch(
        'src.accounts.services.user.transaction.on_commit',
        side_effect=lambda f: f(),
    )
    mocker.patch(
        'src.accounts.services.user.send_user_deactivated_notification.delay',
    )

    # act
    service.deactivate()

    # assert
    report.refresh_from_db()
    assert report.manager is None
    send_updated_mock.assert_called_once()
    send_deleted_mock.assert_called_once()
    assert send_updated_mock.call_args[1]['user_data']['id'] == report.id


def test_partial_update__manager_changed__managers_notified(mocker):
    # arrange
    account = create_test_account()
    old_manager = create_test_not_admin(account=account, email='old@test.test')
    new_manager = create_test_not_admin(account=account, email='new@test.test')
    user = create_test_not_admin(account=account, email='user@test.test')
    user.manager = old_manager
    user.save()

    owner = create_test_owner(account=account)
    service = UserService(instance=user, user=owner)
    send_mock = mocker.patch(
        'src.accounts.services.user.send_user_updated_notification.delay',
    )

    # act
    service.partial_update(manager=new_manager)

    # assert
    # Notifies user + old_manager + new_manager = 3 times
    assert send_mock.call_count == 3
    notified_ids = {
        call[1]['user_data']['id'] for call in send_mock.call_args_list
    }
    assert notified_ids == {user.id, old_manager.id, new_manager.id}


def test_partial_update__manager_not_changed__only_user_notified(mocker):
    # arrange
    account = create_test_account()
    old_manager = create_test_not_admin(account=account, email='old@test.test')
    user = create_test_not_admin(account=account, email='user@test.test')
    user.manager = old_manager
    user.save()

    owner = create_test_owner(account=account)
    service = UserService(instance=user, user=owner)
    send_mock = mocker.patch(
        'src.accounts.services.user.send_user_updated_notification.delay',
    )

    # act
    service.partial_update(manager=old_manager, first_name='Test')

    # assert
    # Notifies only user since manager hasn't actually changed
    send_mock.assert_called_once()
    assert send_mock.call_args[1]['user_data']['id'] == user.id


def test_deactivate__has_manager__clears_mgr_and_notifies(mocker):
    # arrange
    account = create_test_account()
    account.log_api_requests = True
    account.save()
    mgr = create_test_not_admin(
        account=account,
        email='mgr@test.test',
    )
    user = create_test_not_admin(
        account=account,
        email='user@test.test',
    )
    user.manager = mgr
    user.save()

    owner = create_test_owner(account=account)
    service = UserService(instance=user, user=owner)
    send_updated_mock = mocker.patch(
        'src.accounts.services.user.'
        'send_user_updated_notification.delay',
    )
    mocker.patch(
        'src.accounts.services.user.'
        'send_user_deleted_notification.delay',
    )
    mocker.patch(
        'src.accounts.services.user.transaction.on_commit',
        side_effect=lambda f: f(),
    )
    mocker.patch(
        'src.accounts.services.user.'
        'send_user_deactivated_notification.delay',
    )

    # act
    service.deactivate()

    # assert
    user.refresh_from_db()
    assert user.manager is None
    send_updated_mock.assert_called_once()
    assert send_updated_mock.call_args[1][
        'user_data'
    ]['id'] == mgr.id


def test_deactivate__no_manager__skip_mgr_notification(mocker):
    # arrange
    account = create_test_account()
    user = create_test_not_admin(
        account=account,
        email='user@test.test',
    )

    owner = create_test_owner(account=account)
    service = UserService(instance=user, user=owner)
    send_updated_mock = mocker.patch(
        'src.accounts.services.user.'
        'send_user_updated_notification.delay',
    )
    mocker.patch(
        'src.accounts.services.user.'
        'send_user_deleted_notification.delay',
    )
    mocker.patch(
        'src.accounts.services.user.transaction.on_commit',
        side_effect=lambda f: f(),
    )
    mocker.patch(
        'src.accounts.services.user.'
        'send_user_deactivated_notification.delay',
    )

    # act
    service.deactivate()

    # assert
    user.refresh_from_db()
    assert user.manager is None
    send_updated_mock.assert_not_called()


def test_deactivate__has_subs_and_manager__both_notified(mocker):
    # arrange
    account = create_test_account()
    account.log_api_requests = True
    account.save()
    mgr = create_test_not_admin(
        account=account,
        email='mgr@test.test',
    )
    user = create_test_not_admin(
        account=account,
        email='user@test.test',
    )
    user.manager = mgr
    user.save()
    sub = create_test_not_admin(
        account=account,
        email='sub@test.test',
    )
    user.subordinates.set([sub])

    owner = create_test_owner(account=account)
    service = UserService(instance=user, user=owner)
    send_updated_mock = mocker.patch(
        'src.accounts.services.user.'
        'send_user_updated_notification.delay',
    )
    mocker.patch(
        'src.accounts.services.user.'
        'send_user_deleted_notification.delay',
    )
    mocker.patch(
        'src.accounts.services.user.transaction.on_commit',
        side_effect=lambda f: f(),
    )
    mocker.patch(
        'src.accounts.services.user.'
        'send_user_deactivated_notification.delay',
    )

    # act
    service.deactivate()

    # assert
    user.refresh_from_db()
    sub.refresh_from_db()
    assert user.manager is None
    assert sub.manager is None
    # sub notified + manager notified = 2
    assert send_updated_mock.call_count == 2
    notified_ids = {
        call[1]['user_data']['id']
        for call in send_updated_mock.call_args_list
    }
    assert notified_ids == {sub.id, mgr.id}


def test_update_subordinates__old_mgr_notified__ok(mocker):
    # arrange
    account = create_test_account()
    account.log_api_requests = True
    account.save()
    old_mgr = create_test_not_admin(
        account=account,
        email='old_mgr@test.test',
    )
    new_mgr = create_test_not_admin(
        account=account,
        email='new_mgr@test.test',
    )
    report = create_test_not_admin(
        account=account,
        email='report@test.test',
    )
    report.manager = old_mgr
    report.save()
    old_mgr.subordinates.set([report])

    owner = create_test_owner(account=account)
    service = UserService(instance=new_mgr, user=owner)
    send_mock = mocker.patch(
        'src.accounts.services.user.'
        'send_user_updated_notification.delay',
    )
    mocker.patch(
        'src.accounts.services.user.transaction.on_commit',
        side_effect=lambda f: f(),
    )

    # act
    service.partial_update(subordinates=[report])

    # assert
    # partial_update (new_mgr) + _update_subordinates (report
    # + old_mgr) = 3
    assert send_mock.call_count == 3
    notified_ids = {
        call[1]['user_data']['id']
        for call in send_mock.call_args_list
    }
    assert notified_ids == {new_mgr.id, report.id, old_mgr.id}


def test_update_subordinates__no_old_mgr__no_extra_notify(mocker):
    # arrange
    account = create_test_account()
    account.log_api_requests = True
    account.save()
    manager = create_test_not_admin(
        account=account,
        email='mgr@test.test',
    )
    report = create_test_not_admin(
        account=account,
        email='report@test.test',
    )

    owner = create_test_owner(account=account)
    service = UserService(instance=manager, user=owner)
    send_mock = mocker.patch(
        'src.accounts.services.user.'
        'send_user_updated_notification.delay',
    )
    mocker.patch(
        'src.accounts.services.user.transaction.on_commit',
        side_effect=lambda f: f(),
    )

    # act
    service.partial_update(subordinates=[report])

    # assert
    # partial_update (manager) + _update_subordinates (report) = 2
    assert send_mock.call_count == 2
    notified_ids = {
        call[1]['user_data']['id']
        for call in send_mock.call_args_list
    }
    assert notified_ids == {manager.id, report.id}


def test_update_subordinates__report_moved_between_mgrs__old_mgr_notified(
    mocker,
):
    # arrange
    account = create_test_account()
    account.log_api_requests = True
    account.save()
    old_mgr = create_test_not_admin(
        account=account,
        email='old@test.test',
    )
    new_mgr = create_test_not_admin(
        account=account,
        email='new@test.test',
    )
    report_a = create_test_not_admin(
        account=account,
        email='a@test.test',
    )
    report_b = create_test_not_admin(
        account=account,
        email='b@test.test',
    )
    report_a.manager = old_mgr
    report_a.save()
    report_b.manager = old_mgr
    report_b.save()
    old_mgr.subordinates.set([report_a, report_b])

    owner = create_test_owner(account=account)
    service = UserService(instance=new_mgr, user=owner)
    send_mock = mocker.patch(
        'src.accounts.services.user.'
        'send_user_updated_notification.delay',
    )
    mocker.patch(
        'src.accounts.services.user.transaction.on_commit',
        side_effect=lambda f: f(),
    )

    # act
    service.partial_update(subordinates=[report_a])

    # assert
    # partial_update (new_mgr) + _update_subordinates (report_a
    # + old_mgr) = 3
    assert send_mock.call_count == 3
    notified_ids = {
        call[1]['user_data']['id']
        for call in send_mock.call_args_list
    }
    assert old_mgr.id in notified_ids
    assert new_mgr.id in notified_ids
    assert report_a.id in notified_ids


def test_update_subordinates__same_mgr_report__skip_old_mgr_notify(mocker):
    # arrange
    account = create_test_account()
    account.log_api_requests = True
    account.save()
    manager = create_test_not_admin(
        account=account,
        email='mgr@test.test',
    )
    report_a = create_test_not_admin(
        account=account,
        email='a@test.test',
    )
    report_b = create_test_not_admin(
        account=account,
        email='b@test.test',
    )
    report_a.manager = manager
    report_a.save()
    manager.subordinates.set([report_a])

    owner = create_test_owner(account=account)
    service = UserService(instance=manager, user=owner)
    send_mock = mocker.patch(
        'src.accounts.services.user.'
        'send_user_updated_notification.delay',
    )
    mocker.patch(
        'src.accounts.services.user.transaction.on_commit',
        side_effect=lambda f: f(),
    )

    # act
    service.partial_update(subordinates=[report_a, report_b])

    # assert
    # partial_update (manager) + _update_subordinates (report_b) = 2
    # report_a is not changed, no old_mgr (manager == self.instance)
    assert send_mock.call_count == 2
    notified_ids = {
        call[1]['user_data']['id']
        for call in send_mock.call_args_list
    }
    assert notified_ids == {manager.id, report_b.id}


def test_deactivate_subs__clears_manager__ok(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    manager = create_test_not_admin(account=account)
    sub1 = create_test_not_admin(
        account=account,
        email='sub1@test.test',
    )
    sub2 = create_test_not_admin(
        account=account,
        email='sub2@test.test',
    )
    sub1.manager = manager
    sub1.save(update_fields=('manager',))
    sub2.manager = manager
    sub2.save(update_fields=('manager',))
    send_ws_mock = mocker.patch(
        'src.accounts.services.user'
        '.send_user_updated_notification.delay',
    )
    mocker.patch(
        'django.db.transaction.on_commit',
        side_effect=lambda func: func(),
    )
    service = UserService(
        user=owner,
        instance=manager,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )

    # act
    service._deactivate_subordinates()

    # assert
    sub1.refresh_from_db()
    sub2.refresh_from_db()
    assert sub1.manager is None
    assert sub2.manager is None
    assert send_ws_mock.call_count == 2


def test_deactivate_subs__no_subs__no_ws(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    user = create_test_not_admin(account=account)
    send_ws_mock = mocker.patch(
        'src.accounts.services.user'
        '.send_user_updated_notification.delay',
    )
    service = UserService(
        user=owner,
        instance=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )

    # act
    service._deactivate_subordinates()

    # assert
    send_ws_mock.assert_not_called()


def test_update_managers__both__notifies_both(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    old_mgr = create_test_not_admin(
        account=account,
        email='oldmgr@test.test',
    )
    new_mgr = create_test_not_admin(
        account=account,
        email='newmgr@test.test',
    )
    user = create_test_not_admin(
        account=account,
        email='target@test.test',
    )
    send_ws_mock = mocker.patch(
        'src.accounts.services.user'
        '.send_user_updated_notification.delay',
    )
    service = UserService(
        user=owner,
        instance=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )

    # act
    service._update_managers(
        old_manager=old_mgr,
        new_manager=new_mgr,
    )

    # assert
    assert send_ws_mock.call_count == 2


def test_update_managers__old_none__notifies_new(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    new_mgr = create_test_not_admin(
        account=account,
        email='newmgr@test.test',
    )
    user = create_test_not_admin(
        account=account,
        email='target@test.test',
    )
    send_ws_mock = mocker.patch(
        'src.accounts.services.user'
        '.send_user_updated_notification.delay',
    )
    service = UserService(
        user=owner,
        instance=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )

    # act
    service._update_managers(
        old_manager=None,
        new_manager=new_mgr,
    )

    # assert
    assert send_ws_mock.call_count == 1


def test_update_managers__both_none__no_ws(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    user = create_test_not_admin(account=account)
    send_ws_mock = mocker.patch(
        'src.accounts.services.user'
        '.send_user_updated_notification.delay',
    )
    service = UserService(
        user=owner,
        instance=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )

    # act
    service._update_managers(
        old_manager=None,
        new_manager=None,
    )

    # assert
    send_ws_mock.assert_not_called()


def test_update_subs__sets_new__ok(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    manager = create_test_not_admin(account=account)
    sub1 = create_test_not_admin(
        account=account,
        email='sub1@test.test',
    )
    sub2 = create_test_not_admin(
        account=account,
        email='sub2@test.test',
    )
    send_ws_mock = mocker.patch(
        'src.accounts.services.user'
        '.send_user_updated_notification.delay',
    )
    mocker.patch(
        'django.db.transaction.on_commit',
        side_effect=lambda func: func(),
    )
    service = UserService(
        user=owner,
        instance=manager,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )

    # act
    service._update_subordinates([sub1, sub2])

    # assert
    sub1.refresh_from_db()
    sub2.refresh_from_db()
    assert sub1.manager == manager
    assert sub2.manager == manager
    assert send_ws_mock.call_count >= 1


def test_update_subs__replaces__ok(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    manager = create_test_not_admin(account=account)
    old_sub = create_test_not_admin(
        account=account,
        email='oldsub@test.test',
    )
    new_sub = create_test_not_admin(
        account=account,
        email='newsub@test.test',
    )
    old_sub.manager = manager
    old_sub.save(update_fields=('manager',))
    mocker.patch(
        'src.accounts.services.user'
        '.send_user_updated_notification.delay',
    )
    service = UserService(
        user=owner,
        instance=manager,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )

    # act
    service._update_subordinates([new_sub])

    # assert
    old_sub.refresh_from_db()
    new_sub.refresh_from_db()
    assert old_sub.manager is None
    assert new_sub.manager == manager


def test_update_subs__empty__clears_all(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    manager = create_test_not_admin(account=account)
    sub = create_test_not_admin(
        account=account,
        email='sub@test.test',
    )
    sub.manager = manager
    sub.save(update_fields=('manager',))
    send_ws_mock = mocker.patch(
        'src.accounts.services.user'
        '.send_user_updated_notification.delay',
    )
    mocker.patch(
        'django.db.transaction.on_commit',
        side_effect=lambda func: func(),
    )
    service = UserService(
        user=owner,
        instance=manager,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )

    # act
    service._update_subordinates([])

    # assert
    sub.refresh_from_db()
    assert sub.manager is None
    assert send_ws_mock.call_count >= 1


def test_update_subs__from_other_mgr__notifies_all(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    old_mgr = create_test_not_admin(
        account=account,
        email='oldmgr@test.test',
    )
    new_mgr = create_test_not_admin(
        account=account,
        email='newmgr@test.test',
    )
    sub = create_test_not_admin(
        account=account,
        email='sub@test.test',
    )
    sub.manager = old_mgr
    sub.save(update_fields=('manager',))
    send_ws_mock = mocker.patch(
        'src.accounts.services.user'
        '.send_user_updated_notification.delay',
    )
    mocker.patch(
        'django.db.transaction.on_commit',
        side_effect=lambda func: func(),
    )
    service = UserService(
        user=owner,
        instance=new_mgr,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )

    # act
    service._update_subordinates([sub])

    # assert
    sub.refresh_from_db()
    assert sub.manager == new_mgr
    # sub + old_mgr = 2 (manager notified by caller)
    assert send_ws_mock.call_count == 2


def test_deactivate__clears_own_manager__ok(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    manager = create_test_not_admin(
        account=account,
        email='manager@test.test',
    )
    user = create_test_not_admin(
        account=account,
        email='target@test.test',
    )
    user.manager = manager
    user.save(update_fields=('manager',))
    mocker.patch(
        'src.accounts.services.user'
        '.send_user_updated_notification.delay',
    )
    mocker.patch(
        'src.accounts.services.user'
        '.send_user_deleted_notification.delay',
    )
    mocker.patch(
        'src.accounts.services.user'
        '.send_user_deactivated_notification.delay',
    )
    mocker.patch(
        'src.accounts.services.user.AnalyticService',
    )
    service = UserService(
        user=owner,
        instance=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )

    # act
    service.deactivate()

    # assert
    user.refresh_from_db()
    assert user.manager is None


def test_deactivate__clears_subordinates__ok(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    user = create_test_not_admin(account=account)
    sub = create_test_not_admin(
        account=account,
        email='sub@test.test',
    )
    sub.manager = user
    sub.save(update_fields=('manager',))
    mocker.patch(
        'src.accounts.services.user'
        '.send_user_updated_notification.delay',
    )
    mocker.patch(
        'src.accounts.services.user'
        '.send_user_deleted_notification.delay',
    )
    mocker.patch(
        'src.accounts.services.user'
        '.send_user_deactivated_notification.delay',
    )
    mocker.patch(
        'src.accounts.services.user.AnalyticService',
    )
    service = UserService(
        user=owner,
        instance=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )

    # act
    service.deactivate()

    # assert
    sub.refresh_from_db()
    assert sub.manager is None


def test_partial_update__mgr_and_subs__mgr_ws_after_subs(
    mocker,
):
    """When both manager and subordinates change in one
    partial_update call, manager WS notifications must fire
    *after* _update_subordinates completes, so their payloads
    include fresh subordinate data."""

    # arrange
    account = create_test_account()
    account.log_api_requests = True
    account.save()
    old_mgr = create_test_not_admin(
        account=account,
        email='old@test.test',
    )
    new_mgr = create_test_not_admin(
        account=account,
        email='new@test.test',
    )
    user = create_test_not_admin(
        account=account,
        email='user@test.test',
    )
    user.manager = old_mgr
    user.save()
    report = create_test_not_admin(
        account=account,
        email='report@test.test',
    )

    owner = create_test_owner(account=account)
    service = UserService(instance=user, user=owner)

    call_order = []
    real_update_subs = service._update_subordinates
    real_update_mgrs = service._update_managers

    def tracked_update_subs(*a, **kw):
        call_order.append('subordinates')
        return real_update_subs(*a, **kw)

    def tracked_update_mgrs(*a, **kw):
        call_order.append('managers')
        return real_update_mgrs(*a, **kw)

    mocker.patch.object(
        service, '_update_subordinates',
        side_effect=tracked_update_subs,
    )
    mocker.patch.object(
        service, '_update_managers',
        side_effect=tracked_update_mgrs,
    )
    mocker.patch(
        'src.accounts.services.user.'
        'send_user_updated_notification.delay',
    )
    mocker.patch(
        'src.accounts.services.user.transaction.on_commit',
        side_effect=lambda f: f(),
    )

    # act
    service.partial_update(
        manager=new_mgr,
        subordinates=[report],
    )

    # assert
    assert call_order == ['subordinates', 'managers']


def test_validate_manager__ok():
    """Valid manager assignment does not raise."""
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    user = create_test_not_admin(account=account)
    manager = create_test_not_admin(
        account=account, email='mgr@test.test',
    )
    service = UserService(instance=user, user=owner)

    # act / assert — no exception
    service._validate_manager(manager)


def test_validate_manager__self_assignment__error():
    """A user cannot be their own manager."""
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    user = create_test_not_admin(account=account)
    service = UserService(instance=user, user=owner)

    # act
    with pytest.raises(UserServiceException) as ex:
        service._validate_manager(user)

    # assert
    assert ex.value.message == str(messages.MSG_A_0055)


def test_validate_manager__circular__error():
    """Direct cycle: manager.manager = user → assigning
    user.manager = manager creates a loop."""
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    user = create_test_not_admin(account=account)
    manager = create_test_not_admin(
        account=account, email='mgr@test.test',
    )
    manager.manager = user
    manager.save(update_fields=('manager',))
    service = UserService(instance=user, user=owner)

    # act
    with pytest.raises(UserServiceException) as ex:
        service._validate_manager(manager)

    # assert
    assert ex.value.message == str(messages.MSG_A_0056)


def test_validate_manager__deep_chain__error():
    """Cycle detection works for a 3-level chain
    (A->B->C, assigning C as A's manager)."""
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    user_a = create_test_not_admin(
        account=account, email='a@test.test',
    )
    user_b = create_test_not_admin(
        account=account, email='b@test.test',
    )
    user_c = create_test_not_admin(
        account=account, email='c@test.test',
    )
    user_b.manager = user_a
    user_b.save(update_fields=('manager',))
    user_c.manager = user_b
    user_c.save(update_fields=('manager',))
    service = UserService(instance=user_a, user=owner)

    # act
    with pytest.raises(UserServiceException) as ex:
        service._validate_manager(user_c)

    # assert
    assert ex.value.message == str(messages.MSG_A_0056)


def test_validate_manager__inactive_in_chain__ok():
    """Inactive users are excluded from the manager map,
    so stale manager_id on an inactive user does not cause
    a false-positive cycle."""
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    user_a = create_test_not_admin(
        account=account, email='a@test.test',
    )
    user_b = create_test_not_admin(
        account=account, email='b@test.test',
    )
    inactive = create_test_not_admin(
        account=account, email='inactive@test.test',
    )
    inactive.manager = user_a
    inactive.save(update_fields=('manager',))
    inactive.status = UserStatus.INACTIVE
    inactive.is_active = False
    inactive.save(update_fields=('status', 'is_active'))
    service = UserService(instance=user_a, user=owner)

    # act / assert — no exception
    service._validate_manager(user_b)


def test_validate_subordinates__ok():
    """Valid subordinate list does not raise."""
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    user = create_test_not_admin(account=account)
    sub = create_test_not_admin(
        account=account, email='sub@test.test',
    )
    service = UserService(instance=user, user=owner)

    # act / assert — no exception
    service._validate_subordinates([sub])


def test_validate_subordinates__self__error():
    """A user cannot be their own subordinate."""
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    user = create_test_not_admin(account=account)
    service = UserService(instance=user, user=owner)

    # act
    with pytest.raises(UserServiceException) as ex:
        service._validate_subordinates([user])

    # assert
    assert ex.value.message == str(messages.MSG_A_0055)


def test_validate_subordinates__ancestor__error():
    """Assigning an ancestor as subordinate → cycle error."""
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    ancestor = create_test_not_admin(
        account=account, email='anc@test.test',
    )
    user = create_test_not_admin(account=account)
    user.manager = ancestor
    user.save(update_fields=('manager',))
    service = UserService(instance=user, user=owner)

    # act
    with pytest.raises(UserServiceException) as ex:
        service._validate_subordinates(
            [ancestor], user.manager,
        )

    # assert
    assert ex.value.message == str(messages.MSG_A_0056)


def test_validate_subordinates__proposed_mgr_none__ok():
    """When proposed manager is None and old manager is
    assigned as subordinate, the result is non-cyclic and
    must be accepted."""
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    ancestor = create_test_not_admin(
        account=account, email='anc@test.test',
    )
    user = create_test_not_admin(account=account)
    user.manager = ancestor
    user.save(update_fields=('manager',))
    service = UserService(instance=user, user=owner)

    # act / assert — manager=None breaks the old chain,
    # so [ancestor] is a valid subordinate
    service._validate_subordinates(
        [ancestor], None,
    )


def test_validate_subordinates__proposed_mgr_fresh_map():
    """_validate_subordinates uses proposed_manager to patch
    the in-memory map, fixing the stale-cache problem."""
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    user = create_test_not_admin(account=account)
    new_mgr = create_test_not_admin(
        account=account, email='newmgr@test.test',
    )
    # new_mgr has no higher ancestors, so assigning it as
    # manager and its former subordinate as user's sub is
    # safe.
    sub = create_test_not_admin(
        account=account, email='sub@test.test',
    )
    service = UserService(instance=user, user=owner)

    # act / assert — no exception
    service._validate_subordinates(
        [sub], new_mgr,
    )
