from rest_framework.decorators import action
from rest_framework.viewsets import GenericViewSet

from src.accounts.permissions import (
    BillingPlanPermission,
    ExpiredSubscriptionPermission,
)
from src.generics.mixins.views import (
    CustomViewSetMixin,
)
from src.generics.permissions import IsAuthenticated
from src.processes.serializers.file_attachment import (
    FileAttachmentCheckPermissionSerializer,
)
from src.processes.services.attachments import (
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
