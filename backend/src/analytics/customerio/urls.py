
from django.urls import path

from src.analytics.customerio.views import WebhooksView

urlpatterns = [
    path('webhooks', WebhooksView.as_view(), name='customerio-webhooks'),
]
