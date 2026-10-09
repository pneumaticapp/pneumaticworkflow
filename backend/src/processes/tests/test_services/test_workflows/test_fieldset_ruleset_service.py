import pytest
from django.contrib.auth import get_user_model

from src.processes.enums import (
    FieldSetRuleOperator,
    FieldType,
)
from src.processes.messages.fieldset import (
    MSG_FS_0002,
    MSG_FS_0012,
)
from src.processes.models.templates.fields import FieldTemplate
from src.processes.models.templates.fieldset import (
    FieldSetTemplateRuleGroupAnd,
    FieldSetTemplateRuleGroupOr,
    FieldSetTemplateRuleSet,
    FieldsetTemplate,
)
from src.processes.models.workflows.fields import TaskField
from src.processes.models.workflows.fieldset import (
    FieldSet,
    FieldSetRuleGroupAnd,
    FieldSetRuleGroupOr,
    FieldSetRuleSet,
)
from src.processes.services.exceptions import FieldsetServiceException
from src.processes.services.workflows.fieldsets.fieldset_ruleset import (
    FieldSetRuleSetService,
)
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_owner,
    create_test_template,
    create_test_workflow,
)

UserModel = get_user_model()
pytestmark = pytest.mark.django_db


def test_create__from_template__creates_ruleset_tree():

    """ Creates FieldSetRuleSet, binds fields and creates groups """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user, tasks_count=1)
    task_template = template.tasks.first()
    fieldset_template = FieldsetTemplate.objects.create(
        account=account,
        template=template,
        task=task_template,
        name='Finances',
    )
    field_template_1 = FieldTemplate.objects.create(
        account=account,
        template=template,
        task=task_template,
        fieldset=fieldset_template,
        name='Cost 1',
        type=FieldType.NUMBER,
        api_name='cost-1',
    )
    ruleset_template = FieldSetTemplateRuleSet.objects.create(
        account=account,
        template=template,
        fieldset=fieldset_template,
        message='Sum must be 100',
        order=1,
        api_name='fs-ruleset-1',
    )
    ruleset_template.fields.add(field_template_1)
    group_or_template = FieldSetTemplateRuleGroupOr.objects.create(
        account=account,
        template=template,
        fieldset_rule=ruleset_template,
        api_name='group-or-1',
    )
    FieldSetTemplateRuleGroupAnd.objects.create(
        account=account,
        template=template,
        group_or=group_or_template,
        operator=FieldSetRuleOperator.SUM_EQUAL,
        value='100',
        api_name='group-and-1',
    )
    workflow = create_test_workflow(user=user, template=template)
    task = workflow.tasks.first()
    fieldset = FieldSet.objects.create(
        account=account,
        workflow=workflow,
        task=task,
        name='Finances',
    )
    task_field_1 = TaskField.objects.create(
        account=account,
        workflow=workflow,
        task=task,
        fieldset=fieldset,
        name='Cost 1',
        type=FieldType.NUMBER,
        api_name='cost-1',
        value='100',
    )
    service = FieldSetRuleSetService(user=user)

    # act
    ruleset = service.create(
        instance_template=ruleset_template,
        fieldset=fieldset,
        workflow=workflow,
        skip_validation=True,
    )

    # assert
    assert ruleset.account == account
    assert ruleset.workflow == workflow
    assert ruleset.fieldset == fieldset
    assert ruleset.message == 'Sum must be 100'
    assert ruleset.order == 1
    assert ruleset.api_name == 'fs-ruleset-1'

    fields = list(ruleset.fields.all())
    assert len(fields) == 1
    assert fields[0] == task_field_1

    groups_or = list(ruleset.groups_or.all())
    assert len(groups_or) == 1
    assert groups_or[0].api_name == 'group-or-1'

    groups_and = list(groups_or[0].groups_and.all())
    assert len(groups_and) == 1
    assert groups_and[0].api_name == 'group-and-1'
    assert groups_and[0].operator == FieldSetRuleOperator.SUM_EQUAL
    assert groups_and[0].value == '100'


