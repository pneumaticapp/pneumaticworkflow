"""Schema-only view replacements must leave runtime callbacks untouched."""

import pytest
from django.contrib.auth import get_user_model
from drf_spectacular.generators import SchemaGenerator

from src.accounts.models import UserInvite
from src.accounts.views.public.users import PublicUsersViewSet
from src.accounts.views.user_invites import UserInviteViewSet


@pytest.mark.parametrize('view_class,model', [
    (PublicUsersViewSet, get_user_model()),
    (UserInviteViewSet, UserInvite),
])
def test_schema_view__queryset_override__leaves_runtime_callback_unchanged(
    mocker, view_class, model,
) -> None:
    # arrange
    callback = view_class.as_view({'get': 'list'})
    runtime_queryset = mocker.sentinel.runtime_queryset
    get_queryset = mocker.patch.object(
        view_class, 'get_queryset', return_value=runtime_queryset,
    )

    # act
    schema_view = SchemaGenerator().create_view(callback, 'GET')
    queryset = schema_view.get_queryset()

    # assert
    assert queryset.model is model
    assert queryset.query.is_empty()
    get_queryset.assert_not_called()
    assert callback.cls is view_class
    assert view_class().get_queryset() is runtime_queryset
    get_queryset.assert_called_once_with()


def test_invite_schema_context__isolated_from_runtime_context(mocker) -> None:
    # arrange
    callback = UserInviteViewSet.as_view({'post': 'create'})
    runtime_context = {'runtime': True}
    get_context = mocker.patch.object(
        UserInviteViewSet, 'get_serializer_context',
        return_value=runtime_context,
    )

    # act
    schema_view = SchemaGenerator().create_view(callback, 'POST')
    context = schema_view.get_serializer_context()

    # assert
    assert context == {}
    get_context.assert_not_called()
    assert callback.cls is UserInviteViewSet
    assert UserInviteViewSet().get_serializer_context() is runtime_context
    get_context.assert_called_once_with()
