from rest_framework.mixins import ListModelMixin
from rest_framework.viewsets import GenericViewSet

from src.accounts.permissions import (
    BillingPlanPermission,
)
from src.faq.models import FaqItem
from src.faq.serializers import (
    FaqIemSerializer,
)
from src.generics.mixins.views import CustomViewSetMixin
from src.generics.permissions import UserIsAuthenticated


class FaqViewSet(
    CustomViewSetMixin,
    ListModelMixin,
    GenericViewSet,
):

    queryset = FaqItem.objects.active()
    permission_classes = (
        UserIsAuthenticated,
        BillingPlanPermission,
    )
    serializer_class = FaqIemSerializer
