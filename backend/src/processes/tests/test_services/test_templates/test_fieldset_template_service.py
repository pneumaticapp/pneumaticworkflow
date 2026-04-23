import pytest
from src.authentication.enums import AuthTokenType
from src.processes.enums import (
    FieldSetLayout,
    FieldSetRuleType,
    LabelPosition,
)
from src.processes.messages import fieldset as fs_messages
from src.processes.models.templates.fieldset import (
    FieldsetTemplate,
    FieldsetTemplateRule,
)
from src.processes.models.templates.fields import FieldTemplate
from src.processes.services.exceptions import (
    FieldsetTemplateInUseException,
)
from src.processes.services.templates.field_template import (
    FieldTemplateService,
)
from src.processes.services.templates.fieldsets.fieldset import (
    FieldSetTemplateService,
)
from src.processes.services.templates.fieldsets.fieldset_rule import (
    FieldsetTemplateRuleService,
)
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_owner,
    create_test_template,
    create_test_fieldset_template,
)

pytestmark = pytest.mark.django_db


def test__create_instance__default_params__ok():

    """
    Call with default parameters
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user, tasks_count=1)
    service = FieldSetTemplateService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    name = 'Test fieldset'
    order = 1

    # act
    service._create_instance(
        name=name,
        order=order,
        template_id=template.id,
    )

    # assert
    assert service.instance is not None
    assert service.instance.name == name
    assert service.instance.order == order
    assert service.instance.template_id == template.id
    assert service.instance.account_id == account.id
    assert service.instance.description == ''
    assert service.instance.label_position == LabelPosition.TOP
    assert service.instance.layout == FieldSetLayout.VERTICAL


def test__create_instance__all_params__ok():

    """
    Call with all parameters
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user, tasks_count=1)
    service = FieldSetTemplateService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    name = 'Test fieldset'
    order = 2
    description = 'Test description'
    label_position = LabelPosition.LEFT
    layout = FieldSetLayout.HORIZONTAL

    # act
    service._create_instance(
        name=name,
        order=order,
        template_id=template.id,
        description=description,
        label_position=label_position,
        layout=layout,
    )

    # assert
    assert service.instance.name == name
    assert service.instance.order == order
    assert service.instance.template_id == template.id
    assert service.instance.description == description
    assert service.instance.label_position == label_position
    assert service.instance.layout == layout


def test__create_instance__with_kickoff_id__ok():

    """Persist kickoff_id when creating a fieldset template."""

    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user, tasks_count=1)
    kickoff = template.kickoff_instance
    service = FieldSetTemplateService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )

    service._create_instance(
        name='Kickoff fieldset',
        order=1,
        template_id=template.id,
        kickoff_id=kickoff.id,
    )

    assert service.instance.kickoff_id == kickoff.id
    assert service.instance.task_id is None


def test__create_instance__with_task_id__ok():

    """Persist task_id when creating a fieldset template."""

    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user, tasks_count=1)
    task = template.tasks.first()
    service = FieldSetTemplateService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )

    service._create_instance(
        name='Task fieldset',
        order=1,
        template_id=template.id,
        task_id=task.id,
    )

    assert service.instance.task_id == task.id
    assert service.instance.kickoff_id is None


