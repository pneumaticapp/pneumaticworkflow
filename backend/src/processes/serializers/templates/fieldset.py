from drf_spectacular.utils import extend_schema_field
from rest_framework.serializers import (
    ModelSerializer,
    Serializer,
    SerializerMethodField,
)
from src.generics.fields import (
    AccountPrimaryKeyRelatedField,
    DocCharField,
    DocChoiceField,
    DocIntegerField,
)
from src.generics.mixins.serializers import CustomValidationErrorMixin
from src.processes.enums import FieldSetLayout, LabelPosition
from src.processes.models.templates.fieldset import (
    FieldsetTemplate,
)
from src.processes.models.templates.template import Template
from src.processes.serializers.templates.field import (
    FieldTemplateSerializer,
)
from src.processes.serializers.templates.fieldset_rule import (
    FieldSetTemplateRuleSetSerializer,
)


class FieldsetTemplateSerializer(
    ModelSerializer,
    CustomValidationErrorMixin,
):

    class Meta:
        model = FieldsetTemplate
        fields = (
            'title',
            'order',
            'description',
            'api_name',
            'shared_fieldset_id',
            'name',
            'label_position',
            'layout',
            'rulesets',
            'fields',
        )

    shared_fieldset_id = AccountPrimaryKeyRelatedField(
        queryset=FieldsetTemplate.objects.shared(),
        required=True,
        example=1,
    )
    api_name = DocCharField(
        required=False,
        max_length=200,
        example='feedback-fieldset',
    )
    name = DocCharField(
        required=False,
        max_length=1000,
        example='Feedback block',
    )
    title = DocCharField(
        required=False,
        allow_blank=True,
        example='Feedback form',
    )
    description = DocCharField(
        required=False,
        allow_blank=True,
        example='Leave a review about your order',
    )
    label_position = DocChoiceField(
        choices=LabelPosition.CHOICES,
        required=False,
        example=LabelPosition.TOP,
    )
    layout = DocChoiceField(
        choices=FieldSetLayout.CHOICES,
        required=False,
        example=FieldSetLayout.VERTICAL,
    )
    rulesets = FieldSetTemplateRuleSetSerializer(
        many=True,
        required=False,
        default=list,
    )
    fields = FieldTemplateSerializer(
        many=True,
        required=False,
        default=list,
    )
    order = DocIntegerField(
        required=False,
        default=0,
        min_value=0,
        example=0,
    )


class FieldsetUsageSerializer(Serializer):
    id = DocIntegerField(read_only=True, example=1)
    name = DocCharField(read_only=True, example='Employee onboarding')


class SharedFieldsetTemplateSerializer(
    CustomValidationErrorMixin,
    ModelSerializer,
):

    class Meta:
        model = FieldsetTemplate
        fields = (
            'id',
            'title',
            'order',
            'description',
            'api_name',
            'name',
            'label_position',
            'layout',
            'rulesets',
            'fields',
            'usage',
        )

    id = DocIntegerField(read_only=True, example=1)
    api_name = DocCharField(
        required=False,
        max_length=200,
        example='feedback-fieldset',
    )
    name = DocCharField(
        max_length=1000,
        example='Feedback block',
    )
    title = DocCharField(
        required=False,
        allow_blank=True,
        example='Feedback form',
    )
    description = DocCharField(
        required=False,
        allow_blank=True,
        example='Leave a review about your order',
    )
    label_position = DocChoiceField(
        choices=LabelPosition.CHOICES,
        required=False,
        example=LabelPosition.TOP,
    )
    layout = DocChoiceField(
        choices=FieldSetLayout.CHOICES,
        required=False,
        example=FieldSetLayout.VERTICAL,
    )
    order = DocIntegerField(
        required=False,
        default=0,
        min_value=0,
        example=0,
    )
    rulesets = FieldSetTemplateRuleSetSerializer(
        many=True,
        required=False,
        default=list,
    )
    fields = FieldTemplateSerializer(
        many=True,
        required=False,
        default=list,
    )
    usage = SerializerMethodField()

    @extend_schema_field(FieldsetUsageSerializer(many=True))
    def get_usage(self, instance: FieldsetTemplate) -> list:
        prefetched = getattr(instance, '_prefetched_objects_cache', {})
        if 'child_fieldsets' in prefetched:
            usage = {}
            for child in instance.child_fieldsets.all():
                usage[child.template_id] = {
                    'id': child.template_id,
                    'name': child.template.name,
                }
            qst = sorted(usage.values(), key=lambda elem: elem['id'])
        else:
            qst = (
                Template.objects.filter(
                    id__in=instance.child_fieldsets.values('template_id'),
                )
                .order_by('id')
                .distinct()
                .values('id', 'name')
            )
        return FieldsetUsageSerializer(qst, many=True).data
