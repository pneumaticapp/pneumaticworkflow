from types import SimpleNamespace

from src.authentication.permissions import PrivateApiPermission
from src.generics.permissions import (
    StagingPermission,
    UserIsAuthenticated,
)
from src.openapi.preprocessing import exclude_private_endpoints


def test_exclude_private_endpoints__path_prefix__filtered():
    # arrange
    endpoints = [
        (
            '/auth/signup',
            '^/auth/signup$',
            'POST',
            SimpleNamespace(cls=object),
        ),
        (
            '/templates',
            '^/templates$',
            'GET',
            SimpleNamespace(cls=object),
        ),
    ]

    # act
    result = exclude_private_endpoints(endpoints)

    # assert
    assert len(result) == 1
    assert result[0][0] == '/templates'


def test_exclude_private_endpoints__path_startswith__filtered():
    # arrange
    endpoints = [
        (
            '/auth/signup/extra',
            '^/auth/signup/extra$',
            'POST',
            SimpleNamespace(cls=object),
        ),
    ]

    # act
    result = exclude_private_endpoints(endpoints)

    # assert
    assert result == []


def test_exclude_private_endpoints__trailing_slash__filtered():
    # arrange
    endpoints = [
        (
            '/accounts/api-key/',
            '^/accounts/api-key/$',
            'GET',
            SimpleNamespace(cls=object),
        ),
    ]

    # act
    result = exclude_private_endpoints(endpoints)

    # assert
    assert result == []


def test_exclude_private_endpoints__staging_perm__filtered():
    # arrange
    class StagingView:
        permission_classes = (StagingPermission,)

    class PublicView:
        permission_classes = (UserIsAuthenticated,)

    endpoints = [
        (
            '/staging-only',
            '^/staging-only$',
            'GET',
            SimpleNamespace(cls=StagingView),
        ),
        (
            '/webhooks',
            '^/webhooks$',
            'GET',
            SimpleNamespace(cls=PublicView),
        ),
    ]

    # act
    result = exclude_private_endpoints(endpoints)

    # assert
    assert len(result) == 1
    assert result[0][0] == '/webhooks'


def test_exclude_private_endpoints__private_perm__filtered():
    # arrange
    class PrivateView:
        permission_classes = (
            UserIsAuthenticated,
            PrivateApiPermission,
        )

    endpoints = [
        (
            '/accounts/custom-private',
            '^/accounts/custom-private$',
            'GET',
            SimpleNamespace(cls=PrivateView),
        ),
    ]

    # act
    result = exclude_private_endpoints(endpoints)

    # assert
    assert result == []


def test_exclude_private_endpoints__perm_subclass__filtered():
    # arrange
    class CustomPrivate(PrivateApiPermission):
        pass

    class SubclassView:
        permission_classes = (CustomPrivate,)

    endpoints = [
        (
            '/accounts/subclass-private',
            '^/accounts/subclass-private$',
            'GET',
            SimpleNamespace(cls=SubclassView),
        ),
    ]

    # act
    result = exclude_private_endpoints(endpoints)

    # assert
    assert result == []


def test_exclude_private_endpoints__invites_token__filtered():
    # arrange
    endpoints = [
        (
            '/accounts/invites/token',
            '^/accounts/invites/token$',
            'GET',
            SimpleNamespace(cls=object),
        ),
        (
            '/accounts/invites/{id}',
            '^/accounts/invites/(?P<id>[^/.]+)$',
            'GET',
            SimpleNamespace(cls=object),
        ),
    ]

    # act
    result = exclude_private_endpoints(endpoints)

    # assert
    assert result == []


def test_exclude_private_endpoints__get_permissions__filtered():
    # arrange
    class DynamicView:
        permission_classes = (UserIsAuthenticated,)

        def get_permissions(self):
            if self.action == 'list':
                return [PrivateApiPermission()]
            return [UserIsAuthenticated()]

    endpoints = [
        (
            '/accounts/dynamic',
            '^/accounts/dynamic$',
            'GET',
            SimpleNamespace(
                cls=DynamicView,
                actions={'get': 'list'},
            ),
        ),
        (
            '/accounts/dynamic',
            '^/accounts/dynamic$',
            'POST',
            SimpleNamespace(
                cls=DynamicView,
                actions={'post': 'create'},
            ),
        ),
    ]

    # act
    result = exclude_private_endpoints(endpoints)

    # assert
    assert len(result) == 1
    assert result[0][2] == 'POST'


def test_exclude_private_endpoints__api_key__filtered():
    # arrange
    endpoints = [
        (
            '/accounts/api-key',
            '^/accounts/api-key$',
            'GET',
            SimpleNamespace(cls=object),
        ),
    ]

    # act
    result = exclude_private_endpoints(endpoints)

    # assert
    assert result == []


def test_exclude_private_endpoints__callback_no_cls__kept():
    # arrange
    endpoints = [
        (
            '/templates',
            '^/templates$',
            'GET',
            SimpleNamespace(),
        ),
    ]

    # act
    result = exclude_private_endpoints(endpoints)

    # assert
    assert len(result) == 1
    assert result[0][0] == '/templates'


def test_exclude_private_endpoints__empty__empty():
    # arrange
    endpoints = []

    # act
    result = exclude_private_endpoints(endpoints)

    # assert
    assert result == []


def test_exclude_private_endpoints__signout__filtered():
    # arrange
    endpoints = [
        (
            '/auth/signout',
            '^/auth/signout$',
            'POST',
            SimpleNamespace(cls=object),
        ),
    ]

    # act
    result = exclude_private_endpoints(endpoints)

    # assert
    assert result == []


def test_exclude_private_endpoints__get_perms_no_request__fallback():
    # arrange
    class DynamicView:
        permission_classes = (PrivateApiPermission,)

        def get_permissions(self):
            # Mirrors views that branch on self.request.method
            if self.request.method == 'GET':
                return [PrivateApiPermission()]
            return [UserIsAuthenticated()]

    endpoints = [
        (
            '/accounts/dynamic-fail',
            '^/accounts/dynamic-fail$',
            'GET',
            SimpleNamespace(
                cls=DynamicView,
                actions={'get': 'list'},
            ),
        ),
    ]

    # act
    result = exclude_private_endpoints(endpoints)

    # assert
    assert result == []


def test_exclude_private_endpoints__action_missing__fallback():
    # arrange
    class DynamicView:
        permission_classes = (UserIsAuthenticated,)

        def get_permissions(self):
            return [PrivateApiPermission()]

    endpoints = [
        (
            '/accounts/dynamic',
            '^/accounts/dynamic$',
            'GET',
            SimpleNamespace(
                cls=DynamicView,
                actions={'post': 'create'},
            ),
        ),
    ]

    # act
    result = exclude_private_endpoints(endpoints)

    # assert
    assert len(result) == 1
    assert result[0][0] == '/accounts/dynamic'
