import pytest
import pytz
from django.contrib.auth import get_user_model
from pneumatic_backend.accounts.models import (
    Contact,
    APIKey,
)
from pneumatic_backend.accounts.enums import (
    BillingPlanType,
    UserStatus,
    SourceType,
    Language,
    UserDateFormat,
    UserFirstDayWeek,
    Timezone,
    UserInviteStatus,
)
from pneumatic_backend.processes.tests.fixtures import (
    create_test_user,
    create_test_account,
    create_test_workflow,
    create_test_group,
)
from pneumatic_backend.accounts.tests.fixtures import (
    create_invited_user,
)
from pneumatic_backend.accounts.services.exceptions import (
    UserNotFoundException,
    AlreadyAcceptedInviteException,
    UsersLimitInvitesException,
)
from pneumatic_backend.accounts.tokens import (
    TransferToken,
    InviteToken,
)
from pneumatic_backend.accounts.services import (
    UserInviteService,
    AccountService,
)
from pneumatic_backend.accounts.entities import InviteData
from pneumatic_backend.processes.api_v2.services.system_workflows import (
    SystemWorkflowService
)

pytestmark = pytest.mark.django_db
UserModel = get_user_model()


def test__init_service__ok():

    # arrange
    account = create_test_account()
    request_user = create_test_user(account=account)
    current_url = 'http://current.test'
    is_superuser = False

    # act
    service = UserInviteService(
        current_url=current_url,
        is_superuser=is_superuser,
        request_user=request_user
    )

    # assert
    assert service.account is account
    assert service.current_url == current_url
    assert service.request_user == request_user
    assert service.is_superuser == is_superuser


def test_get_invite_token():

    # arrange
    account = create_test_account()
    request_user = create_test_user(account=account)
    invited_user = create_invited_user(request_user)
    current_url = 'http://current.test'
    is_superuser = False
    service = UserInviteService(
        current_url=current_url,
        is_superuser=is_superuser,
        request_user=request_user
    )

    # act
    token_str = service._get_invite_token(invited_user)

    # assert
    token = InviteToken(token_str)
    assert token['user_id'] == invited_user.id


def test_get_transfer_token():

    # arrange
    account = create_test_account()
    request_user = create_test_user(account=account)
    invited_user = create_invited_user(request_user)
    user_to_transfer = create_test_user(
        email='transfer@test.test'
    )
    current_url = 'http://current.test'
    is_superuser = False
    service = UserInviteService(
        current_url=current_url,
        is_superuser=is_superuser,
        request_user=request_user
    )

    # act
    token_str = service._get_transfer_token(
        current_account_user=invited_user,
        another_account_user=user_to_transfer
    )

    # assert
    token = TransferToken(token_str)
    assert token['new_user_id'] == invited_user.id
    assert token['prev_user_id'] == user_to_transfer.id


def test_create_invited_user__ok():

    # arrange
    account = create_test_account()
    language = Language.de
    timezone = pytz.timezone('Atlantic/Faeroe')
    date_fmt = UserDateFormat.PY_EUROPE_24
    date_fdw = UserFirstDayWeek.SATURDAY
    account_owner = create_test_user(
        account=account,
        is_account_owner=True,
        email='owner@test.test',
        tz=str(timezone),
        language=language,
        date_fmt=date_fmt,
        date_fdw=date_fdw,
    )
    request_user = create_test_user(
        account=account,
        is_account_owner=False
    )
    current_url = 'http://current.test'
    is_superuser = False
    email = 'invited@test.test'
    first_name = 'first_name'
    last_name = 'last_name'
    photo = 'http://my.lovely.photo.png'
    service = UserInviteService(
        current_url=current_url,
        is_superuser=is_superuser,
        request_user=request_user
    )

    # act
    user = service._create_invited_user(
        email=email,
        first_name=first_name,
        last_name=last_name,
        photo=photo
    )

    # assert
    assert user.email == email
    assert user.password == ''
    assert user.first_name == first_name.title()
    assert user.last_name == last_name.title()
    assert user.photo == photo
    assert user.account_id == account.id
    assert user.status == UserStatus.INVITED
    assert user.is_active is False
    assert user.is_admin is True
    assert user.language == account_owner.language
    assert user.date_fmt == account_owner.date_fmt
    assert user.date_fdw == account_owner.date_fdw
    assert user.timezone == account_owner.timezone


def test_create_invited_user__transfer__ok():

    # arrange
    account = create_test_account()
    language = Language.fr
    timezone = pytz.timezone('UTC')
    date_fmt = UserDateFormat.PY_EUROPE_24
    date_fdw = UserFirstDayWeek.SATURDAY
    account_owner = create_test_user(
        account=account,
        is_account_owner=True,
        email='owner@test.test',
        tz=str(timezone),
        language=language,
        date_fmt=date_fmt,
        date_fdw=date_fdw,
    )
    request_user = create_test_user(
        account=account,
        is_account_owner=False
    )
    user_to_transfer = create_test_user(
        email='transfer@test.test'
    )
    user_to_transfer.password = '123'
    user_to_transfer.save()
    current_url = 'http://current.test'
    is_superuser = False
    service = UserInviteService(
        current_url=current_url,
        is_superuser=is_superuser,
        request_user=request_user
    )

    # act
    user = service._create_invited_user(
        email=user_to_transfer.email,
        password=user_to_transfer.password
    )

    # assert
    assert user.email == user_to_transfer.email
    assert user.password == user_to_transfer.password
    assert UserModel.objects.get_by_natural_key(
        user_to_transfer.email
    ).id == user_to_transfer.id
    assert user.timezone == account_owner.timezone
    assert user.language == account_owner.language
    assert user.date_fmt == account_owner.date_fmt
    assert user.date_fdw == account_owner.date_fdw


def test_get_another_account_user__ok():

    account = create_test_account()
    request_user = create_test_user(account=account)
    user_to_transfer = create_test_user(
        email='transfer@test.test'
    )
    current_url = 'http://current.test'
    is_superuser = False
    service = UserInviteService(
        current_url=current_url,
        is_superuser=is_superuser,
        request_user=request_user
    )

    # act
    user = service._get_another_account_user(user_to_transfer.email)

    # assert
    assert user.id == user_to_transfer.id


def test_get_another_account_user__from_current_account__return_none():

    account = create_test_account()
    request_user = create_test_user(account=account)
    another_user = create_test_user(
        account=account,
        email='another@test.test'
    )
    current_url = 'http://current.test'
    is_superuser = False
    service = UserInviteService(
        current_url=current_url,
        is_superuser=is_superuser,
        request_user=request_user
    )

    # act
    user = service._get_another_account_user(another_user.email)

    # assert
    assert user is None


