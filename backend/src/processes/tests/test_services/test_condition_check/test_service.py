import pytest
from django.contrib.auth import get_user_model

from src.processes.enums import (
    ConditionAction,
    FieldType,
    PredicateOperator,
    PredicateType,
    TaskStatus,
)
from src.processes.models.workflows.attachment import FileAttachment
from src.processes.models.workflows.conditions import (
    Condition,
    Predicate,
    Rule,
)
from src.processes.models.workflows.fields import (
    FieldSelection,
    TaskField,
)
from src.processes.services.condition_check.service import (
    ConditionCheckService,
)
from src.processes.tests.fixtures import (
    create_test_owner,
    create_test_not_admin,
    create_test_workflow,
)

UserModel = get_user_model()
pytestmark = pytest.mark.django_db


# region number


def test_check__number__equal__matching_integers__ok():

    """Check returns True when number field value equals predicate value."""

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(user=owner, tasks_count=2)
    first_task = workflow.tasks.first()
    second_task = workflow.tasks.last()
    field = TaskField.objects.create(
        name='Number field',
        api_name='number-1',
        task=first_task,
        type=FieldType.NUMBER,
        value='100',
        workflow=workflow,
        account=owner.account,
    )
    condition = Condition.objects.create(
        task=second_task,
        action=ConditionAction.SKIP_TASK,
        order=1,
    )
    rule = Rule.objects.create(condition=condition)
    Predicate.objects.create(
        rule=rule,
        operator=PredicateOperator.EQUAL,
        field_type=field.type,
        field=field.api_name,
        value='100',
    )

    # act
    result = ConditionCheckService.check(
        condition=condition,
        workflow_id=workflow.id,
    )

    # assert
    assert result is True


def test_check__number__equal__decimal_matches_integer__ok():

    """Check returns True when decimal predicate equals integer field value."""

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(user=owner, tasks_count=2)
    first_task = workflow.tasks.first()
    second_task = workflow.tasks.last()
    field = TaskField.objects.create(
        name='Number field',
        api_name='number-1',
        task=first_task,
        type=FieldType.NUMBER,
        value='100',
        workflow=workflow,
        account=owner.account,
    )
    condition = Condition.objects.create(
        task=second_task,
        action=ConditionAction.SKIP_TASK,
        order=1,
    )
    rule = Rule.objects.create(condition=condition)
    Predicate.objects.create(
        rule=rule,
        operator=PredicateOperator.EQUAL,
        field_type=field.type,
        field=field.api_name,
        value='100.00',
    )

    # act
    result = ConditionCheckService.check(
        condition=condition,
        workflow_id=workflow.id,
    )

    # assert
    assert result is True


def test_check__number__equal__different_decimals__fail():

    """Check returns False when decimal values differ at significant digit."""

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(user=owner, tasks_count=2)
    first_task = workflow.tasks.first()
    second_task = workflow.tasks.last()
    field = TaskField.objects.create(
        name='Number field',
        api_name='number-1',
        task=first_task,
        type=FieldType.NUMBER,
        value='1.0',
        workflow=workflow,
        account=owner.account,
    )
    condition = Condition.objects.create(
        task=second_task,
        action=ConditionAction.SKIP_TASK,
        order=1,
    )
    rule = Rule.objects.create(condition=condition)
    Predicate.objects.create(
        rule=rule,
        operator=PredicateOperator.EQUAL,
        field_type=field.type,
        field=field.api_name,
        value='1.01',
    )

    # act
    result = ConditionCheckService.check(
        condition=condition,
        workflow_id=workflow.id,
    )

    # assert
    assert result is False


def test_check__number__equal__field_empty__fail():

    """Check returns False when field value is empty and predicate is set."""

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(user=owner, tasks_count=2)
    first_task = workflow.tasks.first()
    second_task = workflow.tasks.last()
    field = TaskField.objects.create(
        name='Number field',
        api_name='number-1',
        task=first_task,
        type=FieldType.NUMBER,
        value='',
        workflow=workflow,
        account=owner.account,
    )
    condition = Condition.objects.create(
        task=second_task,
        action=ConditionAction.SKIP_TASK,
        order=1,
    )
    rule = Rule.objects.create(condition=condition)
    Predicate.objects.create(
        rule=rule,
        operator=PredicateOperator.EQUAL,
        field_type=field.type,
        field=field.api_name,
        value='1.5',
    )

    # act
    result = ConditionCheckService.check(
        condition=condition,
        workflow_id=workflow.id,
    )

    # assert
    assert result is False


def test_check__number__equal__predicate_empty__fail():

    """Check returns False when predicate value is empty."""

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(user=owner, tasks_count=2)
    first_task = workflow.tasks.first()
    second_task = workflow.tasks.last()
    field = TaskField.objects.create(
        name='Number field',
        api_name='number-1',
        task=first_task,
        type=FieldType.NUMBER,
        value='0',
        workflow=workflow,
        account=owner.account,
    )
    condition = Condition.objects.create(
        task=second_task,
        action=ConditionAction.SKIP_TASK,
        order=1,
    )
    rule = Rule.objects.create(condition=condition)
    Predicate.objects.create(
        rule=rule,
        operator=PredicateOperator.EQUAL,
        field_type=field.type,
        field=field.api_name,
        value='',
    )

    # act
    result = ConditionCheckService.check(
        condition=condition,
        workflow_id=workflow.id,
    )

    # assert
    assert result is False


def test_check__number__not_equal__high_precision_difference__ok():

    """
    Check returns True when values differ beyond float
    precision threshold.
    """

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(user=owner, tasks_count=2)
    first_task = workflow.tasks.first()
    second_task = workflow.tasks.last()
    field = TaskField.objects.create(
        name='Number field',
        api_name='number-1',
        task=first_task,
        type=FieldType.NUMBER,
        value='1',
        workflow=workflow,
        account=owner.account,
    )
    condition = Condition.objects.create(
        task=second_task,
        action=ConditionAction.SKIP_TASK,
        order=1,
    )
    rule = Rule.objects.create(condition=condition)
    Predicate.objects.create(
        rule=rule,
        operator=PredicateOperator.NOT_EQUAL,
        field_type=field.type,
        field=field.api_name,
        value='1.0000000000000000001',
    )

    # act
    result = ConditionCheckService.check(
        condition=condition,
        workflow_id=workflow.id,
    )

    # assert
    assert result is True


def test_check__number__not_equal__field_empty__ok():

    """Check returns True when field is empty and predicate is set."""

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(user=owner, tasks_count=2)
    first_task = workflow.tasks.first()
    second_task = workflow.tasks.last()
    field = TaskField.objects.create(
        name='Number field',
        api_name='number-1',
        task=first_task,
        type=FieldType.NUMBER,
        value='',
        workflow=workflow,
        account=owner.account,
    )
    condition = Condition.objects.create(
        task=second_task,
        action=ConditionAction.SKIP_TASK,
        order=1,
    )
    rule = Rule.objects.create(condition=condition)
    Predicate.objects.create(
        rule=rule,
        operator=PredicateOperator.NOT_EQUAL,
        field_type=field.type,
        field=field.api_name,
        value='1.5',
    )

    # act
    result = ConditionCheckService.check(
        condition=condition,
        workflow_id=workflow.id,
    )

    # assert
    assert result is True


def test_check__number__not_equal__precision_equal__fail():

    """Check returns False when values are equal within Decimal precision."""

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(user=owner, tasks_count=2)
    first_task = workflow.tasks.first()
    second_task = workflow.tasks.last()
    field = TaskField.objects.create(
        name='Number field',
        api_name='number-1',
        task=first_task,
        type=FieldType.NUMBER,
        value='1',
        workflow=workflow,
        account=owner.account,
    )
    condition = Condition.objects.create(
        task=second_task,
        action=ConditionAction.SKIP_TASK,
        order=1,
    )
    rule = Rule.objects.create(condition=condition)
    Predicate.objects.create(
        rule=rule,
        operator=PredicateOperator.NOT_EQUAL,
        field_type=field.type,
        field=field.api_name,
        value='1.0000000000000000000',
    )

    # act
    result = ConditionCheckService.check(
        condition=condition,
        workflow_id=workflow.id,
    )

    # assert
    assert result is False


def test_check__number__exist__zero_value__ok():

    """Check returns True when field value is zero (zero is a valid number)."""

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(user=owner, tasks_count=2)
    first_task = workflow.tasks.first()
    second_task = workflow.tasks.last()
    field = TaskField.objects.create(
        name='Number field',
        api_name='number-1',
        task=first_task,
        type=FieldType.NUMBER,
        value='0',
        workflow=workflow,
        account=owner.account,
    )
    condition = Condition.objects.create(
        task=second_task,
        action=ConditionAction.SKIP_TASK,
        order=1,
    )
    rule = Rule.objects.create(condition=condition)
    Predicate.objects.create(
        rule=rule,
        operator=PredicateOperator.EXIST,
        field_type=field.type,
        field=field.api_name,
        value=None,
    )

    # act
    result = ConditionCheckService.check(
        condition=condition,
        workflow_id=workflow.id,
    )

    # assert
    assert result is True


def test_check__number__exist__nonzero_value__ok():

    """Check returns True when field has a non-zero numeric value."""

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(user=owner, tasks_count=2)
    first_task = workflow.tasks.first()
    second_task = workflow.tasks.last()
    field = TaskField.objects.create(
        name='Number field',
        api_name='number-1',
        task=first_task,
        type=FieldType.NUMBER,
        value='0.1',
        workflow=workflow,
        account=owner.account,
    )
    condition = Condition.objects.create(
        task=second_task,
        action=ConditionAction.SKIP_TASK,
        order=1,
    )
    rule = Rule.objects.create(condition=condition)
    Predicate.objects.create(
        rule=rule,
        operator=PredicateOperator.EXIST,
        field_type=field.type,
        field=field.api_name,
        value=None,
    )

    # act
    result = ConditionCheckService.check(
        condition=condition,
        workflow_id=workflow.id,
    )

    # assert
    assert result is True


def test_check__number__exist__empty_value__fail():

    """Check returns False when field value is an empty string."""

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(user=owner, tasks_count=2)
    first_task = workflow.tasks.first()
    second_task = workflow.tasks.last()
    field = TaskField.objects.create(
        name='Number field',
        api_name='number-1',
        task=first_task,
        type=FieldType.NUMBER,
        value='',
        workflow=workflow,
        account=owner.account,
    )
    condition = Condition.objects.create(
        task=second_task,
        action=ConditionAction.SKIP_TASK,
        order=1,
    )
    rule = Rule.objects.create(condition=condition)
    Predicate.objects.create(
        rule=rule,
        operator=PredicateOperator.EXIST,
        field_type=field.type,
        field=field.api_name,
        value=None,
    )

    # act
    result = ConditionCheckService.check(
        condition=condition,
        workflow_id=workflow.id,
    )

    # assert
    assert result is False


