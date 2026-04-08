from typing import List

from django.contrib.auth import get_user_model

UserModel = get_user_model()


class VacationSubstituteMixin:
    """Shared method for substitute_user_ids serialization."""

    def get_substitute_user_ids(
        self, instance: UserModel,
    ) -> List[int]:
        schedule = getattr(instance, 'vacation_schedule', None)
        if schedule and schedule.substitute_group_id:
            return list(
                schedule.substitute_group.users
                .values_list('id', flat=True),
            )
        return []
