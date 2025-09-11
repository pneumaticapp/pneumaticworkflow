from rest_framework.routers import DefaultRouter
from src.navigation.views import MenuViewSet


router = DefaultRouter(trailing_slash=False)

router.register(
    prefix='menu',
    viewset=MenuViewSet,
    basename='menu'
)

urlpatterns = router.urls
