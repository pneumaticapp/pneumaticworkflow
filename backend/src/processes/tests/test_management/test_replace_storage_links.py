"""Tests for replace_storage_links_with_file_service."""
import pytest
from io import StringIO

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import override_settings

from src.accounts.models import Contact
from src.processes.models.templates.task import TaskTemplate
from src.processes.models.templates.template import (
    TemplateDraft,
)
from src.processes.tests.fixtures import (
    create_test_admin,
    create_test_event,
    create_test_group,
    create_test_workflow,
)
from src.processes.models.workflows.attachment import (
    FileAttachment,
)
from .conftest import GCS_API, FS_DOMAIN, gcs_url

pytestmark = pytest.mark.django_db


# ── Text field replacement ───────────────────────────────────


def test_replace__event_text__replaced(
    create_fa_with_file_id,
    run_replace,
):
    # arrange
    user = create_test_admin()
    workflow = create_test_workflow(
        user=user,
        tasks_count=1,
    )
    url = gcs_url('evt.pdf')
    create_fa_with_file_id(account=user.account, file_id='evt.pdf')
    event = create_test_event(
        workflow=workflow,
        user=user,
    )
    event.text = f'File: {url}'
    event.save(update_fields=['text'])

    # act
    run_replace(account_id=user.account.id)

    # assert
    event.refresh_from_db()
    assert FS_DOMAIN in event.text
    assert GCS_API not in event.text


def test_replace__task_description__replaced(
    create_fa_with_file_id,
    run_replace,
):
    # arrange
    user = create_test_admin()
    workflow = create_test_workflow(
        user=user,
        tasks_count=1,
    )
    task = workflow.tasks.first()
    url = gcs_url('task.pdf')
    create_fa_with_file_id(account=user.account, file_id='task.pdf')
    task.description = f'See {url}'
    task.save(update_fields=['description'])

    # act
    run_replace(account_id=user.account.id)

    # assert
    task.refresh_from_db()
    assert FS_DOMAIN in task.description
    assert GCS_API not in task.description


def test_replace__workflow_description__replaced(
    create_fa_with_file_id,
    run_replace,
):
    # arrange
    user = create_test_admin()
    workflow = create_test_workflow(
        user=user,
        tasks_count=1,
    )
    url = gcs_url('wf.pdf')
    create_fa_with_file_id(account=user.account, file_id='wf.pdf')
    workflow.description = f'Details: {url}'
    workflow.save(update_fields=['description'])

    # act
    run_replace(account_id=user.account.id)

    # assert
    workflow.refresh_from_db()
    assert FS_DOMAIN in workflow.description
    assert GCS_API not in workflow.description


def test_replace__template_description__replaced(
    create_fa_with_file_id,
    run_replace,
):
    # arrange
    user = create_test_admin()
    workflow = create_test_workflow(
        user=user,
        tasks_count=1,
    )
    template = workflow.template
    url = gcs_url('tmpl.pdf')
    create_fa_with_file_id(account=user.account, file_id='tmpl.pdf')
    template.description = f'Tmpl: {url}'
    template.save(update_fields=['description'])

    # act
    run_replace(account_id=user.account.id)

    # assert
    template.refresh_from_db()
    assert FS_DOMAIN in template.description


def test_replace__task_template_desc__replaced(
    create_fa_with_file_id,
    run_replace,
):
    # arrange
    user = create_test_admin()
    workflow = create_test_workflow(
        user=user,
        tasks_count=1,
    )
    tt = TaskTemplate.objects.filter(
        template=workflow.template,
    ).first()
    url = gcs_url('tt.pdf')
    create_fa_with_file_id(account=user.account, file_id='tt.pdf')
    tt.description = f'TaskTmpl: {url}'
    tt.save(update_fields=['description'])

    # act
    run_replace(account_id=user.account.id)

    # assert
    tt.refresh_from_db()
    assert FS_DOMAIN in tt.description


# ── JSON field replacement ───────────────────────────────────


def test_replace__event_task_json__deep_replaced(
    create_fa_with_file_id,
    run_replace,
):
    # arrange
    user = create_test_admin()
    workflow = create_test_workflow(
        user=user,
        tasks_count=1,
    )
    url = gcs_url('json.pdf')
    create_fa_with_file_id(account=user.account, file_id='json.pdf')
    event = create_test_event(
        workflow=workflow,
        user=user,
    )
    event.task_json = {
        'attachments': [
            {'url': url, 'name': 'file.pdf'},
        ],
    }
    event.save(update_fields=['task_json'])

    # act
    run_replace(account_id=user.account.id)

    # assert
    event.refresh_from_db()
    assert GCS_API not in str(event.task_json)
    assert FS_DOMAIN in str(event.task_json)


