from rest_framework import serializers

from pneumatic_backend.processes.models import Delay
from pneumatic_backend.generics.fields import TimeStampField


class DelayInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Delay
        fields = (
            'id',
            'duration',
            'start_date',
            'start_date_tsp',
            'end_date',
            'end_date_tsp',
            'estimated_end_date',
            'estimated_end_date_tsp',
        )

    start_date_tsp = TimeStampField(source='start_date')
    end_date_tsp = TimeStampField(source='end_date')
    estimated_end_date_tsp = TimeStampField(source='estimated_end_date')
