import pytest
from pneumatic_backend.accounts.enums import (
    BillingPlanType,
    UserStatus,
    SourceType,
)
from pneumatic_backend.accounts.tests.fixtures import (
    create_test_user,
    create_invited_user,
    create_test_account,
)
from pneumatic_backend.processes.enums import (
    PerformerType,
)
from pneumatic_backend.accounts.tokens import (
    TransferToken
)
from pneumatic_backend.accounts.services.user_transfer import (
    UserTransferService
)
from pneumatic_backend.accounts.services import exceptions
from pneumatic_backend.accounts.services import (
    UserInviteService
)
from pneumatic_backend.accounts.services import AccountService
from pneumatic_backend.authentication.enums import AuthTokenType
from pneumatic_backend.payment.stripe.service import (
    StripeService
)

pytestmark = pytest.mark.django_db


def test_accept_transfer__ok(mocker):

    # arrange
    prev_account = create_test_account(name='prev')
    prev_user = create_test_user(
        account=prev_account,
        email='transferred@test.test'
    )
    new_account = create_test_account(name='new')
    new_account_owner = create_test_user(account=new_account)
    new_user = create_invited_user(
        user=new_account_owner,
        email='transferred@test.test',
    )
    token = TransferToken()
    token['prev_user_id'] = prev_user.id
    token['new_user_id'] = new_user.id
    get_valid_token_mock = mocker.patch(
        'pneumatic_backend.accounts.services.user_transfer.'
        'UserTransferService._get_valid_token',
        return_value=token
    )
    get_valid_user_mock = mocker.patch(
        'pneumatic_backend.accounts.services.user_transfer.'
        'UserTransferService._get_valid_user',
        return_value=new_user
    )
    get_valid_prev_user = mocker.patch(
        'pneumatic_backend.accounts.services.user_transfer.'
        'UserTransferService._get_valid_prev_user',
        return_value=prev_user
    )
    deactivate_prev_user_mock = mocker.patch(
        'pneumatic_backend.accounts.services.user_transfer.'
        'UserTransferService._deactivate_prev_user'
    )
    activate_user_mock = mocker.patch(
        'pneumatic_backend.accounts.services.user_transfer.'
        'UserTransferService._activate_user'
    )
    after_transfer_actions_mock = mocker.patch(
        'pneumatic_backend.accounts.services.user_transfer.'
        'UserTransferService._after_transfer_actions'
    )
    service = UserTransferService()

    # act
    service.accept_transfer(
        user_id=new_user.id,
        token_str=str(token)
    )

    # assert
    get_valid_token_mock.assert_called_once_with(str(token))
    get_valid_user_mock.assert_called_once_with(new_user.id)
    get_valid_prev_user.assert_called_once()
    deactivate_prev_user_mock.assert_called_once()
    activate_user_mock.assert_called_once()
    after_transfer_actions_mock.assert_called_once()


def test_get_valid_user__ok():

    # arrange
    prev_account = create_test_account(name='prev')
    prev_user = create_test_user(
        account=prev_account,
        email='transferred@test.test'
    )
    new_account = create_test_account(name='new')
    account_owner = create_test_user(
        account=new_account,
        email='owner@test.test',
        is_account_owner=True
    )
    new_user = create_invited_user(
        user=account_owner,
    )
    token = TransferToken()
    token['prev_user_id'] = prev_user.id
    token['new_user_id'] = new_user.id
    service = UserTransferService()
    service.token = token

    # act
    user = service._get_valid_user(user_id=new_user.id)

    # assert
    assert user.id == new_user.id


def test_get_valid_user__already_accepted__raise_exception():

    # arrange
    prev_account = create_test_account(name='prev')
    prev_user = create_test_user(
        account=prev_account,
        email='transferred@test.test'
    )
    new_account = create_test_account(name='new')
    account_owner = create_test_user(
        account=new_account,
        email='owner@test.test',
        is_account_owner=True
    )
    new_user = create_invited_user(
        user=account_owner,
        status=UserStatus.ACTIVE
    )
    token = TransferToken()
    token['prev_user_id'] = prev_user.id
    token['new_user_id'] = new_user.id
    service = UserTransferService()
    service.token = token

    # act
    with pytest.raises(exceptions.AlreadyAcceptedInviteException):
        service._get_valid_user(user_id=new_user.id)


