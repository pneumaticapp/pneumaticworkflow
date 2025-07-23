from django.core.exceptions import MultipleObjectsReturned
from django.contrib.auth.base_user import BaseUserManager
from pneumatic_backend.accounts.enums import UserStatus
from pneumatic_backend.generics.mixins.managers import NormalizeEmailMixin
from pneumatic_backend.accounts.enums import UserType


class SoftDeleteUserManager(NormalizeEmailMixin, BaseUserManager):

    def get_queryset(self):
        return (
            super().get_queryset()
            .filter(
                is_deleted=False,
                type=UserType.USER
            )
            .exclude(
                status=UserStatus.INACTIVE
            )
        )

    def get_by_natural_key(self, email: str):

        """ Resolves the situation when there are active and invited
            users with the same email at the same time

            The method is used in the django authenticate function
        """

        try:
            return self.get(email=email)
        except MultipleObjectsReturned:
            return self.get(
                status=UserStatus.ACTIVE,
                email=email
            )


class SoftDeleteGuestManager(NormalizeEmailMixin, BaseUserManager):

    def get_queryset(self):
        return (
            super().get_queryset()
            .filter(
                is_deleted=False,
                type=UserType.GUEST
            )
            .exclude(
                status=UserStatus.INACTIVE
            )
        )
