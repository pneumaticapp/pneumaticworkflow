from typing import List, Optional

from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema, extend_schema_view
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
from src.accounts.models import Notification
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
from src.openapi.permission_docs import (
    ACCESS_NOTIFICATIONS_DESTROY,
    ACCESS_NOTIFICATIONS_LIST,
)
from src.openapi.serializers import CountResponseSerializer
from src.openapi.responses import EMPTY, FORBIDDEN, NOT_FOUND, UNAUTHORIZED
from src.openapi.internal_serializers import NotificationsReadRequestSerializer

UserModel = get_user_model()


@extend_schema_view(
    list=extend_schema(
        tags=['Notifications'],
        summary='List notifications',
        description=ACCESS_NOTIFICATIONS_LIST,
        responses={
            200: NotificationsSerializer(many=True),
            401: UNAUTHORIZED,
            403: FORBIDDEN,
        },
    ),
    destroy=extend_schema(
        tags=['Notifications'],
        summary='Delete notification',
        description=ACCESS_NOTIFICATIONS_DESTROY,
        responses={
            204: EMPTY,
            401: UNAUTHORIZED,
            403: FORBIDDEN,
            404: NOT_FOUND,
        },
    ),
)
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
        if getattr(self, 'swagger_fake_view', False):
            return Notification.objects.none()
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

    @extend_schema(
        tags=['Notifications'],
        summary='Count notifications',
        description=ACCESS_NOTIFICATIONS_LIST,
        responses={
            200: CountResponseSerializer,
            401: UNAUTHORIZED,
            403: FORBIDDEN,
        },
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

    @extend_schema(
        tags=['Notifications'],
        summary='Mark current user notifications read',
        description=(
            'Requires a non-guest user, a billing plan and an unexpired '
            'subscription. Marks only unread notifications belonging to '
            'the current user. Omitted/empty notifications makes no change.'
        ),
        request=NotificationsReadRequestSerializer,
        responses={204: EMPTY, 401: UNAUTHORIZED, 403: FORBIDDEN},
    )
    def post(self, request, *args, **kwargs):
        notifications_ids = request.data.get('notifications')
        if notifications_ids:
            queryset = self.get_queryset()
            queryset.by_ids(notifications_ids).update(
                status=NotificationStatus.READ,
            )
        return self.response_ok()
