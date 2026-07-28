from django.db import IntegrityError
from rest_framework.viewsets import GenericViewSet

from src.accounts.permissions import (
    BillingPlanPermission,
    ExpiredSubscriptionPermission,
    UserIsAdminOrAccountOwner,
    UsersOverlimitedPermission,
)
from src.ai.messages import MSG_AI_0001
from src.ai.models import AIAgent
from src.ai.permissions import AiPerformersEnabledPermission
from src.ai.serializers import AIAgentSerializer
from src.generics.mixins.views import CustomViewSetMixin
from src.generics.permissions import UserIsAuthenticated
from src.utils.validation import raise_validation_error


class AIAgentViewSet(
    CustomViewSetMixin,
    GenericViewSet,
):

    serializer_class = AIAgentSerializer

    def get_permissions(self):
        permissions = (
            UserIsAuthenticated(),
            ExpiredSubscriptionPermission(),
            BillingPlanPermission(),
            UsersOverlimitedPermission(),
            AiPerformersEnabledPermission(),
        )
        if self.action in ('list', 'retrieve'):
            return permissions
        return (*permissions, UserIsAdminOrAccountOwner())

    def get_queryset(self):
        return AIAgent.objects.on_account(self.request.user.account_id)

    def list(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_queryset(), many=True)
        return self.response_ok(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_object())
        return self.response_ok(serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            agent = serializer.save(account=request.user.account)
        except IntegrityError:
            raise_validation_error(message=MSG_AI_0001)
        return self.response_created(
            self.get_serializer(agent).data,
        )

    def partial_update(self, request, *args, **kwargs):
        agent = self.get_object()
        serializer = self.get_serializer(
            agent,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        try:
            agent = serializer.save()
        except IntegrityError:
            raise_validation_error(message=MSG_AI_0001)
        return self.response_ok(
            self.get_serializer(agent).data,
        )

    def destroy(self, request, *args, **kwargs):
        agent = self.get_object()
        agent.delete()
        return self.response_ok()
