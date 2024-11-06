import pytest
from django.contrib.auth.hashers import check_password
from pneumatic_backend.accounts.models import (
    UserInvite,
    APIKey,
    Contact,
)
from pneumatic_backend.authentication.enums import AuthTokenType
from pneumatic_backend.accounts.enums import (
    UserStatus,
    LeaseLevel,
    SourceType,
    Language,
    UserDateFormat,
    UserFirstDayWeek,
)
from pneumatic_backend.processes.tests.fixtures import (
    create_test_user,
    create_test_account,
    create_test_guest,
)
from pneumatic_backend.processes.tests.fixtures import (
    create_invited_user,
)
from pneumatic_backend.accounts.services.exceptions import (
    UserIsPerformerException,
    AlreadyRegisteredException,
)
from pneumatic_backend.accounts.services import (
    UserService
)
from pneumatic_backend.accounts.messages import MSG_A_0005


pytestmark = pytest.mark.django_db


def test_create_instance__all_fields__ok(mocker):

    # arrange
    account = create_test_account()
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
        'pneumatic_backend.accounts.services.user.make_password',
        return_value=safe_password
    )
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
        'pneumatic_backend.accounts.services.user.UserModel.'
        'objects.make_random_password',
        return_value=random_password
    )
    safe_password = 'some safe password'
    make_password_mock = mocker.patch(
        'pneumatic_backend.accounts.services.user.make_password',
        return_value=safe_password
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


def test_create_instance__not_account_owner___ok(mocker):

    # arrange
    account = create_test_account()
    language_owner = Language.fr
    tz_owner = 'Atlantic/Faeroe'
    date_fmt_owner = UserDateFormat.PY_EUROPE_24
    date_fdw_owner = UserFirstDayWeek.SATURDAY
    safe_password = 'some safe password'
    make_password_mock = mocker.patch(
        'pneumatic_backend.accounts.services.user.make_password',
        return_value=safe_password
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
        'pneumatic_backend.accounts.services.user.UserModel.'
        'objects.make_random_password',
    )
    make_password_mock = mocker.patch(
        'pneumatic_backend.accounts.services.user.make_password',
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
        'pneumatic_backend.accounts.services.user.UserModel.'
        'objects.make_random_password'
    )
    mocker.patch(
        'pneumatic_backend.accounts.services.user.make_password'
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
    assert ex.value.message == MSG_A_0005


def test_create_instance__invited_email_exists__ok(mocker):

    # arrange
    account = create_test_account()
    create_test_user(account=account, is_account_owner=True)
    email = 'test@test.test'
    password = '12112323'
    mocker.patch(
        'pneumatic_backend.accounts.services.user.UserModel.'
        'objects.make_random_password'
    )
    mocker.patch(
        'pneumatic_backend.accounts.services.user.make_password'
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
        'pneumatic_backend.accounts.services.user.UserModel.'
        'objects.make_random_password'
    )
    mocker.patch(
        'pneumatic_backend.accounts.services.user.make_password'
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
        'pneumatic_backend.accounts.services.user.UserModel.'
        'objects.make_random_password'
    )
    mocker.patch(
        'pneumatic_backend.accounts.services.user.make_password'
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
        account=account
    )
    email = 'test@test.test'
    password = '12112323'
    mocker.patch(
        'pneumatic_backend.accounts.services.user.UserModel.'
        'objects.make_random_password'
    )
    mocker.patch(
        'pneumatic_backend.accounts.services.user.make_password'
    )
    create_test_guest(
        email=email,
        account=account
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
       'pneumatic_backend.accounts.services.user.settings'
    )
    language = Language.fr
    settings_mock.LANGUAGE_CODE = language
    settings_mock.TIME_ZONE = 'UTC'

    # act
    user = service._create_instance(
        is_account_owner=True,
        account=account,
        email=email,
        password=password
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
        language=language
    )
    email = 'test@test.test'
    password = '12123'
    service = UserService()

    # act
    user = service._create_instance(
        is_account_owner=False,
        account=account,
        email=email,
        password=password
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
       'pneumatic_backend.accounts.services.user.settings'
    )
    tz = 'Atlantic/Faeroe'
    settings_mock.LANGUAGE_CODE = Language.fr
    settings_mock.TIME_ZONE = tz

    # act
    user = service._create_instance(
        is_account_owner=True,
        account=account,
        email=email,
        password=password
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
        tz=tz
    )
    email = 'test@test.test'
    password = '12123'
    service = UserService()

    # act
    user = service._create_instance(
        is_account_owner=False,
        account=account,
        email=email,
        password=password
    )

    # assert
    assert user.account == account
    assert user.email == email
    assert user.timezone == tz


def test_create_related__ok(mocker):

    # arrange
    user = create_test_user()
    user.account.accountsignupdata_set.get().delete()
    key = '!@#q2qwe'
    create_token_mock = mocker.patch(
        'pneumatic_backend.accounts.services.user.PneumaticToken.create',
        return_value=key
    )

    service = UserService(instance=user)

    # act
    service._create_related()

    # arrange
    assert APIKey.objects.get(
        user=user,
        name=user.get_full_name(),
        account=user.account,
        key=key
    )
    create_token_mock.assert_called_once_with(
        user=user,
        for_api_key=True
    )


def test_create_actions__account_owner__ok(
    mocker,
    identify_mock,
    group_mock
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
        invited_user=user
    )
    is_superuser = True
    auth_type = AuthTokenType.API
    account_created_mock = mocker.patch(
        'pneumatic_backend.accounts.services.user'
        '.AnalyticService.account_created'
    )
    account_verified_mock = mocker.patch(
        'pneumatic_backend.accounts.services.user'
        '.AnalyticService.account_verified'
    )

    service = UserService(
        instance=user,
        auth_type=auth_type,
        is_superuser=is_superuser
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
    group_mock
):

    # arrange
    account = create_test_account()
    account.is_verified = False
    account.save()
    user = create_test_user(account=account)
    is_superuser = True
    auth_type = AuthTokenType.API
    account_created_mock = mocker.patch(
        'pneumatic_backend.accounts.services.user'
        '.AnalyticService.account_created'
    )
    account_verified_mock = mocker.patch(
        'pneumatic_backend.accounts.services.user'
        '.AnalyticService.account_verified'
    )

    service = UserService(
        instance=user,
        auth_type=auth_type,
        is_superuser=is_superuser
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
        domain=domain
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
        domain=domain
    )

    # assert
    assert email == f'{local}+{number+1}@{domain}'


def test_get_free_email__invited_user_already_exist__increment_number():

    # arrange
    local = 'admin'
    number = 1
    domain = 'test.com'
    create_test_user(
        status=UserStatus.INVITED,
        email=f'{local}+{number}@{domain}'
    )
    user = create_test_user()
    service = UserService(instance=user)

    # act
    email = service._get_free_email(
        local=local,
        number=number,
        domain=domain
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
        email=f'{local}+{number}@{domain}'
    )
    create_test_user(
        status=UserStatus.INACTIVE,
        email=f'{local}+{number}@{domain}'
    )
    user = create_test_user()
    service = UserService(instance=user)

    # act
    email = service._get_free_email(
        local=local,
        number=number,
        domain=domain
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
        email=f'{local}+{number}@{domain}'
    )
    user = create_test_user()
    service = UserService(instance=user)

    # act
    email = service._get_free_email(
        local=local,
        number=number,
        domain=domain
    )

    # assert
    assert email == f'{local}+{number + 1}@{domain}'


def test_get_free_email__deleted_user_already_exist__not_increment_number():

    # arrange
    local = 'admin'
    number = 1
    domain = 'test.com'
    deleted_user = create_test_user(
        email=f'{local}+{number}@{domain}'
    )
    deleted_user.delete()
    user = create_test_user()
    service = UserService(instance=user)

    # act
    email = service._get_free_email(
        local=local,
        number=number,
        domain=domain
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
        email=f'{local}+{number}@{domain}'
    )
    service = UserService(instance=user)

    # act
    email = service._get_free_email(
        local=local,
        number=number,
        domain=domain
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
        'pneumatic_backend.accounts.services.user'
        '.UserService._get_free_email',
        return_value=incremented_email
    )

    service = UserService(instance=user)

    # act
    result = service._get_incremented_email(user=user)

    # assert
    assert result == incremented_email
    get_free_email_mock.assert_called_once_with(
        local=local,
        number=number,
        domain=domain
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
        'pneumatic_backend.accounts.services.user'
        '.UserService._get_free_email',
        return_value=incremented_email
    )

    service = UserService(instance=user)

    # act
    result = service._get_incremented_email(user=user)

    # assert
    assert result == incremented_email
    get_free_email_mock.assert_called_once_with(
        local=local,
        number=number,
        domain=domain
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
        'pneumatic_backend.accounts.services.user'
        '.UserService._get_free_email',
        return_value=incremented_email
    )

    service = UserService(instance=user)

    # act
    result = service._get_incremented_email(user=user)

    # assert
    assert result == incremented_email
    get_free_email_mock.assert_called_once_with(
        local=local,
        number=number,
        domain=domain
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
        lease_level=LeaseLevel.TENANT
    )
    tenant_account_owner = mocker.Mock()
    create_mock = mocker.patch(
        'pneumatic_backend.accounts.services.user'
        '.UserService.create',
        return_value=tenant_account_owner
    )
    incremented_email = 'test+1@test.com'
    get_incremented_email_mock = mocker.patch(
        'pneumatic_backend.accounts.services.user'
        '.UserService._get_incremented_email',
        return_value=incremented_email
    )
    service = UserService()

    # act
    result = service.create_tenant_account_owner(
        tenant_account=tenant_account,
        master_account=master_account_owner.account
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
        is_account_owner=True
    )
    get_incremented_email_mock.assert_called_once_with(master_account_owner)


def test_validate_deactivate__user_is_performer__raise_exception(mocker):

    # arrange
    user = create_test_user()
    user_is_performer_mock = mocker.patch(
        'pneumatic_backend.accounts.services.user.user_is_performer',
        return_value=True
    )

    # act
    with pytest.raises(UserIsPerformerException):
        UserService._validate_deactivate(user)

    # assert
    user_is_performer_mock.assert_called_once_with(user)


def test_validate_deactivate__user_is_not_performer__ok(mocker):

    # arrange
    user = create_test_user()
    user_is_performer_mock = mocker.patch(
        'pneumatic_backend.accounts.services.user.user_is_performer',
        return_value=False
    )

    # act
    UserService._validate_deactivate(user)

    # assert
    user_is_performer_mock.assert_called_once_with(user)


def test_deactivate__ok(mocker):

    # arrange
    user = create_test_user()

    deactivate_mock = mocker.patch(
        'pneumatic_backend.accounts.services.user.UserService.'
        '_deactivate'
    )
    deactivate_actions_mock = mocker.patch(
        'pneumatic_backend.accounts.services.user.UserService'
        '._deactivate_actions'
    )
    validate_deactivate_mock = mocker.patch(
        'pneumatic_backend.accounts.services.user.UserService'
        '._validate_deactivate'
    )

    # act
    UserService.deactivate(user)

    # assert
    validate_deactivate_mock.assert_called_once_with(user)
    deactivate_mock.assert_called_once_with(user)
    deactivate_actions_mock.assert_called_once_with(user)


def test_deactivate__skip_validation__ok(mocker):

    # arrange
    user = create_test_user()

    deactivate_mock = mocker.patch(
        'pneumatic_backend.accounts.services.user.UserService.'
        '_deactivate'
    )
    deactivate_actions_mock = mocker.patch(
        'pneumatic_backend.accounts.services.user.UserService'
        '._deactivate_actions'
    )
    validate_deactivate_mock = mocker.patch(
        'pneumatic_backend.accounts.services.user.UserService'
        '._validate_deactivate'
    )

    # act
    UserService.deactivate(user, skip_validation=True)

    # assert
    validate_deactivate_mock.assert_not_called()
    deactivate_mock.assert_called_once_with(user)
    deactivate_actions_mock.assert_called_once_with(user)


def test_deactivate__not_call_actions_for_invited_user__ok(mocker):

    # arrange
    user = create_test_user()
    invited_user = create_invited_user(user)
    validate_deactivate_mock = mocker.patch(
        'pneumatic_backend.accounts.services.user.UserService'
        '._validate_deactivate'
    )
    deactivate_mock = mocker.patch(
        'pneumatic_backend.accounts.services.user.UserService.'
        '_deactivate'
    )
    deactivate_actions_mock = mocker.patch(
        'pneumatic_backend.accounts.services.user.UserService'
        '._deactivate_actions'
    )

    # act
    UserService.deactivate(invited_user)

    # assert
    validate_deactivate_mock.assert_called_once_with(invited_user)
    deactivate_mock.assert_called_once_with(invited_user)
    deactivate_actions_mock.assert_not_called()


def test_private_deactivate__ok(mocker):

    # arrange
    account = create_test_account()
    user = create_test_user(account=account)
    invited_user = create_invited_user(user)
    remove_user_from_draft_mock = mocker.patch(
        'pneumatic_backend.accounts.services.user.'
        'remove_user_from_draft'
    )
    update_users_counts_mock = mocker.patch(
        'pneumatic_backend.accounts.services.AccountService.'
        'update_users_counts'
    )
    identify_mock = mocker.patch(
        'pneumatic_backend.accounts.services.user.UserService.'
        'identify'
    )

    # act
    UserService._deactivate(invited_user)

    # assert
    invited_user.refresh_from_db()
    assert not invited_user.incoming_invites.exists()
    assert invited_user.status == UserStatus.INACTIVE
    assert invited_user.is_active is False
    remove_user_from_draft_mock.assert_called_once_with(
        user_id=invited_user.id,
        account_id=account.id
    )
    update_users_counts_mock.assert_called_once()
    identify_mock.assert_called_once_with(invited_user)


def test_private_deactivate__activate_contacts__ok(mocker):

    # arrange
    account = create_test_account()
    user = create_test_user(account=account)
    invited_user = create_invited_user(user)
    another_user = create_test_user(
        account=account,
        email='another@email.com',
        is_account_owner=False
    )
    another_account_user = create_test_user(
        email='anotheraccount@email.com',
    )
    mocker.patch(
        'pneumatic_backend.accounts.services.user.'
        'remove_user_from_draft'
    )
    mocker.patch(
        'pneumatic_backend.accounts.services.AccountService.'
        'update_users_counts'
    )
    mocker.patch(
        'pneumatic_backend.accounts.services.user.UserService.'
        'identify'
    )
    google_contact = Contact.objects.create(
        account=account,
        user_id=user.id,
        source=SourceType.GOOGLE,
        email=invited_user.email
    )
    ms_contact = Contact.objects.create(
        account=account,
        user_id=user.id,
        source=SourceType.MICROSOFT,
        email=invited_user.email
    )
    another_user_contact = Contact.objects.create(
        account=account,
        user_id=another_user.id,
        source=SourceType.MICROSOFT,
        email=invited_user.email
    )
    another_account_contact = Contact.objects.create(
        account=another_account_user.account,
        user_id=another_account_user.id,
        source=SourceType.GOOGLE,
        email=invited_user.email
    )
    another_contact = Contact.objects.create(
        account=account,
        user_id=user.id,
        source=SourceType.MICROSOFT,
        email='another@email.com'
    )

    # act
    UserService._deactivate(invited_user)

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
    user = create_test_user()
    send_user_deactivated_email_mock = mocker.patch(
        'pneumatic_backend.services.email.EmailService.'
        'send_user_deactivated_email'
    )

    # act
    UserService._deactivate_actions(user)

    # assert
    send_user_deactivated_email_mock.assert_called_once_with(user=user)


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
    assert not new_password == user.password
