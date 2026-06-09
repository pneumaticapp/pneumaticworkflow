import pytest
from django.test import override_settings

from src.processes.enums import FieldType
from src.processes.models.templates.fields import FieldTemplate
from src.processes.tests.fixtures import (
    create_test_admin,
    create_test_attachment,
    create_test_account,
    create_test_template,
    create_test_workflow,
)
from src.storage.enums import AccessType, SourceType
from src.storage.models import Attachment
from src.storage.utils import (
    extract_all_file_ids_from_source,
    extract_file_ids_from_text,
    extract_file_ids_from_values,
    get_attachment_description_fields,
    refresh_attachments,
    sync_account_file_fields,
    get_file_service_file_url,
)

pytestmark = pytest.mark.django_db

_FILE_SERVICE_URL = 'https://example.com'
_FILE_SERVICE_HOST_PATH = 'example.com'


class TestExtractFileIdsFromText:

    def test_extract_file_ids__empty_text__empty_list(self):
        # act
        with override_settings(
                FILES_BASE_URL=_FILE_SERVICE_URL,
                FILE_SERVICE_HOST_PATH=_FILE_SERVICE_HOST_PATH,
        ):
            result = extract_file_ids_from_text('')

        # assert
        assert result == []

    def test_extract_file_ids__none__empty_list(self):
        # act
        with override_settings(
                FILES_BASE_URL=_FILE_SERVICE_URL,
                FILE_SERVICE_HOST_PATH=_FILE_SERVICE_HOST_PATH,
        ):
            result = extract_file_ids_from_text(None)

        # assert
        assert result == []

    def test_extract_file_ids__files_pattern__ok(self):
        # arrange
        text = (
            'Check this file: '
            '[doc](https://example.com/abc123def456ghi789)'
        )

        # act
        with override_settings(
                FILES_BASE_URL=_FILE_SERVICE_URL,
                FILE_SERVICE_HOST_PATH=_FILE_SERVICE_HOST_PATH,
        ):
            result = extract_file_ids_from_text(text)

        # assert
        assert 'abc123def456ghi789' in result

    def test_extract_file_ids__files_pattern_only__ok(self):
        # arrange
        text = (
            'Download from: '
            '[file](https://example.com/xyz987uvw654rst321)'
        )

        # act
        with override_settings(
                FILES_BASE_URL=_FILE_SERVICE_URL,
                FILE_SERVICE_HOST_PATH=_FILE_SERVICE_HOST_PATH,
        ):
            result = extract_file_ids_from_text(text)

        # assert
        assert 'xyz987uvw654rst321' in result

    def test_extract_file_ids__plain_file_id_not_supported__empty(self):
        # arrange
        text = 'file_id=qwerty123456asdfgh or file_id:mnbvcx098765lkjhgf'

        # act
        with override_settings(
                FILES_BASE_URL=_FILE_SERVICE_URL,
                FILE_SERVICE_HOST_PATH=_FILE_SERVICE_HOST_PATH,
        ):
            result = extract_file_ids_from_text(text)

        # assert
        assert result == []

    def test_extract_file_ids__multiple__ok(self):
        # arrange
        text = (
            'Files: [a](https://example.com/file1_id_123456) and '
            '[b](https://example.com/file2_id_789012)'
        )

        # act
        with override_settings(
                FILES_BASE_URL=_FILE_SERVICE_URL,
                FILE_SERVICE_HOST_PATH=_FILE_SERVICE_HOST_PATH,
        ):
            result = extract_file_ids_from_text(text)

        # assert
        assert len(result) == 2
        assert 'file1_id_123456' in result
        assert 'file2_id_789012' in result

    def test_extract_file_ids__duplicates_removed__ok(self):
        # arrange
        text = (
            '[x](https://example.com/duplicate_id_123) and '
            '[y](https://example.com/duplicate_id_123)'
        )

        # act
        with override_settings(
                FILES_BASE_URL=_FILE_SERVICE_URL,
                FILE_SERVICE_HOST_PATH=_FILE_SERVICE_HOST_PATH,
        ):
            result = extract_file_ids_from_text(text)

        # assert
        assert result.count('duplicate_id_123') == 1

    def test_extract_file_ids__no_matches__empty_list(self):
        # arrange
        text = 'This text has no file IDs'

        # act
        with override_settings(
                FILES_BASE_URL=_FILE_SERVICE_URL,
                FILE_SERVICE_HOST_PATH=_FILE_SERVICE_HOST_PATH,
        ):
            result = extract_file_ids_from_text(text)

        # assert
        assert result == []

    def test_extract_file_ids__short_id__not_matched(self):
        # arrange
        text = '[f](https://example.com/short)'

        # act
        with override_settings(
                FILES_BASE_URL=_FILE_SERVICE_URL,
                FILE_SERVICE_HOST_PATH=_FILE_SERVICE_HOST_PATH,
        ):
            result = extract_file_ids_from_text(text)

        # assert
        assert result == []

    def test_extract_file_ids__special_chars__ok(self):
        # arrange
        text = '[f](https://example.com/file-id_with-special_123456)'

        # act
        with override_settings(
                FILES_BASE_URL=_FILE_SERVICE_URL,
                FILE_SERVICE_HOST_PATH=_FILE_SERVICE_HOST_PATH,
        ):
            result = extract_file_ids_from_text(text)

        # assert
        assert 'file-id_with-special_123456' in result

    def test_extract_file_ids__file_id_with_dot__ok(self):
        """Legacy GCS file_id with dot (extension) must be captured."""
        # arrange
        text = (
            '[pic.png](https://example.com/'
            'VumcsgTMmIiSagrYrvDdMFUBbWhUYN_pic.png)'
        )

        # act
        with override_settings(
                FILES_BASE_URL=_FILE_SERVICE_URL,
                FILE_SERVICE_HOST_PATH=_FILE_SERVICE_HOST_PATH,
        ):
            result = extract_file_ids_from_text(text)

        # assert
        assert 'VumcsgTMmIiSagrYrvDdMFUBbWhUYN_pic.png' in result

    def test_extract_file_ids__file_id_with_multiple_dots__ok(self):
        """File_id with multiple dots must be fully captured."""
        # arrange
        text = (
            '[report](https://example.com/'
            'ZfcsxZayjl_report.final.v2.pdf)'
        )

        # act
        with override_settings(
                FILES_BASE_URL=_FILE_SERVICE_URL,
                FILE_SERVICE_HOST_PATH=_FILE_SERVICE_HOST_PATH,
        ):
            result = extract_file_ids_from_text(text)

        # assert
        assert 'ZfcsxZayjl_report.final.v2.pdf' in result

    def test_extract_file_ids__image_markdown_with_dot__ok(self):
        """Image markdown ![name](url) with dotted file_id."""
        # arrange
        text = '![photo](https://example.com/AbcDefGhIj_photo.jpg)'

        # act
        with override_settings(
                FILES_BASE_URL=_FILE_SERVICE_URL,
                FILE_SERVICE_HOST_PATH=_FILE_SERVICE_HOST_PATH,
        ):
            result = extract_file_ids_from_text(text)

        # assert
        assert 'AbcDefGhIj_photo.jpg' in result

    def test_extract_file_ids__uuid_without_dots__still_works(self):
        """UUID-based file_id (no dots) still captured correctly."""
        # arrange
        uuid_id = '550e8400-e29b-41d4-a716-446655440000'
        text = f'[doc](https://example.com/{uuid_id})'

        # act
        with override_settings(
                FILES_BASE_URL=_FILE_SERVICE_URL,
                FILE_SERVICE_HOST_PATH=_FILE_SERVICE_HOST_PATH,
        ):
            result = extract_file_ids_from_text(text)

        # assert
        assert uuid_id in result


