from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
)
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
from src.openapi.permission_docs import ACCESS_PUSH
from src.openapi.responses import (
    EMPTY,
    FIELD_VALIDATION_ERROR,
    FORBIDDEN,
    NOT_FOUND,
    UNAUTHORIZED,
)
from src.openapi.helpers import with_access_text
from src.openapi.internal_serializers import (
    DeviceRegistrationRequestSerializer,
)


@extend_schema_view(
    destroy=extend_schema(
        tags=['Notifications'],
        summary='Unregister push device',
        description=ACCESS_PUSH,
        parameters=[OpenApiParameter(
            name='token',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.PATH,
            required=True,
            description='Firebase device token registered by this user.',
        )],
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
        description=with_access_text(
            'Registers or updates the Firebase token. user defaults to the '
            'current user; description and is_app default from User-Agent '
            '(Dart prefix identifies an app). Explicit body values override '
            'these defaults. The token is used in the unregister path.',
            ACCESS_PUSH,
        ),
        request=DeviceRegistrationRequestSerializer,
        responses={
            200: DeviceSerializer,
            400: OpenApiResponse(
                response=FIELD_VALIDATION_ERROR.response,
                description='Device field validation errors.',
                examples=[OpenApiExample(
                    'Missing device token',
                    value={'token': ['This field is required.']},
                    response_only=True,
                )],
            ),
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
        request=None,
        responses={
            204: EMPTY,
            401: UNAUTHORIZED,
            403: FORBIDDEN,
        },
    )
    @action(methods=('POST',), url_path='reset-push-counter', detail=False)
    def reset_push_counter(self, request, *args, **kwargs):
        user = request.user
        user.user_notifications.update(count_unread_push_in_ios_app=0)
        return self.response_ok()