@pytest.mark.parametrize('status', UserStatus.NOT_ACTIVE)
def test_get_another_account_user__not_active_status__return_none(status):
    account = create_test_account()
    request_user = create_test_user(account=account)
    user_to_transfer = create_test_user(
        email='transfer@test.test'
    )
    user_to_transfer.status = status
    user_to_transfer.save()
    current_url = 'http://current.test'
    is_superuser = False
    service = UserInviteService(
        current_url=current_url,
        is_superuser=is_superuser,
        request_user=request_user
    )

    # act
    user = service._get_another_account_user(user_to_transfer.email)

    # assert
    assert user is None


def test_get_account_user__another_account__return_none():

    account = create_test_account()
    request_user = create_test_user(account=account)
    another_invited_user = create_test_user(
        email='another@test.test'
    )
    current_url = 'http://current.test'
    is_superuser = False
    service = UserInviteService(
        current_url=current_url,
        is_superuser=is_superuser,
        request_user=request_user
    )

    # act
    user = service._get_account_user(another_invited_user.email)

    # assert
    assert user is None


def test_get_account_user__ok():
    account = create_test_account()
    request_user = create_test_user(account=account)
    invited_user = create_invited_user(user=request_user)
    current_url = 'http://current.test'
    is_superuser = False
    service = UserInviteService(
        current_url=current_url,
        is_superuser=is_superuser,
        request_user=request_user
    )

    # act
    user = service._get_account_user(invited_user.email)

    # assert
    assert user.id == invited_user.id


def test_create_user_invite__ok():

    # arrange
    request_user = create_test_user()
    current_url = 'http://current.test'
    is_superuser = False
    invited_user = create_invited_user(user=request_user)
    invited_user.incoming_invites.delete()
    service = UserInviteService(
        current_url=current_url,
        is_superuser=is_superuser,
        request_user=request_user
    )

    # act
    service._create_user_invite(
        user=invited_user,
        invited_from=SourceType.EMAIL
    )

    # assert
    assert invited_user.incoming_invites.count() == 1
    user_invite = invited_user.incoming_invites.first()
    assert user_invite.account_id == invited_user.account_id
    assert user_invite.email == invited_user.email
    assert user_invite.invited_by == request_user
    assert user_invite.invited_from == SourceType.EMAIL


@pytest.mark.parametrize('plan', BillingPlanType.PAYMENT_PLANS)
def test_user_create_actions__premium__ok(mocker, plan):

    # arrange
    account = create_test_account(plan=plan)
    request_user = create_test_user(account=account)
    key = '!@#W32423'
    create_key_mock = mocker.patch(
        'pneumatic_backend.accounts.services.user_invite.'
        'PneumaticToken.create',
        return_value=key
    )
    current_url = 'http://current.test'
    is_superuser = False
    workflow = create_test_workflow(request_user, tasks_count=1)
    invited_user = create_invited_user(
        user=request_user,
        first_name='User',
        last_name='Invited'
    )

    service = UserInviteService(
        current_url=current_url,
        is_superuser=is_superuser,
        request_user=request_user
    )

    # act
    service._user_create_actions(invited_user)

    # assert
    workflow.refresh_from_db()
    assert invited_user not in workflow.members.all()
    template = workflow.template
    assert invited_user not in template.template_owners.all()
    assert APIKey.objects.get(
        user=invited_user,
        name='User Invited',
        account_id=account.id,
        key=key
    )
    create_key_mock.assert_called_once_with(invited_user, for_api_key=True)


def test_user_create_actions__freemium__ok(mocker):

    # arrange
    account = create_test_account(plan=BillingPlanType.FREEMIUM)
    request_user = create_test_user(account=account)
    current_url = 'http://current.test'
    is_superuser = False
    workflow = create_test_workflow(request_user, tasks_count=1)
    invited_user = create_invited_user(user=request_user)
    key = '!@#W32423'
    create_key_mock = mocker.patch(
        'pneumatic_backend.accounts.services.user_invite.'
        'PneumaticToken.create',
        return_value=key
    )

    service = UserInviteService(
        current_url=current_url,
        is_superuser=is_superuser,
        request_user=request_user
    )

    # act
    service._user_create_actions(invited_user)

    # assert
    workflow.refresh_from_db()
    assert invited_user in workflow.members.all()
    template = workflow.template
    assert invited_user in template.template_owners.all()
    assert APIKey.objects.get(
        user=invited_user,
        name='',
        account_id=account.id,
        key=key
    )
    create_key_mock.assert_called_once_with(invited_user, for_api_key=True)


def test_send_transfer_email__ok(mocker):

    # arrange
    account = create_test_account(logo_lg='https://another/image.jpg')
    request_user = create_test_user(account=account)
    invited_user = create_invited_user(user=request_user)
    user_to_transfer = create_test_user(email='transfer@test.test')
    current_url = 'http://current.test'
    is_superuser = False
    transfer_token_str = '!@#wweqasd'
    transfer_token_mock = mocker.patch(
        'pneumatic_backend.accounts.services.UserInviteService.'
        '_get_transfer_token',
        return_value=transfer_token_str
    )
    send_user_transfer_email_mock = mocker.patch(
        'pneumatic_backend.services.email.EmailService.'
        'send_user_transfer_email'
    )
    service = UserInviteService(
        current_url=current_url,
        is_superuser=is_superuser,
        request_user=request_user
    )

    # act
    service._send_transfer_email(
        current_account_user=invited_user,
        another_account_user=user_to_transfer
    )

    # assert
    transfer_token_mock.assert_called_once_with(
        current_account_user=invited_user,
        another_account_user=user_to_transfer
    )
    send_user_transfer_email_mock.assert_called_once_with(
        email=user_to_transfer.email,
        invited_by=request_user,
        token=transfer_token_str,
        user_id=invited_user.id,
        logo_lg=account.logo_lg
    )


def test_validate_already_accepted__status_accepted__raise_exception():

    # arrange
    account = create_test_account()
    request_user = create_test_user(account=account)
    accepted_user = create_test_user(
        account=account,
        email='invited@test.test'
    )
    current_url = 'http://current.test'
    is_superuser = False
    service = UserInviteService(
        current_url=current_url,
        is_superuser=is_superuser,
        request_user=request_user
    )

    # act
    with pytest.raises(AlreadyAcceptedInviteException):
        service._validate_already_accepted(accepted_user)


def test_validate_already_accepted__status_invited__ok():

    # arrange
    account = create_test_account()
    request_user = create_test_user(account=account)
    invited_user = create_invited_user(request_user)
    current_url = 'http://current.test'
    is_superuser = False
    service = UserInviteService(
        current_url=current_url,
        is_superuser=is_superuser,
        request_user=request_user
    )

    # act
    service._validate_already_accepted(invited_user)


def test_validate_limit_invites__active_users_less_then_max_users__ok():

    # arrange
    account = create_test_account()
    request_user = create_test_user(account=account)
    account.max_invites = 3
    account.max_users = 5
    account.active_users = 4
    account.save()
    current_url = 'http://current.test'
    is_superuser = False
    service = UserInviteService(
        current_url=current_url,
        is_superuser=is_superuser,
        request_user=request_user
    )

    # act
    service._validate_limit_invites()