def test_validate__sum_equal_satisfied__ok():

    """ Validation succeeds when sum equals rule target """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    workflow = create_test_workflow(user=user)
    fieldset = FieldSet.objects.create(
        account=account,
        workflow=workflow,
        name='Finances',
    )
    field_1 = TaskField.objects.create(
        account=account,
        workflow=workflow,
        fieldset=fieldset,
        name='Part 1',
        type=FieldType.NUMBER,
        value='40',
    )
    field_2 = TaskField.objects.create(
        account=account,
        workflow=workflow,
        fieldset=fieldset,
        name='Part 2',
        type=FieldType.NUMBER,
        value='60',
    )
    ruleset = FieldSetRuleSet.objects.create(
        account=account,
        workflow=workflow,
        fieldset=fieldset,
    )
    ruleset.fields.add(field_1, field_2)
    group_or = FieldSetRuleGroupOr.objects.create(
        account=account,
        workflow=workflow,
        fieldset_rule=ruleset,
    )
    FieldSetRuleGroupAnd.objects.create(
        account=account,
        workflow=workflow,
        group_or=group_or,
        operator=FieldSetRuleOperator.SUM_EQUAL,
        value='100',
    )
    service = FieldSetRuleSetService(user=user, instance=ruleset)

    # act
    result = service.validate()

    # assert
    assert result is True


def test_validate__sum_equal_failed__raises_exception():

    """ Validation fails when sum does not equal rule target """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    workflow = create_test_workflow(user=user)
    fieldset = FieldSet.objects.create(
        account=account,
        workflow=workflow,
        name='Finances',
    )
    field = TaskField.objects.create(
        account=account,
        workflow=workflow,
        fieldset=fieldset,
        name='Part 1',
        type=FieldType.NUMBER,
        value='40',
    )
    ruleset = FieldSetRuleSet.objects.create(
        account=account,
        workflow=workflow,
        fieldset=fieldset,
    )
    ruleset.fields.add(field)
    group_or = FieldSetRuleGroupOr.objects.create(
        account=account,
        workflow=workflow,
        fieldset_rule=ruleset,
    )
    FieldSetRuleGroupAnd.objects.create(
        account=account,
        workflow=workflow,
        group_or=group_or,
        operator=FieldSetRuleOperator.SUM_EQUAL,
        value='100',
    )
    service = FieldSetRuleSetService(user=user, instance=ruleset)

    # act & assert
    with pytest.raises(FieldsetServiceException) as ex:
        service.validate()

    assert ex.value.message == MSG_FS_0002('100')


def test_validate__multiple_predicates_failed__raises_msg_fs_0012():

    """ When multiple predicates fail, MSG_FS_0012 with joined values is
        raised """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    workflow = create_test_workflow(user=user)
    fieldset = FieldSet.objects.create(
        account=account,
        workflow=workflow,
        name='Finances',
    )
    field = TaskField.objects.create(
        account=account,
        workflow=workflow,
        fieldset=fieldset,
        name='Amount',
        type=FieldType.NUMBER,
        value='50',
    )
    ruleset = FieldSetRuleSet.objects.create(
        account=account,
        workflow=workflow,
        fieldset=fieldset,
    )
    ruleset.fields.add(field)
    group_or_1 = FieldSetRuleGroupOr.objects.create(
        account=account,
        workflow=workflow,
        fieldset_rule=ruleset,
        api_name='group-or-1',
    )
    FieldSetRuleGroupAnd.objects.create(
        account=account,
        workflow=workflow,
        group_or=group_or_1,
        operator=FieldSetRuleOperator.SUM_EQUAL,
        value='100',
    )
    group_or_2 = FieldSetRuleGroupOr.objects.create(
        account=account,
        workflow=workflow,
        fieldset_rule=ruleset,
        api_name='group-or-2',
    )
    FieldSetRuleGroupAnd.objects.create(
        account=account,
        workflow=workflow,
        group_or=group_or_2,
        operator=FieldSetRuleOperator.SUM_EQUAL,
        value='200',
    )
    service = FieldSetRuleSetService(user=user, instance=ruleset)

    # act & assert
    with pytest.raises(FieldsetServiceException) as ex:
        service.validate()

    assert ex.value.message == MSG_FS_0012('100, 200')


