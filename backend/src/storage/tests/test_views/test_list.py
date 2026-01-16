import pytest
from guardian.shortcuts import assign_perm

from src.processes.tests.fixtures import (
    create_test_account,
    create_test_admin,
    create_test_workflow,
)
from src.storage.enums import AccessType, SourceType
from src.storage.models import Attachment

pytestmark = pytest.mark.django_db


def test_list__empty__ok(api_client):
    # arrange
    user = create_test_admin()
    api_client.token_authenticate(user)

    # act
    response = api_client.get('/storage/attachments')

    # assert
    assert response.status_code == 200
    assert response.data == []


def test_list__account_attachments__ok(api_client):
    # arrange
    user = create_test_admin()
    api_client.token_authenticate(user)

    attachment = Attachment.objects.create(
        file_id='file_123',
        account=user.account,
        access_type=AccessType.ACCOUNT,
        source_type=SourceType.ACCOUNT,
    )

    # act
    response = api_client.get('/storage/attachments')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['file_id'] == attachment.file_id
    assert response.data[0]['access_type'] == AccessType.ACCOUNT
    assert response.data[0]['source_type'] == SourceType.ACCOUNT


def test_list__public_attachments__ok(api_client):
    # arrange
    user = create_test_admin()
    api_client.token_authenticate(user)

    attachment = Attachment.objects.create(
        file_id='file_public_123',
        account=user.account,
        access_type=AccessType.PUBLIC,
        source_type=SourceType.ACCOUNT,
    )

    # act
    response = api_client.get('/storage/attachments')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['file_id'] == attachment.file_id
    assert response.data[0]['access_type'] == AccessType.PUBLIC


def test_list__restricted_with_permission__ok(api_client):
    # arrange
    user = create_test_admin()
    api_client.token_authenticate(user)
    workflow = create_test_workflow(user=user, tasks_count=1)
    task = workflow.tasks.first()

    attachment = Attachment.objects.create(
        file_id='file_restricted_123',
        account=user.account,
        access_type=AccessType.RESTRICTED,
        source_type=SourceType.TASK,
        task=task,
    )
    assign_perm('view_attachment', user, attachment)

    # act
    response = api_client.get('/storage/attachments')

    # assert
    assert response.status_code == 200
    assert len(response.data) >= 1
    file_ids = [item['file_id'] for item in response.data]
    assert attachment.file_id in file_ids


def test_list__different_account__not_visible(api_client):
    # arrange
    account1 = create_test_account()
    user1 = create_test_admin(account=account1)

    account2 = create_test_account()
    create_test_admin(account=account2, email='admin2@pneumatic.app')

    Attachment.objects.create(
        file_id='file_account2_123',
        account=account2,
        access_type=AccessType.ACCOUNT,
        source_type=SourceType.ACCOUNT,
    )

    api_client.token_authenticate(user1)

    # act
    response = api_client.get('/storage/attachments')

    # assert
    assert response.status_code == 200
    file_ids = [item['file_id'] for item in response.data]
    assert 'file_account2_123' not in file_ids


def test_list__not_authenticated__unauthorized(api_client):
    # act
    response = api_client.get('/storage/attachments')

    # assert
    assert response.status_code == 401


def test_list__multiple_attachments__ok(api_client):
    # arrange
    user = create_test_admin()
    api_client.token_authenticate(user)

    attachment1 = Attachment.objects.create(
        file_id='file_1',
        account=user.account,
        access_type=AccessType.ACCOUNT,
        source_type=SourceType.ACCOUNT,
    )
    attachment2 = Attachment.objects.create(
        file_id='file_2',
        account=user.account,
        access_type=AccessType.PUBLIC,
        source_type=SourceType.ACCOUNT,
    )

    # act
    response = api_client.get('/storage/attachments')

    # assert
    assert response.status_code == 200
    assert len(response.data) >= 2
    file_ids = [item['file_id'] for item in response.data]
    assert attachment1.file_id in file_ids
    assert attachment2.file_id in file_ids


def test_list__soft_deleted__not_visible(api_client):
    # arrange
    user = create_test_admin()
    api_client.token_authenticate(user)

    attachment = Attachment.objects.create(
        file_id='file_deleted',
        account=user.account,
        access_type=AccessType.ACCOUNT,
        source_type=SourceType.ACCOUNT,
    )
    attachment.is_deleted = True
    attachment.save()

    # act
    response = api_client.get('/storage/attachments')

    # assert
    assert response.status_code == 200
    file_ids = [item['file_id'] for item in response.data]
    assert 'file_deleted' not in file_ids
