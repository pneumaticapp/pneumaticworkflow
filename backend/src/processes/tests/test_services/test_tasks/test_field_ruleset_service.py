import pytest

from src.processes.enums import (
    FieldRuleOperator,
    FieldRuleType,
    FieldType,
)
from src.processes.models.workflows.fields import (
    FieldRuleGroupAnd,
    FieldRuleGroupOr,
    FieldRuleSet,
    TaskField,
)
from src.processes.services.tasks.field_ruleset import FieldRuleSetService
from src.processes.tests.fixtures import (
    create_test_field_show_ruleset,
    create_test_fieldset,
    create_test_owner,
    create_test_template,
    create_test_workflow,
)

pytestmark = pytest.mark.django_db


def create_source_field(workflow, task, api_name, value):
    return TaskField.objects.create(
        account=workflow.account,
        workflow=workflow,
        task=task,
        type=FieldType.STRING,
        api_name=api_name,
        name=api_name,
        value=value,
    )


def create_target_field(workflow, task, api_name='target-field-1'):
    return TaskField.objects.create(
        account=workflow.account,
        workflow=workflow,
        task=task,
        type=FieldType.STRING,
        api_name=api_name,
        name=api_name,
    )


def create_show_ruleset(field, source_api_name, value='yes', **kwargs):
    ruleset = FieldRuleSet.objects.create(
        account=field.account,
        workflow=field.workflow,
        field=field,
        api_name=kwargs.get('api_name', 'ruleset-1'),
        name='Show ruleset',
        type=kwargs.get('type', FieldRuleType.SHOW),
    )
    group_or = FieldRuleGroupOr.objects.create(
        account=field.account,
        workflow=field.workflow,
        ruleset=ruleset,
        api_name=kwargs.get('group_or_api_name', 'group-or-1'),
    )
    FieldRuleGroupAnd.objects.create(
        account=field.account,
        workflow=field.workflow,
        group_or=group_or,
        api_name=kwargs.get('group_and_api_name', 'group-and-1'),
        field=source_api_name,
        operator=kwargs.get('operator', FieldRuleOperator.EQUAL),
        value=value,
    )
    return ruleset


def test_create__with_template__ok():

    """ Scalars and the group tree are copied from the template """

    # arrange
    user = create_test_owner()
    template = create_test_template(user=user, tasks_count=1)
    workflow = create_test_workflow(user=user, template=template)
    task = workflow.tasks.get(number=1)
    field_template = template.tasks.get(number=1).fields.create(
        account=user.account,
        template=template,
        type=FieldType.STRING,
        api_name='target-field-1',
        name='Target',
        order=0,
    )
    ruleset_template, _, group_and_template = create_test_field_show_ruleset(
        account=user.account,
        template=template,
        field=field_template,
        source_field_api_name='source-field-1',
        value='yes',
    )
    field = create_target_field(workflow, task)
    service = FieldRuleSetService(user=user)

    # act
    ruleset = service.create(
        instance_template=ruleset_template,
        field=field,
    )

    # assert
    assert ruleset.field_id == field.id
    assert ruleset.workflow_id == workflow.id
    assert ruleset.api_name == ruleset_template.api_name
    assert ruleset.name == ruleset_template.name
    assert ruleset.type == FieldRuleType.SHOW
    assert ruleset.order == ruleset_template.order
    group_or = ruleset.groups_or.get()
    group_and = group_or.groups_and.get()
    assert group_and.field == group_and_template.field
    assert group_and.operator == group_and_template.operator
    assert group_and.value == group_and_template.value


def test_apply_show_rulesets__condition_matches__visible():

    """ The rule passes — the field stays visible """

    # arrange
    user = create_test_owner()
    workflow = create_test_workflow(user=user, tasks_count=1)
    task = workflow.tasks.get(number=1)
    create_source_field(workflow, task, 'source-field-1', 'yes')
    field = create_target_field(workflow, task)
    field.is_hidden = True
    field.save(update_fields=['is_hidden'])
    create_show_ruleset(field, 'source-field-1', value='yes')

    # act
    FieldRuleSetService.apply_show_rulesets([field])

    # assert
    field.refresh_from_db()
    assert field.is_hidden is False


def test_apply_show_rulesets__condition_fails__hidden():

    """ The rule does not pass — the field is hidden """

    # arrange
    user = create_test_owner()
    workflow = create_test_workflow(user=user, tasks_count=1)
    task = workflow.tasks.get(number=1)
    create_source_field(workflow, task, 'source-field-1', 'no')
    field = create_target_field(workflow, task)
    create_show_ruleset(field, 'source-field-1', value='yes')

    # act
    FieldRuleSetService.apply_show_rulesets([field])

    # assert
    field.refresh_from_db()
    assert field.is_hidden is True


def test_apply_show_rulesets__second_group_or_matches__visible():

    """ Branches are combined with OR — one passing branch is enough """

    # arrange
    user = create_test_owner()
    workflow = create_test_workflow(user=user, tasks_count=1)
    task = workflow.tasks.get(number=1)
    create_source_field(workflow, task, 'source-field-1', 'maybe')
    field = create_target_field(workflow, task)
    ruleset = create_show_ruleset(field, 'source-field-1', value='yes')
    group_or_2 = FieldRuleGroupOr.objects.create(
        account=user.account,
        workflow=workflow,
        ruleset=ruleset,
        api_name='group-or-2',
    )
    FieldRuleGroupAnd.objects.create(
        account=user.account,
        workflow=workflow,
        group_or=group_or_2,
        api_name='group-and-2',
        field='source-field-1',
        operator=FieldRuleOperator.EQUAL,
        value='maybe',
    )

    # act
    FieldRuleSetService.apply_show_rulesets([field])

    # assert
    field.refresh_from_db()
    assert field.is_hidden is False


