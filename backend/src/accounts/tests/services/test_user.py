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
from src.accounts.messages import MSG_A_0005
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
    create_test_workflow,
)

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
        'src.accounts.services.user.make_password',
        return_value=safe_password,
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
        'src.accounts.services.user.UserModel.'
        'objects.make_random_password',
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
        'src.accounts.services.user.UserModel.'
        'objects.make_random_password',
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
        'src.accounts.services.user.UserModel.'
        'objects.make_random_password',
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
        'src.accounts.services.user.UserModel.'
        'objects.make_random_password',
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
        'src.accounts.services.user.UserModel.'
        'objects.make_random_password',
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
        'src.accounts.services.user.UserModel.'
        'objects.make_random_password',
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
    assert ex.value.message == MSG_A_0005


def test_create_instance__invited_email_exists__ok(mocker):

    # arrange
    account = create_test_account()
    create_test_user(account=account, is_account_owner=True)
    email = 'test@test.test'
    password = '12112323'
    mocker.patch(
        'src.accounts.services.user.UserModel.'
        'objects.make_random_password',
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
        'src.accounts.services.user.UserModel.'
        'objects.make_random_password',
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
        'src.accounts.services.user.UserModel.'
        'objects.make_random_password',
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
        'src.accounts.services.user.UserModel.'
        'objects.make_random_password',
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


def test_create_related__ok(mocker):

    # arrange
    user = create_test_user()
    user.account.accountsignupdata_set.get().delete()
    key = '!@#q2qwe'
    create_token_mock = mocker.patch(
        'src.accounts.services.user.PneumaticToken.create',
        return_value=key,
    )

    service = UserService(instance=user)

    # act
    service._create_related()

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
        'src.accounts.services.user'
        '.AnalyticService.account_created',
    )
    account_verified_mock = mocker.patch(
        'src.accounts.services.user'
        '.AnalyticService.account_verified',
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
        'src.accounts.services.user'
        '.AnalyticService.account_created',
    )
    account_verified_mock = mocker.patch(
        'src.accounts.services.user'
        '.AnalyticService.account_verified',
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
    assert email == f'{local}+{number+1}@{domain}'


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
        'src.accounts.services.user'
        '.UserService._get_free_email',
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
        'src.accounts.services.user'
        '.UserService._get_free_email',
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
        'src.accounts.services.user'
        '.UserService._get_free_email',
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
        'src.accounts.services.user'
        '.UserService.create',
        return_value=tenant_account_owner,
    )
    incremented_email = 'test+1@test.com'
    get_incremented_email_mock = mocker.patch(
        'src.accounts.services.user'
        '.UserService._get_incremented_email',
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


def test_deactivate__ok(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    deleted_user = create_test_admin(account=account)

    deactivate_mock = mocker.patch(
        'src.accounts.services.user.UserService.'
        '_deactivate',
    )
    deactivate_actions_mock = mocker.patch(
        'src.accounts.services.user.UserService'
        '._deactivate_actions',
    )
    validate_deactivate_mock = mocker.patch(
        'src.accounts.services.user.UserService'
        '._validate_deactivate',
    )
    send_user_deleted_mock = mocker.patch(
        'src.notifications.tasks.'
        'send_user_deleted_notification.delay',
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
        },
    )


def test_deactivate__skip_validation__ok(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    deleted_user = create_test_admin(account=account)

    deactivate_mock = mocker.patch(
        'src.accounts.services.user.UserService.'
        '_deactivate',
    )
    deactivate_actions_mock = mocker.patch(
        'src.accounts.services.user.UserService'
        '._deactivate_actions',
    )
    validate_deactivate_mock = mocker.patch(
        'src.accounts.services.user.UserService'
        '._validate_deactivate',
    )
    send_user_deleted_mock = mocker.patch(
        'src.notifications.tasks.'
        'send_user_deleted_notification.delay',
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
        },
    )


def test_deactivate__not_call_actions_for_invited_user__ok(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    invited_user = create_invited_user(owner)
    validate_deactivate_mock = mocker.patch(
        'src.accounts.services.user.UserService'
        '._validate_deactivate',
    )
    deactivate_mock = mocker.patch(
        'src.accounts.services.user.UserService.'
        '_deactivate',
    )
    deactivate_actions_mock = mocker.patch(
        'src.accounts.services.user.UserService'
        '._deactivate_actions',
    )
    send_user_deleted_mock = mocker.patch(
        'src.notifications.tasks.'
        'send_user_deleted_notification.delay',
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
        },
    )


def test_private_deactivate__ok(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    deleted_user = create_test_admin(account=account)
    remove_user_from_draft_mock = mocker.patch(
        'src.accounts.services.user.'
        'remove_user_from_draft',
    )
    update_users_counts_mock = mocker.patch(
        'src.accounts.services.account.AccountService.'
        'update_users_counts',
    )
    identify_mock = mocker.patch(
        'src.accounts.services.user.UserService.'
        'identify',
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
        'src.accounts.services.user.'
        'remove_user_from_draft',
    )
    mocker.patch(
        'src.accounts.services.account.AccountService.'
        'update_users_counts',
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

    another_user = create_test_owner()
    workflow = create_test_workflow(user=another_user, tasks_count=1)
    task = workflow.tasks.get(number=1)
    user_field = TaskField.objects.create(
        task=task,
        type=FieldType.USER,
        workflow=workflow,
        value=old_name,
        user_id=another_user.id,
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
        'src.payment.stripe.service.StripeService.'
        'update_customer',
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
        'src.payment.stripe.service.StripeService.'
        'update_customer',
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
        'src.payment.stripe.service.StripeService.'
        'update_customer',
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
        'src.payment.stripe.service.StripeService.'
        'update_customer',
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
        'src.payment.stripe.service.StripeService.'
        'update_customer',
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
    partial_update_mock = mocker.patch(
        'src.generics.base.service.BaseModelService.partial_update',
    )
    update_related_user_fields_mock = mocker.patch(
        'src.accounts.services.user.UserService.'
        '_update_related_user_fields',
    )
    update_related_stripe_account_mock = mocker.patch(
        'src.accounts.services.user.UserService.'
        '_update_related_stripe_account',
    )
    update_analytics_mock = mocker.patch(
        'src.accounts.services.user.UserService.'
        '_update_analytics',
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
        force_save=False,
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
        'src.accounts.services.user.UserService.'
        '_update_related_user_fields',
    )
    update_related_stripe_account_mock = mocker.patch(
        'src.accounts.services.user.UserService.'
        '_update_related_stripe_account',
    )
    update_analytics_mock = mocker.patch(
        'src.accounts.services.user.UserService.'
        '_update_analytics',
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
