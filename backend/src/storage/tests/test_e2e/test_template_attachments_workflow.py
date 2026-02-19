"""
E2E tests for template attachments.
Tests full workflow without mocks - real database operations.
"""
import pytest

from src.processes.enums import FieldType, OwnerType
from src.processes.models.templates.fields import FieldTemplate
from src.processes.models.templates.owner import TemplateOwner
from src.processes.tests.fixtures import (
    create_test_admin,
    create_test_group,
    create_test_template,
    create_test_user,
)
from src.storage.enums import AccessType, SourceType
from src.storage.models import Attachment
from src.storage.services.attachments import AttachmentService
from src.storage.utils import refresh_attachments

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def file_domain_template_e2e(settings):
    settings.FILE_SERVICE_URL = 'https://files.example.com'
    settings.FILE_DOMAIN = 'files.example.com'


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
            account=template.account,
            user=owner,
            type=OwnerType.USER,
        )
        template.description = (
            'Template file: '
            '[file](https://files.example.com/template_e2e_123)'
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

    def test_template_kickoff_field_description_with_attachment__e2e__ok(
            self,
    ):
        """
        Scenario: File link only in kickoff field description
        Expected: Attachment created and linked to template
        """
        # arrange
        owner = create_test_admin()
        template = create_test_template(owner, is_active=True)
        template.description = ''
        template.save()
        kickoff = template.kickoff_instance
        FieldTemplate.objects.create(
            name='Kickoff field',
            description=(
                'Field file: '
                '[x](https://files.example.com/kickoff_tpl_e2e_789)'
            ),
            type=FieldType.STRING,
            kickoff=kickoff,
            template=template,
            order=0,
            api_name='kickoff-field-1',
        )

        # act
        new_file_ids = refresh_attachments(source=template, user=owner)

        # assert
        assert 'kickoff_tpl_e2e_789' in new_file_ids
        attachment = Attachment.objects.get(
            file_id='kickoff_tpl_e2e_789',
        )
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
            account=template.account,
            user=owner1,
            type=OwnerType.USER,
        )
        TemplateOwner.objects.create(
            template=template,
            account=template.account,
            user=owner2,
            type=OwnerType.USER,
        )
        template.description = (
            'File: [f](https://files.example.com/tmpl_owners_e2e)'
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
            account=template.account,
            user=owner,
            type=OwnerType.USER,
        )
        template.description = 'Initial template description'
        template.save()
        refresh_attachments(source=template, user=owner)

        # act
        template.description = (
            'Updated: [f](https://files.example.com/tmpl_new_e2e)'
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
            account=template.account,
            user=owner,
            type=OwnerType.USER,
        )
        template.description = (
            'File: [f](https://files.example.com/tmpl_remove_e2e)'
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
        owner2 = create_test_user(
            account=owner1.account,
            is_admin=True,
            email='owner2_tmpl@test.pneumatic.app',
        )
        template = create_test_template(owner1, is_active=True)
        TemplateOwner.objects.create(
            template=template,
            account=template.account,
            user=owner1,
            type=OwnerType.USER,
        )
        template.description = (
            'File: [f](https://files.example.com/tmpl_owner_e2e)'
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
            account=template.account,
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
            account=template.account,
            user=owner,
            type=OwnerType.USER,
        )
        template.description = (
            'Files: '
            '[a](https://files.example.com/tmpl_multi_1_e2e) '
            '[b](https://files.example.com/tmpl_multi_2_e2e)'
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
            account=template.account,
            user=owner,
            type=OwnerType.USER,
        )
        template.description = (
            'File: [f](https://files.example.com/tmpl_no_access_e2e)'
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
            account=template.account,
            user=owner,
            type=OwnerType.USER,
        )
        template.description = (
            'File: [f](https://files.example.com/tmpl_old_e2e)'
        )
        template.save()
        refresh_attachments(source=template, user=owner)
        assert Attachment.objects.filter(
            file_id='tmpl_old_e2e',
        ).exists()

        # act
        template.description = (
            'File: [f](https://files.example.com/tmpl_new_replace_e2e)'
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
        owner2 = create_test_user(
            account=owner1.account,
            is_admin=True,
            email='owner2_remove@test.pneumatic.app',
        )
        template = create_test_template(owner1, is_active=True)
        # owner1 is already created as template owner by create_test_template
        owner2_obj = TemplateOwner.objects.create(
            template=template,
            account=template.account,
            user=owner2,
            type=OwnerType.USER,
        )
        template.description = (
            'File: [f](https://files.example.com/tmpl_remove_owner_e2e)'
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

    def test_template_group_owner__all_group_users_access__ok(self):
        """
        Scenario: Template with group owner
        Expected: All users in owner group have access to attachments
        """
        # arrange
        owner = create_test_admin()
        group_user1 = create_test_user(
            account=owner.account,
            email='group_owner1@test.pneumatic.app',
        )
        group_user2 = create_test_user(
            account=owner.account,
            email='group_owner2@test.pneumatic.app',
        )
        group = create_test_group(
            owner.account,
            name='Template Owner Group E2E',
            users=[group_user1, group_user2],
        )
        template = create_test_template(owner, is_active=True)
        TemplateOwner.objects.create(
            template=template,
            account=template.account,
            group=group,
            type=OwnerType.GROUP,
        )
        template.description = (
            'File: [f](https://files.example.com/tmpl_group_owner_e2e)'
        )
        template.save()

        # act
        refresh_attachments(source=template, user=owner)

        # assert
        attachment = Attachment.objects.get(
            file_id='tmpl_group_owner_e2e',
        )
        svc1 = AttachmentService(user=group_user1)
        svc2 = AttachmentService(user=group_user2)
        assert svc1.check_user_permission(
            user_id=group_user1.id,
            account_id=group_user1.account_id,
            file_id=attachment.file_id,
        )
        assert svc2.check_user_permission(
            user_id=group_user2.id,
            account_id=group_user2.account_id,
            file_id=attachment.file_id,
        )

    def test_template_mixed_owners__all_have_access__ok(self):
        """
        Scenario: Template with both individual and group owners
        Expected: Both individual and group users have access
        """
        # arrange
        owner = create_test_admin()
        individual_owner = create_test_user(
            account=owner.account,
            is_admin=True,
            email='individual_owner@test.pneumatic.app',
        )
        group_user1 = create_test_user(
            account=owner.account,
            email='mixed_group1@test.pneumatic.app',
        )
        group_user2 = create_test_user(
            account=owner.account,
            email='mixed_group2@test.pneumatic.app',
        )
        group = create_test_group(
            owner.account,
            name='Mixed Owner Group E2E',
            users=[group_user1, group_user2],
        )
        template = create_test_template(owner, is_active=True)
        TemplateOwner.objects.create(
            template=template,
            account=template.account,
            user=individual_owner,
            type=OwnerType.USER,
        )
        TemplateOwner.objects.create(
            template=template,
            account=template.account,
            group=group,
            type=OwnerType.GROUP,
        )
        template.description = (
            'File: [f](https://files.example.com/tmpl_mixed_owners_e2e)'
        )
        template.save()

        # act
        refresh_attachments(source=template, user=owner)

        # assert
        attachment = Attachment.objects.get(
            file_id='tmpl_mixed_owners_e2e',
        )
        svc_individual = AttachmentService(user=individual_owner)
        svc_group1 = AttachmentService(user=group_user1)
        svc_group2 = AttachmentService(user=group_user2)
        assert svc_individual.check_user_permission(
            user_id=individual_owner.id,
            account_id=individual_owner.account_id,
            file_id=attachment.file_id,
        )
        assert svc_group1.check_user_permission(
            user_id=group_user1.id,
            account_id=group_user1.account_id,
            file_id=attachment.file_id,
        )
        assert svc_group2.check_user_permission(
            user_id=group_user2.id,
            account_id=group_user2.account_id,
            file_id=attachment.file_id,
        )
