import pytest
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

from src.permissions.enums import PermissionSource
from src.permissions.models import UserObjectPermission
from src.processes.enums import (
    DirectlyStatus,
    OwnerType,
    PerformerType,
)
from src.processes.models.templates.owner import TemplateOwner
from src.processes.models.workflows.task import TaskPerformer
from src.processes.services.workflow_permissions import (
    WorkflowPermissionService,
)
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_attachment,
    create_test_group,
    create_test_not_admin,
    create_test_owner,
    create_test_template,
    create_test_workflow,
)
from src.storage.enums import AccessType, SourceType
from src.storage.models import Attachment
from src.storage.services.attachments import AttachmentService
from src.storage.tasks import sync_workflow_attachment_permissions
from src.storage.utils import reassign_restricted_permissions_for_task

pytestmark = pytest.mark.django_db


def _has_attachment_access(user, file_id: str) -> bool:
    return AttachmentService(user=user).check_user_permission(
        user_id=user.id,
        account_id=user.account_id,
        file_id=file_id,
    )


def test_rebuild_template_att__owner__has_access():

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    template = create_test_template(
        user=owner, is_active=True, tasks_count=1,
    )
    attachment = create_test_attachment(
        account=account,
        file_id='tpl_owner.pdf',
        template=template,
        source_type=SourceType.TEMPLATE,
    )

    # act
    AttachmentService().rebuild_template_attachment_permissions(
        template_id=template.id,
    )

    # assert
    assert _has_attachment_access(owner, attachment.file_id)


def test_rebuild_template_att__workflow_viewer__has_access():

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    viewer = create_test_not_admin(
        account=account, email='viewer@test.test',
    )
    template = create_test_template(
        user=owner, is_active=True, tasks_count=1,
    )
    workflow = create_test_workflow(user=owner, template=template)
    WorkflowPermissionService(workflow).grant_view(
        user=viewer,
        source_type=PermissionSource.WORKFLOW_VIEWER,
        source_id=workflow.pk,
    )
    attachment = create_test_attachment(
        account=account,
        file_id='tpl_viewer.pdf',
        template=template,
        source_type=SourceType.TEMPLATE,
    )

    # act
    AttachmentService().rebuild_template_attachment_permissions(
        template_id=template.id,
    )

    # assert
    assert _has_attachment_access(viewer, attachment.file_id)


def test_rebuild_template_att__outsider__no_access():

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    outsider = create_test_not_admin(
        account=account, email='out@test.test',
    )
    template = create_test_template(
        user=owner, is_active=True, tasks_count=1,
    )
    create_test_workflow(user=owner, template=template)
    attachment = create_test_attachment(
        account=account,
        file_id='tpl_out.pdf',
        template=template,
        source_type=SourceType.TEMPLATE,
    )

    # act
    AttachmentService().rebuild_template_attachment_permissions(
        template_id=template.id,
    )

    # assert
    assert not _has_attachment_access(outsider, attachment.file_id)


def test_rebuild_template_att__removed_viewer__loses_access():

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    viewer = create_test_not_admin(
        account=account, email='viewer@test.test',
    )
    template = create_test_template(
        user=owner, is_active=True, tasks_count=1,
    )
    workflow = create_test_workflow(user=owner, template=template)
    WorkflowPermissionService(workflow).grant_view(
        user=viewer,
        source_type=PermissionSource.WORKFLOW_VIEWER,
        source_id=workflow.pk,
    )
    attachment = create_test_attachment(
        account=account,
        file_id='tpl_removed.pdf',
        template=template,
        source_type=SourceType.TEMPLATE,
    )
    AttachmentService().rebuild_template_attachment_permissions(
        template_id=template.id,
    )
    assert _has_attachment_access(viewer, attachment.file_id)

    WorkflowPermissionService(workflow).revoke_view(
        source_type=PermissionSource.WORKFLOW_VIEWER,
        source_id=workflow.pk,
    )

    # act
    AttachmentService().rebuild_template_attachment_permissions(
        template_id=template.id,
    )

    # assert
    assert not _has_attachment_access(viewer, attachment.file_id)
    assert _has_attachment_access(owner, attachment.file_id)


