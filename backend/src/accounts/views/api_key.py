from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema
from rest_framework.generics import get_object_or_404
from rest_framework.mixins import (
    CreateModelMixin,
    DestroyModelMixin,
    ListModelMixin,
)
from rest_framework.viewsets import GenericViewSet

from src.accounts.models import APIKey
from src.accounts.permissions import (
    AccountOwnerPermission,
    BillingPlanPermission,
    ExpiredSubscriptionPermission,
    UserIsAdminOrAccountOwner,
)
from src.accounts.serializers.api_key import (
    APIKeyCreateSerializer,
    APIKeyListSerializer,
    APIKeyResponseSerializer,
)
from src.accounts.services.api_key import APIKeyService
from src.generics.mixins.views import (
    BaseResponseMixin,
)
from src.generics.permissions import (
    UserIsAuthenticated,
)
from src.openapi import (
    ACCESS_ACCOUNT_OWNER,
    ACCESS_ADMIN_BASE,
    EMPTY,
    FORBIDDEN,
    NOT_FOUND,
    UNAUTHORIZED,
    VALIDATION_ERROR,
)

UserModel = get_user_model()


class APIKeyViewSet(
    CreateModelMixin,
    ListModelMixin,
    DestroyModelMixin,
    GenericViewSet,
    BaseResponseMixin,
):

    permission_classes = (
        UserIsAuthenticated,
        BillingPlanPermission,
        UserIsAdminOrAccountOwner,
        ExpiredSubscriptionPermission,
    )
    serializer_class = APIKeyListSerializer

    def get_queryset(self):
        return (
            APIKey.objects
            .by_user(self.request.user.id)
            .active()
            .order_by('-date_created')
        )

    def get_serializer_class(self):
        if self.action == 'create':
            return APIKeyCreateSerializer
        return APIKeyListSerializer

    @extend_schema(
        tags=['Accounts'],
        summary='List API keys',
        description=ACCESS_ADMIN_BASE,
        responses={
            200: APIKeyListSerializer(many=True),
            401: UNAUTHORIZED,
            403: FORBIDDEN,
        },
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        tags=['Accounts'],
        summary='Create API key',
        description=ACCESS_ADMIN_BASE,
        request=APIKeyCreateSerializer,
        responses={
            201: APIKeyResponseSerializer,
            400: VALIDATION_ERROR,
            401: UNAUTHORIZED,
            403: FORBIDDEN,
        },
    )
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        service = APIKeyService(
            user=request.user,
            is_superuser=request.is_superuser,
            auth_type=request.token_type,
        )
        api_key, raw_key = service.create(
            name=serializer.validated_data.get('name'),
        )

        api_key.key = raw_key
        response_serializer = APIKeyResponseSerializer(api_key)
        return self.response_created(response_serializer.data)

    @extend_schema(
        tags=['Accounts'],
        summary='Revoke API key',
        description=ACCESS_ADMIN_BASE,
        responses={
            200: EMPTY,
            401: UNAUTHORIZED,
            403: FORBIDDEN,
            404: NOT_FOUND,
        },
    )
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        service = APIKeyService(
            user=request.user,
            instance=instance,
            is_superuser=request.is_superuser,
            auth_type=request.token_type,
        )
        service.revoke()
        return self.response_ok()


class UserAPIKeyViewSet(
    CreateModelMixin,
    ListModelMixin,
    DestroyModelMixin,
    GenericViewSet,
    BaseResponseMixin,
):

    permission_classes = (
        AccountOwnerPermission,
        ExpiredSubscriptionPermission,
        BillingPlanPermission,
    )
    serializer_class = APIKeyListSerializer

    def _get_target_user(self):
        return get_object_or_404(
            UserModel.include_inactive
            .all_account_users(self.request.user.account_id),
            id=self.kwargs['user_id'],
        )

    def get_queryset(self):
        return (
            APIKey.objects
            .by_user(self.kwargs['user_id'])
            .filter(account_id=self.request.user.account_id)
            .active()
            .order_by('-date_created')
        )

    def get_serializer_class(self):
        if self.action == 'create':
            return APIKeyCreateSerializer
        return APIKeyListSerializer

    @extend_schema(
        tags=['Accounts'],
        summary='List API keys for user',
        description=ACCESS_ACCOUNT_OWNER,
        responses={
            200: APIKeyListSerializer(many=True),
            401: UNAUTHORIZED,
            403: FORBIDDEN,
            404: NOT_FOUND,
        },
    )
    def list(self, request, *args, **kwargs):
        # Validate user exists in account, return 404 instead of empty list
        self._get_target_user()
        return super().list(request, *args, **kwargs)

    @extend_schema(
        tags=['Accounts'],
        summary='Create API key for user',
        description=ACCESS_ACCOUNT_OWNER,
        request=APIKeyCreateSerializer,
        responses={
            201: APIKeyResponseSerializer,
            400: VALIDATION_ERROR,
            401: UNAUTHORIZED,
            403: FORBIDDEN,
            404: NOT_FOUND,
        },
    )
    def create(self, request, *args, **kwargs):
        target_user = self._get_target_user()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        service = APIKeyService(
            user=request.user,
            is_superuser=request.is_superuser,
            auth_type=request.token_type,
        )
        api_key, raw_key = service.create_for_user(
            target_user=target_user,
            name=serializer.validated_data.get('name'),
        )

        api_key.key = raw_key
        return self.response_created(
            APIKeyResponseSerializer(api_key).data,
        )

    @extend_schema(
        tags=['Accounts'],
        summary='Revoke API key for user',
        description=ACCESS_ACCOUNT_OWNER,
        responses={
            200: EMPTY,
            401: UNAUTHORIZED,
            403: FORBIDDEN,
            404: NOT_FOUND,
        },
    )
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        service = APIKeyService(
            user=request.user,
            instance=instance,
            is_superuser=request.is_superuser,
            auth_type=request.token_type,
        )
        service.revoke()
        return self.response_ok()