def test_replace__template_draft_json__deep_replaced(
    create_fa_with_file_id,
    run_replace,
):
    # arrange
    user = create_test_admin()
    workflow = create_test_workflow(
        user=user,
        tasks_count=1,
    )
    url = gcs_url('draft.pdf')
    create_fa_with_file_id(account=user.account, file_id='draft.pdf')
    draft, _ = TemplateDraft.objects.update_or_create(
        template=workflow.template,
        defaults={
            'draft': {
                'tasks': [{'desc': f'See {url}'}],
            },
        },
    )

    # act
    run_replace(account_id=user.account.id)

    # assert
    draft.refresh_from_db()
    assert GCS_API not in str(draft.draft)
    assert FS_DOMAIN in str(draft.draft)


# ── Logos and photos ─────────────────────────────────────────


def test_replace__account_logo_sm_lg__replaced(
    create_fa_with_file_id,
    run_replace,
):
    # arrange
    user = create_test_admin()
    user.account.logo_sm = gcs_url('logo_sm.png')
    user.account.logo_lg = gcs_url('logo_lg.png')
    user.account.save(
        update_fields=['logo_sm', 'logo_lg'],
    )
    create_fa_with_file_id(
        account=user.account,
        file_id='logo_sm.png',
    )
    create_fa_with_file_id(
        account=user.account,
        file_id='logo_lg.png',
    )

    # act
    run_replace(account_id=user.account.id)

    # assert
    user.account.refresh_from_db()
    assert GCS_API not in (user.account.logo_sm or '')
    assert GCS_API not in (user.account.logo_lg or '')


def test_replace__contact_photo__replaced(
    create_fa_with_file_id,
    run_replace,
):
    # arrange
    user = create_test_admin()
    contact = Contact.objects.create(
        first_name='Test',
        last_name='User',
        photo=gcs_url('contact.jpg'),
        account=user.account,
        user=user,
        source='google',
        source_id=123,
        email='contact@test.com',
    )
    create_fa_with_file_id(
        account=user.account,
        file_id='contact.jpg',
    )

    # act
    run_replace(account_id=user.account.id)

    # assert
    contact.refresh_from_db()
    assert GCS_API not in (contact.photo or '')


def test_replace__user_group_photo__replaced(
    create_fa_with_file_id,
    run_replace,
):
    # arrange
    user = create_test_admin()
    group = create_test_group(
        account=user.account,
        photo=gcs_url('group.jpg'),
    )
    create_fa_with_file_id(
        account=user.account,
        file_id='group.jpg',
    )

    # act
    run_replace(account_id=user.account.id)

    # assert
    group.refresh_from_db()
    assert GCS_API not in (group.photo or '')


# ── URL mapping edge cases ───────────────────────────────────


def test_replace__thumbnail_url__mapped(
    create_fa_with_file_id,
    run_replace,
):
    # arrange
    user = create_test_admin()
    thumb_url = gcs_url('thumb_main_thumb.jpg')
    create_fa_with_file_id(
        account=user.account,
        file_id='thumb_main.pdf',
        thumbnail_url=thumb_url,
    )

    # act
    run_replace(account_id=user.account.id)

    # assert
    fa = FileAttachment.objects.get(
        file_id='thumb_main.pdf',
    )
    assert GCS_API not in (fa.url or '')
    assert GCS_API not in (fa.thumbnail_url or '')


def test_replace__bucket_path__global_mapping(
    create_fa_with_file_id,
    run_replace,
):
    """Global pneumatic-bucket-dev is in url_mapping."""

    # arrange
    user = create_test_admin()
    workflow = create_test_workflow(
        user=user,
        tasks_count=1,
    )
    task = workflow.tasks.first()
    url = (
        'https://storage.googleapis.com'
        '/pneumatic-bucket-dev/file.pdf'
    )
    task.description = f'See {url}'
    task.save(update_fields=['description'])

    # act
    run_replace(account_id=user.account.id)

    # assert
    task.refresh_from_db()
    assert 'pneumatic-bucket-dev' not in task.description
    assert FS_DOMAIN in task.description


