from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import Http404
from rest_framework.serializers import ValidationError
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import AllowAny
from rest_framework.viewsets import GenericViewSet
from rest_framework.mixins import RetrieveModelMixin, ListModelMixin
from pneumatic_backend.accounts.services import (
    UserService,
)
from pneumatic_backend.accounts.filters import (
    UsersListFilterSet,
)
from pneumatic_backend.accounts.services import AccountService
from pneumatic_backend.accounts.models import UserInvite
from pneumatic_backend.accounts.permissions import (
    UserIsAdminOrAccountOwner,
    ExpiredSubscriptionPermission,
    BillingPlanPermission,
    AccountOwnerPermission,
)
from pneumatic_backend.accounts.queries import (
    CountTemplatesByUserQuery,
)
from pneumatic_backend.accounts.serializers.user import (
    UserSerializer,
    UserPrivilegesSerializer,
)
from pneumatic_backend.accounts.serializers.users import (
    ReassignSerializer,
    AcceptTransferSerializer,
)
from pneumatic_backend.accounts.services.user_transfer import (
    UserTransferService,
)
from pneumatic_backend.executor import RawSqlExecutor
from pneumatic_backend.generics.filters import PneumaticFilterBackend
from pneumatic_backend.generics.mixins.views import (
    CustomViewSetMixin,
)
from pneumatic_backend.analytics.mixins import BaseIdentifyMixin
from pneumatic_backend.accounts.services.reassign import (
    ReassignService
)
from pneumatic_backend.generics.permissions import (
    UserIsAuthenticated,
    IsAuthenticated,
)
from pneumatic_backend.accounts.services.exceptions import (
    AlreadyAcceptedInviteException,
    InvalidTransferTokenException,
    UserIsPerformerException,
    ReassignServiceException,
)
from pneumatic_backend.accounts.enums import (
    UserInviteStatus
)
from pneumatic_backend.utils.validation import raise_validation_error

UserModel = get_user_model()


