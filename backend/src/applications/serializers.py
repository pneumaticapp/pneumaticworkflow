from rest_framework import serializers

from src.applications.models import Integration


class IntegrationsListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Integration
        fields = (
            'id',
            'name',
            'logo',
            'short_description',
        )


class IntegrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Integration
        fields = (
            'id',
            'name',
            'logo',
            'long_description',
            'button_text',
            'url',
        )
