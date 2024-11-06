from django.http import Http404
from django.contrib.auth import get_user_model
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import AllowAny
from rest_framework.viewsets import GenericViewSet
from pneumatic_backend.accounts.models import UserInvite
from pneumatic_backend.accounts.permissions import (
    UserIsAdminOrAccountOwner,
    ExpiredSubscriptionPermission,
)
from pneumatic_backend.accounts.serializers.user_invites import (
    UserInviteSerializer,
    InviteUsersSerializer,
    AcceptInviteSerializer,
    TokenSerializer,
)
from pneumatic_backend.accounts.tokens import (
    InviteToken,
)
from pneumatic_backend.authentication.enums import AuthTokenType
from pneumatic_backend.authentication.permissions import PrivateApiPermission
from pneumatic_backend.authentication.services import AuthService
from pneumatic_backend.accounts.throttling import (
    InvitesTokenThrottle
)
from pneumatic_backend.generics.permissions import (
    UserIsAuthenticated,
    PaymentCardPermission,
)
from pneumatic_backend.accounts.services.exceptions import (
    UsersLimitInvitesException,
    AlreadyAcceptedInviteException,
    UserNotFoundException,
    UserIsPerformerException,
    InvalidOrExpiredToken,
    AlreadyRegisteredException,
)
from pneumatic_backend.accounts.services import (
    UserInviteService
)
from pneumatic_backend.utils.validation import raise_validation_error
from pneumatic_backend.analytics.mixins import (
    BaseIdentifyMixin,
)
from pneumatic_backend.generics.mixins.views import (
    CustomViewSetMixin
)
from pneumatic_backend.accounts.services.user import UserService

UserModel = get_user_model()


class UserInviteViewSet(
    CustomViewSetMixin,
    GenericViewSet,
    BaseIdentifyMixin
):
    permission_classes = (
        UserIsAuthenticated,
        UserIsAdminOrAccountOwner,
        PrivateApiPermission,
        ExpiredSubscriptionPermission,
        PaymentCardPermission,
    )
    action_serializer_classes = {
        'create': InviteUsersSerializer,
        'accept': AcceptInviteSerializer,
        'token': TokenSerializer,
    }

    def get_queryset(self):
        queryset = UserInvite.objects.all()
        if self.action == 'decline':
            account_id = self.request.user.account_id
            queryset = queryset.on_account(account_id).not_accepted()
        elif self.action == 'list':
            account_id = self.request.user.account_id
            queryset = queryset.on_account(account_id).order_by_date_desc()
        elif self.action == 'accept':
            queryset = queryset.pending()
        elif self.action == 'retrieve':
            queryset = queryset.pending()
        return queryset

    @property
    def throttle_classes(self):
        if self.action == 'create':
            return (
                InvitesTokenThrottle,
            )
        else:
            return ()

    def get_permissions(self):
        if self.action in ('retrieve', 'token'):
            return (
                PrivateApiPermission(),
            )
        elif self.action == 'accept':
            return (
                AllowAny(),
            )
        elif self.action == 'decline':
            return (
                UserIsAuthenticated(),
                UserIsAdminOrAccountOwner(),
                PaymentCardPermission(),
            )
        elif self.action == 'resend':
            return (
                UserIsAuthenticated(),
                UserIsAdminOrAccountOwner(),
                PrivateApiPermission(),
                PaymentCardPermission(),
            )
        return super(UserInviteViewSet, self).get_permissions()

    def get_serializer_context(self, **kwargs):
        context = super().get_serializer_context(**kwargs)
        if self.action == 'create':
            context['account_id'] = self.request.user.account.id
        return context

    def create(self, request):
        slz = self.get_serializer(data=request.data)
        slz.is_valid(raise_exception=True)
        service = UserInviteService(
            is_superuser=request.is_superuser,
            request_user=request.user,
            current_url=request.META.get('HTTP_X_CURRENT_URL')
        )
        try:
            service.invite_users(data=slz.validated_data['users'])
        except AlreadyAcceptedInviteException as ex:
            return self.response_ok({
                'already_accepted': ex.invites_data
            })
        except UsersLimitInvitesException as ex:
            raise_validation_error(message=ex.message)
        else:
            return self.response_ok({'already_accepted': ()})

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        invite_status = self.request.query_params.get('status', None)
        if invite_status is not None:
            queryset = queryset.with_status(invite_status)

        serializer = UserInviteSerializer(queryset, many=True)
        return self.response_ok(serializer.data)

    @action(detail=False, methods=['get'])
    def token(self, request):
        slz = self.get_serializer(data=request.GET)
        slz.is_valid(raise_exception=True)
        try:
            token = InviteToken(token=slz.validated_data['token'])
        except (
            InvalidOrExpiredToken,
            AlreadyRegisteredException,
            AlreadyAcceptedInviteException
        ) as ex:
            raise_validation_error(message=ex.message)
        else:
            self.identify(token.user)
            self.group(token.user)
            return self.response_ok({'id': token.invite.id})

    def retrieve(self, request, pk=None):
        invite = self.get_object()
        data = UserInviteSerializer(instance=invite).data
        return self.response_ok(data)

    @action(detail=True, methods=['post'])
    def accept(self, request, **kwargs):
        slz = self.get_serializer(data=request.data)
        slz.is_valid(raise_exception=True)
        service = UserInviteService(
            current_url=request.META.get('HTTP_X_CURRENT_URL'),
            is_superuser=False,
            auth_type=AuthTokenType.USER
        )
        try:
            user = service.accept(
                invite=self.get_object(),
                **slz.validated_data
            )
        except AlreadyRegisteredException as ex:
            raise_validation_error(message=ex.message)
        else:
            token = AuthService.get_auth_token(
                user=user,
                user_agent=request.headers.get(
                    'User-Agent',
                    request.META.get('HTTP_USER_AGENT')
                ),
                user_ip=request.META.get('HTTP_X_REAL_IP'),
            )
            return self.response_ok({'token': token})

    @action(detail=False, methods=['post'])
    def decline(self, request):
        queryset = self.get_queryset()
        invite = get_object_or_404(queryset, pk=request.data.get('invite_id'))
        try:
            UserService.deactivate(invite.invited_user)
        except UserIsPerformerException as ex:
            raise_validation_error(message=ex.message)
        return self.response_ok()

    @action(detail=True, methods=['post'])
    def resend(self, request, pk, *args, **kwargs):
        service = UserInviteService(
            is_superuser=request.is_superuser,
            request_user=request.user,
            current_url=request.META.get('HTTP_X_CURRENT_URL')
        )
        try:
            service.resend_invite(user_id=pk)
        except AlreadyAcceptedInviteException as ex:
            raise_validation_error(message=ex.message)
        except UserNotFoundException:
            raise Http404
        return self.response_ok()