class TestExtractFileIdsFromValuesDotSupport:

    def test_plain_url__file_id_with_dot__extracts(self):
        """Plain URL with dotted file_id must be extracted."""
        # arrange
        values = [
            'https://example.com/VumcsgTMmIiSagrYrvDd_pic.png',
        ]

        # act
        with override_settings(
                FILES_BASE_URL=_FILE_SERVICE_URL,
                FILE_SERVICE_HOST_PATH=_FILE_SERVICE_HOST_PATH,
        ):
            result = extract_file_ids_from_values(values)

        # assert
        assert result == ['VumcsgTMmIiSagrYrvDd_pic.png']

    def test_plain_url__file_id_with_multiple_dots__extracts(self):
        """Plain URL with multi-dotted file_id must be extracted."""
        # arrange
        values = [
            'https://example.com/ZfcsxZayjl_report.final.v2.pdf',
        ]

        # act
        with override_settings(
                FILES_BASE_URL=_FILE_SERVICE_URL,
                FILE_SERVICE_HOST_PATH=_FILE_SERVICE_HOST_PATH,
        ):
            result = extract_file_ids_from_values(values)

        # assert
        assert result == ['ZfcsxZayjl_report.final.v2.pdf']


class TestExtractFileIdsDotEdgeCases:
    """Extended edge cases for dot support in file_id regex (P2)."""

    def test_extract__mixed_uuid_and_legacy_in_same_text__ok(self):
        """Both UUID and dotted legacy file_ids in same text."""
        # arrange
        uuid_id = '550e8400-e29b-41d4-a716-446655440000'
        legacy_id = 'VumcsgTMmIiSagrYrvDd_pic.png'
        text = (
            f'New: [doc](https://example.com/{uuid_id}) '
            f'Old: [pic](https://example.com/{legacy_id})'
        )

        # act
        with override_settings(
                FILES_BASE_URL=_FILE_SERVICE_URL,
                FILE_SERVICE_HOST_PATH=_FILE_SERVICE_HOST_PATH,
        ):
            result = extract_file_ids_from_text(text)

        # assert
        assert len(result) == 2
        assert uuid_id in result
        assert legacy_id in result

    def test_extract__multiple_dotted_ids_in_text__all_captured(self):
        """Multiple different dotted file_ids are all captured."""
        # arrange
        text = (
            '[a](https://example.com/AbcDefGh_photo.jpg) '
            '[b](https://example.com/XyzUvwRs_doc.pdf) '
            '[c](https://example.com/MnoPqrSt_data.csv)'
        )

        # act
        with override_settings(
                FILES_BASE_URL=_FILE_SERVICE_URL,
                FILE_SERVICE_HOST_PATH=_FILE_SERVICE_HOST_PATH,
        ):
            result = extract_file_ids_from_text(text)

        # assert
        assert len(result) == 3
        assert 'AbcDefGh_photo.jpg' in result
        assert 'XyzUvwRs_doc.pdf' in result
        assert 'MnoPqrSt_data.csv' in result

    def test_extract__image_with_title_and_dot__ok(self):
        """Image markdown with title attribute and dotted file_id."""
        # arrange
        text = (
            '![photo](https://example.com/'
            'AbcDefGhIj_photo.jpg "My Photo")'
        )

        # act
        with override_settings(
                FILES_BASE_URL=_FILE_SERVICE_URL,
                FILE_SERVICE_HOST_PATH=_FILE_SERVICE_HOST_PATH,
        ):
            result = extract_file_ids_from_text(text)

        # assert
        assert 'AbcDefGhIj_photo.jpg' in result

    def test_extract__boundary_8_chars_with_dot__ok(self):
        """Minimum length file_id (8 chars) with dot."""
        # arrange
        text = '[f](https://example.com/abc.defg)'

        # act
        with override_settings(
                FILES_BASE_URL=_FILE_SERVICE_URL,
                FILE_SERVICE_HOST_PATH=_FILE_SERVICE_HOST_PATH,
        ):
            result = extract_file_ids_from_text(text)

        # assert
        assert 'abc.defg' in result

    def test_extract__7_chars_with_dot__not_matched(self):
        """Below minimum length (7 chars) even with dot."""
        # arrange
        text = '[f](https://example.com/ab.defg)'

        # act
        with override_settings(
                FILES_BASE_URL=_FILE_SERVICE_URL,
                FILE_SERVICE_HOST_PATH=_FILE_SERVICE_HOST_PATH,
        ):
            result = extract_file_ids_from_text(text)

        # assert
        assert result == []

    def test_extract__dot_only_extension__captured_correctly(self):
        """File_id like 'prefix_file.tar.gz' captured fully."""
        # arrange
        text = (
            '[archive](https://example.com/'
            'LongPrefixHere_file.tar.gz)'
        )

        # act
        with override_settings(
                FILES_BASE_URL=_FILE_SERVICE_URL,
                FILE_SERVICE_HOST_PATH=_FILE_SERVICE_HOST_PATH,
        ):
            result = extract_file_ids_from_text(text)

        # assert
        assert 'LongPrefixHere_file.tar.gz' in result

    def test_extract__encoded_cyrillic__decoded_to_match_db(self):
        """URL-encoded cyrillic file_id must be decoded via unquote."""
        # arrange
        text = (
            '[Рисунок](https://example.com/'
            'NiihssB_%D0%A0%D0%B8%D1%81%D1%83'
            '%D0%BD%D0%BE%D0%BA.odg)'
        )

        # act
        with override_settings(
                FILES_BASE_URL=_FILE_SERVICE_URL,
                FILE_SERVICE_HOST_PATH=_FILE_SERVICE_HOST_PATH,
        ):
            result = extract_file_ids_from_text(text)

        # assert — decoded to match DB value
        assert 'NiihssB_Рисунок.odg' in result

    def test_extract__encoded_spaces__decoded_to_match_db(self):
        """URL-encoded spaces must be decoded to match DB value."""
        # arrange
        text = (
            '[video](https://example.com/'
            'Zfcsx_Screencast%202023-08-16.webm)'
        )

        # act
        with override_settings(
                FILES_BASE_URL=_FILE_SERVICE_URL,
                FILE_SERVICE_HOST_PATH=_FILE_SERVICE_HOST_PATH,
        ):
            result = extract_file_ids_from_text(text)

        # assert
        assert 'Zfcsx_Screencast 2023-08-16.webm' in result

    def test_extract__mixed_encoded_and_plain__both_decoded(self):
        """Mix of encoded cyrillic and plain UUID, both extracted."""
        # arrange
        uuid_id = '550e8400-e29b-41d4-a716-446655440000'
        text = (
            f'[doc](https://example.com/{uuid_id}) '
            '[pic](https://example.com/'
            'AbcDefGh_%D0%A4%D0%BE%D1%82%D0%BE.jpg)'
        )

        # act
        with override_settings(
                FILES_BASE_URL=_FILE_SERVICE_URL,
                FILE_SERVICE_HOST_PATH=_FILE_SERVICE_HOST_PATH,
        ):
            result = extract_file_ids_from_text(text)

        # assert
        assert len(result) == 2
        assert uuid_id in result
        assert 'AbcDefGh_Фото.jpg' in result


