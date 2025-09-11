from rest_framework.serializers import ModelSerializer
from src.pages.models import (
    Page,
)


class PageSerializer(ModelSerializer):

    class Meta:
        model = Page
        fields = (
            'slug',
            'title',
            'description',
        )
