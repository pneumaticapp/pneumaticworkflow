import pytest

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
    process_okta_logout_mock = mocker.patch(
        'src.authentication.views.okta_logout.process_okta_logout.delay',
    )
    sub_id_data = {
        'format': 'iss_sub',
        'iss': 'https://dev-123456.okta.com/oauth2/default',
        'sub': '00uid4BxXw6I6TV4m0g3',
    }
    request_data = {
        'sub_id': sub_id_data,
    }
    logout_token = 'test_logout_token'

    # act
    response = api_client.post(
        '/auth/okta/logout',
        data=request_data,
        format='json',
        HTTP_AUTHORIZATION=f'Bearer {logout_token}',
    )

    # assert
    assert response.status_code == 204
    process_okta_logout_mock.assert_called_once_with(
        logout_token=logout_token,
        request_data={
            'format': sub_id_data['format'],
            'sub_id_data': sub_id_data,
        },
    )


def test_logout_okta__invalid_structure__ok(
    mocker,
    api_client,
):
    # arrange
    mocker.patch(
        'src.authentication.views.okta_logout.SSOPermission.'
        'has_permission',
        return_value=True,
    )
    capture_sentry_mock = mocker.patch(
        'src.authentication.views.okta_logout.capture_sentry_message',
    )
    process_okta_logout_mock = mocker.patch(
        'src.authentication.views.okta_logout.process_okta_logout.delay',
    )
    # Invalid structure - missing required fields
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
    capture_sentry_mock.assert_called_once()
    process_okta_logout_mock.assert_not_called()


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
    process_okta_logout_mock = mocker.patch(
        'src.authentication.views.okta_logout.process_okta_logout.delay',
    )
    sub_id_data = {
        'format': 'iss_sub',
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
    process_okta_logout_mock.assert_not_called()


def test_logout_okta__empty_data__ok(
    mocker,
    api_client,
):
    # arrange
    mocker.patch(
        'src.authentication.views.okta_logout.SSOPermission.'
        'has_permission',
        return_value=True,
    )
    capture_sentry_mock = mocker.patch(
        'src.authentication.views.okta_logout.capture_sentry_message',
    )
    process_okta_logout_mock = mocker.patch(
        'src.authentication.views.okta_logout.process_okta_logout.delay',
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
    # Empty data fails validation, logs to Sentry
    capture_sentry_mock.assert_called_once()
    process_okta_logout_mock.assert_not_called()


def test_logout_okta__invalid_authorization_header_format__ok(
    mocker,
    api_client,
):
    # arrange
    mocker.patch(
        'src.authentication.views.okta_logout.SSOPermission.'
        'has_permission',
        return_value=True,
    )
    capture_sentry_mock = mocker.patch(
        'src.authentication.views.okta_logout.capture_sentry_message',
    )
    process_okta_logout_mock = mocker.patch(
        'src.authentication.views.okta_logout.process_okta_logout.delay',
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
        HTTP_AUTHORIZATION='InvalidFormat token',
    )

    # assert
    assert response.status_code == 204
    capture_sentry_mock.assert_called_once()
    assert 'Missing or invalid Authorization header' in (
        capture_sentry_mock.call_args[1]['message']
    )
    process_okta_logout_mock.assert_not_called()


def test_logout_okta__authorization_header_one_word__ok(
    mocker,
    api_client,
):
    # arrange
    mocker.patch(
        'src.authentication.views.okta_logout.SSOPermission.'
        'has_permission',
        return_value=True,
    )
    capture_sentry_mock = mocker.patch(
        'src.authentication.views.okta_logout.capture_sentry_message',
    )
    process_okta_logout_mock = mocker.patch(
        'src.authentication.views.okta_logout.process_okta_logout.delay',
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
        HTTP_AUTHORIZATION='token_without_bearer',
    )

    # assert
    assert response.status_code == 204
    capture_sentry_mock.assert_called_once()
    assert 'Missing or invalid Authorization header' in (
        capture_sentry_mock.call_args[1]['message']
    )
    process_okta_logout_mock.assert_not_called()


def test_logout_okta__email_format__ok(
    mocker,
    api_client,
):
    # arrange
    mocker.patch(
        'src.authentication.views.okta_logout.SSOPermission.'
        'has_permission',
        return_value=True,
    )
    process_okta_logout_mock = mocker.patch(
        'src.authentication.views.okta_logout.process_okta_logout.delay',
    )
    sub_id_data = {
        'format': 'email',
        'email': 'test@example.com',
    }
    request_data = {
        'sub_id': sub_id_data,
    }
    logout_token = 'test_logout_token'

    # act
    response = api_client.post(
        '/auth/okta/logout',
        data=request_data,
        format='json',
        HTTP_AUTHORIZATION=f'Bearer {logout_token}',
    )

    # assert
    assert response.status_code == 204
    process_okta_logout_mock.assert_called_once_with(
        logout_token=logout_token,
        request_data={
            'format': sub_id_data['format'],
            'sub_id_data': sub_id_data,
        },
    )
