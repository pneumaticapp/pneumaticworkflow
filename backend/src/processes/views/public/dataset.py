from typing import Optional, List
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.viewsets import GenericViewSet

from src.generics.mixins.views import CustomViewSetMixin
from src.processes.models.dataset import Dataset
from src.processes.permissions import PublicTemplatePermission
from src.processes.serializers.templates.dataset import (
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

    def retrieve(self, request, *args, **kwargs):
        dataset = self.self.get_object()
        serializer = self.get_serializer(dataset)
        return self.response_ok(serializer.data)
