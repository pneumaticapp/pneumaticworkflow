from typing import List

from django.contrib.auth import get_user_model

UserModel = get_user_model()


class VacationSubstituteMixin:
    """Shared method for substitute_user_ids serialization."""

    def get_substitute_user_ids(
        self, instance: UserModel,
    ) -> List[int]:
        if instance.vacation_substitute_group_id:
            return list(
                instance.vacation_substitute_group.users
                .values_list('id', flat=True),
            )
        return []
