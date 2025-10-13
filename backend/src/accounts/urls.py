from django.urls import path
from rest_framework.routers import DefaultRouter
from src.accounts.views.groups import GroupViewSet
from src.accounts.views.public.users import PublicUsersViewSet
from src.accounts.views.public.account import (
    PublicAccountViewSet,
)
from src.accounts.views.accounts import AccountView
from src.accounts.views.api_key import APIKeyView
from src.accounts.views.notifications import (
    NotificationsViewSet,
    NotificationsReadView,
)
from src.accounts.views.unsubscribes import (
    UnsubscribeDigestView,
    UnsubscribeEmailView,
)
from src.accounts.views.user_invites import UserInviteViewSet
from src.accounts.views.user import UserViewSet
from src.accounts.views.users import UsersViewSet


app_name = 'accounts'


router = DefaultRouter(trailing_slash=False)

router.register('user', UserViewSet, basename='user')
router.register('groups', GroupViewSet, basename='groups')
router.register('public/users', PublicUsersViewSet, basename='public-users')
router.register('public/account', PublicAccountViewSet, basename='pub-account')
router.register('users', UsersViewSet, basename='users')
router.register('invites', UserInviteViewSet, basename='invites')
router.register(
    'notifications',
    NotificationsViewSet,
    basename='notifications',
)

urlpatterns = [
    path('account', AccountView.as_view()),
    path('api-key', APIKeyView.as_view()),
    # TODO: Deprecated api. Remove in https://my.pneumatic.app/workflows/13920
    path('digest/unsubscribe', UnsubscribeDigestView.as_view()),
    path('emails/unsubscribe', UnsubscribeEmailView.as_view()),
    path('notifications/read', NotificationsReadView.as_view()),
] + router.urls
