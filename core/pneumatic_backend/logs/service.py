from typing import Optional
from pneumatic_backend.generics.base.service import BaseModelService
from pneumatic_backend.logs.models import AccountEvent
from django.contrib.auth import get_user_model
from pneumatic_backend.logs.enums import (
    AccountEventStatus,
    AccountEventType,
    RequestDirection,
)


UserModel = get_user_model()


class AccountLogService(BaseModelService):

    def _create_instance(
        self,
        event_type: AccountEventType,
        path: Optional[str] = None,
        method: Optional[str] = None,
        scheme: Optional[str] = None,
        auth_token: Optional[str] = None,
        user_agent: Optional[str] = None,
        ip: Optional[str] = None,
        body: Optional[dict] = None,
        http_status: Optional[int] = None,
        user_id: Optional[int] = None,
        account_id: Optional[int] = None,
        error: Optional[dict] = None,
        contractor: str = None,
        status: AccountEventStatus = AccountEventStatus.PENDING,
        direction: RequestDirection = RequestDirection.RECEIVED,
        **kwargs
    ):

        self.instance = AccountEvent.objects.create(
            event_type=event_type,
            ip=ip,
            user_agent=user_agent,
            auth_token=auth_token,
            scheme=scheme,
            method=method,
            path=path,
            body=body,
            http_status=http_status,
            user_id=user_id,
            account_id=account_id,
            error=error,
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
        path: str,
        http_status: int,
        direction: RequestDirection = RequestDirection.RECEIVED,
        body: Optional[dict] = None,
        response_data: Optional[dict] = None,
        contractor: Optional[str] = None
    ):
        if 200 <= http_status < 300:
            status = AccountEventStatus.SUCCESS
            error = None
        else:
            status = AccountEventStatus.FAILED
            error = response_data

        self.create(
            event_type=AccountEventType.API,
            ip=ip,
            user_agent=user_agent,
            auth_token=auth_token,
            scheme=scheme,
            method=method,
            path=path,
            body=body,
            http_status=http_status,
            status=status,
            user_id=user.id,
            account_id=user.account_id,
            error=error,
            direction=direction,
            contractor=contractor,
        )

    def push_notification(
        self,
        path: str,
        body: dict,
        account_id: int,
        status: AccountEventStatus,
        error: Optional[dict] = None,
    ):
        self.create(
            event_type=AccountEventType.API,
            path=path,
            body=body,
            status=status,
            account_id=account_id,
            error=error,
            direction=RequestDirection.SENT,
            contractor='Firebase',
        )
