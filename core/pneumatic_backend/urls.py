from django.contrib import admin
from django.urls import include, path, re_path
from django.conf import settings
from rest_framework.routers import DefaultRouter

from pneumatic_backend.processes.views.workflow import WorkflowViewSet
from pneumatic_backend.processes.api_v2.views.template import (
    TemplateViewSet
)
from pneumatic_backend.processes.api_v2.views.checklist import (
    CheckListViewSet
)
from pneumatic_backend.processes.api_v2.views.task import (
    TaskViewSet,
    TasksListView,
)
from pneumatic_backend.processes.views.task import (
    RecentTaskView,
)
from pneumatic_backend import views
from pneumatic_backend.accounts.views import (
    AccountPlanView,
    TenantsViewSet,
)
from pneumatic_backend.webhooks.views import (
    WebHookViewSet,
    WebHookEventViewSet,
    WebHookBufferViewSet
)
from pneumatic_backend.services.views import ServicesViewSet
from pneumatic_backend.payment.views import (
    PaymentViewSet,
    StripeViewSet,
    SubscriptionViewSet,
)
from pneumatic_backend.faq.views import FaqViewSet
from pneumatic_backend.notifications.consumers import (
    NotificationsConsumer,
    NewTaskConsumer,
    RemovedTaskConsumer,
    WorkflowEventConsumer,
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

    path('auth/', include('pneumatic_backend.authentication.urls')),
    path('accounts/', include('pneumatic_backend.accounts.urls', 'accounts')),
    path(
        'analytics/',
        include('pneumatic_backend.analytics.urls')
    ),
    path('v2/accounts/plan', AccountPlanView.as_view()),
    path('applications/', include('pneumatic_backend.applications.urls')),
    path('reports/', include('pneumatic_backend.reports.urls')),

    # Using by Zapier
    path('recent-task', RecentTaskView.as_view()),
    path('v3/tasks', TasksListView.as_view()),

    path('templates/', include('pneumatic_backend.processes.urls.templates')),
    path('workflows/', include('pneumatic_backend.processes.urls.workflows')),
    path('notifications/', include('pneumatic_backend.notifications.urls')),
    path('navigation/', include('pneumatic_backend.navigation.urls')),
    path('pages/', include('pneumatic_backend.pages.urls')),
]

urlpatterns += router.urls


websocket_urlpatterns = [
    re_path('ws/notifications', NotificationsConsumer.as_asgi()),
    path('ws/workflows/new-task', NewTaskConsumer.as_asgi()),
    path('ws/workflows/removed-task', RemovedTaskConsumer.as_asgi()),
    path('ws/workflows/events', WorkflowEventConsumer.as_asgi()),
]