def test_validate_limit_invites__active_users_less_then_max_invites__ok():

    # arrange
    account = create_test_account()
    request_user = create_test_user(account=account)
    account.max_invites = 5
    account.max_users = 3
    account.active_users = 4
    account.save()
    current_url = 'http://current.test'
    is_superuser = False
    service = UserInviteService(
        current_url=current_url,
        is_superuser=is_superuser,
        request_user=request_user
    )

    # act
    service._validate_limit_invites()


def test_validate_limit_invites__account_invites_limit__raise_exception():

    # arrange
    account = create_test_account()
    request_user = create_test_user(account=account)
    account.max_invites = 5
    account.max_users = 5
    account.active_users = 5
    account.save()
    current_url = 'http://current.test'
    is_superuser = False
    service = UserInviteService(
        current_url=current_url,
        is_superuser=is_superuser,
        request_user=request_user
    )

    # act
    with pytest.raises(UsersLimitInvitesException):
        service._validate_limit_invites()


def test__user_invite_actions__ok(mocker):

    # arrange
    request_user = create_test_user()
    invited_user = create_invited_user(user=request_user)
    current_url = 'http://current.test'
    is_superuser = False
    invite_token_str = '!@#wweqasd'
    identify_mock = mocker.patch(
        'pneumatic_backend.accounts.services.UserInviteService.'
        'identify'
    )
    invite_token_mock = mocker.patch(
        'pneumatic_backend.accounts.services.UserInviteService.'
        '_get_invite_token',
        return_value=invite_token_str
    )
    users_invited_mock = mocker.patch(
        'pneumatic_backend.analytics.services.AnalyticService.'
        'users_invited'
    )
    users_invite_sent_mock = mocker.patch(
        'pneumatic_backend.analytics.services.AnalyticService.'
        'users_invite_sent'
    )
    service = UserInviteService(
        current_url=current_url,
        is_superuser=is_superuser,
        request_user=request_user
    )

    # act
    service._user_invite_actions(user=invited_user)

    # assert
    identify_mock.assert_called_once_with(invited_user)
    invite_token_mock.assert_called_once_with(invited_user)
    users_invited_mock.assert_called_once_with(
        invite_to=invited_user,
        is_superuser=is_superuser,
        invite_token=invite_token_str
    )
    users_invite_sent_mock.assert_called_once_with(
        invite_from=request_user,
        invite_to=invited_user,
        current_url=current_url,
        is_superuser=is_superuser
    )


def test__user_transfer_actions__ok(mocker):

    # arrange
    request_user = create_test_user()
    invited_user = create_invited_user(user=request_user)
    user_to_transfer = create_test_user(email='transfer@test.test')
    current_url = 'http://current.test'
    is_superuser = False
    invite_token_str = '!@#wweqasd'
    identify_mock = mocker.patch(
        'pneumatic_backend.accounts.services.UserInviteService.'
        'identify'
    )
    invite_token_mock = mocker.patch(
        'pneumatic_backend.accounts.services.UserInviteService.'
        '_get_invite_token',
        return_value=invite_token_str
    )
    users_invited_mock = mocker.patch(
        'pneumatic_backend.analytics.services.AnalyticService.'
        'users_invited'
    )
    users_invite_sent_mock = mocker.patch(
        'pneumatic_backend.analytics.services.AnalyticService.'
        'users_invite_sent'
    )
    service = UserInviteService(
        current_url=current_url,
        is_superuser=is_superuser,
        request_user=request_user
    )

    # act
    service._user_transfer_actions(
        current_account_user=invited_user,
        another_account_user=user_to_transfer
    )

    # assert
    identify_mock.assert_called_once_with(invited_user)
    invite_token_mock.assert_called_once_with(user_to_transfer)
    users_invited_mock.assert_called_once_with(
        invite_to=user_to_transfer,
        is_superuser=is_superuser,
        invite_token=invite_token_str
    )
    users_invite_sent_mock.assert_called_once_with(
        invite_from=request_user,
        invite_to=user_to_transfer,
        current_url=current_url,
        is_superuser=is_superuser
    )


def test_invite_new_user__all_fields__ok(mocker):

    # arrange
    request_user = create_test_user()
    invited_user = create_invited_user(user=request_user)
    group = create_test_group(user=request_user)
    invite_data = InviteData(
        invited_from=SourceType.EMAIL,
        email='transfer@test.test',
        first_name='first',
        last_name='first',
        photo='http://my.link-1.jpg',
        groups=[group.id],
    )
    current_url = 'http://current.test'
    is_superuser = False
    service = UserInviteService(
        current_url=current_url,
        is_superuser=is_superuser,
        request_user=request_user
    )
    get_account_user_mock = mocker.patch(
        'pneumatic_backend.accounts.services.UserInviteService.'
        '_get_account_user',
        return_value=None
    )
    validate_already_accepted_mock = mocker.patch(
        'pneumatic_backend.accounts.services.UserInviteService.'
        '_validate_already_accepted'
    )
    validate_limit_invites_mock = mocker.patch(
        'pneumatic_backend.accounts.services.UserInviteService.'
        '_validate_limit_invites'
    )
    create_invited_user_mock = mocker.patch(
        'pneumatic_backend.accounts.services.UserInviteService.'
        '_create_invited_user',
        return_value=invited_user
    )
    create_user_invite_mock = mocker.patch(
        'pneumatic_backend.accounts.services.UserInviteService.'
        '_create_user_invite'
    )
    user_create_actions_mock = mocker.patch(
        'pneumatic_backend.accounts.services.UserInviteService.'
        '_user_create_actions'
    )
    user_invite_actions_mock = mocker.patch(
        'pneumatic_backend.accounts.services.UserInviteService.'
        '_user_invite_actions'
    )

    # act
    service._invite_new_user(**invite_data)

    # assert
    get_account_user_mock.assert_called_once_with(invite_data['email'])
    validate_already_accepted_mock.assert_not_called()
    validate_limit_invites_mock.assert_called_once()
    create_invited_user_mock.assert_called_once_with(
        email=invite_data['email'],
        first_name=invite_data['first_name'],
        last_name=invite_data['last_name'],
        photo=invite_data['photo']
    )
    create_user_invite_mock.assert_called_once_with(
        user=invited_user,
        invited_from=invite_data['invited_from']
    )
    user_create_actions_mock.assert_called_once_with(invited_user)
    user_invite_actions_mock.assert_called_once_with(invited_user)
    invited_user.refresh_from_db()
    assert invited_user.user_groups.get(id=group.id)


