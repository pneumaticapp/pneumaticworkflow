from django.contrib.auth import get_user_model
from django.http import Http404
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    extend_schema,
)
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import AllowAny
from rest_framework.viewsets import GenericViewSet

from src.accounts.models import UserInvite
from src.accounts.enums import UserInviteStatus
from src.accounts.permissions import (
    BillingPlanPermission,
    ExpiredSubscriptionPermission,
    UserIsAdminOrAccountOwner,
)
from src.accounts.serializers.user_invites import (
    AcceptInviteSerializer,
    InviteUsersSerializer,
    TokenSerializer,
    UserInviteSerializer,
)
from src.accounts.services.exceptions import (
    AlreadyAcceptedInviteException,
    AlreadyRegisteredException,
    InvalidOrExpiredToken,
    UserNotFoundException,
    UsersLimitInvitesException,
)
from src.accounts.services.user_invite import UserInviteService
from src.accounts.throttling import (
    InvitesTokenThrottle,
)
from src.accounts.tokens import (
    InviteToken,
)
from src.analysis.mixins import (
    BaseIdentifyMixin,
)
from src.authentication.enums import AuthTokenType
from src.authentication.permissions import PrivateApiPermission
from src.authentication.services.user_auth import AuthService
from src.generics.mixins.views import (
    CustomViewSetMixin,
)
from src.generics.permissions import (
    UserIsAuthenticated,
)
from src.openapi.permission_docs import ACCESS_ADMIN_BASE
from src.openapi.serializers import AuthTokenResponseSerializer
from src.openapi.responses import (
    EMPTY,
    FORBIDDEN,
    NOT_FOUND,
    UNAUTHORIZED,
    VALIDATION_ERROR,
)
from src.openapi.helpers import with_access_text
from src.openapi.internal_serializers import (
    DeclineInviteRequestSerializer,
    InviteIdResponseSerializer,
    InviteUsersResponseSerializer,
)
from src.openapi.helpers import unpaginated_schema
from src.utils.validation import raise_validation_error

UserModel = get_user_model()


