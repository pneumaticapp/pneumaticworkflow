import pytest
from src.authentication.enums import AuthTokenType
from src.processes.enums import (
    FieldSetRuleOperator,
    FieldType,
)
from src.processes.messages.fieldset import (
    MSG_FS_0002,
    MSG_FS_0007,
    MSG_FS_0012,
)
from src.processes.models.templates.fieldset import (
    FieldsetTemplate,
    FieldSetTemplateRuleSet,
    FieldSetTemplateRuleGroupOr,
    FieldSetTemplateRuleGroupAnd,
)
from src.processes.models.templates.fields import FieldTemplate
from src.processes.models.workflows.fieldset import (
    FieldSetRuleGroupAnd,
    FieldSetRuleGroupOr,
)
from src.processes.services.exceptions import FieldsetServiceException
from src.processes.services.tasks.field import TaskFieldService
from src.processes.services.workflows.fieldsets.fieldset import (
    FieldSetService,
)
from src.processes.services.workflows.fieldsets.fieldset_ruleset import (
    FieldSetRuleSetService,
)
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_fieldset,
    create_test_owner,
    create_test_template,
    create_test_workflow,
    create_test_fieldset_template,
)

pytestmark = pytest.mark.django_db


def test__create_instance__with_kickoff__ok():

    """
    Call with kickoff
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user, tasks_count=1)
    workflow = create_test_workflow(user=user, template=template)
    kickoff = workflow.kickoff_instance
    order = 11
    fieldset_template = FieldsetTemplate.objects.create(
        template=template,
        account=account,
        order=order,
    )
    service = FieldSetService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )

    # act
    service._create_instance(
        instance_template=fieldset_template,
        workflow=workflow,
        kickoff=kickoff,
        order=order,
    )

    # assert
    assert service.instance.account == account
    assert service.instance.workflow_id == workflow.id
    assert service.instance.task is None
    assert service.instance.kickoff == kickoff
    assert service.instance.api_name == fieldset_template.api_name
    assert service.instance.name == fieldset_template.name
    assert service.instance.title == fieldset_template.title
    assert service.instance.description == fieldset_template.description
    assert service.instance.order == order
    assert service.instance.label_position == fieldset_template.label_position
    assert service.instance.layout == fieldset_template.layout


def test__create_instance__with_task__ok():

    """
    Call with task
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user, tasks_count=1)
    workflow = create_test_workflow(user=user, template=template)
    task = workflow.tasks.first()
    order = 11
    fieldset_template = create_test_fieldset_template(
        template=template,
        account=account,
        order=order,
    )
    service = FieldSetService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )

    # act
    service._create_instance(
        instance_template=fieldset_template,
        workflow=workflow,
        task=task,
    )

    # assert
    assert service.instance.account == account
    assert service.instance.workflow == workflow
    assert service.instance.task == task
    assert service.instance.kickoff is None
    assert service.instance.api_name == fieldset_template.api_name
    assert service.instance.name == fieldset_template.name
    assert service.instance.title == fieldset_template.title
    assert service.instance.description == fieldset_template.description
    assert service.instance.order == order
    assert service.instance.label_position == fieldset_template.label_position
    assert service.instance.layout == fieldset_template.layout