def test_check__number__not_exist__empty_value__ok():

    """Check returns True when field value is empty (field was not filled)."""

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(user=owner, tasks_count=2)
    first_task = workflow.tasks.first()
    second_task = workflow.tasks.last()
    field = TaskField.objects.create(
        name='Number field',
        api_name='number-1',
        task=first_task,
        type=FieldType.NUMBER,
        value='',
        workflow=workflow,
        account=owner.account,
    )
    condition = Condition.objects.create(
        task=second_task,
        action=ConditionAction.SKIP_TASK,
        order=1,
    )
    rule = Rule.objects.create(condition=condition)
    Predicate.objects.create(
        rule=rule,
        operator=PredicateOperator.NOT_EXIST,
        field_type=field.type,
        field=field.api_name,
        value=None,
    )

    # act
    result = ConditionCheckService.check(
        condition=condition,
        workflow_id=workflow.id,
    )

    # assert
    assert result is True


def test_check__number__not_exist__zero_value__fail():

    """
    Check returns False when field value is zero
    (zero counts as existing).
    """

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(user=owner, tasks_count=2)
    first_task = workflow.tasks.first()
    second_task = workflow.tasks.last()
    field = TaskField.objects.create(
        name='Number field',
        api_name='number-1',
        task=first_task,
        type=FieldType.NUMBER,
        value='0',
        workflow=workflow,
        account=owner.account,
    )
    condition = Condition.objects.create(
        task=second_task,
        action=ConditionAction.SKIP_TASK,
        order=1,
    )
    rule = Rule.objects.create(condition=condition)
    Predicate.objects.create(
        rule=rule,
        operator=PredicateOperator.NOT_EXIST,
        field_type=field.type,
        field=field.api_name,
        value=None,
    )

    # act
    result = ConditionCheckService.check(
        condition=condition,
        workflow_id=workflow.id,
    )

    # assert
    assert result is False


def test_check__number__more_than__field_greater__ok():

    """Check returns True when field value is greater than predicate."""

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(user=owner, tasks_count=2)
    first_task = workflow.tasks.first()
    second_task = workflow.tasks.last()
    field = TaskField.objects.create(
        name='Number field',
        api_name='number-1',
        task=first_task,
        type=FieldType.NUMBER,
        value='1',
        workflow=workflow,
        account=owner.account,
    )
    condition = Condition.objects.create(
        task=second_task,
        action=ConditionAction.SKIP_TASK,
        order=1,
    )
    rule = Rule.objects.create(condition=condition)
    Predicate.objects.create(
        rule=rule,
        operator=PredicateOperator.MORE_THAN,
        field_type=field.type,
        field=field.api_name,
        value='0',
    )

    # act
    result = ConditionCheckService.check(
        condition=condition,
        workflow_id=workflow.id,
    )

    # assert
    assert result is True


def test_check__number__more_than__field_less__fail():

    """Check returns False when field value is less than predicate."""

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(user=owner, tasks_count=2)
    first_task = workflow.tasks.first()
    second_task = workflow.tasks.last()
    field = TaskField.objects.create(
        name='Number field',
        api_name='number-1',
        task=first_task,
        type=FieldType.NUMBER,
        value='0',
        workflow=workflow,
        account=owner.account,
    )
    condition = Condition.objects.create(
        task=second_task,
        action=ConditionAction.SKIP_TASK,
        order=1,
    )
    rule = Rule.objects.create(condition=condition)
    Predicate.objects.create(
        rule=rule,
        operator=PredicateOperator.MORE_THAN,
        field_type=field.type,
        field=field.api_name,
        value='0.0000000000000001',
    )

    # act
    result = ConditionCheckService.check(
        condition=condition,
        workflow_id=workflow.id,
    )

    # assert
    assert result is False


def test_check__number__more_than__field_equal__fail():

    """
    Check returns False when field value equals predicate
    (not strictly greater).
    """

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(user=owner, tasks_count=2)
    first_task = workflow.tasks.first()
    second_task = workflow.tasks.last()
    field = TaskField.objects.create(
        name='Number field',
        api_name='number-1',
        task=first_task,
        type=FieldType.NUMBER,
        value='2',
        workflow=workflow,
        account=owner.account,
    )
    condition = Condition.objects.create(
        task=second_task,
        action=ConditionAction.SKIP_TASK,
        order=1,
    )
    rule = Rule.objects.create(condition=condition)
    Predicate.objects.create(
        rule=rule,
        operator=PredicateOperator.MORE_THAN,
        field_type=field.type,
        field=field.api_name,
        value='2.0',
    )

    # act
    result = ConditionCheckService.check(
        condition=condition,
        workflow_id=workflow.id,
    )

    # assert
    assert result is False


def test_check__number__more_than__predicate_empty__fail():

    """Check returns False when predicate value is empty."""

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(user=owner, tasks_count=2)
    first_task = workflow.tasks.first()
    second_task = workflow.tasks.last()
    field = TaskField.objects.create(
        name='Number field',
        api_name='number-1',
        task=first_task,
        type=FieldType.NUMBER,
        value='22',
        workflow=workflow,
        account=owner.account,
    )
    condition = Condition.objects.create(
        task=second_task,
        action=ConditionAction.SKIP_TASK,
        order=1,
    )
    rule = Rule.objects.create(condition=condition)
    Predicate.objects.create(
        rule=rule,
        operator=PredicateOperator.MORE_THAN,
        field_type=field.type,
        field=field.api_name,
        value='',
    )

    # act
    result = ConditionCheckService.check(
        condition=condition,
        workflow_id=workflow.id,
    )

    # assert
    assert result is False


def test_check__number__more_than__field_empty__fail():

    """Check returns False when field value is empty."""

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(user=owner, tasks_count=2)
    first_task = workflow.tasks.first()
    second_task = workflow.tasks.last()
    field = TaskField.objects.create(
        name='Number field',
        api_name='number-1',
        task=first_task,
        type=FieldType.NUMBER,
        value='',
        workflow=workflow,
        account=owner.account,
    )
    condition = Condition.objects.create(
        task=second_task,
        action=ConditionAction.SKIP_TASK,
        order=1,
    )
    rule = Rule.objects.create(condition=condition)
    Predicate.objects.create(
        rule=rule,
        operator=PredicateOperator.MORE_THAN,
        field_type=field.type,
        field=field.api_name,
        value='22',
    )

    # act
    result = ConditionCheckService.check(
        condition=condition,
        workflow_id=workflow.id,
    )

    # assert
    assert result is False


def test_check__number__less_than__field_less__ok():

    """Check returns True when field value is less than predicate."""

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(user=owner, tasks_count=2)
    first_task = workflow.tasks.first()
    second_task = workflow.tasks.last()
    field = TaskField.objects.create(
        name='Number field',
        api_name='number-1',
        task=first_task,
        type=FieldType.NUMBER,
        value='0',
        workflow=workflow,
        account=owner.account,
    )
    condition = Condition.objects.create(
        task=second_task,
        action=ConditionAction.SKIP_TASK,
        order=1,
    )
    rule = Rule.objects.create(condition=condition)
    Predicate.objects.create(
        rule=rule,
        operator=PredicateOperator.LESS_THAN,
        field_type=field.type,
        field=field.api_name,
        value='0.0000000000000001',
    )

    # act
    result = ConditionCheckService.check(
        condition=condition,
        workflow_id=workflow.id,
    )

    # assert
    assert result is True


def test_check__number__less_than__field_equal__fail():

    """Check returns False when field equals predicate (not strictly less)."""

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(user=owner, tasks_count=2)
    first_task = workflow.tasks.first()
    second_task = workflow.tasks.last()
    field = TaskField.objects.create(
        name='Number field',
        api_name='number-1',
        task=first_task,
        type=FieldType.NUMBER,
        value='2',
        workflow=workflow,
        account=owner.account,
    )
    condition = Condition.objects.create(
        task=second_task,
        action=ConditionAction.SKIP_TASK,
        order=1,
    )
    rule = Rule.objects.create(condition=condition)
    Predicate.objects.create(
        rule=rule,
        operator=PredicateOperator.LESS_THAN,
        field_type=field.type,
        field=field.api_name,
        value='2.0',
    )

    # act
    result = ConditionCheckService.check(
        condition=condition,
        workflow_id=workflow.id,
    )

    # assert
    assert result is False


def test_check__number__less_than__predicate_empty__fail():

    """Check returns False when predicate value is empty."""

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(user=owner, tasks_count=2)
    first_task = workflow.tasks.first()
    second_task = workflow.tasks.last()
    field = TaskField.objects.create(
        name='Number field',
        api_name='number-1',
        task=first_task,
        type=FieldType.NUMBER,
        value='22',
        workflow=workflow,
        account=owner.account,
    )
    condition = Condition.objects.create(
        task=second_task,
        action=ConditionAction.SKIP_TASK,
        order=1,
    )
    rule = Rule.objects.create(condition=condition)
    Predicate.objects.create(
        rule=rule,
        operator=PredicateOperator.LESS_THAN,
        field_type=field.type,
        field=field.api_name,
        value='',
    )

    # act
    result = ConditionCheckService.check(
        condition=condition,
        workflow_id=workflow.id,
    )

    # assert
    assert result is False


def test_check__number__less_than__field_empty__fail():

    """Check returns False when field value is empty."""

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(user=owner, tasks_count=2)
    first_task = workflow.tasks.first()
    second_task = workflow.tasks.last()
    field = TaskField.objects.create(
        name='Number field',
        api_name='number-1',
        task=first_task,
        type=FieldType.NUMBER,
        value='',
        workflow=workflow,
        account=owner.account,
    )
    condition = Condition.objects.create(
        task=second_task,
        action=ConditionAction.SKIP_TASK,
        order=1,
    )
    rule = Rule.objects.create(condition=condition)
    Predicate.objects.create(
        rule=rule,
        operator=PredicateOperator.LESS_THAN,
        field_type=field.type,
        field=field.api_name,
        value='22',
    )

    # act
    result = ConditionCheckService.check(
        condition=condition,
        workflow_id=workflow.id,
    )

    # assert
    assert result is False


# endregion

# region string


def test_check__string__equal__matching_values__ok():

    """Check returns True when string field value exactly matches predicate."""

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(user=owner, tasks_count=2)
    first_task = workflow.tasks.first()
    second_task = workflow.tasks.last()
    field = TaskField.objects.create(
        name='String field',
        api_name='string-1',
        task=first_task,
        type=FieldType.STRING,
        value='Captain Marvel',
        workflow=workflow,
        account=owner.account,
    )
    condition = Condition.objects.create(
        task=second_task,
        action=ConditionAction.SKIP_TASK,
        order=1,
    )
    rule = Rule.objects.create(condition=condition)
    Predicate.objects.create(
        rule=rule,
        operator=PredicateOperator.EQUAL,
        field_type=field.type,
        field=field.api_name,
        value='Captain Marvel',
    )

    # act
    result = ConditionCheckService.check(
        condition=condition,
        workflow_id=workflow.id,
    )

    # assert
    assert result is True


def test_check__string__equal__similar_but_different__fail():

    """Check returns False when string values differ by whitespace."""

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(user=owner, tasks_count=2)
    first_task = workflow.tasks.first()
    second_task = workflow.tasks.last()
    field = TaskField.objects.create(
        name='String field',
        api_name='string-1',
        task=first_task,
        type=FieldType.STRING,
        value='CaptainMarvel',
        workflow=workflow,
        account=owner.account,
    )
    condition = Condition.objects.create(
        task=second_task,
        action=ConditionAction.SKIP_TASK,
        order=1,
    )
    rule = Rule.objects.create(condition=condition)
    Predicate.objects.create(
        rule=rule,
        operator=PredicateOperator.EQUAL,
        field_type=field.type,
        field=field.api_name,
        value='Captain Marvel',
    )

    # act
    result = ConditionCheckService.check(
        condition=condition,
        workflow_id=workflow.id,
    )

    # assert
    assert result is False


