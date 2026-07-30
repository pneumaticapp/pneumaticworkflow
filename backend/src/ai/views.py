from django.db import IntegrityError
from rest_framework.generics import GenericAPIView
from rest_framework.viewsets import GenericViewSet

from src.accounts.permissions import (
    BillingPlanPermission,
    ExpiredSubscriptionPermission,
    UserIsAdminOrAccountOwner,
    UsersOverlimitedPermission,
)
from src.ai.clients.key_verification import verify_api_key
from src.ai.messages import MSG_AI_0001, MSG_AI_0003
from src.ai.models import AIAgent, AIProviderConnection
from src.ai.permissions import (
    AiPerformersDeployedPermission,
    AiPerformersEnabledPermission,
)
from src.ai.providers import get_provider_connection
from src.ai.serializers import (
    AIAgentSerializer,
    AIProviderConnectionSerializer,
)
from src.generics.mixins.views import BaseResponseMixin, CustomViewSetMixin
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


class AIConnectionView(
    GenericAPIView,
    BaseResponseMixin,
):

    """ Singleton per account: an account owner switches AI
        performers on by saving a provider API key here.
        Gated on the deployment flag only — the connection must be
        manageable while the account-level feature is still off. """

    serializer_class = AIProviderConnectionSerializer
    permission_classes = (
        UserIsAuthenticated,
        ExpiredSubscriptionPermission,
        BillingPlanPermission,
        UsersOverlimitedPermission,
        AiPerformersDeployedPermission,
        UserIsAdminOrAccountOwner,
    )

    def get(self, request, *args, **kwargs):
        connection = get_provider_connection(request.user.account)
        if connection is None:
            return self.response_ok({'connection': None})
        return self.response_ok(
            {'connection': self.get_serializer(connection).data},
        )

    def put(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        base_url = (
            serializer.validated_data.get('base_url')
            or AIProviderConnection._meta.get_field('base_url').default
        )
        api_key = serializer.validated_data['api_key']
        if verify_api_key(base_url=base_url, api_key=api_key) is False:
            raise_validation_error(message=MSG_AI_0003)
        account = request.user.account
        for stale in AIProviderConnection.objects.on_account(account.id):
            stale.delete()
        connection = AIProviderConnection.objects.create(
            account=account,
            name='OpenRouter',
            base_url=base_url,
            api_key=api_key,
        )
        return self.response_ok(
            {'connection': self.get_serializer(connection).data},
        )

    def delete(self, request, *args, **kwargs):
        account = request.user.account
        for connection in AIProviderConnection.objects.on_account(account.id):
            connection.delete()
        return self.response_ok({'connection': None})
