"""Documentation for validated templates and partially populated drafts."""

from typing import Any

from drf_spectacular.utils import (
    PolymorphicProxySerializer,
    extend_schema_field,
    extend_schema_serializer,
)
from rest_framework import serializers

from src.processes.serializers.templates.field import FieldTemplateSerializer
from src.processes.serializers.templates.fieldset import (
    FieldsetTemplateSerializer,
)
from src.processes.serializers.templates.kickoff import KickoffSerializer
from src.processes.serializers.templates.owner import TemplateOwnerSerializer
from src.processes.serializers.templates.raw_performer import (
    RawPerformerSerializer,
)
from src.processes.serializers.templates.task import TaskTemplateSerializer
from src.processes.serializers.templates.template import (
    TemplateListSerializer,
    TemplateSerializer,
)


class ActiveTemplateSerializer(TemplateSerializer):
    is_active = serializers.ChoiceField(choices=[True])
    kickoff = KickoffSerializer()
    owners = serializers.ListField(
        child=TemplateOwnerSerializer(), min_length=1,
    )
    tasks = serializers.ListField(
        child=TaskTemplateSerializer(), min_length=1,
    )
    updated_by = serializers.IntegerField(read_only=True, allow_null=True)


class UnvalidatedDraftField(serializers.JSONField):
    """Document values saved verbatim before template activation."""

    def __init__(self, expected_type: str, **kwargs: Any) -> None:
        super().__init__(
            required=False,
            allow_null=True,
            help_text=(
                f'Normally {expected_type}. Stored as supplied in an inactive '
                'draft; validated only when activating the template.'
            ),
            **kwargs,
        )


class TemplateDraftBooleanField(serializers.JSONField):
    """The draft normalizes any supplied JSON value with bool(value)."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(
            required=False,
            help_text=(
                'Any JSON value is accepted in a draft request. '
                'The response contains bool(value), or false when omitted.'
            ),
            **kwargs,
        )


class TemplateDraftSerializer(serializers.Serializer):
    """Draft JSON is stored before validating nested task/field structures."""

    id = serializers.IntegerField(read_only=True)
    name = UnvalidatedDraftField('a string')
    wf_name_template = UnvalidatedDraftField('a string or null')
    description = UnvalidatedDraftField('a Markdown string')
    is_active = serializers.ChoiceField(choices=[False], default=False)
    is_public = TemplateDraftBooleanField()
    is_embedded = TemplateDraftBooleanField()
    public_success_url = UnvalidatedDraftField('a URL string or null')
    finalizable = UnvalidatedDraftField('a boolean')
    reminder_notification = UnvalidatedDraftField('a boolean')
    completion_notification = UnvalidatedDraftField('a boolean')
    owners = serializers.ListField(
        child=serializers.DictField(), required=False,
    )
    tasks = serializers.ListField(
        child=serializers.DictField(), required=False,
    )
    kickoff = serializers.DictField(required=False)
    public_url = serializers.CharField(read_only=True, required=False)
    embed_url = serializers.CharField(read_only=True, required=False)
    updated_by = serializers.IntegerField(
        read_only=True, required=False, allow_null=True,
    )
    date_updated = serializers.DateTimeField(
        read_only=True, required=False, allow_null=True,
    )
    date_updated_tsp = serializers.FloatField(
        read_only=True, required=False, allow_null=True,
        help_text='Unix timestamp in seconds.',
    )


@extend_schema_field({
    'oneOf': [
        {'type': 'string'},
        {'type': 'integer'},
        {'type': 'object', 'nullable': True, 'enum': [None]},
    ],
    'description': (
        'Unsaved performers retain string, integer or null source IDs. '
        'Automatically assigned user IDs are integers.'
    ),
})
class TemplatePreviewSourceIdField(serializers.JSONField):
    """Source IDs have not passed the saved-template string conversion."""


class TemplatePreviewPerformerSerializer(RawPerformerSerializer):
    source_id = TemplatePreviewSourceIdField(allow_null=True)


class TemplatePreviewFieldSerializer(FieldTemplateSerializer):
    order = serializers.IntegerField(required=False, allow_null=True)


class TemplatePreviewFieldsetSerializer(FieldsetTemplateSerializer):
    shared_fieldset_id = serializers.IntegerField(
        required=False, allow_null=True,
    )
    fields = TemplatePreviewFieldSerializer(many=True, required=False)


@extend_schema_serializer(exclude_fields=['id', 'parents', 'ancestors'])
class TemplatePreviewTaskSerializer(TaskTemplateSerializer):
    raw_performers = TemplatePreviewPerformerSerializer(many=True)
    fields = TemplatePreviewFieldSerializer(many=True, required=False)
    fieldsets = TemplatePreviewFieldsetSerializer(many=True, required=False)


class TemplatePreviewKickoffSerializer(KickoffSerializer):
    class Meta(KickoffSerializer.Meta):
        fields = (*KickoffSerializer.Meta.fields, 'description')

    description = serializers.CharField(allow_blank=True, allow_null=True)
    fields = TemplatePreviewFieldSerializer(many=True, required=False)
    fieldsets = TemplatePreviewFieldsetSerializer(many=True, required=False)


class TemplatePreviewSerializer(serializers.Serializer):
    """Unsaved fill_template_data output, without persistence metadata."""

    name = serializers.CharField(allow_blank=True, allow_null=True)
    wf_name_template = serializers.CharField(allow_blank=True, allow_null=True)
    description = serializers.CharField(allow_blank=True, allow_null=True)
    is_active = serializers.BooleanField()
    finalizable = serializers.BooleanField()
    is_public = serializers.BooleanField()
    owners = TemplateOwnerSerializer(many=True)
    kickoff = TemplatePreviewKickoffSerializer()
    tasks = TemplatePreviewTaskSerializer(many=True)


@extend_schema_serializer(exclude_fields=['workflows_count'])
class OwnedTemplateListSerializer(TemplateListSerializer):
    """The owner-filtered SQL projection does not select workflows_count."""


def template_contract(many: bool = False) -> PolymorphicProxySerializer:
    return PolymorphicProxySerializer(
        component_name='TemplateDocument',
        serializers=[ActiveTemplateSerializer, TemplateDraftSerializer],
        resource_type_field_name=None,
        many=many,
    )
