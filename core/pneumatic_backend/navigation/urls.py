from rest_framework.routers import DefaultRouter
from pneumatic_backend.navigation.views import MenuViewSet


router = DefaultRouter(trailing_slash=False)

router.register(
    prefix='menu',
    viewset=MenuViewSet,
    basename='menu'
)

urlpatterns = router.urls
