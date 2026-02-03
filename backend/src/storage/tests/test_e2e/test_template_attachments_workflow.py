"""
E2E tests for template attachments.
Tests full workflow without mocks - real database operations.
"""
import pytest
from django.test import override_settings, TestCase

from src.processes.enums import OwnerType
from src.processes.models.templates.owner import TemplateOwner
from src.processes.tests.fixtures import (
    create_test_admin,
    create_test_template,
    create_test_user,
)
from src.storage.enums import AccessType, SourceType
from src.storage.models import Attachment
from src.storage.services.attachments import AttachmentService
from src.storage.utils import refresh_attachments

pytestmark = pytest.mark.django_db


@override_settings(FILE_DOMAIN='files.example.com')
class TestTemplateAttachmentsE2E(TestCase):
    """
    End-to-end tests for template attachments.
    No mocks - testing real integration.
    """

    def test_create_template_with_attachment__full_workflow__ok(
        self,
    ):
        """
        Scenario: Create template with file in description
        Expected: Attachment created with correct permissions
        """
        # arrange
        owner = create_test_admin()
        template = create_test_template(owner, is_active=True)
        TemplateOwner.objects.create(
            template=template,
            user=owner,
            type=OwnerType.USER,
        )
        template.description = (
            'Template file: '
            'https://files.example.com/files/template_e2e_123'
        )
        template.save()

        # act
        new_file_ids = refresh_attachments(source=template, user=owner)

        # assert
        assert 'template_e2e_123' in new_file_ids
        attachment = Attachment.objects.get(file_id='template_e2e_123')
        assert attachment.template == template
        assert attachment.source_type == SourceType.TEMPLATE
        assert attachment.access_type == AccessType.RESTRICTED
        svc = AttachmentService(user=owner)
        assert svc.check_user_permission(
            user_id=owner.id,
            account_id=owner.account_id,
            file_id=attachment.file_id,
        )

    def test_template_multiple_owners__all_have_access__ok(self):
        """
        Scenario: Template with multiple owners
        Expected: All owners have access to template attachments
        """
        # arrange
        owner1 = create_test_admin()
        owner2 = create_test_user(account=owner1.account, is_admin=True)
        template = create_test_template(owner1, is_active=True)
        TemplateOwner.objects.create(
            template=template,
            user=owner1,
            type=OwnerType.USER,
        )
        TemplateOwner.objects.create(
            template=template,
            user=owner2,
            type=OwnerType.USER,
        )
        template.description = (
            'File: https://files.example.com/files/tmpl_owners_e2e'
        )
        template.save()

        # act
        refresh_attachments(source=template, user=owner1)

        # assert
        attachment = Attachment.objects.get(file_id='tmpl_owners_e2e')
        svc1 = AttachmentService(user=owner1)
        svc2 = AttachmentService(user=owner2)
        assert svc1.check_user_permission(
            user_id=owner1.id,
            account_id=owner1.account_id,
            file_id=attachment.file_id,
        )
        assert svc2.check_user_permission(
            user_id=owner2.id,
            account_id=owner2.account_id,
            file_id=attachment.file_id,
        )

    def test_update_template_description__add_file__ok(self):
        """
        Scenario: Update template description to add new file
        Expected: New attachment created with permissions
        """
        # arrange
        owner = create_test_admin()
        template = create_test_template(owner, is_active=True)
        TemplateOwner.objects.create(
            template=template,
            user=owner,
            type=OwnerType.USER,
        )
        template.description = 'Initial template description'
        template.save()
        refresh_attachments(source=template, user=owner)

        # act
        template.description = (
            'Updated: https://files.example.com/files/tmpl_new_e2e'
        )
        template.save()
        new_file_ids = refresh_attachments(source=template, user=owner)

        # assert
        assert 'tmpl_new_e2e' in new_file_ids
        assert Attachment.objects.filter(
            file_id='tmpl_new_e2e',
            template=template,
        ).exists()

    def test_update_template_description__remove_file__deleted(
        self,
    ):
        """
        Scenario: Remove file link from template description
        Expected: Attachment deleted
        """
        # arrange
        owner = create_test_admin()
        template = create_test_template(owner, is_active=True)
        TemplateOwner.objects.create(
            template=template,
            user=owner,
            type=OwnerType.USER,
        )
        template.description = (
            'File: https://files.example.com/files/tmpl_remove_e2e'
        )
        template.save()
        refresh_attachments(source=template, user=owner)
        assert Attachment.objects.filter(
            file_id='tmpl_remove_e2e',
        ).exists()

        # act
        template.description = 'No files'
        template.save()
        refresh_attachments(source=template, user=owner)

        # assert
        assert not Attachment.objects.filter(
            file_id='tmpl_remove_e2e',
        ).exists()

    def test_add_template_owner__gets_access__ok(self):
        """
        Scenario: Add new owner to template with existing attachment
        Expected: New owner gets access to attachment
        """
        # arrange
        owner1 = create_test_admin()
        owner2 = create_test_user(account=owner1.account, is_admin=True)
        template = create_test_template(owner1, is_active=True)
        TemplateOwner.objects.create(
            template=template,
            user=owner1,
            type=OwnerType.USER,
        )
        template.description = (
            'File: https://files.example.com/files/tmpl_owner_e2e'
        )
        template.save()
        refresh_attachments(source=template, user=owner1)
        attachment = Attachment.objects.get(file_id='tmpl_owner_e2e')
        svc1 = AttachmentService(user=owner1)
        svc2 = AttachmentService(user=owner2)
        assert svc1.check_user_permission(
            user_id=owner1.id,
            account_id=owner1.account_id,
            file_id=attachment.file_id,
        )
        assert not svc2.check_user_permission(
            user_id=owner2.id,
            account_id=owner2.account_id,
            file_id=attachment.file_id,
        )

        # act
        TemplateOwner.objects.create(
            template=template,
            user=owner2,
            type=OwnerType.USER,
        )
        refresh_attachments(source=template, user=owner1)

        # assert
        attachment.refresh_from_db()
        svc2 = AttachmentService(user=owner2)
        assert svc2.check_user_permission(
            user_id=owner2.id,
            account_id=owner2.account_id,
            file_id=attachment.file_id,
        )

    def test_template_multiple_files__all_created__ok(self):
        """
        Scenario: Template description contains multiple file links
        Expected: All attachments created with permissions
        """
        # arrange
        owner = create_test_admin()
        template = create_test_template(owner, is_active=True)
        TemplateOwner.objects.create(
            template=template,
            user=owner,
            type=OwnerType.USER,
        )
        template.description = (
            'Files: '
            'https://files.example.com/files/tmpl_multi_1_e2e and '
            'https://files.example.com/files/tmpl_multi_2_e2e'
        )
        template.save()

        # act
        new_file_ids = refresh_attachments(source=template, user=owner)

        # assert
        assert len(new_file_ids) == 2
        svc = AttachmentService(user=owner)
        for file_id in new_file_ids:
            attachment = Attachment.objects.get(file_id=file_id)
            assert svc.check_user_permission(
                user_id=owner.id,
                account_id=owner.account_id,
                file_id=attachment.file_id,
            )

    def test_non_owner_no_access__ok(self):
        """
        Scenario: User not owning template
        Expected: No access to template attachments
        """
        # arrange
        owner = create_test_admin()
        other_user = create_test_user(account=owner.account)
        template = create_test_template(owner, is_active=True)
        TemplateOwner.objects.create(
            template=template,
            user=owner,
            type=OwnerType.USER,
        )
        template.description = (
            'File: https://files.example.com/files/tmpl_no_access_e2e'
        )
        template.save()

        # act
        refresh_attachments(source=template, user=owner)

        # assert
        attachment = Attachment.objects.get(
            file_id='tmpl_no_access_e2e',
        )
        svc = AttachmentService(user=other_user)
        assert not svc.check_user_permission(
            user_id=other_user.id,
            account_id=other_user.account_id,
            file_id=attachment.file_id,
        )

    def test_replace_file_in_template__old_deleted_new_created__ok(
        self,
    ):
        """
        Scenario: Replace file link in template description
        Expected: Old attachment deleted, new created
        """
        # arrange
        owner = create_test_admin()
        template = create_test_template(owner, is_active=True)
        TemplateOwner.objects.create(
            template=template,
            user=owner,
            type=OwnerType.USER,
        )
        template.description = (
            'File: https://files.example.com/files/tmpl_old_e2e'
        )
        template.save()
        refresh_attachments(source=template, user=owner)
        assert Attachment.objects.filter(
            file_id='tmpl_old_e2e',
        ).exists()

        # act
        template.description = (
            'File: https://files.example.com/files/tmpl_new_replace_e2e'
        )
        template.save()
        refresh_attachments(source=template, user=owner)

        # assert
        assert not Attachment.objects.filter(
            file_id='tmpl_old_e2e',
        ).exists()
        assert Attachment.objects.filter(
            file_id='tmpl_new_replace_e2e',
        ).exists()

    def test_template_owner_removed__loses_access__ok(self):
        """
        Scenario: Remove owner from template
        Expected: Removed owner loses access to attachments
        """
        # arrange
        owner1 = create_test_admin()
        owner2 = create_test_user(account=owner1.account, is_admin=True)
        template = create_test_template(owner1, is_active=True)
        TemplateOwner.objects.create(
            template=template,
            user=owner1,
            type=OwnerType.USER,
        )
        owner2_obj = TemplateOwner.objects.create(
            template=template,
            user=owner2,
            type=OwnerType.USER,
        )
        template.description = (
            'File: https://files.example.com/files/tmpl_remove_owner_e2e'
        )
        template.save()
        refresh_attachments(source=template, user=owner1)
        attachment = Attachment.objects.get(
            file_id='tmpl_remove_owner_e2e',
        )
        svc2 = AttachmentService(user=owner2)
        svc1 = AttachmentService(user=owner1)
        assert svc2.check_user_permission(
            user_id=owner2.id,
            account_id=owner2.account_id,
            file_id=attachment.file_id,
        )

        # act
        owner2_obj.delete()
        refresh_attachments(source=template, user=owner1)

        # assert
        attachment.refresh_from_db()
        assert not svc2.check_user_permission(
            user_id=owner2.id,
            account_id=owner2.account_id,
            file_id=attachment.file_id,
        )
        assert svc1.check_user_permission(
            user_id=owner1.id,
            account_id=owner1.account_id,
            file_id=attachment.file_id,
        )