def test_get_valid_user__does_not_exist__raise_exception():

    # arrange
    prev_account = create_test_account(name='prev')
    prev_user = create_test_user(
        account=prev_account,
        email='transferred@test.test'
    )
    new_account = create_test_account(name='new')
    account_owner = create_test_user(
        account=new_account,
        email='owner@test.test',
        is_account_owner=True
    )
    new_user = create_invited_user(
        user=account_owner,
        status=UserStatus.ACTIVE
    )
    token = TransferToken()
    token['prev_user_id'] = prev_user.id
    token['new_user_id'] = new_user.id
    service = UserTransferService()
    service.token = token

    # act
    with pytest.raises(exceptions.InvalidTransferTokenException):
        service._get_valid_user(user_id=-999)


def test_get_valid_user__incorrect_token__raise_exception():

    # arrange
    prev_account = create_test_account(name='prev')
    prev_user = create_test_user(
        account=prev_account,
        email='transferred@test.test'
    )
    new_account = create_test_account(name='new')
    account_owner = create_test_user(
        account=new_account,
        email='owner@test.test',
        is_account_owner=True
    )
    new_user = create_invited_user(
        user=account_owner,
        email='invited@test.test',
    )
    token = TransferToken()
    token['prev_user_id'] = prev_user.id
    token['new_user_id'] = new_user.id
    service = UserTransferService()
    service.token = token

    # act
    with pytest.raises(exceptions.InvalidTransferTokenException):
        service._get_valid_user(user_id=account_owner.id)


def test_get_valid_prev_user__ok():

    # arrange
    new_account = create_test_account(name='new')
    account_owner = create_test_user(
        account=new_account,
        email='owner@test.test',
        is_account_owner=True
    )
    new_user = create_invited_user(
        user=account_owner,
        email='transferred@tes.test'
    )
    prev_account = create_test_account(name='new')
    prev_user = create_test_user(
        email='transferred@tes.test',
        account=prev_account
    )
    token = TransferToken()
    token['prev_user_id'] = prev_user.id
    token['new_user_id'] = new_user.id
    service = UserTransferService()
    service.user = new_user
    service.token = token

    # act
    user = service._get_valid_prev_user()

    # assert
    assert user.id == prev_user.id


def test_get_valid_prev_user__inactive__raise_exception():

    # arrange
    new_account = create_test_account(name='new')
    account_owner = create_test_user(
        account=new_account,
        email='owner@test.test',
        is_account_owner=True
    )
    new_user = create_invited_user(
        user=account_owner,
        email='transferred@tes.test'
    )
    prev_account = create_test_account(name='new')
    prev_account_owner = create_test_user(
        account=prev_account,
        email='prev_owner@test.test',
        is_account_owner=True
    )
    prev_user = create_invited_user(
        user=prev_account_owner,
        email='transferred@tes.test',
        status=UserStatus.INACTIVE
    )
    token = TransferToken()
    token['prev_user_id'] = prev_user.id
    token['new_user_id'] = new_user.id
    service = UserTransferService()
    service.user = new_user
    service.token = token

    # act
    with pytest.raises(exceptions.ExpiredTransferTokenException):
        service._get_valid_prev_user()


def test_get_valid_token__ok():

    # arrange
    new_account = create_test_account(name='new')
    new_user = create_test_user(account=new_account)
    prev_account = create_test_account(name='new')
    prev_user = create_test_user(
        email='transferred@tes.test',
        account=prev_account
    )
    token = TransferToken()
    token['prev_user_id'] = prev_user.id
    token['new_user_id'] = new_user.id
    service = UserTransferService()
    service.token = token

    # act
    valid_token = service._get_valid_token(str(token))

    # assert
    assert valid_token['new_user_id'] == token['new_user_id']
    assert valid_token['prev_user_id'] == token['prev_user_id']


