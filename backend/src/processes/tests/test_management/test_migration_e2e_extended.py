"""
E2E integration tests — categories H through O.

Covers: soft delete, priority logic, group/member permissions,
URL formats, error recovery, AttachmentListQuery SQL, workflow
lifecycle, full model URL replacement, consistency edge cases.
"""
import pytest

from django.contrib.contenttypes.models import ContentType
from django.db import connection
from guardian.models import UserObjectPermission

from src.accounts.models import Contact
from src.permissions.models import GroupObjectPermission
from src.processes.enums import OwnerType, WorkflowStatus
from src.processes.models.workflows.attachment import (
    FileAttachment,
)
from src.processes.models.templates.owner import (
    TemplateOwner,
)
from src.processes.models.workflows.task import TaskPerformer
from src.processes.models.templates.template import (
    TemplateDraft,
)
from src.processes.tests.fixtures import (
    create_invited_user,
    create_test_account,
    create_test_admin,
    create_test_event,
    create_test_group,
    create_test_guest,
    create_test_not_admin,
    create_test_owner,
    create_test_workflow,
)
from src.storage.enums import AccessType, SourceType
from src.storage.models import Attachment
from src.storage.queries import AttachmentListQuery
from src.storage.services.attachments import AttachmentService
from .conftest import GCS_API, GCS_CLOUD, FS_DOMAIN, gcs_url

pytestmark = pytest.mark.django_db


# ═══════════════════════════════════════════════════════════
# H. Soft delete and priority logic
# ═══════════════════════════════════════════════════════════


def test_e2e__soft_deleted_fa__not_migrated(
    create_fa,
    run_pipeline,
):
    # arrange
    user = create_test_admin()
    fa = create_fa(
        account=user.account,
        file_key='deleted_file.pdf',
    )
    fa.is_deleted = True
    fa.save(update_fields=['is_deleted'])

    # act
    run_pipeline(account_id=user.account.id)

    # assert
    fa.refresh_from_db()
    assert fa.file_id is None
    assert not Attachment.objects.filter(
        file_id='deleted_file.pdf',
    ).exists()


def test_e2e__wf_and_event__wf_takes_priority(
    create_fa,
    run_pipeline,
):
    # arrange
    user = create_test_admin()
    workflow = create_test_workflow(
        user=user, tasks_count=1,
    )
    task = workflow.tasks.first()
    event = create_test_event(
        workflow=workflow, user=user, task=task,
    )
    create_fa(
        account=user.account,
        file_key='priority_file.pdf',
        workflow=workflow,
        event=event,
    )

    # act
    run_pipeline(account_id=user.account.id)

    # assert
    att = Attachment.objects.get(
        file_id='priority_file.pdf',
    )
    assert att.source_type == SourceType.WORKFLOW
    assert att.workflow_id == workflow.id


def test_e2e__non_gcs_url__skipped_no_error(
    run_fill,
    run_migrate,
):
    # arrange
    user = create_test_admin()
    FileAttachment.objects.create(
        name='external.pdf',
        url='https://cdn.example.com/external.pdf',
        account=user.account,
        size=100,
    )

    # act
    run_fill(account_id=user.account.id)
    run_migrate(account_id=user.account.id)

    # assert
    fa = FileAttachment.objects.get(name='external.pdf')
    assert fa.file_id is None
    assert not Attachment.objects.exists()


# ═══════════════════════════════════════════════════════════
# I. Permissions for groups and multiple participants
# ═══════════════════════════════════════════════════════════


