import pytest
from src.authentication.enums import AuthTokenType
from src.processes.enums import (
    FieldSetRuleType,
    FieldType,
)
from src.processes.messages import fieldset as fs_messages
from src.processes.models.templates.fieldset import (
    FieldsetTemplate,
    FieldsetTemplateRule,
)
from src.processes.models.workflows.fieldset import (
    FieldSetRule,
)
from src.processes.models.workflows.fields import TaskField
from src.processes.services.exceptions import FieldsetServiceException
from src.processes.services.workflows.fieldsets.fieldset_rule import (
    FieldSetRuleService,
)
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_owner,
    create_test_template,
    create_test_workflow,
    create_test_fieldset,
)

pytestmark = pytest.mark.django_db


# FieldSetRuleService._create_instance


def test__create_instance__with_template__ok(mocker):

    """
    Call with instance_template and fieldset
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user, tasks_count=1)
    workflow = create_test_workflow(user=user, template=template)
    fieldset = create_test_fieldset(
        workflow=workflow,
        name='Fieldset',
        order=1,
    )
    fieldset_template = FieldsetTemplate.objects.create(
        template=template,
        account=account,
        name='Fieldset tmpl',
        order=1,
    )
    rule_template = FieldsetTemplateRule.objects.create(
        account=account,
        fieldset=fieldset_template,
        type=FieldSetRuleType.SUM_EQUAL,
        value='100',
    )
    service = FieldSetRuleService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )

    # act
    service._create_instance(
        instance_template=rule_template,
        fieldset=fieldset,
    )

    # assert
    assert service.instance is not None
    assert service.instance.fieldset_id == fieldset.id
    assert service.instance.type == FieldSetRuleType.SUM_EQUAL
    assert service.instance.value == '100'
    assert service.instance.api_name == rule_template.api_name
    assert service.instance.account_id == account.id


# FieldSetRuleService._validate_sum_equal


def test__validate_sum_equal__within_threshold__ok(mocker):

    """
    Total within threshold
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user, tasks_count=1)
    workflow = create_test_workflow(user=user, template=template)
    fieldset = create_test_fieldset(
        workflow=workflow,
        name='Fieldset',
        order=1,
    )
    TaskField.objects.create(
        account=account,
        workflow=workflow,
        fieldset=fieldset,
        name='Field 1',
        type=FieldType.NUMBER,
        value='30',
        order=1,
    )
    TaskField.objects.create(
        account=account,
        workflow=workflow,
        fieldset=fieldset,
        name='Field 2',
        type=FieldType.NUMBER,
        value='70',
        order=2,
    )
    rule = FieldSetRule.objects.create(
        account=account,
        fieldset=fieldset,
        type=FieldSetRuleType.SUM_EQUAL,
        value='100',
    )
    service = FieldSetRuleService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=rule,
    )

    # act
    result = service._validate_sum_equal(
        fieldset=fieldset,
        value='100',
    )

    # assert
    assert result is True


def test__validate_sum_equal__negative_value__ok(mocker):

    """
    Total within threshold
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user, tasks_count=1)
    workflow = create_test_workflow(user=user, template=template)
    fieldset = create_test_fieldset(
        workflow=workflow,
        name='Fieldset',
        order=1,
    )
    TaskField.objects.create(
        account=account,
        workflow=workflow,
        fieldset=fieldset,
        name='Field 1',
        type=FieldType.NUMBER,
        value='30',
        order=1,
    )
    TaskField.objects.create(
        account=account,
        workflow=workflow,
        fieldset=fieldset,
        name='Field 2',
        type=FieldType.NUMBER,
        value='-30',
        order=2,
    )
    rule = FieldSetRule.objects.create(
        account=account,
        fieldset=fieldset,
        type=FieldSetRuleType.SUM_EQUAL,
        value='30',
    )
    service = FieldSetRuleService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=rule,
    )

    # act
    result = service._validate_sum_equal(
        fieldset=fieldset,
        value='0',
    )

    # assert
    assert result is True


def test__validate_sum_equal__exceeds__raise_exception(mocker):

    """
    Total exceeds threshold → exception
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user, tasks_count=1)
    workflow = create_test_workflow(user=user, template=template)
    fieldset = create_test_fieldset(
        workflow=workflow,
        name='Fieldset',
        order=1,
    )
    TaskField.objects.create(
        account=account,
        workflow=workflow,
        fieldset=fieldset,
        name='Field 1',
        type=FieldType.NUMBER,
        value='60',
        order=1,
    )
    TaskField.objects.create(
        account=account,
        workflow=workflow,
        fieldset=fieldset,
        name='Field 2',
        type=FieldType.NUMBER,
        value='50',
        order=2,
    )
    rule = FieldSetRule.objects.create(
        account=account,
        fieldset=fieldset,
        type=FieldSetRuleType.SUM_EQUAL,
        value='100',
    )
    service = FieldSetRuleService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=rule,
    )

    # act
    with pytest.raises(FieldsetServiceException) as ex:
        service._validate_sum_equal(
            fieldset=fieldset,
            value='100',
        )

    # assert
    assert ex.value.message == fs_messages.MSG_FS_0002(100)


