import pytest
from django.contrib.auth import get_user_model

from pneumatic_backend.processes.enums import FileAttachmentAccessType
from pneumatic_backend.processes.models import (
    FileAttachment,
    FileAttachmentPermission
)
from pneumatic_backend.processes.tests.fixtures import (
    create_test_admin,
    create_test_account
)


UserModel = get_user_model()
pytestmark = pytest.mark.django_db


class TestCheckPermission:

    def test_check_permission__account_access_same_account__ok(
        self, 
        api_client,
    ):
        # arrange
        user = create_test_admin()
        FileAttachment.objects.create(
            name='test.pdf',
            url='https://storage.com/files/test123.pdf',
            size=1024,
            account=user.account,
            access_type=FileAttachmentAccessType.ACCOUNT
        )
        
        api_client.token_authenticate(user)
        
        # act
        response = api_client.post(
            '/attachments/check-permission',
            data={
                'file_id': 'test123.pdf'
            }
        )
        
        # assert
        assert response.status_code == 204
        assert response.data is None

    def test_check_permission__account_access_different_account__forbidden(
        self,
        api_client
    ):
        # arrange
        user1 = create_test_admin()
        account2 = create_test_account()
        user2 = create_test_admin(account=account2, email='gfew2bb@vgm.re')
        
        FileAttachment.objects.create(
            name='test.pdf',
            url='https://storage.com/files/test123.pdf',
            size=1024,
            account=user2.account,
            access_type=FileAttachmentAccessType.ACCOUNT
        )
        
        api_client.token_authenticate(user1)
        
        # act
        response = api_client.post(
            '/attachments/check-permission',
            data={
                'file_id': 'test123.pdf'
            }
        )
        
        # assert
        assert response.status_code == 403

    def test_check_permission__restricted_access_has_permission__ok(
        self,
        api_client
    ):
        # arrange
        user = create_test_admin()
        attachment = FileAttachment.objects.create(
            name='test.pdf',
            url='https://storage.com/files/test123.pdf',
            size=1024,
            account=user.account,
            access_type=FileAttachmentAccessType.RESTRICTED
        )
        
        FileAttachmentPermission.objects.create(
            user=user,
            attachment=attachment,
            account=user.account
        )
        
        api_client.token_authenticate(user)
        
        # act
        response = api_client.post(
            '/attachments/check-permission',
            data={
                'file_id': 'test123.pdf'
            }
        )
        
        # assert
        assert response.status_code == 204

    def test_check_permission__restricted_access_no_permission__forbidden(
        self,
        api_client
    ):
        # arrange
        user = create_test_admin()
        FileAttachment.objects.create(
            name='test.pdf',
            url='https://storage.com/files/test123.pdf',
            size=1024,
            account=user.account,
            access_type=FileAttachmentAccessType.RESTRICTED
        )
        
        api_client.token_authenticate(user)
        
        # act
        response = api_client.post(
            '/attachments/check-permission',
            data={
                'file_id': 'test123.pdf'
            }
        )
        
        # assert
        assert response.status_code == 403

    def test_check_permission__file_not_found__forbidden(
        self,
        api_client
    ):
        # arrange
        user = create_test_admin()
        api_client.token_authenticate(user)
        
        # act
        response = api_client.post(
            '/attachments/check-permission',
            data={
                'file_id': 'nonexistent.pdf'
            }
        )
        
        # assert
        assert response.status_code == 403

    def test_check_permission__invalid_data__bad_request(
        self,
        api_client
    ):
        # arrange
        user = create_test_admin()
        api_client.token_authenticate(user)
        
        # act
        response = api_client.post(
            '/attachments/check-permission',
            data={
                'file_id': ''
            }
        )
        
        # assert
        assert response.status_code == 400

    def test_check_permission__not_authenticated__unauthorized(
        self,
        api_client
    ):
        # act
        response = api_client.post(
            '/attachments/check-permission',
            data={
                'file_id': 'test.pdf'
            }
        )
        
        # assert
        assert response.status_code == 401
