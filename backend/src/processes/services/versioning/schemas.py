from rest_framework import serializers

from src.processes.models.templates.checklist import (
    ChecklistTemplate,
    ChecklistTemplateSelection,
)
from src.processes.models.templates.conditions import (
    ConditionTemplate,
    PredicateTemplate,
    RuleTemplate,
)
from src.generics.fields import RelatedApiNameListField
from src.processes.models.templates.fieldset import (
    FieldsetTemplate,
    FieldSetTemplateRuleGroupAnd,
    FieldSetTemplateRuleGroupOr,
    FieldSetTemplateRuleSet,
)
from src.processes.models.templates.fields import (
    FieldTemplate,
    FieldTemplateRuleGroupAnd,
    FieldTemplateRuleGroupOr,
    FieldTemplateRuleSet,
    FieldTemplateSelection,
)
from src.processes.models.templates.kickoff import Kickoff
from src.processes.models.templates.owner import TemplateOwner
from src.processes.models.templates.raw_due_date import RawDueDateTemplate
from src.processes.models.templates.raw_performer import RawPerformerTemplate
from src.processes.models.templates.task import TaskTemplate
from src.processes.models.templates.template import Template
from src.services.markdown import MarkdownService


class SelectionSchemaV1(serializers.ModelSerializer):

    class Meta:
        model = FieldTemplateSelection
        fields = (
            'value',
            'api_name',
        )


class FieldSetRuleGroupAndSchemaV1(serializers.ModelSerializer):

    class Meta:
        model = FieldSetTemplateRuleGroupAnd
        fields = (
            'api_name',
            'operator',
            'value',
        )


class FieldSetRuleGroupOrSchemaV1(serializers.ModelSerializer):

    class Meta:
        model = FieldSetTemplateRuleGroupOr
        fields = (
            'api_name',
            'groups_and',
        )

    groups_and = FieldSetRuleGroupAndSchemaV1(many=True)


class FieldSetRuleSetSchemaV1(serializers.ModelSerializer):

    class Meta:
        model = FieldSetTemplateRuleSet
        fields = (
            'api_name',
            'message',
            'order',
            'fields',
            'groups_or',
        )

    fields = RelatedApiNameListField(default=list)
    groups_or = FieldSetRuleGroupOrSchemaV1(many=True)


class FieldRuleGroupAndSchemaV1(serializers.ModelSerializer):

    class Meta:
        model = FieldTemplateRuleGroupAnd
        fields = (
            'api_name',
            'field',
            'operator',
            'value',
        )


class FieldRuleGroupOrSchemaV1(serializers.ModelSerializer):

    class Meta:
        model = FieldTemplateRuleGroupOr
        fields = (
            'api_name',
            'groups_and',
        )

    groups_and = FieldRuleGroupAndSchemaV1(many=True)


class FieldRuleSetSchemaV1(serializers.ModelSerializer):

    class Meta:
        model = FieldTemplateRuleSet
        fields = (
            'api_name',
            'name',
            'type',
            'message',
            'order',
            'groups_or',
        )

    groups_or = FieldRuleGroupOrSchemaV1(many=True)


class FieldSchemaV1(serializers.ModelSerializer):

    class Meta:
        model = FieldTemplate

        fields = (
            'name',
            'type',
            'description',
            'is_required',
            'is_hidden',
            'api_name',
            'order',
            'default',
            'selections',
            'dataset_id',
            'rulesets',
        )

    selections = SelectionSchemaV1(
        many=True,
        allow_null=True,
        allow_empty=True,
        required=False,
    )
    rulesets = FieldRuleSetSchemaV1(
        many=True,
        allow_null=True,
        allow_empty=True,
    )


class FieldSetSchemaV1(serializers.ModelSerializer):

    class Meta:
        model = FieldsetTemplate
        fields = (
            'name',
            'title',
            'description',
            'order',
            'api_name',
            'label_position',
            'layout',
            'fields',
            'rulesets',
        )

    fields = FieldSchemaV1(many=True, allow_null=True, allow_empty=True)
    rulesets = FieldSetRuleSetSchemaV1(
        many=True,
        allow_null=True,
        allow_empty=True,
    )


class KickoffSchemaV1(serializers.ModelSerializer):

    class Meta:
        model = Kickoff
        fields = (
            'fields',
            'fieldsets',
        )

    fields = FieldSchemaV1(many=True, allow_null=True, allow_empty=True)
    fieldsets = FieldSetSchemaV1(
        many=True,
        allow_null=True,
        allow_empty=True,
        required=False,
    )


class TemplateOwnerSchemaV1(serializers.ModelSerializer):
    class Meta:
        model = TemplateOwner
        fields = (
            'role',
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
            'user_id',
            'group_id',
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
            'source_task_api_name',
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
            'skip_for_starter',
            'fields',
            'fieldsets',
            'delay',
            'conditions',
            'raw_performers',
            'raw_due_date',
            'checklists',
            'revert_task',
            'parents',
        )

    fields = FieldSchemaV1(many=True, allow_null=True, allow_empty=True)
    fieldsets = FieldSetSchemaV1(
        many=True,
        allow_null=True,
        allow_empty=True,
        required=False,
    )
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
            'reminder_notification',
            'completion_notification',
        )
