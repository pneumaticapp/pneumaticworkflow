from rest_framework.serializers import ModelSerializer, SerializerMethodField
from pneumatic_backend.accounts.models import Account


class PublicAccountSerializer(ModelSerializer):

    class Meta:
        model = Account
        fields = (
            'id',
            'name',
            'logo_lg',
            'logo_sm',
            'language',
            'timezone',
            'date_fmt',
            'date_fdw',
        )

    language = SerializerMethodField()
    timezone = SerializerMethodField()
    date_fmt = SerializerMethodField()
    date_fdw = SerializerMethodField()

    def get_language(self, obj):
        return self.context['account_owner'].language

    def get_timezone(self, obj):
        return self.context['account_owner'].timezone

    def get_date_fmt(self, obj):
        return self.context['account_owner'].date_fmt

    def get_date_fdw(self, obj):
        return self.context['account_owner'].date_fdw
