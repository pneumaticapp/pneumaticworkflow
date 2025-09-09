from rest_framework import status
from rest_framework.decorators import action
from rest_framework.viewsets import GenericViewSet

from pneumatic_backend.accounts.permissions import (
    BillingPlanPermission,
    ExpiredSubscriptionPermission,
)
from pneumatic_backend.generics.mixins.views import (
    CustomViewSetMixin,
)
from pneumatic_backend.generics.permissions import IsAuthenticated
from pneumatic_backend.processes.api_v2.serializers.file_attachment import (
    FileAttachmentCheckPermissionSerializer,
)
from pneumatic_backend.processes.api_v2.services.attachments import (
    AttachmentService,
)


class AttachmentsViewSet(
    CustomViewSetMixin,
    GenericViewSet,
):
    
    serializer_class = FileAttachmentCheckPermissionSerializer

    permission_classes = (
        IsAuthenticated,
        ExpiredSubscriptionPermission,
        BillingPlanPermission,
    )

    @action(
        methods=['POST'],
        detail=False,
        url_path='check-permission'
    )
    def check_permission(self, request, *args, **kwargs):
        slz = self.get_serializer(data=request.data)
        slz.is_valid(raise_exception=True)

        service = AttachmentService()
        has_permission = service.check_user_permission(
            user_id=request.user.id,
            account_id=request.user.account_id,
            file_id=slz.validated_data['file_id']
        )

        if has_permission:
            return self.response_ok()
        else:
            return self.response_forbidden()