def test_e2e__multi_performers__all_get_perms(
    create_fa,
    run_pipeline,
):
    # arrange
    user = create_test_admin()
    user2 = create_test_not_admin(
        account=user.account,
        email='performer2@test.com',
    )
    workflow = create_test_workflow(
        user=user, tasks_count=1,
    )
    task = workflow.tasks.first()
    TaskPerformer.objects.create(
        task=task, user=user2,
    )
    event = create_test_event(
        workflow=workflow, user=user, task=task,
    )
    create_fa(
        account=user.account,
        file_key='multi_perf.pdf',
        event=event,
    )

    # act
    run_pipeline(account_id=user.account.id)

    # assert
    svc = AttachmentService(user=user)
    assert svc.check_user_permission(
        user_id=user.id,
        account_id=user.account_id,
        file_id='multi_perf.pdf',
    )
    svc2 = AttachmentService(user=user2)
    assert svc2.check_user_permission(
        user_id=user2.id,
        account_id=user2.account_id,
        file_id='multi_perf.pdf',
    )


def test_e2e__wf_member_not_owner__gets_perm(
    create_fa,
    run_pipeline,
):
    # arrange
    user = create_test_admin()
    member = create_test_not_admin(
        account=user.account,
        email='member@test.com',
    )
    workflow = create_test_workflow(
        user=user, tasks_count=1,
    )
    workflow.members.add(member)
    create_fa(
        account=user.account,
        file_key='member_file.pdf',
        workflow=workflow,
    )

    # act
    run_pipeline(account_id=user.account.id)

    # assert
    svc = AttachmentService(user=member)
    assert svc.check_user_permission(
        user_id=member.id,
        account_id=member.account_id,
        file_id='member_file.pdf',
    )


def test_e2e__group_performer__group_perm_created(
    create_fa,
    run_pipeline,
):
    # arrange
    user = create_test_admin()
    member = create_test_not_admin(
        account=user.account,
        email='group_member@test.com',
    )
    group = create_test_group(
        account=user.account, users=[member],
    )
    workflow = create_test_workflow(
        user=user, tasks_count=1,
    )
    task = workflow.tasks.first()
    TaskPerformer.objects.create(
        task=task, group=group,
    )
    event = create_test_event(
        workflow=workflow, user=user, task=task,
    )
    create_fa(
        account=user.account,
        file_key='group_file.pdf',
        event=event,
    )

    # act
    run_pipeline(account_id=user.account.id)

    # assert
    att = Attachment.objects.get(
        file_id='group_file.pdf',
    )
    ctype = ContentType.objects.get_for_model(Attachment)
    assert GroupObjectPermission.objects.filter(
        group=group,
        object_pk=str(att.pk),
        content_type=ctype,
    ).exists()


def test_e2e__template_owner__gets_permission(
    create_fa,
    run_pipeline,
):
    # arrange
    user = create_test_admin()
    tmpl_owner = create_test_not_admin(
        account=user.account,
        email='tmpl_owner@test.com',
    )
    workflow = create_test_workflow(
        user=user, tasks_count=1,
    )

    TemplateOwner.objects.create(
        template=workflow.template,
        user=tmpl_owner,
        type=OwnerType.USER,
        account=user.account,
    )
    task = workflow.tasks.first()
    event = create_test_event(
        workflow=workflow, user=user, task=task,
    )
    create_fa(
        account=user.account,
        file_key='tmpl_owner_file.pdf',
        event=event,
    )

    # act
    run_pipeline(account_id=user.account.id)

    # assert
    att = Attachment.objects.get(
        file_id='tmpl_owner_file.pdf',
    )
    ctype = ContentType.objects.get_for_model(Attachment)
    assert UserObjectPermission.objects.filter(
        user=tmpl_owner,
        object_pk=str(att.pk),
        permission__content_type=ctype,
    ).exists()


# ═══════════════════════════════════════════════════════════
# J. Different URL formats
# ═══════════════════════════════════════════════════════════


def test_e2e__cloud_google_url__full_pipeline(
    create_fa,
    run_pipeline,
):
    # arrange
    user = create_test_admin()
    workflow = create_test_workflow(
        user=user, tasks_count=1,
    )
    cloud_url = gcs_url(
        'cloud_file.pdf', base=GCS_CLOUD,
    )
    create_fa(
        account=user.account,
        file_key='cloud_file.pdf',
        workflow=workflow,
        url=cloud_url,
    )

    # act
    run_pipeline(account_id=user.account.id)

    # assert
    fa = FileAttachment.objects.get(
        file_id='cloud_file.pdf',
    )
    assert fa.file_id is not None
    assert Attachment.objects.filter(
        file_id=fa.file_id,
    ).exists()