def test_get_valid_token__invalid__raise_exception():

    # arrange
    service = UserTransferService()

    # act
    with pytest.raises(exceptions.InvalidTransferTokenException):
        service._get_valid_token('sad123.sd@!23sd.sadas123')


def test_after_transfer_actions__premium__ok(mocker):

    # arrange
    account = create_test_account(plan=BillingPlanType.PREMIUM)
    user = create_test_user(account=account)
    prev_user = create_test_user(email='prev@test.test')
    users_transferred_mock = mocker.patch(
        'pneumatic_backend.analytics.services.AnalyticService.'
        'users_transferred'
    )
    identify_mock = mocker.patch(
        'pneumatic_backend.accounts.services.user_transfer'
        '.UserTransferService.identify'
    )
    group_mock = mocker.patch(
        'pneumatic_backend.accounts.services.user_transfer'
        '.UserTransferService.group'
    )
    increase_plan_users_mock = mocker.patch(
        'pneumatic_backend.payment.tasks.increase_plan_users.delay'
    )
    settings_mock = mocker.patch(
        'pneumatic_backend.accounts.services.user_transfer.settings'
    )
    settings_mock.PROJECT_CONF = {'BILLING': True}
    service = UserTransferService()
    service.user = user
    service.prev_user = prev_user

    # act
    service._after_transfer_actions()

    # assert
    identify_mock.assert_called_once_with(service.user)
    assert group_mock.call_count == 2
    assert group_mock.has_calls([
        mocker.call(service.prev_user),
        mocker.call(service.user),
    ])
    users_transferred_mock.assert_called_once_with(
        user=service.prev_user
    )
    increase_plan_users_mock.assert_called_once_with(
        account_id=user.account_id,
        is_superuser=False,
        auth_type=AuthTokenType.USER
    )


def test_after_transfer_actions__unlimited__ok(mocker):

    # arrange
    account = create_test_account(plan=BillingPlanType.UNLIMITED)
    user = create_test_user(account=account)
    prev_user = create_test_user(email='prev@test.test')
    users_transferred_mock = mocker.patch(
        'pneumatic_backend.analytics.services.AnalyticService.'
        'users_transferred'
    )
    identify_mock = mocker.patch(
        'pneumatic_backend.accounts.services.user_transfer'
        '.UserTransferService.identify'
    )
    group_mock = mocker.patch(
        'pneumatic_backend.accounts.services.user_transfer'
        '.UserTransferService.group'
    )
    increase_plan_users_mock = mocker.patch(
        'pneumatic_backend.payment.tasks.increase_plan_users.delay'
    )
    settings_mock = mocker.patch(
        'pneumatic_backend.accounts.services.user_transfer.settings'
    )
    settings_mock.PROJECT_CONF = {'BILLING': True}
    service = UserTransferService()
    service.user = user
    service.prev_user = prev_user

    # act
    service._after_transfer_actions()

    # assert
    identify_mock.assert_called_once_with(service.user)
    assert group_mock.call_count == 2
    assert group_mock.has_calls([
        mocker.call(service.prev_user),
        mocker.call(service.user),
    ])
    users_transferred_mock.assert_called_once_with(
        user=service.prev_user
    )
    increase_plan_users_mock.assert_not_called()


