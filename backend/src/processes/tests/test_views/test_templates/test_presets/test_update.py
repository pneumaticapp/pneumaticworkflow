import pytest

from src.authentication.enums import AuthTokenType
from src.processes.enums import PresetType
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_admin,
    create_test_template,
    create_test_template_preset,
)
from src.utils.validation import ErrorCode

pytestmark = pytest.mark.django_db


class TestTemplatePresetUpdateView:

    def test_update__ok(self, api_client, mocker):
        # arrange
        account = create_test_account()
        user = create_test_admin(account=account)
        template = create_test_template(user, is_active=True)
        preset = create_test_template_preset(
            template=template,
            author=user,
            name='Old Name',
            type=PresetType.PERSONAL,
        )

        api_client.token_authenticate(user)

        data = {
            'name': 'New Name',
            'is_default': True,
            'type': PresetType.ACCOUNT,
            'fields': [
                {
                    'api_name': 'new_field',
                    'order': 1,
                    'width': 300,
                },
            ],
        }

        updated_preset = create_test_template_preset(
            template=template,
            author=user,
            name=data['name'],
            is_default=data['is_default'],
            type=data['type'],
        )

        mock_service = mocker.MagicMock()
        mock_service.partial_update.return_value = updated_preset

        service_class_mock = mocker.patch(
            'src.processes.views.template_preset.TemplatePresetService',
            return_value=mock_service,
        )

        # act
        response = api_client.put(
            f'/templates/presets/{preset.id}',
            data=data,
        )

        # assert
        service_class_mock.assert_called_once_with(
            user=user,
            instance=preset,
            is_superuser=False,
            auth_type=AuthTokenType.USER,
        )
        mock_service.partial_update.assert_called_once_with(
            force_save=True,
            **data,
        )
        assert response.status_code == 200
        response_data = response.data
        assert response_data['name'] == data['name']
        assert response_data['is_default'] == data['is_default']
        assert response_data['type'] == data['type']
        assert response_data['author'] == user.id
        assert 'date_created_tsp' in response_data
        assert 'id' in response_data
        assert 'fields' in response_data

    def test_update__invalid_data__validation_error(self, api_client, mocker):
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

        data = {
            'name': 'New Name',
            'is_default': False,
            'type': 'invalid_type',
            'fields': [],
        }

        service_class_mock = mocker.patch(
            'src.processes.views.template_preset.TemplatePresetService',
        )

        # act
        response = api_client.put(
            f'/templates/presets/{preset.id}',
            data=data,
        )

        # assert
        assert response.status_code == 400
        service_class_mock.assert_not_called()

        assert response.data['code'] == ErrorCode.VALIDATION_ERROR

    def test_update__preset_not_found__not_found(self, api_client, mocker):
        # arrange
        account = create_test_account()
        user = create_test_admin(account=account)
        api_client.token_authenticate(user)

        fake_preset_id = 99999
        data = {
            'name': 'New Name',
            'is_default': False,
            'type': PresetType.PERSONAL,
            'fields': [],
        }

        service_class_mock = mocker.patch(
            'src.processes.views.template_preset.TemplatePresetService',
        )

        # act
        response = api_client.put(
            f'/templates/presets/{fake_preset_id}',
            data=data,
        )

        # assert
        assert response.status_code == 403
        service_class_mock.assert_not_called()

    def test_update__not_authenticated__unauthorized(self, api_client, mocker):
        # arrange
        fake_preset_id = 1
        data = {
            'name': 'New Name',
            'is_default': False,
            'type': PresetType.PERSONAL,
            'fields': [],
        }

        service_class_mock = mocker.patch(
            'src.processes.views.template_preset.TemplatePresetService',
        )

        # act
        response = api_client.put(
            f'/templates/presets/{fake_preset_id}',
            data=data,
        )

        # assert
        assert response.status_code == 401
        service_class_mock.assert_not_called()

    def test_update__not_author__permission_denied(self, api_client, mocker):
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

        data = {
            'name': 'New Name',
            'is_default': False,
            'type': PresetType.PERSONAL,
            'fields': [],
        }

        service_class_mock = mocker.patch(
            'src.processes.views.template_preset.TemplatePresetService',
        )

        # act
        response = api_client.put(
            f'/templates/presets/{preset.id}',
            data=data,
        )

        # assert
        assert response.status_code == 403
        service_class_mock.assert_not_called()

    def test_update__different_account____permission_denied(
        self,
        api_client,
        mocker,
    ):
        # arrange
        account1 = create_test_account()
        account2 = create_test_account()
        user1 = create_test_admin(account=account1)
        user2 = create_test_admin(account=account2, email='test@test.com')

        template = create_test_template(user1, is_active=True)
        preset = create_test_template_preset(
            template=template,
            author=user1,
            type=PresetType.PERSONAL,
        )

        api_client.token_authenticate(user2)

        data = {
            'name': 'New Name',
            'is_default': False,
            'type': PresetType.PERSONAL,
            'fields': [],
        }

        service_class_mock = mocker.patch(
            'src.processes.views.template_preset.TemplatePresetService',
        )

        # act
        response = api_client.put(
            f'/templates/presets/{preset.id}',
            data=data,
        )

        # assert
        assert response.status_code == 403
        service_class_mock.assert_not_called()
