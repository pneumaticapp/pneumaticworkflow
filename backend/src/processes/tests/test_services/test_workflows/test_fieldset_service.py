import pytest
from src.authentication.enums import AuthTokenType
from src.processes.enums import (
    FieldSetRuleType,
    FieldType,
)
from src.processes.models.templates.fieldset import (
    FieldsetTemplate,
    FieldsetTemplateRule,
)
from src.processes.models.templates.fields import FieldTemplate
from src.processes.models.workflows.fieldset import (
    FieldSet,
    FieldSetRule,
)
from src.processes.services.tasks.field import TaskFieldService
from src.processes.services.workflows.fieldsets.fieldset import (
    FieldSetService,
)
from src.processes.services.workflows.fieldsets.fieldset_rule import (
    FieldSetRuleService,
)
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_owner,
    create_test_template,
    create_test_workflow,
)

pytestmark = pytest.mark.django_db


# FieldSetService._create_instance


def test__create_instance__with_kickoff__ok(mocker):

    """
    Call with kickoff
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user, tasks_count=1)
    workflow = create_test_workflow(user=user, template=template)
    kickoff = workflow.kickoff_instance
    fieldset_template = FieldsetTemplate.objects.create(
        template=template,
        account=account,
        name='Fieldset',
        description='Description',
        order=1,
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
    )

    # assert
    assert service.instance is not None
    assert service.instance.workflow_id == workflow.id
    assert service.instance.kickoff_id == kickoff.id
    assert service.instance.task is None
    assert service.instance.api_name == fieldset_template.api_name
    assert service.instance.name == 'Fieldset'
    assert service.instance.description == 'Description'
    assert service.instance.order == 1


def test__create_instance__with_task__ok(mocker):

    """
    Call with task
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user, tasks_count=1)
    workflow = create_test_workflow(user=user, template=template)
    task = workflow.tasks.first()
    fieldset_template = FieldsetTemplate.objects.create(
        template=template,
        account=account,
        name='Fieldset',
        order=1,
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
    assert service.instance is not None
    assert service.instance.workflow_id == workflow.id
    assert service.instance.task_id == task.id
    assert service.instance.kickoff is None


def test__create_instance__no_kickoff_no_task__ok(mocker):

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
        order=1,
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
    )

    # assert
    assert service.instance is not None
    assert service.instance.workflow_id == workflow.id
    assert service.instance.kickoff is None
    assert service.instance.task is None


# FieldSetService._create_fields


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
        order=1,
    )
    FieldTemplate.objects.create(
        account=account,
        fieldset=fieldset_template,
        name='Field 1',
        type=FieldType.NUMBER,
        order=1,
    )
    fieldset = FieldSet.objects.create(
        account=account,
        workflow=workflow,
        name='Fieldset',
        order=1,
    )
    service = FieldSetService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=fieldset,
    )

    # mock
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
        order=1,
    )
    field_template_1 = FieldTemplate.objects.create(
        account=account,
        fieldset=fieldset_template,
        name='Field 1',
        type=FieldType.NUMBER,
        order=1,
    )
    fieldset = FieldSet.objects.create(
        account=account,
        workflow=workflow,
        name='Fieldset',
        order=1,
    )
    service = FieldSetService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=fieldset,
    )
    fields_data = {field_template_1.api_name: '42'}

    # mock
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
        order=1,
    )
    FieldTemplate.objects.create(
        account=account,
        fieldset=fieldset_template,
        name='Field 1',
        type=FieldType.NUMBER,
        order=1,
    )
    fieldset = FieldSet.objects.create(
        account=account,
        workflow=workflow,
        name='Fieldset',
        order=1,
    )
    service = FieldSetService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=fieldset,
    )

    # mock
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


# FieldSetService._create_rules


def test__create_rules__with_template__ok(mocker):

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
        order=1,
    )
    rule_template = FieldsetTemplateRule.objects.create(
        account=account,
        fieldset=fieldset_template,
        type=FieldSetRuleType.SUM_EQUAL,
        value='100',
    )
    fieldset = FieldSet.objects.create(
        account=account,
        workflow=workflow,
        name='Fieldset',
        order=1,
    )
    service = FieldSetService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=fieldset,
    )

    # mock
    field_set_rule_service_init_mock = mocker.patch.object(
        FieldSetRuleService,
        attribute='__init__',
        return_value=None,
    )
    field_set_rule_service_create_mock = mocker.patch(
        'src.processes.services.workflows.fieldsets.fieldset_rule.'
        'FieldSetRuleService.create',
    )

    # act
    service._create_rules(instance_template=fieldset_template)

    # assert
    field_set_rule_service_init_mock.assert_called_once_with(
        user=user,
    )
    field_set_rule_service_create_mock.assert_called_once_with(
        instance_template=rule_template,
        fieldset=fieldset,
        skip_validation=None,
    )


# FieldSetService._create_related


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
        order=1,
    )
    service = FieldSetService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )

    # mock
    create_fields_mock = mocker.patch(
        'src.processes.services.workflows.fieldsets.fieldset.'
        'FieldSetService._create_fields',
    )
    create_rules_mock = mocker.patch(
        'src.processes.services.workflows.fieldsets.fieldset.'
        'FieldSetService._create_rules',
    )

    # act
    service._create_related(instance_template=fieldset_template)

    # assert
    create_fields_mock.assert_called_once_with(
        fieldset_template,
    )
    create_rules_mock.assert_called_once_with(
        fieldset_template,
    )


# FieldSetService.validate_rules


def test_validate_rules__with_rules__ok(mocker):

    """
    Call with rules
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user, tasks_count=1)
    workflow = create_test_workflow(user=user, template=template)
    fieldset = FieldSet.objects.create(
        account=account,
        workflow=workflow,
        name='Fieldset',
        order=1,
    )
    rule = FieldSetRule.objects.create(
        account=account,
        fieldset=fieldset,
        type=FieldSetRuleType.SUM_EQUAL,
        value='100',
    )
    service = FieldSetService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=fieldset,
    )

    # mock
    field_set_rule_service_init_mock = mocker.patch.object(
        FieldSetRuleService,
        attribute='__init__',
        return_value=None,
    )
    field_set_rule_service_validate_mock = mocker.patch(
        'src.processes.services.workflows.fieldsets.fieldset_rule.'
        'FieldSetRuleService.validate',
    )

    # act
    service.validate_rules()

    # assert
    field_set_rule_service_init_mock.assert_called_once_with(
        user=user,
        instance=rule,
    )
    field_set_rule_service_validate_mock.assert_called_once_with()
