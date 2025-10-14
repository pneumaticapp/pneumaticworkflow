import pytest
from src.processes.tests.fixtures import (
    create_test_admin,
    create_test_account,
    create_test_template,
    create_test_template_preset,
)
from src.processes.services.templates.preset import TemplatePresetService
from src.processes.enums import PresetType
from src.authentication.enums import AuthTokenType


pytestmark = pytest.mark.django_db


class TestTemplatePresetService:

    def test_init_service__ok(self):
        # arrange
        account = create_test_account()
        request_user = create_test_admin(account=account)
        is_superuser = False

        # act
        service = TemplatePresetService(
            user=request_user,
            is_superuser=is_superuser,
            auth_type=AuthTokenType.USER,
        )

        # assert
        assert service.account is account
        assert service.user == request_user
        assert service.is_superuser == is_superuser
        assert service.auth_type == AuthTokenType.USER

    def test_create_instance__only_required_fields__ok(self):
        # arrange
        account = create_test_account()
        request_user = create_test_admin(account=account)
        template = create_test_template(request_user, is_active=True)
        is_superuser = False
        name = 'new_preset'
        service = TemplatePresetService(
            user=request_user,
            is_superuser=is_superuser,
            auth_type=AuthTokenType.USER,
        )

        # act
        instance = service._create_instance(
            template=template,
            name=name,
            type=PresetType.PERSONAL
        )

        # assert
        assert instance.template == template
        assert instance.author == request_user
        assert instance.account == account
        assert instance.type == PresetType.PERSONAL
        assert instance.is_default is False
        assert instance.name == name

    def test_create_instance__all_fields__ok(self):
        # arrange
        account = create_test_account()
        request_user = create_test_admin(account=account)
        template = create_test_template(request_user, is_active=True)
        is_superuser = False
        service = TemplatePresetService(
            user=request_user,
            is_superuser=is_superuser,
            auth_type=AuthTokenType.USER,
        )
        name = "Test Preset"
        is_default = True

        # act
        instance = service._create_instance(
            template=template,
            name=name,
            is_default=is_default,
            type=PresetType.ACCOUNT
        )

        # assert
        assert instance.template == template
        assert instance.author == request_user
        assert instance.account == account
        assert instance.name == name
        assert instance.is_default == is_default
        assert instance.type == PresetType.ACCOUNT

    def test_create_related__with_fields__ok(self, mocker):
        # arrange
        account = create_test_account()
        user = create_test_admin(account=account)
        template = create_test_template(user, is_active=True)
        preset = create_test_template_preset(
            template=template,
            author=user,
            type=PresetType.PERSONAL
        )
        is_superuser = False
        service = TemplatePresetService(
            user=user,
            is_superuser=is_superuser,
            instance=preset,
            auth_type=AuthTokenType.USER,
        )
        fields_data = [
            {
                'api_name': 'field1',
                'order': 1,
                'width': 200
            },
            {
                'api_name': 'field2',
                'order': 2,
                'width': 150
            }
        ]

        bulk_create_mock = mocker.patch(
            'src.processes.models.templates.preset.'
            'TemplatePresetField.objects.bulk_create'
        )

        # act
        service._create_related(fields=fields_data)

        # assert
        bulk_create_mock.assert_called_once()
        created_fields = bulk_create_mock.call_args[0][0]
        assert len(created_fields) == 2
        assert created_fields[0].api_name == 'field1'
        assert created_fields[1].api_name == 'field2'

    def test_create_related__without_fields__ok(self, mocker):
        # arrange
        account = create_test_account()
        user = create_test_admin(account=account)
        template = create_test_template(user, is_active=True)
        preset = create_test_template_preset(
            template=template,
            author=user,
            type=PresetType.PERSONAL
        )
        is_superuser = False
        service = TemplatePresetService(
            user=user,
            is_superuser=is_superuser,
            instance=preset,
            auth_type=AuthTokenType.USER,
        )

        create_preset_fields_mock = mocker.patch.object(
            service,
            '_create_or_update_preset_fields'
        )

        # act
        service._create_related()

        # assert
        create_preset_fields_mock.assert_not_called()

    def test_partial_update__with_fields__ok(self, mocker):
        # arrange
        account = create_test_account()
        user = create_test_admin(account=account)
        template = create_test_template(user, is_active=True)
        preset = create_test_template_preset(
            template=template,
            author=user,
            type=PresetType.PERSONAL,
            fields=[
                {'api_name': 'old_field', 'order': 1, 'width': 100}
            ]
        )
        is_superuser = False
        service = TemplatePresetService(
            user=user,
            is_superuser=is_superuser,
            instance=preset,
            auth_type=AuthTokenType.USER,
        )

        new_fields = [
            {
                'api_name': 'new_field1',
                'order': 1,
                'width': 200
            },
            {
                'api_name': 'new_field2',
                'order': 2,
                'width': 150
            }
        ]

        create_preset_fields_mock = mocker.patch.object(
            service,
            '_create_or_update_preset_fields'
        )
        reset_default_mock = mocker.patch.object(
            service,
            '_reset_default_presets'
        )

        # act
        service.partial_update(
            name="Updated Preset",
            is_default=True,
            type=PresetType.ACCOUNT,
            fields=new_fields,
            force_save=True
        )

        # assert
        create_preset_fields_mock.assert_called_once_with(
            fields_data=new_fields
        )
        reset_default_mock.assert_called_once_with()

        preset.refresh_from_db()
        assert preset.name == "Updated Preset"
        assert preset.is_default is True
        assert preset.type == PresetType.ACCOUNT

    def test_partial_update__without_fields__ok(self, mocker):
        # arrange
        account = create_test_account()
        user = create_test_admin(account=account)
        template = create_test_template(user, is_active=True)
        preset = create_test_template_preset(
            template=template,
            author=user,
            type=PresetType.PERSONAL,
            fields=[
                {'api_name': 'existing_field', 'order': 1, 'width': 100}
            ]
        )
        is_superuser = False
        service = TemplatePresetService(
            user=user,
            is_superuser=is_superuser,
            instance=preset,
            auth_type=AuthTokenType.USER,
        )

        create_preset_fields_mock = mocker.patch.object(
            service,
            '_create_or_update_preset_fields'
        )
        reset_default_mock = mocker.patch.object(
            service,
            '_reset_default_presets'
        )

        # act
        service.partial_update(
            name="Updated Preset",
            force_save=True
        )

        # assert
        create_preset_fields_mock.assert_not_called()
        reset_default_mock.assert_not_called()

    def test_set_default__ok(self, mocker):
        # arrange
        account = create_test_account()
        user = create_test_admin(account=account)
        template = create_test_template(user, is_active=True)
        preset = create_test_template_preset(
            template=template,
            author=user,
            type=PresetType.PERSONAL
        )
        is_superuser = False
        service = TemplatePresetService(
            user=user,
            is_superuser=is_superuser,
            instance=preset,
            auth_type=AuthTokenType.USER,
        )

        # act
        result = service.set_default()

        # assert
        preset.refresh_from_db()
        assert preset.is_default is True
        assert result == preset

    def test_delete__ok(self, mocker):
        # arrange
        account = create_test_account()
        user = create_test_admin(account=account)
        template = create_test_template(user, is_active=True)
        preset = create_test_template_preset(
            template=template,
            author=user,
            type=PresetType.PERSONAL
        )
        is_superuser = False
        service = TemplatePresetService(
            user=user,
            is_superuser=is_superuser,
            instance=preset,
            auth_type=AuthTokenType.USER,
        )

        delete_mock = mocker.patch.object(preset, 'delete')

        # act
        service.delete()

        # assert
        delete_mock.assert_called_once()

    def test_reset_default_presets__personal__ok(self):
        # arrange
        account = create_test_account()
        user1 = create_test_admin(account=account)
        user2 = create_test_admin(account=account, email='user2@test.com')
        template = create_test_template(user1, is_active=True)

        preset1_user1 = create_test_template_preset(
            template=template,
            author=user1,
            type=PresetType.PERSONAL,
            is_default=True
        )
        preset2_user1 = create_test_template_preset(
            template=template,
            author=user1,
            type=PresetType.PERSONAL,
            is_default=True
        )
        preset_user2 = create_test_template_preset(
            template=template,
            author=user2,
            type=PresetType.PERSONAL,
            is_default=True
        )

        service = TemplatePresetService(
            user=user1,
            is_superuser=False,
            auth_type=AuthTokenType.USER,
            instance=preset2_user1,
        )

        # act
        service._reset_default_presets()

        # assert
        preset1_user1.refresh_from_db()
        preset2_user1.refresh_from_db()
        preset_user2.refresh_from_db()

        assert preset1_user1.is_default is False
        assert preset2_user1.is_default is True
        assert preset_user2.is_default is True

    def test_reset_default_presets__account__ok(self):
        # arrange
        account = create_test_account()
        user1 = create_test_admin(account=account)
        user2 = create_test_admin(account=account, email='user2@test.com')
        template = create_test_template(user1, is_active=True)

        preset1_user1 = create_test_template_preset(
            template=template,
            author=user1,
            type=PresetType.ACCOUNT,
            is_default=True
        )
        preset2_user2 = create_test_template_preset(
            template=template,
            author=user2,
            type=PresetType.ACCOUNT,
            is_default=True
        )

        service = TemplatePresetService(
            user=user1,
            is_superuser=False,
            auth_type=AuthTokenType.USER,
            instance=preset2_user2,
        )

        # act
        service._reset_default_presets()

        # assert
        preset1_user1.refresh_from_db()
        preset2_user2.refresh_from_db()

        assert preset1_user1.is_default is False
        assert preset2_user2.is_default is True

    def test_create__with_fields__ok(self, mocker):
        # arrange
        account = create_test_account()
        user = create_test_admin(account=account)
        template = create_test_template(user, is_active=True)
        service = TemplatePresetService(
            user=user,
            is_superuser=False,
            auth_type=AuthTokenType.USER,
        )

        fields_data = [
            {'api_name': 'field_1', 'order': 1, 'width': 200},
            {'api_name': 'field_2', 'order': 2, 'width': 150}
        ]

        create_preset_fields_mock = mocker.patch(
            'src.processes.services.templates.preset.'
            'TemplatePresetService._create_or_update_preset_fields'
        )

        # act
        preset = service.create(
            template=template,
            name='Test Preset',
            is_default=False,
            type=PresetType.PERSONAL,
            fields=fields_data
        )

        # assert
        assert preset.template == template
        assert preset.author == user
        assert preset.name == 'Test Preset'
        assert preset.is_default is False
        assert preset.type == PresetType.PERSONAL
        create_preset_fields_mock.assert_called_once_with(
            fields_data=fields_data
        )

    def test_create__with_default__resets_other_defaults(self, mocker):
        # arrange
        account = create_test_account()
        user = create_test_admin(account=account)
        template = create_test_template(user, is_active=True)
        service = TemplatePresetService(
            user=user,
            is_superuser=False,
            auth_type=AuthTokenType.USER,
        )

        reset_default_mock = mocker.patch(
            'src.processes.services.templates.preset.'
            'TemplatePresetService._reset_default_presets'
        )

        # act
        preset = service.create(
            template=template,
            name='Default Preset',
            is_default=True,
            type=PresetType.PERSONAL
        )

        # assert
        assert preset.is_default is True
        reset_default_mock.assert_called_once_with()
