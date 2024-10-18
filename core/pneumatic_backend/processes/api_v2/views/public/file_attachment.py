from pneumatic_backend.processes.permissions import (
    PublicTemplatePermission,
)
from pneumatic_backend.accounts.models import Account
from pneumatic_backend.processes.api_v2.views.file_attachment import (
    BaseFileAttachmentViewSet
)
from pneumatic_backend.processes.permissions import StoragePermission


class PublicFileAttachmentViewSet(
    BaseFileAttachmentViewSet
):

    permission_classes = (
        StoragePermission,
        PublicTemplatePermission,
    )

    def get_account(self) -> Account:
        return self.request.public_template.account
