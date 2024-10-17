from rest_framework.viewsets import GenericViewSet
from rest_framework.mixins import RetrieveModelMixin, ListModelMixin
from pneumatic_backend.generics.mixins.views import CustomViewSetMixin
from rest_framework.permissions import AllowAny
from pneumatic_backend.pages.serializers import (
    PageSerializer
)
from pneumatic_backend.pages.models import Page


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
