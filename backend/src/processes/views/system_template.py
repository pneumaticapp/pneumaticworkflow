from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action
from rest_framework.mixins import (
    ListModelMixin,
)
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.viewsets import GenericViewSet

from src.accounts.permissions import (
    BillingPlanPermission,
    ExpiredSubscriptionPermission,
    UserIsAdminOrAccountOwner,
    UsersOverlimitedPermission,
)
from src.authentication.permissions import (
    StaffPermission,
)
from src.generics.filters import PneumaticFilterBackend
from src.generics.mixins.views import (
    CustomViewSetMixin,
)
from src.generics.permissions import (
    UserIsAuthenticated,
)
from src.openapi import (
    ACCESS_STAFF_IMPORT,
    ACCESS_SYSTEM_TEMPLATE,
    EMPTY,
    FORBIDDEN,
    NOT_FOUND,
    UNAUTHORIZED,
    VALIDATION_ERROR,
)
from src.processes.filters import (
    SystemTemplateFilter,
)
from src.processes.models.templates.system_template import (
    SystemTemplate,
    SystemTemplateCategory,
)
from src.processes.parsers import ImportSystemTemplateParser
from src.processes.serializers.templates.system_template import (
    LibraryTemplatesImportRequestSerializer,
    SystemTemplateCategorySerializer,
    SystemTemplateSerializer,
)
from src.processes.serializers.templates.template import (
    TemplateSerializer,
)
from src.processes.services.system_template import (
    SystemTemplateService,
)
from src.processes.services.templates.template import (
    TemplateService,
)


class SystemTemplateViewSet(
    CustomViewSetMixin,
    ListModelMixin,
    GenericViewSet,
):
    pagination_class = LimitOffsetPagination
    filter_backends = (PneumaticFilterBackend, )
    action_filterset_classes = {
        'list': SystemTemplateFilter,
    }

    def get_permissions(self):
        return (
            UserIsAuthenticated(),
            BillingPlanPermission(),
            ExpiredSubscriptionPermission(),
            UserIsAdminOrAccountOwner(),
            UsersOverlimitedPermission(),
        )

    def get_queryset(self):
        if self.action == 'categories':
            return SystemTemplateCategory.objects.active()
        return SystemTemplate.objects.library().active()

    def get_serializer_class(self):
        if self.action == 'categories':
            return SystemTemplateCategorySerializer
        return SystemTemplateSerializer

    @extend_schema(
        tags=['Templates'],
        summary='List system templates',
        description=ACCESS_SYSTEM_TEMPLATE,
        responses={
            200: SystemTemplateSerializer,
            401: UNAUTHORIZED,
            403: FORBIDDEN,
        },
    )
    def list(self, request, *args, **kwargs):
        qst = self.get_queryset()
        qst = self.filter_queryset(qst).order_by('name')
        return self.paginated_response(qst)

    @extend_schema(
        tags=['Templates'],
        summary='Fill template from system template',
        description=ACCESS_SYSTEM_TEMPLATE,
        responses={
            200: TemplateSerializer,
            401: UNAUTHORIZED,
            403: FORBIDDEN,
            404: NOT_FOUND,
        },
    )
    @action(methods=['POST'], detail=True, url_path='fill')
    def fill(self, request, *args, **kwargs):
        system_template = self.get_object()
        service = TemplateService(
            user=request.user,
            is_superuser=request.is_superuser,
            auth_type=request.token_type,
        )
        data = service.get_from_sys_template(system_template)
        return self.response_ok(data)

    @extend_schema(
        tags=['Templates'],
        summary='System template categories',
        description=ACCESS_SYSTEM_TEMPLATE,
        responses={
            200: SystemTemplateCategorySerializer(many=True),
            401: UNAUTHORIZED,
            403: FORBIDDEN,
        },
    )
    @action(methods=['GET'], detail=False)
    def categories(self, request, *args, **kwargs):
        slz = self.get_serializer(instance=self.get_queryset(), many=True)
        return self.response_ok(slz.data)


class SystemTemplatesImportViewSet(
    CustomViewSetMixin,
    GenericViewSet,
):
    parser_classes = [ImportSystemTemplateParser]
    permission_classes = (
        UserIsAuthenticated,
        BillingPlanPermission,
        ExpiredSubscriptionPermission,
        StaffPermission,
    )
    serializer_class = LibraryTemplatesImportRequestSerializer

    @extend_schema(
        tags=['Templates'],
        summary='Import library templates',
        description=ACCESS_STAFF_IMPORT,
        request=LibraryTemplatesImportRequestSerializer,
        responses={
            204: EMPTY,
            400: VALIDATION_ERROR,
            401: UNAUTHORIZED,
            403: FORBIDDEN,
        },
    )
    def create(self, request, *args, **kwargs):
        slz = self.get_serializer(data=request.data)
        slz.is_valid(raise_exception=True)
        service = SystemTemplateService(
            user=request.user,
            auth_type=request.token_type,
            is_superuser=request.is_superuser,
        )
        service.import_library_templates(data=slz.validated_data['templates'])
        return self.response_ok()
