from django.contrib.auth import get_user_model
from django.db.models import Prefetch
from django.http import Http404
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action
from rest_framework.viewsets import GenericViewSet

from src.accounts.filters import (
    GroupsListFilterSet,
)
from src.accounts.models import UserGroup
from src.accounts.permissions import (
    BillingPlanPermission,
    ExpiredSubscriptionPermission,
    UserIsAdminOrAccountOwner,
)
from src.accounts.queries import CountTemplatesByGroupQuery
from src.accounts.serializers.group import (
    GroupRequestSerializer,
    GroupSerializer,
)
from src.accounts.services.exceptions import (
    UserGroupServiceException,
)
from src.accounts.services.group import UserGroupService
from src.executor import RawSqlExecutor
from src.generics.filters import PneumaticFilterBackend
from src.generics.mixins.views import (
    CustomViewSetMixin,
)
from src.generics.permissions import (
    IsAuthenticated,
    UserIsAuthenticated,
)
from src.openapi import (
    ACCESS_ADMIN_BASE,
    ACCESS_ADMIN_BASIC,
    ACCESS_AUTH_LITE,
    CountResponseSerializer,
    EMPTY,
    FORBIDDEN,
    GROUPS_LIST_PARAMS,
    NOT_FOUND,
    UNAUTHORIZED,
    VALIDATION_ERROR,
)
from src.utils.validation import raise_validation_error

UserModel = get_user_model()


class GroupViewSet(
    CustomViewSetMixin,
    GenericViewSet,
):
    filter_backends = [PneumaticFilterBackend]
    serializer_class = GroupSerializer
    action_filterset_classes = {
        'list': GroupsListFilterSet,
    }

    def get_serializer_context(self, **kwargs):
        context = super().get_serializer_context(**kwargs)
        context['account'] = self.request.user.account
        return context

    def get_permissions(self):
        if self.action == 'list':
            return (
                IsAuthenticated(),
                BillingPlanPermission(),
            )
        if self.action == 'retrieve':
            return (
                UserIsAuthenticated(),
                BillingPlanPermission(),
                UserIsAdminOrAccountOwner(),
            )
        return (
            UserIsAuthenticated(),
            BillingPlanPermission(),
            UserIsAdminOrAccountOwner(),
            ExpiredSubscriptionPermission(),
        )

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return UserGroup.objects.none()
        account_id = self.request.user.account_id
        return UserGroup.include_personal.on_account(
            account_id,
        ).prefetch_related(
            Prefetch(
                'users',
                queryset=(
                    UserModel.objects
                    .on_account(account_id)
                    .order_by('last_name')),
            ),
        )

    @extend_schema(
        tags=['Accounts'],
        summary='List groups',
        description=ACCESS_AUTH_LITE,
        parameters=GROUPS_LIST_PARAMS,
        responses={
            200: GroupSerializer(many=True),
            401: UNAUTHORIZED,
            403: FORBIDDEN,
        },
    )
    def list(self, request, *args, **kwargs):
        slz = GroupRequestSerializer(data=request.GET)
        slz.is_valid(raise_exception=True)
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return self.response_ok(serializer.data)

    @extend_schema(
        tags=['Accounts'],
        summary='Create group',
        description=ACCESS_ADMIN_BASE,
        request=GroupSerializer,
        responses={
            200: GroupSerializer,
            400: VALIDATION_ERROR,
            401: UNAUTHORIZED,
            403: FORBIDDEN,
        },
    )
    def create(self, request, *args, **kwargs):
        slz = self.get_serializer(data=request.data)
        slz.is_valid(raise_exception=True)
        service = UserGroupService(
            user=request.user,
            is_superuser=request.is_superuser,
            auth_type=request.token_type,
        )
        try:
            service.create(**slz.validated_data)
        except UserGroupServiceException as ex:
            raise_validation_error(message=ex.message)
        else:
            return self.response_ok(slz.validated_data)

    @extend_schema(
        tags=['Accounts'],
        summary='Get group',
        description=ACCESS_ADMIN_BASIC,
        responses={
            200: GroupSerializer,
            401: UNAUTHORIZED,
            403: FORBIDDEN,
            404: NOT_FOUND,
        },
    )
    def retrieve(self, request, *args, **kwargs):
        group = self.get_object()
        serializer = self.get_serializer(group)
        return self.response_ok(serializer.data)

    @extend_schema(
        tags=['Accounts'],
        summary='Update group',
        description=ACCESS_ADMIN_BASE,
        request=GroupSerializer,
        responses={
            200: GroupSerializer,
            400: VALIDATION_ERROR,
            401: UNAUTHORIZED,
            403: FORBIDDEN,
            404: NOT_FOUND,
        },
    )
    def update(self, request, *args, **kwargs):
        group = self.get_object()
        slz = self.get_serializer(group, data=request.data)
        slz.is_valid(raise_exception=True)
        service = UserGroupService(
            user=request.user,
            instance=group,
            is_superuser=request.is_superuser,
            auth_type=request.token_type,
        )
        try:
            instance = service.partial_update(
                force_save=True,
                **slz.validated_data,
            )
        except UserGroupServiceException as ex:
            raise_validation_error(message=ex.message)
        else:
            serializer = GroupSerializer(instance)
            return self.response_ok(serializer.data)

    @extend_schema(
        tags=['Accounts'],
        summary='Delete group',
        description=ACCESS_ADMIN_BASE,
        responses={
            200: EMPTY,
            401: UNAUTHORIZED,
            403: FORBIDDEN,
            404: NOT_FOUND,
        },
    )
    def destroy(self, request, *args, **kwargs):
        group = self.get_object()
        service = UserGroupService(
            user=request.user,
            instance=group,
            is_superuser=request.is_superuser,
            auth_type=request.token_type,
        )
        service.delete()
        return self.response_ok()

    @extend_schema(
        tags=['Accounts'],
        summary='Count workflows for group',
        description=ACCESS_ADMIN_BASE,
        responses={
            200: CountResponseSerializer,
            401: UNAUTHORIZED,
            403: FORBIDDEN,
            404: NOT_FOUND,
        },
    )
    @action(
        detail=True,
        methods=('get',),
        url_path='count-workflows',
    )
    def count_workflows(self, request, pk=None):

        # Used before reassigning group tasks to know
        # if the reassign request needs to be executed.

        try:
            group = self.get_queryset().get(id=pk)
        except UserGroup.DoesNotExist as ex:
            raise Http404 from ex
        query = CountTemplatesByGroupQuery(
            group_id=group.id,
            account_id=request.user.account_id,
        )
        result = list(RawSqlExecutor.fetch(*query.get_sql()))
        count = sum(item['count'] for item in result)
        return self.response_ok(
            data={'count': count},
        )
