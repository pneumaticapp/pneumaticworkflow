
from django.urls import path
from pneumatic_backend.analytics.customerio.views import WebhooksView


urlpatterns = [
    path('webhooks', WebhooksView.as_view(), name='customerio-webhooks')
]
