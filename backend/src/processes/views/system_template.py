from src.authentication.permissions import (
    StaffPermission,
)
from src.accounts.permissions import (
    BillingPlanPermission,
    UserIsAdminOrAccountOwner,
    UsersOverlimitedPermission,
    ExpiredSubscriptionPermission,
)
from src.generics.permissions import (
    UserIsAuthenticated,
)
from src.processes.filters import (
    SystemTemplateFilter,
)
from src.processes.models import (
    SystemTemplate,
    SystemTemplateCategory,
)
from rest_framework.mixins import (
    ListModelMixin,
)
from rest_framework.decorators import action
from rest_framework.viewsets import GenericViewSet
from rest_framework.pagination import LimitOffsetPagination

from src.generics.mixins.views import (
    CustomViewSetMixin,
)
from src.processes.serializers.templates.system_template import (
        SystemTemplateSerializer,
        SystemTemplateCategorySerializer,
        LibraryTemplateImportSerializer,
    )
from src.processes.services.templates.template import (
    TemplateService,
)
from src.processes.services.system_template import (
    SystemTemplateService,
)
from src.processes.parsers import ImportSystemTemplateParser
from src.generics.filters import PneumaticFilterBackend


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
            auth_type=request.token_type,
        )
        data = service.get_from_sys_template(system_template)
        return self.response_ok(data)

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
    serializer_class = LibraryTemplateImportSerializer

    def create(self, request, *args, **kwargs):
        slz = self.get_serializer(
            data=request.data.get('templates'),
            many=True,
        )
        slz.is_valid(raise_exception=True)
        service = SystemTemplateService(
            user=request.user,
            auth_type=request.token_type,
            is_superuser=request.is_superuser,
        )
        service.import_library_templates(data=slz.validated_data)
        return self.response_ok()
