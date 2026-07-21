from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework.decorators import action
from rest_framework.generics import (
    CreateAPIView,
    DestroyAPIView,
)
from rest_framework.viewsets import GenericViewSet

from src.generics.mixins.views import CustomViewSetMixin
from src.generics.permissions import UserIsAuthenticated
from src.notifications.models import Device
from src.notifications.permissions import PushPermission
from src.notifications.serializers import DeviceSerializer
from src.openapi import (
    ACCESS_PUSH,
    EMPTY,
    FORBIDDEN,
    NOT_FOUND,
    UNAUTHORIZED,
    VALIDATION_ERROR,
)


@extend_schema_view(
    destroy=extend_schema(
        tags=['Notifications'],
        summary='Unregister push device',
        description=ACCESS_PUSH,
        responses={
            204: EMPTY,
            401: UNAUTHORIZED,
            403: FORBIDDEN,
            404: NOT_FOUND,
        },
    ),
)
class DeviceViewSet(
    CustomViewSetMixin,
    CreateAPIView,
    DestroyAPIView,
    GenericViewSet,
):
    permission_classes = (
        UserIsAuthenticated,
        PushPermission,
    )
    serializer_class = DeviceSerializer

    lookup_field = 'token'

    def get_queryset(self):
        return Device.objects.by_user(self.request.user)

    @extend_schema(
        tags=['Notifications'],
        summary='Register push device',
        description=ACCESS_PUSH,
        request=DeviceSerializer,
        responses={
            200: DeviceSerializer,
            400: VALIDATION_ERROR,
            401: UNAUTHORIZED,
            403: FORBIDDEN,
        },
    )
    def create(self, request, *args, **kwargs):
        user_agent = request.headers.get(
            'User-Agent',
            request.META.get('HTTP_USER_AGENT'),
        )
        serializer = self.get_serializer(
            data={
                'user': request.user.id,
                'description': user_agent,
                'is_app': user_agent.startswith('Dart'),
                **request.data,
            },
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return self.response_ok(serializer.data)


class IosViewSet(
    CustomViewSetMixin,
    GenericViewSet,
):
    serializer_class = DeviceSerializer
    permission_classes = (
        UserIsAuthenticated,
        PushPermission,
    )

    @extend_schema(
        tags=['Notifications'],
        summary='Reset iOS push counter',
        description=ACCESS_PUSH,
        responses={
            200: EMPTY,
            401: UNAUTHORIZED,
            403: FORBIDDEN,
        },
    )
    @action(methods=('POST',), url_path='reset-push-counter', detail=False)
    def reset_push_counter(self, request, *args, **kwargs):
        user = request.user
        user.user_notifications.update(count_unread_push_in_ios_app=0)
        return self.response_ok()