def test_e2e__multi_urls_in_field__all_replaced(
    create_fa,
    run_pipeline,
):
    # arrange
    user = create_test_admin()
    workflow = create_test_workflow(
        user=user, tasks_count=1,
    )
    task = workflow.tasks.first()
    url1 = gcs_url('file_a.pdf')
    url2 = gcs_url('file_b.pdf')
    create_fa(
        account=user.account,
        file_key='file_a.pdf',
        workflow=workflow,
    )
    create_fa(
        account=user.account,
        file_key='file_b.pdf',
        workflow=workflow,
    )
    task.description = f'See {url1} and also {url2}'
    task.save(update_fields=['description'])

    # act
    run_pipeline(account_id=user.account.id)

    # assert
    task.refresh_from_db()
    assert GCS_API not in task.description
    assert task.description.count(FS_DOMAIN) == 2


def test_e2e__url_in_markdown__replaced(
    create_fa,
    run_pipeline,
):
    # arrange
    user = create_test_admin()
    workflow = create_test_workflow(
        user=user, tasks_count=1,
    )
    task = workflow.tasks.first()
    url = gcs_url('md_file.pdf')
    create_fa(
        account=user.account,
        file_key='md_file.pdf',
        workflow=workflow,
    )
    task.description = f'[report.pdf]({url})'
    task.save(update_fields=['description'])

    # act
    run_pipeline(account_id=user.account.id)

    # assert
    task.refresh_from_db()
    assert '[report.pdf](' in task.description
    assert GCS_API not in task.description
    assert FS_DOMAIN in task.description


# ═══════════════════════════════════════════════════════════
# K. Error recovery and counter accuracy
# ═══════════════════════════════════════════════════════════


def test_e2e__partial_fail__ok_files_accessible(
    create_fa,
    run_pipeline,
):
    # arrange
    user = create_test_admin()
    workflow = create_test_workflow(
        user=user, tasks_count=1,
    )
    create_fa(
        account=user.account,
        file_key='ok_file_1.pdf',
        workflow=workflow,
    )
    create_fa(
        account=user.account,
        file_key='ok_file_2.pdf',
        workflow=workflow,
    )
    create_fa(
        account=user.account,
        file_key='dup_file.pdf',
        workflow=workflow,
    )
    Attachment.objects.create(
        file_id='dup_file.pdf',
        access_type=AccessType.ACCOUNT,
        source_type=SourceType.ACCOUNT,
        account=user.account,
    )

    # act
    run_pipeline(account_id=user.account.id)

    # assert
    assert Attachment.objects.filter(
        file_id='ok_file_1.pdf',
    ).exists()
    assert Attachment.objects.filter(
        file_id='ok_file_2.pdf',
    ).exists()


def test_e2e__counters__created_skipped(
    create_fa,
    run_fill,
    run_migrate,
):
    # arrange
    user = create_test_admin()
    create_fa(
        account=user.account,
        file_key='count_new.pdf',
    )
    create_fa(
        account=user.account,
        file_key='count_dup.pdf',
    )
    Attachment.objects.create(
        file_id='count_dup.pdf',
        access_type=AccessType.ACCOUNT,
        source_type=SourceType.ACCOUNT,
        account=user.account,
    )

    # act
    run_fill(account_id=user.account.id)
    output = run_migrate(account_id=user.account.id)

    # assert
    assert 'Created: 1' in output
    assert 'Skipped: 1' in output


