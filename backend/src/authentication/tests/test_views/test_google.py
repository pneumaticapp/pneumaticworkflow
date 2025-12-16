import pytest

from src.processes.tests.fixtures import (
    create_test_admin,
    create_test_owner,
)

pytestmark = pytest.mark.django_db


class TestGoogleAuthViewSet:
    def test_token__sso_enabled_not_owner__raise_exception(
        self,
        mocker,
        api_client,
    ):
        # arrange
        mocker.patch(
            'src.authentication.views.google.'
            'GoogleAuthPermission.has_permission',
            return_value=True,
        )
        user = create_test_admin()
        user_data = {
            'email': user.email,
            'first_name': 'Test',
            'last_name': 'User',
        }
        google_service_mock = mocker.patch(
            'src.authentication.services.google.'
            'GoogleAuthService.get_user_data',
            return_value=user_data,
        )
        settings_mock = mocker.patch(
            'src.authentication.views.mixins.settings',
        )
        settings_mock.PROJECT_CONF = {'SSO_AUTH': True}

        auth_response = {
            'code': '4/0AbUR2VMeHxU...',
            'state': 'test_state',
        }

        # act
        response = api_client.get(
            '/auth/google/token',
            data=auth_response,
        )

        # assert
        assert response.status_code == 400
        google_service_mock.assert_called_once()

    def test_token__sso_enabled_owner__ok(
        self,
        mocker,
        api_client,
    ):
        # arrange
        mocker.patch(
            'src.authentication.views.google.'
            'GoogleAuthPermission.has_permission',
            return_value=True,
        )
        user = create_test_owner()
        user_data = {
            'email': user.email,
            'first_name': 'Test',
            'last_name': 'User',
        }
        google_service_mock = mocker.patch(
            'src.authentication.services.google.'
            'GoogleAuthService.get_user_data',
            return_value=user_data,
        )
        save_tokens_mock = mocker.patch(
            'src.authentication.services.google.'
            'GoogleAuthService.save_tokens_for_user',
        )
        update_contacts_mock = mocker.patch(
            'src.authentication.views.google.'
            'update_google_contacts.delay',
        )
        settings_mock = mocker.patch(
            'src.authentication.views.mixins.settings',
        )
        settings_mock.PROJECT_CONF = {'SSO_AUTH': True}

        auth_response = {
            'code': '4/0AbUR2VMeHxU...',
            'state': 'test_state',
        }

        # act
        response = api_client.get(
            '/auth/google/token',
            data=auth_response,
        )

        # assert
        assert response.status_code == 200
        assert 'token' in response.data
        google_service_mock.assert_called_once()
        save_tokens_mock.assert_called_once()
        update_contacts_mock.assert_called_once_with(user.id)
