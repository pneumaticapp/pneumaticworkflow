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
    UserWebsocketSerializer,
)
from src.analysis.mixins import BaseIdentifyMixin
from src.analysis.services import AnalyticService
from src.generics.filters import PneumaticFilterBackend
from src.generics.mixins.views import (
    CustomViewSetMixin,
)
from src.generics.permissions import (
    IsAuthenticated,
    UserIsAuthenticated,
)
from src.notifications.tasks import send_user_updated_notification
from src.payment.stripe.exceptions import StripeServiceException
from src.payment.stripe.service import StripeService
from src.processes.enums import FieldType
from src.processes.models.workflows.fields import TaskField
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
        slz = self.get_serializer(
            instance=request.user,
            data=request.data,
            partial=False,
        )
        slz.is_valid(raise_exception=True)

        old_first_name = request.user.first_name
        old_last_name = request.user.last_name

        user = slz.save()

        if (
            old_first_name != user.first_name or
            old_last_name != user.last_name
        ):
            TaskField.objects.filter(
                type=FieldType.USER,
                user_id=user.id,
            ).update(value=user.name)

        if (
            not user.account.is_tenant
            and user.is_account_owner
            and user.account.billing_sync
        ):
            try:
                service = StripeService(
                    user=user,
                    auth_type=self.request.token_type,
                    is_superuser=self.request.is_superuser,
                )
                service.update_customer()
            except StripeServiceException as ex:
                raise_validation_error(message=ex.message)

        if slz.data.get('is_digest_subscriber') is False:
            AnalyticService.users_digest(
                user=user,
                auth_type=self.request.token_type,
                is_superuser=self.request.is_superuser,
            )
        send_user_updated_notification.delay(
            logging=user.account.log_api_requests,
            account_id=user.account.id,
            user_data=UserWebsocketSerializer(user).data,
        )
        self.identify(user)
        return self.response_ok(slz.data)
