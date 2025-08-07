from django.urls import path
from pneumatic_backend.applications.views import (
    IntegrationsListView,
    IntegrationView
)


urlpatterns = [
    path('integrations', IntegrationsListView.as_view()),
    path('integrations/<int:pk>', IntegrationView.as_view())
]
