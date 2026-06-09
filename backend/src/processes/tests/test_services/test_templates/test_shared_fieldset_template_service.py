import pytest
from src.authentication.enums import AuthTokenType
from src.processes.enums import (
    FieldSetLayout,
    FieldSetRuleType,
    LabelPosition,
)
from src.processes.models.templates.shared_fieldset import SharedFieldSetTemplate
from src.processes.models.templates.fields import FieldTemplate
from src.processes.services.templates.field_template import (
    FieldTemplateService,
)
from src.processes.services.templates.fieldsets.fieldset import (
    FieldSetTemplateService
)
from src.processes.services.templates.fieldsets.fieldset_rule import (
    FieldsetTemplateRuleService,
)
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_owner,
)

pytestmark = pytest.mark.django_db


def test__create_instance__default_params__ok():

    """
    Call with default parameters
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    service = FieldSetTemplateService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    name = 'Test shared fieldset'

    # act
    service._create_instance(name=name)

    # assert
    assert service.instance is not None
    assert service.instance.name == name
    assert service.instance.api_name
    assert service.instance.order == 0
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
    service = FieldSetTemplateService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    name = 'Test shared fieldset'
    description = 'Test description'
    label_position = LabelPosition.LEFT
    layout = FieldSetLayout.HORIZONTAL
    api_name = 'shared-fs-1'
    order = 3

    # act
    service._create_instance(
        name=name,
        order=order,
        description=description,
        label_position=label_position,
        layout=layout,
        api_name=api_name,
    )

    # assert
    assert service.instance.name == name
    assert service.instance.order == order
    assert service.instance.description == description
    assert service.instance.label_position == label_position
    assert service.instance.layout == layout
    assert service.instance.api_name == api_name


def test__create_fields__with_data__ok(mocker):

    """
    Call with fields data
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    fieldset = SharedFieldSetTemplate.objects.create(
        account=account,
        name='Shared Fieldset',
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
                name='Field 1',
                type='string',
                order=1,
            ),
            mocker.call(
                fieldset_id=fieldset.id,
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
    fieldset = SharedFieldSetTemplate.objects.create(
        account=account,
        name='Shared Fieldset',
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
        'src.processes.services.templates.fieldsets.shared_fieldset.'
        'FieldSetTemplateService.create_rules',
    )
    create_fields_mock = mocker.patch(
        'src.processes.services.templates.fieldsets.shared_fieldset.'
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
        'src.processes.services.templates.fieldsets.shared_fieldset.'
        'FieldSetTemplateService.create_rules',
    )
    create_fields_mock = mocker.patch(
        'src.processes.services.templates.fieldsets.shared_fieldset.'
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
        'src.processes.services.templates.fieldsets.shared_fieldset.'
        'FieldSetTemplateService.create_rules',
    )
    create_fields_mock = mocker.patch(
        'src.processes.services.templates.fieldsets.shared_fieldset.'
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
        'src.processes.services.templates.fieldsets.shared_fieldset.'
        'FieldSetTemplateService.create_rules',
    )
    create_fields_mock = mocker.patch(
        'src.processes.services.templates.fieldsets.shared_fieldset.'
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
    fieldset = SharedFieldSetTemplate.objects.create(
        account=account,
        name='Shared Fieldset',
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
    fieldset = SharedFieldSetTemplate.objects.create(
        account=account,
        name='Shared Fieldset',
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
    fieldset = SharedFieldSetTemplate.objects.create(
        account=account,
        name='Shared Fieldset',
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
    mocker.patch(
        'src.processes.services.templates.field_template.'
        'FieldTemplateService.partial_update',
    )

    # act
    service._update_fields(fields_data=fields_data)

    # assert
    field_template_service_init_mock.assert_called_once()
    assert not FieldTemplate.objects.filter(id=field_2.id).exists()
    assert FieldTemplate.objects.filter(id=field_1.id).exists()


def test_partial_update_name__ok(mocker):

    """Call `partial_update` with name only"""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    fieldset = SharedFieldSetTemplate.objects.create(
        account=account,
        name='Shared Fieldset',
        order=0,
    )
    mocker.patch(
        'src.processes.services.templates.fieldsets.shared_fieldset.'
        'FieldSetTemplateService._update_fields',
    )
    mocker.patch(
        'src.processes.services.templates.fieldsets.shared_fieldset.'
        'FieldSetTemplateService.update_rules',
    )
    mocker.patch(
        'src.processes.services.templates.fieldsets.shared_fieldset.'
        'FieldSetTemplateService._validate_rules',
    )
    service = FieldSetTemplateService(instance=fieldset, user=user)
    data = {'name': 'Updated Name'}

    # act
    result = service.partial_update(**data)

    # assert
    assert result.name == data['name']


def test_partial_update_order__ok(mocker):

    """Call `partial_update` with order"""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    fieldset = SharedFieldSetTemplate.objects.create(
        account=account,
        name='Shared Fieldset',
        order=0,
    )
    mocker.patch(
        'src.processes.services.templates.fieldsets.shared_fieldset.'
        'FieldSetTemplateService._update_fields',
    )
    mocker.patch(
        'src.processes.services.templates.fieldsets.shared_fieldset.'
        'FieldSetTemplateService.update_rules',
    )
    mocker.patch(
        'src.processes.services.templates.fieldsets.shared_fieldset.'
        'FieldSetTemplateService._validate_rules',
    )
    service = FieldSetTemplateService(instance=fieldset, user=user)
    data = {'order': 5}

    # act
    result = service.partial_update(**data)

    # assert
    assert result.order == 5


def test_partial_update_fields__ok(mocker):

    """Verify fields update logic"""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    fieldset = SharedFieldSetTemplate.objects.create(
        account=account,
        name='Shared Fieldset',
    )
    service = FieldSetTemplateService(user=user, instance=fieldset)

    mock_update_fields = mocker.patch(
        'src.processes.services.templates.fieldsets.shared_fieldset.'
        'FieldSetTemplateService._update_fields',
    )
    mock_update_rules = mocker.patch(
        'src.processes.services.templates.fieldsets.shared_fieldset.'
        'FieldSetTemplateService.update_rules',
    )
    mock_validate_rules = mocker.patch(
        'src.processes.services.templates.fieldsets.shared_fieldset.'
        'FieldSetTemplateService._validate_rules',
    )
    mock_super_partial_update = mocker.patch(
        'src.generics.base.service.'
        'BaseModelService.partial_update',
    )
    data = {
        'fields': [
            {'api_name': 'field_1', 'value': 'val'},
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

    """Verify rules update logic"""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    fieldset = SharedFieldSetTemplate.objects.create(
        account=account,
        name='Shared Fieldset',
    )
    mock_super_partial_update = mocker.patch(
        'src.generics.base.service.'
        'BaseModelService.partial_update',
    )
    mock_update_fields = mocker.patch(
        'src.processes.services.templates.fieldsets.shared_fieldset.'
        'FieldSetTemplateService._update_fields',
    )
    mock_update_rules = mocker.patch(
        'src.processes.services.templates.fieldsets.shared_fieldset.'
        'FieldSetTemplateService.update_rules',
    )
    mock_validate_rules = mocker.patch(
        'src.processes.services.templates.fieldsets.shared_fieldset.'
        'FieldSetTemplateService._validate_rules',
    )
    service = FieldSetTemplateService(user=user, instance=fieldset)
    data = {
        'rules': [
            {'api_name': 'rule_1', 'condition': 'eq'},
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


def test_delete__ok():

    """
    Instance deleted successfully
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    fieldset = SharedFieldSetTemplate.objects.create(
        account=account,
        name='Shared Fieldset',
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
    assert not SharedFieldSetTemplate.objects.filter(id=fieldset.id).exists()