def test_replace__exact_url_priority_over_base_bucket(
    create_fa_with_file_id,
    run_replace,
):
    """Exact attachment URL must match before base bucket URL.

    Without longest-match-first ordering, the shorter base
    bucket URL ``https://storage.googleapis.com/{bucket}``
    could replace first, leaving the raw (unencoded) filename
    in the result instead of the properly encoded file_id.
    """

    # arrange
    user = create_test_admin()
    workflow = create_test_workflow(
        user=user,
        tasks_count=1,
    )
    file_id = 'PqRsTu_Picture (1).png'
    url = gcs_url(file_id)
    create_fa_with_file_id(
        account=user.account,
        file_id=file_id,
        url=url,
    )
    task = workflow.tasks.first()
    task.description = f'See {url}'
    task.save(update_fields=['description'])

    # act
    run_replace(account_id=user.account.id)

    # assert — must use encoded file_id, not raw filename
    task.refresh_from_db()
    assert GCS_API not in task.description
    assert 'Picture (1)' not in task.description
    assert 'Picture%20%281%29' in task.description
    assert FS_DOMAIN in task.description


def test_replace__file_attachment_processed_last(
    create_fa_with_file_id,
    run_replace,
):
    """FA.url updated last so mapping is still valid."""

    # arrange
    user = create_test_admin()
    workflow = create_test_workflow(
        user=user,
        tasks_count=1,
    )
    url = gcs_url('last.pdf')
    fa = create_fa_with_file_id(
        account=user.account,
        file_id='last.pdf',
    )
    event = create_test_event(
        workflow=workflow,
        user=user,
    )
    event.text = f'Link: {url}'
    event.save(update_fields=['text'])

    # act
    run_replace(account_id=user.account.id)

    # assert
    event.refresh_from_db()
    fa.refresh_from_db()
    assert GCS_API not in event.text
    assert GCS_API not in (fa.url or '')


def test_replace__idempotent__second_run_safe(
    create_fa_with_file_id,
    run_replace,
):
    # arrange
    user = create_test_admin()
    workflow = create_test_workflow(
        user=user,
        tasks_count=1,
    )
    url = gcs_url('idem.pdf')
    create_fa_with_file_id(account=user.account, file_id='idem.pdf')
    event = create_test_event(
        workflow=workflow,
        user=user,
    )
    event.text = f'File: {url}'
    event.save(update_fields=['text'])

    # act
    run_replace(account_id=user.account.id)
    run_replace(account_id=user.account.id)

    # assert
    event.refresh_from_db()
    assert FS_DOMAIN in event.text


# ── Options ──────────────────────────────────────────────────


def test_replace__dry_run__no_changes(
    create_fa_with_file_id,
    run_replace,
):
    # arrange
    user = create_test_admin()
    workflow = create_test_workflow(
        user=user,
        tasks_count=1,
    )
    url = gcs_url('dry.pdf')
    create_fa_with_file_id(account=user.account, file_id='dry.pdf')
    event = create_test_event(
        workflow=workflow,
        user=user,
    )
    event.text = f'File: {url}'
    event.save(update_fields=['text'])

    # act
    output = run_replace(
        account_id=user.account.id,
        dry_run=True,
    )

    # assert
    event.refresh_from_db()
    assert url in event.text
    assert 'DRY RUN' in output


def test_replace__no_file_service_domain__raises():
    # arrange
    user = create_test_admin()

    # act
    with pytest.raises(
        CommandError,
        match='FILE_SERVICE_URL',
    ), override_settings(FILE_SERVICE_URL=None):
        call_command(
            'replace_storage_links_with_file_service',
            account_ids=str(user.account.id),
            file_service_domain='',
            stdout=StringIO(),
        )


# ── URL encoding (P4) ───────────────────────────────────────


def test_replace__special_chars_file_id__url_encoded(
    create_fa_with_file_id,
    run_replace,
):
    """File_id with special chars must be URL-encoded."""
    # arrange
    user = create_test_admin()
    workflow = create_test_workflow(
        user=user,
        tasks_count=1,
    )
    file_id = 'NiihssB_Drawing (v2).odg'
    url = gcs_url(file_id)
    create_fa_with_file_id(
        account=user.account,
        file_id=file_id,
        url=url,
    )
    event = create_test_event(
        workflow=workflow,
        user=user,
    )
    event.text = f'File: {url}'
    event.save(update_fields=['text'])

    # act
    run_replace(account_id=user.account.id)

    # assert
    event.refresh_from_db()
    assert 'Drawing (v2)' not in event.text
    assert 'Drawing%20%28v2%29' in event.text
    assert FS_DOMAIN in event.text


