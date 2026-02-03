import pytest
from unittest.mock import Mock

from src.processes.tests.fixtures import (
    create_test_admin,
    create_test_user,
)

pytestmark = pytest.mark.django_db


class TestFileSyncViewSet:

    def test_sync__superuser__ok(self, api_client, mocker):
        # arrange
        superuser = create_test_admin()
        superuser.is_superuser = True
        superuser.save()
        api_client.token_authenticate(superuser)

        mock_service = mocker.patch(
            'src.storage.views.FileSyncService',
        )
        mock_instance = Mock()
        mock_instance.sync_all_files.return_value = {
            'synced': 10,
            'errors': 0,
        }
        mock_instance.sync_all_attachments_to_storage.return_value = {
            'created': 5,
            'updated': 3,
        }
        mock_service.return_value = mock_instance

        # act
        response = api_client.post('/storage/file-sync')

        # assert
        assert response.status_code == 200
        assert response.data['file_service']['synced'] == 10
        assert response.data['storage']['created'] == 5
        mock_instance.sync_all_files.assert_called_once()
        mock_instance.sync_all_attachments_to_storage.assert_called_once()

    def test_sync__regular_user__forbidden(self, api_client):
        # arrange
        user = create_test_user()
        api_client.token_authenticate(user)

        # act
        response = api_client.post('/storage/file-sync')

        # assert
        assert response.status_code == 403

    def test_sync__admin_not_superuser__forbidden(self, api_client):
        # arrange
        admin = create_test_admin()
        admin.is_superuser = False
        admin.save()
        api_client.token_authenticate(admin)

        # act
        response = api_client.post('/storage/file-sync')

        # assert
        assert response.status_code == 403

    def test_sync__not_authenticated__unauthorized(self, api_client):
        # arrange
        # act
        response = api_client.post('/storage/file-sync')

        # assert
        assert response.status_code == 401