class TestExtractEncodedFromValues:

    def test_plain_url__encoded_cyrillic__decoded(self):
        """Plain URL with encoded cyrillic must be decoded."""
        # arrange
        values = [
            'https://example.com/'
            'NiihssB_%D0%A0%D0%B8%D1%81%D1%83'
            '%D0%BD%D0%BE%D0%BA.odg',
        ]

        # act
        with override_settings(
                FILES_BASE_URL=_FILE_SERVICE_URL,
                FILE_SERVICE_HOST_PATH=_FILE_SERVICE_HOST_PATH,
        ):
            result = extract_file_ids_from_values(values)

        # assert
        assert result == ['NiihssB_Рисунок.odg']

    def test_plain_url__encoded_spaces__decoded(self):
        """Plain URL with encoded spaces must be decoded."""
        # arrange
        values = [
            'https://example.com/'
            'Zfcsx_Screencast%202023-08-16.webm',
        ]

        # act
        with override_settings(
                FILES_BASE_URL=_FILE_SERVICE_URL,
                FILE_SERVICE_HOST_PATH=_FILE_SERVICE_HOST_PATH,
        ):
            result = extract_file_ids_from_values(values)

        # assert
        assert result == ['Zfcsx_Screencast 2023-08-16.webm']


class TestExtractFileIdsFromValues:

    def test_plain_url__single__extracts_file_id(self):
        # arrange
        values = ['https://example.com/abc123def456ghi789']

        # act
        with override_settings(
                FILES_BASE_URL=_FILE_SERVICE_URL,
                FILE_SERVICE_HOST_PATH=_FILE_SERVICE_HOST_PATH,
        ):
            result = extract_file_ids_from_values(values)

        # assert
        assert result == ['abc123def456ghi789']

    def test_plain_url__with_query__extracts_file_id(self):
        # arrange
        values = ['https://example.com/xyz987uvw654?token=abc']

        # act
        with override_settings(
                FILES_BASE_URL=_FILE_SERVICE_URL,
                FILE_SERVICE_HOST_PATH=_FILE_SERVICE_HOST_PATH,
        ):
            result = extract_file_ids_from_values(values)

        # assert
        assert result == ['xyz987uvw654']

    def test_plain_url__multiple_values__deduplicated(self):
        # arrange
        values = [
            'https://example.com/file1_id_123456',
            'https://example.com/file1_id_123456',
        ]

        # act
        with override_settings(
                FILES_BASE_URL=_FILE_SERVICE_URL,
                FILE_SERVICE_HOST_PATH=_FILE_SERVICE_HOST_PATH,
        ):
            result = extract_file_ids_from_values(values)

        # assert
        assert result == ['file1_id_123456']

    def test_plain_url__non_file_service__empty(self):
        # arrange
        values = ['https://other.com/abc123def456ghi789']

        # act
        with override_settings(
                FILES_BASE_URL=_FILE_SERVICE_URL,
                FILE_SERVICE_HOST_PATH=_FILE_SERVICE_HOST_PATH,
        ):
            result = extract_file_ids_from_values(values)

        # assert
        assert result == []

    def test_markdown_and_plain_url__both_extracted(self):
        # arrange
        values = [
            'https://example.com/plain_id_123456',
            'See [doc](https://example.com/markdown_id_789012)',
        ]

        # act
        with override_settings(
                FILES_BASE_URL=_FILE_SERVICE_URL,
                FILE_SERVICE_HOST_PATH=_FILE_SERVICE_HOST_PATH,
        ):
            result = extract_file_ids_from_values(values)

        # assert
        assert len(result) == 2
        assert 'plain_id_123456' in result
        assert 'markdown_id_789012' in result

    def test_none_and_empty__ignored(self):
        # arrange
        values = [None, '', 'https://example.com/single_file_id_12']

        # act
        with override_settings(
                FILES_BASE_URL=_FILE_SERVICE_URL,
                FILE_SERVICE_HOST_PATH=_FILE_SERVICE_HOST_PATH,
        ):
            result = extract_file_ids_from_values(values)

        # assert
        assert result == ['single_file_id_12']


