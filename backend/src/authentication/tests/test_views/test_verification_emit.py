import pytest

from src.accounts.tokens import VerificationToken
from src.authentication import messages
from src.authentication.enums import AuthTokenType
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_admin,
    create_test_owner,
)
from src.utils.validation import ErrorCode

pytestmark = pytest.mark.django_db


def test_verify__not_verified__audit_account_verified(
    mocker,
    api_client,
):

    # arrange
    account = create_test_account(is_verified=False)
    owner = create_test_owner(account=account)
    token = str(VerificationToken.for_user(owner))
    account_verified_mock = mocker.patch(
        'src.authentication.views.verification.'
        'AnalyticService.account_verified',
    )
    audit_account_verified_mock = mocker.patch(
        'src.authentication.views.verification.AuditEventService.'
        'account_verified',
    )

    # act
    response = api_client.get(f'/auth/verification?token={token}')

    # assert
    assert response.status_code == 204
    account.refresh_from_db()
    assert account.is_verified is True
    audit_account_verified_mock.assert_called_once_with(user=owner)
    account_verified_mock.assert_called_once_with(
        user=owner,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )


def test_verify__already_verified__audit_not_called(
    mocker,
    api_client,
):

    # arrange
    account = create_test_account(is_verified=True)
    owner = create_test_owner(account=account)
    token = str(VerificationToken.for_user(owner))
    account_verified_mock = mocker.patch(
        'src.authentication.views.verification.'
        'AnalyticService.account_verified',
    )
    audit_account_verified_mock = mocker.patch(
        'src.authentication.views.verification.AuditEventService.'
        'account_verified',
    )

    # act
    response = api_client.get(f'/auth/verification?token={token}')

    # assert
    assert response.status_code == 204
    audit_account_verified_mock.assert_not_called()
    account_verified_mock.assert_not_called()


def test_verify__wrong_token__audit_not_called(
    mocker,
    api_client,
):

    # arrange
    account = create_test_account(is_verified=False)
    create_test_owner(account=account)
    account_verified_mock = mocker.patch(
        'src.authentication.views.verification.'
        'AnalyticService.account_verified',
    )
    audit_account_verified_mock = mocker.patch(
        'src.authentication.views.verification.AuditEventService.'
        'account_verified',
    )

    # act
    response = api_client.get('/auth/verification?token=12345')

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == messages.MSG_AU_0008
    assert response.data['details'] == {}
    account.refresh_from_db()
    assert account.is_verified is False
    audit_account_verified_mock.assert_not_called()
    account_verified_mock.assert_not_called()


def test_resend__not_verified__audit_verification_resent(
    mocker,
    api_client,
    verification_check_true_mock,
):

    """ An admin asks for the letter, the letter goes to the owner:
        the actor is the admin, the target is the owner. """

    # arrange
    account = create_test_account(is_verified=False)
    owner = create_test_owner(account=account)
    admin = create_test_admin(account=account)
    send_verification_mock = mocker.patch(
        'src.authentication.views.verification.'
        'send_verification_notification.delay',
    )
    verification_resent_mock = mocker.patch(
        'src.authentication.views.verification.AuditEventService.'
        'verification_resent',
    )
    api_client.token_authenticate(admin)

    # act
    response = api_client.post('/auth/resend-verification')

    # assert
    assert response.status_code == 200
    assert response.data['email'] == owner.email
    verification_resent_mock.assert_called_once_with(
        user=admin,
        auth_type=AuthTokenType.USER,
        account_owner=owner,
    )
    send_verification_mock.assert_called_once_with(
        user_id=owner.id,
        user_email=owner.email,
        account_id=account.id,
        user_first_name=owner.first_name,
        token=mocker.ANY,
        logo_lg=account.logo_lg,
    )


def test_resend__verification_check_off__audit_not_called(
    mocker,
    api_client,
    settings,
):

    # arrange
    settings.VERIFICATION_CHECK = False
    account = create_test_account(is_verified=False)
    owner = create_test_owner(account=account)
    send_verification_mock = mocker.patch(
        'src.authentication.views.verification.'
        'send_verification_notification.delay',
    )
    verification_resent_mock = mocker.patch(
        'src.authentication.views.verification.AuditEventService.'
        'verification_resent',
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.post('/auth/resend-verification')

    # assert
    assert response.status_code == 200
    verification_resent_mock.assert_not_called()
    send_verification_mock.assert_not_called()


def test_resend__already_verified__audit_not_called(
    mocker,
    api_client,
    verification_check_true_mock,
):

    # arrange
    account = create_test_account(is_verified=True)
    owner = create_test_owner(account=account)
    send_verification_mock = mocker.patch(
        'src.authentication.views.verification.'
        'send_verification_notification.delay',
    )
    verification_resent_mock = mocker.patch(
        'src.authentication.views.verification.AuditEventService.'
        'verification_resent',
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.post('/auth/resend-verification')

    # assert
    assert response.status_code == 200
    verification_resent_mock.assert_not_called()
    send_verification_mock.assert_not_called()