def test_validate__custom_message__raises_exception():

    """ Validation uses custom ruleset message if provided """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    workflow = create_test_workflow(user=user)
    fieldset = FieldSet.objects.create(
        account=account,
        workflow=workflow,
        name='Finances',
    )
    field = TaskField.objects.create(
        account=account,
        workflow=workflow,
        fieldset=fieldset,
        name='Part 1',
        type=FieldType.NUMBER,
        value='50',
    )
    ruleset = FieldSetRuleSet.objects.create(
        account=account,
        workflow=workflow,
        fieldset=fieldset,
        message='Amounts must match 100!',
    )
    ruleset.fields.add(field)
    group_or = FieldSetRuleGroupOr.objects.create(
        account=account,
        workflow=workflow,
        fieldset_rule=ruleset,
    )
    FieldSetRuleGroupAnd.objects.create(
        account=account,
        workflow=workflow,
        group_or=group_or,
        operator=FieldSetRuleOperator.SUM_EQUAL,
        value='100',
    )
    service = FieldSetRuleSetService(user=user, instance=ruleset)

    # act & assert
    with pytest.raises(FieldsetServiceException) as ex:
        service.validate()

    assert ex.value.message == 'Amounts must match 100!'


def test_validate__sum_greater_than__satisfied__ok():

    """ Validation succeeds for sum_greater_than operator """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    workflow = create_test_workflow(user=user)
    fieldset = FieldSet.objects.create(
        account=account,
        workflow=workflow,
        name='Finances',
    )
    field = TaskField.objects.create(
        account=account,
        workflow=workflow,
        fieldset=fieldset,
        name='Amount',
        type=FieldType.NUMBER,
        value='150',
    )
    ruleset = FieldSetRuleSet.objects.create(
        account=account,
        workflow=workflow,
        fieldset=fieldset,
    )
    ruleset.fields.add(field)
    group_or = FieldSetRuleGroupOr.objects.create(
        account=account,
        workflow=workflow,
        fieldset_rule=ruleset,
    )
    FieldSetRuleGroupAnd.objects.create(
        account=account,
        workflow=workflow,
        group_or=group_or,
        operator=FieldSetRuleOperator.SUM_GREATER_THAN,
        value='100',
    )
    service = FieldSetRuleSetService(user=user, instance=ruleset)

    # act
    result = service.validate()

    # assert
    assert result is True


def test_validate__sum_less_than__satisfied__ok():

    """ Validation succeeds for sum_less_than operator """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    workflow = create_test_workflow(user=user)
    fieldset = FieldSet.objects.create(
        account=account,
        workflow=workflow,
        name='Finances',
    )
    field = TaskField.objects.create(
        account=account,
        workflow=workflow,
        fieldset=fieldset,
        name='Amount',
        type=FieldType.NUMBER,
        value='80',
    )
    ruleset = FieldSetRuleSet.objects.create(
        account=account,
        workflow=workflow,
        fieldset=fieldset,
    )
    ruleset.fields.add(field)
    group_or = FieldSetRuleGroupOr.objects.create(
        account=account,
        workflow=workflow,
        fieldset_rule=ruleset,
    )
    FieldSetRuleGroupAnd.objects.create(
        account=account,
        workflow=workflow,
        group_or=group_or,
        operator=FieldSetRuleOperator.SUM_LESS_THAN,
        value='100',
    )
    service = FieldSetRuleSetService(user=user, instance=ruleset)

    # act
    result = service.validate()

    # assert
    assert result is True


def test_validate__no_values_exist__validation_skipped_ok():

    """ If all fields are empty and not required, validation passes """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    workflow = create_test_workflow(user=user)
    fieldset = FieldSet.objects.create(
        account=account,
        workflow=workflow,
        name='Finances',
    )
    field = TaskField.objects.create(
        account=account,
        workflow=workflow,
        fieldset=fieldset,
        name='Amount',
        type=FieldType.NUMBER,
        value='',
        is_required=False,
    )
    ruleset = FieldSetRuleSet.objects.create(
        account=account,
        workflow=workflow,
        fieldset=fieldset,
    )
    ruleset.fields.add(field)
    group_or = FieldSetRuleGroupOr.objects.create(
        account=account,
        workflow=workflow,
        fieldset_rule=ruleset,
    )
    FieldSetRuleGroupAnd.objects.create(
        account=account,
        workflow=workflow,
        group_or=group_or,
        operator=FieldSetRuleOperator.SUM_EQUAL,
        value='100',
    )
    service = FieldSetRuleSetService(user=user, instance=ruleset)

    # act
    result = service.validate()

    # assert
    assert result is True