class TestSyncAccountFileFields:

    def test_sync_account_file_fields__empty_to_single_url__calls_with_add(
            self,
            mocker,
    ):
        # arrange
        account = create_test_account()
        user = create_test_admin(account=account)
        sync_mock = mocker.patch(
            'src.storage.utils.sync_storage_attachments_for_scope',
        )
        old_values = [None]
        new_values = ['https://example.com/file_id_abc123']

        # act
        with override_settings(
                FILES_BASE_URL=_FILE_SERVICE_URL,
                FILE_SERVICE_HOST_PATH=_FILE_SERVICE_HOST_PATH,
        ):
            sync_account_file_fields(
                account=account,
                user=user,
                old_values=old_values,
                new_values=new_values,
            )

        # assert
        sync_mock.assert_called_once_with(
            account=account,
            user=user,
            add_file_ids=['file_id_abc123'],
            remove_file_ids=[],
            source_type=SourceType.ACCOUNT,
            access_type=AccessType.ACCOUNT,
        )

    def test_sync_account_file_fields__single_url_to_empty__calls_with_remove(
            self,
            mocker,
    ):
        # arrange
        account = create_test_account()
        user = create_test_admin(account=account)
        sync_mock = mocker.patch(
            'src.storage.utils.sync_storage_attachments_for_scope',
        )
        old_values = ['https://example.com/old_file_xyz']
        new_values = [None]

        # act
        with override_settings(
                FILES_BASE_URL=_FILE_SERVICE_URL,
                FILE_SERVICE_HOST_PATH=_FILE_SERVICE_HOST_PATH,
        ):
            sync_account_file_fields(
                account=account,
                user=user,
                old_values=old_values,
                new_values=new_values,
            )

        # assert
        sync_mock.assert_called_once_with(
            account=account,
            user=user,
            add_file_ids=[],
            remove_file_ids=['old_file_xyz'],
            source_type=SourceType.ACCOUNT,
            access_type=AccessType.ACCOUNT,
        )

    def test_sync_account_file_fields__change_url__calls_with_add_and_remove(
            self,
            mocker,
    ):
        # arrange
        account = create_test_account()
        user = create_test_admin(account=account)
        sync_mock = mocker.patch(
            'src.storage.utils.sync_storage_attachments_for_scope',
        )
        old_values = ['https://example.com/old_id_111']
        new_values = ['https://example.com/new_id_222']

        # act
        with override_settings(
                FILES_BASE_URL=_FILE_SERVICE_URL,
                FILE_SERVICE_HOST_PATH=_FILE_SERVICE_HOST_PATH,
        ):
            sync_account_file_fields(
                account=account,
                user=user,
                old_values=old_values,
                new_values=new_values,
            )

        # assert
        sync_mock.assert_called_once_with(
            account=account,
            user=user,
            add_file_ids=['new_id_222'],
            remove_file_ids=['old_id_111'],
            source_type=SourceType.ACCOUNT,
            access_type=AccessType.ACCOUNT,
        )

    def test_sync_account_file_fields__same_url__calls_with_empty_lists(
            self,
            mocker,
    ):
        # arrange
        account = create_test_account()
        user = create_test_admin(account=account)
        sync_mock = mocker.patch(
            'src.storage.utils.sync_storage_attachments_for_scope',
        )
        url = 'https://example.com/same_file_id'
        old_values = [url]
        new_values = [url]

        # act
        with override_settings(
                FILES_BASE_URL=_FILE_SERVICE_URL,
                FILE_SERVICE_HOST_PATH=_FILE_SERVICE_HOST_PATH,
        ):
            sync_account_file_fields(
                account=account,
                user=user,
                old_values=old_values,
                new_values=new_values,
            )

        # assert
        sync_mock.assert_called_once_with(
            account=account,
            user=user,
            add_file_ids=[],
            remove_file_ids=[],
            source_type=SourceType.ACCOUNT,
            access_type=AccessType.ACCOUNT,
        )

    def test_sync_account_file_fields__no_file_domain__calls_sync_with_empty(
            self,
            mocker,
    ):
        # arrange
        account = create_test_account()
        user = create_test_admin(account=account)
        sync_mock = mocker.patch(
            'src.storage.utils.sync_storage_attachments_for_scope',
        )
        old_values = [None]
        new_values = ['https://other.com/not_file_service']

        # act
        with override_settings(FILE_SERVICE_HOST_PATH=None):
            sync_account_file_fields(
                account=account,
                user=user,
                old_values=old_values,
                new_values=new_values,
            )

        # assert
        sync_mock.assert_called_once_with(
            account=account,
            user=user,
            add_file_ids=[],
            remove_file_ids=[],
            source_type=SourceType.ACCOUNT,
            access_type=AccessType.ACCOUNT,
        )