@pytest.mark.parametrize('plan', BillingPlanType.PAYMENT_PLANS)
def test_after_transfer_actions__disable_billing__ok(mocker, plan):

    # arrange
    account = create_test_account(
        plan=plan,
        billing_sync=True
    )
    user = create_test_user(account=account, is_account_owner=True)
    prev_user = create_test_user(email='prev@test.test')
    users_transferred_mock = mocker.patch(
        'pneumatic_backend.analytics.services.AnalyticService.'
        'users_transferred'
    )
    identify_mock = mocker.patch(
        'pneumatic_backend.accounts.services.user_transfer'
        '.UserTransferService.identify'
    )
    group_mock = mocker.patch(
        'pneumatic_backend.accounts.services.user_transfer'
        '.UserTransferService.group'
    )
    increase_plan_users_mock = mocker.patch(
        'pneumatic_backend.payment.tasks.increase_plan_users.delay'
    )
    settings_mock = mocker.patch(
        'pneumatic_backend.accounts.services.user_transfer.settings'
    )
    settings_mock.PROJECT_CONF = {'BILLING': False}
    service = UserTransferService()
    service.user = user
    service.prev_user = prev_user

    # act
    service._after_transfer_actions()

    # assert
    identify_mock.assert_called_once_with(service.user)
    assert group_mock.call_count == 2
    assert group_mock.has_calls([
        mocker.call(service.prev_user),
        mocker.call(service.user),
    ])
    users_transferred_mock.assert_called_once_with(
        user=service.prev_user
    )
    increase_plan_users_mock.assert_not_called()


def test_deactivate_prev_user__ok(mocker):

    # arrange
    user = create_test_user()
    prev_account = create_test_account(plan=BillingPlanType.FREEMIUM)
    create_test_user(
        email='prev_owner@test.test',
        account=prev_account
    )
    prev_user = create_test_user(
        account=prev_account,
        email='prev@test.test',
        is_account_owner=False
    )

    service = UserTransferService()
    service.user = user
    service.prev_user = prev_user
    reassign_everywhere_mock = mocker.patch(
        'pneumatic_backend.accounts.services.reassign.ReassignService.'
        'reassign_everywhere'
    )
    remove_user_from_draft_mock = mocker.patch(
        'pneumatic_backend.accounts.services.user_transfer'
        '.remove_user_from_draft'
    )
    delete_pending_invites_mock = mocker.patch(
        'pneumatic_backend.accounts.services.user_transfer'
        '.UserTransferService._delete_prev_user_pending_invites'
    )
    cancel_subscription_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService.cancel_subscription'
    )
    deactivate_mock = mocker.patch(
        'pneumatic_backend.accounts.services.user.UserService.deactivate'
    )
    settings_mock = mocker.patch(
        'pneumatic_backend.accounts.services.user_transfer.settings'
    )
    settings_mock.PROJECT_CONF = {'BILLING': True}

    # act
    service._deactivate_prev_user()

    # assert
    reassign_everywhere_mock.assert_called_once()
    remove_user_from_draft_mock.assert_called_once_with(
        account_id=prev_user.account.id,
        user_id=prev_user.id
    )
    delete_pending_invites_mock.assert_called_once()
    cancel_subscription_mock.assert_not_called()
    deactivate_mock.assert_called_once_with(
        prev_user,
        skip_validation=True
    )


def test_deactivate_prev_user__last_user_freemium__not_reassign(mocker):

    # arrange
    user = create_test_user()
    prev_account = create_test_account(plan=BillingPlanType.FREEMIUM)
    prev_user = create_test_user(
        account=prev_account,
        email='prev@test.test'
    )

    service = UserTransferService()
    service.user = user
    service.prev_user = prev_user
    reassign_everywhere_mock = mocker.patch(
        'pneumatic_backend.accounts.services.reassign.ReassignService.'
        'reassign_everywhere'
    )
    remove_user_from_draft_mock = mocker.patch(
        'pneumatic_backend.accounts.services.user_transfer'
        '.remove_user_from_draft'
    )
    delete_pending_invites_mock = mocker.patch(
        'pneumatic_backend.accounts.services.user_transfer'
        '.UserTransferService._delete_prev_user_pending_invites'
    )
    cancel_subscription_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService.cancel_subscription'
    )
    deactivate_mock = mocker.patch(
        'pneumatic_backend.accounts.services.user.UserService.deactivate'
    )
    settings_mock = mocker.patch(
        'pneumatic_backend.accounts.services.user_transfer.settings'
    )
    settings_mock.PROJECT_CONF = {'BILLING': True}

    # act
    service._deactivate_prev_user()

    # assert
    reassign_everywhere_mock.assert_not_called()
    remove_user_from_draft_mock.assert_called_once_with(
        account_id=prev_user.account.id,
        user_id=prev_user.id
    )
    delete_pending_invites_mock.assert_called_once()
    cancel_subscription_mock.assert_not_called()
    deactivate_mock.assert_called_once_with(
        prev_user,
        skip_validation=True
    )


