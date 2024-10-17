from pneumatic_backend.authentication.permissions import (
    StaffPermission
)
from pneumatic_backend.accounts.permissions import (
    UserIsAdminOrAccountOwner,
    UsersOverlimitedPermission,
    ExpiredSubscriptionPermission,
)
from pneumatic_backend.generics.permissions import (
    UserIsAuthenticated,
    PaymentCardPermission,
)
from pneumatic_backend.processes.filters import (
    SystemTemplateFilter
)
from pneumatic_backend.processes.models import (
    SystemTemplate,
    SystemTemplateCategory,
)
from rest_framework.mixins import (
    ListModelMixin
)
from rest_framework.decorators import action
from rest_framework.viewsets import GenericViewSet
from rest_framework.pagination import LimitOffsetPagination

from pneumatic_backend.generics.mixins.views import (
    CustomViewSetMixin,
)
from pneumatic_backend.processes.api_v2.serializers.\
    template.system_template import (
        SystemTemplateSerializer,
        SystemTemplateCategorySerializer,
        LibraryTemplateImportSerializer,
    )
from pneumatic_backend.processes.api_v2.services import (
    TemplateService,
    SystemTemplateService,
)
from pneumatic_backend.processes.parsers import ImportSystemTemplateParser
from pneumatic_backend.generics.filters import PneumaticFilterBackend


class SystemTemplateViewSet(
    CustomViewSetMixin,
    ListModelMixin,
    GenericViewSet
):
    pagination_class = LimitOffsetPagination
    filter_backends = (PneumaticFilterBackend, )
    action_filterset_classes = {
        'list': SystemTemplateFilter,
    }

    def get_permissions(self):
        return (
            UserIsAuthenticated(),
            UserIsAdminOrAccountOwner(),
            ExpiredSubscriptionPermission(),
            UsersOverlimitedPermission(),
            PaymentCardPermission(),
        )

    def get_queryset(self):
        if self.action == 'categories':
            return SystemTemplateCategory.objects.active()
        else:
            return SystemTemplate.objects.library().active()

    def get_serializer_class(self):
        if self.action == 'categories':
            return SystemTemplateCategorySerializer
        else:
            return SystemTemplateSerializer

    def list(self, request, *args, **kwargs):
        qst = self.get_queryset()
        qst = self.filter_queryset(qst).order_by('name')
        return self.paginated_response(qst)

    @action(methods=['POST'], detail=True, url_path='fill')
    def fill(self, request, *args, **kwargs):
        system_template = self.get_object()
        service = TemplateService(
            user=request.user,
            is_superuser=request.is_superuser,
            auth_type=request.token_type
        )
        data = service.get_from_sys_template(system_template)
        return self.response_ok(data)

    @action(methods=['GET'], detail=False)
    def categories(self, request, *args, **kwargs):
        slz = self.get_serializer(instance=self.get_queryset(), many=True)
        return self.response_ok(slz.data)


class SystemTemplatesImportViewSet(
    CustomViewSetMixin,
    GenericViewSet
):
    parser_classes = [ImportSystemTemplateParser]
    permission_classes = (
        UserIsAuthenticated,
        StaffPermission,
    )
    serializer_class = LibraryTemplateImportSerializer

    def create(self, request, *args, **kwargs):
        slz = self.get_serializer(
            data=request.data.get('templates'),
            many=True
        )
        slz.is_valid(raise_exception=True)
        service = SystemTemplateService(
            user=request.user,
            auth_type=request.token_type,
            is_superuser=request.is_superuser,
        )
        service.import_library_templates(data=slz.validated_data)
        return self.response_ok()