class TestRefreshAttachments:

    def test_refresh_attachments__task__create_new__ok(self):
        # arrange
        user = create_test_admin()
        workflow = create_test_workflow(user=user, tasks_count=1)
        task = workflow.tasks.first()
        task.description = (
            'File: [f](https://example.com/new_file_id_123456)'
        )
        task.save()

        # act
        with override_settings(
                FILES_BASE_URL=_FILE_SERVICE_URL,
                FILE_SERVICE_HOST_PATH=_FILE_SERVICE_HOST_PATH,
        ):
            new_file_ids = refresh_attachments(source=task, user=user)

        # assert
        assert 'new_file_id_123456' in new_file_ids
        assert Attachment.objects.filter(
            file_id='new_file_id_123456',
            task=task,
        ).exists()

    def test_refresh_attachments__workflow__create_new__ok(self):
        # arrange
        user = create_test_admin()
        workflow = create_test_workflow(user=user, tasks_count=1)
        workflow.description = (
            'File: [f](https://example.com/workflow_file_123)'
        )
        workflow.save()

        # act
        with override_settings(
                FILES_BASE_URL=_FILE_SERVICE_URL,
                FILE_SERVICE_HOST_PATH=_FILE_SERVICE_HOST_PATH,
        ):
            new_file_ids = refresh_attachments(source=workflow, user=user)

        # assert
        assert 'workflow_file_123' in new_file_ids
        assert Attachment.objects.filter(
            file_id='workflow_file_123',
            workflow=workflow,
        ).exists()

    def test_refresh_attachments__no_files__delete_old__ok(self):
        # arrange
        user = create_test_admin()
        workflow = create_test_workflow(user=user, tasks_count=1)
        task = workflow.tasks.first()

        create_test_attachment(
            user.account,
            file_id='old_file_to_delete',
            task=task,
        )

        task.description = 'No files here'
        task.save()

        # act
        with override_settings(
                FILES_BASE_URL=_FILE_SERVICE_URL,
                FILE_SERVICE_HOST_PATH=_FILE_SERVICE_HOST_PATH,
        ):
            new_file_ids = refresh_attachments(source=task, user=user)

        # assert
        assert new_file_ids == []
        assert not Attachment.objects.filter(
            file_id='old_file_to_delete',
        ).exists()

    def test_refresh_attachments__keep_existing__ok(self):
        # arrange
        user = create_test_admin()
        workflow = create_test_workflow(user=user, tasks_count=1)
        task = workflow.tasks.first()

        create_test_attachment(
            user.account,
            file_id='existing_file_123',
            task=task,
        )

        task.description = (
            'File: [f](https://example.com/existing_file_123)'
        )
        task.save()

        # act
        with override_settings(
                FILES_BASE_URL=_FILE_SERVICE_URL,
                FILE_SERVICE_HOST_PATH=_FILE_SERVICE_HOST_PATH,
        ):
            new_file_ids = refresh_attachments(source=task, user=user)

        # assert
        assert new_file_ids == []
        assert Attachment.objects.filter(
            file_id='existing_file_123',
            task=task,
        ).exists()

    def test_refresh_attachments__add_and_remove__ok(self):
        # arrange
        user = create_test_admin()
        workflow = create_test_workflow(user=user, tasks_count=1)
        task = workflow.tasks.first()

        create_test_attachment(
            user.account,
            file_id='old_file_remove',
            task=task,
        )

        task.description = (
            'New file: [f](https://example.com/new_file_add_123)'
        )
        task.save()

        # act
        with override_settings(
                FILES_BASE_URL=_FILE_SERVICE_URL,
                FILE_SERVICE_HOST_PATH=_FILE_SERVICE_HOST_PATH,
        ):
            new_file_ids = refresh_attachments(source=task, user=user)

        # assert
        assert 'new_file_add_123' in new_file_ids
        assert not Attachment.objects.filter(
            file_id='old_file_remove',
        ).exists()
        assert Attachment.objects.filter(
            file_id='new_file_add_123',
            task=task,
        ).exists()

    def test_refresh_attachments__unsupported_source__empty(self):
        # arrange
        user = create_test_admin()
        unsupported_source = user.account

        # act
        new_file_ids = refresh_attachments(
            source=unsupported_source,
            user=user,
        )

        # assert
        assert new_file_ids == []

    def test_refresh_attachments__multiple_files__ok(self):
        # arrange
        user = create_test_admin()
        workflow = create_test_workflow(user=user, tasks_count=1)
        task = workflow.tasks.first()

        task.description = (
            'Files: [a](https://example.com/file1_multi_123) '
            '[b](https://example.com/file2_multi_456)'
        )
        task.save()

        # act
        with override_settings(
                FILES_BASE_URL=_FILE_SERVICE_URL,
                FILE_SERVICE_HOST_PATH=_FILE_SERVICE_HOST_PATH,
        ):
            new_file_ids = refresh_attachments(source=task, user=user)

        # assert
        assert len(new_file_ids) == 2
        assert 'file1_multi_123' in new_file_ids
        assert 'file2_multi_456' in new_file_ids

    def test_refresh_attachments__workflow_kickoff_description__creates_ok(
            self,
    ):
        # arrange
        user = create_test_admin()
        workflow = create_test_workflow(user=user, tasks_count=1)
        workflow.description = ''
        workflow.save()
        kickoff = workflow.kickoff_instance
        kickoff.clear_description = (
            'Kickoff: [doc](https://example.com/kickoff_refresh_111)'
        )
        kickoff.save()

        # act
        with override_settings(
                FILES_BASE_URL=_FILE_SERVICE_URL,
                FILE_SERVICE_HOST_PATH=_FILE_SERVICE_HOST_PATH,
        ):
            new_file_ids = refresh_attachments(source=workflow, user=user)

        # assert
        assert 'kickoff_refresh_111' in new_file_ids
        assert Attachment.objects.filter(
            file_id='kickoff_refresh_111',
            workflow=workflow,
        ).exists()

    def test_refresh_attachments__template_kickoff_field_description__ok(
            self,
    ):
        # arrange
        user = create_test_admin()
        template = create_test_template(user, is_active=True, tasks_count=1)
        template.description = ''
        template.save()
        kickoff = template.kickoff_instance
        FieldTemplate.objects.create(
            name='Kickoff field',
            description=(
                'File in field: [x](https://example.com/kickoff_tpl_222)'
            ),
            type=FieldType.STRING,
            kickoff=kickoff,
            template=template,
            order=0,
            api_name='kickoff-field-1',
            account=user.account,
        )

        # act
        with override_settings(
                FILES_BASE_URL=_FILE_SERVICE_URL,
                FILE_SERVICE_HOST_PATH=_FILE_SERVICE_HOST_PATH,
        ):
            new_file_ids = refresh_attachments(source=template, user=user)

        # assert
        assert 'kickoff_tpl_222' in new_file_ids
        assert Attachment.objects.filter(
            file_id='kickoff_tpl_222',
            template=template,
        ).exists()