def test__create_fields__with_data__ok(mocker):

    """
    Call with fields data
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user, tasks_count=1)
    fieldset = FieldsetTemplate.objects.create(
        template=template,
        account=account,
        name='Fieldset',
        order=1,
    )
    service = FieldSetTemplateService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=fieldset,
    )
    fields_data = [
        {'name': 'Field 1', 'type': 'string', 'order': 1},
        {'name': 'Field 2', 'type': 'number', 'order': 2},
    ]

    # mock
    field_template_service_init_mock = mocker.patch.object(
        FieldTemplateService,
        attribute='__init__',
        return_value=None,
    )
    field_template_service_create_mock = mocker.patch(
        'src.processes.services.templates.field_template.'
        'FieldTemplateService.create',
    )

    # act
    service._create_fields(fields_data=fields_data)

    # assert
    assert field_template_service_init_mock.call_count == 2
    assert field_template_service_create_mock.call_count == 2
    field_template_service_create_mock.assert_has_calls(
        [
            mocker.call(
                fieldset_id=fieldset.id,
                template_id=template.id,
                name='Field 1',
                type='string',
                order=1,
            ),
            mocker.call(
                fieldset_id=fieldset.id,
                template_id=template.id,
                name='Field 2',
                type='number',
                order=2,
            ),
        ],
        any_order=True,
    )


def test_create_rules__with_data__ok(mocker):

    """
    Call with rules data
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user, tasks_count=1)
    fieldset = FieldsetTemplate.objects.create(
        template=template,
        account=account,
        name='Fieldset',
        order=1,
    )
    service = FieldSetTemplateService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=fieldset,
    )
    rules_data = [
        {'type': FieldSetRuleType.SUM_EQUAL, 'value': '100'},
    ]

    # mock
    fieldset_template_rule_service_init_mock = mocker.patch.object(
        FieldsetTemplateRuleService,
        attribute='__init__',
        return_value=None,
    )
    fieldset_template_rule_service_create_mock = mocker.patch(
        'src.processes.services.templates.fieldsets.fieldset_rule.'
        'FieldsetTemplateRuleService.create',
    )

    # act
    service.create_rules(rules_data=rules_data)

    # assert
    fieldset_template_rule_service_init_mock.assert_called_once_with(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    fieldset_template_rule_service_create_mock.assert_called_once_with(
        fieldset_id=fieldset.id,
        type=FieldSetRuleType.SUM_EQUAL,
        value='100',
    )


def test__create_related__default_params__ok(mocker):

    """
    Call with default parameters (no rules, no fields)
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    service = FieldSetTemplateService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )

    # mock
    create_rules_mock = mocker.patch(
        'src.processes.services.templates.fieldsets.fieldset.'
        'FieldSetTemplateService.create_rules',
    )
    create_fields_mock = mocker.patch(
        'src.processes.services.templates.fieldsets.fieldset.'
        'FieldSetTemplateService._create_fields',
    )

    # act
    service._create_related()

    # assert
    create_rules_mock.assert_not_called()
    create_fields_mock.assert_not_called()


def test__create_related__rules_provided__ok(mocker):

    """
    Rules provided
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    service = FieldSetTemplateService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    rules = [{'type': FieldSetRuleType.SUM_EQUAL, 'value': '100'}]

    # mock
    create_rules_mock = mocker.patch(
        'src.processes.services.templates.fieldsets.fieldset.'
        'FieldSetTemplateService.create_rules',
    )
    create_fields_mock = mocker.patch(
        'src.processes.services.templates.fieldsets.fieldset.'
        'FieldSetTemplateService._create_fields',
    )

    # act
    service._create_related(rules=rules)

    # assert
    create_rules_mock.assert_called_once_with(rules_data=rules)
    create_fields_mock.assert_not_called()


def test__create_related__fields_provided__ok(mocker):

    """
    Fields provided
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    service = FieldSetTemplateService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    fields = [{'name': 'Field 1', 'type': 'string', 'order': 1}]

    # mock
    create_rules_mock = mocker.patch(
        'src.processes.services.templates.fieldsets.fieldset.'
        'FieldSetTemplateService.create_rules',
    )
    create_fields_mock = mocker.patch(
        'src.processes.services.templates.fieldsets.fieldset.'
        'FieldSetTemplateService._create_fields',
    )

    # act
    service._create_related(fields=fields)

    # assert
    create_rules_mock.assert_not_called()
    create_fields_mock.assert_called_once_with(fields_data=fields)


def test__create_related__both_provided__ok(mocker):

    """
    Both rules and fields provided
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    service = FieldSetTemplateService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    rules = [{'type': FieldSetRuleType.SUM_EQUAL, 'value': '100'}]
    fields = [{'name': 'Field 1', 'type': 'string', 'order': 1}]

    # mock
    create_rules_mock = mocker.patch(
        'src.processes.services.templates.fieldsets.fieldset.'
        'FieldSetTemplateService.create_rules',
    )
    create_fields_mock = mocker.patch(
        'src.processes.services.templates.fieldsets.fieldset.'
        'FieldSetTemplateService._create_fields',
    )

    # act
    service._create_related(rules=rules, fields=fields)

    # assert
    create_rules_mock.assert_called_once_with(rules_data=rules)
    create_fields_mock.assert_called_once_with(fields_data=fields)


def test__update_fields__existing_field__ok(mocker):

    """
    Update existing field
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user, tasks_count=1)
    fieldset = FieldsetTemplate.objects.create(
        template=template,
        account=account,
        name='Fieldset',
        order=1,
    )
    field_1 = FieldTemplate.objects.create(
        account=account,
        fieldset=fieldset,
        name='Field 1',
        type='string',
        order=1,
    )
    service = FieldSetTemplateService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=fieldset,
    )
    fields_data = [{'api_name': field_1.api_name, 'name': 'Updated Field 1'}]

    # mock
    field_template_service_init_mock = mocker.patch.object(
        FieldTemplateService,
        attribute='__init__',
        return_value=None,
    )
    field_template_service_partial_update_mock = mocker.patch(
        'src.processes.services.templates.field_template.'
        'FieldTemplateService.partial_update',
    )
    field_template_service_create_mock = mocker.patch(
        'src.processes.services.templates.field_template.'
        'FieldTemplateService.create',
    )

    # act
    service._update_fields(fields_data=fields_data)

    # assert
    field_template_service_init_mock.assert_called_once_with(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=field_1,
    )
    field_template_service_partial_update_mock.assert_called_once_with(
        name='Updated Field 1',
        force_save=True,
    )
    field_template_service_create_mock.assert_not_called()


def test__update_fields__new_field__ok(mocker):

    """
    Create new field
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user, tasks_count=1)

    fieldset = create_test_fieldset_template(
        account=account,
        template=template,
        kickoff=template.kickoff_instance,
    )
    service = FieldSetTemplateService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=fieldset,
    )
    fields_data = [
        {'name': 'New Field', 'type': 'number', 'order': 1},
    ]

    # mock
    create_return = mocker.Mock()
    create_return.api_name = 'field_api_name'
    field_template_service_init_mock = mocker.patch.object(
        FieldTemplateService,
        attribute='__init__',
        return_value=None,
    )
    field_template_service_create_mock = mocker.patch(
        'src.processes.services.templates.field_template.'
        'FieldTemplateService.create',
        return_value=create_return,
    )
    field_template_service_partial_update_mock = mocker.patch(
        'src.processes.services.templates.field_template.'
        'FieldTemplateService.partial_update',
    )

    # act
    service._update_fields(fields_data=fields_data)

    # assert
    field_template_service_init_mock.assert_called_once_with(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    field_template_service_create_mock.assert_called_once_with(
        fieldset_id=fieldset.id,
        template_id=template.id,
        name='New Field',
        type='number',
        order=1,
    )
    field_template_service_partial_update_mock.assert_not_called()


def test__update_fields__orphan_fields__deleted(mocker):

    """
    Orphan fields deleted
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user, tasks_count=1)
    fieldset = FieldsetTemplate.objects.create(
        template=template,
        account=account,
        name='Fieldset',
        order=1,
    )
    field_1 = FieldTemplate.objects.create(
        account=account,
        fieldset=fieldset,
        name='Field 1',
        type='string',
        order=1,
    )
    field_2 = FieldTemplate.objects.create(
        account=account,
        fieldset=fieldset,
        name='Field 2',
        type='string',
        order=2,
    )
    service = FieldSetTemplateService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=fieldset,
    )
    fields_data = [{'api_name': field_1.api_name, 'name': 'Updated Field 1'}]

    # mock
    field_template_service_init_mock = mocker.patch.object(
        FieldTemplateService,
        attribute='__init__',
        return_value=None,
    )
    field_template_service_update_mock = mocker.patch(
        'src.processes.services.templates.field_template.'
        'FieldTemplateService.partial_update',
    )

    # act
    service._update_fields(fields_data=fields_data)

    # assert
    field_template_service_init_mock.assert_called_once()
    field_template_service_update_mock.assert_called_once()
    assert not FieldTemplate.objects.filter(
        id=field_2.id,
    ).exists()
    assert FieldTemplate.objects.filter(id=field_1.id).exists()


def test__validate_rules__with_rules__ok(mocker):

    """
    Call with rules
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user, tasks_count=1)
    fieldset = FieldsetTemplate.objects.create(
        template=template,
        account=account,
        name='Fieldset',
        order=1,
    )
    rule_1 = FieldsetTemplateRule.objects.create(
        account=account,
        fieldset=fieldset,
        type=FieldSetRuleType.SUM_EQUAL,
        value='100',
    )
    service = FieldSetTemplateService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=fieldset,
    )

    # mock
    fieldset_template_rule_service_init_mock = mocker.patch.object(
        FieldsetTemplateRuleService,
        attribute='__init__',
        return_value=None,
    )
    fieldset_template_rule_service_validate_mock = mocker.patch(
        'src.processes.services.templates.fieldsets.fieldset_rule.'
        'FieldsetTemplateRuleService._validate',
    )

    # act
    service._validate_rules()

    # assert
    fieldset_template_rule_service_init_mock.assert_called_once_with(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=rule_1,
    )
    fieldset_template_rule_service_validate_mock.assert_called_once_with()


