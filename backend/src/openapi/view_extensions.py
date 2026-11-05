"""Schema-only replacements for views that require an authenticated context."""

from typing import Any, Type

from django.contrib.auth import get_user_model
from django.db.models import QuerySet
from drf_spectacular.extensions import OpenApiViewExtension
from rest_framework.views import APIView


class PublicUsersViewSchema(OpenApiViewExtension):
    target_class = 'src.accounts.views.public.users.PublicUsersViewSet'

    def view_replacement(self) -> Type[APIView]:
        user_model = get_user_model()

        class SchemaView(self.target):
            queryset = user_model.objects.none()

            def get_queryset(self) -> QuerySet:
                return self.queryset

        return SchemaView


class UserInviteViewSchema(OpenApiViewExtension):
    target_class = 'src.accounts.views.user_invites.UserInviteViewSet'

    def view_replacement(self) -> Type[APIView]:
        from src.accounts.models import UserInvite  # noqa: PLC0415

        class SchemaView(self.target):
            queryset = UserInvite.objects.none()

            def get_queryset(self) -> QuerySet:
                return self.queryset

            def get_serializer_context(self, **kwargs: Any) -> dict:
                return kwargs

        return SchemaView