def test_check__string__equal__predicate_none__fail():

    """Check returns False when predicate value is None."""

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(user=owner, tasks_count=2)
    first_task = workflow.tasks.first()
    second_task = workflow.tasks.last()
    field = TaskField.objects.create(
        name='String field',
        api_name='string-1',
        task=first_task,
        type=FieldType.STRING,
        value='Captain Marvel',
        workflow=workflow,
        account=owner.account,
    )
    condition = Condition.objects.create(
        task=second_task,
        action=ConditionAction.SKIP_TASK,
        order=1,
    )
    rule = Rule.objects.create(condition=condition)
    Predicate.objects.create(
        rule=rule,
        operator=PredicateOperator.EQUAL,
        field_type=field.type,
        field=field.api_name,
        value=None,
    )

    # act
    result = ConditionCheckService.check(
        condition=condition,
        workflow_id=workflow.id,
    )

    # assert
    assert result is False


def test_check__string__not_equal__field_empty__ok():

    """Check returns True when field is empty and predicate is set."""

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(user=owner, tasks_count=2)
    first_task = workflow.tasks.first()
    second_task = workflow.tasks.last()
    field = TaskField.objects.create(
        name='String field',
        api_name='string-1',
        task=first_task,
        type=FieldType.STRING,
        value='',
        workflow=workflow,
        account=owner.account,
    )
    condition = Condition.objects.create(
        task=second_task,
        action=ConditionAction.SKIP_TASK,
        order=1,
    )
    rule = Rule.objects.create(condition=condition)
    Predicate.objects.create(
        rule=rule,
        operator=PredicateOperator.NOT_EQUAL,
        field_type=field.type,
        field=field.api_name,
        value='Captain Marvel',
    )

    # act
    result = ConditionCheckService.check(
        condition=condition,
        workflow_id=workflow.id,
    )

    # assert
    assert result is True


def test_check__string__exist__non_empty_value__ok():

    """Check returns True when field has a non-empty string value."""

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(user=owner, tasks_count=2)
    first_task = workflow.tasks.first()
    second_task = workflow.tasks.last()
    field = TaskField.objects.create(
        name='String field',
        api_name='string-1',
        task=first_task,
        type=FieldType.STRING,
        value='Captain Marvel',
        workflow=workflow,
        account=owner.account,
    )
    condition = Condition.objects.create(
        task=second_task,
        action=ConditionAction.SKIP_TASK,
        order=1,
    )
    rule = Rule.objects.create(condition=condition)
    Predicate.objects.create(
        rule=rule,
        operator=PredicateOperator.EXIST,
        field_type=field.type,
        field=field.api_name,
        value=None,
    )

    # act
    result = ConditionCheckService.check(
        condition=condition,
        workflow_id=workflow.id,
    )

    # assert
    assert result is True


def test_check__string__exist__empty_value__fail():

    """Check returns False when field value is empty string."""

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(user=owner, tasks_count=2)
    first_task = workflow.tasks.first()
    second_task = workflow.tasks.last()
    field = TaskField.objects.create(
        name='String field',
        api_name='string-1',
        task=first_task,
        type=FieldType.STRING,
        value='',
        workflow=workflow,
        account=owner.account,
    )
    condition = Condition.objects.create(
        task=second_task,
        action=ConditionAction.SKIP_TASK,
        order=1,
    )
    rule = Rule.objects.create(condition=condition)
    Predicate.objects.create(
        rule=rule,
        operator=PredicateOperator.EXIST,
        field_type=field.type,
        field=field.api_name,
        value=None,
    )

    # act
    result = ConditionCheckService.check(
        condition=condition,
        workflow_id=workflow.id,
    )

    # assert
    assert result is False


def test_check__string__not_exist__non_empty_value__fail():

    """Check returns False when field has a value (field is filled)."""

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(user=owner, tasks_count=2)
    first_task = workflow.tasks.first()
    second_task = workflow.tasks.last()
    field = TaskField.objects.create(
        name='String field',
        api_name='string-1',
        task=first_task,
        type=FieldType.STRING,
        value='Captain Marvel',
        workflow=workflow,
        account=owner.account,
    )
    condition = Condition.objects.create(
        task=second_task,
        action=ConditionAction.SKIP_TASK,
        order=1,
    )
    rule = Rule.objects.create(condition=condition)
    Predicate.objects.create(
        rule=rule,
        operator=PredicateOperator.NOT_EXIST,
        field_type=field.type,
        field=field.api_name,
        value=None,
    )

    # act
    result = ConditionCheckService.check(
        condition=condition,
        workflow_id=workflow.id,
    )

    # assert
    assert result is False


def test_check__string__contain__field_is_substring_of_predicate__fail():

    """
    Check returns False when field is a substring of predicate
    (wrong direction).
    """

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(user=owner, tasks_count=2)
    first_task = workflow.tasks.first()
    second_task = workflow.tasks.last()
    field = TaskField.objects.create(
        name='String field',
        api_name='string-1',
        task=first_task,
        type=FieldType.STRING,
        value='Marvel',
        workflow=workflow,
        account=owner.account,
    )
    condition = Condition.objects.create(
        task=second_task,
        action=ConditionAction.SKIP_TASK,
        order=1,
    )
    rule = Rule.objects.create(condition=condition)
    Predicate.objects.create(
        rule=rule,
        operator=PredicateOperator.CONTAIN,
        field_type=field.type,
        field=field.api_name,
        value='Captain Marvel',
    )

    # act
    result = ConditionCheckService.check(
        condition=condition,
        workflow_id=workflow.id,
    )

    # assert
    assert result is False


def test_check__string__contain__predicate_none__fail():

    """Check returns False when predicate value is None."""

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(user=owner, tasks_count=2)
    first_task = workflow.tasks.first()
    second_task = workflow.tasks.last()
    field = TaskField.objects.create(
        name='String field',
        api_name='string-1',
        task=first_task,
        type=FieldType.STRING,
        value='Captain Marvel',
        workflow=workflow,
        account=owner.account,
    )
    condition = Condition.objects.create(
        task=second_task,
        action=ConditionAction.SKIP_TASK,
        order=1,
    )
    rule = Rule.objects.create(condition=condition)
    Predicate.objects.create(
        rule=rule,
        operator=PredicateOperator.CONTAIN,
        field_type=field.type,
        field=field.api_name,
        value=None,
    )

    # act
    result = ConditionCheckService.check(
        condition=condition,
        workflow_id=workflow.id,
    )

    # assert
    assert result is False


def test_check__string__contain__predicate_is_substring__ok():

    """Check returns True when predicate is a substring of field value."""

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(user=owner, tasks_count=2)
    first_task = workflow.tasks.first()
    second_task = workflow.tasks.last()
    field = TaskField.objects.create(
        name='String field',
        api_name='string-1',
        task=first_task,
        type=FieldType.STRING,
        value='Captain Marvel',
        workflow=workflow,
        account=owner.account,
    )
    condition = Condition.objects.create(
        task=second_task,
        action=ConditionAction.SKIP_TASK,
        order=1,
    )
    rule = Rule.objects.create(condition=condition)
    Predicate.objects.create(
        rule=rule,
        operator=PredicateOperator.CONTAIN,
        field_type=field.type,
        field=field.api_name,
        value='Marvel',
    )

    # act
    result = ConditionCheckService.check(
        condition=condition,
        workflow_id=workflow.id,
    )

    # assert
    assert result is True


def test_check__string__contain__no_match__fail():

    """Check returns False when predicate is not found in field value."""

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(user=owner, tasks_count=2)
    first_task = workflow.tasks.first()
    second_task = workflow.tasks.last()
    field = TaskField.objects.create(
        name='String field',
        api_name='string-1',
        task=first_task,
        type=FieldType.STRING,
        value='Iran Many',
        workflow=workflow,
        account=owner.account,
    )
    condition = Condition.objects.create(
        task=second_task,
        action=ConditionAction.SKIP_TASK,
        order=1,
    )
    rule = Rule.objects.create(condition=condition)
    Predicate.objects.create(
        rule=rule,
        operator=PredicateOperator.CONTAIN,
        field_type=field.type,
        field=field.api_name,
        value='Captain Marvel',
    )

    # act
    result = ConditionCheckService.check(
        condition=condition,
        workflow_id=workflow.id,
    )

    # assert
    assert result is False


def test_check__string__not_contain__predicate_none__fail():

    """Check returns False when predicate is None."""

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(user=owner, tasks_count=2)
    first_task = workflow.tasks.first()
    second_task = workflow.tasks.last()
    field = TaskField.objects.create(
        name='String field',
        api_name='string-1',
        task=first_task,
        type=FieldType.STRING,
        value='Captain Marvel',
        workflow=workflow,
        account=owner.account,
    )
    condition = Condition.objects.create(
        task=second_task,
        action=ConditionAction.SKIP_TASK,
        order=1,
    )
    rule = Rule.objects.create(condition=condition)
    Predicate.objects.create(
        rule=rule,
        operator=PredicateOperator.NOT_CONTAIN,
        field_type=field.type,
        field=field.api_name,
        value=None,
    )

    # act
    result = ConditionCheckService.check(
        condition=condition,
        workflow_id=workflow.id,
    )

    # assert
    assert result is False


def test_check__string__not_contain__no_match__ok():

    """Check returns True when predicate is not found in field value."""

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(user=owner, tasks_count=2)
    first_task = workflow.tasks.first()
    second_task = workflow.tasks.last()
    field = TaskField.objects.create(
        name='String field',
        api_name='string-1',
        task=first_task,
        type=FieldType.STRING,
        value='Iran Many',
        workflow=workflow,
        account=owner.account,
    )
    condition = Condition.objects.create(
        task=second_task,
        action=ConditionAction.SKIP_TASK,
        order=1,
    )
    rule = Rule.objects.create(condition=condition)
    Predicate.objects.create(
        rule=rule,
        operator=PredicateOperator.NOT_CONTAIN,
        field_type=field.type,
        field=field.api_name,
        value='Captain Marvel',
    )

    # act
    result = ConditionCheckService.check(
        condition=condition,
        workflow_id=workflow.id,
    )

    # assert
    assert result is True


# endregion

# region file


def test_check__file__exist__has_attachment__ok():

    """Check returns True when file field has an attachment."""

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(user=owner, tasks_count=2)
    first_task = workflow.tasks.first()
    second_task = workflow.tasks.last()
    field = TaskField.objects.create(
        name='File field',
        api_name='file-1',
        task=first_task,
        type=FieldType.FILE,
        value='some png url',
        workflow=workflow,
        account=owner.account,
    )
    FileAttachment.objects.create(
        name='john.cena',
        url='https://john.cena/john.cena',
        size=1488,
        account_id=owner.account_id,
        output=field,
    )
    condition = Condition.objects.create(
        task=second_task,
        action=ConditionAction.SKIP_TASK,
        order=1,
    )
    rule = Rule.objects.create(condition=condition)
    Predicate.objects.create(
        rule=rule,
        operator=PredicateOperator.EXIST,
        field_type=field.type,
        field=field.api_name,
        value=None,
    )

    # act
    result = ConditionCheckService.check(
        condition=condition,
        workflow_id=workflow.id,
    )

    # assert
    assert result is True


