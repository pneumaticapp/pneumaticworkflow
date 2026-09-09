import pytest

from src.processes.enums import FieldSetRuleOperator, FieldType
from src.processes.messages.fieldset import MSG_FS_0002, MSG_FS_0012
from src.processes.models.workflows.fieldset import (
    FieldSetRuleGroupAnd,
    FieldSetRuleGroupOr,
)
from src.processes.services.exceptions import FieldsetServiceException
from src.processes.services.workflows.fieldsets.fieldset_ruleset import (
    FieldSetRuleSetService,
)
from src.processes.tests.fixtures import (
    create_test_fieldset,
    create_test_fieldset_template,
    create_test_owner,
    create_test_template,
    create_test_workflow,
)

pytestmark = pytest.mark.django_db


def add_group_or(ruleset, api_name, operator, value):
    group_or = FieldSetRuleGroupOr.objects.create(
        account=ruleset.account,
        workflow=ruleset.workflow,
        fieldset_rule=ruleset,
        api_name=api_name,
    )
    FieldSetRuleGroupAnd.objects.create(
        account=ruleset.account,
        workflow=ruleset.workflow,
        group_or=group_or,
        api_name=f'{api_name}-and',
        operator=operator,
        value=value,
    )
    return group_or


def create_ruleset(workflow, operator, value, message=None):

    """ A fieldset with one ruleset, one OR-branch and one number
        field holding 10.

        The fixture only makes the field numeric for sum_equal, so the
        type and the value are set explicitly: with a non-numeric field
        the total stays None and validate() returns True regardless of
        the operator. """

    fieldset = create_test_fieldset(
        workflow=workflow,
        rule_operator=operator,
        rule_value=value,
        rule_message=message,
    )
    fieldset.fields.update(type=FieldType.NUMBER, value='10')
    ruleset = fieldset.rulesets.first()
    ruleset.fields.add(fieldset.fields.first())
    return fieldset, ruleset


def test_create__with_template__ok():

    """ Scalars, the group tree and the fields m2m are copied """

    # arrange
    user = create_test_owner()
    template = create_test_template(user=user, tasks_count=1)
    workflow = create_test_workflow(user=user, template=template)
    fieldset_template = create_test_fieldset_template(
        account=user.account,
        template=template,
        rule_operator=FieldSetRuleOperator.SUM_EQUAL,
        rule_value='100',
    )
    ruleset_template = fieldset_template.rulesets.first()
    group_and_template = (
        ruleset_template.groups_or.first().groups_and.first()
    )
    fieldset = create_test_fieldset(workflow=workflow)
    field = fieldset.fields.first()
    ruleset_template.fields.add(fieldset_template.fields.first())
    field.api_name = fieldset_template.fields.first().api_name
    field.save(update_fields=['api_name'])
    service = FieldSetRuleSetService(user=user)

    # act
    ruleset = service.create(
        instance_template=ruleset_template,
        fieldset=fieldset,
    )

    # assert
    assert ruleset.fieldset_id == fieldset.id
    assert ruleset.workflow_id == workflow.id
    assert ruleset.api_name == ruleset_template.api_name
    assert ruleset.order == ruleset_template.order
    group_and = ruleset.groups_or.get().groups_and.get()
    assert group_and.operator == group_and_template.operator
    assert group_and.value == group_and_template.value
    assert list(ruleset.fields.all()) == [field]


def test_validate__sum_equal_matches__ok():

    """ The only branch passes """

    # arrange
    user = create_test_owner()
    workflow = create_test_workflow(user=user)
    _, ruleset = create_ruleset(
        workflow,
        FieldSetRuleOperator.SUM_EQUAL,
        '10',
    )
    service = FieldSetRuleSetService(user=user, instance=ruleset)

    # act
    result = service.validate()

    # assert
    assert result is True


def test_validate__sum_equal_differs__raise():

    """ The branch fails — the single expected value is reported """

    # arrange
    user = create_test_owner()
    workflow = create_test_workflow(user=user)
    _, ruleset = create_ruleset(
        workflow,
        FieldSetRuleOperator.SUM_EQUAL,
        '100',
    )
    service = FieldSetRuleSetService(user=user, instance=ruleset)

    # act
    with pytest.raises(FieldsetServiceException) as ex:
        service.validate()

    # assert
    assert ex.value.message == MSG_FS_0002('100')


