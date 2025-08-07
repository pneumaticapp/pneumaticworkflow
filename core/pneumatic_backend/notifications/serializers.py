from rest_framework.serializers import ModelSerializer
from pneumatic_backend.notifications.models import Device, UserNotifications


class DeviceSerializer(ModelSerializer):

    class Meta:
        model = Device
        fields = (
            'user',
            'token',
            'description',
            'is_app',
        )

    def create(self, validated_data):
        instance, _ = self.Meta.model.objects.update_or_create(
            token=validated_data['token'],
            defaults={
                'user': validated_data['user'],
                'description': validated_data['description'],
                'is_app': validated_data['is_app']
            },
        )
        UserNotifications.objects.get_or_create(
            user=validated_data['user']
        )
        return instance
