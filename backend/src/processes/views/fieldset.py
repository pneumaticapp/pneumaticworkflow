from rest_framework.viewsets import GenericViewSet

from src.accounts.permissions import (
    BillingPlanPermission,
    ExpiredSubscriptionPermission,
    UserIsAdminOrAccountOwner,
    UsersOverlimitedPermission,
)
from src.generics.exceptions import BaseServiceException
from src.generics.mixins.views import CustomViewSetMixin
from src.generics.permissions import UserIsAuthenticated
from src.processes.models.templates.fieldset import (
    FieldsetTemplate,
)
from src.processes.serializers.templates.fieldset import (
    FieldsetTemplateSerializer,
)
from src.processes.services.templates.fieldsets.fieldset import (
    FieldSetTemplateService,
)
from src.utils.validation import raise_validation_error


class FieldsetTemplateViewSet(
    CustomViewSetMixin,
    GenericViewSet,
):
    serializer_class = FieldsetTemplateSerializer

    def get_serializer_context(self, **kwargs):
        context = super().get_serializer_context(**kwargs)
        context['user'] = self.request.user
        context['account'] = self.request.user.account
        context['is_superuser'] = self.request.is_superuser
        context['auth_type'] = self.request.token_type
        return context

    def get_permissions(self):
        return (
            UserIsAuthenticated(),
            ExpiredSubscriptionPermission(),
            BillingPlanPermission(),
            UsersOverlimitedPermission(),
            UserIsAdminOrAccountOwner(),
        )

    def get_queryset(self):
        user = self.request.user
        return (
            FieldsetTemplate.objects
            .select_related('template')
            .on_account(user.account_id)
        )

    def retrieve(self, request, *args, **kwargs):
        fieldset = self.get_object()
        serializer = self.get_serializer(fieldset)
        return self.response_ok(serializer.data)

    def partial_update(self, request, *args, **kwargs):
        fieldset = self.get_object()
        serializer = self.get_serializer(
            fieldset,
            data=request.data,
            partial=True,
            extra_fields={'template': fieldset.template},
        )
        serializer.is_valid(raise_exception=True)
        service = FieldSetTemplateService(
            user=request.user,
            instance=fieldset,
            is_superuser=request.is_superuser,
            auth_type=request.token_type,
        )
        try:
            fieldset = service.partial_update(
                **serializer.validated_data,
            )
        except BaseServiceException as ex:
            raise_validation_error(message=ex.message)
        fieldset.refresh_from_db()
        response_serializer = FieldsetTemplateSerializer(fieldset)
        return self.response_ok(response_serializer.data)

    def destroy(self, request, *args, **kwargs):
        fieldset = self.get_object()
        service = FieldSetTemplateService(
            user=request.user,
            instance=fieldset,
            is_superuser=request.is_superuser,
            auth_type=request.token_type,
        )
        try:
            service.delete()
        except BaseServiceException as ex:
            raise_validation_error(message=ex.message)
        return self.response_ok()