def test_validate__empty_ruleset_without_predicates__returns_true():

    """ Returns True when ruleset has no predicates """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    workflow = create_test_workflow(user=user)
    fieldset = FieldSet.objects.create(
        account=account,
        workflow=workflow,
        name='Finances',
    )
    ruleset = FieldSetRuleSet.objects.create(
        account=account,
        workflow=workflow,
        fieldset=fieldset,
    )
    service = FieldSetRuleSetService(user=user, instance=ruleset)

    # act
    result = service.validate()

    # assert
    assert result is True


def test_create__soft_deleted_fields_and_groups__ignored():

    """ Soft deleted template fields and groups are ignored """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user, tasks_count=1)
    task_template = template.tasks.first()
    fieldset_template = FieldsetTemplate.objects.create(
        account=account,
        template=template,
        task=task_template,
        name='Finances',
    )
    field_active = FieldTemplate.objects.create(
        account=account,
        template=template,
        task=task_template,
        fieldset=fieldset_template,
        name='Active Field',
        type=FieldType.NUMBER,
        api_name='active-field',
        is_deleted=False,
    )
    FieldTemplate.objects.create(
        account=account,
        template=template,
        task=task_template,
        fieldset=fieldset_template,
        name='Deleted Field',
        type=FieldType.NUMBER,
        api_name='deleted-field',
        is_deleted=True,
    )
    ruleset_template = FieldSetTemplateRuleSet.objects.create(
        account=account,
        template=template,
        fieldset=fieldset_template,
        api_name='fs-ruleset-1',
    )
    group_or_active = FieldSetTemplateRuleGroupOr.objects.create(
        account=account,
        template=template,
        fieldset_rule=ruleset_template,
        api_name='fs-group-or-active',
        is_deleted=False,
    )
    FieldSetTemplateRuleGroupOr.objects.create(
        account=account,
        template=template,
        fieldset_rule=ruleset_template,
        api_name='fs-group-or-deleted',
        is_deleted=True,
    )
    FieldSetTemplateRuleGroupAnd.objects.create(
        account=account,
        template=template,
        group_or=group_or_active,
        operator=FieldSetRuleOperator.SUM_EQUAL,
        value='100',
        api_name='fs-group-and-active',
        is_deleted=False,
    )
    FieldSetTemplateRuleGroupAnd.objects.create(
        account=account,
        template=template,
        group_or=group_or_active,
        operator=FieldSetRuleOperator.SUM_EQUAL,
        value='200',
        api_name='fs-group-and-deleted',
        is_deleted=True,
    )
    ruleset_template.fields.add(field_active)

    workflow = create_test_workflow(user=user, template=template)
    task = workflow.tasks.first()
    fieldset = FieldSet.objects.create(
        account=account,
        workflow=workflow,
        task=task,
        name='Finances',
    )
    TaskField.objects.create(
        account=account,
        workflow=workflow,
        task=task,
        fieldset=fieldset,
        name='Active Field',
        type=FieldType.NUMBER,
        api_name='active-field',
    )
    service = FieldSetRuleSetService(user=user)

    # act
    ruleset = service.create(
        instance_template=ruleset_template,
        fieldset=fieldset,
        workflow=workflow,
    )

    # assert
    assert list(ruleset.fields.values_list('api_name', flat=True)) == [
        'active-field',
    ]
    groups_or = list(ruleset.groups_or.all())
    assert len(groups_or) == 1
    assert groups_or[0].api_name == 'fs-group-or-active'
    groups_and = list(groups_or[0].groups_and.all())
    assert len(groups_and) == 1
    assert groups_and[0].api_name == 'fs-group-and-active'


def test_create__without_user__account_from_fieldset_fallback_ok():

    """ Falls back to fieldset account if user is None """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    workflow = create_test_workflow(user=user)
    fieldset = FieldSet.objects.create(
        account=account,
        workflow=workflow,
        name='Finances',
    )
    service = FieldSetRuleSetService(user=None)

    # act
    ruleset = service.create(
        fieldset=fieldset,
        api_name='custom-fs-ruleset',
    )

    # assert
    assert ruleset.account == account
    assert ruleset.workflow_id == workflow.id
