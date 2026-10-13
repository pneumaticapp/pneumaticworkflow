from django.urls import path

from src.authentication.views.consent import LoginCompleteView
from src.authentication.views.oauth import (
    AuthorizationView,
    MCPRevokeView,
    MCPTokenView,
    RegistrationManagementView,
    RegistrationView,
)

app_name = 'oauth2_provider'
urlpatterns = [
    path('authorize', AuthorizationView.as_view(), name='authorize'),
    path('token', MCPTokenView.as_view(), name='token'),
    path('revoke', MCPRevokeView.as_view(), name='revoke-token'),
    path('register', RegistrationView.as_view(), name='dcr-register'),
    path(
        'register/<str:client_id>',
        RegistrationManagementView.as_view(),
        name='dcr-register-management',
    ),
    path('login', LoginCompleteView.as_view(), name='login'),
]
