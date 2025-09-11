from django.contrib.auth import get_user_model
from rest_framework.decorators import action
from rest_framework.viewsets import GenericViewSet
from src.generics.permissions import (
    IsAuthenticated,
)
from src.processes.permissions import (
    GuestTaskPermission,
)
from src.accounts.permissions import (
    ExpiredSubscriptionPermission,
    BillingPlanPermission,
)
from src.generics.mixins.views import (
    CustomViewSetMixin,
)
from src.processes.models import (
    Checklist
)
from src.processes.services.tasks.exceptions import (
    ChecklistServiceException,
)
from src.utils.validation import raise_validation_error
from src.analytics.mixins import BaseIdentifyMixin
from src.processes.services.tasks.checklist import (
    ChecklistService
)
from src.processes.serializers.workflows.checklist import (
    CheckListSerializer,
    CheckListRequestSerializer
)
from src.accounts.enums import UserType

UserModel = get_user_model()


class CheckListViewSet(
    CustomViewSetMixin,
    BaseIdentifyMixin,
    GenericViewSet,
):
    serializer_class = CheckListSerializer
    permission_classes = (
        IsAuthenticated,
        ExpiredSubscriptionPermission,
        BillingPlanPermission,
        GuestTaskPermission,
    )

    def get_serializer_context(self, **kwargs):
        context = super().get_serializer_context(**kwargs)
        context['user'] = self.request.user
        context['account'] = self.request.user.account
        return context

    def get_queryset(self):
        qst = Checklist.objects.filter(
            task__account_id=self.request.user.account_id
        )
        user = self.request.user
        skip_member_access = (
            user.is_account_owner or user.type == UserType.GUEST
        )
        if not skip_member_access:
            qst = qst.with_workflow_member(user.id)
        return qst

    def retrieve(self, *args, **kwargs):
        checklist = self.get_object()
        slz = self.get_serializer(instance=checklist)
        return self.response_ok(slz.data)

    @action(methods=('POST',), detail=True)
    def mark(self, request, *args, **kwargs):
        checklist = self.get_object()
        request_slz = CheckListRequestSerializer(data=request.data)
        request_slz.is_valid(raise_exception=True)
        try:
            checklist_service = ChecklistService(
                instance=checklist,
                user=request.user,
                is_superuser=request.is_superuser,
                auth_type=request.token_type,
            )
            checklist_service.mark(
                selection_id=request_slz.validated_data['selection_id']
            )
        except ChecklistServiceException as ex:
            raise_validation_error(message=ex.message)
        else:
            slz = self.get_serializer(instance=checklist_service.instance)
            return self.response_ok(slz.data)

    @action(methods=('POST',), detail=True)
    def unmark(self, request, *args, **kwargs):
        checklist = self.get_object()
        request_slz = CheckListRequestSerializer(data=request.data)
        request_slz.is_valid(raise_exception=True)
        try:
            checklist_service = ChecklistService(
                instance=checklist,
                user=request.user,
                is_superuser=request.is_superuser,
                auth_type=request.token_type,
            )
            checklist_service.unmark(
                selection_id=request_slz.validated_data['selection_id']
            )
        except ChecklistServiceException as ex:
            raise_validation_error(message=ex.message)
        else:
            slz = self.get_serializer(instance=checklist_service.instance)
            return self.response_ok(slz.data)
