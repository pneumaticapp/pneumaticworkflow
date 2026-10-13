from uuid import UUID

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import QuerySet
from django.shortcuts import get_object_or_404
from django.utils import timezone
from oauth2_provider.models import AccessToken, Application, RefreshToken
from rest_framework.exceptions import PermissionDenied

from src.accounts.enums import UserStatus
from src.mcp.models import (
    AccessBinding,
    ClientPolicy,
    Connection,
    Delegation,
    RefreshBinding,
)

UserModel = get_user_model()


class ConnectionService:
    # Fields identifying the same consent of one user to one client.
    IDENTITY_FIELDS = ('user_id', 'account_id', 'application_id', 'resource')

    @classmethod
    def is_eligible_user(cls, user: UserModel, account_id: int) -> bool:
        return (
            user.account_id == account_id
            and user.status == UserStatus.ACTIVE
            and user.is_active
            and user.is_user
            and not user.is_deleted
            and not user.account.is_deleted
        )

    @classmethod
    def is_live(cls, connection: Connection) -> bool:
        return (
            settings.MCP_ENABLED
            and connection.revoked_at is None
            and connection.resource == settings.MCP_PUBLIC_URL
            and cls.is_eligible_user(
                user=connection.user,
                account_id=connection.account_id,
            )
            and ClientPolicy.objects.filter(
                application_id=connection.application_id,
                is_active=True,
            ).exists()
        )

    @classmethod
    def check_live(cls, connection: Connection):
        if not cls.is_live(connection=connection):
            raise PermissionDenied

    @classmethod
    def is_same_identity(cls, first: Connection, second: Connection) -> bool:
        """Legacy duplicate grants of one consent share storage identity."""
        return all(
            getattr(first, name) == getattr(second, name)
            for name in cls.IDENTITY_FIELDS
        )

    @classmethod
    def get_user_connections(cls, user: UserModel) -> QuerySet[Connection]:
        return Connection.objects.filter(
            user=user,
            account_id=user.account_id,
        ).select_related('application')

    @classmethod
    def get_user_connection(
        cls,
        user: UserModel,
        connection_id: UUID,
    ) -> Connection:
        return get_object_or_404(
            Connection,
            pk=connection_id,
            user=user,
            account_id=user.account_id,
        )

    @classmethod
    def save_grant(
        cls,
        user: UserModel,
        application: Application,
        scopes: list[str],
    ) -> Connection:
        """Merge a new grant into the oldest live consent of the user.

        Call inside a transaction: the user row and consents are locked so
        that parallel grants cannot create duplicates.
        """
        locked_user = UserModel.objects.select_for_update().get(pk=user.pk)
        if locked_user.account_id != user.account_id:
            raise PermissionDenied
        candidates = list(
            Connection.objects.select_for_update()
            .filter(
                application=application,
                user=locked_user,
                account_id=locked_user.account_id,
                resource=settings.MCP_PUBLIC_URL,
                revoked_at__isnull=True,
            )
            .order_by('pk'),
        )
        merged_scopes = set(scopes)
        for candidate in candidates:
            merged_scopes.update(candidate.scopes)
        if candidates:
            connection = min(
                candidates,
                key=lambda item: (item.created_at, str(item.pk)),
            )
        else:
            connection = Connection(
                application=application,
                user=locked_user,
                account_id=locked_user.account_id,
                resource=settings.MCP_PUBLIC_URL,
            )
        connection.scopes = sorted(merged_scopes)
        cls.check_live(connection=connection)
        connection.save()
        ClientPolicy.objects.get_or_create(
            application=application,
            defaults={'registration_type': application.registration_source},
        )
        return connection

    @classmethod
    def lock_group(cls, connection: Connection) -> list[UUID]:
        """Lock live duplicates of the consent; call inside a transaction.

        Duplicates keep their rows: uploads and files stay bound to them.
        """
        return list(
            Connection.objects.select_for_update()
            .filter(
                user_id=connection.user_id,
                account_id=connection.account_id,
                application_id=connection.application_id,
                resource=connection.resource,
                revoked_at__isnull=True,
            )
            .order_by('pk')
            .values_list('pk', flat=True),
        )

    @classmethod
    @transaction.atomic
    def revoke(cls, connection: Connection):
        """Revoke the consent with its duplicates and every issued token."""
        connection.refresh_from_db(fields=['revoked_at'])
        if connection.revoked_at is not None:
            return
        connection_ids = cls.lock_group(connection=connection)
        revoked_at = timezone.now()
        Connection.objects.filter(pk__in=connection_ids).update(
            revoked_at=revoked_at,
        )
        RefreshToken.objects.filter(
            pk__in=RefreshBinding.objects.filter(
                connection_id__in=connection_ids,
            ).values('refresh_token_id'),
        ).update(revoked=revoked_at)
        AccessToken.objects.filter(
            pk__in=AccessBinding.objects.filter(
                connection_id__in=connection_ids,
            ).values('access_token_id'),
        ).delete()
        Delegation.objects.filter(connection_id__in=connection_ids).delete()
