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
from src.openapi.permission_docs import ACCESS_AUTH_BASIC
from src.openapi.responses import FORBIDDEN, UNAUTHORIZED
from src.openapi.helpers import LIMIT_OFFSET_LEGACY_NOTE, with_access_text


@extend_schema(
    tags=['FAQ'],
    summary='List active frequently asked questions',
    description=with_access_text(
        'Returns active FAQ items with question, answer and display order. '
        + LIMIT_OFFSET_LEGACY_NOTE,
        ACCESS_AUTH_BASIC,
    ),
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
