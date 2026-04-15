# ruff: noqa: PLC0415
import re
from typing import Optional, List

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.db import IntegrityError, transaction

from src.accounts.enums import (
    Language,
    UserDateFormat,
    UserFirstDayWeek,
    UserStatus,
)
from src.accounts.models import (
    Account,
    APIKey,
    Contact,
)
from src.accounts.messages import (
    MSG_A_0049,
    MSG_A_0050,
)
from src.accounts.serializers.user import UserWebsocketSerializer
from src.accounts.services.exceptions import (
    AlreadyRegisteredException,
    UserIsPerformerException,
    UserServiceException,
    PreventSelfDeletion,
    PreventAccountOwnerDeletion,
)
from src.accounts.validators import user_is_last_performer
from src.analysis.mixins import BaseIdentifyMixin
from src.analysis.services import AnalyticService
from src.authentication.tokens import PneumaticToken
from src.generics.base.service import BaseModelService
from src.notifications.tasks import (
    send_user_deleted_notification,
    send_user_updated_notification,
)
from src.payment.stripe.exceptions import StripeServiceException
from src.payment.stripe.service import StripeService
from src.processes.enums import FieldType
from src.processes.models.workflows.fields import TaskField
from src.processes.services.remove_user_from_draft import (
    remove_user_from_draft,
)
from src.notifications.tasks import send_user_deactivated_notification

UserModel = get_user_model()


