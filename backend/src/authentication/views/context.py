from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema
from rest_framework.generics import (
    ListAPIView,
)

from src.authentication.serializers import (
    ContextUserSerializer,
)
from src.generics.mixins.views import (
    BaseResponseMixin,
)
from src.generics.permissions import (
    IsAuthenticated,
)
from src.openapi import FORBIDDEN, UNAUTHORIZED

UserModel = get_user_model()


class ContextUserView(
    ListAPIView,
    BaseResponseMixin,
):

    permission_classes = (IsAuthenticated,)

    @extend_schema(
        tags=['Auth'],
        summary='Get current session context',
        responses={
            200: ContextUserSerializer,
            401: UNAUTHORIZED,
            403: FORBIDDEN,
        },
    )
    def get(self, request, *args, **kwargs):
        data = ContextUserSerializer(
            request.user,
            context={'is_supermode': request.is_superuser},
        ).data
        return self.response_ok(data)
