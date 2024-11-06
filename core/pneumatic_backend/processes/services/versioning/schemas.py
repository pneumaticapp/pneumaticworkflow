from rest_framework import serializers
from pneumatic_backend.services.markdown import MarkdownService
from pneumatic_backend.processes.models import (
    Template,
    TaskTemplate,
    Kickoff,
    FieldTemplate,
    FieldTemplateSelection,
    PredicateTemplate,
    RuleTemplate,
    ConditionTemplate,
    RawPerformerTemplate,
    ChecklistTemplate,
    ChecklistTemplateSelection,
    RawDueDateTemplate,
)


class SelectionSchemaV1(serializers.ModelSerializer):

    # TODO deprecate id

    class Meta:
        model = FieldTemplateSelection
        fields = (
            'id',
            'value',
            'api_name',
        )


class FieldSchemaV1(serializers.ModelSerializer):

    # TODO deprecate id

    class Meta:
        model = FieldTemplate
        fields = (
            'id',
            'name',
            'type',
            'description',
            'is_required',
            'api_name',
            'order',
            'default',
            'selections',
        )

    selections = SelectionSchemaV1(
        many=True,
        allow_null=True,
        allow_empty=True,
        required=False,
    )


class KickoffSchemaV1(serializers.ModelSerializer):

    class Meta:
        model = Kickoff
        fields = (
            'id',
            'description',
            'clear_description',
            'fields',
        )

    fields = FieldSchemaV1(many=True, allow_null=True, allow_empty=True)
    clear_description = serializers.SerializerMethodField(allow_null=True)

    def get_clear_description(self, obj):
        return MarkdownService.clear(obj.description)


class PredicateSchemaV1(serializers.ModelSerializer):

    # TODO deprecate id

    class Meta:
        model = PredicateTemplate
        fields = (
            'id',
            'operator',
            'field',
            'field_type',
            'value',
            'api_name',
        )


class RuleSchemaV1(serializers.ModelSerializer):

    # TODO deprecate id

    class Meta:
        model = RuleTemplate
        fields = (
            'id',
            'predicates',
            'api_name',
        )

    predicates = PredicateSchemaV1(many=True)


class ConditionSchemaV1(serializers.ModelSerializer):

    # TODO deprecate id

    class Meta:
        model = ConditionTemplate
        fields = (
            'id',
            'action',
            'rules',
            'order',
            'api_name',
        )

    rules = RuleSchemaV1(many=True)


class RawPerformerTemplateFieldSchemaV1(serializers.ModelSerializer):
    class Meta:
        model = FieldTemplate
        fields = (
            'api_name',
        )


class RawPerformerTemplateSchemaV1(serializers.ModelSerializer):

    # TODO deprecate id

    class Meta:
        model = RawPerformerTemplate
        fields = (
            'id',
            'type',
            'user_id',
            'api_name',
            'field',
        )

    field = RawPerformerTemplateFieldSchemaV1(allow_null=True, required=False)


class ChecklistTemplateSelectionSchemeV1(serializers.ModelSerializer):

    class Meta:
        model = ChecklistTemplateSelection
        fields = (
            'api_name',
            'value',
        )


class CheckListTemplateSchemeV1(serializers.ModelSerializer):

    class Meta:
        model = ChecklistTemplate
        fields = (
            'api_name',
            'selections',
        )

    selections = ChecklistTemplateSelectionSchemeV1(many=True)


class RawDueDateTemplateSchemaV1(serializers.ModelSerializer):

    class Meta:
        model = RawDueDateTemplate
        fields = (
            'api_name',
            'rule',
            'duration',
            'duration_months',
            'source_id',
        )


class TaskSchemaV1(serializers.ModelSerializer):

    # TODO deprecate id

    class Meta:
        model = TaskTemplate
        fields = (
            'id',
            'api_name',
            'name',
            'description',
            'clear_description',
            'number',
            'require_completion_by_all',
            'fields',
            'delay',
            'conditions',
            'raw_performers',
            'raw_due_date',
            'checklists',
        )

    fields = FieldSchemaV1(many=True, allow_null=True, allow_empty=True)
    conditions = ConditionSchemaV1(
        many=True,
        allow_null=True,
        allow_empty=True,
    )
    raw_performers = RawPerformerTemplateSchemaV1(
        many=True,
        allow_null=True,
        allow_empty=True
    )
    checklists = CheckListTemplateSchemeV1(
        many=True,
        required=False
    )
    raw_due_date = RawDueDateTemplateSchemaV1(required=False)
    clear_description = serializers.SerializerMethodField(allow_null=True)

    def get_clear_description(self, obj):
        return MarkdownService.clear(obj.description)


class TemplateSchemaV1(serializers.ModelSerializer):
    kickoff = KickoffSchemaV1(
        required=False,
        allow_null=True,
        source='kickoff_instance',
    )
    tasks = TaskSchemaV1(many=True)

    class Meta:
        model = Template
        fields = (
            'id',
            'kickoff',
            'tasks',
            'finalizable',
            'description',
            'template_owners',
            'updated_by',
            'wf_name_template',
        )
