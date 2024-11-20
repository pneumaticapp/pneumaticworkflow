from rest_framework.viewsets import GenericViewSet
from rest_framework.mixins import ListModelMixin
from pneumatic_backend.generics.mixins.views import CustomViewSetMixin
from pneumatic_backend.generics.permissions import UserIsAuthenticated
from pneumatic_backend.faq.serializers import (
    FaqIemSerializer
)
from pneumatic_backend.accounts.permissions import (
    BillingPlanPermission,
)
from pneumatic_backend.faq.models import FaqItem


class FaqViewSet(
    CustomViewSetMixin,
    ListModelMixin,
    GenericViewSet
):

    queryset = FaqItem.objects.active()
    permission_classes = (
        UserIsAuthenticated,
        BillingPlanPermission,
    )
    serializer_class = FaqIemSerializer