def test__validate_sum_equal__null_values__skip(mocker):

    """
    Fields with null values skipped
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user, tasks_count=1)
    workflow = create_test_workflow(user=user, template=template)
    fieldset = create_test_fieldset(
        workflow=workflow,
        name='Fieldset',
        order=1,
    )
    TaskField.objects.create(
        account=account,
        workflow=workflow,
        fieldset=fieldset,
        name='Field 1',
        type=FieldType.NUMBER,
        value='100',
        order=1,
    )
    TaskField.objects.create(
        account=account,
        workflow=workflow,
        fieldset=fieldset,
        name='Field 2',
        type=FieldType.NUMBER,
        value='',
        order=2,
    )
    rule = FieldSetRule.objects.create(
        account=account,
        fieldset=fieldset,
        type=FieldSetRuleType.SUM_EQUAL,
        value='100',
    )
    service = FieldSetRuleService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=rule,
    )

    # act
    result = service._validate_sum_equal(
        fieldset=fieldset,
        value='100',
    )

    # assert - no exception raised, null/empty fields are skipped
    assert result is True


# FieldSetRuleService.validate


def test_validate__ok(mocker):

    """
    Known type, validator exists
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    workflow = create_test_workflow(user, tasks_count=1)
    fieldset = create_test_fieldset(
        workflow=workflow,
        kickoff=workflow.kickoff_instance,
    )
    service = FieldSetRuleService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )

    # mock
    validate_sum_equal_mock = mocker.patch(
        'src.processes.services.workflows.fieldsets.fieldset_rule.'
        'FieldSetRuleService._validate_sum_equal',
    )

    # act
    service.validate(
        type=FieldSetRuleType.SUM_EQUAL,
        fieldset=fieldset,
        value='10',
    )

    # assert
    validate_sum_equal_mock.assert_called_once_with(
        fieldset=fieldset,
        value='10',
    )


# FieldSetRuleService.create


def test_create__skip_val_false__ok(mocker):

    """
    skip_validation is False
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user, tasks_count=1)
    workflow = create_test_workflow(user=user, template=template)
    fieldset = create_test_fieldset(
        workflow=workflow,
        name='Fieldset',
        order=1,
    )
    fieldset_template = FieldsetTemplate.objects.create(
        template=template,
        account=account,
        name='Fieldset tmpl',
        order=1,
    )
    rule_template = FieldsetTemplateRule.objects.create(
        account=account,
        fieldset=fieldset_template,
        type=FieldSetRuleType.SUM_EQUAL,
        value='100',
    )
    service = FieldSetRuleService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )

    # mock
    validate_mock = mocker.patch(
        'src.processes.services.workflows.fieldsets.fieldset_rule.'
        'FieldSetRuleService.validate',
    )

    # act
    result = service.create(
        instance_template=rule_template,
        fieldset=fieldset,
        skip_validation=False,
    )

    # assert
    assert result.type == FieldSetRuleType.SUM_EQUAL
    assert result.value == '100'
    assert result.fieldset_id == fieldset.id
    validate_mock.assert_called_once_with(
        instance_template=rule_template,
        fieldset=fieldset,
        skip_validation=False,
    )


def test_create__skip_val_not_false__ok(mocker):

    """
    skip_validation is not False
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user, tasks_count=1)
    workflow = create_test_workflow(user=user, template=template)
    fieldset = create_test_fieldset(
        workflow=workflow,
        name='Fieldset',
        order=1,
    )
    fieldset_template = FieldsetTemplate.objects.create(
        template=template,
        account=account,
        name='Fieldset tmpl',
        order=1,
    )
    rule_template = FieldsetTemplateRule.objects.create(
        account=account,
        fieldset=fieldset_template,
        type=FieldSetRuleType.SUM_EQUAL,
        value='100',
    )
    service = FieldSetRuleService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )

    # mock
    validate_mock = mocker.patch(
        'src.processes.services.workflows.fieldsets.fieldset_rule.'
        'FieldSetRuleService.validate',
    )

    # act
    result = service.create(
        instance_template=rule_template,
        fieldset=fieldset,
        skip_validation=None,
    )

    # assert
    assert result.type == FieldSetRuleType.SUM_EQUAL
    assert result.fieldset_id == fieldset.id
    validate_mock.assert_not_called()


# FieldSetRuleService.partial_update


def test_partial_update__valid_data__ok(mocker):

    """
    Call with valid data
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user, tasks_count=1)
    workflow = create_test_workflow(user=user, template=template)
    fieldset = create_test_fieldset(
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
    service = FieldSetRuleService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=rule,
    )

    # mock
    validate_mock = mocker.patch(
        'src.processes.services.workflows.fieldsets.fieldset_rule.'
        'FieldSetRuleService.validate',
    )

    # act
    result = service.partial_update(value='200')

    # assert
    assert result.value == '200'
    validate_mock.assert_called_once_with(
        value='200',
    )
