# ruff: noqa: PLC0415
import re
from typing import Optional

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
from src.accounts.serializers.user import UserWebsocketSerializer
from src.accounts.services.exceptions import (
    AlreadyRegisteredException,
    UserIsPerformerException,
)
from src.accounts.validators import user_is_last_performer
from src.analysis.mixins import BaseIdentifyMixin
from src.analysis.services import AnalyticService
from src.authentication.tokens import PneumaticToken
from src.generics.base.service import BaseModelService
from src.notifications.tasks import send_user_deleted_notification
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
        status: UserStatus = UserStatus.ACTIVE,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        photo: Optional[str] = None,
        raw_password: Optional[str] = None,
        password: Optional[str] = None,
        is_admin: bool = True,
        is_account_owner: bool = False,
        language: Language.LITERALS = None,
        timezone: Optional[str] = None,
        date_fmt: UserDateFormat = None,
        date_fdw: UserFirstDayWeek = None,
        is_superuser: bool = False,
        is_staff: bool = False,
        **kwargs,
    ) -> UserModel:

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
                email=email,
                first_name=first_name or '',
                last_name=last_name or '',
                password=password,
                photo=photo,
                phone=phone,
                is_admin=is_admin,
                is_account_owner=is_account_owner,
                account=account,
                status=status,
                language=language,
                timezone=timezone,
                date_fmt=date_fmt,
                date_fdw=date_fdw,
                is_superuser=is_superuser,
                is_staff=is_staff,
            )
        except IntegrityError as ex:
            raise AlreadyRegisteredException from ex
        return self.instance

    def _create_related(self, **kwargs):
        key = PneumaticToken.create(user=self.instance, for_api_key=True)
        APIKey.objects.create(
            user=self.instance,
            name=self.instance.get_full_name(),
            account=self.instance.account,
            key=key,
        )

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

    @classmethod
    def _deactivate_actions(cls, user: UserModel):
        send_user_deactivated_notification.delay(
            user_id=user.id,
            user_email=user.email,
            account_id=user.account_id,
            logo_lg=user.account.logo_lg,
        )

    @classmethod
    def _validate_deactivate(cls, user):
        if user_is_last_performer(user):
            raise UserIsPerformerException

    @classmethod
    def _deactivate(
        cls,
        user: UserModel,
    ):
        with transaction.atomic():
            remove_user_from_draft(
                account_id=user.account_id,
                user_id=user.id,
            )
            user.incoming_invites.delete()
            user.status = UserStatus.INACTIVE
            user.is_active = False  # need for django admin
            user.save(update_fields=('status', 'is_active'))
            Contact.objects.filter(
                account=user.account,
                email=user.email,
                status=UserStatus.ACTIVE,
            ).update(
                status=UserStatus.INVITED,
            )
            from src.accounts.services.account import AccountService
            service = AccountService(
                instance=user.account,
                user=user,
            )
            service.update_users_counts()
            cls.identify(user)

    @classmethod
    def deactivate(cls, user: UserModel, skip_validation=False):

        """ Deactivate user and call delete actions
            If user is invited not send identify and deactivation email """

        if not skip_validation:
            cls._validate_deactivate(user)
        run_deactivate_actions = user.status == UserStatus.ACTIVE
        cls._deactivate(user)
        send_user_deleted_notification.delay(
            logging=user.account.log_api_requests,
            account_id=user.account_id,
            user_data=UserWebsocketSerializer(user).data,
        )
        if run_deactivate_actions:
            cls._deactivate_actions(user)
