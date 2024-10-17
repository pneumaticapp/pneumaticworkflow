from typing import Optional
from django.db import transaction
from django.contrib.auth import get_user_model
from pneumatic_backend.webhooks.models import WebHook
from pneumatic_backend.generics.mixins.services import DefaultClsCacheMixin
from pneumatic_backend.webhooks.enums import HookEvent
from pneumatic_backend.webhooks import exceptions
from pneumatic_backend.processes.api_v2.services.templates\
    .integrations import TemplateIntegrationsService
from pneumatic_backend.analytics.services import AnalyticService


UserModel = get_user_model()


class WebhookService:

    def __init__(
        self,
        user: UserModel,
        is_superuser: bool = False
    ):
        self.user = user
        self.account = user.account
        self.is_superuser = is_superuser

    def _get_events(self) -> set:
        return HookEvent.VALUES

    def _validate_event(self, event: str):
        if event not in self._get_events():
            raise exceptions.InvalidEventException()

    def unsubscribe(self):
        WebHook.objects.on_account(self.account.id).delete()
        service = TemplateIntegrationsService(
            account=self.account,
            user=self.user,
            is_superuser=self.is_superuser
        )
        service.webhooks_unsubscribed()

    def unsubscribe_event(self, event: str):
        self._validate_event(event)
        WebHook.objects.on_account(
            self.account.id
        ).for_event(event).delete()
        if not WebHook.objects.on_account(
            self.account.id
        ).exists():
            service = TemplateIntegrationsService(
                account=self.account,
                user=self.user,
                is_superuser=self.is_superuser
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
                    target=url
                ) for event in self._get_events()
            )
            service = TemplateIntegrationsService(
                account=self.account,
                user=self.user,
                is_superuser=self.is_superuser
            )
            service.webhooks_subscribed()
            AnalyticService.accounts_webhooks_subscribed(
                user=self.user,
                is_superuser=self.is_superuser
            )

    def subscribe_event(
        self,
        url: str,
        event: str
    ):
        self._validate_event(event)
        events_exists = WebHook.objects.on_account(self.account.id).exists()
        WebHook.objects.update_or_create(
            user_id=self.user.id,
            event=event,
            account_id=self.account.id,
            defaults={'target': url}
        )
        service = TemplateIntegrationsService(
            account=self.account,
            user=self.user,
            is_superuser=self.is_superuser
        )
        service.webhooks_subscribed()
        if not events_exists:
            AnalyticService.accounts_webhooks_subscribed(
                user=self.user,
                is_superuser=self.is_superuser
            )

    def get_event_url(
        self,
        event: str,
    ) -> Optional[str]:
        self._validate_event(event)
        hook = WebHook.objects.on_account(
            self.account.id
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
