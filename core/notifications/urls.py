from rest_framework.routers import DefaultRouter

from pneumatic_backend.notifications.views import (
    DeviceViewSet,
    IosViewSet,
)

router = DefaultRouter(trailing_slash=False)

router.register(
    'device',
    viewset=DeviceViewSet,
    basename='device',
)
router.register(
    'ios',
    viewset=IosViewSet,
    basename='ios'
)

urlpatterns = router.urls
