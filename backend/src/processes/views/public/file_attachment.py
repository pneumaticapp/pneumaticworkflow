from src.accounts.models import Account
from src.processes.permissions import (
    PublicTemplatePermission,
    StoragePermission,
)
from src.processes.views.file_attachment import (
    BaseFileAttachmentViewSet,
)


class PublicFileAttachmentViewSet(
    BaseFileAttachmentViewSet,
):

    permission_classes = (
        StoragePermission,
        PublicTemplatePermission,
    )

    def get_account(self) -> Account:
        return self.request.public_template.account
