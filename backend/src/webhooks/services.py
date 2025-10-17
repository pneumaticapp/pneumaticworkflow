import json
from typing import Optional

import requests
from django.contrib.auth import get_user_model
from django.db import transaction

from src.analytics.services import AnalyticService
from src.generics.mixins.services import DefaultClsCacheMixin
from src.logs.enums import (
    AccountEventStatus,
)
from src.logs.service import AccountLogService
from src.processes.services.templates.integrations import (
    TemplateIntegrationsService,
)
from src.utils.logging import (
    SentryLogLevel,
    capture_sentry_message,
)
from src.webhooks import exceptions
from src.webhooks.enums import HookEvent
from src.webhooks.models import WebHook

UserModel = get_user_model()


class WebhookService:

    def __init__(
        self,
        user: UserModel,
        is_superuser: bool = False,
    ):
        self.user = user
        self.account = user.account
        self.is_superuser = is_superuser

    def _get_events(self) -> set:
        return HookEvent.VALUES

    def _validate_event(self, event: str):
        if event not in self._get_events():
            raise exceptions.InvalidEventException

    def unsubscribe(self):
        WebHook.objects.on_account(self.account.id).delete()
        service = TemplateIntegrationsService(
            account=self.account,
            user=self.user,
            is_superuser=self.is_superuser,
        )
        service.webhooks_unsubscribed()

    def unsubscribe_event(self, event: str):
        self._validate_event(event)
        WebHook.objects.on_account(
            self.account.id,
        ).for_event(event).delete()
        if not WebHook.objects.on_account(
            self.account.id,
        ).exists():
            service = TemplateIntegrationsService(
                account=self.account,
                user=self.user,
                is_superuser=self.is_superuser,
            )
            service.webhooks_unsubscribed()

    def subscribe(self, url: str):
        with transaction.atomic():
            WebHook.objects.on_account(self.account.id).delete()
            WebHook.objects.bulk_create(
                WebHook(
                    user_id=self.user.id,
                    event=event,
                    account_id=self.account.id,
                    target=url,
                ) for event in self._get_events()
            )
            service = TemplateIntegrationsService(
                account=self.account,
                user=self.user,
                is_superuser=self.is_superuser,
            )
            service.webhooks_subscribed()
            AnalyticService.accounts_webhooks_subscribed(
                user=self.user,
                is_superuser=self.is_superuser,
            )

    def subscribe_event(
        self,
        url: str,
        event: str,
    ):
        self._validate_event(event)
        events_exists = WebHook.objects.on_account(self.account.id).exists()
        WebHook.objects.update_or_create(
            user_id=self.user.id,
            event=event,
            account_id=self.account.id,
            defaults={'target': url},
        )
        service = TemplateIntegrationsService(
            account=self.account,
            user=self.user,
            is_superuser=self.is_superuser,
        )
        service.webhooks_subscribed()
        if not events_exists:
            AnalyticService.accounts_webhooks_subscribed(
                user=self.user,
                is_superuser=self.is_superuser,
            )

    def get_event_url(
        self,
        event: str,
    ) -> Optional[str]:
        self._validate_event(event)
        hook = WebHook.objects.on_account(
            self.account.id,
        ).for_event(event).first()
        return hook.target if hook else None

    def get_events(self) -> list:
        data = {
            event: {'url': None, 'event': event}
            for event in self._get_events()
        }
        for hook in WebHook.objects.on_account(self.account.id):
            data[hook.event]['url'] = hook.target
        return list(data.values())


class WebhookDeliverer:

    def send(
        self,
        event: HookEvent.LITERALS,
        user_id: int,
        account_id: int,
        payload: dict,
    ):

        hooks = WebHook.objects.on_account(account_id).for_event(event)
        for hook in hooks:
            status = AccountEventStatus.SUCCESS
            error = {}
            hook_payload = {'hook': hook.dict(), **payload}
            http_status = None
            try:
                response = requests.post(
                    url=hook.target,
                    data=json.dumps(hook_payload),
                    headers={'Content-Type': 'application/json'},
                )
            except ConnectionError as e:
                capture_sentry_message(
                    message='HttpException sending webhook',
                    data={
                        'request_url': hook.target,
                        'exception': str(e),
                    },
                    level=SentryLogLevel.INFO,
                )
                status = AccountEventStatus.FAILED
                error['ConnectionError'] = str(e)
                raise e
            else:
                http_status = response.status_code
                if not response.ok:
                    data = {
                        'request_url': hook.target,
                        'response_status': response.status_code,
                    }
                    if response.status_code != 404:
                        content_type = response.headers.get('content-type', '')
                        if 'text' in content_type:
                            data['response_text'] = response.text
                        elif 'application/json' in content_type:
                            data['response_json'] = response.json()
                    capture_sentry_message(
                        message='Error sending webhook',
                        data=data,
                        level=SentryLogLevel.INFO,
                    )
                    status = AccountEventStatus.FAILED
                    http_status = response.status_code
                    error['response'] = data
                if response.status_code >= 500:
                    raise ConnectionError(
                        f'Error sending webhook ({response.status_code})',
                    )
            finally:
                AccountLogService().webhook(
                    title=f'Webhook: {hook.event}',
                    path=hook.target,
                    request_data=hook_payload,
                    account_id=account_id,
                    status=status,
                    http_status=http_status,
                    response_data=error,
                    user_id=user_id,
                )


class WebhookBufferService(DefaultClsCacheMixin):

    default_cache_key = 'wh_buffer'
    cache_timeout = 600

    @classmethod
    def push(cls, data: dict):
        value = cls._get_cache(default=[])
        value.append(data)
        cls._set_cache(value)

    @classmethod
    def get_list(cls) -> list:
        data = cls._get_cache(default=[])
        if isinstance(data, list):
            data.reverse()
        else:
            data = []
        return data

    @classmethod
    def clear(cls):
        cls._delete_cache()