def test_check__file__exist__no_attachment__fail():

    """Check returns False when file field has no attachment."""

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(user=owner, tasks_count=2)
    first_task = workflow.tasks.first()
    second_task = workflow.tasks.last()
    field = TaskField.objects.create(
        name='File field',
        api_name='file-1',
        task=first_task,
        type=FieldType.FILE,
        value='',
        workflow=workflow,
        account=owner.account,
    )
    FileAttachment.objects.create(
        name='john.cena',
        url='https://john.cena/john.cena',
        size=1488,
        account_id=owner.account_id,
        output=None,
    )
    condition = Condition.objects.create(
        task=second_task,
        action=ConditionAction.SKIP_TASK,
        order=1,
    )
    rule = Rule.objects.create(condition=condition)
    Predicate.objects.create(
        rule=rule,
        operator=PredicateOperator.EXIST,
        field_type=field.type,
        field=field.api_name,
        value=None,
    )

    # act
    result = ConditionCheckService.check(
        condition=condition,
        workflow_id=workflow.id,
    )

    # assert
    assert result is False


def test_check__file__not_exist__no_attachment__ok():

    """Check returns True when file field has no attachment."""

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(user=owner, tasks_count=2)
    first_task = workflow.tasks.first()
    second_task = workflow.tasks.last()
    field = TaskField.objects.create(
        name='File field',
        api_name='file-1',
        task=first_task,
        type=FieldType.FILE,
        value='',
        workflow=workflow,
        account=owner.account,
    )
    FileAttachment.objects.create(
        name='john.cena',
        url='https://john.cena/john.cena',
        size=1488,
        account_id=owner.account_id,
        output=None,
    )
    condition = Condition.objects.create(
        task=second_task,
        action=ConditionAction.SKIP_TASK,
        order=1,
    )
    rule = Rule.objects.create(condition=condition)
    Predicate.objects.create(
        rule=rule,
        operator=PredicateOperator.NOT_EXIST,
        field_type=field.type,
        field=field.api_name,
        value=None,
    )

    # act
    result = ConditionCheckService.check(
        condition=condition,
        workflow_id=workflow.id,
    )

    # assert
    assert result is True


def test_check__file__not_exist__has_attachment__fail():

    """Check returns False when file field has an attachment."""

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(user=owner, tasks_count=2)
    first_task = workflow.tasks.first()
    second_task = workflow.tasks.last()
    field = TaskField.objects.create(
        name='File field',
        api_name='file-1',
        task=first_task,
        type=FieldType.FILE,
        value='Captain Marvel',
        workflow=workflow,
        account=owner.account,
    )
    FileAttachment.objects.create(
        name='john.cena',
        url='https://john.cena/john.cena',
        size=1488,
        account_id=owner.account_id,
        output=field,
    )
    condition = Condition.objects.create(
        task=second_task,
        action=ConditionAction.SKIP_TASK,
        order=1,
    )
    rule = Rule.objects.create(condition=condition)
    Predicate.objects.create(
        rule=rule,
        operator=PredicateOperator.NOT_EXIST,
        field_type=field.type,
        field=field.api_name,
        value=None,
    )

    # act
    result = ConditionCheckService.check(
        condition=condition,
        workflow_id=workflow.id,
    )

    # assert
    assert result is False


# endregion

# region dropdown


def test_check__dropdown__equal__first_selected__ok():

    """Check returns True when selected option api_name matches predicate."""

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(user=owner, tasks_count=2)
    first_task = workflow.tasks.first()
    second_task = workflow.tasks.last()
    field = TaskField.objects.create(
        name='Dropdown field',
        api_name='dropdown-1',
        task=first_task,
        type=FieldType.DROPDOWN,
        value='select-1',
        workflow=workflow,
        account=owner.account,
    )
    FieldSelection.objects.create(field=field, api_name='select-1', value='1')
    FieldSelection.objects.create(field=field, api_name='select-2', value='2')
    condition = Condition.objects.create(
        task=second_task,
        action=ConditionAction.SKIP_TASK,
        order=1,
    )
    rule = Rule.objects.create(condition=condition)
    Predicate.objects.create(
        rule=rule,
        operator=PredicateOperator.EQUAL,
        field_type=field.type,
        field=field.api_name,
        value='select-1',
    )

    # act
    result = ConditionCheckService.check(
        condition=condition,
        workflow_id=workflow.id,
    )

    # assert
    assert result is True


def test_check__dropdown__equal__none_selected__fail():

    """Check returns False when no option is selected."""

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(user=owner, tasks_count=2)
    first_task = workflow.tasks.first()
    second_task = workflow.tasks.last()
    field = TaskField.objects.create(
        name='Dropdown field',
        api_name='dropdown-1',
        task=first_task,
        type=FieldType.DROPDOWN,
        value='',
        workflow=workflow,
        account=owner.account,
    )
    FieldSelection.objects.create(field=field, api_name='select-1', value='1')
    FieldSelection.objects.create(field=field, api_name='select-2', value='2')
    condition = Condition.objects.create(
        task=second_task,
        action=ConditionAction.SKIP_TASK,
        order=1,
    )
    rule = Rule.objects.create(condition=condition)
    Predicate.objects.create(
        rule=rule,
        operator=PredicateOperator.EQUAL,
        field_type=field.type,
        field=field.api_name,
        value='select-1',
    )

    # act
    result = ConditionCheckService.check(
        condition=condition,
        workflow_id=workflow.id,
    )

    # assert
    assert result is False


def test_check__dropdown__equal__predicate_none__fail():

    """Check returns False when predicate value is None."""

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(user=owner, tasks_count=2)
    first_task = workflow.tasks.first()
    second_task = workflow.tasks.last()
    field = TaskField.objects.create(
        name='Dropdown field',
        api_name='dropdown-1',
        task=first_task,
        type=FieldType.DROPDOWN,
        value='select-1',
        workflow=workflow,
        account=owner.account,
    )
    FieldSelection.objects.create(field=field, api_name='select-1', value='1')
    FieldSelection.objects.create(field=field, api_name='select-2', value='2')
    condition = Condition.objects.create(
        task=second_task,
        action=ConditionAction.SKIP_TASK,
        order=1,
    )
    rule = Rule.objects.create(condition=condition)
    Predicate.objects.create(
        rule=rule,
        operator=PredicateOperator.EQUAL,
        field_type=field.type,
        field=field.api_name,
        value=None,
    )

    # act
    result = ConditionCheckService.check(
        condition=condition,
        workflow_id=workflow.id,
    )

    # assert
    assert result is False


def test_check__dropdown__not_equal__second_selected__ok():

    """Check returns True when selected option differs from predicate."""

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(user=owner, tasks_count=2)
    first_task = workflow.tasks.first()
    second_task = workflow.tasks.last()
    field = TaskField.objects.create(
        name='Dropdown field',
        api_name='dropdown-1',
        task=first_task,
        type=FieldType.DROPDOWN,
        value='select-2',
        workflow=workflow,
        account=owner.account,
    )
    FieldSelection.objects.create(field=field, api_name='select-1', value='1')
    FieldSelection.objects.create(field=field, api_name='select-2', value='2')
    condition = Condition.objects.create(
        task=second_task,
        action=ConditionAction.SKIP_TASK,
        order=1,
    )
    rule = Rule.objects.create(condition=condition)
    Predicate.objects.create(
        rule=rule,
        operator=PredicateOperator.NOT_EQUAL,
        field_type=field.type,
        field=field.api_name,
        value='select-1',
    )

    # act
    result = ConditionCheckService.check(
        condition=condition,
        workflow_id=workflow.id,
    )

    # assert
    assert result is True


def test_check__dropdown__exist__first_selected__ok():

    """Check returns True when an option is selected."""

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(user=owner, tasks_count=2)
    first_task = workflow.tasks.first()
    second_task = workflow.tasks.last()
    field = TaskField.objects.create(
        name='Dropdown field',
        api_name='dropdown-1',
        task=first_task,
        type=FieldType.DROPDOWN,
        value='select-1',
        workflow=workflow,
        account=owner.account,
    )
    FieldSelection.objects.create(field=field, api_name='select-1', value='1')
    FieldSelection.objects.create(field=field, api_name='select-2', value='2')
    condition = Condition.objects.create(
        task=second_task,
        action=ConditionAction.SKIP_TASK,
        order=1,
    )
    rule = Rule.objects.create(condition=condition)
    Predicate.objects.create(
        rule=rule,
        operator=PredicateOperator.EXIST,
        field_type=field.type,
        field=field.api_name,
        value=None,
    )

    # act
    result = ConditionCheckService.check(
        condition=condition,
        workflow_id=workflow.id,
    )

    # assert
    assert result is True


def test_check__dropdown__exist__none_selected__fail():

    """Check returns False when no option is selected."""

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(user=owner, tasks_count=2)
    first_task = workflow.tasks.first()
    second_task = workflow.tasks.last()
    field = TaskField.objects.create(
        name='Dropdown field',
        api_name='dropdown-1',
        task=first_task,
        type=FieldType.DROPDOWN,
        value='',
        workflow=workflow,
        account=owner.account,
    )
    FieldSelection.objects.create(field=field, api_name='select-1', value='1')
    FieldSelection.objects.create(field=field, api_name='select-2', value='2')
    condition = Condition.objects.create(
        task=second_task,
        action=ConditionAction.SKIP_TASK,
        order=1,
    )
    rule = Rule.objects.create(condition=condition)
    Predicate.objects.create(
        rule=rule,
        operator=PredicateOperator.EXIST,
        field_type=field.type,
        field=field.api_name,
        value=None,
    )

    # act
    result = ConditionCheckService.check(
        condition=condition,
        workflow_id=workflow.id,
    )

    # assert
    assert result is False


def test_check__dropdown__not_exist__first_selected__fail():

    """Check returns False when an option is selected."""

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(user=owner, tasks_count=2)
    first_task = workflow.tasks.first()
    second_task = workflow.tasks.last()
    field = TaskField.objects.create(
        name='Dropdown field',
        api_name='dropdown-1',
        task=first_task,
        type=FieldType.DROPDOWN,
        value='select-1',
        workflow=workflow,
        account=owner.account,
    )
    FieldSelection.objects.create(field=field, api_name='select-1', value='1')
    FieldSelection.objects.create(field=field, api_name='select-2', value='2')
    condition = Condition.objects.create(
        task=second_task,
        action=ConditionAction.SKIP_TASK,
        order=1,
    )
    rule = Rule.objects.create(condition=condition)
    Predicate.objects.create(
        rule=rule,
        operator=PredicateOperator.NOT_EXIST,
        field_type=field.type,
        field=field.api_name,
        value=None,
    )

    # act
    result = ConditionCheckService.check(
        condition=condition,
        workflow_id=workflow.id,
    )

    # assert
    assert result is False


# endregion

# region checkbox


