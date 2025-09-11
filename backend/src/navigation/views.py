from typing import List
from django.db.models import Prefetch
from rest_framework.viewsets import GenericViewSet
from src.generics.mixins.views import CustomViewSetMixin
from src.navigation.serializers import (
    MenuSerializer
)
from src.navigation.models import Menu, MenuItem
from src.generics.permissions import (
    IsAuthenticated
)
from src.accounts.permissions import (
    BillingPlanPermission,
)


class MenuViewSet(
    CustomViewSetMixin,
    GenericViewSet
):

    lookup_field = 'slug'
    queryset = Menu.objects.all()
    permission_classes = (
        IsAuthenticated,
        BillingPlanPermission,
    )
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
