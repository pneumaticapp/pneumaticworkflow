import pytest

from src.authentication.enums import AuthTokenType
from src.processes.enums import PresetType
from src.processes.services.exceptions import TemplatePresetServiceException
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_admin,
    create_test_owner,
    create_test_template,
    create_test_template_preset,
    create_test_user,
)
from src.utils.validation import ErrorCode

pytestmark = pytest.mark.django_db


class TestTemplatePresetsCreateView:

    def test_create__all_fields__ok(self, api_client, mocker):
        # arrange
        account = create_test_account()
        user = create_test_admin(account=account)
        template = create_test_template(user, is_active=True)

        api_client.token_authenticate(user)

        request_data = {
            'name': 'Test Preset',
            'is_default': False,
            'type': PresetType.PERSONAL,
            'fields': [
                {
                    'api_name': 'field_1',
                    'order': 1,
                    'width': 200,
                },
            ],
        }

        service_init_mock = mocker.patch(
            'src.processes.services.templates.preset.'
            'TemplatePresetService.__init__',
            return_value=None,
        )

        preset = create_test_template_preset(
            template=template,
            author=user,
            name=request_data['name'],
            is_default=request_data['is_default'],
            type=request_data['type'],
            fields=request_data['fields'],
        )

        service_create_mock = mocker.patch(
            'src.processes.services.templates.preset.'
            'TemplatePresetService.create',
            return_value=preset,
        )

        # act
        response = api_client.post(
            f'/templates/{template.id}/preset',
            data=request_data,
        )

        # assert
        service_init_mock.assert_called_once_with(
            user=user,
            is_superuser=False,
            auth_type=AuthTokenType.USER,
        )
        service_create_mock.assert_called_once_with(
            template=template,
            **request_data,
        )
        assert response.status_code == 200
        data = response.data
        assert data['name'] == request_data['name']
        assert data['is_default'] == request_data['is_default']
        assert data['type'] == request_data['type']
        assert data['author'] == user.id
        assert 'date_created_tsp' in data
        assert 'id' in data
        assert 'fields' in data

    def test_create__empty_fields__ok(self, api_client, mocker):
        # arrange
        account = create_test_account()
        user = create_test_admin(account=account)
        template = create_test_template(user, is_active=True)

        api_client.token_authenticate(user)

        request_data = {
            'name': 'Empty Preset',
            'is_default': False,
            'type': PresetType.PERSONAL,
            'fields': [],
        }

        service_init_mock = mocker.patch(
            'src.processes.services.templates.preset.'
            'TemplatePresetService.__init__',
            return_value=None,
        )

        preset = create_test_template_preset(
            template=template,
            author=user,
            name=request_data['name'],
            is_default=request_data['is_default'],
            type=request_data['type'],
            fields=request_data['fields'],
        )

        service_create_mock = mocker.patch(
            'src.processes.services.templates.preset.'
            'TemplatePresetService.create',
            return_value=preset,
        )

        # act
        response = api_client.post(
            f'/templates/{template.id}/preset',
            data=request_data,
        )

        # assert
        service_init_mock.assert_called_once_with(
            user=user,
            is_superuser=False,
            auth_type=AuthTokenType.USER,
        )
        service_create_mock.assert_called_once_with(
            template=template,
            **request_data,
        )
        assert response.status_code == 200
        data = response.data
        assert data['name'] == request_data['name']
        assert data['is_default'] == request_data['is_default']
        assert data['type'] == request_data['type']
        assert data['author'] == user.id
        assert 'date_created_tsp' in data
        assert 'id' in data
        assert data['fields'] == []

    def test_create__preset_type_account__ok(self, api_client, mocker):
        # arrange
        account = create_test_account()
        user = create_test_admin(account=account)
        template = create_test_template(user, is_active=True)

        api_client.token_authenticate(user)

        request_data = {
            'name': 'Empty Preset',
            'is_default': False,
            'type': PresetType.ACCOUNT,
            'fields': [],
        }

        service_init_mock = mocker.patch(
            'src.processes.services.templates.preset.'
            'TemplatePresetService.__init__',
            return_value=None,
        )

        preset = create_test_template_preset(
            template=template,
            author=user,
            name=request_data['name'],
            is_default=request_data['is_default'],
            type=request_data['type'],
            fields=request_data['fields'],
        )

        service_create_mock = mocker.patch(
            'src.processes.services.templates.preset.'
            'TemplatePresetService.create',
            return_value=preset,
        )

        # act
        response = api_client.post(
            f'/templates/{template.id}/preset',
            data=request_data,
        )

        # assert
        service_init_mock.assert_called_once_with(
            user=user,
            is_superuser=False,
            auth_type=AuthTokenType.USER,
        )
        service_create_mock.assert_called_once_with(
            template=template,
            **request_data,
        )
        assert response.status_code == 200
        data = response.data
        assert data['name'] == request_data['name']
        assert data['is_default'] == request_data['is_default']
        assert data['type'] == request_data['type']
        assert data['author'] == user.id
        assert 'date_created_tsp' in data
        assert 'id' in data
        assert data['fields'] == []

    def test_create__service_exception__validation_error(
        self,
        api_client,
        mocker,
    ):
        # arrange
        account = create_test_account()
        user = create_test_admin(account=account)
        template = create_test_template(user, is_active=True)

        api_client.token_authenticate(user)

        data = {
            'name': 'Test Preset',
            'is_default': False,
            'type': PresetType.PERSONAL,
            'fields': [],
        }

        service_init_mock = mocker.patch(
            'src.processes.services.templates.preset.'
            'TemplatePresetService.__init__',
            return_value=None,
        )

        error_message = 'Service error occurred'
        service_create_mock = mocker.patch(
            'src.processes.services.templates.preset.'
            'TemplatePresetService.create',
            side_effect=TemplatePresetServiceException(error_message),
        )

        # act
        response = api_client.post(
            f'/templates/{template.id}/preset',
            data=data,
        )

        # assert
        assert response.status_code == 400
        service_init_mock.assert_called_once_with(
            user=user,
            is_superuser=False,
            auth_type=AuthTokenType.USER,
        )
        service_create_mock.assert_called_once_with(
            template=template,
            **data,
        )

        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['message'] == error_message

    def test_create__invalid_data__validation_error(self, api_client, mocker):
        # arrange
        account = create_test_account()
        user = create_test_admin(account=account)
        template = create_test_template(user, is_active=True)

        api_client.token_authenticate(user)

        data = {
            'name': 'Test Preset',
            'is_default': False,
            'type': 'invalid_type',
            'fields': [],
        }

        service_init_mock = mocker.patch(
            'src.processes.services.templates.preset.'
            'TemplatePresetService.__init__',
            return_value=None,
        )

        service_create_mock = mocker.patch(
            'src.processes.services.templates.preset.'
            'TemplatePresetService.create',
        )

        # act
        response = api_client.post(
            f'/templates/{template.id}/preset',
            data=data,
        )

        # assert
        assert response.status_code == 400
        service_init_mock.assert_not_called()
        service_create_mock.assert_not_called()

        assert response.data['code'] == ErrorCode.VALIDATION_ERROR

    def test_create__template_not_found__permission_denied(
        self,
        api_client,
        mocker,
    ):
        # arrange
        account = create_test_account()
        user = create_test_admin(account=account)
        api_client.token_authenticate(user)

        fake_template_id = 99999
        data = {
            'name': 'Test Preset',
            'is_default': False,
            'type': PresetType.PERSONAL,
            'fields': [],
        }

        service_init_mock = mocker.patch(
            'src.processes.services.templates.preset.'
            'TemplatePresetService.__init__',
            return_value=None,
        )

        service_create_mock = mocker.patch(
            'src.processes.services.templates.preset.'
            'TemplatePresetService.create',
        )

        # act
        response = api_client.post(
            f'/templates/{fake_template_id}/preset',
            data=data,
        )

        # assert
        assert response.status_code == 403
        service_init_mock.assert_not_called()
        service_create_mock.assert_not_called()

    def test_create__not_authenticated__unauthorized(self, api_client, mocker):
        # arrange
        account = create_test_account()
        user = create_test_admin(account=account)
        template = create_test_template(user, is_active=True)
        data = {
            'name': 'Test Preset',
            'is_default': False,
            'type': PresetType.PERSONAL,
            'fields': [],
        }

        service_init_mock = mocker.patch(
            'src.processes.services.templates.preset.'
            'TemplatePresetService.__init__',
            return_value=None,
        )

        service_create_mock = mocker.patch(
            'src.processes.services.templates.preset.'
            'TemplatePresetService.create',
        )

        # act
        response = api_client.post(
            f'/templates/{template.id}/preset',
            data=data,
        )

        # assert
        assert response.status_code == 401
        service_init_mock.assert_not_called()
        service_create_mock.assert_not_called()

    def test_create__different_account__permission_denied(
        self,
        api_client,
        mocker,
    ):
        # arrange
        account1 = create_test_account()
        account2 = create_test_account()
        user1 = create_test_admin(account=account1)
        user2 = create_test_admin(account=account2, email='admin2@test.com')

        template = create_test_template(user1, is_active=True)
        api_client.token_authenticate(user2)

        data = {
            'name': 'Test Preset',
            'is_default': False,
            'type': PresetType.PERSONAL,
            'fields': [],
        }

        service_init_mock = mocker.patch(
            'src.processes.services.templates.preset.'
            'TemplatePresetService.__init__',
            return_value=None,
        )

        service_create_mock = mocker.patch(
            'src.processes.services.templates.preset.'
            'TemplatePresetService.create',
        )

        # act
        response = api_client.post(
            f'/templates/{template.id}/preset',
            data=data,
        )

        # assert
        assert response.status_code == 403
        service_init_mock.assert_not_called()
        service_create_mock.assert_not_called()

    def test_create__account_owner__ok(self, api_client, mocker):
        # arrange
        account = create_test_account()
        account_owner = create_test_owner(account=account)
        template = create_test_template(account_owner, is_active=True)

        api_client.token_authenticate(account_owner)

        request_data = {
            'name': 'Owner Preset',
            'is_default': False,
            'type': PresetType.ACCOUNT,
            'fields': [],
        }

        preset = create_test_template_preset(
            template=template,
            author=account_owner,
            name=request_data['name'],
            is_default=request_data['is_default'],
            type=request_data['type'],
            fields=request_data['fields'],
        )

        mock_service = mocker.MagicMock()
        mock_service.create.return_value = preset

        service_class_mock = mocker.patch(
            'src.processes.views.template.TemplatePresetService',
            return_value=mock_service,
        )

        # act
        response = api_client.post(
            f'/templates/{template.id}/preset',
            data=request_data,
        )

        # assert
        service_class_mock.assert_called_once_with(
            user=account_owner,
            is_superuser=False,
            auth_type=AuthTokenType.USER,
        )
        mock_service.create.assert_called_once_with(
            template=template,
            **request_data,
        )
        assert response.status_code == 200
        data = response.data
        assert data['name'] == request_data['name']
        assert data['is_default'] == request_data['is_default']
        assert data['type'] == request_data['type']
        assert data['author'] == account_owner.id
        assert 'date_created_tsp' in data
        assert 'id' in data
        assert data['fields'] == []

    def test_create__not_admin__permission_denied(self, api_client, mocker):
        # arrange
        account = create_test_account()
        admin_user = create_test_admin(account=account)
        not_admin = create_test_user(
            account=account,
            email='regular@test.com',
            is_admin=False,
            is_account_owner=False,
        )
        template = create_test_template(admin_user, is_active=True)

        api_client.token_authenticate(not_admin)

        request_data = {
            'name': 'Regular User Preset',
            'is_default': False,
            'type': PresetType.PERSONAL,
            'fields': [],
        }

        service_class_mock = mocker.patch(
            'src.processes.views.template.TemplatePresetService',
        )

        # act
        response = api_client.post(
            f'/templates/{template.id}/preset',
            data=request_data,
        )

        # assert
        assert response.status_code == 403
        service_class_mock.assert_not_called()

    def test_create__admin_not_template_owner__permission_denied(
        self,
        api_client,
        mocker,
    ):
        # arrange
        account = create_test_account()
        admin = create_test_admin(account=account)
        template_owner = create_test_admin(
            account=account,
            email='template_owner@test.com',
        )
        template = create_test_template(template_owner, is_active=True)

        api_client.token_authenticate(admin)

        request_data = {
            'name': 'Test Preset',
            'is_default': False,
            'type': PresetType.PERSONAL,
            'fields': [],
        }

        service_class_mock = mocker.patch(
            'src.processes.views.template.TemplatePresetService',
        )

        # act
        response = api_client.post(
            f'/templates/{template.id}/preset',
            data=request_data,
        )

        # assert
        assert response.status_code == 403
        service_class_mock.assert_not_called()

    def test_create__account_owner_and_template_owner__ok(
        self,
        api_client,
        mocker,
    ):
        # arrange
        account = create_test_account()
        account_owner = create_test_owner(account=account)
        template = create_test_template(account_owner, is_active=True)

        api_client.token_authenticate(account_owner)

        request_data = {
            'name': 'Test Preset',
            'is_default': False,
            'type': PresetType.PERSONAL,
            'fields': [],
        }

        preset = create_test_template_preset(
            template=template,
            author=account_owner,
            name=request_data['name'],
            is_default=request_data['is_default'],
            type=request_data['type'],
        )

        service_class_mock = mocker.patch(
            'src.processes.views.template.TemplatePresetService',
        )
        mock_service = mocker.MagicMock()
        mock_service.create.return_value = preset
        service_class_mock.return_value = mock_service

        # act
        response = api_client.post(
            f'/templates/{template.id}/preset',
            data=request_data,
        )

        # assert
        assert response.status_code == 200
        service_class_mock.assert_called_once_with(
            user=account_owner,
            is_superuser=False,
            auth_type=AuthTokenType.USER,
        )
        mock_service.create.assert_called_once_with(
            template=template,
            **request_data,
        )
