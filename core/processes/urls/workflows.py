from rest_framework.routers import DefaultRouter

from pneumatic_backend.processes.views.workflow_counts import (
    WorkflowCountsViewSet
)
from pneumatic_backend.processes.views.comments import CommentViewSet
from pneumatic_backend.processes.api_v2.views.public.file_attachment import (
    PublicFileAttachmentViewSet
)
from pneumatic_backend.processes.api_v2.views.file_attachment import (
    FileAttachmentViewSet,
)

router = DefaultRouter(trailing_slash=False)

router.register(
    'attachments',
    FileAttachmentViewSet,
    basename='attachments'
)
router.register(
    'public/attachments',
    PublicFileAttachmentViewSet,
    basename='public_attachments'
)
router.register(
    'count',
    WorkflowCountsViewSet,
    basename='count'
)
router.register(
    'comments',
    CommentViewSet,
    basename='comments'
)

urlpatterns = router.urls
