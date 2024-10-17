from rest_framework.routers import DefaultRouter
from pneumatic_backend.pages.views import PublicPageViewSet


router = DefaultRouter(trailing_slash=False)

router.register(
    prefix='public',
    viewset=PublicPageViewSet,
    basename='public-pages'
)

urlpatterns = router.urls
