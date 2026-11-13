from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin
from rest_framework.permissions import AllowAny
from rest_framework.viewsets import GenericViewSet

from src.generics.mixins.views import CustomViewSetMixin
from src.pages.models import Page
from src.pages.serializers import (
    PageSerializer,
)
from src.openapi.helpers import LIMIT_OFFSET_LEGACY_NOTE
from src.openapi.responses import NOT_FOUND, UNAUTHORIZED


@extend_schema_view(
    list=extend_schema(
        tags=['Pages'],
        summary='List public content pages',
        description=(
            'No session is required. Lists pages marked public. An invalid '
            'supplied bearer token returns 401. '
            + LIMIT_OFFSET_LEGACY_NOTE
        ),
        auth=[],
        responses={200: PageSerializer(many=True), 401: UNAUTHORIZED},
    ),
    retrieve=extend_schema(
        tags=['Pages'],
        summary='Get a public content page by slug',
        description=(
            'No session is required. Returns the title and description for '
            'a public page. Private or unknown slugs return 404. An invalid '
            'supplied bearer token returns 401.'
        ),
        auth=[],
        responses={200: PageSerializer, 401: UNAUTHORIZED, 404: NOT_FOUND},
    ),
)
class PublicPageViewSet(
    CustomViewSetMixin,
    ListModelMixin,
    RetrieveModelMixin,
    GenericViewSet,
):

    lookup_field = 'slug'
    queryset = Page.objects.public()
    permission_classes = (AllowAny,)
    serializer_class = PageSerializer
