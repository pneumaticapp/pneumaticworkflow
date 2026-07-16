from rest_framework.routers import DefaultRouter

from src.processes.views.comments import CommentViewSet
from src.processes.views.workflow_counts import (
    WorkflowCountsViewSet,
)

router = DefaultRouter(trailing_slash=False)

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
