from typing import Optional, List
from django.db.models import Count
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.viewsets import GenericViewSet

from src.accounts.permissions import (
    BillingPlanPermission,
    ExpiredSubscriptionPermission,
    UserIsAdminOrAccountOwner,
    UsersOverlimitedPermission,
)
from src.generics.filters import PneumaticFilterBackend
from src.generics.mixins.views import CustomViewSetMixin
from src.generics.permissions import UserIsAuthenticated
from src.processes.filters import DatasetFilter
from src.processes.models.dataset import Dataset
from src.processes.serializers.templates.dataset import (
    DatasetListSerializer,
    DatasetSerializer,
)
from src.processes.services.exceptions import DataSetServiceException
from src.processes.services.templates.dataset import DataSetService
from src.utils.validation import raise_validation_error


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
    filter_backends = (PneumaticFilterBackend,)
    action_filterset_classes = {
        'list': DatasetFilter,
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
        if self.action == 'list':
            queryset = queryset.annotate(
                items_count=Count('items'),
            )
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
        queryset = self.filter_queryset(queryset)
        return self.paginated_response(queryset)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        service = DataSetService(
            user=request.user,
            is_superuser=request.is_superuser,
            auth_type=request.token_type,
        )
        try:
            dataset = service.create(**serializer.validated_data)
        except DataSetServiceException as ex:
            raise_validation_error(message=ex.message)
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
        service = DataSetService(
            user=request.user,
            instance=dataset,
            is_superuser=request.is_superuser,
            auth_type=request.token_type,
        )
        try:
            service.partial_update(
                force_save=True,
                **serializer.validated_data,
            )
        except DataSetServiceException as ex:
            raise_validation_error(message=ex.message)
        response_serializer = DatasetSerializer(dataset)
        return self.response_ok(response_serializer.data)

    def destroy(self, request, *args, **kwargs):
        dataset = self.get_object()
        service = DataSetService(
            user=request.user,
            instance=dataset,
            is_superuser=request.is_superuser,
            auth_type=request.token_type,
        )
        try:
            service.delete()
        except DataSetServiceException as ex:
            raise_validation_error(message=ex.message)
        return self.response_ok()
