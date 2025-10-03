import pytest
from src.processes.tests.fixtures import (
    create_test_admin,
    create_test_account,
    create_test_template,
    create_test_template_preset,
    create_test_owner,
    create_test_not_admin
)
from src.processes.enums import PresetType


pytestmark = pytest.mark.django_db


class TestTemplatePresetsListView:

    def test_presets__admin_template_owner__ok(self, api_client, mocker):
        # arrange
        account = create_test_account()
        user = create_test_admin(account=account)
        template = create_test_template(user, is_active=True)

        preset = create_test_template_preset(
            template=template,
            author=user,
            name='Test Preset',
            is_default=True,
            preset_type=PresetType.PERSONAL,
            fields=[
                {
                    'api_name': 'field_1',
                    'order': 1,
                    'width': 200
                }
            ]
        )

        api_client.token_authenticate(user)

        mock_queryset = mocker.MagicMock()
        mock_queryset.select_related.return_value = mock_queryset
        mock_queryset.prefetch_related.return_value = [preset]
        by_presets_mock = mocker.patch(
            'src.processes.models.templates.preset.'
            'TemplatePreset.objects.by_user',
            return_value=mock_queryset
        )

        # act
        response = api_client.get(f'/templates/{template.id}/presets')

        # assert
        by_presets_mock.assert_called_once_with(
            user, template.id
        )
        assert response.status_code == 200
        data = response.data
        assert len(data) == 1
        preset_data = data[0]
        assert preset_data['name'] == 'Test Preset'
        assert preset_data['is_default'] is True
        assert preset_data['type'] == PresetType.PERSONAL
        assert preset_data['author'] == user.id
        assert 'date_created_tsp' in preset_data
        assert 'id' in preset_data
        assert 'fields' in preset_data
        assert len(preset_data['fields']) == 1
        assert preset_data['fields'][0]['api_name'] == 'field_1'
        assert preset_data['fields'][0]['order'] == 1
        assert preset_data['fields'][0]['width'] == 200

    def test_presets__account_owner_template_owner__ok(
        self,
        api_client,
        mocker
    ):
        # arrange
        account = create_test_account()
        account_owner = create_test_owner(account=account)
        template = create_test_template(account_owner, is_active=True)

        preset = create_test_template_preset(
            template=template,
            author=account_owner,
            name='Owner Preset',
            is_default=True,
            preset_type=PresetType.ACCOUNT
        )

        api_client.token_authenticate(account_owner)

        mock_queryset = mocker.MagicMock()
        mock_queryset.select_related.return_value = mock_queryset
        mock_queryset.prefetch_related.return_value = [preset]
        by_presets_mock = mocker.patch(
            'src.processes.models.templates.preset.'
            'TemplatePreset.objects.by_user',
            return_value=mock_queryset
        )

        # act
        response = api_client.get(f'/templates/{template.id}/presets')

        # assert
        assert response.status_code == 200
        by_presets_mock.assert_called_once_with(
            account_owner, template.id
        )

    def test_presets__admin_not_template_owner__permission_denied(
        self,
        api_client,
        mocker
    ):
        # arrange
        account = create_test_account()
        admin = create_test_admin(account=account)
        template_owner = create_test_admin(
            account=account,
            email='template_owner@test.com'
        )
        template = create_test_template(template_owner, is_active=True)

        api_client.token_authenticate(admin)

        by_presets_mock = mocker.patch(
            'src.processes.models.templates.preset.'
            'TemplatePreset.objects.by_user'
        )

        # act
        response = api_client.get(f'/templates/{template.id}/presets')

        # assert
        assert response.status_code == 403
        by_presets_mock.assert_not_called()

    def test_presets__not_admin_not_template_owner__permission_denied(
        self,
        api_client,
        mocker
    ):
        # arrange
        account = create_test_account()
        admin = create_test_admin(account=account)
        not_admin = create_test_not_admin(
            account=account,
            email='regular@test.com',
        )
        template = create_test_template(admin, is_active=True)

        api_client.token_authenticate(not_admin)

        by_presets_mock = mocker.patch(
            'src.processes.models.templates.preset.'
            'TemplatePreset.objects.by_user'
        )

        # act
        response = api_client.get(f'/templates/{template.id}/presets')

        # assert
        assert response.status_code == 403
        by_presets_mock.assert_not_called()

    def test_presets__template_not_found__permission_denied(
        self,
        api_client,
        mocker
    ):
        # arrange
        account = create_test_account()
        user = create_test_admin(account=account)
        api_client.token_authenticate(user)

        fake_template_id = 99999

        by_presets_mock = mocker.patch(
            'src.processes.models.templates.preset.'
            'TemplatePreset.objects.by_user'
        )

        # act
        response = api_client.get(f'/templates/{fake_template_id}/presets')

        # assert
        assert response.status_code == 403
        by_presets_mock.assert_not_called()

    def test_presets__not_authenticated__unauthorized(
        self,
        api_client,
        mocker
    ):
        # arrange
        fake_template_id = 1

        by_presets_mock = mocker.patch(
            'src.processes.models.templates.preset.'
            'TemplatePreset.objects.by_user'
        )

        # act
        response = api_client.get(f'/templates/{fake_template_id}/presets')

        # assert
        assert response.status_code == 401
        by_presets_mock.assert_not_called()

    def test_presets__different_account__permission_denied(
        self,
        api_client,
        mocker
    ):
        # arrange
        account1 = create_test_account()
        account2 = create_test_account()
        user1 = create_test_admin(account=account1)
        user2 = create_test_admin(account=account2, email='user2@test.com')
        template = create_test_template(user1, is_active=True)

        api_client.token_authenticate(user2)

        by_presets_mock = mocker.patch(
            'src.processes.models.templates.preset.'
            'TemplatePreset.objects.by_user'
        )

        # act
        response = api_client.get(f'/templates/{template.id}/presets')

        # assert
        assert response.status_code == 403
        by_presets_mock.assert_not_called()

    def test_presets__empty_list__ok(self, api_client, mocker):
        # arrange
        account = create_test_account()
        user = create_test_admin(account=account)
        template = create_test_template(user, is_active=True)

        api_client.token_authenticate(user)

        mock_queryset = mocker.MagicMock()
        mock_queryset.select_related.return_value = mock_queryset
        mock_queryset.prefetch_related.return_value = []
        by_presets_mock = mocker.patch(
            'src.processes.models.templates.preset.'
            'TemplatePreset.objects.by_user',
            return_value=mock_queryset
        )

        # act
        response = api_client.get(f'/templates/{template.id}/presets')

        # assert
        assert response.status_code == 200
        data = response.data
        assert len(data) == 0
        by_presets_mock.assert_called_once_with(user, template.id)
