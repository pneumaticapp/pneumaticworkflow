from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework.decorators import action
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.viewsets import GenericViewSet
from pneumatic_backend.accounts.filters import (
    ContactsFilterSet,
)
from pneumatic_backend.accounts.models import (
    Contact,
)
from pneumatic_backend.accounts.serializers.user import (
    ContactRequestSerializer,
    ContactResponseSerializer,
    UserSerializer,
)
from pneumatic_backend.generics.filters import PneumaticFilterBackend
from pneumatic_backend.generics.mixins.views import (
    CustomViewSetMixin,
)
from pneumatic_backend.processes.models import (
    Task
)
from pneumatic_backend.accounts.permissions import (
    ExpiredSubscriptionPermission
)
from pneumatic_backend.generics.permissions import (
    IsAuthenticated,
    UserIsAuthenticated,
    PaymentCardPermission,
)
from pneumatic_backend.analytics.mixins import BaseIdentifyMixin
from pneumatic_backend.analytics.services import AnalyticService
from pneumatic_backend.utils.validation import raise_validation_error
from pneumatic_backend.payment.stripe.service import StripeService
from pneumatic_backend.payment.stripe.exceptions import StripeServiceException

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
                PaymentCardPermission(),
                ExpiredSubscriptionPermission(),
            )
        elif self.action == 'list':
            return (
                IsAuthenticated(),
                PaymentCardPermission(),
            )
        else:
            return (
                UserIsAuthenticated(),
                PaymentCardPermission(),
            )

    def get_queryset(self):
        if self.action == 'contacts':
            return Contact.objects.by_user(
                user_id=self.request.user.id
            ).active()

    @action(methods=('GET',), detail=False)
    def counters(self, request, *args, **kwargs):
        return self.response_ok({
            'tasks_count': Task.objects.using(
                settings.REPLICA
            ).active_for_user(request.user.id).count()
        })

    @action(methods=('GET',), detail=False)
    def contacts(self, request, *args, **kwargs):
        slz = ContactRequestSerializer(data=request.GET)
        slz.is_valid(raise_exception=True)
        return self.paginated_response(
            self.filter_queryset(self.get_queryset())
        )

    def list(self, request, *args, **kwargs):
        slz = self.get_serializer(instance=request.user)
        return self.response_ok(slz.data)

    def put(self, request, *args, **kwargs):
        slz = self.get_serializer(
            instance=request.user,
            data=request.data,
            partial=False
        )
        slz.is_valid(raise_exception=True)
        user = slz.save()
        if (
            not user.account.is_tenant
            and user.is_account_owner
            and user.account.billing_sync
        ):
            try:
                service = StripeService(
                    user=user,
                    auth_type=self.request.token_type,
                    is_superuser=self.request.is_superuser
                )
                service.update_customer()
            except StripeServiceException as ex:
                raise_validation_error(message=ex.message)

        if slz.data.get('is_digest_subscriber') is False:
            AnalyticService.users_digest(
                user=user,
                auth_type=self.request.token_type,
                is_superuser=self.request.is_superuser
            )
        self.identify(user)
        return self.response_ok(slz.data)
