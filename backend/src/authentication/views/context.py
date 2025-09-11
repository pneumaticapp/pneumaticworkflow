from django.contrib.auth import get_user_model
from rest_framework.generics import (
    ListAPIView,
)
from src.generics.mixins.views import (
    BaseResponseMixin
)
from src.authentication.serializers import (
    ContextUserSerializer,
)
from src.generics.permissions import (
    IsAuthenticated
)


UserModel = get_user_model()


class ContextUserView(
    ListAPIView,
    BaseResponseMixin
):

    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        data = ContextUserSerializer(
            request.user,
            context={'is_supermode': request.is_superuser}
        ).data
        return self.response_ok(data)
