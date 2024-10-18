from django.urls import path
from rest_framework.routers import DefaultRouter
from pneumatic_backend.processes.api_v2.views.public.template import (
    PublicTemplateViewSet
)
from pneumatic_backend.processes.api_v2.views.system_template import (
    SystemTemplateViewSet,
    SystemTemplatesImportViewSet,
)
from pneumatic_backend.processes.api_v2.views.template import (
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