def test_rebuild_template_att__keeps_access_via_other_workflow():

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    viewer = create_test_not_admin(
        account=account, email='viewer@test.test',
    )
    template = create_test_template(
        user=owner, is_active=True, tasks_count=1,
    )
    workflow_1 = create_test_workflow(user=owner, template=template)
    workflow_2 = create_test_workflow(user=owner, template=template)
    for workflow in (workflow_1, workflow_2):
        WorkflowPermissionService(workflow).grant_view(
            user=viewer,
            source_type=PermissionSource.WORKFLOW_VIEWER,
            source_id=workflow.pk,
        )
    attachment = create_test_attachment(
        account=account,
        file_id='tpl_keep.pdf',
        template=template,
        source_type=SourceType.TEMPLATE,
    )
    AttachmentService().rebuild_template_attachment_permissions(
        template_id=template.id,
    )
    assert _has_attachment_access(viewer, attachment.file_id)

    WorkflowPermissionService(workflow_1).revoke_view(
        source_type=PermissionSource.WORKFLOW_VIEWER,
        source_id=workflow_1.pk,
    )

    # act
    AttachmentService().rebuild_template_attachment_permissions(
        template_id=template.id,
    )

    # assert
    assert _has_attachment_access(viewer, attachment.file_id)


def test_rebuild_template_att__group_performer__member_has_access():

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    member = create_test_not_admin(
        account=account, email='member@test.test',
    )
    group = create_test_group(account, users=[member])
    template = create_test_template(
        user=owner, is_active=True, tasks_count=1,
    )
    workflow = create_test_workflow(user=owner, template=template)
    task = workflow.tasks.get(number=1)
    TaskPerformer.objects.create(
        task=task,
        type=PerformerType.GROUP,
        group=group,
    )
    attachment = create_test_attachment(
        account=account,
        file_id='tpl_group.pdf',
        template=template,
        source_type=SourceType.TEMPLATE,
    )

    # act
    AttachmentService().rebuild_template_attachment_permissions(
        template_id=template.id,
    )

    # assert
    assert _has_attachment_access(member, attachment.file_id)


def test_rebuild_template_att__deleted_group_performer__no_access():

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    member = create_test_not_admin(
        account=account, email='member@test.test',
    )
    group = create_test_group(account, users=[member])
    template = create_test_template(
        user=owner, is_active=True, tasks_count=1,
    )
    workflow = create_test_workflow(user=owner, template=template)
    task = workflow.tasks.get(number=1)
    TaskPerformer.objects.create(
        task=task,
        type=PerformerType.GROUP,
        group=group,
        directly_status=DirectlyStatus.DELETED,
    )
    attachment = create_test_attachment(
        account=account,
        file_id='tpl_del_group.pdf',
        template=template,
        source_type=SourceType.TEMPLATE,
    )

    # act
    AttachmentService().rebuild_template_attachment_permissions(
        template_id=template.id,
    )

    # assert
    assert not _has_attachment_access(member, attachment.file_id)


def test_rebuild_template_att__template_owner_group__ok():

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    member = create_test_not_admin(
        account=account, email='owner_grp@test.test',
    )
    group = create_test_group(account, users=[member])
    template = create_test_template(
        user=owner, is_active=True, tasks_count=1,
    )
    TemplateOwner.objects.create(
        template=template,
        account=account,
        type=OwnerType.GROUP,
        group=group,
    )
    attachment = create_test_attachment(
        account=account,
        file_id='tpl_own_grp.pdf',
        template=template,
        source_type=SourceType.TEMPLATE,
    )

    # act
    AttachmentService().rebuild_template_attachment_permissions(
        template_id=template.id,
    )

    # assert
    assert _has_attachment_access(member, attachment.file_id)


def test_rebuild_template_att__no_attachments__noop():

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    template = create_test_template(
        user=owner, is_active=True, tasks_count=1,
    )

    # act / assert — must not raise
    AttachmentService().rebuild_template_attachment_permissions(
        template_id=template.id,
    )