def test__create_instance__no_kickoff_no_task__raise_exception():

    """
    Call without kickoff and task
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user, tasks_count=1)
    workflow = create_test_workflow(user=user, template=template)
    fieldset_template = FieldsetTemplate.objects.create(
        template=template,
        account=account,
        name='Fieldset',
    )
    service = FieldSetService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    order = 11

    # act
    with pytest.raises(FieldsetServiceException) as ex:
        service._create_instance(
            instance_template=fieldset_template,
            workflow=workflow,
            order=order,
        )

    # assert
    assert ex.value.message == MSG_FS_0007


def test__create_fields__default_params__ok(mocker):

    """
    Call with default parameters
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user, tasks_count=1)
    workflow = create_test_workflow(user=user, template=template)
    fieldset_template = FieldsetTemplate.objects.create(
        template=template,
        account=account,
        name='Fieldset',
    )
    FieldTemplate.objects.create(
        account=account,
        fieldset=fieldset_template,
        name='Field 1',
        type=FieldType.NUMBER,
        order=1,
    )
    fieldset = create_test_fieldset(
        workflow=workflow,
    )
    service = FieldSetService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=fieldset,
    )
    task_field_service_init_mock = mocker.patch.object(
        TaskFieldService,
        attribute='__init__',
        return_value=None,
    )
    task_field_service_create_mock = mocker.patch(
        'src.processes.services.tasks.field.'
        'TaskFieldService.create',
    )

    # act
    service._create_fields(
        instance_template=fieldset_template,
    )

    # assert
    task_field_service_init_mock.assert_called_once_with(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    task_field_service_create_mock.assert_called_once_with(
        instance_template=fieldset_template.fields.first(),
        workflow_id=fieldset.workflow_id,
        fieldset_id=fieldset.id,
        skip_value=False,
        value='',
    )


def test__create_fields__with_fields_data__ok(mocker):

    """
    Call with fields_data provided
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user, tasks_count=1)
    workflow = create_test_workflow(user=user, template=template)
    fieldset_template = FieldsetTemplate.objects.create(
        template=template,
        account=account,
        name='Fieldset',
    )
    field_template_1 = FieldTemplate.objects.create(
        account=account,
        fieldset=fieldset_template,
        name='Field 1',
        type=FieldType.NUMBER,
        order=1,
    )
    fieldset = create_test_fieldset(
        workflow=workflow,
    )
    service = FieldSetService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=fieldset,
    )
    fields_data = {field_template_1.api_name: '42'}
    task_field_service_init_mock = mocker.patch.object(
        TaskFieldService,
        attribute='__init__',
        return_value=None,
    )
    task_field_service_create_mock = mocker.patch(
        'src.processes.services.tasks.field.'
        'TaskFieldService.create',
    )

    # act
    service._create_fields(
        instance_template=fieldset_template,
        fields_data=fields_data,
    )

    # assert
    task_field_service_init_mock.assert_called_once_with(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    task_field_service_create_mock.assert_called_once_with(
        instance_template=field_template_1,
        workflow_id=fieldset.workflow_id,
        fieldset_id=fieldset.id,
        skip_value=False,
        value='42',
    )


def test__create_fields__skip_value_true__ok(mocker):

    """
    Call with skip_value=True
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user, tasks_count=1)
    workflow = create_test_workflow(user=user, template=template)
    fieldset_template = FieldsetTemplate.objects.create(
        template=template,
        account=account,
        name='Fieldset',
    )
    FieldTemplate.objects.create(
        account=account,
        fieldset=fieldset_template,
        name='Field 1',
        type=FieldType.NUMBER,
        order=1,
    )
    fieldset = create_test_fieldset(
        workflow=workflow,
    )
    service = FieldSetService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=fieldset,
    )
    task_field_service_init_mock = mocker.patch.object(
        TaskFieldService,
        attribute='__init__',
        return_value=None,
    )
    task_field_service_create_mock = mocker.patch(
        'src.processes.services.tasks.field.'
        'TaskFieldService.create',
    )

    # act
    service._create_fields(
        instance_template=fieldset_template,
        skip_value=True,
    )

    # assert
    task_field_service_init_mock.assert_called_once_with(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    task_field_service_create_mock.assert_called_once_with(
        instance_template=fieldset_template.fields.first(),
        workflow_id=fieldset.workflow_id,
        fieldset_id=fieldset.id,
        skip_value=True,
        value='',
    )


def test__create_rulesets__with_template__ok(mocker):

    """
    Call with instance_template
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user, tasks_count=1)
    workflow = create_test_workflow(user=user, template=template)
    fieldset_template = FieldsetTemplate.objects.create(
        template=template,
        account=account,
        name='Fieldset',
    )
    ruleset = FieldSetTemplateRuleSet.objects.create(
        account=account,
        fieldset=fieldset_template,
        api_name='ruleset-1',
    )
    group_or = FieldSetTemplateRuleGroupOr.objects.create(
        fieldset_rule=ruleset,
        account=account,
        api_name='group-or-1',
    )
    FieldSetTemplateRuleGroupAnd.objects.create(
        group_or=group_or,
        account=account,
        api_name='group-and-1',
        operator=FieldSetRuleOperator.SUM_EQUAL,
        value='100',
    )
    fieldset = create_test_fieldset(
        workflow=workflow,
    )
    service = FieldSetService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=fieldset,
    )
    ruleset_service_init_mock = mocker.patch.object(
        FieldSetRuleSetService,
        attribute='__init__',
        return_value=None,
    )
    ruleset_service_create_mock = mocker.patch(
        'src.processes.services.workflows.fieldsets.fieldset_ruleset.'
        'FieldSetRuleSetService.create',
    )

    # act
    service._create_rulesets(instance_template=fieldset_template)

    # assert
    ruleset_service_init_mock.assert_called_once_with(
        user=user,
    )
    ruleset_service_create_mock.assert_called_once_with(
        instance_template=ruleset,
        fieldset=fieldset,
        skip_validation=None,
    )


def test__create_related__with_template__ok(mocker):

    """
    Call with instance_template
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user, tasks_count=1)
    fieldset_template = FieldsetTemplate.objects.create(
        template=template,
        account=account,
        name='Fieldset',
    )
    service = FieldSetService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    create_fields_mock = mocker.patch(
        'src.processes.services.workflows.fieldsets.fieldset.'
        'FieldSetService._create_fields',
    )
    create_rulesets_mock = mocker.patch(
        'src.processes.services.workflows.fieldsets.fieldset.'
        'FieldSetService._create_rulesets',
    )

    # act
    service._create_related(instance_template=fieldset_template)

    # assert
    create_rulesets_mock.assert_called_once_with(
        fieldset_template,
    )
    create_fields_mock.assert_called_once_with(
        fieldset_template,
    )


