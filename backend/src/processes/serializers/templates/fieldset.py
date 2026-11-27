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
        help_text=(
            'Id of the shared fieldset this template '
            'binding is copied from.'
        ),
    )
    api_name = DocCharField(
        required=False,
        max_length=200,
        example='feedback-fieldset',
        help_text='Stable unique identifier. Generated if omitted.',
    )
    name = DocCharField(
        required=False,
        max_length=1000,
        example='Feedback block',
        help_text='Internal name shown in the fieldset catalog.',
    )
    title = DocCharField(
        required=False,
        allow_blank=True,
        example='Feedback form',
        help_text=(
            'Heading displayed above the fieldset in the form.'
        ),
    )
    description = DocCharField(
        required=False,
        allow_blank=True,
        example='Leave a review about your order',
        help_text='Helper text shown under the fieldset heading.',
    )
    label_position = DocChoiceField(
        choices=LabelPosition.CHOICES,
        required=False,
        example=LabelPosition.TOP,
        help_text=(
            'Where field labels are placed relative to '
            'inputs: `top` or `left`.'
        ),
    )
    layout = DocChoiceField(
        choices=FieldSetLayout.CHOICES,
        required=False,
        example=FieldSetLayout.VERTICAL,
        help_text=(
            'How fields are arranged: `vertical` or '
            '`horizontal`.'
        ),
    )
    rulesets = FieldSetTemplateRuleSetSerializer(
        many=True,
        required=False,
        default=list,
        help_text=(
            'Fieldset-level rules. Conditions in '
            '`groups_or` are combined with OR; '
            'conditions inside each group with AND.'
        ),
    )
    fields = FieldTemplateSerializer(
        many=True,
        required=False,
        default=list,
        help_text='Fields that belong to this fieldset.',
    )
    order = DocIntegerField(
        required=False,
        default=0,
        min_value=0,
        example=0,
        help_text=(
            'Display order among fieldsets on the same '
            'step. Starts at 0.'
        ),
    )


class FieldsetUsageSerializer(Serializer):
    id = DocIntegerField(
        read_only=True,
        example=1,
        help_text='Template id.',
    )
    name = DocCharField(
        read_only=True,
        example='Employee onboarding',
        help_text='Template name.',
    )


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

    id = DocIntegerField(
        read_only=True,
        example=1,
        help_text='Shared fieldset id. Read-only.',
    )
    api_name = DocCharField(
        required=False,
        max_length=200,
        example='feedback-fieldset',
        help_text='Stable unique identifier. Generated if omitted.',
    )
    name = DocCharField(
        max_length=1000,
        example='Feedback block',
        help_text='Internal name shown in the fieldset catalog.',
    )
    title = DocCharField(
        required=False,
        allow_blank=True,
        example='Feedback form',
        help_text=(
            'Heading displayed above the fieldset in the form.'
        ),
    )
    description = DocCharField(
        required=False,
        allow_blank=True,
        example='Leave a review about your order',
        help_text='Helper text shown under the fieldset heading.',
    )
    label_position = DocChoiceField(
        choices=LabelPosition.CHOICES,
        required=False,
        example=LabelPosition.TOP,
        help_text=(
            'Where field labels are placed relative to '
            'inputs: `top` or `left`.'
        ),
    )
    layout = DocChoiceField(
        choices=FieldSetLayout.CHOICES,
        required=False,
        example=FieldSetLayout.VERTICAL,
        help_text=(
            'How fields are arranged: `vertical` or `horizontal`.'
        ),
    )
    order = DocIntegerField(
        required=False,
        default=0,
        min_value=0,
        example=0,
        help_text=(
            'Display order among fieldsets on the same '
            'step. Starts at 0.'
        ),
    )
    rulesets = FieldSetTemplateRuleSetSerializer(
        many=True,
        required=False,
        default=list,
        help_text=(
            'Fieldset-level rules. Conditions in '
            '`groups_or` are combined with OR; '
            'conditions inside each group with AND.'
        ),
    )
    fields = FieldTemplateSerializer(
        many=True,
        required=False,
        default=list,
        help_text='Fields that belong to this fieldset.',
    )
    usage = SerializerMethodField(
        help_text=(
            'Templates that use this shared fieldset. '
            'Non-empty usage makes the fieldset read-only.'
        ),
    )

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
