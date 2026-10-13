from rest_framework import serializers

from src.processes.serializers.templates.kickoff import KickoffListSerializer


class KickoffResponseSerializer(serializers.Serializer):
    template_id = serializers.IntegerField(source='pk')
    name = serializers.CharField()
    kickoff = KickoffListSerializer(source='kickoff_instance')