def test_update_rules__existing_rule__ok(mocker):

    """
    Update existing rule
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user, tasks_count=1)
    fieldset = FieldsetTemplate.objects.create(
        template=template,
        account=account,
        name='Fieldset',
        order=1,
    )
    rule_1 = FieldsetTemplateRule.objects.create(
        account=account,
        fieldset=fieldset,
        type=FieldSetRuleType.SUM_EQUAL,
        value='100',
    )
    service = FieldSetTemplateService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=fieldset,
    )
    rules_data = [{'id': rule_1.id, 'value': '200'}]

    # mock
    fieldset_template_rule_service_init_mock = mocker.patch.object(
        FieldsetTemplateRuleService,
        attribute='__init__',
        return_value=None,
    )
    fieldset_template_rule_service_partial_update_mock = mocker.patch(
        'src.processes.services.templates.fieldsets.fieldset_rule.'
        'FieldsetTemplateRuleService.partial_update',
    )
    fieldset_template_rule_service_create_mock = mocker.patch(
        'src.processes.services.templates.fieldsets.fieldset_rule.'
        'FieldsetTemplateRuleService.create',
    )

    # act
    service.update_rules(rules_data=rules_data)

    # assert
    fieldset_template_rule_service_init_mock.assert_called_once_with(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=rule_1,
    )
    fs_rule_update_mock = (
        fieldset_template_rule_service_partial_update_mock
    )
    fs_rule_update_mock.assert_called_once_with(
        value='200',
        force_save=True,
    )
    fieldset_template_rule_service_create_mock.assert_not_called()


def test_update_rules__new_rule__ok(mocker):

    """
    Create new rule
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user, tasks_count=1)
    fieldset = FieldsetTemplate.objects.create(
        template=template,
        account=account,
        name='Fieldset',
        order=1,
    )
    service = FieldSetTemplateService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=fieldset,
    )
    rules_data = [
        {'type': FieldSetRuleType.SUM_EQUAL, 'value': '100'},
    ]

    # mock
    create_return = mocker.Mock()
    create_return.id = 999
    fs_rule_init_mock = mocker.patch.object(
        FieldsetTemplateRuleService,
        attribute='__init__',
        return_value=None,
    )
    fs_rule_create_mock = mocker.patch(
        'src.processes.services.templates.fieldsets.fieldset_rule.'
        'FieldsetTemplateRuleService.create',
        return_value=create_return,
    )
    fs_rule_update_mock = mocker.patch(
        'src.processes.services.templates.fieldsets.fieldset_rule.'
        'FieldsetTemplateRuleService.partial_update',
    )

    # act
    service.update_rules(rules_data=rules_data)

    # assert
    fs_rule_init_mock.assert_called_once_with(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    fs_rule_create_mock.assert_called_once_with(
        fieldset_id=fieldset.id,
        type=FieldSetRuleType.SUM_EQUAL,
        value='100',
    )
    fs_rule_update_mock.assert_not_called()


def test_update_rules__orphan_rules__deleted(mocker):

    """
    Orphan rules deleted
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user, tasks_count=1)
    fieldset = FieldsetTemplate.objects.create(
        template=template,
        account=account,
        name='Fieldset',
        order=1,
    )
    rule_1 = FieldsetTemplateRule.objects.create(
        account=account,
        fieldset=fieldset,
        type=FieldSetRuleType.SUM_EQUAL,
        value='100',
    )
    rule_2 = FieldsetTemplateRule.objects.create(
        account=account,
        fieldset=fieldset,
        type=FieldSetRuleType.SUM_EQUAL,
        value='200',
    )
    service = FieldSetTemplateService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=fieldset,
    )
    rules_data = [{'id': rule_1.id, 'value': '150'}]

    # mock
    fs_rule_init_mock = mocker.patch.object(
        FieldsetTemplateRuleService,
        attribute='__init__',
        return_value=None,
    )
    fs_rule_update_mock = mocker.patch(
        'src.processes.services.templates.fieldsets.fieldset_rule.'
        'FieldsetTemplateRuleService.partial_update',
    )

    # act
    service.update_rules(rules_data=rules_data)

    # assert
    fs_rule_init_mock.assert_called_once()
    fs_rule_update_mock.assert_called_once()
    assert not FieldsetTemplateRule.objects.filter(
        id=rule_2.id,
    ).exists()
    assert FieldsetTemplateRule.objects.filter(
        id=rule_1.id,
    ).exists()


def test_create__bind_kickoff__ok(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    template = create_test_template(user=owner, tasks_count=1)
    kickoff = template.kickoff_instance
    data = {
        "template_id": template.id,
        "name": "Test Fieldset",
        "fields": [],
        "rules": [],
    }

    mock_create_instance = mocker.patch(
        'src.processes.services.templates.fieldsets.fieldset.'
        'FieldSetTemplateService._create_instance',
    )
    mock_create_related = mocker.patch(
        'src.processes.services.templates.fieldsets.fieldset.'
        'FieldSetTemplateService._create_related',
    )
    mock_create_actions = mocker.patch(
        'src.processes.services.templates.fieldsets.fieldset.'
        'FieldSetTemplateService._create_actions',
    )
    service = FieldSetTemplateService(user=owner)

    # act
    service.create(**data)

    # assert
    mock_create_instance.assert_called_once_with(**data, kickoff_id=kickoff.id)
    mock_create_related.assert_called_once_with(**data, kickoff_id=kickoff.id)
    mock_create_actions.assert_called_once_with(**data, kickoff_id=kickoff.id)


def test_create_with_task_bind_task_ok(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    template = create_test_template(user=owner, tasks_count=1)
    task = template.tasks.get(number=1)
    data = {
        "template_id": template.id,
        "name": "Test Fieldset",
        "fields": [],
        "rules": [],
        "task_id": task.id,
    }

    mock_create_instance = mocker.patch(
        'src.processes.services.templates.fieldsets.fieldset.'
        'FieldSetTemplateService._create_instance',
    )
    mock_create_related = mocker.patch(
        'src.processes.services.templates.fieldsets.fieldset.'
        'FieldSetTemplateService._create_related',
    )
    mock_create_actions = mocker.patch(
        'src.processes.services.templates.fieldsets.fieldset.'
        'FieldSetTemplateService._create_actions',
    )
    service = FieldSetTemplateService(user=owner)

    # act
    service.create(**data)

    # assert
    mock_create_instance.assert_called_once_with(**data)
    mock_create_related.assert_called_once_with(**data)
    mock_create_actions.assert_called_once_with(**data)


def test_partial_update_name__ok(mocker):

    """Call `partial_update` with default parameters"""

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    template = create_test_template(user=owner, tasks_count=1)
    task = template.tasks.get(number=1)
    fieldset = create_test_fieldset_template(
        account=account,
        template=template,
        task=task,
    )
    mock_update_fields = mocker.patch(
        'src.processes.services.templates.fieldsets.fieldset.'
        'FieldSetTemplateService._update_fields',
    )
    mock_update_rules = mocker.patch(
        'src.processes.services.templates.fieldsets.fieldset.'
        'FieldSetTemplateService.update_rules',
    )
    mock_validate_rules = mocker.patch(
        'src.processes.services.templates.fieldsets.fieldset.'
        'FieldSetTemplateService._validate_rules',
    )
    service = FieldSetTemplateService(instance=fieldset, user=owner)
    data = {"name": 'Updated Name'}

    # act
    result = service.partial_update(**data)

    # assert
    assert result.name == data['name']
    mock_update_fields.assert_not_called()
    mock_update_rules.assert_not_called()
    mock_validate_rules.assert_called_once_with()


def test_partial_update_unbind_task_ok(mocker):

    """Test handling of `task_id` being set to None (unbind from task)"""

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    template = create_test_template(user=owner, tasks_count=1)
    task = template.tasks.get(number=1)
    fieldset = create_test_fieldset_template(
        account=account,
        template=template,
        task=task,
    )

    mock_update_fields = mocker.patch(
        'src.processes.services.templates.fieldsets.fieldset.'
        'FieldSetTemplateService._update_fields',
    )
    mock_update_rules = mocker.patch(
        'src.processes.services.templates.fieldsets.fieldset.'
        'FieldSetTemplateService.update_rules',
    )
    mock_validate_rules = mocker.patch(
        'src.processes.services.templates.fieldsets.fieldset.'
        'FieldSetTemplateService._validate_rules',
    )
    service = FieldSetTemplateService(instance=fieldset, user=owner)
    data = {"task_id": None}

    # act
    result = service.partial_update(**data)

    # assert
    fieldset.refresh_from_db()
    assert result is fieldset
    assert fieldset.task is None
    assert fieldset.kickoff == template.kickoff_instance
    mock_update_fields.assert_not_called()
    mock_update_rules.assert_not_called()
    mock_validate_rules.assert_called_once_with()


def test_partial_update_bind_task_ok(mocker):
    """Test handling of `task_id` being provided (bind to task)"""

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    template = create_test_template(user=owner, tasks_count=1)
    task = template.tasks.get(number=1)
    fieldset = create_test_fieldset_template(
        account=account,
        template=template,
        kickoff=template.kickoff_instance,
    )

    mock_update_fields = mocker.patch(
        'src.processes.services.templates.fieldsets.fieldset.'
        'FieldSetTemplateService._update_fields',
    )
    mock_update_rules = mocker.patch(
        'src.processes.services.templates.fieldsets.fieldset.'
        'FieldSetTemplateService.update_rules',
    )
    mock_validate_rules = mocker.patch(
        'src.processes.services.templates.fieldsets.fieldset.'
        'FieldSetTemplateService._validate_rules',
    )
    service = FieldSetTemplateService(instance=fieldset, user=owner)
    data = {"task_id": task.id}

    # act
    result = service.partial_update(**data)

    # assert
    fieldset.refresh_from_db()
    assert result is fieldset
    assert fieldset.task == task
    assert fieldset.kickoff is None
    mock_update_fields.assert_not_called()
    mock_update_rules.assert_not_called()
    mock_validate_rules.assert_called_once_with()


def test_partial_update_fields_ok(mocker):
    """Verify fields update logic for existing and new fields"""

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    template = create_test_template(user=owner, tasks_count=1)
    task = template.tasks.get(number=1)
    fieldset = create_test_fieldset_template(
        account=account,
        template=template,
        task=task,
    )
    service = FieldSetTemplateService(user=owner, instance=fieldset)

    mock_update_fields = mocker.patch(
        'src.processes.services.templates.fieldsets.fieldset.'
        'FieldSetTemplateService._update_fields',
    )
    mock_update_rules = mocker.patch(
        'src.processes.services.templates.fieldsets.fieldset.'
        'FieldSetTemplateService.update_rules',
    )
    mock_validate_rules = mocker.patch(
        'src.processes.services.templates.fieldsets.fieldset.'
        'FieldSetTemplateService._validate_rules',
    )
    mock_super_partial_update = mocker.patch(
        'src.generics.base.service.'
        'BaseModelService.partial_update',
    )
    data = {
        "fields": [
            {"api_name": "field_1", "value": "val"},
        ],
    }

    # act
    service.partial_update(**data)

    # assert
    mock_super_partial_update.assert_not_called()
    mock_update_fields.assert_called_once_with(fields_data=data['fields'])
    mock_update_rules.assert_not_called()
    mock_validate_rules.assert_called_once_with()


def test_partial_update__rules__ok(mocker):
    """Verify rules update logic for existing and new rules"""

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    template = create_test_template(user=owner, tasks_count=1)
    task = template.tasks.get(number=1)
    fieldset = create_test_fieldset_template(
        account=account,
        template=template,
        task=task,
    )

    mock_super_partial_update = mocker.patch(
        'src.generics.base.service.'
        'BaseModelService.partial_update',
    )
    mock_update_fields = mocker.patch(
        'src.processes.services.templates.fieldsets.fieldset.'
        'FieldSetTemplateService._update_fields',
    )
    mock_update_rules = mocker.patch(
        'src.processes.services.templates.fieldsets.fieldset.'
        'FieldSetTemplateService.update_rules',
    )
    mock_validate_rules = mocker.patch(
        'src.processes.services.templates.fieldsets.fieldset.'
        'FieldSetTemplateService._validate_rules',
    )
    service = FieldSetTemplateService(user=owner, instance=fieldset)
    data = {
        'rules': [
            {"api_name": "rule_1", "condition": "eq"},
        ],
    }

    # act
    result = service.partial_update(**data)

    # assert
    assert result is fieldset
    mock_super_partial_update.assert_not_called()
    mock_update_fields.assert_not_called()
    mock_update_rules.assert_called_once_with(rules_data=data['rules'])
    mock_validate_rules.assert_called_once_with()


def test_delete__not_in_use__ok():

    """
    Not in use → deleted
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user, tasks_count=1)
    fieldset = FieldsetTemplate.objects.create(
        template=template,
        account=account,
        name='Fieldset',
        order=1,
    )
    service = FieldSetTemplateService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=fieldset,
    )

    # act
    service.delete()

    # assert
    assert not FieldsetTemplate.objects.filter(id=fieldset.id).exists()


def test_delete__used_by_kickoff__raise_exception():

    """
    In use by kickoff → exception
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user, tasks_count=1)
    kickoff = template.kickoff_instance
    fieldset = FieldsetTemplate.objects.create(
        template=template,
        account=account,
        name='Fieldset',
        kickoff=kickoff,
        order=1,
    )
    service = FieldSetTemplateService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=fieldset,
    )

    # act
    with pytest.raises(FieldsetTemplateInUseException) as ex:
        service.delete()

    # assert
    assert ex.value.message == fs_messages.MSG_FS_0001
    assert FieldsetTemplate.objects.filter(id=fieldset.id).exists()


def test_delete__used_by_task__raise_exception():

    """
    In use by task → exception
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user, tasks_count=1)
    task_template = template.tasks.first()
    fieldset = FieldsetTemplate.objects.create(
        template=template,
        account=account,
        task=task_template,
        name='Fieldset',
        order=1,
    )
    service = FieldSetTemplateService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=fieldset,
    )

    # act
    with pytest.raises(FieldsetTemplateInUseException) as ex:
        service.delete()

    # assert
    assert ex.value.message == fs_messages.MSG_FS_0001
    assert FieldsetTemplate.objects.filter(id=fieldset.id).exists()