def test_e2e__incremental__new_files_only(
    create_fa,
    run_pipeline,
    run_fill,
    run_migrate,
):
    # arrange
    user = create_test_admin()
    for i in range(3):
        create_fa(
            account=user.account,
            file_key=f'batch1_{i}.pdf',
        )
    run_pipeline(account_id=user.account.id)
    assert Attachment.objects.count() == 3
    for i in range(2):
        create_fa(
            account=user.account,
            file_key=f'batch2_{i}.pdf',
        )

    # act
    run_fill(account_id=user.account.id)
    output = run_migrate(account_id=user.account.id)

    # assert
    assert Attachment.objects.count() == 5
    assert 'Created: 2' in output
    assert 'Skipped: 3' in output


def test_e2e__large_batch__100_files__all_correct(
    create_fa,
    run_pipeline,
):
    # arrange
    user = create_test_admin()
    workflow = create_test_workflow(
        user=user, tasks_count=1,
    )
    for i in range(100):
        create_fa(
            account=user.account,
            file_key=f'batch_{i:03d}.pdf',
            workflow=workflow,
        )

    # act
    run_pipeline(account_id=user.account.id)

    # assert
    assert Attachment.objects.filter(
        account=user.account,
    ).count() == 100
    assert Attachment.objects.filter(
        access_type=AccessType.RESTRICTED,
    ).count() == 100


# ═══════════════════════════════════════════════════════════
# L. AttachmentListQuery SQL visibility
# ═══════════════════════════════════════════════════════════


def _execute_list_query(user, limit=100):
    query = AttachmentListQuery(
        user=user, limit=limit,
    )
    sql, params = query.get_sql()
    with connection.cursor() as cursor:
        cursor.execute(sql, params)
        columns = [
            col[0] for col in cursor.description
        ]
        return [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]


def test_e2e__list_query__restricted_with_perm(
    create_fa,
    run_pipeline,
):
    # arrange
    user = create_test_admin()
    workflow = create_test_workflow(
        user=user, tasks_count=1,
    )
    create_fa(
        account=user.account,
        file_key='lq_visible.pdf',
        workflow=workflow,
    )
    run_pipeline(account_id=user.account.id)

    # act
    rows = _execute_list_query(user=user)

    # assert
    file_ids = [r['file_id'] for r in rows]
    assert 'lq_visible.pdf' in file_ids


def test_e2e__list_query__restricted_no_perm(
    create_fa,
    run_pipeline,
):
    # arrange
    user = create_test_admin()
    workflow = create_test_workflow(
        user=user, tasks_count=1,
    )
    create_fa(
        account=user.account,
        file_key='lq_hidden.pdf',
        workflow=workflow,
    )
    run_pipeline(account_id=user.account.id)
    outsider_acc = create_test_account(name='Outsider')
    outsider = create_test_admin(
        account=outsider_acc,
        email='lq_outsider@test.com',
    )

    # act
    rows = _execute_list_query(user=outsider)

    # assert
    file_ids = [r['file_id'] for r in rows]
    assert 'lq_hidden.pdf' not in file_ids


def test_e2e__list_query__account_same_account(
    create_fa,
    run_pipeline,
):
    # arrange
    user = create_test_admin()
    colleague = create_test_not_admin(
        account=user.account,
        email='colleague@test.com',
    )
    create_fa(
        account=user.account,
        file_key='lq_account.pdf',
    )
    run_pipeline(account_id=user.account.id)

    # act
    rows = _execute_list_query(user=colleague)

    # assert
    file_ids = [r['file_id'] for r in rows]
    assert 'lq_account.pdf' in file_ids


def test_e2e__list_query__group_perm_visible(
    create_fa,
    run_pipeline,
):
    # arrange
    user = create_test_admin()
    member = create_test_not_admin(
        account=user.account,
        email='grp_member@test.com',
    )
    group = create_test_group(
        account=user.account, users=[member],
    )
    workflow = create_test_workflow(
        user=user, tasks_count=1,
    )
    task = workflow.tasks.first()
    TaskPerformer.objects.create(
        task=task, group=group,
    )
    event = create_test_event(
        workflow=workflow, user=user, task=task,
    )
    create_fa(
        account=user.account,
        file_key='lq_group.pdf',
        event=event,
    )
    run_pipeline(account_id=user.account.id)

    # act
    rows = _execute_list_query(user=member)

    # assert
    file_ids = [r['file_id'] for r in rows]
    assert 'lq_group.pdf' in file_ids