def test_check__checkbox__equal__first_selected__ok():

    """Check returns True when only the predicate option is selected."""

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(user=owner, tasks_count=2)
    first_task = workflow.tasks.get(number=1)
    second_task = workflow.tasks.get(number=2)
    field = TaskField.objects.create(
        name='Checkbox field',
        api_name='checkbox-1',
        task=first_task,
        type=FieldType.CHECKBOX,
        value='select-1',
        workflow=workflow,
        account=owner.account,
    )
    FieldSelection.objects.create(field=field, api_name='select-1', value='1')
    FieldSelection.objects.create(field=field, api_name='select-2', value='2')
    condition = Condition.objects.create(
        task=second_task,
        action=ConditionAction.SKIP_TASK,
        order=1,
    )
    rule = Rule.objects.create(condition=condition)
    Predicate.objects.create(
        rule=rule,
        operator=PredicateOperator.EQUAL,
        field_type=field.type,
        field=field.api_name,
        value='select-1',
    )

    # act
    result = ConditionCheckService.check(
        condition=condition,
        workflow_id=workflow.id,
    )

    # assert
    assert result is True


def test_check__checkbox__equal__none_selected__fail():

    """Check returns False when no option is selected."""

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(user=owner, tasks_count=2)
    first_task = workflow.tasks.get(number=1)
    second_task = workflow.tasks.get(number=2)
    field = TaskField.objects.create(
        name='Checkbox field',
        api_name='checkbox-1',
        task=first_task,
        type=FieldType.CHECKBOX,
        value='',
        workflow=workflow,
        account=owner.account,
    )
    FieldSelection.objects.create(field=field, api_name='select-1', value='1')
    FieldSelection.objects.create(field=field, api_name='select-2', value='2')
    condition = Condition.objects.create(
        task=second_task,
        action=ConditionAction.SKIP_TASK,
        order=1,
    )
    rule = Rule.objects.create(condition=condition)
    Predicate.objects.create(
        rule=rule,
        operator=PredicateOperator.EQUAL,
        field_type=field.type,
        field=field.api_name,
        value='select-1',
    )

    # act
    result = ConditionCheckService.check(
        condition=condition,
        workflow_id=workflow.id,
    )

    # assert
    assert result is False


def test_check__checkbox__equal__both_selected__fail():

    """
    Check returns False when multiple options are selected
    (equal requires exact single match).
    """

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(user=owner, tasks_count=2)
    first_task = workflow.tasks.get(number=1)
    second_task = workflow.tasks.get(number=2)
    field = TaskField.objects.create(
        name='Checkbox field',
        api_name='checkbox-1',
        task=first_task,
        type=FieldType.CHECKBOX,
        value='select-1,select-2',
        workflow=workflow,
        account=owner.account,
    )
    FieldSelection.objects.create(field=field, api_name='select-1', value='1')
    FieldSelection.objects.create(field=field, api_name='select-2', value='2')
    condition = Condition.objects.create(
        task=second_task,
        action=ConditionAction.SKIP_TASK,
        order=1,
    )
    rule = Rule.objects.create(condition=condition)
    Predicate.objects.create(
        rule=rule,
        operator=PredicateOperator.EQUAL,
        field_type=field.type,
        field=field.api_name,
        value='select-1',
    )

    # act
    result = ConditionCheckService.check(
        condition=condition,
        workflow_id=workflow.id,
    )

    # assert
    assert result is False


def test_check__checkbox__equal__predicate_none__fail():

    """Check returns False when predicate value is None."""

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(user=owner, tasks_count=2)
    first_task = workflow.tasks.get(number=1)
    second_task = workflow.tasks.get(number=2)
    field = TaskField.objects.create(
        name='Checkbox field',
        api_name='checkbox-1',
        task=first_task,
        type=FieldType.CHECKBOX,
        value='select-1',
        workflow=workflow,
        account=owner.account,
    )
    FieldSelection.objects.create(field=field, api_name='select-1', value='1')
    FieldSelection.objects.create(field=field, api_name='select-2', value='2')
    condition = Condition.objects.create(
        task=second_task,
        action=ConditionAction.SKIP_TASK,
        order=1,
    )
    rule = Rule.objects.create(condition=condition)
    Predicate.objects.create(
        rule=rule,
        operator=PredicateOperator.EQUAL,
        field_type=field.type,
        field=field.api_name,
        value=None,
    )

    # act
    result = ConditionCheckService.check(
        condition=condition,
        workflow_id=workflow.id,
    )

    # assert
    assert result is False


def test_check__checkbox__not_equal__second_selected__ok():

    """Check returns True when selected option differs from predicate."""

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(user=owner, tasks_count=2)
    first_task = workflow.tasks.get(number=1)
    second_task = workflow.tasks.get(number=2)
    field = TaskField.objects.create(
        name='Checkbox field',
        api_name='checkbox-1',
        task=first_task,
        type=FieldType.CHECKBOX,
        value='select-2',
        workflow=workflow,
        account=owner.account,
    )
    FieldSelection.objects.create(field=field, api_name='select-1', value='1')
    FieldSelection.objects.create(field=field, api_name='select-2', value='2')
    condition = Condition.objects.create(
        task=second_task,
        action=ConditionAction.SKIP_TASK,
        order=1,
    )
    rule = Rule.objects.create(condition=condition)
    Predicate.objects.create(
        rule=rule,
        operator=PredicateOperator.NOT_EQUAL,
        field_type=field.type,
        field=field.api_name,
        value='select-1',
    )

    # act
    result = ConditionCheckService.check(
        condition=condition,
        workflow_id=workflow.id,
    )

    # assert
    assert result is True


def test_check__checkbox__exist__first_selected__ok():

    """Check returns True when at least one option is selected."""

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(user=owner, tasks_count=2)
    first_task = workflow.tasks.get(number=1)
    second_task = workflow.tasks.get(number=2)
    field = TaskField.objects.create(
        name='Checkbox field',
        api_name='checkbox-1',
        task=first_task,
        type=FieldType.CHECKBOX,
        value='select-1',
        workflow=workflow,
        account=owner.account,
    )
    FieldSelection.objects.create(field=field, api_name='select-1', value='1')
    FieldSelection.objects.create(field=field, api_name='select-2', value='2')
    condition = Condition.objects.create(
        task=second_task,
        action=ConditionAction.SKIP_TASK,
        order=1,
    )
    rule = Rule.objects.create(condition=condition)
    Predicate.objects.create(
        rule=rule,
        operator=PredicateOperator.EXIST,
        field_type=field.type,
        field=field.api_name,
        value=None,
    )

    # act
    result = ConditionCheckService.check(
        condition=condition,
        workflow_id=workflow.id,
    )

    # assert
    assert result is True


def test_check__checkbox__exist__none_selected__fail():

    """Check returns False when no option is selected."""

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(user=owner, tasks_count=2)
    first_task = workflow.tasks.get(number=1)
    second_task = workflow.tasks.get(number=2)
    field = TaskField.objects.create(
        name='Checkbox field',
        api_name='checkbox-1',
        task=first_task,
        type=FieldType.CHECKBOX,
        value='',
        workflow=workflow,
        account=owner.account,
    )
    FieldSelection.objects.create(field=field, api_name='select-1', value='1')
    FieldSelection.objects.create(field=field, api_name='select-2', value='2')
    condition = Condition.objects.create(
        task=second_task,
        action=ConditionAction.SKIP_TASK,
        order=1,
    )
    rule = Rule.objects.create(condition=condition)
    Predicate.objects.create(
        rule=rule,
        operator=PredicateOperator.EXIST,
        field_type=field.type,
        field=field.api_name,
        value=None,
    )

    # act
    result = ConditionCheckService.check(
        condition=condition,
        workflow_id=workflow.id,
    )

    # assert
    assert result is False


def test_check__checkbox__not_exist__first_selected__fail():

    """Check returns False when an option is selected."""

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(user=owner, tasks_count=2)
    first_task = workflow.tasks.get(number=1)
    second_task = workflow.tasks.get(number=2)
    field = TaskField.objects.create(
        name='Checkbox field',
        api_name='checkbox-1',
        task=first_task,
        type=FieldType.CHECKBOX,
        value='select-1',
        workflow=workflow,
        account=owner.account,
    )
    FieldSelection.objects.create(field=field, api_name='select-1', value='1')
    FieldSelection.objects.create(field=field, api_name='select-2', value='2')
    condition = Condition.objects.create(
        task=second_task,
        action=ConditionAction.SKIP_TASK,
        order=1,
    )
    rule = Rule.objects.create(condition=condition)
    Predicate.objects.create(
        rule=rule,
        operator=PredicateOperator.NOT_EXIST,
        field_type=field.type,
        field=field.api_name,
        value=None,
    )

    # act
    result = ConditionCheckService.check(
        condition=condition,
        workflow_id=workflow.id,
    )

    # assert
    assert result is False


def test_check__checkbox__contain__first_selected__ok():

    """Check returns True when predicate option is among selected options."""

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(user=owner, tasks_count=2)
    first_task = workflow.tasks.get(number=1)
    second_task = workflow.tasks.get(number=2)
    field = TaskField.objects.create(
        name='Checkbox field',
        api_name='checkbox-1',
        task=first_task,
        type=FieldType.CHECKBOX,
        value='select-1',
        workflow=workflow,
        account=owner.account,
    )
    FieldSelection.objects.create(field=field, api_name='select-1', value='1')
    FieldSelection.objects.create(field=field, api_name='select-2', value='2')
    condition = Condition.objects.create(
        task=second_task,
        action=ConditionAction.SKIP_TASK,
        order=1,
    )
    rule = Rule.objects.create(condition=condition)
    Predicate.objects.create(
        rule=rule,
        operator=PredicateOperator.CONTAIN,
        field_type=field.type,
        field=field.api_name,
        value='select-1',
    )

    # act
    result = ConditionCheckService.check(
        condition=condition,
        workflow_id=workflow.id,
    )

    # assert
    assert result is True


def test_check__checkbox__contain__both_selected__ok():

    """
    Check returns True when predicate option is among
    multiple selected options.
    """

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(user=owner, tasks_count=2)
    first_task = workflow.tasks.get(number=1)
    second_task = workflow.tasks.get(number=2)
    field = TaskField.objects.create(
        name='Checkbox field',
        api_name='checkbox-1',
        task=first_task,
        type=FieldType.CHECKBOX,
        value='select-1,select-2',
        workflow=workflow,
        account=owner.account,
    )
    FieldSelection.objects.create(field=field, api_name='select-1', value='1')
    FieldSelection.objects.create(field=field, api_name='select-2', value='2')
    condition = Condition.objects.create(
        task=second_task,
        action=ConditionAction.SKIP_TASK,
        order=1,
    )
    rule = Rule.objects.create(condition=condition)
    Predicate.objects.create(
        rule=rule,
        operator=PredicateOperator.CONTAIN,
        field_type=field.type,
        field=field.api_name,
        value='select-1',
    )

    # act
    result = ConditionCheckService.check(
        condition=condition,
        workflow_id=workflow.id,
    )

    # assert
    assert result is True


