from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiParameter,
    extend_schema,
)
from rest_framework.decorators import action
from rest_framework.viewsets import GenericViewSet

from src.accounts.permissions import (
    BillingPlanPermission,
    ExpiredSubscriptionPermission,
    UserIsAdminOrAccountOwner,
    UsersOverlimitedPermission,
)
from src.generics.exceptions import BaseServiceException
from src.generics.filters import PneumaticFilterBackend
from src.generics.mixins.views import CustomViewSetMixin
from src.generics.permissions import UserIsAuthenticated
from src.openapi import (
    ACCESS_ADMIN,
    EMPTY,
    FORBIDDEN,
    LIMIT_OFFSET_LEGACY_NOTE,
    NOT_FOUND,
    UNAUTHORIZED,
    VALIDATION_ERROR,
    with_access_text,
)
from src.processes.filters import FieldSetFilter
from src.processes.models.templates.fieldset import (
    FieldsetTemplate,
)
from src.processes.serializers.templates.fieldset import (
    SharedFieldsetTemplateSerializer,
)
from src.processes.serializers.templates.template import (
    FieldsetTemplateFilterSerializer,
)
from src.processes.services.fieldsets.fieldset import (
    FieldSetTemplateService,
)
from src.utils.validation import raise_validation_error


class SharedFieldsetTemplateViewSet(
    CustomViewSetMixin,
    GenericViewSet,
):
    serializer_class = SharedFieldsetTemplateSerializer
    filter_backends = (PneumaticFilterBackend,)

    action_filterset_classes = {
        'list': FieldSetFilter,
    }

    def get_serializer_context(self, **kwargs):
        context = super().get_serializer_context(**kwargs)
        if getattr(self, 'swagger_fake_view', False):
            return context
        context['user'] = self.request.user
        context['account'] = self.request.user.account
        context['is_superuser'] = self.request.is_superuser
        context['auth_type'] = self.request.token_type
        return context

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
            return FieldsetTemplate.objects.none()
        user = self.request.user
        return (
            FieldsetTemplate.objects
            .select_related('template')
            .shared()
            .on_account(user.account_id)
        )

    @extend_schema(
        tags=['Fieldsets'],
        summary='List shared fieldsets',
        description=with_access_text(
            LIMIT_OFFSET_LEGACY_NOTE,
            ACCESS_ADMIN,
        ),
        parameters=[
            OpenApiParameter(
                name='ordering',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=False,
                description='Sort field: name, date (prefix - to invert)',
            ),
            OpenApiParameter(
                name='limit',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                required=False,
            ),
            OpenApiParameter(
                name='offset',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                required=False,
            ),
        ],
        responses={
            # Item serializer; spectacular wraps with pagination.
            200: SharedFieldsetTemplateSerializer,
            400: VALIDATION_ERROR,
            401: UNAUTHORIZED,
            403: FORBIDDEN,
        },
    )
    def list(self, request, *args, **kwargs):
        filter_slz = FieldsetTemplateFilterSerializer(data=request.GET)
        filter_slz.is_valid(raise_exception=True)
        queryset = self.filter_queryset(self.get_queryset())
        return self.paginated_response(queryset)

    @extend_schema(
        tags=['Fieldsets'],
        summary='Create shared fieldset',
        description=ACCESS_ADMIN,
        request=SharedFieldsetTemplateSerializer,
        responses={
            201: SharedFieldsetTemplateSerializer,
            400: VALIDATION_ERROR,
            401: UNAUTHORIZED,
            403: FORBIDDEN,
        },
    )
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        service = FieldSetTemplateService(
            user=request.user,
            is_superuser=request.is_superuser,
            auth_type=request.token_type,
        )
        try:
            fieldset = service.create_shared_fieldset(
                **serializer.validated_data,
            )
        except BaseServiceException as ex:
            raise_validation_error(message=ex.message)
        else:
            response_serializer = SharedFieldsetTemplateSerializer(fieldset)
            return self.response_created(response_serializer.data)

    @extend_schema(
        tags=['Fieldsets'],
        summary='Get shared fieldset',
        description=ACCESS_ADMIN,
        responses={
            200: SharedFieldsetTemplateSerializer,
            401: UNAUTHORIZED,
            403: FORBIDDEN,
            404: NOT_FOUND,
        },
    )
    def retrieve(self, request, *args, **kwargs):
        fieldset = self.get_object()
        serializer = self.get_serializer(fieldset)
        return self.response_ok(serializer.data)

    @extend_schema(
        tags=['Fieldsets'],
        summary='Update shared fieldset',
        description=ACCESS_ADMIN,
        request=SharedFieldsetTemplateSerializer,
        responses={
            200: SharedFieldsetTemplateSerializer,
            400: VALIDATION_ERROR,
            401: UNAUTHORIZED,
            403: FORBIDDEN,
            404: NOT_FOUND,
        },
    )
    def partial_update(self, request, *args, **kwargs):
        fieldset = self.get_object()
        serializer = self.get_serializer(
            fieldset,
            data=request.data,
            partial=True,
            extra_fields={'template': fieldset.template},
        )
        serializer.is_valid(raise_exception=True)
        service = FieldSetTemplateService(
            user=request.user,
            instance=fieldset,
            is_superuser=request.is_superuser,
            auth_type=request.token_type,
        )
        try:
            fieldset = service.partial_update(
                **serializer.validated_data,
            )
        except BaseServiceException as ex:
            raise_validation_error(message=ex.message)
        fieldset.refresh_from_db()
        response_serializer = SharedFieldsetTemplateSerializer(fieldset)
        return self.response_ok(response_serializer.data)

    @extend_schema(
        tags=['Fieldsets'],
        summary='Delete shared fieldset',
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
        fieldset = self.get_object()
        service = FieldSetTemplateService(
            user=request.user,
            instance=fieldset,
            is_superuser=request.is_superuser,
            auth_type=request.token_type,
        )
        try:
            service.delete()
        except BaseServiceException as ex:
            raise_validation_error(message=ex.message)
        return self.response_ok()

    @extend_schema(
        tags=['Fieldsets'],
        summary='Clone shared fieldset',
        description=ACCESS_ADMIN,
        responses={
            201: SharedFieldsetTemplateSerializer,
            400: VALIDATION_ERROR,
            401: UNAUTHORIZED,
            403: FORBIDDEN,
            404: NOT_FOUND,
        },
    )
    @action(methods=['POST'], detail=True)
    def clone(self, request, *args, **kwargs):
        fieldset = self.get_object()
        service = FieldSetTemplateService(
            user=request.user,
            instance=fieldset,
            is_superuser=request.is_superuser,
            auth_type=request.token_type,
        )
        try:
            fieldset = service.get_clone()
        except BaseServiceException as ex:
            raise_validation_error(message=ex.message)
        else:
            response_serializer = SharedFieldsetTemplateSerializer(fieldset)
            return self.response_created(response_serializer.data)