def test_apply_show_rulesets__validator_ruleset__not_applied():

    """ Only show rulesets drive visibility """

    # arrange
    user = create_test_owner()
    workflow = create_test_workflow(user=user, tasks_count=1)
    task = workflow.tasks.get(number=1)
    create_source_field(workflow, task, 'source-field-1', 'no')
    field = create_target_field(workflow, task)
    create_show_ruleset(
        field,
        'source-field-1',
        value='yes',
        type=FieldRuleType.VALIDATOR,
    )

    # act
    FieldRuleSetService.apply_show_rulesets([field])

    # assert
    field.refresh_from_db()
    assert field.is_hidden is False


def test_apply_show_rulesets__field_without_rulesets__untouched():

    """ A field with no show rulesets keeps its is_hidden """

    # arrange
    user = create_test_owner()
    workflow = create_test_workflow(user=user, tasks_count=1)
    task = workflow.tasks.get(number=1)
    field = create_target_field(workflow, task)
    field.is_hidden = True
    field.save(update_fields=['is_hidden'])

    # act
    FieldRuleSetService.apply_show_rulesets([field])

    # assert
    field.refresh_from_db()
    assert field.is_hidden is True


def test_apply_show_rulesets__source_field_missing__hidden():

    """ An unresolvable source hides the field: without the value
        there is no reason to consider the rule satisfied. """

    # arrange
    user = create_test_owner()
    workflow = create_test_workflow(user=user, tasks_count=1)
    task = workflow.tasks.get(number=1)
    field = create_target_field(workflow, task)
    create_show_ruleset(field, 'nonexistent-field', value='yes')

    # act
    FieldRuleSetService.apply_show_rulesets([field])

    # assert
    field.refresh_from_db()
    assert field.is_hidden is True


def test_apply_show_rulesets__empty_list__skip():

    """ Nothing to recalculate """

    # act
    FieldRuleSetService.apply_show_rulesets([])

    # assert
    assert not FieldRuleSet.objects.exists()


def test_apply_show_rulesets_for_task__fieldset_field__recalculated():

    """ Fieldset fields carry no task FK, so a naive task.output query
        misses them. """

    # arrange
    user = create_test_owner()
    workflow = create_test_workflow(user=user, tasks_count=1)
    task = workflow.tasks.get(number=1)
    create_source_field(workflow, task, 'source-field-1', 'yes')
    fieldset = create_test_fieldset(workflow=workflow, task=task)
    field = fieldset.fields.first()
    field.is_hidden = True
    field.save(update_fields=['is_hidden'])
    create_show_ruleset(field, 'source-field-1', value='yes')

    # act
    FieldRuleSetService.apply_show_rulesets_for_task(task)

    # assert
    field.refresh_from_db()
    assert field.is_hidden is False


def test_apply_show_rulesets_for_workflow__fieldset_field__recalculated():

    """ PATCH of the kickoff has to reach fieldset fields too """

    # arrange
    user = create_test_owner()
    workflow = create_test_workflow(user=user, tasks_count=1)
    task = workflow.tasks.get(number=1)
    create_source_field(workflow, task, 'source-field-1', 'no')
    fieldset = create_test_fieldset(workflow=workflow, task=task)
    field = fieldset.fields.first()
    create_show_ruleset(field, 'source-field-1', value='yes')

    # act
    FieldRuleSetService.apply_show_rulesets_for_workflow(workflow)

    # assert
    field.refresh_from_db()
    assert field.is_hidden is True


def test_apply_show_rulesets_for_workflow__kickoff_field__recalculated():

    """ A show target on the kickoff itself must flip, not only
        task fields. """

    # arrange
    user = create_test_owner()
    workflow = create_test_workflow(user=user, tasks_count=1)
    kickoff_field = TaskField.objects.create(
        account=user.account,
        workflow=workflow,
        kickoff=workflow.kickoff_instance,
        type=FieldType.STRING,
        api_name='kickoff-field-1',
        name='Kickoff',
        value='no',
        is_hidden=False,
    )
    create_show_ruleset(kickoff_field, 'kickoff-field-1', value='yes')

    # act
    FieldRuleSetService.apply_show_rulesets_for_workflow(workflow)

    # assert
    kickoff_field.refresh_from_db()
    assert kickoff_field.is_hidden is True


def test_apply_show_rulesets_for_workflow__kickoff_fieldset_field__recalculated():

    """ Fieldset fields on the kickoff have no task FK and
        fieldset.task is null — the old filter skipped them. """

    # arrange
    user = create_test_owner()
    workflow = create_test_workflow(user=user, tasks_count=1)
    source = TaskField.objects.create(
        account=user.account,
        workflow=workflow,
        kickoff=workflow.kickoff_instance,
        type=FieldType.STRING,
        api_name='fieldset-status',
        name='Fieldset status',
        value='no',
    )
    fieldset = create_test_fieldset(
        workflow=workflow,
        kickoff=workflow.kickoff_instance,
    )
    note = fieldset.fields.first()
    create_show_ruleset(note, source.api_name, value='yes')

    # act
    FieldRuleSetService.apply_show_rulesets_for_workflow(workflow)

    # assert
    note.refresh_from_db()
    assert note.is_hidden is True
    assert note.task_id is None
    assert note.fieldset.task_id is None
