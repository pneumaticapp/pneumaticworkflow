from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from src.processes.models.templates.owner import TemplateOwner
from src.processes.models.templates.starter import TemplateStarter

UserModel = get_user_model()


class Command(BaseCommand):

    help = (
        'Migrate non-admin template owners to template starters. '
        'This command converts all template owners who are not admins '
        'into template starters, preserving admin-only ownership.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be migrated without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)

        if dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN MODE - No changes will be made'),
            )

        # Get all template owners that are not admins
        non_admin_owners = TemplateOwner.objects.filter(
            is_deleted=False,
            type='user',
            user__isnull=False,
            user__is_admin=False,
        ).select_related('user', 'template', 'account')

        total_count = non_admin_owners.count()
        self.stdout.write(
            f'Found {total_count} non-admin template owners to migrate',
        )

        if total_count == 0:
            self.stdout.write(
                self.style.SUCCESS('No non-admin owners found. '
                                   'Nothing to migrate.'),
            )
            return

        migrated_count = 0
        skipped_count = 0
        error_count = 0

        with transaction.atomic():
            for owner in non_admin_owners:
                try:
                    # Check if starter already exists
                    existing_starter = TemplateStarter.objects.filter(
                        template=owner.template,
                        type=owner.type,
                        user=owner.user,
                        is_deleted=False,
                    ).first()

                    if existing_starter:
                        self.stdout.write(
                            self.style.WARNING(
                                f'Skipping: Starter already exists for '
                                f'user {owner.user.email} '
                                f'in template {owner.template.name}',
                            ),
                        )
                        skipped_count += 1
                        continue

                    if not dry_run:
                        # Create template starter
                        TemplateStarter.objects.create(
                            template=owner.template,
                            type=owner.type,
                            user=owner.user,
                            account=owner.account,
                        )

                        # Delete the owner
                        owner.delete()

                    self.stdout.write(
                        f'Migrated: {owner.user.email} -> '
                        f'Template: {owner.template.name}',
                    )
                    migrated_count += 1

                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(
                            f'Error migrating owner {owner.id}: {e!s}',
                        ),
                    )
                    error_count += 1
                    if not dry_run:
                        raise

            if dry_run:
                self.stdout.write(
                    self.style.WARNING(
                        'DRY RUN COMPLETE - No changes were made',
                    ),
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Migration complete! '
                        f'Migrated: {migrated_count}, '
                        f'Skipped: {skipped_count}, '
                        f'Errors: {error_count}',
                    ),
                )

        # Also handle group-based owners
        non_admin_group_owners = TemplateOwner.objects.filter(
            is_deleted=False,
            type='group',
            group__isnull=False,
        ).select_related('group', 'template', 'account')

        group_count = non_admin_group_owners.count()
        if group_count > 0:
            self.stdout.write(
                f'\nFound {group_count} group-based template owners '
                f'to migrate',
            )

            group_migrated = 0
            group_skipped = 0

            with transaction.atomic():
                for owner in non_admin_group_owners:
                    try:
                        # Check if all users in group are non-admins
                        admin_users = owner.group.users.filter(
                            is_admin=True,
                        ).exists()

                        if admin_users:
                            self.stdout.write(
                                self.style.WARNING(
                                    f'Skipping group {owner.group.name}: '
                                    f'Contains admin users',
                                ),
                            )
                            group_skipped += 1
                            continue

                        # Check if starter already exists
                        existing_starter = TemplateStarter.objects.filter(
                            template=owner.template,
                            type=owner.type,
                            group=owner.group,
                            is_deleted=False,
                        ).first()

                        if existing_starter:
                            self.stdout.write(
                                self.style.WARNING(
                                    f'Skipping: Starter already exists for '
                                    f'group {owner.group.name} '
                                    f'in template {owner.template.name}',
                                ),
                            )
                            group_skipped += 1
                            continue

                        if not dry_run:
                            # Create template starter
                            TemplateStarter.objects.create(
                                template=owner.template,
                                type=owner.type,
                                group=owner.group,
                                account=owner.account,
                            )

                            # Delete the owner
                            owner.delete()

                        self.stdout.write(
                            f'Migrated group: {owner.group.name} -> '
                            f'Template: {owner.template.name}',
                        )
                        group_migrated += 1

                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(
                                f'Error migrating group owner {owner.id}: '
                                f'{e!s}',
                            ),
                        )
                        if not dry_run:
                            raise

                if dry_run:
                    self.stdout.write(
                        self.style.WARNING(
                            'DRY RUN COMPLETE - No changes were made',
                        ),
                    )
                else:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Group migration complete! '
                            f'Migrated: {group_migrated}, '
                            f'Skipped: {group_skipped}',
                        ),
                    )
