from typing import Optional, List
from django.contrib.auth import get_user_model
from django.utils import timezone
from pneumatic_backend.generics.mixins.services import ClsCacheMixin
from pneumatic_backend.processes.models import Template
from pneumatic_backend.processes.enums import TemplateIntegrationType
from pneumatic_backend.processes.entities import (
    TemplateIntegrationsData,
    PrivateTemplateIntegrationsData
)
from pneumatic_backend.accounts.models import Account
from pneumatic_backend.processes.models import TemplateIntegrations
from pneumatic_backend.processes.api_v2.serializers.template.\
    integrations import TemplateIntegrationsSerializer
from pneumatic_backend.analytics.services import AnalyticService


UserModel = get_user_model()


class TemplateIntegrationsService(ClsCacheMixin):

    cache_timeout = 86400  # 24 hours in seconds
    cache_key_prefix = 't_int'
    serializer_cls = TemplateIntegrationsSerializer

    def __init__(
        self,
        account: Account,
        user: Optional[UserModel] = None,
        anonymous_id: str = None,
        is_superuser: bool = False
    ):
        self.account = account
        self.user_id = user.id if user else None
        self.anonymous_id = anonymous_id
        self.is_superuser = is_superuser

    def _update_instance_attr(
        self,
        attr_name: TemplateIntegrationType.LITERALS,
        value: bool,
        template_id: int
    ) -> TemplateIntegrations:

        instance = TemplateIntegrations.objects.get(
            template_id=template_id
        )
        setattr(instance, attr_name, value)
        if value is True:
            if getattr(instance, f'{attr_name}_date', None) is None:
                if attr_name != TemplateIntegrationType.WEBHOOKS:
                    AnalyticService.templates_integrated(
                        template_id=template_id,
                        account_id=instance.account_id,
                        is_superuser=self.is_superuser,
                        user_id=self.user_id,
                        anonymous_id=self.anonymous_id,
                        integration_type=attr_name
                    )
            setattr(instance, f'{attr_name}_date', timezone.now())
        instance.save()
        return instance

    def _set_attr_value(
        self,
        attr_name: TemplateIntegrationType.LITERALS,
        value: bool,
        template_id: int
    ):

        instance = self._update_instance_attr(
            template_id=template_id,
            attr_name=attr_name,
            value=value
        )
        self._set_cache(
            key=template_id,
            value=instance,
        )

    def create_integrations_for_template(
        self,
        template: Template,
        webhooks: Optional[bool] = None
    ) -> TemplateIntegrations:

        instance = TemplateIntegrations.objects.create(
            account_id=template.account_id,
            template_id=template.id,
        )
        webhooks_exists = (
            template.account.webhook_set.all().exists()
        ) if webhooks is None else webhooks
        if webhooks_exists:
            self._set_attr_value(
                template_id=template.id,
                attr_name=TemplateIntegrationType.WEBHOOKS,
                value=True
            )
        return instance

    def _shared_date_expired(self, tsp: float) -> bool:
        expiration_date = timezone.now().timestamp() - self.cache_timeout
        return expiration_date > tsp

    def _get_template_integrations_data(
        self,
        template_id: int
    ) -> PrivateTemplateIntegrationsData:

        """ Returns template integrations data """

        data = self._get_cache(key=template_id)
        if data is None:
            instance = TemplateIntegrations.objects.get(
                template_id=template_id
            )
            data = self._set_cache(
                key=template_id,
                value=instance
            )
        return data

    def get_template_integrations_data(
        self,
        template_id: int
    ) -> TemplateIntegrationsData:

        data = self._get_template_integrations_data(template_id)
        return TemplateIntegrationsData(
            id=data['id'],
            shared=data['shared'],
            api=data['api'],
            zapier=data['zapier'],
            webhooks=data['webhooks'],
        )

    def get_integrations(
        self,
        template_id: Optional[list] = None,
    ) -> List[TemplateIntegrationsData]:

        """ Returns templates integrations data for the given templates ids
            or for all templates ids """

        result = []
        if template_id is None:
            template_id = Template.objects.on_account(
                self.account.id
            ).exclude_onboarding().only_ids()
        for elem in template_id:
            result.append(self.get_template_integrations_data(elem))
        return result

    def public_api_request(
        self,
        template: Template,
    ):

        """ Sets "Shared" flag for template integrations
            after receiving a request on a public API """

        data = self._get_template_integrations_data(template.id)
        if data[TemplateIntegrationType.SHARED] is False:
            self._set_attr_value(
                attr_name=TemplateIntegrationType.SHARED,
                value=True,
                template_id=template.id
            )

    def template_updated(
        self,
        template: Template,
    ):

        """ Disable "Shared" flag if:
            - is_shared or is_embedded deactivated
            - template status 'draft'
            Enable "Shared" flag if:
            - "Shared" flag is disabled,
              but has been enabled in the last 24 hours
              (just template has been edited)
        """

        data = self._get_template_integrations_data(template.id)
        share_enabled = (
            template.is_active and (
                template.is_public or template.is_embedded
            )
        )
        share_value = data[TemplateIntegrationType.SHARED]
        shared_date = data.get('shared_date_tsp')
        if share_enabled and not share_value:
            if shared_date and not self._shared_date_expired(shared_date):
                self._set_attr_value(
                    attr_name=TemplateIntegrationType.SHARED,
                    value=True,
                    template_id=template.id
                )
        elif not share_enabled and share_value:
            self._set_attr_value(
                attr_name=TemplateIntegrationType.SHARED,
                value=False,
                template_id=template.id
            )

    def api_request(
        self,
        template: Template,
        user_agent: Optional[str] = None
    ):

        """ Sets API and Zapier flag in for template integrations """

        data = self._get_template_integrations_data(template.id)
        if data[TemplateIntegrationType.API] is False:
            self._set_attr_value(
                attr_name=TemplateIntegrationType.API,
                value=True,
                template_id=template.id
            )
        if (
            user_agent == 'Zapier'
            and data[TemplateIntegrationType.ZAPIER] is False
        ):
            self._set_attr_value(
                attr_name=TemplateIntegrationType.ZAPIER,
                value=True,
                template_id=template.id
            )

    def webhooks_subscribed(self):

        """ Enable webhooks flag in all account template integrations """

        for data in self.get_integrations():
            if data[TemplateIntegrationType.WEBHOOKS] is False:
                self._set_attr_value(
                    attr_name=TemplateIntegrationType.WEBHOOKS,
                    value=True,
                    template_id=data['id']
                )

    def webhooks_unsubscribed(self):

        """ Disable webhooks flag in all account template integrations """

        for data in self.get_integrations():
            if data[TemplateIntegrationType.WEBHOOKS] is True:
                self._set_attr_value(
                    attr_name=TemplateIntegrationType.WEBHOOKS,
                    value=False,
                    template_id=data['id']
                )