def test_validate_rules__one_rule__ok(mocker):

    """
    Call with rules
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user, tasks_count=1)
    workflow = create_test_workflow(user=user, template=template)
    fieldset = create_test_fieldset(
        workflow=workflow,
        rule_operator=FieldSetRuleOperator.SUM_EQUAL,
        rule_value='100',
    )
    rule = fieldset.rulesets.first()
    service = FieldSetService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=fieldset,
    )
    ruleset_service_init_mock = mocker.patch.object(
        FieldSetRuleSetService,
        attribute='__init__',
        return_value=None,
    )
    ruleset_service_validate_mock = mocker.patch(
        'src.processes.services.workflows.fieldsets.fieldset_ruleset.'
        'FieldSetRuleSetService.validate',
    )

    # act
    service.validate_rules()

    # assert
    ruleset_service_init_mock.assert_called_once_with(
        user=user,
        instance=rule,
    )
    ruleset_service_validate_mock.assert_called_once_with()


def test_validate_rules__one_rule_none_matches__raise_exception(mocker):

    """
    Call with rules
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user, tasks_count=1)
    workflow = create_test_workflow(user=user, template=template)
    fieldset = create_test_fieldset(
        workflow=workflow,
        rule_operator=FieldSetRuleOperator.SUM_EQUAL,
        rule_value='100',
    )
    field = fieldset.fields.first()
    rule_100 = fieldset.rulesets.first()
    rule_100.fields.add(field)
    service = FieldSetService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=fieldset,
    )

    # act
    with pytest.raises(FieldsetServiceException) as ex:
        service.validate_rules()

    # assert
    assert ex.value.message == MSG_FS_0002('100')


def test_validate_rules__two_groups_or__first_matches__ok():

    """
    One ruleset with two OR-branches, sum_equal 10 and 0.
    Fields sum equals the first branch — validation passes.
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    workflow = create_test_workflow(user=user)
    fieldset = create_test_fieldset(
        workflow=workflow,
        rule_operator=FieldSetRuleOperator.SUM_EQUAL,
        rule_value='10',
    )
    field = fieldset.fields.first()
    ruleset = fieldset.rulesets.first()
    ruleset.fields.add(field)
    group_or_0 = FieldSetRuleGroupOr.objects.create(
        account=account,
        workflow=workflow,
        fieldset_rule=ruleset,
        api_name='group-or-2',
    )
    FieldSetRuleGroupAnd.objects.create(
        account=account,
        workflow=workflow,
        group_or=group_or_0,
        api_name='group-and-2',
        operator=FieldSetRuleOperator.SUM_EQUAL,
        value='0',
    )
    service = FieldSetService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=fieldset,
    )

    # act
    service.validate_rules()

    # assert
    assert service.instance == fieldset


def test_validate_rules__two_groups_or__second_matches__ok():

    """
    One ruleset with two OR-branches, sum_equal 100 and 10.
    Fields sum equals the second branch — validation passes.
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    workflow = create_test_workflow(user=user)
    fieldset = create_test_fieldset(
        workflow=workflow,
        rule_operator=FieldSetRuleOperator.SUM_EQUAL,
        rule_value='100',
    )
    field = fieldset.fields.first()
    ruleset = fieldset.rulesets.first()
    ruleset.fields.add(field)
    group_or_10 = FieldSetRuleGroupOr.objects.create(
        account=account,
        workflow=workflow,
        fieldset_rule=ruleset,
        api_name='group-or-2',
    )
    FieldSetRuleGroupAnd.objects.create(
        account=account,
        workflow=workflow,
        group_or=group_or_10,
        api_name='group-and-2',
        operator=FieldSetRuleOperator.SUM_EQUAL,
        value='10',
    )
    service = FieldSetService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=fieldset,
    )

    # act
    service.validate_rules()

    # assert
    assert service.instance == fieldset


def test_validate_rules__two_groups_or__none_matches__raise():

    """
    One ruleset with two OR-branches, sum_equal 100 and 0.
    Fields sum matches neither — raises FieldsetServiceException
    with MSG_FS_0012 listing the values of both branches.
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    workflow = create_test_workflow(user=user)
    fieldset = create_test_fieldset(
        workflow=workflow,
        rule_operator=FieldSetRuleOperator.SUM_EQUAL,
        rule_value='100',
    )
    field = fieldset.fields.first()
    ruleset = fieldset.rulesets.first()
    ruleset.fields.add(field)
    group_or_0 = FieldSetRuleGroupOr.objects.create(
        account=account,
        workflow=workflow,
        fieldset_rule=ruleset,
        api_name='group-or-2',
    )
    FieldSetRuleGroupAnd.objects.create(
        account=account,
        workflow=workflow,
        group_or=group_or_0,
        api_name='group-and-2',
        operator=FieldSetRuleOperator.SUM_EQUAL,
        value='0',
    )
    service = FieldSetService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=fieldset,
    )

    # act
    with pytest.raises(FieldsetServiceException) as ex:
        service.validate_rules()

    # assert
    assert ex.value.message == MSG_FS_0012('100, 0')