class TestGetAttachmentDescriptionFields:

    def test_get_attachment_description_fields__task__ok(self):
        # arrange
        user = create_test_admin()
        workflow = create_test_workflow(user=user, tasks_count=1)
        task = workflow.tasks.first()

        # act
        result = get_attachment_description_fields(task)

        # assert
        assert result == ['description']

    def test_get_attachment_description_fields__workflow__ok(self):
        # arrange
        user = create_test_admin()
        workflow = create_test_workflow(user=user, tasks_count=1)

        # act
        result = get_attachment_description_fields(workflow)

        # assert
        assert result == ['description']

    def test_get_attachment_description_fields__unsupported__empty(self):
        # arrange
        user = create_test_admin()

        # act
        result = get_attachment_description_fields(user.account)

        # assert
        assert result == []


class TestExtractAllFileIdsFromSource:

    def test_extract_all_file_ids__task__ok(self):
        # arrange
        user = create_test_admin()
        workflow = create_test_workflow(user=user, tasks_count=1)
        task = workflow.tasks.first()
        task.description = (
            'File: [f](https://example.com/extract_all_123)'
        )
        task.save()

        # act
        with override_settings(
                FILES_BASE_URL=_FILE_SERVICE_URL,
                FILE_SERVICE_HOST_PATH=_FILE_SERVICE_HOST_PATH,
        ):
            result = extract_all_file_ids_from_source(task)

        # assert
        assert 'extract_all_123' in result

    def test_extract_all_file_ids__workflow__ok(self):
        # arrange
        user = create_test_admin()
        workflow = create_test_workflow(user=user, tasks_count=1)
        workflow.description = (
            'File: [f](https://example.com/workflow_extract_456)'
        )
        workflow.save()

        # act
        with override_settings(
                FILES_BASE_URL=_FILE_SERVICE_URL,
                FILE_SERVICE_HOST_PATH=_FILE_SERVICE_HOST_PATH,
        ):
            result = extract_all_file_ids_from_source(workflow)

        # assert
        assert 'workflow_extract_456' in result

    def test_extract_all_file_ids__no_files__empty(self):
        # arrange
        user = create_test_admin()
        workflow = create_test_workflow(user=user, tasks_count=1)
        task = workflow.tasks.first()
        task.description = 'No files here'
        task.save()

        # act
        with override_settings(
                FILES_BASE_URL=_FILE_SERVICE_URL,
                FILE_SERVICE_HOST_PATH=_FILE_SERVICE_HOST_PATH,
        ):
            result = extract_all_file_ids_from_source(task)

        # assert
        assert result == []

    def test_extract_all_file_ids__unsupported__empty(self):
        # arrange
        user = create_test_admin()

        # act
        with override_settings(
                FILES_BASE_URL=_FILE_SERVICE_URL,
                FILE_SERVICE_HOST_PATH=_FILE_SERVICE_HOST_PATH,
        ):
            result = extract_all_file_ids_from_source(user.account)

        # assert
        assert result == []

    def test_extract_all_file_ids__duplicates_removed__ok(self):
        # arrange
        user = create_test_admin()
        workflow = create_test_workflow(user=user, tasks_count=1)
        task = workflow.tasks.first()
        task.description = (
            '[a](https://example.com/duplicate_789) '
            '[b](https://example.com/duplicate_789)'
        )
        task.save()

        # act
        with override_settings(
                FILES_BASE_URL=_FILE_SERVICE_URL,
                FILE_SERVICE_HOST_PATH=_FILE_SERVICE_HOST_PATH,
        ):
            result = extract_all_file_ids_from_source(task)

        # assert
        assert result.count('duplicate_789') == 1

    def test_extract_all_file_ids__empty_description__empty(self):
        # arrange
        user = create_test_admin()
        workflow = create_test_workflow(user=user, tasks_count=1)
        task = workflow.tasks.first()
        task.description = ''
        task.save()

        # act
        with override_settings(
                FILES_BASE_URL=_FILE_SERVICE_URL,
                FILE_SERVICE_HOST_PATH=_FILE_SERVICE_HOST_PATH,
        ):
            result = extract_all_file_ids_from_source(task)

        # assert
        assert result == []

    def test_extract_all_file_ids__workflow_kickoff_description__ok(self):
        # arrange
        user = create_test_admin()
        workflow = create_test_workflow(user=user, tasks_count=1)
        workflow.description = ''
        workflow.save()
        kickoff = workflow.kickoff_instance
        kickoff.clear_description = (
            'Kickoff file: [f](https://example.com/kickoff_wf_999)'
        )
        kickoff.save()

        # act
        with override_settings(
                FILES_BASE_URL=_FILE_SERVICE_URL,
                FILE_SERVICE_HOST_PATH=_FILE_SERVICE_HOST_PATH,
        ):
            result = extract_all_file_ids_from_source(workflow)

        # assert
        assert 'kickoff_wf_999' in result

    def test_extract_all_file_ids__template_kickoff_field_description__ok(
            self,
    ):
        # arrange
        user = create_test_admin()
        template = create_test_template(user, is_active=True, tasks_count=1)
        kickoff = template.kickoff_instance
        FieldTemplate.objects.create(
            name='Kickoff field',
            description=(
                'Field file: [x](https://example.com/kickoff_tpl_777)'
            ),
            type=FieldType.STRING,
            kickoff=kickoff,
            template=template,
            order=0,
            api_name='kickoff-field-1',
            account=user.account,
        )

        # act
        with override_settings(
                FILES_BASE_URL=_FILE_SERVICE_URL,
                FILE_SERVICE_HOST_PATH=_FILE_SERVICE_HOST_PATH,
        ):
            result = extract_all_file_ids_from_source(template)

        # assert
        assert 'kickoff_tpl_777' in result


