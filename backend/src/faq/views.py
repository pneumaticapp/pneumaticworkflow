from drf_spectacular.utils import extend_schema
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
from src.openapi import ACCESS_AUTH_BASIC, FORBIDDEN, UNAUTHORIZED


@extend_schema(
    tags=['FAQ'],
    description=ACCESS_AUTH_BASIC,
    responses={
        200: FaqIemSerializer(many=True),
        401: UNAUTHORIZED,
        403: FORBIDDEN,
    },
)
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
