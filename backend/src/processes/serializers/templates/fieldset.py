from django.core.validators import MinValueValidator
from rest_framework.fields import CharField, ChoiceField, IntegerField
from rest_framework.serializers import ModelSerializer, SerializerMethodField
from src.generics.fields import (
    RelatedApiNameListField, AccountPrimaryKeyRelatedField,
)
from src.generics.mixins.serializers import CustomValidationErrorMixin
from src.processes.enums import FieldSetLayout, LabelPosition
from src.processes.models.templates.fieldset import (
    FieldsetTemplate,
    FieldsetTemplateRule,
)
from src.processes.models.templates.template import Template
from src.processes.serializers.templates.field import (
    FieldTemplateSerializer,
)


class FieldsetTemplateRuleSerializer(
    CustomValidationErrorMixin,
    ModelSerializer,
):

    class Meta:
        model = FieldsetTemplateRule
        fields = (
            'type',
            'value',
            'api_name',
            'fields',
        )

    api_name = CharField(required=False, max_length=200)
    fields = RelatedApiNameListField(
        required=False,
        allow_empty=True,
        default=list,
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
            'rules',
            'fields',
        )

    shared_fieldset_id = AccountPrimaryKeyRelatedField(
        queryset=FieldsetTemplate.objects.shared(),
        required=True,
    )
    api_name = CharField(required=False, max_length=200)
    name = CharField(required=False, max_length=1000)
    label_position = ChoiceField(
        choices=LabelPosition.CHOICES,
        required=False,
    )
    layout = ChoiceField(
        choices=FieldSetLayout.CHOICES,
        required=False,
    )
    rules = FieldsetTemplateRuleSerializer(
        many=True,
        required=False,
        default=list,
    )
    fields = FieldTemplateSerializer(
        many=True,
        required=False,
        default=list,
    )
    order = IntegerField(
        required=False,
        default=0,
        validators=[MinValueValidator(0)],
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
            'rules',
            'fields',
            'usage',
        )

    rules = FieldsetTemplateRuleSerializer(
        many=True,
        required=False,
        default=list,
    )
    fields = FieldTemplateSerializer(
        many=True,
        required=False,
        default=list,
    )
    api_name = CharField(required=False, max_length=200)
    usage = SerializerMethodField()

    def get_usage(self, instance: FieldsetTemplate) -> list:
        prefetched = getattr(instance, '_prefetched_objects_cache', {})
        if 'child_fieldsets' in prefetched:
            usage = {}
            for child in instance.child_fieldsets.all():
                usage[child.template_id] = {
                    'id': child.template_id,
                    'name': child.template.name,
                }
            return sorted(usage.values(), key=lambda elem: elem['id'])
        return list(
            Template.objects.filter(
                id__in=instance.child_fieldsets.values('template_id'),
            )
            .order_by('id')
            .distinct()
            .values('id', 'name'),
        )