def test_invite_new_user__only_required_fields__ok(mocker):

    # arrange
    request_user = create_test_user()
    invited_user = create_invited_user(user=request_user)
    invite_data = InviteData(
        invited_from=SourceType.EMAIL,
        email='transfer@test.test',
    )
    current_url = 'http://current.test'
    is_superuser = False
    service = UserInviteService(
        current_url=current_url,
        is_superuser=is_superuser,
        request_user=request_user
    )
    get_account_user_mock = mocker.patch(
        'pneumatic_backend.accounts.services.UserInviteService.'
        '_get_account_user',
        return_value=None
    )
    validate_already_accepted_mock = mocker.patch(
        'pneumatic_backend.accounts.services.UserInviteService.'
        '_validate_already_accepted'
    )
    validate_limit_invites_mock = mocker.patch(
        'pneumatic_backend.accounts.services.UserInviteService.'
        '_validate_limit_invites'
    )
    create_invited_user_mock = mocker.patch(
        'pneumatic_backend.accounts.services.UserInviteService.'
        '_create_invited_user',
        return_value=invited_user
    )
    create_user_invite_mock = mocker.patch(
        'pneumatic_backend.accounts.services.UserInviteService.'
        '_create_user_invite'
    )
    user_create_actions_mock = mocker.patch(
        'pneumatic_backend.accounts.services.UserInviteService.'
        '_user_create_actions'
    )
    user_invite_actions_mock = mocker.patch(
        'pneumatic_backend.accounts.services.UserInviteService.'
        '_user_invite_actions'
    )

    # act
    service._invite_new_user(**invite_data)

    # assert
    get_account_user_mock.assert_called_once_with(invite_data['email'])
    validate_already_accepted_mock.assert_not_called()
    validate_limit_invites_mock.assert_called_once()
    create_invited_user_mock.assert_called_once_with(
        email=invite_data['email'],
        first_name=None,
        last_name=None,
        photo=None,
    )
    create_user_invite_mock.assert_called_once_with(
        user=invited_user,
        invited_from=invite_data['invited_from']
    )
    user_create_actions_mock.assert_called_once_with(invited_user)
    user_invite_actions_mock.assert_called_once_with(invited_user)
    group_add = UserModel.objects.get(id=invited_user.id).user_groups.first()
    assert group_add is None


def test_invite_new_user__already_accepted__ok(mocker):

    # arrange
    request_user = create_test_user()
    invited_user = create_invited_user(user=request_user)
    create_test_group(user=request_user)
    invite_data = InviteData(
        invited_from=SourceType.EMAIL,
        email='transfer@test.test',
        first_name='first',
        last_name='first',
        photo='http://my.link-1.jpg'
    )
    current_url = 'http://current.test'
    is_superuser = False
    service = UserInviteService(
        current_url=current_url,
        is_superuser=is_superuser,
        request_user=request_user
    )
    get_account_user_mock = mocker.patch(
        'pneumatic_backend.accounts.services.UserInviteService.'
        '_get_account_user',
        return_value=invited_user
    )
    validate_already_accepted_mock = mocker.patch(
        'pneumatic_backend.accounts.services.UserInviteService.'
        '_validate_already_accepted'
    )
    validate_limit_invites_mock = mocker.patch(
        'pneumatic_backend.accounts.services.UserInviteService.'
        '_validate_limit_invites'
    )
    create_invited_user_mock = mocker.patch(
        'pneumatic_backend.accounts.services.UserInviteService.'
        '_create_invited_user'
    )
    create_user_invite_mock = mocker.patch(
        'pneumatic_backend.accounts.services.UserInviteService.'
        '_create_user_invite'
    )
    user_create_actions_mock = mocker.patch(
        'pneumatic_backend.accounts.services.UserInviteService.'
        '_user_create_actions'
    )
    user_invite_actions_mock = mocker.patch(
        'pneumatic_backend.accounts.services.UserInviteService.'
        '_user_invite_actions'
    )

    # act
    service._invite_new_user(**invite_data)

    # assert
    get_account_user_mock.assert_called_once_with(invite_data['email'])
    validate_already_accepted_mock.assert_called_once_with(invited_user)
    validate_limit_invites_mock.assert_not_called()
    create_invited_user_mock.assert_not_called()
    create_user_invite_mock.assert_not_called()
    user_create_actions_mock.assert_not_called()
    user_invite_actions_mock.assert_not_called()


def test_invite_new_user__not_send_email__ok(mocker):

    # arrange
    request_user = create_test_user()
    invited_user = create_invited_user(user=request_user)
    create_test_group(user=request_user)
    invite_data = InviteData(
        invited_from=SourceType.EMAIL,
        email='transfer@test.test',
        first_name='first',
        last_name='first',
        photo='http://my.link-1.jpg'
    )
    current_url = 'http://current.test'
    is_superuser = False
    service = UserInviteService(
        current_url=current_url,
        is_superuser=is_superuser,
        request_user=request_user,
        send_email=False
    )
    get_account_user_mock = mocker.patch(
        'pneumatic_backend.accounts.services.UserInviteService.'
        '_get_account_user',
        return_value=None
    )
    validate_already_accepted_mock = mocker.patch(
        'pneumatic_backend.accounts.services.UserInviteService.'
        '_validate_already_accepted'
    )
    validate_limit_invites_mock = mocker.patch(
        'pneumatic_backend.accounts.services.UserInviteService.'
        '_validate_limit_invites'
    )
    create_invited_user_mock = mocker.patch(
        'pneumatic_backend.accounts.services.UserInviteService.'
        '_create_invited_user',
        return_value=invited_user
    )
    create_user_invite_mock = mocker.patch(
        'pneumatic_backend.accounts.services.UserInviteService.'
        '_create_user_invite'
    )
    user_create_actions_mock = mocker.patch(
        'pneumatic_backend.accounts.services.UserInviteService.'
        '_user_create_actions'
    )
    user_invite_actions_mock = mocker.patch(
        'pneumatic_backend.accounts.services.UserInviteService.'
        '_user_invite_actions'
    )

    # act
    service._invite_new_user(**invite_data)

    # assert
    get_account_user_mock.assert_called_once_with(invite_data['email'])
    validate_already_accepted_mock.assert_not_called()
    validate_limit_invites_mock.assert_called_once()
    create_invited_user_mock.assert_called_once_with(
        email=invite_data['email'],
        first_name=invite_data['first_name'],
        last_name=invite_data['last_name'],
        photo=invite_data['photo']
    )
    create_user_invite_mock.assert_called_once_with(
        user=invited_user,
        invited_from=invite_data['invited_from']
    )
    user_create_actions_mock.assert_called_once_with(invited_user)
    user_invite_actions_mock.assert_not_called()


