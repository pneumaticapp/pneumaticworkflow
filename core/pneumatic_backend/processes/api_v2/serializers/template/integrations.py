from rest_framework.serializers import (
    Serializer,
    ModelSerializer,
    CharField,
    IntegerField,
)
from pneumatic_backend.generics.fields import TimeStampField
from pneumatic_backend.generics.mixins.serializers import (
    CustomValidationErrorMixin,
    ValidationUtilsMixin,
)
from pneumatic_backend.processes.models import TemplateIntegrations


class TemplateIntegrationsFilterSerializer(
    CustomValidationErrorMixin,
    ValidationUtilsMixin,
    Serializer,
):

    template_id = CharField(required=False)

    def validate_template_id(self, value):
        return self.get_valid_list_integers(value)


class TemplateIntegrationsSerializer(
    ModelSerializer
):

    class Meta:
        model = TemplateIntegrations
        fields = (
            'id',
            'shared',
            'shared_date_tsp',
            'api',
            'api_date_tsp',
            'zapier',
            'zapier_date_tsp',
            'webhooks',
            'webhooks_date_tsp',
        )

    id = IntegerField(source='template_id', read_only=True)
    shared_date_tsp = TimeStampField(source='shared_date', read_only=True)
    api_date_tsp = TimeStampField(source='api_date', read_only=True)
    zapier_date_tsp = TimeStampField(source='zapier_date', read_only=True)
    webhooks_date_tsp = TimeStampField(source='webhooks_date', read_only=True)
