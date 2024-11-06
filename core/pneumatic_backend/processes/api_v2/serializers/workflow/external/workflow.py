from django.contrib.auth import get_user_model
from rest_framework.serializers import (
    Serializer,
    DictField,
)
from drf_recaptcha.fields import ReCaptchaV2Field
from pneumatic_backend.generics.mixins.serializers import (
    CustomValidationErrorMixin
)


UserModel = get_user_model()


class ExternalWorkflowCreateSerializer(
    CustomValidationErrorMixin,
    Serializer
):

    class Meta:
        fields = (
            'fields',
        )

    fields = DictField(allow_empty=True, required=False, allow_null=True)

    def validate(self, data):
        data['fields'] = data.get('fields', {})
        return data


class SecuredExternalWorkflowCreateSerializer(
    ExternalWorkflowCreateSerializer
):
    class Meta:
        fields = (
            'fields',
            'captcha',
        )
    captcha = ReCaptchaV2Field()
