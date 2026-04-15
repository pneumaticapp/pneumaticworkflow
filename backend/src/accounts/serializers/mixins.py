from typing import TYPE_CHECKING, List

from rest_framework import serializers

if TYPE_CHECKING:
    from src.accounts.models import UserVacation


class VacationSerializer(serializers.Serializer):
    """Nested serializer for the UserVacation object."""

    start_date = serializers.DateField(read_only=True)
    end_date = serializers.DateField(read_only=True)
    absence_status = serializers.CharField(read_only=True)
    substitute_user_ids = serializers.SerializerMethodField()

    def get_substitute_user_ids(
        self,
        instance: 'UserVacation',
    ) -> List[int]:
        if instance.substitute_group_id:
            return list(
                instance.substitute_group.users
                .values_list('id', flat=True),
            )
        return []