# ═══════════════════════════════════════════════════════════
# M. Workflow lifecycle and user statuses
# ═══════════════════════════════════════════════════════════


def test_e2e__completed_wf__files_still_migrate(
    create_fa,
    run_pipeline,
):
    # arrange
    user = create_test_admin()
    workflow = create_test_workflow(
        user=user, tasks_count=1,
    )
    workflow.status = WorkflowStatus.DONE
    workflow.save(update_fields=['status'])
    create_fa(
        account=user.account,
        file_key='done_wf.pdf',
        workflow=workflow,
    )

    # act
    run_pipeline(account_id=user.account.id)

    # assert
    att = Attachment.objects.get(file_id='done_wf.pdf')
    assert att.access_type == AccessType.RESTRICTED


def test_e2e__guest__no_perm_after_migrate(
    create_fa,
    run_pipeline,
):
    # arrange
    user = create_test_owner()
    guest = create_test_guest(
        account=user.account,
        email='guest_no_perm@test.com',
    )
    workflow = create_test_workflow(
        user=user, tasks_count=1,
    )
    create_fa(
        account=user.account,
        file_key='guest_file.pdf',
        workflow=workflow,
    )

    # act
    run_pipeline(account_id=user.account.id)

    # assert
    svc = AttachmentService(user=guest)
    assert not svc.check_user_permission(
        user_id=guest.id,
        account_id=guest.account_id,
        file_id='guest_file.pdf',
    )


def test_e2e__invited_performer__gets_perm(
    create_fa,
    run_pipeline,
):
    # arrange
    user = create_test_admin()
    invited = create_invited_user(
        user=user,
        email='invited_perf@test.com',
    )
    workflow = create_test_workflow(
        user=user, tasks_count=1,
    )
    task = workflow.tasks.first()
    TaskPerformer.objects.create(
        task=task, user=invited,
    )
    event = create_test_event(
        workflow=workflow, user=user, task=task,
    )
    create_fa(
        account=user.account,
        file_key='invited_file.pdf',
        event=event,
    )

    # act
    run_pipeline(account_id=user.account.id)

    # assert
    att = Attachment.objects.get(
        file_id='invited_file.pdf',
    )
    ctype = ContentType.objects.get_for_model(Attachment)
    assert UserObjectPermission.objects.filter(
        user=invited,
        object_pk=str(att.pk),
        permission__content_type=ctype,
    ).exists()


# ═══════════════════════════════════════════════════════════
# N. Full model URL replacement coverage
# ═══════════════════════════════════════════════════════════


def test_e2e__account_logos__both_replaced(
    create_fa,
    run_pipeline,
):
    # arrange
    user = create_test_admin()
    user.account.logo_sm = gcs_url('logo_sm.png')
    user.account.logo_lg = gcs_url('logo_lg.png')
    user.account.save(
        update_fields=['logo_sm', 'logo_lg'],
    )
    create_fa(
        account=user.account,
        file_key='logo_sm.png',
    )
    create_fa(
        account=user.account,
        file_key='logo_lg.png',
    )

    # act
    run_pipeline(account_id=user.account.id)

    # assert
    user.account.refresh_from_db()
    assert GCS_API not in (
        user.account.logo_sm or ''
    )
    assert GCS_API not in (
        user.account.logo_lg or ''
    )


def test_e2e__contact_photo__replaced(
    create_fa,
    run_pipeline,
):
    # arrange
    user = create_test_admin()
    contact = Contact.objects.create(
        first_name='Test',
        last_name='Contact',
        photo=gcs_url('contact_photo.jpg'),
        account=user.account,
        user=user,
        source='google',
        source_id='123',
        email='contact@test.com',
    )
    create_fa(
        account=user.account,
        file_key='contact_photo.jpg',
    )

    # act
    run_pipeline(account_id=user.account.id)

    # assert
    contact.refresh_from_db()
    assert GCS_API not in (contact.photo or '')