def test_check__checkbox__contain__second_selected__fail():

    """Check returns False when only a different option is selected."""

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(user=owner, tasks_count=2)
    first_task = workflow.tasks.get(number=1)
    second_task = workflow.tasks.get(number=2)
    field = TaskField.objects.create(
        name='Checkbox field',
        api_name='checkbox-1',
        task=first_task,
        type=FieldType.CHECKBOX,
        value='select-2',
        workflow=workflow,
        account=owner.account,
    )
    FieldSelection.objects.create(field=field, api_name='select-1', value='1')
    FieldSelection.objects.create(field=field, api_name='select-2', value='2')
    condition = Condition.objects.create(
        task=second_task,
        action=ConditionAction.SKIP_TASK,
        order=1,
    )
    rule = Rule.objects.create(condition=condition)
    Predicate.objects.create(
        rule=rule,
        operator=PredicateOperator.CONTAIN,
        field_type=field.type,
        field=field.api_name,
        value='select-1',
    )

    # act
    result = ConditionCheckService.check(
        condition=condition,
        workflow_id=workflow.id,
    )

    # assert
    assert result is False


def test_check__checkbox__contain__predicate_none__fail():

    """Check returns False when predicate value is None."""

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(user=owner, tasks_count=2)
    first_task = workflow.tasks.get(number=1)
    second_task = workflow.tasks.get(number=2)
    field = TaskField.objects.create(
        name='Checkbox field',
        api_name='checkbox-1',
        task=first_task,
        type=FieldType.CHECKBOX,
        value='select-2',
        workflow=workflow,
        account=owner.account,
    )
    FieldSelection.objects.create(field=field, api_name='select-1', value='1')
    FieldSelection.objects.create(field=field, api_name='select-2', value='2')
    condition = Condition.objects.create(
        task=second_task,
        action=ConditionAction.SKIP_TASK,
        order=1,
    )
    rule = Rule.objects.create(condition=condition)
    Predicate.objects.create(
        rule=rule,
        operator=PredicateOperator.CONTAIN,
        field_type=field.type,
        field=field.api_name,
        value=None,
    )

    # act
    result = ConditionCheckService.check(
        condition=condition,
        workflow_id=workflow.id,
    )

    # assert
    assert result is False


def test_check__checkbox__not_contain__predicate_none__fail():

    """Check returns False when predicate value is None."""

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(user=owner, tasks_count=2)
    first_task = workflow.tasks.get(number=1)
    second_task = workflow.tasks.get(number=2)
    field = TaskField.objects.create(
        name='Checkbox field',
        api_name='checkbox-1',
        task=first_task,
        type=FieldType.CHECKBOX,
        value='select-2',
        workflow=workflow,
        account=owner.account,
    )
    FieldSelection.objects.create(field=field, api_name='select-1', value='1')
    FieldSelection.objects.create(field=field, api_name='select-2', value='2')
    condition = Condition.objects.create(
        task=second_task,
        action=ConditionAction.SKIP_TASK,
        order=1,
    )
    rule = Rule.objects.create(condition=condition)
    Predicate.objects.create(
        rule=rule,
        operator=PredicateOperator.NOT_CONTAIN,
        field_type=field.type,
        field=field.api_name,
        value=None,
    )

    # act
    result = ConditionCheckService.check(
        condition=condition,
        workflow_id=workflow.id,
    )

    # assert
    assert result is False


def test_check__checkbox__not_contain__both_selected__fail():

    """Check returns False when predicate option is among selected options."""

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(user=owner, tasks_count=2)
    first_task = workflow.tasks.get(number=1)
    second_task = workflow.tasks.get(number=2)
    field = TaskField.objects.create(
        name='Checkbox field',
        api_name='checkbox-1',
        task=first_task,
        type=FieldType.CHECKBOX,
        value='select-1,select-2',
        workflow=workflow,
        account=owner.account,
    )
    FieldSelection.objects.create(field=field, api_name='select-1', value='1')
    FieldSelection.objects.create(field=field, api_name='select-2', value='2')
    condition = Condition.objects.create(
        task=second_task,
        action=ConditionAction.SKIP_TASK,
        order=1,
    )
    rule = Rule.objects.create(condition=condition)
    Predicate.objects.create(
        rule=rule,
        operator=PredicateOperator.NOT_CONTAIN,
        field_type=field.type,
        field=field.api_name,
        value='select-1',
    )

    # act
    result = ConditionCheckService.check(
        condition=condition,
        workflow_id=workflow.id,
    )

    # assert
    assert result is False


# endregion

# region date


def test_check__date__equal__non_timestamp_field_value__fail():

    """Check returns False when field value is not a valid timestamp."""

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(user=owner, tasks_count=2)
    first_task = workflow.tasks.first()
    second_task = workflow.tasks.last()
    field = TaskField.objects.create(
        name='Date field',
        api_name='date-1',
        task=first_task,
        type=FieldType.DATE,
        value='Captain Marvel',
        workflow=workflow,
        account=owner.account,
    )
    condition = Condition.objects.create(
        task=second_task,
        action=ConditionAction.SKIP_TASK,
        order=1,
    )
    rule = Rule.objects.create(condition=condition)
    Predicate.objects.create(
        rule=rule,
        operator=PredicateOperator.EQUAL,
        field_type=field.type,
        field=field.api_name,
        value='1740087999',
    )

    # act
    result = ConditionCheckService.check(
        condition=condition,
        workflow_id=workflow.id,
    )

    # assert
    assert result is False


def test_check__date__equal__matching_integer_timestamps__ok():

    """
    Check returns True when integer field timestamp
    equals predicate string timestamp.
    """

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(user=owner, tasks_count=2)
    first_task = workflow.tasks.first()
    second_task = workflow.tasks.last()
    field = TaskField.objects.create(
        name='Date field',
        api_name='date-1',
        task=first_task,
        type=FieldType.DATE,
        value=1740087999,
        workflow=workflow,
        account=owner.account,
    )
    condition = Condition.objects.create(
        task=second_task,
        action=ConditionAction.SKIP_TASK,
        order=1,
    )
    rule = Rule.objects.create(condition=condition)
    Predicate.objects.create(
        rule=rule,
        operator=PredicateOperator.EQUAL,
        field_type=field.type,
        field=field.api_name,
        value='1740087999',
    )

    # act
    result = ConditionCheckService.check(
        condition=condition,
        workflow_id=workflow.id,
    )

    # assert
    assert result is True


def test_check__date__equal__predicate_none__fail():

    """Check returns False when predicate value is None."""

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(user=owner, tasks_count=2)
    first_task = workflow.tasks.first()
    second_task = workflow.tasks.last()
    field = TaskField.objects.create(
        name='Date field',
        api_name='date-1',
        task=first_task,
        type=FieldType.DATE,
        value='1740087999',
        workflow=workflow,
        account=owner.account,
    )
    condition = Condition.objects.create(
        task=second_task,
        action=ConditionAction.SKIP_TASK,
        order=1,
    )
    rule = Rule.objects.create(condition=condition)
    Predicate.objects.create(
        rule=rule,
        operator=PredicateOperator.EQUAL,
        field_type=field.type,
        field=field.api_name,
        value=None,
    )

    # act
    result = ConditionCheckService.check(
        condition=condition,
        workflow_id=workflow.id,
    )

    # assert
    assert result is False


def test_check__date__equal__matching_string_timestamps__ok():

    """
    Check returns True when both field and predicate
    are equal timestamp strings.
    """

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(user=owner, tasks_count=2)
    first_task = workflow.tasks.first()
    second_task = workflow.tasks.last()
    field = TaskField.objects.create(
        name='Date field',
        api_name='date-1',
        task=first_task,
        type=FieldType.DATE,
        value='1740087999',
        workflow=workflow,
        account=owner.account,
    )
    condition = Condition.objects.create(
        task=second_task,
        action=ConditionAction.SKIP_TASK,
        order=1,
    )
    rule = Rule.objects.create(condition=condition)
    Predicate.objects.create(
        rule=rule,
        operator=PredicateOperator.EQUAL,
        field_type=field.type,
        field=field.api_name,
        value='1740087999',
    )

    # act
    result = ConditionCheckService.check(
        condition=condition,
        workflow_id=workflow.id,
    )

    # assert
    assert result is True


def test_check__date__not_equal__non_timestamp_predicate__fail():

    """Check returns False when predicate is not a valid timestamp."""

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(user=owner, tasks_count=2)
    first_task = workflow.tasks.first()
    second_task = workflow.tasks.last()
    field = TaskField.objects.create(
        name='Date field',
        api_name='date-1',
        task=first_task,
        type=FieldType.DATE,
        value='',
        workflow=workflow,
        account=owner.account,
    )
    condition = Condition.objects.create(
        task=second_task,
        action=ConditionAction.SKIP_TASK,
        order=1,
    )
    rule = Rule.objects.create(condition=condition)
    Predicate.objects.create(
        rule=rule,
        operator=PredicateOperator.NOT_EQUAL,
        field_type=field.type,
        field=field.api_name,
        value='Captain Marvel',
    )

    # act
    result = ConditionCheckService.check(
        condition=condition,
        workflow_id=workflow.id,
    )

    # assert
    assert result is False


def test_check__date__not_equal__same_timestamps__fail():

    """Check returns False when field and predicate timestamps are the same."""

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(user=owner, tasks_count=2)
    first_task = workflow.tasks.first()
    second_task = workflow.tasks.last()
    field = TaskField.objects.create(
        name='Date field',
        api_name='date-1',
        task=first_task,
        type=FieldType.DATE,
        value='1740087999',
        workflow=workflow,
        account=owner.account,
    )
    condition = Condition.objects.create(
        task=second_task,
        action=ConditionAction.SKIP_TASK,
        order=1,
    )
    rule = Rule.objects.create(condition=condition)
    Predicate.objects.create(
        rule=rule,
        operator=PredicateOperator.NOT_EQUAL,
        field_type=field.type,
        field=field.api_name,
        value='1740087999',
    )

    # act
    result = ConditionCheckService.check(
        condition=condition,
        workflow_id=workflow.id,
    )

    # assert
    assert result is False


def test_check__date__not_equal__different_timestamps__ok():

    """Check returns True when field and predicate timestamps differ."""

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(user=owner, tasks_count=2)
    first_task = workflow.tasks.first()
    second_task = workflow.tasks.last()
    field = TaskField.objects.create(
        name='Date field',
        api_name='date-1',
        task=first_task,
        type=FieldType.DATE,
        value='1740087998',
        workflow=workflow,
        account=owner.account,
    )
    condition = Condition.objects.create(
        task=second_task,
        action=ConditionAction.SKIP_TASK,
        order=1,
    )
    rule = Rule.objects.create(condition=condition)
    Predicate.objects.create(
        rule=rule,
        operator=PredicateOperator.NOT_EQUAL,
        field_type=field.type,
        field=field.api_name,
        value='1740087999',
    )

    # act
    result = ConditionCheckService.check(
        condition=condition,
        workflow_id=workflow.id,
    )

    # assert
    assert result is True


def test_check__date__exist__non_timestamp_value__fail():

    """Check returns False when field value is not a valid timestamp."""

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(user=owner, tasks_count=2)
    first_task = workflow.tasks.first()
    second_task = workflow.tasks.last()
    field = TaskField.objects.create(
        name='Date field',
        api_name='date-1',
        task=first_task,
        type=FieldType.DATE,
        value='Captain Marvel',
        workflow=workflow,
        account=owner.account,
    )
    condition = Condition.objects.create(
        task=second_task,
        action=ConditionAction.SKIP_TASK,
        order=1,
    )
    rule = Rule.objects.create(condition=condition)
    Predicate.objects.create(
        rule=rule,
        operator=PredicateOperator.EXIST,
        field_type=field.type,
        field=field.api_name,
        value=None,
    )

    # act
    result = ConditionCheckService.check(
        condition=condition,
        workflow_id=workflow.id,
    )

    # assert
    assert result is False


