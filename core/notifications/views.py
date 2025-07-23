from rest_framework.decorators import action
from rest_framework.generics import (
    CreateAPIView,
    DestroyAPIView,
)
from rest_framework.viewsets import GenericViewSet
from pneumatic_backend.generics.permissions import UserIsAuthenticated
from pneumatic_backend.notifications.permissions import PushPermission
from pneumatic_backend.generics.mixins.views import CustomViewSetMixin
from pneumatic_backend.notifications.models import Device
from pneumatic_backend.notifications.serializers import DeviceSerializer


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

    def create(self, request, *args, **kwargs):
        user_agent = request.headers.get(
            'User-Agent',
            request.META.get('HTTP_USER_AGENT')
        )
        serializer = self.get_serializer(
            data={
                'user': request.user.id,
                'description': user_agent,
                'is_app': user_agent.startswith('Dart'),
                **request.data
            }
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return self.response_ok(serializer.data)


class IosViewSet(
    CustomViewSetMixin,
    GenericViewSet,
):
    permission_classes = (
        UserIsAuthenticated,
        PushPermission,
    )

    @action(methods=('POST',), url_path='reset-push-counter', detail=False)
    def reset_push_counter(self, request, *args, **kwargs):
        user = request.user
        user.user_notifications.update(count_unread_push_in_ios_app=0)
        return self.response_ok()
