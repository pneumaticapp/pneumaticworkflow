"""Tests for fill_file_attachment_file_id management command."""
import pytest

from src.processes.models.workflows.attachment import (
    FileAttachment,
)
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_admin,
)
from .conftest import GCS_API, GCS_CLOUD, BUCKET

pytestmark = pytest.mark.django_db


# -- GCS URL extraction -------------------------------------------


def test_fill__gcs_url__extracts_file_id(create_fa, run_fill):
    # arrange
    user = create_test_admin()
    create_fa(
        account=user.account,
        file_key='prefix_file.pdf',
    )

    # act
    run_fill(account_id=user.account.id)

    # assert
    fa = FileAttachment.objects.get(
        name='prefix_file.pdf',
    )
    assert fa.file_id == 'prefix_file.pdf'


def test_fill__cloud_google_url__extracts_file_id(
    create_fa,
    run_fill,
):
    # arrange
    user = create_test_admin()
    cloud_url = (
        f'{GCS_CLOUD}/{BUCKET}/cloud_file.pdf'
    )
    create_fa(
        account=user.account,
        file_key='cloud_file.pdf',
        url=cloud_url,
    )

    # act
    run_fill(account_id=user.account.id)

    # assert
    fa = FileAttachment.objects.get(
        name='cloud_file.pdf',
    )
    assert fa.file_id == 'cloud_file.pdf'


def test_fill__url_encoded__decodes_correctly(
    create_fa,
    run_fill,
):
    # arrange
    user = create_test_admin()
    encoded = 'File%20(1).pdf'
    url = f'{GCS_API}/{BUCKET}/{encoded}'
    create_fa(
        account=user.account,
        file_key=encoded,
        url=url,
        name='File (1).pdf',
    )

    # act
    run_fill(account_id=user.account.id)

    # assert
    fa = FileAttachment.objects.get(
        name='File (1).pdf',
    )
    assert fa.file_id == 'File (1).pdf'


# -- Skip cases ---------------------------------------------------


def test_fill__non_gcs_url__skipped(create_fa, run_fill):
    # arrange
    user = create_test_admin()
    create_fa(
        account=user.account,
        file_key='ext.pdf',
        url='https://example.com/file.pdf',
    )

    # act
    output = run_fill(account_id=user.account.id)

    # assert
    fa = FileAttachment.objects.get(name='ext.pdf')
    assert fa.file_id is None
    assert 'Skipped: 1' in output


def test_fill__empty_url__skipped(run_fill):
    # arrange
    user = create_test_admin()
    fa = FileAttachment.objects.create(
        name='empty.pdf',
        url='',
        account=user.account,
        size=1024,
    )

    # act
    output = run_fill(account_id=user.account.id)

    # assert
    fa.refresh_from_db()
    assert fa.file_id is None
    assert 'Skipped: 1' in output


def test_fill__already_has_file_id__skipped(run_fill):
    # arrange
    user = create_test_admin()
    url = f'{GCS_API}/{BUCKET}/existing.pdf'
    fa = FileAttachment.objects.create(
        name='existing.pdf',
        url=url,
        file_id='already_set',
        account=user.account,
        size=1024,
    )

    # act
    run_fill(account_id=user.account.id)

    # assert
    fa.refresh_from_db()
    assert fa.file_id == 'already_set'


def test_fill__url_no_path_parts__skipped(run_fill):
    # arrange
    user = create_test_admin()
    FileAttachment.objects.create(
        name='nopath.pdf',
        url=f'{GCS_API}/onlybucket',
        account=user.account,
        size=1024,
    )

    # act
    output = run_fill(account_id=user.account.id)

    # assert
    fa = FileAttachment.objects.get(name='nopath.pdf')
    assert fa.file_id is None
    assert 'Skipped: 1' in output


# -- Options -------------------------------------------------------


def test_fill__dry_run__no_changes(create_fa, run_fill):
    # arrange
    user = create_test_admin()
    create_fa(
        account=user.account,
        file_key='dry_file.pdf',
    )

    # act
    output = run_fill(
        account_id=user.account.id,
        dry_run=True,
    )

    # assert
    fa = FileAttachment.objects.get(
        name='dry_file.pdf',
    )
    assert fa.file_id is None
    assert 'DRY RUN' in output
    assert 'Updated: 1' in output


def test_fill__filters_by_account_ids(
    create_fa,
    run_fill,
):
    # arrange
    user = create_test_admin()
    account2 = create_test_account(name='Other')
    create_fa(
        account=user.account,
        file_key='acc1.pdf',
    )
    create_fa(
        account=account2,
        file_key='acc2.pdf',
    )

    # act
    run_fill(account_id=user.account.id)

    # assert
    fa1 = FileAttachment.objects.get(name='acc1.pdf')
    fa2 = FileAttachment.objects.get(name='acc2.pdf')
    assert fa1.file_id == 'acc1.pdf'
    assert fa2.file_id is None


def test_fill__idempotent__second_run_no_changes(
    create_fa,
    run_fill,
):
    # arrange
    user = create_test_admin()
    create_fa(
        account=user.account,
        file_key='idem.pdf',
    )

    # act
    run_fill(account_id=user.account.id)
    output = run_fill(account_id=user.account.id)

    # assert
    assert 'Found 0 attachments' in output


def test_fill__progress_reporting__every_100(
    create_fa,
    run_fill,
):
    # arrange
    user = create_test_admin()
    for i in range(101):
        create_fa(
            account=user.account,
            file_key=f'file_{i:03d}.pdf',
            name=f'file_{i:03d}.pdf',
        )

    # act
    output = run_fill(account_id=user.account.id)

    # assert
    assert 'Processed 100 /' in output