def test_transfer_existent_user__all_fields__ok(mocker):

    # arrange
    request_user = create_test_user()
    invited_user = create_invited_user(user=request_user)
    group = create_test_group(user=request_user)
    invite_data = InviteData(
        invited_from=SourceType.EMAIL,
        email='transfer@test.test',
        first_name='first',
        last_name='first',
        photo='http://my.link-1.jpg',
        groups=[group.id],
    )
    user_to_transfer = create_test_user(email='transfer@test.test')
    user_to_transfer.password = 123
    user_to_transfer.save()
    current_url = 'http://current.test'
    is_superuser = False
    service = UserInviteService(
        current_url=current_url,
        is_superuser=is_superuser,
        request_user=request_user
    )
    get_account_user_mock = mocker.patch(
        'pneumatic_backend.accounts.services.UserInviteService.'
        '_get_account_user',
        return_value=None
    )
    validate_already_accepted_mock = mocker.patch(
        'pneumatic_backend.accounts.services.UserInviteService.'
        '_validate_already_accepted'
    )
    validate_limit_invites_mock = mocker.patch(
        'pneumatic_backend.accounts.services.UserInviteService.'
        '_validate_limit_invites'
    )
    create_invited_user_mock = mocker.patch(
        'pneumatic_backend.accounts.services.UserInviteService.'
        '_create_invited_user',
        return_value=invited_user
    )
    create_user_invite_mock = mocker.patch(
        'pneumatic_backend.accounts.services.UserInviteService.'
        '_create_user_invite'
    )
    user_create_actions_mock = mocker.patch(
        'pneumatic_backend.accounts.services.UserInviteService.'
        '_user_create_actions'
    )
    user_transfer_actions_mock = mocker.patch(
        'pneumatic_backend.accounts.services.UserInviteService.'
        '_user_transfer_actions'
    )
    send_transfer_email_mock = mocker.patch(
        'pneumatic_backend.accounts.services.UserInviteService.'
        '_send_transfer_email'
    )

    # act
    service._transfer_existent_user(
        another_account_user=user_to_transfer,
        **invite_data
    )

    # assert
    get_account_user_mock.assert_called_once_with(invite_data['email'])
    validate_already_accepted_mock.assert_not_called()
    validate_limit_invites_mock.assert_called_once()
    create_invited_user_mock.assert_called_once_with(
        email=invite_data['email'],
        first_name=invite_data['first_name'],
        last_name=invite_data['last_name'],
        photo=invite_data['photo'],
        password=user_to_transfer.password
    )
    create_user_invite_mock.assert_called_once_with(
        user=invited_user,
        invited_from=invite_data['invited_from']
    )
    user_create_actions_mock.assert_called_once_with(invited_user)
    user_transfer_actions_mock.assert_called_once_with(
        current_account_user=invited_user,
        another_account_user=user_to_transfer
    )
    send_transfer_email_mock.assert_called_once_with(
        current_account_user=invited_user,
        another_account_user=user_to_transfer
    )
    invited_user.refresh_from_db()
    assert invited_user.user_groups.get(id=group.id)


def test_transfer_existent_user__only_required_fields__ok(mocker):

    # arrange
    request_user = create_test_user()
    invited_user = create_invited_user(user=request_user)
    invite_data = InviteData(
        invited_from=SourceType.EMAIL,
        email='transfer@test.test',
    )
    user_to_transfer = create_test_user(email='transfer@test.test')
    user_to_transfer.password = 123
    user_to_transfer.save()
    current_url = 'http://current.test'
    is_superuser = False
    service = UserInviteService(
        current_url=current_url,
        is_superuser=is_superuser,
        request_user=request_user
    )
    get_account_user_mock = mocker.patch(
        'pneumatic_backend.accounts.services.UserInviteService.'
        '_get_account_user',
        return_value=None
    )
    validate_already_accepted_mock = mocker.patch(
        'pneumatic_backend.accounts.services.UserInviteService.'
        '_validate_already_accepted'
    )
    validate_limit_invites_mock = mocker.patch(
        'pneumatic_backend.accounts.services.UserInviteService.'
        '_validate_limit_invites'
    )
    create_invited_user_mock = mocker.patch(
        'pneumatic_backend.accounts.services.UserInviteService.'
        '_create_invited_user',
        return_value=invited_user
    )
    create_user_invite_mock = mocker.patch(
        'pneumatic_backend.accounts.services.UserInviteService.'
        '_create_user_invite'
    )
    user_create_actions_mock = mocker.patch(
        'pneumatic_backend.accounts.services.UserInviteService.'
        '_user_create_actions'
    )
    user_transfer_actions_mock = mocker.patch(
        'pneumatic_backend.accounts.services.UserInviteService.'
        '_user_transfer_actions'
    )
    send_transfer_email_mock = mocker.patch(
        'pneumatic_backend.accounts.services.UserInviteService.'
        '_send_transfer_email'
    )

    # act
    service._transfer_existent_user(
        another_account_user=user_to_transfer,
        **invite_data
    )

    # assert
    get_account_user_mock.assert_called_once_with(invite_data['email'])
    validate_already_accepted_mock.assert_not_called()
    validate_limit_invites_mock.assert_called_once()
    create_invited_user_mock.assert_called_once_with(
        email=invite_data['email'],
        first_name=None,
        last_name=None,
        photo=None,
        password=user_to_transfer.password
    )
    create_user_invite_mock.assert_called_once_with(
        user=invited_user,
        invited_from=invite_data['invited_from']
    )
    user_create_actions_mock.assert_called_once_with(invited_user)
    user_transfer_actions_mock.assert_called_once_with(
        current_account_user=invited_user,
        another_account_user=user_to_transfer
    )
    send_transfer_email_mock.assert_called_once_with(
        current_account_user=invited_user,
        another_account_user=user_to_transfer
    )
    group_add = UserModel.objects.get(id=invited_user.id).user_groups.first()
    assert group_add is None


def test_transfer_existent_user__already_accepted__ok(mocker):

    # arrange
    request_user = create_test_user()
    invited_user = create_invited_user(
        user=request_user,
        email='transfer@test.test'
    )
    create_test_group(user=request_user)
    invite_data = InviteData(
        invited_from=SourceType.EMAIL,
        email='transfer@test.test',
        first_name='first',
        last_name='first',
        photo='http://my.link-1.jpg'
    )
    user_to_transfer = create_test_user(email='transfer@test.test')
    current_url = 'http://current.test'
    is_superuser = False
    service = UserInviteService(
        current_url=current_url,
        is_superuser=is_superuser,
        request_user=request_user
    )
    get_account_user_mock = mocker.patch(
        'pneumatic_backend.accounts.services.UserInviteService.'
        '_get_account_user',
        return_value=invited_user
    )
    validate_already_accepted_mock = mocker.patch(
        'pneumatic_backend.accounts.services.UserInviteService.'
        '_validate_already_accepted'
    )
    validate_limit_invites_mock = mocker.patch(
        'pneumatic_backend.accounts.services.UserInviteService.'
        '_validate_limit_invites'
    )
    create_invited_user_mock = mocker.patch(
        'pneumatic_backend.accounts.services.UserInviteService.'
        '_create_invited_user'
    )
    create_user_invite_mock = mocker.patch(
        'pneumatic_backend.accounts.services.UserInviteService.'
        '_create_user_invite'
    )
    user_create_actions_mock = mocker.patch(
        'pneumatic_backend.accounts.services.UserInviteService.'
        '_user_create_actions'
    )
    user_transfer_actions_mock = mocker.patch(
        'pneumatic_backend.accounts.services.UserInviteService.'
        '_user_transfer_actions'
    )
    send_transfer_email_mock = mocker.patch(
        'pneumatic_backend.accounts.services.UserInviteService.'
        '_send_transfer_email'
    )

    # act
    service._transfer_existent_user(
        another_account_user=user_to_transfer,
        **invite_data
    )

    # assert
    get_account_user_mock.assert_called_once_with(invite_data['email'])
    validate_already_accepted_mock.assert_called_once_with(invited_user)
    validate_limit_invites_mock.assert_not_called()
    create_invited_user_mock.assert_not_called()
    create_user_invite_mock.assert_not_called()
    user_create_actions_mock.assert_not_called()
    user_transfer_actions_mock.assert_not_called()
    send_transfer_email_mock.assert_not_called()


