from rest_framework.serializers import ModelSerializer
from src.navigation.models import (
    Menu,
    MenuItem,
)


class MenuItemSerializer(ModelSerializer):

    class Meta:
        model = MenuItem
        fields = (
            'order',
            'label',
            'link',
        )


class MenuSerializer(ModelSerializer):

    class Meta:
        model = Menu
        fields = (
            'slug',
            'label',
            'link',
            'items',
        )

    items = MenuItemSerializer(many=True)
