from rest_framework.pagination import LimitOffsetPagination
from rest_framework.viewsets import GenericViewSet

from src.accounts.permissions import (
    BillingPlanPermission,
    ExpiredSubscriptionPermission,
    UserIsAdminOrAccountOwner,
    UsersOverlimitedPermission,
)
from src.generics.mixins.views import CustomViewSetMixin
from src.generics.permissions import UserIsAuthenticated
from src.processes.models.templates.fieldset import FieldsetTemplateRule
from src.processes.serializers.templates.fieldset import (
    FieldsetTemplateRuleSerializer,
)
from src.processes.services.exceptions import (
    FieldsetTemplateRuleServiceException,
)
from src.processes.services.fieldset_template_rule import (
    FieldsetTemplateRuleService,
)
from src.utils.validation import raise_validation_error


class FieldsetTemplateRuleViewSet(
    CustomViewSetMixin,
    GenericViewSet,
):
    serializer_class = FieldsetTemplateRuleSerializer
    action_paginator_classes = {
        'list': LimitOffsetPagination,
    }

    def get_serializer_context(self, **kwargs):
        context = super().get_serializer_context(**kwargs)
        context['user'] = self.request.user
        context['account'] = self.request.user.account
        context['is_superuser'] = self.request.is_superuser
        context['auth_type'] = self.request.token_type
        return context

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return (
                UserIsAuthenticated(),
                ExpiredSubscriptionPermission(),
                BillingPlanPermission(),
                UsersOverlimitedPermission(),
            )
        return (
            UserIsAuthenticated(),
            ExpiredSubscriptionPermission(),
            BillingPlanPermission(),
            UsersOverlimitedPermission(),
            UserIsAdminOrAccountOwner(),
        )

    def get_queryset(self):
        user = self.request.user
        return FieldsetTemplateRule.objects.on_account(user.account_id)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        return self.paginated_response(queryset)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        service = FieldsetTemplateRuleService(
            user=request.user,
            is_superuser=request.is_superuser,
            auth_type=request.token_type,
        )
        try:
            rule = service.create(**serializer.validated_data)
        except FieldsetTemplateRuleServiceException as ex:
            raise_validation_error(message=ex.message)
        response_serializer = FieldsetTemplateRuleSerializer(rule)
        return self.response_created(response_serializer.data)

    def retrieve(self, request, *args, **kwargs):
        rule = self.get_object()
        serializer = self.get_serializer(rule)
        return self.response_ok(serializer.data)

    def partial_update(self, request, *args, **kwargs):
        rule = self.get_object()
        serializer = self.get_serializer(
            rule,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        service = FieldsetTemplateRuleService(
            user=request.user,
            instance=rule,
            is_superuser=request.is_superuser,
            auth_type=request.token_type,
        )
        try:
            rule = service.partial_update(
                **serializer.validated_data,
            )
        except FieldsetTemplateRuleServiceException as ex:
            raise_validation_error(message=ex.message)
        rule.refresh_from_db()
        response_serializer = FieldsetTemplateRuleSerializer(rule)
        return self.response_ok(response_serializer.data)

    def destroy(self, request, *args, **kwargs):
        rule = self.get_object()
        service = FieldsetTemplateRuleService(
            user=request.user,
            instance=rule,
            is_superuser=request.is_superuser,
            auth_type=request.token_type,
        )
        try:
            service.delete()
        except FieldsetTemplateRuleServiceException as ex:
            raise_validation_error(message=ex.message)
        return self.response_ok()
