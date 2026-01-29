from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import Http404
from rest_framework.decorators import action
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import AllowAny
from rest_framework.serializers import ValidationError
from rest_framework.viewsets import GenericViewSet

from src.accounts.enums import (
    UserInviteStatus,
)
from src.accounts.filters import UsersListFilterSet
from src.accounts.models import UserInvite
from src.accounts.permissions import (
    AccountOwnerPermission,
    BillingPlanPermission,
    ExpiredSubscriptionPermission,
    UserIsAdminOrAccountOwner,
)
from src.accounts.queries import CountTemplatesByUserQuery
from src.accounts.serializers.user import (
    UserPrivilegesSerializer,
    UserSerializer,
)
from src.accounts.serializers.users import (
    AcceptTransferSerializer,
    ReassignSerializer,
)
from src.accounts.services.account import AccountService
from src.accounts.services.exceptions import (
    AlreadyAcceptedInviteException,
    InvalidTransferTokenException,
    ReassignServiceException,
    UserIsPerformerException, UserServiceException,
)
from src.accounts.services.reassign import (
    ReassignService,
)
from src.accounts.services.user import UserService
from src.accounts.services.user_transfer import (
    UserTransferService,
)
from src.analysis.mixins import BaseIdentifyMixin
from src.executor import RawSqlExecutor
from src.generics.filters import PneumaticFilterBackend
from src.generics.mixins.views import (
    CustomViewSetMixin,
)
from src.generics.permissions import (
    IsAuthenticated,
    UserIsAuthenticated,
)
from src.utils.validation import raise_validation_error

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
        if self.action in {'list', 'active_count'}:
            return (
                IsAuthenticated(),
                BillingPlanPermission(),
            )
        if self.action == 'privileges':
            return (
                AccountOwnerPermission(),
                ExpiredSubscriptionPermission(),
                BillingPlanPermission(),
            )
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
            extra_fields=extra_fields,
        )

    def get_queryset(self):
        account_id = self.request.user.account_id
        user = self.request.user
        if self.action == 'transfer':
            queryset = UserModel.objects.all()
        elif self.action in {'list', 'privileges'}:
            queryset = (
                UserModel.include_inactive
                .all_account_users(account_id)
            )
        elif self.action == 'toggle_admin':
            queryset = (
                UserModel.objects
                .on_account(account_id)
                .exclude(is_account_owner=True)
                .exclude(id=user.id)
            )
        elif self.action == 'destroy':
            queryset = (
                UserModel.objects
                .on_account(account_id)
                .exclude(id=user.id)
            )
        else:
            queryset = UserModel.objects.on_account(account_id)
        return self.prefetch_queryset(queryset)

    def create(self, request, *args, **kwargs):
        slz = self.get_serializer(data=request.data)
        slz.is_valid(raise_exception=True)
        service = UserService(
            user=request.user,
            is_superuser=request.is_superuser,
            auth_type=request.token_type,
        )
        try:
            user = service.create(**slz.validated_data)
        except UserServiceException as ex:
            raise_validation_error(message=ex.message)
        return self.response_ok(UserSerializer(instance=user).data)

    def update(self, request, *args, **kwargs):
        user = self.get_object()
        slz = self.get_serializer(data=request.data)
        slz.is_valid(raise_exception=True)
        service = UserService(
            user=request.user,
            instance=user,
            is_superuser=request.is_superuser,
            auth_type=request.token_type,
        )
        try:
            user = service.partial_update(**slz.validated_data)
        except UserServiceException as ex:
            raise_validation_error(message=ex.message)
        return self.response_ok(UserSerializer(instance=user).data)

    def destroy(self, request, *args, **kwargs):
        request_user = request.user
        user = self.get_object()
        service = UserService(
            user=request_user,
            instance=user,
            is_superuser=request.is_superuser,
            auth_type=request.token_type,
        )
        try:
            service.deactivate()
        except UserIsPerformerException as ex:
            raise_validation_error(message=ex.message)
        return self.response_ok()

    @action(detail=False, methods=('get',))
    def privileges(self, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        return self.paginated_response(queryset)

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
                **serializer.validated_data,
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
    #         from src.authentication.services.user_auth import AuthService
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
            },
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
                user_id=slz.validated_data['user_id'],
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
        except UserModel.DoesNotExist as ex:
            if UserInvite.objects.filter(
                status=UserInviteStatus.PENDING,
                account=request.user.account,
                invited_user_id=pk,
            ).exists():
                user = UserModel.objects.get(id=pk)
            else:
                raise Http404 from ex
        query = CountTemplatesByUserQuery(
            user_id=user.id,
            account_id=request.user.account_id,
        )
        result = list(RawSqlExecutor.fetch(*query.get_sql()))
        count = sum(item['count'] for item in result)
        return self.response_ok(
            data={'count': count},
        )

    @action(
        detail=False,
        methods=('get',),
        url_path='active-count',
    )
    def active_count(self, request, *args, **kwargs):
        account_data = AccountService.get_cached_data(
            request.user.account_id,
        )
        return self.response_ok(data=account_data)
