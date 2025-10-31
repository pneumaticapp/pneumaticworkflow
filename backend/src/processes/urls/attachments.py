from rest_framework.routers import DefaultRouter

from src.processes.views.attachments import (
    AttachmentsViewSet,
)

router = DefaultRouter(trailing_slash=False)

router.register(
    '',
    AttachmentsViewSet,
    basename='attachments',
)

urlpatterns = router.urls
