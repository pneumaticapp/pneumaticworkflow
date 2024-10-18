from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth import get_user_model

from rest_framework.generics import ListAPIView
from rest_framework.pagination import LimitOffsetPagination

from pneumatic_backend.accounts.permissions import (
    ExpiredSubscriptionPermission,
)
from pneumatic_backend.processes.filters import RecentTaskFilter
from pneumatic_backend.processes.models import (
    Task,
)
from pneumatic_backend.processes.serializers.task import (
    RecentTaskSerializer,
)
from pneumatic_backend.generics.permissions import UserIsAuthenticated


UserModel = get_user_model()


class OneItemPagination(LimitOffsetPagination):
    def get_limit(self, request):
        return 1

    def get_offset(self, request):
        return 0


class RecentTaskView(ListAPIView):

    """ Using by Zapier """

    serializer_class = RecentTaskSerializer
    permission_classes = (
        UserIsAuthenticated,
        ExpiredSubscriptionPermission,
    )
    pagination_class = OneItemPagination
    filter_backends = (DjangoFilterBackend, )
    filterset_class = RecentTaskFilter

    def get_queryset(self):
        return Task.objects.on_account(
            self.request.user.account_id
        ).started().order_by('-date_started')