def test_transfer_existent_user__not_send_email__ok(mocker):

    # arrange
    request_user = create_test_user()
    invited_user = create_invited_user(user=request_user)
    create_test_group(user=request_user)
    invite_data = InviteData(
        invited_from=SourceType.EMAIL,
        email='transfer@test.test',
        first_name='first',
        last_name='first',
        photo='http://my.link-1.jpg'
    )
    user_to_transfer = create_test_user(email='transfer@test.test')
    user_to_transfer.password = 123
    user_to_transfer.save()
    current_url = 'http://current.test'
    is_superuser = False
    service = UserInviteService(
        current_url=current_url,
        is_superuser=is_superuser,
        request_user=request_user,
        send_email=False
    )
    get_account_user_mock = mocker.patch(
        'pneumatic_backend.accounts.services.UserInviteService.'
        '_get_account_user',
        return_value=None
    )
    validate_already_accepted_mock = mocker.patch(
        'pneumatic_backend.accounts.services.UserInviteService.'
        '_validate_already_accepted'
    )
    validate_limit_invites_mock = mocker.patch(
        'pneumatic_backend.accounts.services.UserInviteService.'
        '_validate_limit_invites'
    )
    create_invited_user_mock = mocker.patch(
        'pneumatic_backend.accounts.services.UserInviteService.'
        '_create_invited_user',
        return_value=invited_user
    )
    create_user_invite_mock = mocker.patch(
        'pneumatic_backend.accounts.services.UserInviteService.'
        '_create_user_invite'
    )
    user_create_actions_mock = mocker.patch(
        'pneumatic_backend.accounts.services.UserInviteService.'
        '_user_create_actions'
    )
    user_transfer_actions_mock = mocker.patch(
        'pneumatic_backend.accounts.services.UserInviteService.'
        '_user_transfer_actions'
    )
    send_transfer_email_mock = mocker.patch(
        'pneumatic_backend.accounts.services.UserInviteService.'
        '_send_transfer_email'
    )

    # act
    service._transfer_existent_user(
        another_account_user=user_to_transfer,
        **invite_data
    )

    # assert
    get_account_user_mock.assert_called_once_with(invite_data['email'])
    validate_already_accepted_mock.assert_not_called()
    validate_limit_invites_mock.assert_called_once()
    create_invited_user_mock.assert_called_once_with(
        email=invite_data['email'],
        first_name=invite_data['first_name'],
        last_name=invite_data['last_name'],
        photo=invite_data['photo'],
        password=user_to_transfer.password
    )
    create_user_invite_mock.assert_called_once_with(
        user=invited_user,
        invited_from=invite_data['invited_from']
    )
    user_create_actions_mock.assert_called_once_with(invited_user)
    user_transfer_actions_mock.assert_called_once_with(
        current_account_user=invited_user,
        another_account_user=user_to_transfer
    )
    send_transfer_email_mock.assert_not_called()


def test_resend_invite__ok(mocker):

    # arrange
    account = create_test_account()
    request_user = create_test_user(account=account)
    invited_user = create_invited_user(user=request_user)
    current_url = 'http://current.test'
    is_superuser = False
    service = UserInviteService(
        current_url=current_url,
        is_superuser=is_superuser,
        request_user=request_user
    )
    user_invite_actions_mock = mocker.patch(
        'pneumatic_backend.accounts.services.UserInviteService.'
        '_user_invite_actions'
    )
    send_transfer_email_mock = mocker.patch(
        'pneumatic_backend.accounts.services.UserInviteService.'
        '_send_transfer_email'
    )
    user_transfer_actions_mock = mocker.patch(
        'pneumatic_backend.accounts.services.UserInviteService.'
        '_user_transfer_actions'
    )

    # act
    service.resend_invite(user_id=invited_user.id)

    # assert
    user_invite_actions_mock.assert_called_once_with(
        invited_user
    )
    send_transfer_email_mock.assert_not_called()
    user_transfer_actions_mock.assert_not_called()


def test_resend_invite_transfer__ok(mocker):

    # arrange
    user_to_transfer = create_test_user(email='transfer@test.test')
    account = create_test_account()
    request_user = create_test_user(account=account)
    invited_user = create_invited_user(
        email='transfer@test.test',
        user=request_user
    )
    current_url = 'http://current.test'
    is_superuser = False
    service = UserInviteService(
        current_url=current_url,
        is_superuser=is_superuser,
        request_user=request_user
    )
    user_invite_actions_mock = mocker.patch(
        'pneumatic_backend.accounts.services.UserInviteService.'
        '_user_invite_actions'
    )
    send_transfer_email_mock = mocker.patch(
        'pneumatic_backend.accounts.services.UserInviteService.'
        '_send_transfer_email'
    )
    user_transfer_actions_mock = mocker.patch(
        'pneumatic_backend.accounts.services.UserInviteService.'
        '_user_transfer_actions'
    )

    # act
    service.resend_invite(user_id=invited_user.id)

    # assert
    send_transfer_email_mock.assert_called_once_with(
        current_account_user=invited_user,
        another_account_user=user_to_transfer,

    )
    user_transfer_actions_mock.assert_called_once_with(
        current_account_user=invited_user,
        another_account_user=user_to_transfer,
    )
    user_invite_actions_mock.assert_not_called()


def test_resend_invite__invite_yourself__raise_exception(mocker):

    # arrange
    account = create_test_account()
    request_user = create_test_user(account=account)
    current_url = 'http://current.test'
    is_superuser = False
    service = UserInviteService(
        current_url=current_url,
        is_superuser=is_superuser,
        request_user=request_user
    )
    user_invite_actions_mock = mocker.patch(
        'pneumatic_backend.accounts.services.UserInviteService.'
        '_user_invite_actions'
    )
    send_transfer_email_mock = mocker.patch(
        'pneumatic_backend.accounts.services.UserInviteService.'
        '_send_transfer_email'
    )
    user_transfer_actions_mock = mocker.patch(
        'pneumatic_backend.accounts.services.UserInviteService.'
        '_user_transfer_actions'
    )

    # act
    with pytest.raises(AlreadyAcceptedInviteException):
        service.resend_invite(user_id=request_user.id)

    # assert
    user_invite_actions_mock.assert_not_called()
    send_transfer_email_mock.assert_not_called()
    user_transfer_actions_mock.assert_not_called()


