from django.contrib.auth import get_user_model
from rest_framework import serializers


UserModel = get_user_model()


class FinishSignUpSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField()

    class Meta:
        model = UserModel
        fields = (
            'phone',
            'company_name'
        )

    def update(self, instance, validated_data):
        instance.account.name = validated_data.get('company_name')
        instance.account.save(update_fields=['name'])

        # вместо пустой строки записываем None
        phone = validated_data.get('phone') or None
        if instance.phone != phone:
            instance.phone = phone
            instance.save(update_fields=['phone'])

        return instance