def test_replace__file_id_with_spaces__url_encoded(
    create_fa_with_file_id,
    run_replace,
):
    """File_id with spaces must be URL-encoded."""
    # arrange
    user = create_test_admin()
    workflow = create_test_workflow(
        user=user,
        tasks_count=1,
    )
    file_id = 'Zfcsx_Screencast 2023-08-16.webm'
    url = gcs_url(file_id)
    create_fa_with_file_id(
        account=user.account,
        file_id=file_id,
        url=url,
    )
    event = create_test_event(
        workflow=workflow,
        user=user,
    )
    event.text = f'File: {url}'
    event.save(update_fields=['text'])

    # act
    run_replace(account_id=user.account.id)

    # assert
    event.refresh_from_db()
    assert '%20' in event.text
    assert FS_DOMAIN in event.text


def test_replace__ascii_file_id__not_encoded(
    create_fa_with_file_id,
    run_replace,
):
    """ASCII-only file_id must NOT be encoded (stays readable)."""
    # arrange
    user = create_test_admin()
    workflow = create_test_workflow(
        user=user,
        tasks_count=1,
    )
    file_id = 'VumcsgTMm_pic.png'
    url = gcs_url(file_id)
    create_fa_with_file_id(
        account=user.account,
        file_id=file_id,
        url=url,
    )
    event = create_test_event(
        workflow=workflow,
        user=user,
    )
    event.text = f'File: {url}'
    event.save(update_fields=['text'])

    # act
    run_replace(account_id=user.account.id)

    # assert
    event.refresh_from_db()
    expected_url = f'{FS_DOMAIN}/{file_id}'
    assert expected_url in event.text


def test_replace__special_thumbnail__url_encoded(
    create_fa_with_file_id,
    run_replace,
):
    """Thumbnail URL with special chars in file_id must also be encoded."""
    # arrange
    user = create_test_admin()
    file_id = 'AbcDefGh_Photo (1).jpg'
    thumb_url = gcs_url(f'{file_id}_thumb')
    create_fa_with_file_id(
        account=user.account,
        file_id=file_id,
        thumbnail_url=thumb_url,
    )

    # act
    run_replace(account_id=user.account.id)

    # assert
    fa = FileAttachment.objects.get(file_id=file_id)
    assert 'Photo (1)' not in (fa.thumbnail_url or '')
    assert GCS_API not in (fa.thumbnail_url or '')


def test_replace__encoded_idempotent__second_run_safe(
    create_fa_with_file_id,
    run_replace,
):
    """Double run with encoded URLs must not double-encode."""
    # arrange
    user = create_test_admin()
    workflow = create_test_workflow(
        user=user,
        tasks_count=1,
    )
    file_id = 'NiihssB_Document (v1).pdf'
    url = gcs_url(file_id)
    create_fa_with_file_id(
        account=user.account,
        file_id=file_id,
        url=url,
    )
    event = create_test_event(
        workflow=workflow,
        user=user,
    )
    event.text = f'File: {url}'
    event.save(update_fields=['text'])

    # act
    run_replace(account_id=user.account.id)
    event.refresh_from_db()

    run_replace(account_id=user.account.id)
    event.refresh_from_db()
    second_text = event.text

    # assert: no double encoding (%25 would mean % was re-encoded)
    assert '%25' not in second_text
    assert FS_DOMAIN in second_text


def test_replace__json_field_with_special_chars__encoded(
    create_fa_with_file_id,
    run_replace,
):
    """JSON fields with special chars in file_id URLs must be encoded."""
    # arrange
    user = create_test_admin()
    workflow = create_test_workflow(
        user=user,
        tasks_count=1,
    )
    file_id = 'XyzUvwRs_Report (Q1).xlsx'
    url = gcs_url(file_id)
    create_fa_with_file_id(
        account=user.account,
        file_id=file_id,
        url=url,
    )
    event = create_test_event(
        workflow=workflow,
        user=user,
    )
    event.task_json = {'attachments': [{'url': url}]}
    event.save(update_fields=['task_json'])

    # act
    run_replace(account_id=user.account.id)

    # assert
    event.refresh_from_db()
    json_str = str(event.task_json)
    assert 'Report (Q1)' not in json_str
    assert FS_DOMAIN in json_str