class UserInviteViewSet(
    CustomViewSetMixin,
    GenericViewSet,
    BaseIdentifyMixin,
):

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
        elif self.action in {'accept', 'retrieve'}:
            queryset = queryset.pending()
        return queryset

    @property
    def throttle_classes(self):
        if self.action == 'create':
            return (
                InvitesTokenThrottle,
            )
        return ()

    def get_permissions(self):
        if self.action in ('retrieve', 'token'):
            return (
                PrivateApiPermission(),
            )
        if self.action == 'accept':
            return (
                AllowAny(),
            )
        return (
            UserIsAuthenticated(),
            BillingPlanPermission(),
            ExpiredSubscriptionPermission(),
            UserIsAdminOrAccountOwner(),
        )

    def get_serializer_context(self, **kwargs):
        context = super().get_serializer_context(**kwargs)
        if self.action == 'create':
            context['account_id'] = self.request.user.account.id
        return context

    @extend_schema(
        tags=['Accounts'],
        summary='Invite users to the account',
        description=with_access_text(
            'Sends invitations for users in the request. Each user must '
            'include invited_from (or its legacy alias type). All group IDs '
            'must belong to the account. already_accepted reports users '
            'whose invitations were already accepted; it is otherwise [].',
            ACCESS_ADMIN_BASE,
        ),
        request=InviteUsersSerializer,
        responses={
            200: InviteUsersResponseSerializer,
            400: VALIDATION_ERROR,
            401: UNAUTHORIZED,
            403: FORBIDDEN,
        },
        examples=[OpenApiExample(
            'Invite a colleague',
            value={'users': [{
                'email': 'colleague@example.com',
                'invited_from': 'email',
                'first_name': 'Jane',
            }]},
            request_only=True,
        )],
    )
    def create(self, request):
        slz = self.get_serializer(data=request.data)
        slz.is_valid(raise_exception=True)
        service = UserInviteService(
            is_superuser=request.is_superuser,
            request_user=request.user,
            current_url=request.META.get('HTTP_X_CURRENT_URL'),
        )
        try:
            service.invite_users(data=slz.validated_data['users'])
        except AlreadyAcceptedInviteException as ex:
            return self.response_ok({
                'already_accepted': ex.invites_data,
            })
        except UsersLimitInvitesException as ex:
            raise_validation_error(message=ex.message)
        else:
            return self.response_ok({'already_accepted': ()})

    @unpaginated_schema
    @extend_schema(
        tags=['Accounts'],
        summary='List account invitations',
        description=with_access_text(
            'Returns a flat array ordered newest first. The optional status '
            'filter uses the invitation status; there is no pagination.',
            ACCESS_ADMIN_BASE,
        ),
        parameters=[OpenApiParameter(
            name='status',
            location=OpenApiParameter.QUERY,
            type=OpenApiTypes.STR,
            enum=[choice[0] for choice in UserInviteStatus.CHOICES],
        )],
        responses={
            200: UserInviteSerializer(many=True),
            401: UNAUTHORIZED,
            403: FORBIDDEN,
        },
    )
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        invite_status = self.request.query_params.get('status', None)
        if invite_status is not None:
            queryset = queryset.with_status(invite_status)

        serializer = UserInviteSerializer(queryset, many=True)
        return self.response_ok(serializer.data)

    @extend_schema(
        tags=['Accounts'],
        summary='Resolve an invitation email token',
        description=(
            'Internal frontend operation. No user session is required, but '
            'private API source-IP restrictions apply. Validates the signed '
            'invite token and returns the invite record ID. Expired, '
            'already accepted or already registered invitations fail.'
        ),
        auth=[],
        parameters=[TokenSerializer],
        responses={
            200: InviteIdResponseSerializer,
            400: VALIDATION_ERROR,
            401: UNAUTHORIZED,
            403: FORBIDDEN,
        },
    )
    @action(detail=False, methods=['get'])
    def token(self, request):
        slz = self.get_serializer(data=request.GET)
        slz.is_valid(raise_exception=True)
        try:
            token = InviteToken(token=slz.validated_data['token'])
        except (
            InvalidOrExpiredToken,
            AlreadyRegisteredException,
            AlreadyAcceptedInviteException,
        ) as ex:
            raise_validation_error(message=ex.message)
        else:
            self.identify(token.user)
            self.group(token.user)
            return self.response_ok({'id': token.invite.id})

    @extend_schema(
        tags=['Accounts'],
        summary='Get a pending invitation',
        description=(
            'Internal frontend operation. Returns a pending invitation by '
            'record ID. No user session is required; private API source-IP '
            'restrictions apply. Non-pending or missing records return 404.'
        ),
        parameters=[OpenApiParameter(
            name='id',
            type=OpenApiTypes.UUID,
            location=OpenApiParameter.PATH,
            required=True,
        )],
        auth=[],
        responses={
            200: UserInviteSerializer,
            401: UNAUTHORIZED,
            403: FORBIDDEN,
            404: NOT_FOUND,
        },
    )
    def retrieve(self, request, pk=None):
        invite = self.get_object()
        data = UserInviteSerializer(instance=invite).data
        return self.response_ok(data)

    @extend_schema(
        tags=['Accounts'],
        summary='Accept a pending invitation',
        description=(
            'No existing session is required. Use the pending invite record '
            'ID obtained from the invitation token. Registers the invited '
            'user with the supplied profile/password and returns a '
            'Pneumatic Bearer session token.'
        ),
        parameters=[OpenApiParameter(
            name='id',
            type=OpenApiTypes.UUID,
            location=OpenApiParameter.PATH,
            required=True,
        )],
        auth=[],
        request=AcceptInviteSerializer,
        responses={
            200: AuthTokenResponseSerializer,
            400: VALIDATION_ERROR,
            404: NOT_FOUND,
        },
    )
    @action(detail=True, methods=['post'])
    def accept(self, request, **kwargs):
        invite = self.get_object()
        slz = self.get_serializer(data=request.data)
        slz.is_valid(raise_exception=True)
        service = UserInviteService(
            request_user=invite.invited_user,
            current_url=request.META.get('HTTP_X_CURRENT_URL'),
            is_superuser=False,
            auth_type=AuthTokenType.USER,
        )
        try:
            user = service.accept(
                invite=invite,
                **slz.validated_data,
            )
        except AlreadyRegisteredException as ex:
            raise_validation_error(message=ex.message)
        else:
            token = AuthService.get_auth_token(
                user=user,
                user_agent=request.headers.get(
                    'User-Agent',
                    request.META.get('HTTP_USER_AGENT'),
                ),
                user_ip=request.META.get('HTTP_X_REAL_IP'),
            )
            return self.response_ok({'token': token})

    @extend_schema(
        tags=['Accounts'],
        summary='Decline an account invitation',
        description=with_access_text(
            'Declines the invite_id in the body. Only unaccepted '
            'invitations on the current account can be declined.',
            ACCESS_ADMIN_BASE,
        ),
        request=DeclineInviteRequestSerializer,
        responses={
            204: EMPTY,
            401: UNAUTHORIZED,
            403: FORBIDDEN,
            404: NOT_FOUND,
        },
    )
    @action(detail=False, methods=['post'])
    def decline(self, request):
        queryset = self.get_queryset()
        invite = get_object_or_404(queryset, pk=request.data.get('invite_id'))
        service = UserInviteService(
            request_user=invite.invited_user,
            is_superuser=request.is_superuser,
            auth_type=request.token_type,
        )
        service.decline(invite)
        return self.response_ok()

    @extend_schema(
        tags=['Accounts'],
        summary='Resend an account invitation',
        description=with_access_text(
            'Resends the invitation for the invited USER ID in the path '
            '(not the invitation record ID). Already accepted invitations '
            'are rejected; unknown users return 404.',
            ACCESS_ADMIN_BASE,
        ),
        parameters=[OpenApiParameter(
            name='id',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.PATH,
            required=True,
            description='Invited user ID, not invitation record ID.',
        )],
        request=None,
        responses={
            204: EMPTY,
            400: VALIDATION_ERROR,
            401: UNAUTHORIZED,
            403: FORBIDDEN,
            404: NOT_FOUND,
        },
    )
    @action(detail=True, methods=['post'])
    def resend(self, request, pk, *args, **kwargs):
        service = UserInviteService(
            is_superuser=request.is_superuser,
            request_user=request.user,
            current_url=request.META.get('HTTP_X_CURRENT_URL'),
        )
        try:
            service.resend_invite(user_id=pk)
        except AlreadyAcceptedInviteException as ex:
            raise_validation_error(message=ex.message)
        except UserNotFoundException as ex:
            raise Http404 from ex
        return self.response_ok()
