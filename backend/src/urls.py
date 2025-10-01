from django.contrib import admin
from django.urls import include, path, re_path
from django.conf import settings
from rest_framework.routers import DefaultRouter

from src.processes.views.workflow import WorkflowViewSet
from src.processes.views.template import (
    TemplateViewSet
)
from src.processes.views.checklist import (
    CheckListViewSet
)
from src.processes.views.task import (
    TaskViewSet,
    TasksListView,
)
from src import views
from src.accounts.views import (
    AccountPlanView,
    TenantsViewSet,
)
from src.webhooks.views import (
    WebHookViewSet,
    WebHookEventViewSet,
    WebHookBufferViewSet
)
from src.services.views import ServicesViewSet
from src.payment.views import (
    PaymentViewSet,
    StripeViewSet,
    SubscriptionViewSet,
)
from src.faq.views import FaqViewSet
from src.notifications.consumers import (
    NotificationsConsumer,
    NewTaskConsumer,
    RemovedTaskConsumer,
    WorkflowEventConsumer,
    EventsConsumer,
)


router = DefaultRouter(trailing_slash=False)
router.register('templates', TemplateViewSet, basename='templates')
router.register('workflows', WorkflowViewSet, basename='workflows')
router.register('webhooks', WebHookViewSet, basename='webhooks')
router.register(
    'webhooks/buffer',
    WebHookBufferViewSet, basename='webhooks-buffer'
)
router.register(
    'webhooks/events',
    WebHookEventViewSet, basename='webhooks-events'
)
router.register('v2/tasks', TaskViewSet, basename='tasks')
router.register('v2/tasks/checklists', CheckListViewSet, basename='cl')
router.register('tenants', TenantsViewSet, basename='tenants')
router.register('services', ServicesViewSet, basename='services')
router.register('payment', PaymentViewSet, basename='payment')
router.register('payment/stripe', StripeViewSet, basename='stripe')
router.register('payment/subscription', SubscriptionViewSet, basename='subs')
router.register('faq', FaqViewSet, basename='faq')


urlpatterns = [
    path('', views.index, name='index'),
    path(f'{settings.ADMIN_PATH}/', admin.site.urls),

    path('auth/', include('src.authentication.urls')),
    path('accounts/', include('src.accounts.urls', 'accounts')),
    path(
        'analytics/',
        include('src.analytics.urls')
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


websocket_urlpatterns = [
    re_path('ws/notifications', NotificationsConsumer.as_asgi()),
    path('ws/workflows/new-task', NewTaskConsumer.as_asgi()),
    path('ws/workflows/removed-task', RemovedTaskConsumer.as_asgi()),
    path('ws/workflows/events', WorkflowEventConsumer.as_asgi()),
    path('ws/events', EventsConsumer.as_asgi()),
]
