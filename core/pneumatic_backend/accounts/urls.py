from django.urls import path
from rest_framework.routers import DefaultRouter

from pneumatic_backend.accounts.views.groups import GroupViewSet
from pneumatic_backend.accounts.views.public.users import PublicUsersViewSet
from pneumatic_backend.accounts.views.public.account import (
    PublicAccountViewSet
)
from pneumatic_backend.accounts.views import (
    UsersViewSet,
    UserInviteViewSet,
    UpdateUserProfileView,
    AccountView,
    UserViewSet,
    UnsubscribeDigestView,
    APIKeyView,
    NotificationsReadView,
    NotificationsViewSet,
    UnsubscribeEmailView,
)
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
    basename='notifications'
)

urlpatterns = [
    path('profile', UpdateUserProfileView.as_view(), name='profile'),
    path('account', AccountView.as_view()),
    path('api-key', APIKeyView.as_view()),
    # TODO: Deprecated api. Remove in https://my.pneumatic.app/workflows/13920
    path('digest/unsubscribe', UnsubscribeDigestView.as_view()),
    path('emails/unsubscribe', UnsubscribeEmailView.as_view()),
    path('notifications/read', NotificationsReadView.as_view()),
] + router.urls
