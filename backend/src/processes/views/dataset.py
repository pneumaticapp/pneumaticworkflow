from typing import Optional, List
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.viewsets import GenericViewSet

from src.accounts.permissions import (
    BillingPlanPermission,
    ExpiredSubscriptionPermission,
    UserIsAdminOrAccountOwner,
    UsersOverlimitedPermission,
)
from src.generics.mixins.views import CustomViewSetMixin
from src.generics.permissions import UserIsAuthenticated
from src.processes.models.templates.dataset import Dataset
from src.processes.serializers.templates.dataset import (
    DatasetListSerializer,
    DatasetSerializer,
)


class DatasetViewSet(
    CustomViewSetMixin,
    GenericViewSet,
):
    serializer_class = DatasetSerializer
    action_serializer_classes = {
        'list': DatasetListSerializer,
    }
    action_paginator_classes = {
        'list': LimitOffsetPagination,
    }

    def get_serializer_context(self, **kwargs):
        context = super().get_serializer_context(**kwargs)
        context['user'] = self.request.user
        context['account'] = self.request.user.account
        context['is_superuser'] = self.request.is_superuser
        context['auth_type'] = self.request.token_type
        if self.request.user.is_guest:
            context['guest_task_id'] = self.request.task_id
        return context

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return (
                UserIsAuthenticated(),
                ExpiredSubscriptionPermission(),
                BillingPlanPermission(),
                UsersOverlimitedPermission(),
            )
        return (
            UserIsAuthenticated(),
            ExpiredSubscriptionPermission(),
            BillingPlanPermission(),
            UsersOverlimitedPermission(),
            UserIsAdminOrAccountOwner(),
        )

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

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return self.response_ok(serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        dataset = Dataset.objects.create(
            account=request.user.account,
            **serializer.validated_data,
        )
        response_serializer = DatasetSerializer(dataset)
        return self.response_created(response_serializer.data)

    def retrieve(self, request, *args, **kwargs):
        dataset = self.get_object()
        serializer = self.get_serializer(dataset)
        return self.response_ok(serializer.data)

    def partial_update(self, request, *args, **kwargs):
        dataset = self.get_object()
        serializer = self.get_serializer(
            dataset,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        response_serializer = DatasetSerializer(dataset)
        return self.response_ok(response_serializer.data)

    def destroy(self, request, *args, **kwargs):
        dataset = self.get_object()
        dataset.delete()
        return self.response_ok()
