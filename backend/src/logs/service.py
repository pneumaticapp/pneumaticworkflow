from typing import Optional
from src.generics.base.service import BaseModelService
from src.logs.models import AccountEvent
from django.contrib.auth import get_user_model
from src.logs.enums import (
    AccountEventStatus,
    AccountEventType,
    RequestDirection,
)


UserModel = get_user_model()


class AccountLogService(BaseModelService):

    def _create_instance(
        self,
        event_type: AccountEventType,
        title: Optional[str] = None,
        path: Optional[str] = None,
        method: Optional[str] = None,
        scheme: Optional[str] = None,
        auth_token: Optional[str] = None,
        user_agent: Optional[str] = None,
        ip: Optional[str] = None,
        request_data: Optional[dict] = None,
        http_status: Optional[int] = None,
        user_id: Optional[int] = None,
        account_id: Optional[int] = None,
        response_data: Optional[dict] = None,
        contractor: str = None,
        status: AccountEventStatus = AccountEventStatus.PENDING,
        direction: RequestDirection = RequestDirection.RECEIVED,
        **kwargs
    ):

        self.instance = AccountEvent.objects.create(
            event_type=event_type,
            title=title,
            ip=ip,
            user_agent=user_agent,
            auth_token=auth_token,
            scheme=scheme,
            method=method,
            path=path,
            request_data=request_data,
            http_status=http_status,
            user_id=user_id,
            account_id=account_id,
            response_data=response_data,
            status=status,
            direction=direction,
            contractor=contractor,
        )

    def _create_related(self, **kwargs):
        pass

    def api_request(
        self,
        user: UserModel,
        ip: str,
        user_agent: str,
        auth_token: str,
        scheme: str,
        method: str,
        title: str,
        path: str,
        http_status: int,
        direction: RequestDirection = RequestDirection.RECEIVED,
        request_data: Optional[dict] = None,
        response_data: Optional[dict] = None,
        contractor: Optional[str] = None
    ):
        if 200 <= http_status < 300:
            status = AccountEventStatus.SUCCESS
        else:
            status = AccountEventStatus.FAILED
        self.create(
            event_type=AccountEventType.API,
            ip=ip,
            user_agent=user_agent,
            auth_token=auth_token,
            scheme=scheme,
            method=method,
            title=title,
            path=path,
            request_data=request_data,
            http_status=http_status,
            status=status,
            user_id=user.id,
            account_id=user.account_id,
            response_data=response_data,
            direction=direction,
            contractor=contractor,
        )

    def push_notification(
        self,
        title: str,
        request_data: dict,
        account_id: int,
        status: AccountEventStatus,
        response_data: Optional[dict] = None,
    ):
        self.create(
            event_type=AccountEventType.API,
            title=title,
            request_data=request_data,
            status=status,
            account_id=account_id,
            response_data=response_data,
            direction=RequestDirection.SENT,
            contractor='Firebase',
        )

    def email_message(
        self,
        title: str,
        request_data: dict,
        account_id: int,
        contractor: str,
        status: AccountEventStatus,
        response_data: Optional[dict] = None,
    ):
        self.create(
            event_type=AccountEventType.API,
            title=title,
            request_data=request_data,
            status=status,
            account_id=account_id,
            response_data=response_data,
            direction=RequestDirection.SENT,
            contractor=contractor,
        )

    def webhook(
        self,
        title: str,
        path: str,
        request_data: dict,
        account_id: int,
        status: AccountEventStatus,
        http_status: int,
        response_data: Optional[dict] = None,
        user_id: Optional[int] = None
    ):
        self.create(
            event_type=AccountEventType.WEBHOOK,
            title=title,
            path=path,
            request_data=request_data,
            http_status=http_status,
            status=status,
            account_id=account_id,
            response_data=response_data,
            direction=RequestDirection.SENT,
            user_id=user_id,
        )

    def contacts_request(
        self,
        user: UserModel,
        title: str,
        path: str,
        http_status: int,
        response_data: Optional[dict] = None,
        contractor: Optional[str] = None
    ):
        if 200 <= http_status < 300:
            status = AccountEventStatus.SUCCESS
        else:
            status = AccountEventStatus.FAILED

        self.create(
            event_type=AccountEventType.API,
            scheme='https',
            method='GET',
            title=title,
            path=path,
            http_status=http_status,
            status=status,
            user_id=user.id,
            account_id=user.account_id,
            response_data=response_data,
            direction=RequestDirection.SENT,
            contractor=contractor,
        )

    def system_log(
        self,
        user: UserModel,
        title: str,
        status: AccountEventStatus.LITERALS = AccountEventStatus.SUCCESS,
        data: Optional[dict] = None,
    ):

        self.create(
            event_type=AccountEventType.SYSTEM,
            title=title,
            status=status,
            user=user,
            account_id=user.account_id,
            response_data=data
        )

    def log_auth0(
        self,
        title: str,
        status: AccountEventStatus.LITERALS = AccountEventStatus.SUCCESS,
        data: Optional[dict] = None,
    ):

        self.create(
            event_type=AccountEventType.AUTH,
            title=title,
            status=status,
            response_data=data
        )