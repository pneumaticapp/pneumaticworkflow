
from django.urls import path

from src.analysis.customerio.views import WebhooksView

urlpatterns = [
    path('webhooks', WebhooksView.as_view(), name='customerio-webhooks'),
]