def test_deactivate_prev_user__cancel_subscription__ok(mocker):

    # arrange
    user = create_test_user()
    prev_account = create_test_account(plan=BillingPlanType.PREMIUM)
    create_test_user(
        email='prev_owner@test.test',
        account=prev_account
    )
    prev_user = create_test_user(
        account=prev_account,
        email='prev@test.test',
        is_account_owner=True
    )

    service = UserTransferService()
    service.user = user
    service.prev_user = prev_user
    reassign_everywhere_mock = mocker.patch(
        'pneumatic_backend.accounts.services.reassign.ReassignService.'
        'reassign_everywhere'
    )
    remove_user_from_draft_mock = mocker.patch(
        'pneumatic_backend.accounts.services.user_transfer'
        '.remove_user_from_draft'
    )
    delete_pending_invites_mock = mocker.patch(
        'pneumatic_backend.accounts.services.user_transfer'
        '.UserTransferService._delete_prev_user_pending_invites'
    )
    stripe_service_init_mock = mocker.patch.object(
        StripeService,
        attribute='__init__',
        return_value=None
    )
    cancel_subscription_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService.cancel_subscription'
    )
    deactivate_mock = mocker.patch(
        'pneumatic_backend.accounts.services.user.UserService.deactivate'
    )
    settings_mock = mocker.patch(
        'pneumatic_backend.accounts.services.user_transfer.settings'
    )
    settings_mock.PROJECT_CONF = {'BILLING': True}

    # act
    service._deactivate_prev_user()

    # assert
    reassign_everywhere_mock.assert_called_once()
    remove_user_from_draft_mock.assert_called_once_with(
        account_id=prev_user.account.id,
        user_id=prev_user.id
    )
    delete_pending_invites_mock.assert_called_once()
    stripe_service_init_mock.assert_called_once_with(
        user=prev_user,
        is_superuser=False,
        auth_type=AuthTokenType.USER
    )
    cancel_subscription_mock.assert_called_once()
    deactivate_mock.assert_called_once_with(
        prev_user,
        skip_validation=True
    )


@pytest.mark.parametrize('plan', BillingPlanType.PAYMENT_PLANS)
def test_deactivate_prev_user__disable_billing__ok(plan, mocker):

    # arrange
    user = create_test_user()
    prev_account = create_test_account(
        plan=plan,
        billing_sync=True
    )
    create_test_user(
        email='prev_owner@test.test',
        account=prev_account
    )
    prev_user = create_test_user(
        account=prev_account,
        email='prev@test.test',
        is_account_owner=False
    )

    service = UserTransferService()
    service.user = user
    service.prev_user = prev_user
    reassign_everywhere_mock = mocker.patch(
        'pneumatic_backend.accounts.services.reassign.ReassignService.'
        'reassign_everywhere'
    )
    remove_user_from_draft_mock = mocker.patch(
        'pneumatic_backend.accounts.services.user_transfer'
        '.remove_user_from_draft'
    )
    delete_pending_invites_mock = mocker.patch(
        'pneumatic_backend.accounts.services.user_transfer'
        '.UserTransferService._delete_prev_user_pending_invites'
    )
    cancel_subscription_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService.cancel_subscription'
    )
    deactivate_mock = mocker.patch(
        'pneumatic_backend.accounts.services.user.UserService.deactivate'
    )
    settings_mock = mocker.patch(
        'pneumatic_backend.accounts.services.user_transfer.settings'
    )
    settings_mock.PROJECT_CONF = {'BILLING': False}

    # act
    service._deactivate_prev_user()

    # assert
    reassign_everywhere_mock.assert_called_once()
    remove_user_from_draft_mock.assert_called_once_with(
        account_id=prev_user.account.id,
        user_id=prev_user.id
    )
    delete_pending_invites_mock.assert_called_once()
    cancel_subscription_mock.assert_not_called()
    deactivate_mock.assert_called_once_with(
        prev_user,
        skip_validation=True
    )