class UsersViewSet(
    CustomViewSetMixin,
    RetrieveModelMixin,
    ListModelMixin,
    GenericViewSet,
    BaseIdentifyMixin,
):
    serializer_class = UserSerializer
    pagination_class = LimitOffsetPagination
    filter_backends = [PneumaticFilterBackend]
    action_serializer_classes = {
        'reassign': ReassignSerializer,
        'privileges': UserPrivilegesSerializer,
    }
    action_filterset_classes = {
        'list': UsersListFilterSet,
        'privileges': UsersListFilterSet,
    }

    def get_permissions(self):
        if self.action == 'transfer':
            return (AllowAny(),)
        elif self.action in {'list', 'active_count'}:
            return (
                IsAuthenticated(),
                BillingPlanPermission(),
            )
        elif self.action == 'privileges':
            return (
                AccountOwnerPermission(),
                ExpiredSubscriptionPermission(),
                BillingPlanPermission(),
            )
        else:
            return (
                UserIsAuthenticated(),
                BillingPlanPermission(),
                ExpiredSubscriptionPermission(),
                UserIsAdminOrAccountOwner(),
            )

    def get_serializer_context(self, **kwargs):
        context = super().get_serializer_context(**kwargs)
        context['account'] = self.request.user.account
        context['user'] = self.request.user
        return context

    def prefetch_queryset(self, queryset, extra_fields=None):
        if self.action in {'list', 'delete'}:
            extra_fields = (
                'user_groups',
                'incoming_invites',
            )
        elif self.action == 'privileges':
            queryset = queryset.prefetch_related(
                'user_groups',
                'incoming_invites',
            )

        return super().prefetch_queryset(
            queryset=queryset,
            extra_fields=extra_fields
        )

    def get_queryset(self):
        if self.action == 'transfer':
            queryset = UserModel.objects.all()
        elif self.action in {'list', 'privileges'}:
            account_id = self.request.user.account_id
            queryset = UserModel.include_inactive.all_account_users(
                account_id
            )
        elif self.action == 'toggle_admin':
            account = self.request.user.account
            queryset = UserModel.objects.on_account(account.id).exclude(
                is_account_owner=True
            ).exclude(id=self.request.user.id)
        else:
            queryset = self.request.user.account.users
        queryset = self.prefetch_queryset(queryset)
        return queryset

    @action(detail=False, methods=('get',))
    def privileges(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        return self.paginated_response(queryset)

    @action(detail=True, methods=('post',))
    def delete(self, request, pk=None):
        queryset = self.get_queryset().exclude(id=request.user.id)
        user = get_object_or_404(queryset, pk=pk)
        try:
            UserService.deactivate(user)
        except UserIsPerformerException as ex:
            raise_validation_error(message=ex.message)
        return self.response_ok()

    @action(
        detail=True,
        methods=('post',),
        url_path='toggle-admin',
    )
    def toggle_admin(self, *args, **kwargs):
        user = self.get_object()
        user.is_admin = not user.is_admin
        user.save(update_fields=['is_admin'])
        self.identify(user)
        return self.response_ok()

    @action(detail=False, methods=('post',))
    def reassign(self, request):
        serializer = self.get_serializer(data=request.data)
        # TODO need return formatted validation error
        serializer.is_valid(raise_exception=True)
        try:
            service = ReassignService(
                is_superuser=request.is_superuser,
                auth_type=request.token_type,
                **serializer.validated_data
            )
            service.reassign_everywhere()
        except ReassignServiceException as ex:
            raise_validation_error(message=ex.message)
        return self.response_ok()

    # TODO uncomment in https://my.pneumatic.app/workflows/15691/
    # @action(detail=True, methods=('get',))
    # def transfer(self, request, pk=None):
    #     slz = AcceptTransferSerializer(
    #         data={
    #             'user_id': pk,
    #             'token': request.GET.get('token'),
    #         }
    #     )
    #     slz.is_valid(raise_exception=True)
    #     service = UserTransferService()
    #     try:
    #         service.accept_transfer(
    #             token_str=slz.validated_data['token'],
    #             user_id=slz.validated_data['user_id']
    #         )
    #     except AlreadyAcceptedInviteException as ex:
    #         raise_validation_error(
    #             error_code=ErrorCode.INVITE_ALREADY_ACCEPTED,
    #             message=ex.message
    #         )
    #     except InvalidTransferTokenException as ex:
    #         raise_validation_error(message=ex.message)
    #     else:
    #         from pneumatic_backend.authentication.services import AuthService
    #         token = AuthService.get_auth_token(
    #             user=service.get_user(),
    #             user_agent=request.headers.get(
    #                 'User-Agent',
    #                 request.META.get('HTTP_USER_AGENT')
    #             ),
    #             user_ip=request.META.get('HTTP_X_REAL_IP'),
    #         )
    #         return self.response_ok({'token': token})

    # TODO remove in https://my.pneumatic.app/workflows/15691/
    @action(detail=True, methods=('get',))
    def transfer(self, request, pk=None):
        slz = AcceptTransferSerializer(
            data={
                'user_id': pk,
                'token': request.GET.get('token'),
            }
        )
        try:
            slz.is_valid(raise_exception=True)
        except ValidationError:
            return self.redirect(settings.EXPIRED_INVITE_PAGE)

        service = UserTransferService()
        host = settings.FRONTEND_URL
        try:
            service.accept_transfer(
                token_str=slz.validated_data['token'],
                user_id=slz.validated_data['user_id']
            )
        except AlreadyAcceptedInviteException:
            return self.redirect(host)
        except InvalidTransferTokenException:
            return self.redirect(settings.EXPIRED_INVITE_PAGE)
        else:
            account = service.get_account()
            return self.response_raw(f"""
              <script>
                  setTimeout("location.href = '{host}';",3000);
              </script>
              You was successfully transferred to account {account.name}
          """)

    @action(
        detail=True,
        methods=('get',),
        url_path='count-workflows',
    )
    def count_workflows(self, request, pk=None):

        # Used before deleting a user to know
        # if the reassign request needs to be executed.

        try:
            user = self.get_queryset().get(id=pk)
        except UserModel.DoesNotExist:
            if UserInvite.objects.filter(
                status=UserInviteStatus.PENDING,
                account=request.user.account,
                invited_user_id=pk
            ).exists():
                user = UserModel.objects.get(id=pk)
            else:
                raise Http404
        query = CountTemplatesByUserQuery(
            user_id=user.id,
            account_id=request.user.account_id,
        )
        result = list(RawSqlExecutor.fetch(*query.get_sql()))
        count = sum(item['count'] for item in result)
        return self.response_ok(
            data={'count': count}
        )

    @action(
        detail=False,
        methods=('get',),
        url_path='active-count'
    )
    def active_count(self, request, *args, **kwargs):
        account_data = AccountService.get_cached_data(
            request.user.account_id
        )
        return self.response_ok(data=account_data)