def test_resend_invite__non_existent_user__raise_exception(mocker):

    # arrange
    account = create_test_account()
    another_account_owner = create_test_user(email='another.owner@test.test')
    another_account_invited_user = create_invited_user(
        user=another_account_owner
    )
    request_user = create_test_user(account=account)
    current_url = 'http://current.test'
    is_superuser = False
    service = UserInviteService(
        current_url=current_url,
        is_superuser=is_superuser,
        request_user=request_user
    )
    user_invite_actions_mock = mocker.patch(
        'pneumatic_backend.accounts.services.UserInviteService.'
        '_user_invite_actions'
    )
    send_transfer_email_mock = mocker.patch(
        'pneumatic_backend.accounts.services.UserInviteService.'
        '_send_transfer_email'
    )
    user_transfer_actions_mock = mocker.patch(
        'pneumatic_backend.accounts.services.UserInviteService.'
        '_user_transfer_actions'
    )

    # act
    with pytest.raises(UserNotFoundException):
        service.resend_invite(user_id=another_account_invited_user.id)

    # assert
    user_invite_actions_mock.assert_not_called()
    send_transfer_email_mock.assert_not_called()
    user_transfer_actions_mock.assert_not_called()


def test_resend_invite__already_active_user__raise_exception(mocker):

    # arrange
    account = create_test_account()
    invited_user = create_test_user(account=account, email='invited@test.test')
    request_user = create_test_user(account=account)
    current_url = 'http://current.test'
    is_superuser = False
    service = UserInviteService(
        current_url=current_url,
        is_superuser=is_superuser,
        request_user=request_user
    )
    user_invite_actions_mock = mocker.patch(
        'pneumatic_backend.accounts.services.UserInviteService.'
        '_user_invite_actions'
    )
    send_transfer_email_mock = mocker.patch(
        'pneumatic_backend.accounts.services.UserInviteService.'
        '_send_transfer_email'
    )
    user_transfer_actions_mock = mocker.patch(
        'pneumatic_backend.accounts.services.UserInviteService.'
        '_user_transfer_actions'
    )

    # act
    with pytest.raises(AlreadyAcceptedInviteException):
        service.resend_invite(user_id=invited_user.id)

    # assert
    user_invite_actions_mock.assert_not_called()
    send_transfer_email_mock.assert_not_called()
    user_transfer_actions_mock.assert_not_called()


def test_invite_user__ok(mocker):

    # arrange
    request_user = create_test_user()
    group = create_test_group(user=request_user)
    invite_data = InviteData(
        invited_from=SourceType.EMAIL,
        email='test_1@test.test',
        first_name='first',
        last_name='first',
        photo='http://my.link-1.jpg',
        groups=[group.id],
    )
    current_url = 'http://current.test'
    is_superuser = False
    service = UserInviteService(
        current_url=current_url,
        is_superuser=is_superuser,
        request_user=request_user
    )
    invite_new_user_mock = mocker.patch(
        'pneumatic_backend.accounts.services.UserInviteService.'
        '_invite_new_user'
    )
    transfer_existent_user_mock = mocker.patch(
        'pneumatic_backend.accounts.services.UserInviteService.'
        '_transfer_existent_user'
    )

    # act
    service.invite_user(**invite_data)

    # assert
    invite_new_user_mock.assert_called_once_with(**invite_data)
    transfer_existent_user_mock.assert_not_called()


def test_invite_user__transfer_invite__ok(mocker):

    # arrange
    user_to_transfer = create_test_user(
        email='transfer@test.test',
    )
    invite_data = InviteData(
        invited_from=SourceType.EMAIL,
        email='transfer@test.test',
        first_name='first',
        last_name='first',
        photo='http://my.link-1.jpg'
    )
    request_user = create_test_user()
    current_url = 'http://current.test'
    is_superuser = False
    service = UserInviteService(
        current_url=current_url,
        is_superuser=is_superuser,
        request_user=request_user
    )
    invite_new_user_mock = mocker.patch(
        'pneumatic_backend.accounts.services.UserInviteService.'
        '_invite_new_user'
    )
    transfer_existent_user_mock = mocker.patch(
        'pneumatic_backend.accounts.services.UserInviteService.'
        '_transfer_existent_user'
    )

    # act
    service.invite_user(**invite_data)

    # assert
    invite_new_user_mock.assert_not_called()
    transfer_existent_user_mock.assert_called_once_with(
        another_account_user=user_to_transfer,
        groups=None,
        **invite_data
    )


def test_invite_user__update_contacts__ok(mocker):

    # arrange
    email = 'test_1@ms.test'
    invite_data = InviteData(
        invited_from=SourceType.MICROSOFT,
        email=email,
        first_name='first',
        last_name='first',
        photo=None
    )
    account = create_test_account()
    request_user = create_test_user(account=account)
    another_user = create_test_user(
        account=account,
        email='another@email.com',
        is_account_owner=False
    )
    another_account_user = create_test_user(
        email='anotheraccount@email.com',
    )
    current_url = 'http://current.test'
    is_superuser = False
    service = UserInviteService(
        current_url=current_url,
        is_superuser=is_superuser,
        request_user=request_user
    )
    invite_new_user_mock = mocker.patch(
        'pneumatic_backend.accounts.services.UserInviteService.'
        '_invite_new_user'
    )
    transfer_existent_user_mock = mocker.patch(
        'pneumatic_backend.accounts.services.UserInviteService.'
        '_transfer_existent_user'
    )
    google_contact = Contact.objects.create(
        account=request_user.account,
        user_id=request_user.id,
        source=SourceType.GOOGLE,
        email=email
    )
    ms_contact = Contact.objects.create(
        account=request_user.account,
        user_id=request_user.id,
        source=SourceType.MICROSOFT,
        email=email
    )
    another_user_contact = Contact.objects.create(
        account=request_user.account,
        user_id=another_user.id,
        source=SourceType.MICROSOFT,
        email=email
    )
    another_account_contact = Contact.objects.create(
        account=another_account_user.account,
        user_id=another_account_user.id,
        source=SourceType.GOOGLE,
        email=email
    )
    another_contact = Contact.objects.create(
        account=request_user.account,
        user_id=request_user.id,
        source=SourceType.MICROSOFT,
        email='another@email.com'
    )

    # act
    service.invite_user(**invite_data)

    # assert
    invite_new_user_mock.assert_called_once_with(
        groups=None,
        **invite_data
    )
    transfer_existent_user_mock.assert_not_called()

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


