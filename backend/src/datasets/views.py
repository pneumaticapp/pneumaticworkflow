from django.db.models import Count, Q
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.viewsets import GenericViewSet

from src.accounts.permissions import (
    BillingPlanPermission,
    ExpiredSubscriptionPermission,
    UserIsAdminOrAccountOwner,
    UsersOverlimitedPermission,
)
from src.datasets.exceptions import DataSetServiceException
from src.datasets.filters import DatasetFilter
from src.datasets.models import Dataset, DatasetItem
from src.datasets.serializers import (
    DatasetItemSerializer,
    DatasetListSerializer,
    DatasetSerializer,
)
from src.datasets.services.dataset import DataSetService
from src.datasets.services.dataset_item import DataSetItemService
from src.generics.filters import PneumaticFilterBackend
from src.generics.mixins.views import CustomViewSetMixin
from src.generics.permissions import UserIsAuthenticated
from src.openapi import (
    ACCESS_ADMIN,
    ACCESS_AUTH_OVERLIMIT,
    DATASETS_LIST_PARAMS,
    EMPTY,
    FORBIDDEN,
    NOT_FOUND,
    UNAUTHORIZED,
    VALIDATION_ERROR,
)
from src.openapi.examples import DATASET_CREATE_EXAMPLE
from src.utils.validation import raise_validation_error


class DatasetViewSet(
    CustomViewSetMixin,
    GenericViewSet,
):
    serializer_class = DatasetSerializer
    action_serializer_classes = {
        'list': DatasetListSerializer,
        'create_item': DatasetItemSerializer,
        'create_items': DatasetItemSerializer,
        'update_items': DatasetItemSerializer,
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
        if getattr(self, 'swagger_fake_view', False):
            return Dataset.objects.none()
        user = self.request.user
        queryset = Dataset.objects.on_account(user.account_id)
        if self.action == 'list':
            queryset = queryset.annotate(
                items_count=Count(
                    'items',
                    filter=Q(items__is_deleted=False),
                ),
            )
        return self.prefetch_queryset(queryset)

    @extend_schema(
        tags=['Datasets'],
        summary='List datasets',
        description=ACCESS_AUTH_OVERLIMIT,
        parameters=DATASETS_LIST_PARAMS,
        responses={
            # Item serializer; spectacular wraps with pagination.
            200: DatasetListSerializer,
            401: UNAUTHORIZED,
            403: FORBIDDEN,
        },
    )
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        queryset = self.filter_queryset(queryset)
        return self.paginated_response(queryset)

    @extend_schema(
        tags=['Datasets'],
        summary='Create dataset',
        description=ACCESS_ADMIN,
        request=DatasetSerializer,
        examples=[DATASET_CREATE_EXAMPLE],
        responses={
            201: DatasetSerializer,
            400: VALIDATION_ERROR,
            401: UNAUTHORIZED,
            403: FORBIDDEN,
        },
    )
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

    @extend_schema(
        tags=['Datasets'],
        summary='Get dataset',
        description=ACCESS_AUTH_OVERLIMIT,
        responses={
            200: DatasetSerializer,
            401: UNAUTHORIZED,
            403: FORBIDDEN,
            404: NOT_FOUND,
        },
    )
    def retrieve(self, request, *args, **kwargs):
        dataset = self.get_object()
        serializer = self.get_serializer(dataset)
        return self.response_ok(serializer.data)

    @extend_schema(
        tags=['Datasets'],
        summary='Update dataset',
        description=ACCESS_ADMIN,
        request=DatasetSerializer,
        responses={
            200: DatasetSerializer,
            400: VALIDATION_ERROR,
            401: UNAUTHORIZED,
            403: FORBIDDEN,
            404: NOT_FOUND,
        },
    )
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
            dataset = service.partial_update(
                **serializer.validated_data,
            )
        except DataSetServiceException as ex:
            raise_validation_error(message=ex.message)
        dataset.refresh_from_db()
        response_serializer = DatasetSerializer(dataset)
        return self.response_ok(response_serializer.data)

    @extend_schema(
        tags=['Datasets'],
        summary='Delete dataset',
        description=ACCESS_ADMIN,
        responses={
            204: EMPTY,
            400: VALIDATION_ERROR,
            401: UNAUTHORIZED,
            403: FORBIDDEN,
            404: NOT_FOUND,
        },
    )
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

    @extend_schema(
        tags=['Datasets'],
        summary='Add dataset items',
        description=ACCESS_ADMIN,
        request=DatasetItemSerializer(many=True),
        responses={
            200: DatasetItemSerializer(many=True),
            400: VALIDATION_ERROR,
            401: UNAUTHORIZED,
            403: FORBIDDEN,
            404: NOT_FOUND,
        },
    )
    @action(methods=['post'], detail=True, url_path='items')
    def create_items(self, request, *args, **kwargs):
        dataset = self.get_object()
        serializer = self.get_serializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)
        service = DataSetService(
            user=request.user,
            instance=dataset,
            is_superuser=request.is_superuser,
            auth_type=request.token_type,
        )
        try:
            service.create_items(items_data=serializer.validated_data)
        except DataSetServiceException as ex:
            raise_validation_error(message=ex.message)
        items = dataset.items.all()
        response_serializer = self.get_serializer(instance=items, many=True)
        return self.response_ok(response_serializer.data)

    @extend_schema(
        tags=['Datasets'],
        summary='Replace dataset items',
        description=ACCESS_ADMIN,
        request=DatasetItemSerializer(many=True),
        responses={
            200: DatasetItemSerializer(many=True),
            400: VALIDATION_ERROR,
            401: UNAUTHORIZED,
            403: FORBIDDEN,
            404: NOT_FOUND,
        },
    )
    @create_items.mapping.put
    def update_items(self, request, *args, **kwargs):
        dataset = self.get_object()
        serializer = self.get_serializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)
        service = DataSetService(
            user=request.user,
            instance=dataset,
            is_superuser=request.is_superuser,
            auth_type=request.token_type,
        )
        try:
            service.update_items(items_data=serializer.validated_data)
        except DataSetServiceException as ex:
            raise_validation_error(message=ex.message)
        items = dataset.items.all()
        response_serializer = self.get_serializer(instance=items, many=True)
        return self.response_ok(response_serializer.data)

    @extend_schema(
        tags=['Datasets'],
        summary='Create dataset item',
        description=ACCESS_ADMIN,
        request=DatasetItemSerializer,
        responses={
            201: DatasetItemSerializer,
            400: VALIDATION_ERROR,
            401: UNAUTHORIZED,
            403: FORBIDDEN,
            404: NOT_FOUND,
        },
    )
    @action(methods=['post'], detail=True, url_path='item')
    def create_item(self, request, *args, **kwargs):
        dataset = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        service = DataSetItemService(
            user=request.user,
            is_superuser=request.is_superuser,
            auth_type=request.token_type,
        )
        try:
            item = service.create(
                dataset_id=dataset.id,
                **serializer.validated_data,
            )
        except DataSetServiceException as ex:
            raise_validation_error(message=ex.message)
        response_serializer = self.get_serializer(instance=item)
        return self.response_created(response_serializer.data)


