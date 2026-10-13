import pytest
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

from src.permissions.enums import PermissionSource
from src.permissions.models import GroupObjectPermission, UserObjectPermission
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_admin,
    create_test_group,
    create_test_workflow,
)
from src.storage.enums import AccessType, SourceType
from src.storage.models import Attachment
from src.storage.services.attachments import AttachmentService

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize('grant_type', ['user', 'group'])
def test_batch__restricted_grants__any_live_attachment(grant_type):
    # arrange
    user = create_test_admin()
    group = create_test_group(account=user.account, users=[user])
    attachments = [
        Attachment.objects.create(
            account=user.account,
            file_id=file_id,
            access_type=AccessType.RESTRICTED,
            source_type=SourceType.ACCOUNT,
        )
        for file_id in ('batch_restricted_a', 'batch_restricted_b')
    ]
    ctype = ContentType.objects.get_for_model(Attachment)
    permission = Permission.objects.get(
        content_type=ctype,
        codename='access_attachment',
    )
    for attachment in attachments:
        data = {
            'content_type': ctype,
            'permission': permission,
            'object_pk': str(attachment.pk),
        }
        if grant_type == 'user':
            UserObjectPermission.objects.create(
                user=user,
                source_type=PermissionSource.PERFORMER,
                source_id=0,
                **data,
            )
        else:
            GroupObjectPermission.objects.create(group=group, **data)
    service = AttachmentService(user=user)

    # act
    allowed = service.check_account_files_permission(
        file_ids=[attachment.file_id for attachment in attachments],
    )
    attachments[0].delete()
    denied = service.check_account_files_permission(
        file_ids=[attachment.file_id for attachment in attachments],
    )

    # assert
    assert allowed is True
    assert denied is False


@pytest.mark.parametrize(
    'other_access,expected',
    [
        (AccessType.PUBLIC, True),
        (AccessType.ACCOUNT, False),
        (AccessType.RESTRICTED, False),
    ],
)
def test_batch__cross_account_attachment__preserves_public_access(
    other_access,
    expected,
):
    # arrange
    user = create_test_admin()
    other = create_test_account()
    other_user = create_test_admin(
        account=other, email='other-batch@test.test',
    )
    other_workflow = create_test_workflow(user=other_user)
    file_id = 'batch_shared_file'
    Attachment.objects.create(
        account=user.account,
        file_id=file_id,
        access_type=AccessType.RESTRICTED,
        source_type=SourceType.ACCOUNT,
    )
    Attachment.objects.create(
        account=other,
        file_id=file_id,
        access_type=other_access,
        source_type=SourceType.ACCOUNT,
        workflow=other_workflow,
    )

    # act
    result = AttachmentService(user=user).check_account_files_permission(
        file_ids=[file_id],
    )

    # assert
    assert result is expected


def test_batch__foreign_public_without_local_reference__denied():
    # arrange
    user = create_test_admin()
    attachment = Attachment.objects.create(
        account=create_test_account(),
        file_id='batch_foreign_public',
        access_type=AccessType.PUBLIC,
        source_type=SourceType.ACCOUNT,
    )

    # act
    result = AttachmentService(user=user).check_account_files_permission(
        file_ids=[attachment.file_id],
    )

    # assert
    assert result is False


def test_batch__many_files__constant_query_budget(django_assert_num_queries):
    # arrange
    user = create_test_admin()
    file_ids = [f'batch_account_{index}' for index in range(50)]
    Attachment.objects.bulk_create(
        [
            Attachment(
                account=user.account,
                file_id=file_id,
                access_type=AccessType.ACCOUNT,
                source_type=SourceType.ACCOUNT,
            )
            for file_id in file_ids
        ],
    )
    ContentType.objects.get_for_model(Attachment)
    service = AttachmentService(user=user)

    # act
    with django_assert_num_queries(2):
        result = service.check_account_files_permission(
            file_ids=[*file_ids, file_ids[0]],
        )

    # assert
    assert result is True
