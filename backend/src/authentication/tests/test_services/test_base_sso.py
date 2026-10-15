import pytest

from src.accounts.enums import UserStatus
from src.authentication.enums import AuthTokenType
from src.authentication.messages import MSG_AU_0021
from src.authentication.services.auth0 import Auth0Service
from src.authentication.services.okta import OktaService
from src.processes.tests.fixtures import create_test_admin

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize('service_class', (Auth0Service, OktaService))
@pytest.mark.parametrize(
    'statuses,expected_status',
    (
        ((), None),
        ((UserStatus.INACTIVE,), UserStatus.INACTIVE),
        ((UserStatus.ACTIVE,), UserStatus.ACTIVE),
        ((UserStatus.INVITED,), UserStatus.INVITED),
        ((UserStatus.INACTIVE, UserStatus.ACTIVE), UserStatus.ACTIVE),
        ((UserStatus.INACTIVE, UserStatus.INVITED), UserStatus.INVITED),
        ((UserStatus.INVITED, UserStatus.ACTIVE), UserStatus.ACTIVE),
    ),
)
def test_complete_authentication__user_status_and_login_audit(
    mocker,
    service_class,
    statuses,
    expected_status,
):
    # arrange
    email = 'sso@example.com'
    users = {
        status: create_test_admin(email=email, status=status)
        for status in statuses
    }
    user = users.get(expected_status) or mocker.Mock()
    user_data = {'email': email}
    mocker.patch.object(service_class, '_get_config')
    service = service_class()
    activate_mock = mocker.patch.object(
        service, '_activate_invited_user', return_value=user,
    )
    create_mock = mocker.patch.object(
        service, '_create_new_user', return_value=user,
    )
    token_mock = mocker.patch(
        'src.authentication.services.base_sso.AuthService.get_auth_token',
        return_value='test_token',
    )
    save_mock = mocker.patch.object(service, 'save_tokens_for_user')
    analytics_mock = mocker.patch(
        'src.authentication.services.base_sso.AnalyticService.users_logged_in',
    )
    audit_mock = mocker.patch(
        'src.authentication.services.base_sso.'
        'AuditEventService.user_logged_in',
    )

    # act
    if expected_status == UserStatus.INACTIVE:
        with pytest.raises(service.exception_class) as exc_info:
            service._complete_authentication(
                user_data, 'Test-Agent', '1.2.3.4',
            )
        result = None
    else:
        result = service._complete_authentication(
            user_data, 'Test-Agent', '1.2.3.4',
        )

    # assert
    if expected_status == UserStatus.INACTIVE:
        assert exc_info.value.message == MSG_AU_0021
        token_mock.assert_not_called()
        save_mock.assert_not_called()
        analytics_mock.assert_not_called()
    else:
        assert result == (user, 'test_token')
        token_mock.assert_called_once_with(
            user=user, user_agent='Test-Agent', user_ip='1.2.3.4',
        )
        save_mock.assert_called_once_with(user)
        analytics_mock.assert_called_once_with(
            user=user,
            is_superuser=False,
            auth_type=AuthTokenType.USER,
            source=service.source,
        )
    if expected_status == UserStatus.INVITED:
        activate_mock.assert_called_once_with(user, user_data)
    else:
        activate_mock.assert_not_called()
    if expected_status is None:
        create_mock.assert_called_once_with(user_data)
    else:
        create_mock.assert_not_called()
    if expected_status in (UserStatus.ACTIVE, UserStatus.INVITED):
        audit_mock.assert_called_once_with(user=user, source=service.source)
    else:
        audit_mock.assert_not_called()
