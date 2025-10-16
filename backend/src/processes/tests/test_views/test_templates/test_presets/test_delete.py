import pytest

from src.authentication.enums import AuthTokenType
from src.processes.enums import PresetType
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_admin,
    create_test_template,
    create_test_template_preset,
)

pytestmark = pytest.mark.django_db


class TestTemplatePresetDeleteView:

    def test_delete__ok(self, api_client, mocker):
        # arrange
        account = create_test_account()
        user = create_test_admin(account=account)
        template = create_test_template(user, is_active=True)
        preset = create_test_template_preset(
            template=template,
            author=user,
            type=PresetType.PERSONAL,
        )

        api_client.token_authenticate(user)

        mock_service = mocker.MagicMock()

        service_class_mock = mocker.patch(
            'src.processes.views.template_preset.TemplatePresetService',
            return_value=mock_service,
        )

        # act
        response = api_client.delete(f'/templates/presets/{preset.id}')

        # assert
        assert response.status_code == 204
        service_class_mock.assert_called_once_with(
            user=user,
            instance=preset,
            is_superuser=False,
            auth_type=AuthTokenType.USER,
        )
        mock_service.delete.assert_called_once()

    def test_delete__preset_not_found__permission_denied(
        self,
        api_client,
        mocker,
    ):
        # arrange
        account = create_test_account()
        user = create_test_admin(account=account)
        api_client.token_authenticate(user)

        fake_preset_id = 99999

        service_class_mock = mocker.patch(
            'src.processes.views.template_preset.TemplatePresetService',
        )

        # act
        response = api_client.delete(f'/templates/presets/{fake_preset_id}')

        # assert
        assert response.status_code == 403
        service_class_mock.assert_not_called()

    def test_delete__not_authenticated__unauthorized(self, api_client, mocker):
        # arrange
        fake_preset_id = 1

        service_class_mock = mocker.patch(
            'src.processes.views.template_preset.TemplatePresetService',
        )

        # act
        response = api_client.delete(f'/templates/presets/{fake_preset_id}')

        # assert
        assert response.status_code == 401
        service_class_mock.assert_not_called()

    def test_delete__not_author__permission_denied(self, api_client, mocker):
        # arrange
        account = create_test_account()
        user1 = create_test_admin(account=account)
        user2 = create_test_admin(account=account, email='user2@test.test')
        template = create_test_template(user1, is_active=True)
        preset = create_test_template_preset(
            template=template,
            author=user1,
            type=PresetType.PERSONAL,
        )

        api_client.token_authenticate(user2)

        service_class_mock = mocker.patch(
            'src.processes.views.template_preset.TemplatePresetService',
        )

        # act
        response = api_client.delete(f'/templates/presets/{preset.id}')

        # assert
        assert response.status_code == 403
        service_class_mock.assert_not_called()

    def test_delete__different_account__permission_denied(
        self,
        api_client,
        mocker,
    ):
        # arrange
        account1 = create_test_account()
        account2 = create_test_account()
        user1 = create_test_admin(account=account1)
        user2 = create_test_admin(account=account2, email='user2@test.test')

        template = create_test_template(user1, is_active=True)
        preset = create_test_template_preset(
            template=template,
            author=user1,
            type=PresetType.PERSONAL,
        )

        api_client.token_authenticate(user2)

        service_class_mock = mocker.patch(
            'src.processes.views.template_preset.TemplatePresetService',
        )

        # act
        response = api_client.delete(f'/templates/presets/{preset.id}')

        # assert
        assert response.status_code == 403
        service_class_mock.assert_not_called()

    def test_delete__account_preset_by_admin__permission_denied(
        self,
        api_client,
        mocker,
    ):
        # arrange
        account = create_test_account()
        user1 = create_test_admin(account=account)
        user2 = create_test_admin(account=account, email='user2@test.test')
        template = create_test_template(user1, is_active=True)
        preset = create_test_template_preset(
            template=template,
            author=user1,
            type=PresetType.ACCOUNT,
        )

        api_client.token_authenticate(user2)

        service_class_mock = mocker.patch(
            'src.processes.views.template_preset.TemplatePresetService',
        )

        # act
        response = api_client.delete(f'/templates/presets/{preset.id}')

        # assert
        assert response.status_code == 403
        service_class_mock.assert_not_called()
