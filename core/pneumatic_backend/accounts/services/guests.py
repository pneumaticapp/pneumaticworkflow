from django.contrib.auth import get_user_model
from pneumatic_backend.accounts.enums import (
    UserType,
    UserStatus
)


UserModel = get_user_model()


class GuestService:

    @classmethod
    def create(
        cls,
        email: str,
        account_id: int
    ) -> UserModel:
        owner = UserModel.objects.get(
            account_id=account_id,
            is_account_owner=True
        )
        user = UserModel(
            email=email,
            first_name='',
            last_name='',
            account_id=account_id,
            type=UserType.GUEST,
            status=UserStatus.ACTIVE,
            is_admin=False,
            is_account_owner=False,
            notify_about_tasks=False,
            is_digest_subscriber=False,
            is_tasks_digest_subscriber=False,
            is_special_offers_subscriber=False,
            is_newsletters_subscriber=False,
            is_new_tasks_subscriber=True,
            is_complete_tasks_subscriber=True,
            is_comments_mentions_subscriber=False,
            language=owner.language,
            timezone=owner.timezone,
            date_fmt=owner.date_fmt,
            date_fdw=owner.date_fdw,
        )
        user.set_unusable_password()
        user.save()
        return user

    @classmethod
    def get_or_create(
        cls,
        email: str,
        account_id: int
    ) -> UserModel:

        try:
            return UserModel.guests_objects.get(
                email=email,
                account_id=account_id,
                type=UserType.GUEST,
                status=UserStatus.ACTIVE
            )
        except UserModel.DoesNotExist:
            return cls.create(
                account_id=account_id,
                email=email
            )
