from rest_framework import serializers
from src.services.markdown import MarkdownService
from src.processes.models import (
    Template,
    TemplateOwner,
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

    class Meta:
        model = FieldTemplateSelection
        fields = (
            'value',
            'api_name',
        )


class FieldSchemaV1(serializers.ModelSerializer):

    class Meta:
        model = FieldTemplate
        fields = (
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
            'fields',
        )

    fields = FieldSchemaV1(many=True, allow_null=True, allow_empty=True)


class TemplateOwnerSchemaV1(serializers.ModelSerializer):
    class Meta:
        model = TemplateOwner
        fields = (
            'type',
            'user_id',
            'group_id',
            'api_name',
        )


class PredicateSchemaV1(serializers.ModelSerializer):

    class Meta:
        model = PredicateTemplate
        fields = (
            'operator',
            'field',
            'field_type',
            'value',
            'api_name',
        )


class RuleSchemaV1(serializers.ModelSerializer):

    class Meta:
        model = RuleTemplate
        fields = (
            'predicates',
            'api_name',
        )

    predicates = PredicateSchemaV1(many=True)


class ConditionSchemaV1(serializers.ModelSerializer):

    class Meta:
        model = ConditionTemplate
        fields = (
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

    class Meta:
        model = RawPerformerTemplate
        fields = (
            'type',
            'user_id',
            'group_id',
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

    class Meta:
        model = TaskTemplate
        fields = (
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
            'revert_task',
            'parents',
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
        allow_empty=True,
    )
    checklists = CheckListTemplateSchemeV1(
        many=True,
        required=False,
    )
    raw_due_date = RawDueDateTemplateSchemaV1(required=False)
    clear_description = serializers.SerializerMethodField(allow_null=True)

    def get_clear_description(self, obj):
        return MarkdownService.clear(obj.description)


class TemplateSchemaV1(serializers.ModelSerializer):
    owners = TemplateOwnerSchemaV1(many=True)
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
            'owners',
            'updated_by',
            'wf_name_template',
        )
