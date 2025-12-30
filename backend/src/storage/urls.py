from rest_framework.routers import DefaultRouter

from src.storage.views import AttachmentViewSet

router = DefaultRouter()

router.register(
    r'attachments',
    AttachmentViewSet,
    basename='attachments',
)

urlpatterns = router.urls
