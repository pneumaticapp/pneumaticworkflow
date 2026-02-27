from django.contrib.auth import get_user_model
from rest_framework.decorators import action
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.viewsets import GenericViewSet

from src.accounts.filters import (
    ContactsFilterSet,
)
from src.accounts.models import (
    Contact,
)
from src.accounts.permissions import (
    BillingPlanPermission,
    ExpiredSubscriptionPermission,
)
from src.accounts.serializers.user import (
    ContactRequestSerializer,
    ContactResponseSerializer,
    UserSerializer,
)
from src.accounts.services.exceptions import UserServiceException
from src.accounts.services.user import UserService
from src.analysis.mixins import BaseIdentifyMixin
from src.generics.filters import PneumaticFilterBackend
from src.generics.mixins.views import (
    CustomViewSetMixin,
)
from src.generics.permissions import (
    IsAuthenticated,
    UserIsAuthenticated,
)
from src.processes.models.workflows.task import Task
from src.utils.validation import raise_validation_error

UserModel = get_user_model()


class UserViewSet(
    CustomViewSetMixin,
    GenericViewSet,
    BaseIdentifyMixin,
):

    serializer_class = UserSerializer
    filter_backends = [PneumaticFilterBackend]
    pagination_class = LimitOffsetPagination
    action_filterset_classes = {
        'contacts': ContactsFilterSet,
    }
    action_serializer_classes = {
        'contacts': ContactResponseSerializer,
    }

    def get_permissions(self):
        method = self.request.method
        if self.action is None and method == 'PUT':
            return (
                UserIsAuthenticated(),
                BillingPlanPermission(),
                ExpiredSubscriptionPermission(),
            )
        if self.action == 'list':
            return (
                IsAuthenticated(),
                BillingPlanPermission(),
            )
        return (
            UserIsAuthenticated(),
            BillingPlanPermission(),
        )

    def get_queryset(self):
        if self.action == 'contacts':
            return Contact.objects.by_user(
                user_id=self.request.user.id,
            ).active()
        return None

    @action(methods=('GET',), detail=False)
    def counters(self, request, *args, **kwargs):
        return self.response_ok({
            'tasks_count': (
                Task.objects
                .active_for_user(request.user.id)
                .distinct()
                .count()
            ),
        })

    @action(methods=('GET',), detail=False)
    def contacts(self, request, *args, **kwargs):
        slz = ContactRequestSerializer(data=request.GET)
        slz.is_valid(raise_exception=True)
        return self.paginated_response(
            self.filter_queryset(self.get_queryset()),
        )

    def list(self, request, *args, **kwargs):
        slz = self.get_serializer(instance=request.user)
        return self.response_ok(slz.data)

    def put(self, request, *args, **kwargs):
        user = request.user
        slz = self.get_serializer(data=request.data)
        slz.is_valid(raise_exception=True)
        service = UserService(
            user=user,
            instance=user,
            is_superuser=request.is_superuser,
            auth_type=request.token_type,
        )
        try:
            user = service.partial_update(**slz.validated_data)
        except UserServiceException as ex:
            raise_validation_error(message=ex.message)
        return self.response_ok(UserSerializer(instance=user).data)
