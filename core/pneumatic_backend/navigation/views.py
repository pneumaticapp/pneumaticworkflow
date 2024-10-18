from typing import List
from django.db.models import Prefetch
from rest_framework.viewsets import GenericViewSet
from pneumatic_backend.generics.mixins.views import CustomViewSetMixin
from pneumatic_backend.navigation.serializers import (
    MenuSerializer
)
from pneumatic_backend.navigation.models import Menu, MenuItem
from pneumatic_backend.generics.permissions import (
    IsAuthenticated
)


class MenuViewSet(
    CustomViewSetMixin,
    GenericViewSet
):

    lookup_field = 'slug'
    queryset = Menu.objects.all()
    permission_classes = (IsAuthenticated,)
    serializer_class = MenuSerializer

    def prefetch_queryset(
        self,
        queryset,
        extra_fields: List[str] = None
    ):

        return queryset.prefetch_related(
            Prefetch(
                'items',
                queryset=MenuItem.objects.filter(show=True),
             )
        )

    def get_queryset(self):
        return self.prefetch_queryset(self.queryset)

    def retrieve(self, *args, **kwargs):
        instance = self.get_object()
        slz = self.get_serializer(instance=instance)
        return self.response_ok(data=slz.data)
