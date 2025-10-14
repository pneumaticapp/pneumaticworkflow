from rest_framework.routers import DefaultRouter

from src.processes.views.comments import CommentViewSet
from src.processes.views.file_attachment import (
    FileAttachmentViewSet,
)
from src.processes.views.public.file_attachment import (
    PublicFileAttachmentViewSet,
)
from src.processes.views.workflow_counts import (
    WorkflowCountsViewSet,
)

router = DefaultRouter(trailing_slash=False)

router.register(
    'attachments',
    FileAttachmentViewSet,
    basename='attachments',
)
router.register(
    'public/attachments',
    PublicFileAttachmentViewSet,
    basename='public_attachments',
)
router.register(
    'count',
    WorkflowCountsViewSet,
    basename='count',
)
router.register(
    'comments',
    CommentViewSet,
    basename='comments',
)

urlpatterns = router.urls