class DatasetItemViewSet(
    CustomViewSetMixin,
    GenericViewSet,
):
    serializer_class = DatasetItemSerializer

    def get_permissions(self):
        return (
            UserIsAuthenticated(),
            ExpiredSubscriptionPermission(),
            BillingPlanPermission(),
            UsersOverlimitedPermission(),
            UserIsAdminOrAccountOwner(),
        )

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return DatasetItem.objects.none()
        user = self.request.user
        return DatasetItem.objects.filter(
            account_id=user.account_id,
            is_deleted=False,
        )

    @extend_schema(
        tags=['Datasets'],
        summary='Update dataset item',
        description=ACCESS_ADMIN,
        request=DatasetItemSerializer,
        responses={
            200: DatasetItemSerializer,
            400: VALIDATION_ERROR,
            401: UNAUTHORIZED,
            403: FORBIDDEN,
            404: NOT_FOUND,
        },
    )
    def partial_update(self, request, *args, **kwargs):
        item = self.get_object()
        serializer = self.get_serializer(
            item,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        service = DataSetItemService(
            user=request.user,
            instance=item,
            is_superuser=request.is_superuser,
            auth_type=request.token_type,
        )
        try:
            item = service.partial_update(
                force_save=True,
                **serializer.validated_data,
            )
        except DataSetServiceException as ex:
            raise_validation_error(message=ex.message)
        item.refresh_from_db()
        response_serializer = self.get_serializer(item)
        return self.response_ok(response_serializer.data)

    @extend_schema(
        tags=['Datasets'],
        summary='Delete dataset item',
        description=ACCESS_ADMIN,
        responses={
            204: EMPTY,
            401: UNAUTHORIZED,
            403: FORBIDDEN,
            404: NOT_FOUND,
        },
    )
    def destroy(self, request, *args, **kwargs):
        item = self.get_object()
        service = DataSetItemService(
            user=request.user,
            instance=item,
            is_superuser=request.is_superuser,
            auth_type=request.token_type,
        )
        service.delete()
        return self.response_ok()
