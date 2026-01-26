"""
E2E tests for template attachments.
Tests full workflow without mocks - real database operations.
"""
import pytest

from src.processes.enums import OwnerType
from src.processes.models.templates.owner import TemplateOwner
from src.processes.tests.fixtures import (
    create_test_admin,
    create_test_template,
    create_test_user,
)
from src.storage.enums import AccessType, SourceType
from src.storage.models import Attachment
from src.storage.utils import refresh_attachments

pytestmark = pytest.mark.django_db


class TestTemplateAttachmentsE2E:
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
        assert owner.has_perm('access_attachment', attachment)

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
        assert owner1.has_perm('access_attachment', attachment)
        assert owner2.has_perm('access_attachment', attachment)

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
        assert owner1.has_perm('access_attachment', attachment)
        assert not owner2.has_perm('access_attachment', attachment)

        # act
        TemplateOwner.objects.create(
            template=template,
            user=owner2,
            type=OwnerType.USER,
        )
        refresh_attachments(source=template, user=owner1)

        # assert
        attachment.refresh_from_db()
        assert owner2.has_perm('access_attachment', attachment)

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
        for file_id in new_file_ids:
            attachment = Attachment.objects.get(file_id=file_id)
            assert owner.has_perm('access_attachment', attachment)

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
        assert not other_user.has_perm('access_attachment', attachment)

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
        assert owner2.has_perm('access_attachment', attachment)

        # act
        owner2_obj.delete()
        refresh_attachments(source=template, user=owner1)

        # assert
        attachment.refresh_from_db()
        assert not owner2.has_perm('access_attachment', attachment)
        assert owner1.has_perm('access_attachment', attachment)