def test_check__date__exist__valid_timestamp__ok():

    """Check returns True when field value is a valid Unix timestamp."""

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(user=owner, tasks_count=2)
    first_task = workflow.tasks.first()
    second_task = workflow.tasks.last()
    field = TaskField.objects.create(
        name='Date field',
        api_name='date-1',
        task=first_task,
        type=FieldType.DATE,
        value='1740087999',
        workflow=workflow,
        account=owner.account,
    )
    condition = Condition.objects.create(
        task=second_task,
        action=ConditionAction.SKIP_TASK,
        order=1,
    )
    rule = Rule.objects.create(condition=condition)
    Predicate.objects.create(
        rule=rule,
        operator=PredicateOperator.EXIST,
        field_type=field.type,
        field=field.api_name,
        value=None,
    )

    # act
    result = ConditionCheckService.check(
        condition=condition,
        workflow_id=workflow.id,
    )

    # assert
    assert result is True


def test_check__date__not_exist__non_timestamp_value__ok():

    """
    Check returns True when field value is not a valid
    timestamp (treated as absent).
    """

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(user=owner, tasks_count=2)
    first_task = workflow.tasks.first()
    second_task = workflow.tasks.last()
    field = TaskField.objects.create(
        name='Date field',
        api_name='date-1',
        task=first_task,
        type=FieldType.DATE,
        value='C',
        workflow=workflow,
        account=owner.account,
    )
    condition = Condition.objects.create(
        task=second_task,
        action=ConditionAction.SKIP_TASK,
        order=1,
    )
    rule = Rule.objects.create(condition=condition)
    Predicate.objects.create(
        rule=rule,
        operator=PredicateOperator.NOT_EXIST,
        field_type=field.type,
        field=field.api_name,
        value=None,
    )

    # act
    result = ConditionCheckService.check(
        condition=condition,
        workflow_id=workflow.id,
    )

    # assert
    assert result is True


def test_check__date__more_than__field_greater__ok():

    """Check returns True when field timestamp is greater than predicate."""

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(user=owner, tasks_count=2)
    first_task = workflow.tasks.first()
    second_task = workflow.tasks.last()
    field = TaskField.objects.create(
        name='Date field',
        api_name='date-1',
        task=first_task,
        type=FieldType.DATE,
        value='1740097999',
        workflow=workflow,
        account=owner.account,
    )
    condition = Condition.objects.create(
        task=second_task,
        action=ConditionAction.SKIP_TASK,
        order=1,
    )
    rule = Rule.objects.create(condition=condition)
    Predicate.objects.create(
        rule=rule,
        operator=PredicateOperator.MORE_THAN,
        field_type=field.type,
        field=field.api_name,
        value='1740087999',
    )

    # act
    result = ConditionCheckService.check(
        condition=condition,
        workflow_id=workflow.id,
    )

    # assert
    assert result is True


def test_check__date__more_than__field_less__fail():

    """Check returns False when field timestamp is less than predicate."""

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(user=owner, tasks_count=2)
    first_task = workflow.tasks.first()
    second_task = workflow.tasks.last()
    field = TaskField.objects.create(
        name='Date field',
        api_name='date-1',
        task=first_task,
        type=FieldType.DATE,
        value='1740077999',
        workflow=workflow,
        account=owner.account,
    )
    condition = Condition.objects.create(
        task=second_task,
        action=ConditionAction.SKIP_TASK,
        order=1,
    )
    rule = Rule.objects.create(condition=condition)
    Predicate.objects.create(
        rule=rule,
        operator=PredicateOperator.MORE_THAN,
        field_type=field.type,
        field=field.api_name,
        value='1740087999',
    )

    # act
    result = ConditionCheckService.check(
        condition=condition,
        workflow_id=workflow.id,
    )

    # assert
    assert result is False


def test_check__date__less_than__field_greater__fail():

    """Check returns False when field timestamp is greater than predicate."""

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(user=owner, tasks_count=2)
    first_task = workflow.tasks.first()
    second_task = workflow.tasks.last()
    field = TaskField.objects.create(
        name='Date field',
        api_name='date-1',
        task=first_task,
        type=FieldType.DATE,
        value='1740097999',
        workflow=workflow,
        account=owner.account,
    )
    condition = Condition.objects.create(
        task=second_task,
        action=ConditionAction.SKIP_TASK,
        order=1,
    )
    rule = Rule.objects.create(condition=condition)
    Predicate.objects.create(
        rule=rule,
        operator=PredicateOperator.LESS_THAN,
        field_type=field.type,
        field=field.api_name,
        value='1740087999',
    )

    # act
    result = ConditionCheckService.check(
        condition=condition,
        workflow_id=workflow.id,
    )

    # assert
    assert result is False


def test_check__date__less_than__field_less__ok():

    """Check returns True when field timestamp is less than predicate."""

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(user=owner, tasks_count=2)
    first_task = workflow.tasks.first()
    second_task = workflow.tasks.last()
    field = TaskField.objects.create(
        name='Date field',
        api_name='date-1',
        task=first_task,
        type=FieldType.DATE,
        value='1740077999',
        workflow=workflow,
        account=owner.account,
    )
    condition = Condition.objects.create(
        task=second_task,
        action=ConditionAction.SKIP_TASK,
        order=1,
    )
    rule = Rule.objects.create(condition=condition)
    Predicate.objects.create(
        rule=rule,
        operator=PredicateOperator.LESS_THAN,
        field_type=field.type,
        field=field.api_name,
        value='1740087999',
    )

    # act
    result = ConditionCheckService.check(
        condition=condition,
        workflow_id=workflow.id,
    )

    # assert
    assert result is True


# endregion

# region user


def test_check__user__equal__different_users__fail():

    """
    Check returns False when field user_id differs
    from predicate user id.
    """

    # arrange
    owner = create_test_owner()
    second_user = create_test_not_admin(account=owner.account)
    workflow = create_test_workflow(user=owner, tasks_count=2)
    first_task = workflow.tasks.first()
    second_task = workflow.tasks.last()
    field = TaskField.objects.create(
        name='User field',
        api_name='user-1',
        task=first_task,
        type=FieldType.USER,
        value=second_user.get_full_name(),
        workflow=workflow,
        user_id=second_user.id,
        account=owner.account,
    )
    condition = Condition.objects.create(
        task=second_task,
        action=ConditionAction.SKIP_TASK,
        order=1,
    )
    rule = Rule.objects.create(condition=condition)
    Predicate.objects.create(
        rule=rule,
        operator=PredicateOperator.EQUAL,
        field_type=field.type,
        field=field.api_name,
        value=owner.id,
    )

    # act
    result = ConditionCheckService.check(
        condition=condition,
        workflow_id=workflow.id,
    )

    # assert
    assert result is False


def test_check__user__equal__same_user__ok():

    """Check returns True when field user_id matches predicate user id."""

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(user=owner, tasks_count=2)
    first_task = workflow.tasks.first()
    second_task = workflow.tasks.last()
    field = TaskField.objects.create(
        name='User field',
        api_name='user-1',
        task=first_task,
        type=FieldType.USER,
        value=owner.get_full_name(),
        workflow=workflow,
        user_id=owner.id,
        account=owner.account,
    )
    condition = Condition.objects.create(
        task=second_task,
        action=ConditionAction.SKIP_TASK,
        order=1,
    )
    rule = Rule.objects.create(condition=condition)
    Predicate.objects.create(
        rule=rule,
        operator=PredicateOperator.EQUAL,
        field_type=field.type,
        field=field.api_name,
        value=owner.id,
    )

    # act
    result = ConditionCheckService.check(
        condition=condition,
        workflow_id=workflow.id,
    )

    # assert
    assert result is True


def test_check__user__equal__predicate_none__fail():

    """Check returns False when predicate value is None."""

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(user=owner, tasks_count=2)
    first_task = workflow.tasks.first()
    second_task = workflow.tasks.last()
    field = TaskField.objects.create(
        name='User field',
        api_name='user-1',
        task=first_task,
        type=FieldType.USER,
        value=owner.get_full_name(),
        workflow=workflow,
        user_id=owner.id,
        account=owner.account,
    )
    condition = Condition.objects.create(
        task=second_task,
        action=ConditionAction.SKIP_TASK,
        order=1,
    )
    rule = Rule.objects.create(condition=condition)
    Predicate.objects.create(
        rule=rule,
        operator=PredicateOperator.EQUAL,
        field_type=field.type,
        field=field.api_name,
        value=None,
    )

    # act
    result = ConditionCheckService.check(
        condition=condition,
        workflow_id=workflow.id,
    )

    # assert
    assert result is False


def test_check__user__not_equal__field_empty__fail():

    """Check returns False when field has no user and predicate is None."""

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(user=owner, tasks_count=2)
    first_task = workflow.tasks.first()
    second_task = workflow.tasks.last()
    field = TaskField.objects.create(
        name='User field',
        api_name='user-1',
        task=first_task,
        type=FieldType.USER,
        value='',
        workflow=workflow,
        user_id=None,
        account=owner.account,
    )
    condition = Condition.objects.create(
        task=second_task,
        action=ConditionAction.SKIP_TASK,
        order=1,
    )
    rule = Rule.objects.create(condition=condition)
    Predicate.objects.create(
        rule=rule,
        operator=PredicateOperator.NOT_EQUAL,
        field_type=field.type,
        field=field.api_name,
        value=None,
    )

    # act
    result = ConditionCheckService.check(
        condition=condition,
        workflow_id=workflow.id,
    )

    # assert
    assert result is False


def test_check__user__not_equal__same_user__fail():

    """Check returns False when field user_id matches predicate user id."""

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(user=owner, tasks_count=2)
    first_task = workflow.tasks.first()
    second_task = workflow.tasks.last()
    field = TaskField.objects.create(
        name='User field',
        api_name='user-1',
        task=first_task,
        type=FieldType.USER,
        value=owner.get_full_name(),
        workflow=workflow,
        user_id=owner.id,
        account=owner.account,
    )
    condition = Condition.objects.create(
        task=second_task,
        action=ConditionAction.SKIP_TASK,
        order=1,
    )
    rule = Rule.objects.create(condition=condition)
    Predicate.objects.create(
        rule=rule,
        operator=PredicateOperator.NOT_EQUAL,
        field_type=field.type,
        field=field.api_name,
        value=owner.id,
    )

    # act
    result = ConditionCheckService.check(
        condition=condition,
        workflow_id=workflow.id,
    )

    # assert
    assert result is False


def test_check__user__exist__user_set__ok():

    """Check returns True when field has a user assigned."""

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(user=owner, tasks_count=2)
    first_task = workflow.tasks.first()
    second_task = workflow.tasks.last()
    field = TaskField.objects.create(
        name='User field',
        api_name='user-1',
        task=first_task,
        type=FieldType.USER,
        value=owner.get_full_name(),
        workflow=workflow,
        user_id=owner.id,
        account=owner.account,
    )
    condition = Condition.objects.create(
        task=second_task,
        action=ConditionAction.SKIP_TASK,
        order=1,
    )
    rule = Rule.objects.create(condition=condition)
    Predicate.objects.create(
        rule=rule,
        operator=PredicateOperator.EXIST,
        field_type=field.type,
        field=field.api_name,
        value=None,
    )

    # act
    result = ConditionCheckService.check(
        condition=condition,
        workflow_id=workflow.id,
    )

    # assert
    assert result is True


