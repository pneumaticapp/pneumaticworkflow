from typing import List

from django.contrib.auth import get_user_model
from rest_framework import serializers

from src.accounts.models import UserVacation

UserModel = get_user_model()


class VacationSerializer(serializers.ModelSerializer):
    """Nested serializer for the UserVacation object."""

    substitute_user_ids = serializers.SerializerMethodField()

    class Meta:
        model = UserVacation
        fields = (
            'start_date',
            'end_date',
            'absence_status',
            'substitute_user_ids',
        )

    def get_substitute_user_ids(self, instance) -> List[int]:
        if instance.substitute_group_id:
            return list(
                instance.substitute_group.users
                .values_list('id', flat=True),
            )
        return []
