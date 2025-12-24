import pytest

from src.authentication.services.okta_logout import OktaLogoutService

pytestmark = pytest.mark.django_db


def test_logout_okta__valid_data__ok(
    mocker,
    api_client,
):
    # arrange
    mocker.patch(
        'src.authentication.views.okta_logout.SSOPermission.'
        'has_permission',
        return_value=True,
    )
    okta_logout_service_init_mock = mocker.patch.object(
        OktaLogoutService,
        attribute='__init__',
        return_value=None,
    )
    process_logout_mock = mocker.patch(
        'src.authentication.services.okta_logout.'
        'OktaLogoutService.process_logout',
    )
    sub_id_data = {
        'format': 'iss_sub',
        'iss': 'https://dev-123456.okta.com/oauth2/default',
        'sub': '00uid4BxXw6I6TV4m0g3',
    }
    request_data = {
        'sub_id': sub_id_data,
    }

    # act
    response = api_client.post(
        '/auth/okta/logout',
        data=request_data,
        format='json',
    )

    # assert
    assert response.status_code == 204
    okta_logout_service_init_mock.assert_called_once()
    process_logout_mock.assert_called_once_with(
        iss=sub_id_data['iss'],
        sub=sub_id_data['sub'],
    )


def test_logout_okta__invalid_data__ok(
    mocker,
    api_client,
):
    # arrange
    mocker.patch(
        'src.authentication.views.okta_logout.SSOPermission.'
        'has_permission',
        return_value=True,
    )
    okta_logout_service_init_mock = mocker.patch.object(
        OktaLogoutService,
        attribute='__init__',
        return_value=None,
    )
    process_logout_mock = mocker.patch(
        'src.authentication.services.okta_logout.'
        'OktaLogoutService.process_logout',
    )
    request_data = {
        'invalid_field': 'invalid_value',
    }

    # act
    response = api_client.post(
        '/auth/okta/logout',
        data=request_data,
        format='json',
    )

    # assert
    assert response.status_code == 204
    okta_logout_service_init_mock.assert_not_called()
    process_logout_mock.assert_not_called()


def test_logout_okta__disable_sso_auth__permission_denied(
    mocker,
    api_client,
):
    # arrange
    mocker.patch(
        'src.authentication.views.okta_logout.SSOPermission.'
        'has_permission',
        return_value=False,
    )
    okta_logout_service_init_mock = mocker.patch.object(
        OktaLogoutService,
        attribute='__init__',
        return_value=None,
    )
    process_logout_mock = mocker.patch(
        'src.authentication.services.okta_logout.'
        'OktaLogoutService.process_logout',
    )
    sub_id_data = {
        'format': 'iss_sub',
        'iss': 'https://dev-123456.okta.com/oauth2/default',
        'sub': '00uid4BxXw6I6TV4m0g3',
    }
    request_data = {
        'sub_id': sub_id_data,
    }

    # act
    response = api_client.post(
        '/auth/okta/logout',
        data=request_data,
        format='json',
    )

    # assert
    assert response.status_code == 403
    okta_logout_service_init_mock.assert_not_called()
    process_logout_mock.assert_not_called()


def test_logout_okta__missing_sub_id__ok(
    mocker,
    api_client,
):
    # arrange
    mocker.patch(
        'src.authentication.views.okta_logout.SSOPermission.'
        'has_permission',
        return_value=True,
    )
    okta_logout_service_init_mock = mocker.patch.object(
        OktaLogoutService,
        attribute='__init__',
        return_value=None,
    )
    process_logout_mock = mocker.patch(
        'src.authentication.services.okta_logout.'
        'OktaLogoutService.process_logout',
    )
    request_data = {}

    # act
    response = api_client.post(
        '/auth/okta/logout',
        data=request_data,
        format='json',
    )

    # assert
    assert response.status_code == 204
    okta_logout_service_init_mock.assert_not_called()
    process_logout_mock.assert_not_called()