def test_e2e__user_group_photo__replaced(
    create_fa,
    run_pipeline,
):
    # arrange
    user = create_test_admin()
    group = create_test_group(
        account=user.account,
        photo=gcs_url('group_photo.jpg'),
    )
    create_fa(
        account=user.account,
        file_key='group_photo.jpg',
    )

    # act
    run_pipeline(account_id=user.account.id)

    # assert
    group.refresh_from_db()
    assert GCS_API not in (group.photo or '')


def test_e2e__template_draft_json__deep_replaced(
    create_fa,
    run_pipeline,
):
    # arrange
    user = create_test_admin()
    workflow = create_test_workflow(
        user=user, tasks_count=1,
    )
    url = gcs_url('draft_file.pdf')
    create_fa(
        account=user.account,
        file_key='draft_file.pdf',
        workflow=workflow,
    )
    draft, _ = TemplateDraft.objects.update_or_create(
        template=workflow.template,
        defaults={
            'draft': {
                'tasks': [{
                    'description': f'See {url}',
                    'attachments': [{'url': url}],
                }],
            },
        },
    )

    # act
    run_pipeline(account_id=user.account.id)

    # assert
    draft.refresh_from_db()
    assert GCS_API not in str(draft.draft)


# ═══════════════════════════════════════════════════════════
# O. Consistency and boundary values
# ═══════════════════════════════════════════════════════════


def test_e2e__file_size_zero__synced(
    create_fa,
    run_pipeline,
):
    # arrange
    user = create_test_admin()
    create_fa(
        account=user.account,
        file_key='empty_file.pdf',
        size=0,
    )

    # act
    run_pipeline(account_id=user.account.id)

    # assert
    att = Attachment.objects.get(
        file_id='empty_file.pdf',
    )
    assert att is not None


def test_e2e__pipeline_fail_midway__consistent(
    create_fa,
    run_fill,
    run_migrate,
):
    # arrange
    user = create_test_admin()
    create_fa(
        account=user.account,
        file_key='midway.pdf',
    )

    # act — fill succeeds
    run_fill(account_id=user.account.id)
    fa = FileAttachment.objects.get(
        url=gcs_url('midway.pdf'),
    )
    assert fa.file_id == 'midway.pdf'
    assert not Attachment.objects.exists()

    # act — migrate picks up
    run_migrate(account_id=user.account.id)

    # assert
    assert Attachment.objects.filter(
        file_id='midway.pdf',
    ).exists()


def test_e2e__replace_fa_processed_last(
    create_fa,
    run_pipeline,
):
    # arrange
    user = create_test_admin()
    workflow = create_test_workflow(
        user=user, tasks_count=1,
    )
    url = gcs_url('ordering_file.pdf')
    fa = create_fa(
        account=user.account,
        file_key='ordering_file.pdf',
        workflow=workflow,
    )
    event = create_test_event(
        workflow=workflow, user=user,
    )
    event.text = f'Link: {url}'
    event.save(update_fields=['text'])

    # act
    run_pipeline(account_id=user.account.id)

    # assert
    event.refresh_from_db()
    fa.refresh_from_db()
    assert GCS_API not in event.text
    assert GCS_API not in (fa.url or '')


def test_e2e__no_bucket_name__global_mapping(
    create_fa,
    run_pipeline,
):
    # arrange
    user = create_test_admin()
    workflow = create_test_workflow(
        user=user, tasks_count=1,
    )
    create_fa(
        account=user.account,
        file_key='global_bucket.pdf',
        workflow=workflow,
    )

    # act
    run_pipeline(account_id=user.account.id)

    # assert
    assert Attachment.objects.filter(
        file_id='global_bucket.pdf',
    ).exists()
