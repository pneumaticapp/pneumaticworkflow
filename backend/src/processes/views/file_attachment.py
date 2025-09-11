from abc import abstractmethod

from rest_framework.decorators import action
from rest_framework.mixins import DestroyModelMixin
from rest_framework.viewsets import GenericViewSet

from src.accounts.models import Account
from src.accounts.permissions import (
    BillingPlanPermission,
    ExpiredSubscriptionPermission,
)
from src.generics.mixins.views import (
    AnonymousMixin,
    CustomViewSetMixin,
)
from src.generics.permissions import IsAuthenticated
from src.processes.serializers.file_attachment import (
    FileAttachmentCreateSerializer,
    FileAttachmentSerializer,
)
from src.processes.services.attachments import (
    AttachmentService,
)
from src.processes.services.exceptions import (
    AttachmentServiceException,
)
from src.processes.models import FileAttachment
from src.processes.permissions import StoragePermission
from src.utils.validation import raise_validation_error


class BaseFileAttachmentViewSet(
    CustomViewSetMixin,
    DestroyModelMixin,
    AnonymousMixin,
    GenericViewSet,
):

    serializer_class = FileAttachmentCreateSerializer
    action_serializer_classes = {
        'create': FileAttachmentCreateSerializer,
        'publish': FileAttachmentSerializer,
    }
    queryset = FileAttachment.objects.all()

    @abstractmethod
    def get_account(self) -> Account:
        pass

    def post_create_actions(self):
        pass

    def post_publish_actions(self):
        pass

    def get_queryset(self):
        account = self.get_account()
        qst = self.queryset.on_account(account.id)
        if self.action == 'destroy':
            qst = qst.not_on_event()
        return qst

    def create(self, request, *args, **kwargs):
        slz = self.get_serializer(data=request.data)
        slz.is_valid(raise_exception=True)
        try:
            service = AttachmentService(account=self.get_account())
            (
                attachment,
                upload_url,
                thumb_upload_url
            ) = service.create(**slz.validated_data)
        except AttachmentServiceException as ex:
            raise_validation_error(message=ex.message)
        else:
            self.post_create_actions()
            return self.response_ok({
                'id': attachment.id,
                'file_upload_url': upload_url,
                'thumbnail_upload_url': thumb_upload_url
            })

    @action(methods=['POST'], detail=True)
    def publish(self, request, *args, **kwargs):
        instance = self.get_object()
        try:
            service = AttachmentService(account=self.get_account())
            service.publish(
                attachment=instance,
                request_user=request.user,
                auth_type=request.token_type,
                anonymous_id=request.data.get(
                    'anonymous_id',
                    self.get_user_ip(self.request)
                )
            )
        except AttachmentServiceException as ex:
            raise_validation_error(message=ex.message)
        else:
            self.post_publish_actions()
            return self.response_ok(self.get_serializer(instance).data)


class FileAttachmentViewSet(
    BaseFileAttachmentViewSet
):
    permission_classes = (
        StoragePermission,
        IsAuthenticated,
        ExpiredSubscriptionPermission,
        BillingPlanPermission,
    )

    def get_account(self) -> Account:
        return self.request.user.account

    @action(methods=['POST'], detail=True)
    def clone(self, *args, **kwargs):
        instance = self.get_object()
        service = AttachmentService()
        clone = service.create_clone(instance)
        return self.response_ok({'id': clone.id})