def test_rebuild_template_att__multiple_files__all_synced():

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    viewer = create_test_not_admin(
        account=account, email='viewer@test.test',
    )
    template = create_test_template(
        user=owner, is_active=True, tasks_count=1,
    )
    workflow = create_test_workflow(user=owner, template=template)
    WorkflowPermissionService(workflow).grant_view(
        user=viewer,
        source_type=PermissionSource.MENTION,
        source_id=1,
    )
    att_1 = create_test_attachment(
        account=account,
        file_id='tpl_a.pdf',
        template=template,
        source_type=SourceType.TEMPLATE,
    )
    att_2 = create_test_attachment(
        account=account,
        file_id='tpl_b.pdf',
        template=template,
        source_type=SourceType.TEMPLATE,
    )

    # act
    AttachmentService().rebuild_template_attachment_permissions(
        template_id=template.id,
    )

    # assert
    assert _has_attachment_access(viewer, att_1.file_id)
    assert _has_attachment_access(viewer, att_2.file_id)


def test_rebuild_template_att__clears_stale_uop():

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    stale = create_test_not_admin(
        account=account, email='stale@test.test',
    )
    template = create_test_template(
        user=owner, is_active=True, tasks_count=1,
    )
    attachment = create_test_attachment(
        account=account,
        file_id='tpl_stale.pdf',
        template=template,
        source_type=SourceType.TEMPLATE,
    )
    ctype = ContentType.objects.get_for_model(Attachment)
    perm = Permission.objects.get(
        content_type=ctype,
        codename='access_attachment',
    )
    UserObjectPermission.objects.create(
        user=stale,
        permission=perm,
        content_type=ctype,
        object_pk=str(attachment.pk),
        source_type=PermissionSource.WORKFLOW_VIEWER,
        source_id=template.id,
    )
    assert _has_attachment_access(stale, attachment.file_id)

    # act
    AttachmentService().rebuild_template_attachment_permissions(
        template_id=template.id,
    )

    # assert
    assert not _has_attachment_access(stale, attachment.file_id)


def test_rebuild_template_att__owner_not_duplicated_as_viewer():

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    template = create_test_template(
        user=owner, is_active=True, tasks_count=1,
    )
    workflow = create_test_workflow(user=owner, template=template)
    # owner already has view via TEMPLATE_OWNER from fixture
    assert WorkflowPermissionService(workflow).has_view(user=owner)
    attachment = create_test_attachment(
        account=account,
        file_id='tpl_dedupe.pdf',
        template=template,
        source_type=SourceType.TEMPLATE,
    )

    # act
    AttachmentService().rebuild_template_attachment_permissions(
        template_id=template.id,
    )

    # assert
    ctype = ContentType.objects.get_for_model(Attachment)
    rows = UserObjectPermission.objects.filter(
        user=owner,
        content_type=ctype,
        object_pk=str(attachment.pk),
    )
    assert rows.filter(
        source_type=PermissionSource.TEMPLATE_OWNER,
    ).exists()
    assert not rows.filter(
        source_type=PermissionSource.WORKFLOW_VIEWER,
    ).exists()


def test_sync_workflow_attachment_permissions__also_rebuilds_template():

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    viewer = create_test_not_admin(
        account=account, email='viewer@test.test',
    )
    template = create_test_template(
        user=owner, is_active=True, tasks_count=1,
    )
    workflow = create_test_workflow(user=owner, template=template)
    WorkflowPermissionService(workflow).grant_view(
        user=viewer,
        source_type=PermissionSource.WORKFLOW_VIEWER,
        source_id=workflow.pk,
    )
    task_att = create_test_attachment(
        account=account,
        file_id='task_file.pdf',
        task=workflow.tasks.get(number=1),
        workflow=workflow,
        source_type=SourceType.TASK,
    )
    tpl_att = create_test_attachment(
        account=account,
        file_id='tpl_via_wf.pdf',
        template=template,
        source_type=SourceType.TEMPLATE,
    )

    # act
    sync_workflow_attachment_permissions(workflow.id)

    # assert
    assert _has_attachment_access(owner, task_att.file_id)
    assert _has_attachment_access(viewer, tpl_att.file_id)


