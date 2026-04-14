from django.contrib.auth import get_user_model
from rest_framework.decorators import action
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.viewsets import GenericViewSet

from src.accounts.filters import (
    ContactsFilterSet,
)
from src.accounts.messages import MSG_A_0052
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
    VacationActivateSerializer,
)
from src.accounts.services.exceptions import (
    UserServiceException,
)
from src.accounts.services.user import UserService
from src.accounts.services.vacation import (
    VacationDelegationService,
)
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
        'activate_vacation': VacationActivateSerializer,
    }

    def get_serializer_context(self, **kwargs):
        context = super().get_serializer_context(**kwargs)
        context['account'] = self.request.user.account
        context['user'] = self.request.user
        return context

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
        if self.action in {
            'activate_vacation',
            'deactivate_vacation',
        }:
            return (
                UserIsAuthenticated(),
                BillingPlanPermission(),
                ExpiredSubscriptionPermission(),
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
            user = service.partial_update(
                **slz.validated_data,
                force_save=True,
            )
        except UserServiceException as ex:
            raise_validation_error(message=ex.message)
        return self.response_ok(
            UserSerializer(instance=user).data,
        )

    @action(
        detail=False,
        methods=('post',),
        url_path='activate-vacation',
    )
    def activate_vacation(self, request, *args, **kwargs):
        user = request.user
        slz = self.get_serializer(
            data=request.data,
            extra_fields={
                'vacation_user': user,
            },
        )
        slz.is_valid(raise_exception=True)
        data = slz.validated_data
        service = VacationDelegationService(user=user)
        user = service.activate(
            substitute_user_ids=data['substitute_user_ids'],
            absence_status=data['absence_status'],
            vacation_start_date=(data.get('vacation_start_date')),
            vacation_end_date=(data.get('vacation_end_date')),
        )
        return self.response_ok(UserSerializer(instance=user).data)

    @action(
        detail=False,
        methods=('post',),
        url_path='deactivate-vacation',
    )
    def deactivate_vacation(self, request, *args, **kwargs):
        user = request.user
        if not user.is_absent:
            raise_validation_error(
                message=MSG_A_0052,
            )
        service = VacationDelegationService(user=user)
        user = service.deactivate()
        return self.response_ok(UserSerializer(instance=user).data)
