from rest_framework.routers import DefaultRouter

from src.storage.views import AttachmentViewSet, FileSyncViewSet

router = DefaultRouter(trailing_slash=False)

router.register(
    r'attachments',
    AttachmentViewSet,
    basename='attachments',
)
router.register(
    r'file-sync',
    FileSyncViewSet,
    basename='file-sync',
)

urlpatterns = router.urls
