from django.urls import path
from rest_framework.routers import DefaultRouter
from src.processes.views.public.template import (
    PublicTemplateViewSet
)
from src.processes.views.system_template import (
    SystemTemplateViewSet,
    SystemTemplatesImportViewSet,
)
from src.processes.views.template import (
    TemplateIntegrationsViewSet
)


router = DefaultRouter(trailing_slash=False)
router.register(
    prefix='system',
    viewset=SystemTemplateViewSet,
    basename='system_templates'
)
router.register(
    prefix='system/import',
    viewset=SystemTemplatesImportViewSet,
    basename='library_templates_import'
)
router.register(
    prefix='integrations',
    viewset=TemplateIntegrationsViewSet,
    basename='templates_integrations'
)
urlpatterns = [
    path('public', PublicTemplateViewSet.as_view({'get': 'retrieve'})),
    path('public/run', PublicTemplateViewSet.as_view({'post': 'run'})),
]
urlpatterns += router.urls
