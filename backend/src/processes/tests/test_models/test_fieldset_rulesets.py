import pytest

from src.processes.enums import FieldSetRuleOperator
from src.processes.models.templates.fieldset import (
    FieldSetTemplateRuleGroupAnd,
    FieldSetTemplateRuleGroupOr,
    FieldSetTemplateRuleSet,
)
from src.processes.models.workflows.fieldset import (
    FieldSetRuleGroupAnd,
    FieldSetRuleGroupOr,
    FieldSetRuleSet,
)
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_fieldset,
    create_test_owner,
    create_test_shared_fieldset,
    create_test_workflow,
)

pytestmark = pytest.mark.django_db


def _row_is_deleted(model, pk):

    """ Reads through _base_manager, the only unfiltered manager left """

    return model._base_manager.values_list('is_deleted', flat=True).get(id=pk)


def test_delete__template_ruleset_queryset__soft_delete_with_cascade():

    """ Removing a template ruleset keeps rows and hides the whole tree """

    # arrange
    account = create_test_account()
    fieldset = create_test_shared_fieldset(
        account=account,
        rule_operator=FieldSetRuleOperator.SUM_EQUAL,
        rule_value='10',
    )
    ruleset = fieldset.rulesets.get()
    group_or = ruleset.groups_or.get()
    group_and = group_or.groups_and.get()

    # act
    fieldset.rulesets.all().delete()

    # assert
    assert _row_is_deleted(FieldSetTemplateRuleSet, ruleset.id) is True
    assert _row_is_deleted(FieldSetTemplateRuleGroupOr, group_or.id) is True
    assert _row_is_deleted(FieldSetTemplateRuleGroupAnd, group_and.id) is True

    assert FieldSetTemplateRuleSet.objects.filter(id=ruleset.id).count() == 0
    assert FieldSetTemplateRuleGroupOr.objects.filter(
        id=group_or.id,
    ).count() == 0
    assert FieldSetTemplateRuleGroupAnd.objects.filter(
        id=group_and.id,
    ).count() == 0
    assert fieldset.rulesets.count() == 0


def test_delete__workflow_ruleset_queryset__soft_delete_with_cascade():

    """ Removing a runtime ruleset keeps rows and hides the whole tree """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    workflow = create_test_workflow(user=user, tasks_count=1)
    fieldset = create_test_fieldset(
        workflow=workflow,
        kickoff=workflow.kickoff_instance,
        rule_operator=FieldSetRuleOperator.SUM_EQUAL,
        rule_value='10',
    )
    ruleset = fieldset.rulesets.get()
    group_or = ruleset.groups_or.get()
    group_and = group_or.groups_and.get()

    # act
    fieldset.rulesets.all().delete()

    # assert
    assert _row_is_deleted(FieldSetRuleSet, ruleset.id) is True
    assert _row_is_deleted(FieldSetRuleGroupOr, group_or.id) is True
    assert _row_is_deleted(FieldSetRuleGroupAnd, group_and.id) is True

    assert FieldSetRuleSet.objects.filter(id=ruleset.id).count() == 0
    assert FieldSetRuleGroupOr.objects.filter(id=group_or.id).count() == 0
    assert FieldSetRuleGroupAnd.objects.filter(id=group_and.id).count() == 0
    assert fieldset.rulesets.count() == 0


def test_delete__one_of_two_rulesets__other_is_kept():

    """ Only the excluded ruleset survives the update flow """

    # arrange
    account = create_test_account()
    fieldset = create_test_shared_fieldset(
        account=account,
        rule_operator=FieldSetRuleOperator.SUM_EQUAL,
        rule_value='10',
    )
    removed = fieldset.rulesets.get()
    kept = FieldSetTemplateRuleSet.objects.create(
        fieldset=fieldset,
        account=account,
        api_name=f'{fieldset.api_name}-shared-rule-2',
    )

    # act
    fieldset.rulesets.exclude(api_name=kept.api_name).delete()

    # assert
    assert list(fieldset.rulesets.values_list('id', flat=True)) == [kept.id]
    assert _row_is_deleted(FieldSetTemplateRuleSet, removed.id) is True
    assert _row_is_deleted(FieldSetTemplateRuleSet, kept.id) is False
