from django.urls import path
from src.applications.views import (
    IntegrationsListView,
    IntegrationView
)


urlpatterns = [
    path('integrations', IntegrationsListView.as_view()),
    path('integrations/<int:pk>', IntegrationView.as_view())
]
