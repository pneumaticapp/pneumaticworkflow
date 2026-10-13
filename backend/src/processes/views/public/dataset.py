from typing import Optional, List

from drf_spectacular.utils import extend_schema
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.viewsets import GenericViewSet

from src.generics.mixins.views import CustomViewSetMixin
from src.datasets.models import Dataset
from src.openapi import (
    ACCESS_PUBLIC_TEMPLATE,
    FORBIDDEN,
    NOT_FOUND,
)
from src.processes.permissions import PublicTemplatePermission
from src.datasets.serializers import (
    DatasetSerializer,
)


class PublicDatasetViewSet(
    CustomViewSetMixin,
    GenericViewSet,
):
    permission_classes = (PublicTemplatePermission,)
    serializer_class = DatasetSerializer
    action_paginator_classes = {
        'list': LimitOffsetPagination,
    }

    def get_queryset(self):
        user = self.request.user
        queryset = Dataset.objects.on_account(user.account_id)
        return self.prefetch_queryset(queryset)

    def prefetch_queryset(
        self,
        queryset,
        extra_fields: Optional[List[str]] = None,
    ):
        extra_fields = [
            'items',
        ]
        return super().prefetch_queryset(
            queryset=queryset,
            extra_fields=extra_fields,
        )

    @extend_schema(
        tags=['Templates Public'],
        summary='Get public dataset',
        description=ACCESS_PUBLIC_TEMPLATE,
        auth=[{'publicTemplateAuth': []}],
        responses={
            200: DatasetSerializer,
            403: FORBIDDEN,
            404: NOT_FOUND,
        },
    )
    def retrieve(self, request, *args, **kwargs):
        dataset = self.get_object()
        serializer = self.get_serializer(dataset)
        return self.response_ok(serializer.data)
