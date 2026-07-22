from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView
from rest_framework.routers import DefaultRouter

from src import views
from src.authentication.services.user_auth import (
    CookieTokenAuthentication,
)
from src.openapi.views import DocsRedocView, DocsSwaggerView
from src.accounts.views.accounts import AccountPlanView
from src.accounts.views.tenants import TenantsViewSet
from src.faq.views import FaqViewSet
from src.notifications.consumers import (
    EventsConsumer,
)
from src.payment.views import (
    PaymentViewSet,
    StripeViewSet,
    SubscriptionViewSet,
)
from src.processes.views.checklist import (
    CheckListViewSet,
)
from src.processes.views.task import (
    TasksListView,
    TaskViewSet,
)
from src.processes.views.fieldset import (
    SharedFieldsetTemplateViewSet,
)
from src.datasets.views import DatasetViewSet, DatasetItemViewSet
from src.processes.views.template import (
    TemplateViewSet,
)
from src.processes.views.workflow import WorkflowViewSet
from src.services.views import ServicesViewSet
from src.storage.views import AttachmentViewSet
from src.webhooks.views.buffer import WebHookBufferViewSet
from src.webhooks.views.events import WebHookEventViewSet
from src.webhooks.views.webhooks import WebHookViewSet

router = DefaultRouter(trailing_slash=False)
router.register('templates', TemplateViewSet, basename='templates')
router.register('workflows', WorkflowViewSet, basename='workflows')
router.register('webhooks', WebHookViewSet, basename='webhooks')
router.register(
    'webhooks/buffer',
    WebHookBufferViewSet, basename='webhooks-buffer',
)
router.register(
    'webhooks/events',
    WebHookEventViewSet, basename='webhooks-events',
)
router.register('v2/tasks', TaskViewSet, basename='tasks')
router.register('v2/tasks/checklists', CheckListViewSet, basename='cl')
router.register('tenants', TenantsViewSet, basename='tenants')
router.register('services', ServicesViewSet, basename='services')
router.register('payment', PaymentViewSet, basename='payment')
router.register('payment/stripe', StripeViewSet, basename='stripe')
router.register('payment/subscription', SubscriptionViewSet, basename='subs')
router.register('faq', FaqViewSet, basename='faq')
router.register('attachments', AttachmentViewSet, basename='attachments')
router.register('datasets', DatasetViewSet, basename='datasets')
router.register('datasets/items', DatasetItemViewSet, basename='dataset-items')
router.register(
    prefix='fieldsets',
    viewset=SharedFieldsetTemplateViewSet,
    basename='fieldsets',
)

urlpatterns = [
    path('', views.index, name='index'),
    path(f'{settings.ADMIN_PATH}/', admin.site.urls),

    path('auth/', include('src.authentication.urls')),
    path('accounts/', include('src.accounts.urls', 'accounts')),
    path(
        'analytics/',
        include('src.analysis.urls'),
    ),
    path('v2/accounts/plan', AccountPlanView.as_view()),
    path('applications/', include('src.applications.urls')),
    path('reports/', include('src.reports.urls')),

    # Using by Zapier
    path('v3/tasks', TasksListView.as_view()),

    path('templates/', include('src.processes.urls.templates')),
    path('workflows/', include('src.processes.urls.workflows')),
    path('notifications/', include('src.notifications.urls')),
    path('navigation/', include('src.navigation.urls')),
    path('pages/', include('src.pages.urls')),
]

urlpatterns += router.urls

urlpatterns += [
    # Schema stays on SpectacularAPIView (JSON 403 if anonymous).
    # Docs UI views redirect browsers to frontend login.
    path(
        'api/schema/',
        SpectacularAPIView.as_view(
            authentication_classes=(CookieTokenAuthentication,),
        ),
        name='schema',
    ),
    path(
        'api/docs/',
        DocsSwaggerView.as_view(
            url_name='schema',
            authentication_classes=(CookieTokenAuthentication,),
        ),
        name='swagger-ui',
    ),
    path(
        'api/redoc/',
        DocsRedocView.as_view(
            url_name='schema',
            authentication_classes=(CookieTokenAuthentication,),
        ),
        name='redoc',
    ),
]


websocket_urlpatterns = [
    path('ws/events', EventsConsumer.as_asgi()),
]