@pytest.mark.parametrize('is_active', (True, False))
@pytest.mark.parametrize('is_account_owner', (True, False))
def test_accept_transfer__template_owner_in_template__ok(
    api_client,
    is_active,
    is_account_owner,
):

    # arrange
    account_1 = create_test_account(name='transfer from')
    account_2 = create_test_account(
        name='transfer to',
        plan=BillingPlanType.FREEMIUM
    )
    user_to_transfer = create_test_user(
        account=account_1,
        email='user_to_transfer@test.test',
        is_account_owner=is_account_owner
    )
    account_2_owner = create_test_user(
        account=account_2,
        is_account_owner=True,
        email='owner@test.test'
    )
    current_url = 'some_url'
    service = UserInviteService(
        request_user=account_2_owner,
        current_url=current_url
    )
    service.invite_user(
        email=user_to_transfer.email,
        invited_from=SourceType.EMAIL
    )
    account_2_new_user = account_2.users.get(email=user_to_transfer.email)
    token = TransferToken()
    token['prev_user_id'] = user_to_transfer.id
    token['new_user_id'] = account_2_new_user.id
    api_client.token_authenticate(account_2_owner)

    response_create = api_client.post(
        path='/templates',
        data={
            'name': 'Template',
            'template_owners': [account_2_owner.id, account_2_new_user.id],
            'is_active': True,
            'kickoff': {},
            'tasks': [
                {
                    'number': 1,
                    'name': 'First step',
                    'raw_performers': [
                        {
                            'type': PerformerType.USER,
                            'source_id': str(account_2_new_user.id)
                        }
                    ]
                }
            ]
        }
    )
    service = UserTransferService()
    service.accept_transfer(
        user_id=account_2_new_user.id,
        token_str=str(token)
    )

    # act
    response = api_client.get(f'/templates/{response_create.data["id"]}')

    # assert
    assert response_create.status_code == 200
    assert response.status_code == 200
    assert account_2_new_user.id in response.data['template_owners']
    raw_performer_data = response.data['tasks'][0]['raw_performers'][0]
    assert raw_performer_data['source_id'] == str(
        account_2_new_user.id
    )


def test_activate_user__ok(mocker):

    # arrange
    email = 'transfer@test.test'
    prev_user = create_test_user(
        email=email,
        first_name='old first name',
        last_name='old last name',
    )
    prev_user.status = UserStatus.INACTIVE
    prev_user.save(update_fields=['status'])
    account_2 = create_test_account(
        name='transfer to',
        plan=BillingPlanType.FREEMIUM
    )
    account_2_owner = create_test_user(
        account=account_2,
        is_account_owner=True,
        email='owner@test.test'
    )
    account_2_new_user = create_invited_user(
        user=account_2_owner,
        email=email,
    )

    service = UserTransferService()
    service.user = account_2_new_user
    service.prev_user = prev_user

    account_service_init_mock = mocker.patch.object(
        AccountService,
        attribute='__init__',
        return_value=None
    )
    update_users_counts_mock = mocker.patch(
        'pneumatic_backend.accounts.services.'
        'AccountService.update_users_counts'
    )

    # act
    service._activate_user()

    # assert
    account_2_new_user.refresh_from_db()
    assert account_2_new_user.is_active is True
    assert account_2_new_user.status == UserStatus.ACTIVE
    assert account_2_new_user.first_name == prev_user.first_name
    assert account_2_new_user.last_name == prev_user.last_name
    account_service_init_mock.assert_called_once_with(
        instance=account_2_new_user.account,
        user=account_2_new_user
    )
    update_users_counts_mock.assert_called_once()
