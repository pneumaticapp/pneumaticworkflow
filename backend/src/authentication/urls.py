from django.urls import path

from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from src.authentication.views.verification import (
    VerificationTokenView,
    VerificationTokenResendView,
)
from src.authentication.views.password import (
    ChangePasswordView,
    ResetPasswordViewSet,
)
from src.authentication.views.google import (
    SignInWithGoogleView,
    GoogleAuthViewSet,
)
from src.authentication.views.signin import (
    TokenObtainPairCustomView,
    SuperuserEmailTokenView,
)
from src.authentication.views.signup import SignUpView
from src.authentication.views.context import ContextUserView
from src.authentication.views.signout import SignOutView
from src.authentication.views.microsoft import MSAuthViewSet
from src.authentication.views.auth0 import Auth0ViewSet


app_name = 'auth'

urlpatterns = [
    path(
        'context',
        ContextUserView.as_view(),
        name='auth-context',
    ),
    path(
        'signin-google',
        SignInWithGoogleView.as_view(),
        name='auth-signin-google',
    ),

    # JSON Web Tokens
    path(
        'token/obtain',
        TokenObtainPairCustomView.as_view(),
        name='auth-token-obtain',
    ),
    path(
        'token/refresh',
        TokenRefreshView.as_view(),
        name='auth-token-refresh',
    ),

    path('signup', SignUpView.as_view(), name='auth-signup'),
    path('signout', SignOutView.as_view(), name='auth-signout'),
    path(
        'change-password',
        ChangePasswordView.as_view(),
        name='auth-change-password',
    ),
    path('verification', VerificationTokenView.as_view()),
    path('resend-verification', VerificationTokenResendView.as_view()),
    path('superuser/token', SuperuserEmailTokenView.as_view()),
]

router = DefaultRouter(trailing_slash=False)
router.register('google', GoogleAuthViewSet, basename='auth-google')
router.register(
    'reset-password',
    ResetPasswordViewSet,
    basename='reset-password',
)
router.register(
    'microsoft',
    MSAuthViewSet,
    basename='microsoft',
)

router.register(
    'auth0',
    Auth0ViewSet,
    basename='auth0',
)

urlpatterns += router.urls
