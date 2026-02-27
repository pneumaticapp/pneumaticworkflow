import pytest
from io import StringIO
from django.core.management import call_command
from django.contrib.auth import get_user_model

from src.processes.models.templates.owner import TemplateOwner
from src.processes.models.templates.starter import TemplateStarter
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_group,
    create_test_template,
    create_test_user,
)

UserModel = get_user_model()
pytestmark = pytest.mark.django_db


class TestMigrateTemplateOwnersToStarters:

    def test_migrate__non_admin_user_owner__converted_to_starter(self):
        # arrange
        account = create_test_account()
        admin_user = create_test_user(
            account=account,
            email='admin@test.com',
            is_admin=True,
        )
        non_admin_user = create_test_user(
            account=account,
            email='nonadmin@test.com',
            is_admin=False,
        )
        template = create_test_template(admin_user)

        # Add non-admin as owner
        TemplateOwner.objects.create(
            template=template,
            type='user',
            user=non_admin_user,
            account=account,
        )

        out = StringIO()

        # act
        call_command(
            'migrate_template_owners_to_starters',
            stdout=out,
        )

        # assert
        # Non-admin owner should be converted to starter
        assert not TemplateOwner.objects.filter(
            template=template,
            user=non_admin_user,
            is_deleted=False,
        ).exists()

        assert TemplateStarter.objects.filter(
            template=template,
            user=non_admin_user,
            is_deleted=False,
        ).exists()

        # Admin owner should remain
        assert TemplateOwner.objects.filter(
            template=template,
            user=admin_user,
            is_deleted=False,
        ).exists()

    def test_migrate__admin_user_owner__remains_owner(self):
        # arrange
        account = create_test_account()
        admin_user = create_test_user(
            account=account,
            email='admin@test.com',
            is_admin=True,
        )
        template = create_test_template(admin_user)

        out = StringIO()

        # act
        call_command(
            'migrate_template_owners_to_starters',
            stdout=out,
        )

        # assert
        # Admin owner should remain as owner
        assert TemplateOwner.objects.filter(
            template=template,
            user=admin_user,
            is_deleted=False,
        ).exists()

        # Should not be converted to starter
        assert not TemplateStarter.objects.filter(
            template=template,
            user=admin_user,
        ).exists()

    def test_migrate__group_owner_no_admins__converted_to_starter(self):
        # arrange
        account = create_test_account()
        admin_user = create_test_user(
            account=account,
            email='admin@test.com',
            is_admin=True,
        )
        non_admin_user1 = create_test_user(
            account=account,
            email='user1@test.com',
            is_admin=False,
        )
        non_admin_user2 = create_test_user(
            account=account,
            email='user2@test.com',
            is_admin=False,
        )
        template = create_test_template(admin_user)
        group = create_test_group(
            account=account,
            name='Non-Admin Group',
        )
        group.users.add(non_admin_user1, non_admin_user2)

        # Add group as owner
        TemplateOwner.objects.create(
            template=template,
            type='group',
            group=group,
            account=account,
        )

        out = StringIO()

        # act
        call_command(
            'migrate_template_owners_to_starters',
            stdout=out,
        )

        # assert
        # Group owner should be converted to starter
        assert not TemplateOwner.objects.filter(
            template=template,
            group=group,
            is_deleted=False,
        ).exists()

        assert TemplateStarter.objects.filter(
            template=template,
            group=group,
            is_deleted=False,
        ).exists()

    def test_migrate__group_owner_with_admin__remains_owner(self):
        # arrange
        account = create_test_account()
        admin_user = create_test_user(
            account=account,
            email='admin@test.com',
            is_admin=True,
        )
        non_admin_user = create_test_user(
            account=account,
            email='nonadmin@test.com',
            is_admin=False,
        )
        template = create_test_template(admin_user)
        group = create_test_group(
            account=account,
            name='Mixed Group',
        )
        group.users.add(admin_user, non_admin_user)

        # Add group as owner
        TemplateOwner.objects.create(
            template=template,
            type='group',
            group=group,
            account=account,
        )

        out = StringIO()

        # act
        call_command(
            'migrate_template_owners_to_starters',
            stdout=out,
        )

        # assert
        # Group with admin should remain as owner
        assert TemplateOwner.objects.filter(
            template=template,
            group=group,
            is_deleted=False,
        ).exists()

        # Should not be converted to starter
        assert not TemplateStarter.objects.filter(
            template=template,
            group=group,
        ).exists()

    def test_migrate__dry_run__no_changes(self):
        # arrange
        account = create_test_account()
        admin_user = create_test_user(
            account=account,
            email='admin@test.com',
            is_admin=True,
        )
        non_admin_user = create_test_user(
            account=account,
            email='nonadmin@test.com',
            is_admin=False,
        )
        template = create_test_template(admin_user)

        # Add non-admin as owner
        TemplateOwner.objects.create(
            template=template,
            type='user',
            user=non_admin_user,
            account=account,
        )

        out = StringIO()

        # act
        call_command(
            'migrate_template_owners_to_starters',
            '--dry-run',
            stdout=out,
        )

        # assert
        # Nothing should change in dry-run mode
        assert TemplateOwner.objects.filter(
            template=template,
            user=non_admin_user,
            is_deleted=False,
        ).exists()

        assert not TemplateStarter.objects.filter(
            template=template,
            user=non_admin_user,
        ).exists()

        # Check output mentions dry run
        output = out.getvalue()
        assert 'DRY RUN' in output

    def test_migrate__existing_starter__skipped(self):
        # arrange
        account = create_test_account()
        admin_user = create_test_user(
            account=account,
            email='admin@test.com',
            is_admin=True,
        )
        non_admin_user = create_test_user(
            account=account,
            email='nonadmin@test.com',
            is_admin=False,
        )
        template = create_test_template(admin_user)

        # Add non-admin as owner
        TemplateOwner.objects.create(
            template=template,
            type='user',
            user=non_admin_user,
            account=account,
        )

        # Create starter beforehand
        TemplateStarter.objects.create(
            template=template,
            type='user',
            user=non_admin_user,
            account=account,
        )

        out = StringIO()

        # act
        call_command(
            'migrate_template_owners_to_starters',
            stdout=out,
        )

        # assert
        # Owner should remain because starter already exists
        assert TemplateOwner.objects.filter(
            template=template,
            user=non_admin_user,
            is_deleted=False,
        ).exists()

        # Only one starter should exist
        assert TemplateStarter.objects.filter(
            template=template,
            user=non_admin_user,
            is_deleted=False,
        ).count() == 1

        # Check output mentions skipping
        output = out.getvalue()
        assert 'Skipping' in output
