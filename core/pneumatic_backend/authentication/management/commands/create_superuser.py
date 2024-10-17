from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from pneumatic_backend.accounts.services import (
    AccountService,
    UserService,
)


class Command(BaseCommand):

    help = "Create first superuser"

    def add_arguments(self, parser):
        parser.add_argument("email", type=str)

    def handle(self, *args, **options):
        email = options.get("email")
        if not email:
            raise CommandError('Parameter email is required')
        account_service = AccountService()
        user_service = UserService()
        with transaction.atomic():
            account = account_service.create(
                billing_sync=False,
            )
            account_owner = user_service.create(
                account=account,
                email=email,
                first_name='Admin',
                raw_password='password',
                is_account_owner=True,
            )
            account_owner.is_superuser = True
            account_owner.is_staff = True
            account_owner.save()
