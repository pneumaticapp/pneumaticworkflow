import pytest
from src.processes.enums import (
    FieldRuleOperator,
    FieldRuleType,
    FieldSetRuleOperator,
    FieldType,
    PerformerType,
)
from src.processes.models.templates.raw_performer import RawPerformerTemplate
from src.processes.services.versioning.schemas import (
    FieldSchemaV1,
    FieldSetSchemaV1,
    RawPerformerTemplateSchemaV1,
)
from src.processes.tests.fixtures import (
    create_test_field_show_ruleset,
    create_test_fieldset_template,
    create_test_owner,
    create_test_template,
)


pytestmark = pytest.mark.django_db


def test_raw_performer_schema__manager__includes_source_task_api_name():
    """
    RawPerformerTemplateSchemaV1 must serialize source_task_api_name
    so that MANAGER performers preserve their link to the source step
    during process versioning/updates.
    """

    # arrange
    user = create_test_owner()
    template = create_test_template(user=user, tasks_count=2)
    task_template_1 = template.tasks.get(number=1)
    task_template_2 = template.tasks.get(number=2)

    raw_performer = RawPerformerTemplate.objects.create(
        template=template,
        task=task_template_2,
        account=user.account,
        type=PerformerType.MANAGER,
        source_task_api_name=task_template_1.api_name,
        api_name='raw-performer-mgr-1',
    )

    # act
    serialized = RawPerformerTemplateSchemaV1(raw_performer).data

    # assert
    assert 'source_task_api_name' in serialized
    assert serialized['source_task_api_name'] == task_template_1.api_name
    assert serialized['type'] == PerformerType.MANAGER


def test_raw_performer_schema__user__source_task_api_name_null():
    """
    USER type has null source_task_api_name — schema serializes it as None.
    """

    # arrange
    user = create_test_owner()
    template = create_test_template(user=user, tasks_count=1)
    task_template = template.tasks.get(number=1)

    raw_performer = RawPerformerTemplate.objects.create(
        template=template,
        task=task_template,
        account=user.account,
        type=PerformerType.USER,
        user=user,
        api_name='raw-performer-usr-1',
    )

    # act
    serialized = RawPerformerTemplateSchemaV1(raw_performer).data

    # assert
    assert serialized['source_task_api_name'] is None
    assert serialized['type'] == PerformerType.USER


def test_fieldset_schema__rulesets__replaces_deprecated_rules():
    """
    The snapshot carries the ruleset tree, not the deprecated flat
    `rules`: without it a version update gets no rules at all.
    """

    # arrange
    user = create_test_owner()
    template = create_test_template(user=user, tasks_count=1)
    fieldset = create_test_fieldset_template(
        account=user.account,
        template=template,
        rule_operator=FieldSetRuleOperator.SUM_EQUAL,
        rule_value='100',
    )
    ruleset = fieldset.rulesets.first()
    ruleset.fields.add(fieldset.fields.first())
    group_and = ruleset.groups_or.first().groups_and.first()

    # act
    serialized = FieldSetSchemaV1(fieldset).data

    # assert
    assert 'rules' not in serialized
    assert len(serialized['rulesets']) == 1
    ruleset_data = serialized['rulesets'][0]
    assert ruleset_data['api_name'] == ruleset.api_name
    assert ruleset_data['order'] == ruleset.order
    assert ruleset_data['fields'] == [fieldset.fields.first().api_name]
    group_and_data = ruleset_data['groups_or'][0]['groups_and'][0]
    assert group_and_data['operator'] == group_and.operator
    assert group_and_data['value'] == group_and.value


def test_fieldset_schema__no_rulesets__empty_list():

    # arrange
    user = create_test_owner()
    template = create_test_template(user=user, tasks_count=1)
    fieldset = create_test_fieldset_template(
        account=user.account,
        template=template,
    )

    # act
    serialized = FieldSetSchemaV1(fieldset).data

    # assert
    assert serialized['rulesets'] == []


def test_field_schema__rulesets__replaces_deprecated_rules():
    """
    Field rulesets keep `name` and `type`, and every condition keeps
    the api_name of the source field it reads.
    """

    # arrange
    user = create_test_owner()
    template = create_test_template(user=user, tasks_count=1)
    task_template = template.tasks.get(number=1)
    field = task_template.fields.create(
        account=user.account,
        template=template,
        type=FieldType.STRING,
        api_name='target-field-1',
        name='Target',
        order=0,
    )
    ruleset, _, group_and = create_test_field_show_ruleset(
        account=user.account,
        template=template,
        field=field,
        source_field_api_name='source-field-1',
        value='yes',
    )

    # act
    serialized = FieldSchemaV1(field).data

    # assert
    assert 'rules' not in serialized
    assert len(serialized['rulesets']) == 1
    ruleset_data = serialized['rulesets'][0]
    assert ruleset_data['api_name'] == ruleset.api_name
    assert ruleset_data['name'] == ruleset.name
    assert ruleset_data['type'] == FieldRuleType.SHOW
    group_and_data = ruleset_data['groups_or'][0]['groups_and'][0]
    assert group_and_data['field'] == 'source-field-1'
    assert group_and_data['operator'] == FieldRuleOperator.EQUAL
    assert group_and_data['value'] == 'yes'


def test_field_schema__no_rulesets__empty_list():

    # arrange
    user = create_test_owner()
    template = create_test_template(user=user, tasks_count=1)
    task_template = template.tasks.get(number=1)
    field = task_template.fields.create(
        account=user.account,
        template=template,
        type=FieldType.STRING,
        api_name='target-field-1',
        name='Target',
        order=0,
    )

    # act
    serialized = FieldSchemaV1(field).data

    # assert
    assert serialized['rulesets'] == []
