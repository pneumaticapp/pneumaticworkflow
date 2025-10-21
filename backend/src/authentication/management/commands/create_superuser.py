from django.core.management.base import BaseCommand
from django.db import transaction

from src.accounts.services.account import AccountService
from src.accounts.services.user import UserService
from src.reports.serializers import UserModel


class Command(BaseCommand):

    help = "Create first superuser"

    def add_arguments(self, parser):
        parser.add_argument("email", type=str)
        parser.add_argument("password", type=str)

    def handle(self, *args, **options):
        email = options["email"]
        password = options["password"]

        if UserModel.objects.filter(email=email).exists():
            self.stdout.write(
                self.style.ERROR('User with the given email already exists.'),
            )
            return

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
                raw_password=password,
                is_account_owner=True,
            )
            account_owner.is_superuser = True
            account_owner.is_staff = True
            account_owner.save()
            self.stdout.write(
                self.style.SUCCESS('User successfully created.'),
            )
