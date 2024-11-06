from rest_framework.serializers import ModelSerializer
from pneumatic_backend.faq.models import (
    FaqItem,
)


class FaqIemSerializer(ModelSerializer):

    class Meta:
        model = FaqItem
        fields = (
            'order',
            'question',
            'answer',
        )