def test_reassign_for_task__rebuilds_template_acl(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    template = create_test_template(
        user=owner, is_active=True, tasks_count=1,
    )
    workflow = create_test_workflow(user=owner, template=template)
    task = workflow.tasks.get(number=1)
    rebuild_mock = mocker.patch.object(
        AttachmentService,
        'rebuild_template_attachment_permissions',
    )

    # act
    reassign_restricted_permissions_for_task(task=task, user=owner)

    # assert
    rebuild_mock.assert_called_once_with(template_id=template.id)


def test_reassign_for_task__grants_template_access():

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    viewer = create_test_not_admin(
        account=account, email='viewer@test.test',
    )
    template = create_test_template(
        user=owner, is_active=True, tasks_count=1,
    )
    workflow = create_test_workflow(user=owner, template=template)
    task = workflow.tasks.get(number=1)
    WorkflowPermissionService(workflow).grant_view(
        user=viewer,
        source_type=PermissionSource.WORKFLOW_VIEWER,
        source_id=workflow.pk,
    )
    attachment = create_test_attachment(
        account=account,
        file_id='tpl_eager.pdf',
        template=template,
        source_type=SourceType.TEMPLATE,
    )

    # act
    reassign_restricted_permissions_for_task(task=task, user=owner)

    # assert
    assert _has_attachment_access(viewer, attachment.file_id)


def test_reassign_for_task__removed_viewer_loses_template_access():

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    viewer = create_test_not_admin(
        account=account, email='viewer@test.test',
    )
    template = create_test_template(
        user=owner, is_active=True, tasks_count=1,
    )
    workflow = create_test_workflow(user=owner, template=template)
    task = workflow.tasks.get(number=1)
    WorkflowPermissionService(workflow).grant_view(
        user=viewer,
        source_type=PermissionSource.WORKFLOW_VIEWER,
        source_id=workflow.pk,
    )
    attachment = create_test_attachment(
        account=account,
        file_id='tpl_reassign_rm.pdf',
        template=template,
        source_type=SourceType.TEMPLATE,
    )
    reassign_restricted_permissions_for_task(task=task, user=owner)
    assert _has_attachment_access(viewer, attachment.file_id)

    WorkflowPermissionService(workflow).revoke_view(
        source_type=PermissionSource.WORKFLOW_VIEWER,
        source_id=workflow.pk,
    )

    # act
    reassign_restricted_permissions_for_task(task=task, user=owner)

    # assert
    assert not _has_attachment_access(viewer, attachment.file_id)


def test_rebuild_template_att__ignores_public_and_task_files():

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    outsider = create_test_not_admin(
        account=account, email='out@test.test',
    )
    template = create_test_template(
        user=owner, is_active=True, tasks_count=1,
    )
    workflow = create_test_workflow(user=owner, template=template)
    public_att = create_test_attachment(
        account=account,
        file_id='public.pdf',
        template=template,
        source_type=SourceType.TEMPLATE,
        access_type=AccessType.PUBLIC,
    )
    task_att = create_test_attachment(
        account=account,
        file_id='task_only.pdf',
        task=workflow.tasks.get(number=1),
        workflow=workflow,
        source_type=SourceType.TASK,
    )

    # act
    AttachmentService().rebuild_template_attachment_permissions(
        template_id=template.id,
    )

    # assert — rebuild must not create UOP for public/task files
    ctype = ContentType.objects.get_for_model(Attachment)
    assert not UserObjectPermission.objects.filter(
        content_type=ctype,
        object_pk=str(public_att.pk),
    ).exists()
    assert not UserObjectPermission.objects.filter(
        content_type=ctype,
        object_pk=str(task_att.pk),
    ).exists()
    # outsider still has no restricted template access path
    assert not Attachment.objects.filter(
        template_id=template.id,
        source_type=SourceType.TEMPLATE,
        access_type=AccessType.RESTRICTED,
    ).exists()
    assert outsider.id is not None


def test_rebuild_template_att__deleted_workflow_viewers_excluded():

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    viewer = create_test_not_admin(
        account=account, email='viewer@test.test',
    )
    template = create_test_template(
        user=owner, is_active=True, tasks_count=1,
    )
    workflow = create_test_workflow(user=owner, template=template)
    WorkflowPermissionService(workflow).grant_view(
        user=viewer,
        source_type=PermissionSource.WORKFLOW_VIEWER,
        source_id=workflow.pk,
    )
    attachment = create_test_attachment(
        account=account,
        file_id='tpl_del_wf.pdf',
        template=template,
        source_type=SourceType.TEMPLATE,
    )
    workflow.delete()

    # act
    AttachmentService().rebuild_template_attachment_permissions(
        template_id=template.id,
    )

    # assert
    assert not _has_attachment_access(viewer, attachment.file_id)
    assert _has_attachment_access(owner, attachment.file_id)
