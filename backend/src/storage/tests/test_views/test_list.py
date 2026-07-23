import pytest
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

from src.permissions.models import UserObjectPermission
from src.permissions.enums import PermissionSource
from django.test import override_settings

from src.processes.tests.fixtures import (
    create_test_account,
    create_test_admin,
    create_test_attachment,
    create_test_workflow,
)
from src.storage.enums import AccessType, SourceType

pytestmark = pytest.mark.django_db


class TestListView:

    @override_settings(FILE_SERVICE_URL='https://example.com')
    def test_list__account_attachments__ok(self, api_client):
        # arrange
        user = create_test_admin()
        api_client.token_authenticate(user)
        attachment = create_test_attachment(
            user.account,
            file_id='file_123',
            access_type=AccessType.ACCOUNT,
            source_type=SourceType.ACCOUNT,
        )
        expected_url = f'https://example.com/{attachment.file_id}'

        # act
        response = api_client.get('/attachments')

        # assert
        assert response.status_code == 200
        assert response.data['count'] == 1
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['file_id'] == attachment.file_id
        assert response.data['results'][0]['access_type'] == AccessType.ACCOUNT
        assert response.data['results'][0]['source_type'] == SourceType.ACCOUNT
        assert response.data['results'][0]['url'] == expected_url

    def test_list__public_attachments__ok(self, api_client):
        # arrange
        user = create_test_admin()
        api_client.token_authenticate(user)

        attachment = create_test_attachment(
            user.account,
            file_id='file_public_123',
            access_type=AccessType.PUBLIC,
            source_type=SourceType.ACCOUNT,
        )

        # act
        response = api_client.get('/attachments')

        # assert
        assert response.status_code == 200
        assert response.data['count'] == 1
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['file_id'] == attachment.file_id
        assert response.data['results'][0]['access_type'] == AccessType.PUBLIC

    def test_list__restricted_with_permission__ok(self, api_client):
        # arrange
        user = create_test_admin()
        api_client.token_authenticate(user)
        workflow = create_test_workflow(user=user, tasks_count=1)
        task = workflow.tasks.first()

        attachment = create_test_attachment(
            user.account,
            file_id='file_restricted_123',
            access_type=AccessType.RESTRICTED,
            task=task,
        )
        att_ctype = ContentType.objects.get_for_model(attachment)
        att_perm = Permission.objects.get(
            content_type=att_ctype,
            codename='access_attachment',
        )
        UserObjectPermission.objects.create(
            user=user,
            permission=att_perm,
            content_type=att_ctype,
            object_pk=str(attachment.pk),
            source_type=PermissionSource.PERFORMER,
            source_id=0,
        )

        # act
        response = api_client.get('/attachments')

        # assert
        assert response.status_code == 200
        assert response.data['count'] >= 1
        assert len(response.data['results']) >= 1
        file_ids = [item['file_id'] for item in response.data['results']]
        assert attachment.file_id in file_ids

    def test_list__different_account__not_visible(self, api_client):
        # arrange
        account1 = create_test_account()
        user1 = create_test_admin(account=account1)

        account2 = create_test_account()
        create_test_admin(account=account2, email='admin2@pneumatic.app')

        attachment = create_test_attachment(
            account2,
            file_id='file_account2_123',
            access_type=AccessType.ACCOUNT,
            source_type=SourceType.ACCOUNT,
        )

        api_client.token_authenticate(user1)

        # act
        response = api_client.get('/attachments')

        # assert
        assert response.status_code == 200
        file_ids = [item['file_id'] for item in response.data['results']]
        assert attachment.file_id not in file_ids

    def test_list__not_authenticated__unauthorized(self, api_client):
        # arrange
        # act
        response = api_client.get('/attachments')

        # assert
        assert response.status_code == 401

    def test_list__multiple_attachments__ok(self, api_client):
        # arrange
        user = create_test_admin()
        api_client.token_authenticate(user)

        attachment1 = create_test_attachment(
            user.account,
            file_id='file_1',
            access_type=AccessType.ACCOUNT,
            source_type=SourceType.ACCOUNT,
        )
        attachment2 = create_test_attachment(
            user.account,
            file_id='file_2',
            access_type=AccessType.PUBLIC,
            source_type=SourceType.ACCOUNT,
        )

        # act
        response = api_client.get('/attachments')

        # assert
        assert response.status_code == 200
        assert response.data['count'] >= 2
        assert len(response.data['results']) >= 2
        file_ids = [item['file_id'] for item in response.data['results']]
        assert attachment1.file_id in file_ids
        assert attachment2.file_id in file_ids

    def test_list__soft_deleted__not_visible(self, api_client):
        # arrange
        user = create_test_admin()
        api_client.token_authenticate(user)

        attachment = create_test_attachment(
            user.account,
            file_id='file_deleted',
            access_type=AccessType.ACCOUNT,
            source_type=SourceType.ACCOUNT,
        )
        attachment.is_deleted = True
        attachment.save()

        # act
        response = api_client.get('/attachments')

        # assert
        assert response.status_code == 200
        file_ids = [item['file_id'] for item in response.data['results']]
        assert 'file_deleted' not in file_ids

    def test_list__pagination__ok(self, api_client):
        # arrange
        user = create_test_admin()
        api_client.token_authenticate(user)

        # Create 25 attachments
        attachments = []
        for i in range(25):
            attachment = create_test_attachment(
                user.account,
                file_id=f'file_{i}',
                access_type=AccessType.ACCOUNT,
                source_type=SourceType.ACCOUNT,
            )
            attachments.append(attachment)

        # act
        response = api_client.get('/attachments?limit=10&offset=0')

        # assert
        assert response.status_code == 200
        assert response.data['count'] == 25
        assert len(response.data['results']) == 10
        assert response.data['next'] is not None
        assert response.data['previous'] is None

    def test_list__pagination_second_page__ok(self, api_client):
        # arrange
        user = create_test_admin()
        api_client.token_authenticate(user)

        # Create 25 attachments
        for i in range(25):
            create_test_attachment(
                user.account,
                file_id=f'file_{i}',
                access_type=AccessType.ACCOUNT,
                source_type=SourceType.ACCOUNT,
            )

        # act
        response = api_client.get('/attachments?limit=10&offset=10')

        # assert
        assert response.status_code == 200
        assert response.data['count'] == 25
        assert len(response.data['results']) == 10
        assert response.data['next'] is not None
        assert response.data['previous'] is not None

    def test_list__pagination_last_page__ok(self, api_client):
        # arrange
        user = create_test_admin()
        api_client.token_authenticate(user)

        # Create 25 attachments
        for i in range(25):
            create_test_attachment(
                user.account,
                file_id=f'file_{i}',
                access_type=AccessType.ACCOUNT,
                source_type=SourceType.ACCOUNT,
            )

        # act
        response = api_client.get('/attachments?limit=10&offset=20')

        # assert
        assert response.status_code == 200
        assert response.data['count'] == 25
        assert len(response.data['results']) == 5
        assert response.data['next'] is None
        assert response.data['previous'] is not None