def test_validate__sum_greater_than__ok():

    # arrange
    user = create_test_owner()
    workflow = create_test_workflow(user=user)
    _, ruleset = create_ruleset(
        workflow,
        FieldSetRuleOperator.SUM_GREATER_THAN,
        '5',
    )
    service = FieldSetRuleSetService(user=user, instance=ruleset)

    # act
    result = service.validate()

    # assert
    assert result is True


def test_validate__sum_less_than__raise():

    # arrange
    user = create_test_owner()
    workflow = create_test_workflow(user=user)
    _, ruleset = create_ruleset(
        workflow,
        FieldSetRuleOperator.SUM_LESS_THAN,
        '5',
    )
    service = FieldSetRuleSetService(user=user, instance=ruleset)

    # act
    with pytest.raises(FieldsetServiceException) as ex:
        service.validate()

    # assert
    assert ex.value.message == MSG_FS_0002('5')


def test_validate__two_groups_or__none_matches__raise():

    """ Both branches fail — every expected value is reported """

    # arrange
    user = create_test_owner()
    workflow = create_test_workflow(user=user)
    _, ruleset = create_ruleset(
        workflow,
        FieldSetRuleOperator.SUM_EQUAL,
        '100',
    )
    add_group_or(
        ruleset,
        api_name='group-or-2',
        operator=FieldSetRuleOperator.SUM_EQUAL,
        value='0',
    )
    service = FieldSetRuleSetService(user=user, instance=ruleset)

    # act
    with pytest.raises(FieldsetServiceException) as ex:
        service.validate()

    # assert
    assert ex.value.message == MSG_FS_0012('100, 0')


def test_validate__custom_message__used():

    """ The ruleset message wins over the generated one """

    # arrange
    user = create_test_owner()
    workflow = create_test_workflow(user=user)
    _, ruleset = create_ruleset(
        workflow,
        FieldSetRuleOperator.SUM_EQUAL,
        '100',
        message='Shares must add up to 100%',
    )
    service = FieldSetRuleSetService(user=user, instance=ruleset)

    # act
    with pytest.raises(FieldsetServiceException) as ex:
        service.validate()

    # assert
    assert ex.value.message == 'Shares must add up to 100%'


def test_validate__no_groups_or__ok():

    """ A ruleset without branches has nothing to check """

    # arrange
    user = create_test_owner()
    workflow = create_test_workflow(user=user)
    _, ruleset = create_ruleset(
        workflow,
        FieldSetRuleOperator.SUM_EQUAL,
        '100',
    )
    ruleset.groups_or.all().delete()
    service = FieldSetRuleSetService(user=user, instance=ruleset)

    # act
    result = service.validate()

    # assert
    assert result is True


def test_validate__all_fields_blank_not_required__skip():

    """ Nothing is filled in and nothing is required — no verdict yet """

    # arrange
    user = create_test_owner()
    workflow = create_test_workflow(user=user)
    fieldset, ruleset = create_ruleset(
        workflow,
        FieldSetRuleOperator.SUM_EQUAL,
        '100',
    )
    fieldset.fields.update(value='', is_required=False)
    service = FieldSetRuleSetService(user=user, instance=ruleset)

    # act
    result = service.validate()

    # assert
    assert result is True


def test_validate__required_field_blank__raise():

    """ A required field left blank counts as zero """

    # arrange
    user = create_test_owner()
    workflow = create_test_workflow(user=user)
    fieldset, ruleset = create_ruleset(
        workflow,
        FieldSetRuleOperator.SUM_EQUAL,
        '100',
    )
    fieldset.fields.update(value='', is_required=True)
    service = FieldSetRuleSetService(user=user, instance=ruleset)

    # act
    with pytest.raises(FieldsetServiceException) as ex:
        service.validate()

    # assert
    assert ex.value.message == MSG_FS_0002('100')