def test_invite_users__ok(mocker):

    # arrange
    invite_data_1 = InviteData(
        invited_from=SourceType.EMAIL,
        email='test_1@test.test',
        first_name='first',
        last_name='first',
        photo='http://my.link-1.jpg'
    )
    invite_data_2 = InviteData(
        invited_from=SourceType.GOOGLE,
        email='test_2@test.test',
        first_name='second',
        last_name='second',
        photo='http://my.link-2.jpg'
    )
    request_user = create_test_user()
    current_url = 'http://current.test'
    is_superuser = False
    service = UserInviteService(
        current_url=current_url,
        is_superuser=is_superuser,
        request_user=request_user
    )
    invite_user_mock = mocker.patch(
        'pneumatic_backend.accounts.services.UserInviteService.invite_user'
    )

    # act
    service.invite_users(data=[invite_data_1, invite_data_2])

    # assert
    invite_user_mock.has_calls([
        mocker.call(**invite_data_1),
        mocker.call(**invite_data_2)
    ])


def test__accept__all_fields__ok(identify_mock, group_mock, mocker):

    # arrange
    account = create_test_account(plan=BillingPlanType.UNLIMITED)
    request_user = create_test_user(
        account=account,
        language=Language.de,
        tz=Timezone.UTC
    )
    invited_user = create_invited_user(user=request_user)
    invite = invited_user.invite
    current_url = 'http://current.test'
    is_superuser = False
    service = UserInviteService(
        current_url=current_url,
        is_superuser=is_superuser,
        request_user=request_user
    )
    password = '!#!%%!#ASDsg@!'
    make_password_mock = mocker.patch(
        'pneumatic_backend.accounts.services.user_invite.make_password',
        return_value=password
    )
    sys_wf_service_init_mock = mocker.patch.object(
        SystemWorkflowService,
        attribute='__init__',
        return_value=None
    )
    create_onboarding_workflows_mock = mocker.patch(
        'pneumatic_backend.accounts.services.user_invite.'
        'SystemWorkflowService.create_onboarding_workflows'
    )
    create_activated_workflows_mock = mocker.patch(
        'pneumatic_backend.accounts.services.user_invite.'
        'SystemWorkflowService.create_activated_workflows'
    )
    account_service_init_mock = mocker.patch.object(
        AccountService,
        attribute='__init__',
        return_value=None
    )
    update_users_counts_mock = mocker.patch(
        'pneumatic_backend.accounts.services.user_invite.AccountService.'
        'update_users_counts'
    )
    increase_plan_users_mock = mocker.patch(
        'pneumatic_backend.accounts.services.user_invite.'
        'increase_plan_users.delay'
    )
    users_joined_mock = mocker.patch(
        'pneumatic_backend.accounts.services.user_invite.'
        'AnalyticService.users_joined'
    )
    settings_mock = mocker.patch(
        'pneumatic_backend.accounts.services.user_invite.settings'
    )
    settings_mock.PROJECT_CONF = {'BILLING': True}
    first_name = 'John'
    last_name = 'Wick'
    language = Language.fr
    tz = Timezone.UTC_8
    raw_password = 'bad-boy-1995'

    # act
    result = service.accept(
        invite=invite,
        first_name=first_name,
        last_name=last_name,
        language=language,
        timezone=tz,
        password=raw_password
    )

    # accept
    assert result == invited_user
    make_password_mock.assert_called_once_with(raw_password)
    invited_user.refresh_from_db()
    assert invited_user.first_name == first_name
    assert invited_user.last_name == last_name
    assert invited_user.password == password
    assert invited_user.is_active is True
    assert invited_user.status == UserStatus.ACTIVE
    assert invited_user.timezone == tz

    invite.refresh_from_db()
    assert invite.status == UserInviteStatus.ACCEPTED
    sys_wf_service_init_mock.assert_called_once_with(user=invited_user)
    create_onboarding_workflows_mock.assert_called_once()
    create_activated_workflows_mock.assert_called_once()
    account_service_init_mock.assert_called_once_with(
        instance=account,
        user=invited_user
    )
    update_users_counts_mock.assert_called_once()
    increase_plan_users_mock.assert_not_called()
    users_joined_mock.assert_called_once_with(invited_user)
    identify_mock.assert_called_once_with(invited_user)
    group_mock.assert_called_once_with(invited_user)


def test__accept__only_required_fields__ok(identify_mock, group_mock, mocker):

    # arrange
    account = create_test_account(plan=BillingPlanType.UNLIMITED)
    request_user = create_test_user(
        account=account,
        tz=Timezone.UTC,
        language=Language.en
    )
    invited_user = create_invited_user(user=request_user)
    invite = invited_user.invite
    current_url = 'http://current.test'
    is_superuser = False
    service = UserInviteService(
        current_url=current_url,
        is_superuser=is_superuser,
        request_user=request_user
    )
    make_password_mock = mocker.patch(
        'pneumatic_backend.accounts.services.user_invite.make_password',
    )
    sys_wf_service_init_mock = mocker.patch.object(
        SystemWorkflowService,
        attribute='__init__',
        return_value=None
    )
    create_onboarding_workflows_mock = mocker.patch(
        'pneumatic_backend.accounts.services.user_invite.'
        'SystemWorkflowService.create_onboarding_workflows'
    )
    create_activated_workflows_mock = mocker.patch(
        'pneumatic_backend.accounts.services.user_invite.'
        'SystemWorkflowService.create_activated_workflows'
    )
    account_service_init_mock = mocker.patch.object(
        AccountService,
        attribute='__init__',
        return_value=None
    )
    update_users_counts_mock = mocker.patch(
        'pneumatic_backend.accounts.services.user_invite.AccountService.'
        'update_users_counts'
    )
    increase_plan_users_mock = mocker.patch(
        'pneumatic_backend.accounts.services.user_invite.'
        'increase_plan_users.delay'
    )
    users_joined_mock = mocker.patch(
        'pneumatic_backend.accounts.services.user_invite.'
        'AnalyticService.users_joined'
    )
    settings_mock = mocker.patch(
        'pneumatic_backend.accounts.services.user_invite.settings'
    )
    settings_mock.PROJECT_CONF = {'BILLING': True}
    first_name = 'John'
    last_name = 'Wick'

    # act
    result = service.accept(
        invite=invite,
        first_name=first_name,
        last_name=last_name
    )

    # accept
    assert result == invited_user
    make_password_mock.assert_not_called()
    invited_user.refresh_from_db()
    assert invited_user.first_name == first_name
    assert invited_user.last_name == last_name
    assert invited_user.password == ''
    assert invited_user.is_active is True
    assert invited_user.status == UserStatus.ACTIVE
    assert invited_user.timezone == request_user.timezone
    assert invited_user.language == request_user.language

    invite.refresh_from_db()
    assert invite.status == UserInviteStatus.ACCEPTED
    sys_wf_service_init_mock.assert_called_once_with(user=invited_user)
    create_onboarding_workflows_mock.assert_called_once()
    create_activated_workflows_mock.assert_called_once()
    account_service_init_mock.assert_called_once_with(
        instance=account,
        user=invited_user
    )
    update_users_counts_mock.assert_called_once()
    increase_plan_users_mock.assert_not_called()
    users_joined_mock.assert_called_once_with(invited_user)
    identify_mock.assert_called_once_with(invited_user)
    group_mock.assert_called_once_with(invited_user)
