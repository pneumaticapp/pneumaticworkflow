from rest_framework.mixins import ListModelMixin, RetrieveModelMixin
from rest_framework.permissions import AllowAny
from rest_framework.viewsets import GenericViewSet

from src.generics.mixins.views import CustomViewSetMixin
from src.pages.models import Page
from src.pages.serializers import (
    PageSerializer,
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