class UserService(
    BaseModelService,
    BaseIdentifyMixin,
):

    def _create_instance(
        self,
        account: Account,
        email: str,
        phone: Optional[str] = None,
        status: UserStatus.LITERALS = UserStatus.ACTIVE,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        photo: Optional[str] = None,
        raw_password: Optional[str] = None,
        password: Optional[str] = None,  # hash for database storage
        is_admin: bool = True,
        is_account_owner: bool = False,
        language: Language.LITERALS = None,
        timezone: Optional[str] = None,
        date_fmt: UserDateFormat.LITERALS = None,
        date_fdw: UserFirstDayWeek.LITERALS = None,
        is_superuser: bool = False,
        is_staff: bool = False,
        is_tasks_digest_subscriber: bool = True,
        is_digest_subscriber: bool = True,
        is_newsletters_subscriber: bool = True,
        is_special_offers_subscriber: bool = True,
        is_new_tasks_subscriber: bool = True,
        is_complete_tasks_subscriber: bool = True,
        is_comments_mentions_subscriber: bool = True,
        **kwargs,
    ) -> UserModel:

        """ password parameter need for create tenant account owner """

        if not password:
            if not raw_password:
                raw_password = UserModel.objects.make_random_password()
            password = make_password(raw_password)

        if is_account_owner:
            if date_fdw is None:
                date_fdw = UserFirstDayWeek.SUNDAY
            if date_fmt is None:
                date_fmt = UserDateFormat.PY_USA_12
            if language is None:
                language = settings.LANGUAGE_CODE
            if timezone is None:
                timezone = settings.TIME_ZONE
            if not UserModel.objects.exists():
                is_superuser = True
                is_staff = True
        else:
            if date_fdw is None:
                date_fdw = account.get_owner().date_fdw
            if date_fmt is None:
                date_fmt = account.get_owner().date_fmt
            if language is None:
                language = account.get_owner().language
            if timezone is None:
                timezone = account.get_owner().timezone

        try:
            self.instance = UserModel.objects.create(
                account=account,
                email=email,
                first_name=first_name or '',
                last_name=last_name or '',
                password=password,
                photo=photo,
                phone=phone,
                is_admin=is_admin,
                is_account_owner=is_account_owner,
                status=status,
                language=language,
                timezone=timezone,
                date_fmt=date_fmt,
                date_fdw=date_fdw,
                is_superuser=is_superuser,
                is_staff=is_staff,
                is_tasks_digest_subscriber=is_tasks_digest_subscriber,
                is_digest_subscriber=is_digest_subscriber,
                is_newsletters_subscriber=is_newsletters_subscriber,
                is_special_offers_subscriber=is_special_offers_subscriber,
                is_new_tasks_subscriber=is_new_tasks_subscriber,
                is_complete_tasks_subscriber=is_complete_tasks_subscriber,
                is_comments_mentions_subscriber=(
                    is_comments_mentions_subscriber
                ),
            )
        except IntegrityError as ex:
            raise AlreadyRegisteredException from ex
        return self.instance

    def _create_related(self, user_groups: Optional[list] = None, **kwargs):
        key = PneumaticToken.create(user=self.instance, for_api_key=True)
        APIKey.objects.create(
            user=self.instance,
            name=self.instance.get_full_name(),
            account=self.instance.account,
            key=key,
        )
        if user_groups is not None:
            self.instance.user_groups.set(user_groups)

    def _create_actions(self, **kwargs):
        self.identify(self.instance)
        if self.instance.is_account_owner:
            self.instance.incoming_invites.not_accepted().delete()
            account = self.instance.account
            self.group(user=self.instance, account=account)
            AnalyticService.account_created(
                user=self.instance,
                is_superuser=self.is_superuser,
                auth_type=self.auth_type,
            )
            if account.is_verified:
                AnalyticService.account_verified(
                    user=self.instance,
                    is_superuser=self.is_superuser,
                    auth_type=self.auth_type,
                )

    def _get_free_email(
        self,
        local: str,
        number: int,
        domain: str,
    ):
        email = f'{local}+{number}@{domain}'
        if UserModel.include_inactive.filter(email=email).exists():
            return self._get_free_email(
                local=local,
                number=number + 1,
                domain=domain,
            )
        return email

    def _get_incremented_email(self, user: UserModel) -> str:

        """ increment email, check if it free and return it

            master@test.com -> master+1@test.com
            master+10@test.com -> master+11@test.com """

        local, domain = user.email.split('@')
        parse_result = re.search(r'^(.+)\+(\d+)$', local)
        if parse_result:
            local, number = parse_result.groups()
            number = int(number) + 1
        else:
            number = 1
        return self._get_free_email(
            local=local,
            number=number,
            domain=domain,
        )

    def create_tenant_account_owner(
        self,
        tenant_account: Account,
        master_account: Account,
    ) -> UserModel:

        master_user = master_account.get_owner()
        return self.create(
            account=tenant_account,
            email=self._get_incremented_email(master_user),
            status=UserStatus.ACTIVE,
            first_name=master_user.first_name,
            last_name=master_user.last_name,
            password=master_user.password,
            photo=master_user.photo,
            phone=master_user.phone,
            is_admin=True,
            is_account_owner=True,
        )

    def change_password(self, password: str):
        self.user.set_password(password)
        self.user.save()

    def _update_related_user_fields(self, old_name):

        """ Call after update instance """

        if old_name != self.instance.name:
            TaskField.objects.filter(
                type=FieldType.USER,
                user_id=self.instance.id,
            ).update(value=self.instance.name)

    def _update_related_stripe_account(self):

        """ Call after update instance """

        if (
            not self.account.is_tenant
            and self.instance.is_account_owner
            and self.account.billing_sync
        ):
            try:
                service = StripeService(
                    user=self.instance,
                    auth_type=self.auth_type,
                    is_superuser=self.is_superuser,
                )
                service.update_customer()
            except StripeServiceException as ex:
                raise UserServiceException(message=ex.message) from ex

    def _update_analytics(self, **update_kwargs):

        """ Call after update instance """

        if update_kwargs.get('is_digest_subscriber') is False:
            AnalyticService.users_digest(
                user=self.instance,
                auth_type=self.auth_type,
                is_superuser=self.is_superuser,
            )
        self.identify(self.instance)

    def _deactivate_actions(self):
        send_user_deactivated_notification.delay(
            user_id=self.instance.id,
            user_email=self.instance.email,
            account_id=self.account.id,
            logo_lg=self.account.logo_lg,
        )

    def _validate_deactivate(self):
        if self.instance.id == self.user.id:
            raise PreventSelfDeletion
        if self.instance.is_account_owner:
            raise PreventAccountOwnerDeletion
        if user_is_last_performer(self.instance):
            raise UserIsPerformerException

    def _deactivate_subordinates(self):
        """Clear the manager FK on all subordinates of the deactivated
        user and schedule WebSocket notifications.

        Uses transaction.on_commit so Celery tasks fire only after a
        successful commit.  The default-argument capture (data=ws_data)
        prevents closure-variable rebinding across loop iterations.
        """
        user = self.instance
        subordinates = list(UserModel.objects.filter(manager=user))
        if subordinates:
            sub_ids = [s.id for s in subordinates]
            UserModel.objects.filter(
                id__in=sub_ids,
            ).update(manager=None)

        for subordinate in subordinates:
            subordinate.manager = None
            ws_data = UserWebsocketSerializer(subordinate).data

            # Capture ws_data via default argument so each
            # iteration gets its own snapshot; without it the
            # closure would reference the rebinding loop variable.
            def notify(data=ws_data):
                send_user_updated_notification.delay(
                    logging=False,
                    account_id=self.account.id,
                    user_data=data,
                )

            transaction.on_commit(notify)

    def _deactivate(self):
        user = self.instance
        old_manager = user.manager
        with transaction.atomic():
            self._deactivate_subordinates()

            if old_manager is not None:
                user.manager = None
                user.save(update_fields=('manager',))

            remove_user_from_draft(
                account_id=user.account_id,
                user_id=user.id,
            )
            user.incoming_invites.delete()
            user.status = UserStatus.INACTIVE
            user.is_active = False  # need for django admin
            user.save(update_fields=('status', 'is_active'))
            Contact.objects.filter(
                account=self.account,
                email=user.email,
                status=UserStatus.ACTIVE,
            ).update(
                status=UserStatus.INVITED,
            )
            from src.accounts.services.account import AccountService
            service = AccountService(
                instance=self.account,
                user=user,
            )
            service.update_users_counts()
            self.identify(user)

        if old_manager is not None:
            send_user_updated_notification.delay(
                logging=False,
                account_id=self.account.id,
                user_data=UserWebsocketSerializer(old_manager).data,
            )

    def deactivate(self, skip_validation=False):

        """ Deactivate user and call delete actions
            If user is invited not send identify and deactivation email """

        if not skip_validation:
            self._validate_deactivate()
        run_deactivate_actions = self.instance.status == UserStatus.ACTIVE
        self._deactivate()
        # Refresh to clear stale prefetch cache (e.g. subordinates)
        # so the WS payload reflects the post-deactivation state.
        self.instance.refresh_from_db()
        send_user_deleted_notification.delay(
            logging=self.account.log_api_requests,
            account_id=self.account.id,
            user_data=UserWebsocketSerializer(
                self.instance,
            ).data,
        )
        if run_deactivate_actions:
            self._deactivate_actions()

    def _update_managers(self, old_manager, new_manager):
        """Send WebSocket notifications to old and/or new managers
        after a manager change on self.instance."""
        managers_to_notify = {
            m for m in (old_manager, new_manager)
            if m is not None
        }
        for mgr in managers_to_notify:
            ws_data_mgr = UserWebsocketSerializer(mgr).data
            send_user_updated_notification.delay(
                logging=False,
                account_id=self.account.id,
                user_data=ws_data_mgr,
            )

    def _validate_manager(self, manager):
        """Validate that assigning *manager* to self.instance
        does not create a circular hierarchy.

        1. A user cannot be their own manager (MSG_A_0049).
        2. Walk up from *manager* through the chain; if we
           encounter self.instance the assignment would
           create a cycle (MSG_A_0050).

        Builds an in-memory {user_id: manager_id} map from
        active users so the check runs in a single DB query.
        """
        if manager.id == self.instance.id:
            raise UserServiceException(
                message=str(MSG_A_0049),
            )
        manager_map = dict(
            UserModel.objects.on_account(
                self.account.id,
            ).active().values_list('id', 'manager_id'),
        )
        current_id = manager.id
        visited = set()
        while current_id is not None:
            if current_id in visited:
                break
            if current_id == self.instance.id:
                raise UserServiceException(
                    message=str(MSG_A_0050),
                )
            visited.add(current_id)
            current_id = manager_map.get(current_id)

    def _validate_subordinates(
        self,
        subordinates: List[UserModel],
        proposed_manager=None,
    ):
        """Validate the proposed subordinate list.

        1. A user cannot be their own subordinate (MSG_A_0049).
        2. No proposed subordinate may be an ancestor of the
           user in the *future* hierarchy (MSG_A_0050).

        The *future* hierarchy is computed by patching the
        in-memory manager map with *proposed_manager*,
        which fixes the stale-cache problem that occurs when
        manager and subordinates are updated simultaneously.
        """
        for sub in subordinates:
            if sub.id == self.instance.id:
                raise UserServiceException(
                    message=str(MSG_A_0049),
                )

        manager_map = dict(
            UserModel.objects.on_account(
                self.account.id,
            ).active().values_list('id', 'manager_id'),
        )
        # Patch the map with the proposed manager so the
        # ancestor walk reflects the future state.
        if proposed_manager is not None:
            manager_map[self.instance.id] = proposed_manager.id
        else:
            manager_map[self.instance.id] = None

        ancestor_ids = set()
        current_id = manager_map.get(self.instance.id)
        while current_id is not None:
            if current_id in ancestor_ids:
                break
            ancestor_ids.add(current_id)
            current_id = manager_map.get(current_id)

        for sub in subordinates:
            if sub.id in ancestor_ids:
                raise UserServiceException(
                    message=str(MSG_A_0050),
                )

    def partial_update(
        self,
        force_save=False,
        user_groups: Optional[list] = None,
        raw_password: Optional[str] = None,
        **update_kwargs,
    ) -> UserModel:

        subordinates = update_kwargs.pop('subordinates', None)
        old_name = self.instance.name
        old_manager = self.instance.manager
        manager_changed = (
            'manager' in update_kwargs
            and update_kwargs['manager'] != old_manager
        )

        # Validate hierarchy constraints before any DB mutation.
        new_manager = update_kwargs.get('manager')
        if 'manager' in update_kwargs and new_manager is not None:
            self._validate_manager(new_manager)
        if subordinates is not None:
            proposed_manager = update_kwargs.get(
                'manager', self.instance.manager,
            )
            self._validate_subordinates(
                subordinates, proposed_manager,
            )

        # Single transaction wrapping both the user save and
        # subordinates update so partial state is never committed.
        with transaction.atomic():
            if raw_password:
                super().partial_update(
                    password=make_password(raw_password),
                    **update_kwargs,
                    force_save=True,
                )
            else:
                super().partial_update(**update_kwargs, force_save=True)
            if user_groups is not None:
                self.instance.user_groups.set(user_groups)
            self._update_related_user_fields(old_name=old_name)

            if subordinates is not None:
                self._update_subordinates(subordinates)

        self._update_related_stripe_account()
        self._update_analytics(**update_kwargs)

        # Refresh to clear stale prefetch cache so the WS
        # payload reflects the updated state.
        if subordinates is not None:
            self.instance.refresh_from_db()

        if manager_changed:
            self._update_managers(old_manager, self.instance.manager)

        ws_data = UserWebsocketSerializer(self.instance).data
        send_user_updated_notification.delay(
            logging=self.account.log_api_requests,
            account_id=self.account.id,
            user_data=ws_data,
        )

        return self.instance

    def _update_subordinates(
        self,
        subordinates: List[UserModel],
    ):
        """Replace all current subordinates with the given list.

        Sends WS notifications to:
        - Each changed subordinate
        - Each old manager who lost a subordinate

        Does NOT notify self.instance (the manager) — the caller
        (partial_update) sends that notification after refresh_from_db
        to avoid duplicates.

        Uses transaction.on_commit so Celery tasks fire only after a
        successful commit.  The default-argument capture (data=ws_data)
        prevents closure-variable rebinding across loop iterations.
        """
        new_ids = {s.id for s in subordinates}

        with transaction.atomic():
            current_ids = set(
                self.instance.subordinates.values_list('id', flat=True),
            )
            changed_user_ids = current_ids ^ new_ids
            # Collect old managers inside the transaction so the
            # read is consistent with the subsequent set() call.
            old_manager_ids = set()
            if changed_user_ids:
                old_manager_ids = set(
                    UserModel.objects.filter(
                        id__in=changed_user_ids,
                        manager__isnull=False,
                    ).exclude(
                        manager=self.instance,
                    ).values_list('manager_id', flat=True),
                )

            self.instance.subordinates.set(subordinates)

            if changed_user_ids:
                changed_users = UserModel.objects.filter(
                    id__in=changed_user_ids,
                )
                for user in changed_users:
                    ws_data_user = (
                        UserWebsocketSerializer(user).data
                    )

                    # Capture ws_data_user via default argument
                    # so each iteration gets its own snapshot;
                    # without it the closure would reference the
                    # rebinding loop variable.
                    def notify(data=ws_data_user):
                        send_user_updated_notification.delay(
                            logging=False,
                            account_id=self.account.id,
                            user_data=data,
                        )

                    transaction.on_commit(notify)

            if old_manager_ids:
                old_managers = UserModel.objects.filter(
                    id__in=old_manager_ids,
                )
                for mgr in old_managers:
                    ws_data_mgr = (
                        UserWebsocketSerializer(mgr).data
                    )

                    # Same default-argument capture pattern
                    # as notify() above.
                    def notify_mgr(data=ws_data_mgr):
                        send_user_updated_notification.delay(
                            logging=False,
                            account_id=self.account.id,
                            user_data=data,
                        )

                    transaction.on_commit(notify_mgr)
