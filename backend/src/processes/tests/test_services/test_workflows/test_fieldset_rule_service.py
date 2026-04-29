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


def test__create_instance__with_template__ok():

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


def test__validate_sum_equal__within_threshold__ok():

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
        rule_type=FieldSetRuleType.SUM_EQUAL,
        rule_value='100',
    )
    rule = fieldset.rules.first()
    field_1 = TaskField.objects.create(
        account=account,
        workflow=workflow,
        fieldset=fieldset,
        name='Field 1',
        type=FieldType.NUMBER,
        value='30',
        order=1,
    )
    field_1.rules.add(rule)
    field_2 = TaskField.objects.create(
        account=account,
        workflow=workflow,
        fieldset=fieldset,
        name='Field 2',
        type=FieldType.NUMBER,
        value='70',
        order=2,
    )
    field_2.rules.add(rule)
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


def test__validate_sum_equal__negative_value__ok():

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
        rule_type=FieldSetRuleType.SUM_EQUAL,
        rule_value='0',
    )
    rule = fieldset.rules.first()
    field_1 = TaskField.objects.create(
        account=account,
        workflow=workflow,
        fieldset=fieldset,
        name='Field 1',
        type=FieldType.NUMBER,
        value='30',
        order=1,
    )
    field_1.rules.add(rule)
    field_2 = TaskField.objects.create(
        account=account,
        workflow=workflow,
        fieldset=fieldset,
        name='Field 2',
        type=FieldType.NUMBER,
        value='-30',
        order=2,
    )
    field_2.rules.add(rule)
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


def test__validate_sum_equal__exceeds__raise_exception():

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
        rule_type=FieldSetRuleType.SUM_EQUAL,
        rule_value='100',
    )
    rule = fieldset.rules.first()
    field_1 = TaskField.objects.create(
        account=account,
        workflow=workflow,
        fieldset=fieldset,
        name='Field 1',
        type=FieldType.NUMBER,
        value='60',
        order=1,
    )
    field_1.rules.add(rule)
    field_2 = TaskField.objects.create(
        account=account,
        workflow=workflow,
        fieldset=fieldset,
        name='Field 2',
        type=FieldType.NUMBER,
        value='50',
        order=2,
    )
    field_2.rules.add(rule)
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


def test__validate_sum_equal__null_values__skip():

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
        rule_type=FieldSetRuleType.SUM_EQUAL,
        rule_value='100',
    )
    rule = fieldset.rules.first()
    field_1 = TaskField.objects.create(
        account=account,
        workflow=workflow,
        fieldset=fieldset,
        name='Field 1',
        type=FieldType.NUMBER,
        value='100',
        order=1,
    )
    field_1.rules.add(rule)
    field_2 = TaskField.objects.create(
        account=account,
        workflow=workflow,
        fieldset=fieldset,
        name='Field 2',
        type=FieldType.NUMBER,
        value='',
        order=2,
    )
    field_2.rules.add(rule)
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
        rule_type=FieldSetRuleType.SUM_EQUAL,
    )
    rule = fieldset.rules.first()
    service = FieldSetRuleService(
        instance=rule,
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )

    validate_sum_equal_mock = mocker.patch(
        'src.processes.services.workflows.fieldsets.fieldset_rule.'
        'FieldSetRuleService._validate_sum_equal',
    )
    kwargs = {'some': 'value'}

    # act
    service.validate(**kwargs)

    # assert
    validate_sum_equal_mock.assert_called_once_with(**kwargs)


def test_create__default_params__ok(mocker):

    """
    Call with default params
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    create_instance_mock = mocker.patch(
        'src.processes.services.workflows.fieldsets.fieldset_rule.'
        'FieldSetRuleService._create_instance',
    )
    create_related_mock = mocker.patch(
        'src.processes.services.workflows.fieldsets.fieldset_rule.'
        'FieldSetRuleService._create_related',
    )
    create_actions_mock = mocker.patch(
        'src.processes.services.workflows.fieldsets.fieldset_rule.'
        'FieldSetRuleService._create_actions',
    )
    validate_mock = mocker.patch(
        'src.processes.services.workflows.fieldsets.fieldset_rule.'
        'FieldSetRuleService.validate',
    )
    instance = mocker.Mock()
    service = FieldSetRuleService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=instance,
    )
    kwargs = {
        'some': 'value',
    }

    # act
    result = service.create(**kwargs)

    # assert
    create_instance_mock.assert_called_once_with(**kwargs)
    create_related_mock.assert_called_once_with(**kwargs)
    create_actions_mock.assert_called_once_with(**kwargs)
    validate_mock.assert_not_called()
    assert result is instance


def test_create__skip_validation_false__ok(mocker):

    """
    Call with skip_validation=False
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    create_instance_mock = mocker.patch(
        'src.processes.services.workflows.fieldsets.fieldset_rule.'
        'FieldSetRuleService._create_instance',
    )
    create_related_mock = mocker.patch(
        'src.processes.services.workflows.fieldsets.fieldset_rule.'
        'FieldSetRuleService._create_related',
    )
    create_actions_mock = mocker.patch(
        'src.processes.services.workflows.fieldsets.fieldset_rule.'
        'FieldSetRuleService._create_actions',
    )
    validate_mock = mocker.patch(
        'src.processes.services.workflows.fieldsets.fieldset_rule.'
        'FieldSetRuleService.validate',
    )
    instance = mocker.Mock()
    service = FieldSetRuleService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=instance,
    )
    kwargs = {
        'skip_validation': False,
    }

    # act
    result = service.create(**kwargs)

    # assert
    create_instance_mock.assert_called_once_with(**kwargs)
    create_related_mock.assert_called_once_with(**kwargs)
    create_actions_mock.assert_called_once_with(**kwargs)
    validate_mock.assert_called_once_with(**kwargs)
    assert result is instance


def test_partial_update__default_params__ok(mocker):

    """
    Call with default params
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    service = FieldSetRuleService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )

    result_mock = mocker.Mock()
    mock_super_partial_update = mocker.patch(
        'src.generics.base.service.'
        'BaseModelService.partial_update',
        return_value=result_mock,
    )
    validate_mock = mocker.patch(
        'src.processes.services.workflows.fieldsets.fieldset_rule.'
        'FieldSetRuleService.validate',
    )
    kwargs = {
        'value': 200,
    }

    # act
    result = service.partial_update(**kwargs)

    # assert
    assert result is result_mock
    mock_super_partial_update.assert_called_once_with(**kwargs)
    validate_mock.assert_called_once_with(**kwargs)