# endregion

# region group


def test_check__group__equal__matching_group__ok():

    """Check returns True when field group_id matches predicate group id."""

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(user=owner, tasks_count=2)
    first_task = workflow.tasks.get(number=1)
    second_task = workflow.tasks.get(number=2)
    field = TaskField.objects.create(
        name='Group field',
        api_name='group-1',
        task=first_task,
        type=FieldType.USER,
        value='1',
        workflow=workflow,
        group_id=1,
        account=owner.account,
    )
    condition = Condition.objects.create(
        task=second_task,
        action=ConditionAction.SKIP_TASK,
        order=1,
    )
    rule = Rule.objects.create(condition=condition)
    Predicate.objects.create(
        rule=rule,
        operator=PredicateOperator.EQUAL,
        field_type=PredicateType.GROUP,
        field=field.api_name,
        value='1',
    )

    # act
    result = ConditionCheckService.check(
        condition=condition,
        workflow_id=workflow.id,
    )

    # assert
    assert result is True


def test_check__group__equal__different_group__fail():

    """Check returns False when field group_id differs from predicate."""

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(user=owner, tasks_count=2)
    first_task = workflow.tasks.get(number=1)
    second_task = workflow.tasks.get(number=2)
    field = TaskField.objects.create(
        name='Group field',
        api_name='group-1',
        task=first_task,
        type=FieldType.USER,
        value='2',
        workflow=workflow,
        group_id=2,
        account=owner.account,
    )
    condition = Condition.objects.create(
        task=second_task,
        action=ConditionAction.SKIP_TASK,
        order=1,
    )
    rule = Rule.objects.create(condition=condition)
    Predicate.objects.create(
        rule=rule,
        operator=PredicateOperator.EQUAL,
        field_type=PredicateType.GROUP,
        field=field.api_name,
        value='1',
    )

    # act
    result = ConditionCheckService.check(
        condition=condition,
        workflow_id=workflow.id,
    )

    # assert
    assert result is False


def test_check__group__equal__predicate_none__fail():

    """Check returns False when predicate value is None."""

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(user=owner, tasks_count=2)
    first_task = workflow.tasks.get(number=1)
    second_task = workflow.tasks.get(number=2)
    field = TaskField.objects.create(
        name='Group field',
        api_name='group-1',
        task=first_task,
        type=FieldType.USER,
        value='1',
        workflow=workflow,
        group_id=1,
        account=owner.account,
    )
    condition = Condition.objects.create(
        task=second_task,
        action=ConditionAction.SKIP_TASK,
        order=1,
    )
    rule = Rule.objects.create(condition=condition)
    Predicate.objects.create(
        rule=rule,
        operator=PredicateOperator.EQUAL,
        field_type=PredicateType.GROUP,
        field=field.api_name,
        value=None,
    )

    # act
    result = ConditionCheckService.check(
        condition=condition,
        workflow_id=workflow.id,
    )

    # assert
    assert result is False


def test_check__group__not_equal__different_group__ok():

    """Check returns True when field group_id differs from predicate."""

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(user=owner, tasks_count=2)
    first_task = workflow.tasks.get(number=1)
    second_task = workflow.tasks.get(number=2)
    field = TaskField.objects.create(
        name='Group field',
        api_name='group-1',
        task=first_task,
        type=FieldType.USER,
        value='2',
        workflow=workflow,
        group_id=2,
        account=owner.account,
    )
    condition = Condition.objects.create(
        task=second_task,
        action=ConditionAction.SKIP_TASK,
        order=1,
    )
    rule = Rule.objects.create(condition=condition)
    Predicate.objects.create(
        rule=rule,
        operator=PredicateOperator.NOT_EQUAL,
        field_type=PredicateType.GROUP,
        field=field.api_name,
        value='1',
    )

    # act
    result = ConditionCheckService.check(
        condition=condition,
        workflow_id=workflow.id,
    )

    # assert
    assert result is True


def test_check__group__not_equal__same_group__fail():

    """Check returns False when field group_id matches predicate."""

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(user=owner, tasks_count=2)
    first_task = workflow.tasks.get(number=1)
    second_task = workflow.tasks.get(number=2)
    field = TaskField.objects.create(
        name='Group field',
        api_name='group-1',
        task=first_task,
        type=FieldType.USER,
        value='1',
        workflow=workflow,
        group_id=1,
        account=owner.account,
    )
    condition = Condition.objects.create(
        task=second_task,
        action=ConditionAction.SKIP_TASK,
        order=1,
    )
    rule = Rule.objects.create(condition=condition)
    Predicate.objects.create(
        rule=rule,
        operator=PredicateOperator.NOT_EQUAL,
        field_type=PredicateType.GROUP,
        field=field.api_name,
        value='1',
    )

    # act
    result = ConditionCheckService.check(
        condition=condition,
        workflow_id=workflow.id,
    )

    # assert
    assert result is False


def test_check__group__exist__group_set__ok():

    """Check returns True when field has a group assigned."""

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(user=owner, tasks_count=2)
    first_task = workflow.tasks.get(number=1)
    second_task = workflow.tasks.get(number=2)
    field = TaskField.objects.create(
        name='Group field',
        api_name='group-1',
        task=first_task,
        type=FieldType.USER,
        value='1',
        workflow=workflow,
        group_id=1,
        account=owner.account,
    )
    condition = Condition.objects.create(
        task=second_task,
        action=ConditionAction.SKIP_TASK,
        order=1,
    )
    rule = Rule.objects.create(condition=condition)
    Predicate.objects.create(
        rule=rule,
        operator=PredicateOperator.EXIST,
        field_type=PredicateType.GROUP,
        field=field.api_name,
        value=None,
    )

    # act
    result = ConditionCheckService.check(
        condition=condition,
        workflow_id=workflow.id,
    )

    # assert
    assert result is True


def test_check__group__exist__group_none__fail():

    """Check returns False when field has no group assigned."""

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(user=owner, tasks_count=2)
    first_task = workflow.tasks.get(number=1)
    second_task = workflow.tasks.get(number=2)
    field = TaskField.objects.create(
        name='Group field',
        api_name='group-1',
        task=first_task,
        type=FieldType.USER,
        value='',
        workflow=workflow,
        group_id=None,
        account=owner.account,
    )
    condition = Condition.objects.create(
        task=second_task,
        action=ConditionAction.SKIP_TASK,
        order=1,
    )
    rule = Rule.objects.create(condition=condition)
    Predicate.objects.create(
        rule=rule,
        operator=PredicateOperator.EXIST,
        field_type=PredicateType.GROUP,
        field=field.api_name,
        value=None,
    )

    # act
    result = ConditionCheckService.check(
        condition=condition,
        workflow_id=workflow.id,
    )

    # assert
    assert result is False


def test_check__group__not_exist__group_none__ok():

    """Check returns True when field has no group assigned."""

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(user=owner, tasks_count=2)
    first_task = workflow.tasks.get(number=1)
    second_task = workflow.tasks.get(number=2)
    field = TaskField.objects.create(
        name='Group field',
        api_name='group-1',
        task=first_task,
        type=FieldType.USER,
        value='',
        workflow=workflow,
        group_id=None,
        account=owner.account,
    )
    condition = Condition.objects.create(
        task=second_task,
        action=ConditionAction.SKIP_TASK,
        order=1,
    )
    rule = Rule.objects.create(condition=condition)
    Predicate.objects.create(
        rule=rule,
        operator=PredicateOperator.NOT_EXIST,
        field_type=PredicateType.GROUP,
        field=field.api_name,
        value=None,
    )

    # act
    result = ConditionCheckService.check(
        condition=condition,
        workflow_id=workflow.id,
    )

    # assert
    assert result is True


def test_check__group__not_exist__group_set__fail():

    """Check returns False when field has a group assigned."""

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(user=owner, tasks_count=2)
    first_task = workflow.tasks.get(number=1)
    second_task = workflow.tasks.get(number=2)
    field = TaskField.objects.create(
        name='Group field',
        api_name='group-1',
        task=first_task,
        type=FieldType.USER,
        value='1',
        workflow=workflow,
        group_id=1,
        account=owner.account,
    )
    condition = Condition.objects.create(
        task=second_task,
        action=ConditionAction.SKIP_TASK,
        order=1,
    )
    rule = Rule.objects.create(condition=condition)
    Predicate.objects.create(
        rule=rule,
        operator=PredicateOperator.NOT_EXIST,
        field_type=PredicateType.GROUP,
        field=field.api_name,
        value=None,
    )

    # act
    result = ConditionCheckService.check(
        condition=condition,
        workflow_id=workflow.id,
    )

    # assert
    assert result is False


# endregion

# region task / kickoff


def test_check__task_completed__return_true():

    """Check returns True when the referenced task has completed status."""

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(user=owner, tasks_count=2)
    task_1 = workflow.tasks.get(number=1)
    task_1.status = TaskStatus.COMPLETED
    task_1.save()
    task_2 = workflow.tasks.get(number=2)
    condition = Condition.objects.create(
        task=task_2,
        action=ConditionAction.SKIP_TASK,
        order=1,
    )
    rule = Rule.objects.create(condition=condition)
    Predicate.objects.create(
        rule=rule,
        operator=PredicateOperator.COMPLETED,
        field_type=PredicateType.TASK,
        field=task_1.api_name,
        value=None,
    )

    # act
    result = ConditionCheckService.check(
        condition=condition,
        workflow_id=workflow.id,
    )

    # assert
    assert result is True


def test_check__task_not_completed__return_false():

    """Check returns False when the referenced task has not completed."""

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(user=owner, tasks_count=2)
    task_1 = workflow.tasks.get(number=1)
    task_2 = workflow.tasks.get(number=2)
    condition = Condition.objects.create(
        task=task_2,
        action=ConditionAction.SKIP_TASK,
        order=1,
    )
    rule = Rule.objects.create(condition=condition)
    Predicate.objects.create(
        rule=rule,
        operator=PredicateOperator.COMPLETED,
        field_type=PredicateType.TASK,
        field=task_1.api_name,
        value=None,
    )

    # act
    result = ConditionCheckService.check(
        condition=condition,
        workflow_id=workflow.id,
    )

    # assert
    assert result is False


def test_check__kickoff_completed__return_true():

    """Check returns True when predicate type is kickoff (always completed)."""

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(user=owner, tasks_count=1)
    task_1 = workflow.tasks.get(number=1)
    condition = Condition.objects.create(
        task=task_1,
        action=ConditionAction.SKIP_TASK,
        order=1,
    )
    rule = Rule.objects.create(condition=condition)
    Predicate.objects.create(
        rule=rule,
        operator=PredicateOperator.COMPLETED,
        field_type=PredicateType.KICKOFF,
        field=None,
        value=None,
    )

    # act
    result = ConditionCheckService.check(
        condition=condition,
        workflow_id=workflow.id,
    )

    # assert
    assert result is True

# endregion
