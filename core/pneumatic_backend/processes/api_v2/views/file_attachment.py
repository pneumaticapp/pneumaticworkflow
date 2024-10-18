from abc import abstractmethod
from rest_framework.mixins import DestroyModelMixin
from rest_framework.viewsets import GenericViewSet
from rest_framework.decorators import action
from pneumatic_backend.processes.permissions import StoragePermission
from pneumatic_backend.accounts.permissions import (
    ExpiredSubscriptionPermission,
)
from pneumatic_backend.generics.permissions import (
    IsAuthenticated,
    PaymentCardPermission,
)
from pneumatic_backend.generics.mixins.views import (
    CustomViewSetMixin,
    AnonymousMixin,
)
from pneumatic_backend.processes.models import FileAttachment
from pneumatic_backend.processes.api_v2.serializers.file_attachment import (
    FileAttachmentCreateSerializer,
    FileAttachmentSerializer,
)
from pneumatic_backend.accounts.models import Account
from pneumatic_backend.processes.api_v2.services.exceptions import (
    AttachmentServiceException
)
from pneumatic_backend.processes.api_v2.services.attachments import (
    AttachmentService
)
from pneumatic_backend.utils.validation import raise_validation_error


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
            (
                attachment,
                upload_url,
                thumb_upload_url
            ) = AttachmentService.create(
                account_id=self.get_account().id,
                **slz.validated_data
            )
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
            AttachmentService.publish(
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
        PaymentCardPermission,
        ExpiredSubscriptionPermission,
    )

    def get_account(self) -> Account:
        return self.request.user.account

    @action(methods=['POST'], detail=True)
    def clone(self, *args, **kwargs):
        instance = self.get_object()
        clone = AttachmentService.create_clone(instance)
        return self.response_ok({'id': clone.id})
