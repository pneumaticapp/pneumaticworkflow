from typing import List, Optional

from django.contrib.auth import get_user_model
from rest_framework.decorators import action
from rest_framework.generics import (
    CreateAPIView,
)
from rest_framework.mixins import (
    DestroyModelMixin,
    ListModelMixin,
)
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.viewsets import GenericViewSet

from src.accounts.enums import (
    NotificationStatus,
)
from src.accounts.filters import (
    NotificationFilter,
)
from src.accounts.permissions import (
    BillingPlanPermission,
    ExpiredSubscriptionPermission,
)
from src.accounts.serializers.notifications import (
    NotificationsSerializer,
)
from src.generics.filters import PneumaticFilterBackend
from src.generics.mixins.views import (
    BaseResponseMixin,
    CustomViewSetMixin,
)
from src.generics.permissions import (
    UserIsAuthenticated,
)

UserModel = get_user_model()


class NotificationsViewSet(
    CustomViewSetMixin,
    ListModelMixin,
    DestroyModelMixin,
    GenericViewSet,
):
    pagination_class = LimitOffsetPagination
    serializer_class = NotificationsSerializer
    filterset_class = NotificationFilter
    filter_backends = [PneumaticFilterBackend]

    def get_permissions(self):
        if self.action in 'destroy':
            return (
                UserIsAuthenticated(),
                BillingPlanPermission(),
                ExpiredSubscriptionPermission(),
            )
        return (
            UserIsAuthenticated(),
        )

    def get_queryset(self):
        return self.request.user.notifications

    def prefetch_queryset(
        self,
        queryset,
        extra_fields: Optional[List[str]] = None,
    ):
        if self.action == 'list':
            extra_fields = ('task__workflow', 'comment')
        return super().prefetch_queryset(
            queryset=queryset,
            extra_fields=extra_fields,
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

    # TODO Move to NotificationsViewSet

    permission_classes = (
        UserIsAuthenticated,
        ExpiredSubscriptionPermission,
        BillingPlanPermission,
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
