from rest_framework.routers import DefaultRouter

from pneumatic_backend.processes.api_v2.views.attachments import (
    AttachmentsViewSet,
)

router = DefaultRouter(trailing_slash=False)

router.register(
    '',
    AttachmentsViewSet,
    basename='attachments'
)

urlpatterns = router.urls
