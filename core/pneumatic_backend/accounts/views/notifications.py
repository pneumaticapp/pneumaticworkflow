from typing import List
from django.contrib.auth import get_user_model
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.generics import (
    CreateAPIView,
)
from rest_framework.viewsets import GenericViewSet
from rest_framework.mixins import (
    ListModelMixin,
    DestroyModelMixin,
)
from pneumatic_backend.accounts.enums import (
    NotificationStatus,
)
from pneumatic_backend.accounts.filters import (
    NotificationFilter,
)
from pneumatic_backend.accounts.permissions import (
    ExpiredSubscriptionPermission,
)
from pneumatic_backend.accounts.serializers.notifications import (
    NotificationsSerializer,
)
from pneumatic_backend.generics.filters import PneumaticFilterBackend
from pneumatic_backend.generics.permissions import (
    UserIsAuthenticated,
    PaymentCardPermission,
)
from pneumatic_backend.generics.mixins.views import (
    CustomViewSetMixin,
    BaseResponseMixin,
)


UserModel = get_user_model()


class NotificationsViewSet(
    CustomViewSetMixin,
    ListModelMixin,
    DestroyModelMixin,
    GenericViewSet
):
    pagination_class = LimitOffsetPagination
    permission_classes = (
        ExpiredSubscriptionPermission,
        UserIsAuthenticated,
        PaymentCardPermission,
    )
    serializer_class = NotificationsSerializer
    filterset_class = NotificationFilter
    filter_backends = [OrderingFilter, PneumaticFilterBackend]
    ordering_fields = ['datetime']
    ordering = ['-datetime']

    def get_queryset(self):
        return self.request.user.notifications

    def prefetch_queryset(self, queryset, extra_fields: List[str] = None):
        if self.action == 'list':
            extra_fields = ('task__workflow', 'comment')
        return super().prefetch_queryset(
            queryset=queryset,
            extra_fields=extra_fields
        )

    @action(methods=['GET'], detail=False)
    def count(self, request):
        queryset = self.get_queryset()
        queryset = self.filter_queryset(queryset)
        return self.response_ok(data={'count': queryset.count()})


class NotificationsReadView(
    CreateAPIView,
    BaseResponseMixin,
):
    permission_classes = (
        ExpiredSubscriptionPermission,
        UserIsAuthenticated,
        PaymentCardPermission,
    )

    def get_queryset(self):
        return self.request.user.notifications.exclude_read()

    def post(self, request, *args, **kwargs):
        notifications_ids = request.data.get('notifications')
        if notifications_ids:
            queryset = self.get_queryset()
            queryset.by_ids(notifications_ids).update(
                status=NotificationStatus.READ,
            )
        return self.response_ok()
