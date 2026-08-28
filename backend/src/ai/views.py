from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.viewsets import GenericViewSet

from src.accounts.permissions import (
    UserIsAdminOrAccountOwner,
)
from src.ai.exceptions import AIServiceException
from src.ai.models import AIAgent, AIProvider
from src.ai.serializers import (
    AIAgentSerializer,
    AIModelSerializer,
    AIProviderSerializer,
)
from src.ai.services.agent import AIAgentService
from src.ai.services.provider import AIProviderService
from src.generics.mixins.views import CustomViewSetMixin
from src.generics.permissions import UserIsAuthenticated
from src.openapi import (
    ACCESS_AI,
    ACCESS_AI_ADMIN,
    EMPTY,
    FORBIDDEN,
    LIMIT_OFFSET_PARAMS,
    NOT_FOUND,
    UNAUTHORIZED,
    VALIDATION_ERROR,
)
from src.openapi.examples import (
    AI_AGENT_CREATE_EXAMPLE,
    AI_PROVIDER_CREATE_EXAMPLE,
)
from src.utils.validation import raise_validation_error


class AIProviderViewSet(
    CustomViewSetMixin,
    GenericViewSet,
):
    serializer_class = AIProviderSerializer
    action_serializer_classes = {
        'models': AIModelSerializer,
    }
    action_paginator_classes = {
        'list': LimitOffsetPagination,
    }

    def get_permissions(self):
        if self.action in ('create', 'partial_update', 'destroy'):
            return (
                UserIsAuthenticated(),
                UserIsAdminOrAccountOwner(),
            )
        return (
            UserIsAuthenticated(),
        )

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return AIProvider.objects.none()
        return self.prefetch_queryset(
            AIProvider.objects.on_account(self.request.user.account_id),
        )

    @extend_schema(
        tags=['AI'],
        summary='List AI providers',
        description=ACCESS_AI,
        parameters=LIMIT_OFFSET_PARAMS,
        responses={
            200: AIProviderSerializer,
            401: UNAUTHORIZED,
            403: FORBIDDEN,
        },
    )
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        return self.paginated_response(queryset)

    @extend_schema(
        tags=['AI'],
        summary='Create AI provider',
        description=ACCESS_AI_ADMIN,
        request=AIProviderSerializer,
        examples=[AI_PROVIDER_CREATE_EXAMPLE],
        responses={
            201: AIProviderSerializer,
            400: VALIDATION_ERROR,
            401: UNAUTHORIZED,
            403: FORBIDDEN,
        },
    )
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        service = AIProviderService(
            user=request.user,
            is_superuser=request.is_superuser,
            auth_type=request.token_type,
        )
        try:
            provider = service.create(**serializer.validated_data)
        except AIServiceException as ex:
            raise_validation_error(message=ex.message)
        response_serializer = self.get_serializer(instance=provider)
        return self.response_created(response_serializer.data)

    @extend_schema(
        tags=['AI'],
        summary='Get AI provider',
        description=ACCESS_AI,
        responses={
            200: AIProviderSerializer,
            401: UNAUTHORIZED,
            403: FORBIDDEN,
            404: NOT_FOUND,
        },
    )
    def retrieve(self, request, *args, **kwargs):
        provider = self.get_object()
        serializer = self.get_serializer(provider)
        return self.response_ok(serializer.data)

    @extend_schema(
        tags=['AI'],
        summary='Update AI provider',
        description=ACCESS_AI_ADMIN,
        request=AIProviderSerializer,
        responses={
            200: AIProviderSerializer,
            400: VALIDATION_ERROR,
            401: UNAUTHORIZED,
            403: FORBIDDEN,
            404: NOT_FOUND,
        },
    )
    def partial_update(self, request, *args, **kwargs):
        provider = self.get_object()
        serializer = self.get_serializer(
            provider,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        service = AIProviderService(
            user=request.user,
            instance=provider,
            is_superuser=request.is_superuser,
            auth_type=request.token_type,
        )
        try:
            provider = service.partial_update(**serializer.validated_data)
        except AIServiceException as ex:
            raise_validation_error(message=ex.message)
        response_serializer = self.get_serializer(provider)
        return self.response_ok(response_serializer.data)

    @extend_schema(
        tags=['AI'],
        summary='Delete AI provider',
        description=ACCESS_AI_ADMIN,
        responses={
            204: EMPTY,
            400: VALIDATION_ERROR,
            401: UNAUTHORIZED,
            403: FORBIDDEN,
            404: NOT_FOUND,
        },
    )
    def destroy(self, request, *args, **kwargs):
        provider = self.get_object()
        service = AIProviderService(
            user=request.user,
            instance=provider,
            is_superuser=request.is_superuser,
            auth_type=request.token_type,
        )
        try:
            service.delete()
        except AIServiceException as ex:
            raise_validation_error(message=ex.message)
        return self.response_ok()

    @extend_schema(
        tags=['AI'],
        summary='List AI provider models',
        description=ACCESS_AI,
        responses={
            200: AIModelSerializer(many=True),
            401: UNAUTHORIZED,
            403: FORBIDDEN,
            404: NOT_FOUND,
        },
    )
    @action(methods=['get'], detail=True, url_path='models')
    def models(self, request, *args, **kwargs):
        provider = self.get_object()
        service = AIProviderService(
            user=request.user,
            instance=provider,
            is_superuser=request.is_superuser,
            auth_type=request.token_type,
        )
        try:
            models = service.get_models()
        except AIServiceException as ex:
            raise_validation_error(message=ex.message)
        serializer = self.get_serializer(instance=models, many=True)
        return self.response_ok(serializer.data)


class AIAgentViewSet(
    CustomViewSetMixin,
    GenericViewSet,
):
    serializer_class = AIAgentSerializer
    action_paginator_classes = {
        'list': LimitOffsetPagination,
    }

    def get_permissions(self):
        if self.action in ('create', 'partial_update', 'destroy'):
            return (
                UserIsAuthenticated(),
                UserIsAdminOrAccountOwner(),
            )
        return (
            UserIsAuthenticated(),
        )

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return AIAgent.objects.none()
        return self.prefetch_queryset(
            AIAgent.objects.on_account(self.request.user.account_id),
        )

    @extend_schema(
        tags=['AI'],
        summary='List AI agents',
        description=ACCESS_AI,
        parameters=LIMIT_OFFSET_PARAMS,
        responses={
            200: AIAgentSerializer,
            401: UNAUTHORIZED,
            403: FORBIDDEN,
        },
    )
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        return self.paginated_response(queryset)

    @extend_schema(
        tags=['AI'],
        summary='Create AI agent',
        description=ACCESS_AI_ADMIN,
        request=AIAgentSerializer,
        examples=[AI_AGENT_CREATE_EXAMPLE],
        responses={
            201: AIAgentSerializer,
            400: VALIDATION_ERROR,
            401: UNAUTHORIZED,
            403: FORBIDDEN,
        },
    )
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        service = AIAgentService(
            user=request.user,
            is_superuser=request.is_superuser,
            auth_type=request.token_type,
        )
        try:
            agent = service.create(**serializer.validated_data)
        except AIServiceException as ex:
            raise_validation_error(message=ex.message)
        response_serializer = AIAgentSerializer(agent)
        return self.response_created(response_serializer.data)

    @extend_schema(
        tags=['AI'],
        summary='Get AI agent',
        description=ACCESS_AI,
        responses={
            200: AIAgentSerializer,
            401: UNAUTHORIZED,
            403: FORBIDDEN,
            404: NOT_FOUND,
        },
    )
    def retrieve(self, request, *args, **kwargs):
        agent = self.get_object()
        serializer = self.get_serializer(agent)
        return self.response_ok(serializer.data)

    @extend_schema(
        tags=['AI'],
        summary='Update AI agent',
        description=ACCESS_AI_ADMIN,
        request=AIAgentSerializer,
        responses={
            200: AIAgentSerializer,
            400: VALIDATION_ERROR,
            401: UNAUTHORIZED,
            403: FORBIDDEN,
            404: NOT_FOUND,
        },
    )
    def partial_update(self, request, *args, **kwargs):
        agent = self.get_object()
        serializer = self.get_serializer(
            agent,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        service = AIAgentService(
            user=request.user,
            instance=agent,
            is_superuser=request.is_superuser,
            auth_type=request.token_type,
        )
        try:
            agent = service.partial_update(**serializer.validated_data)
        except AIServiceException as ex:
            raise_validation_error(message=ex.message)
        response_serializer = AIAgentSerializer(agent)
        return self.response_ok(response_serializer.data)

    @extend_schema(
        tags=['AI'],
        summary='Delete AI agent',
        description=ACCESS_AI_ADMIN,
        responses={
            204: EMPTY,
            400: VALIDATION_ERROR,
            401: UNAUTHORIZED,
            403: FORBIDDEN,
            404: NOT_FOUND,
        },
    )
    def destroy(self, request, *args, **kwargs):
        agent = self.get_object()
        service = AIAgentService(
            user=request.user,
            instance=agent,
            is_superuser=request.is_superuser,
            auth_type=request.token_type,
        )
        try:
            service.delete()
        except AIServiceException as ex:
            raise_validation_error(message=ex.message)
        return self.response_ok()
