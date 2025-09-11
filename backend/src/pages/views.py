from rest_framework.viewsets import GenericViewSet
from rest_framework.mixins import RetrieveModelMixin, ListModelMixin
from src.generics.mixins.views import CustomViewSetMixin
from rest_framework.permissions import AllowAny
from src.pages.serializers import (
    PageSerializer
)
from src.pages.models import Page


class PublicPageViewSet(
    CustomViewSetMixin,
    ListModelMixin,
    RetrieveModelMixin,
    GenericViewSet
):

    lookup_field = 'slug'
    queryset = Page.objects.public()
    permission_classes = (AllowAny,)
    serializer_class = PageSerializer