class TestGetFileServiceFileUrl:
    """P6: get_file_service_file_url must URL-encode file_id."""

    def test_cyrillic_file_id__url_encoded(self):
        """Cyrillic chars in file_id must be percent-encoded."""
        # act
        with override_settings(FILE_SERVICE_URL='https://files.app'):
            result = get_file_service_file_url('NiihssB_Рисунок.odg')

        # assert
        assert result is not None
        assert 'Рисунок' not in result
        assert '%D0%A0%D0%B8%D1%81' in result

    def test_spaces_in_file_id__url_encoded(self):
        """Spaces in file_id must be percent-encoded."""
        # act
        with override_settings(FILE_SERVICE_URL='https://files.app'):
            result = get_file_service_file_url(
                'Zfcsx_Screencast 2023-08-16.webm',
            )

        # assert
        assert result is not None
        assert ' ' not in result
        assert '%20' in result

    def test_uuid_file_id__not_encoded(self):
        """UUID file_id (ASCII) must stay readable."""
        # act
        with override_settings(FILE_SERVICE_URL='https://files.app'):
            result = get_file_service_file_url(
                '550e8400-e29b-41d4-a716-446655440000',
            )

        # assert
        assert result == (
            'https://files.app/'
            '550e8400-e29b-41d4-a716-446655440000'
        )

    def test_legacy_ascii_file_id__not_encoded(self):
        """Legacy ASCII file_id must stay readable."""
        # act
        with override_settings(FILE_SERVICE_URL='https://files.app'):
            result = get_file_service_file_url('VumcsgTMm_pic.png')

        # assert
        assert result == 'https://files.app/VumcsgTMm_pic.png'

    def test_empty_file_id__returns_none(self):
        # act
        with override_settings(FILE_SERVICE_URL='https://files.app'):
            result = get_file_service_file_url('')

        # assert
        assert result is None

    def test_no_service_url__returns_none(self):
        # act
        with override_settings(FILE_SERVICE_URL=None):
            result = get_file_service_file_url('some-file-id')

        # assert
        assert result is None
