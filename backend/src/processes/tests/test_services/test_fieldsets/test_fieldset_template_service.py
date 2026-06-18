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
    FieldsetTemplateSharedIdMissing,
    FieldsetTemplateTemplateIdMissing,
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
    shared_fieldset = FieldsetTemplate.objects.create(
        account=account,
        name='Shared FS',
        is_shared=True,
    )
    service = FieldSetTemplateService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    name = 'Test fieldset'

    # act
    service._create_instance(
        name=name,
        template_id=template.id,
        is_shared=False,
        shared_fieldset_id=shared_fieldset.id,
    )

    # assert
    assert service.instance is not None
    assert service.instance.name == name
    assert service.instance.api_name
    assert service.instance.template_id == template.id
    assert service.instance.shared_fieldset_id == shared_fieldset.id
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
    shared_fieldset = FieldsetTemplate.objects.create(
        account=account,
        name='Shared FS',
        is_shared=True,
    )
    service = FieldSetTemplateService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    name = 'Test fieldset'
    description = 'Test description'
    label_position = LabelPosition.LEFT
    layout = FieldSetLayout.HORIZONTAL
    api_name = 'fs-1'

    # act
    service._create_instance(
        name=name,
        template_id=template.id,
        is_shared=False,
        shared_fieldset_id=shared_fieldset.id,
        description=description,
        label_position=label_position,
        layout=layout,
        api_name=api_name,
    )

    # assert
    assert service.instance.name == name
    assert service.instance.template_id == template.id
    assert service.instance.shared_fieldset_id == shared_fieldset.id
    assert service.instance.description == description
    assert service.instance.label_position == label_position
    assert service.instance.layout == layout
    assert service.instance.api_name == api_name


def test__create_instance__shared_fieldset__ok():

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
    name = 'Test fieldset'

    # act
    service._create_instance(
        name=name,
        is_shared=True,
    )

    # assert
    assert service.instance is not None
    assert service.instance.name == name
    assert service.instance.is_shared is True
    assert service.instance.template_id is None
    assert service.instance.title == ''
    assert service.instance.description == ''
    assert service.instance.kickoff_id is None
    assert service.instance.task_id is None
    assert service.instance.shared_fieldset_id is None
    assert service.instance.api_name
    assert service.instance.account_id == account.id
    assert service.instance.label_position == LabelPosition.TOP
    assert service.instance.layout == FieldSetLayout.VERTICAL


def test__create_instance__is_shared_api_name_provided__ok():

    """
    is_shared=True, api_name provided
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    service = FieldSetTemplateService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    name = 'Shared fieldset'
    api_name = 'fs-custom-1'

    # act
    service._create_instance(
        name=name,
        is_shared=True,
        api_name=api_name,
    )

    # assert
    assert service.instance.api_name == api_name
    assert service.instance.is_shared is True
    assert service.instance.template_id is None


def test__create_instance__not_shared_no_template_id__raise_exception():

    """
    is_shared=False, template_id missing
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    shared_fieldset = FieldsetTemplate.objects.create(
        account=account,
        name='Shared FS',
        is_shared=True,
    )
    service = FieldSetTemplateService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )

    # act
    with pytest.raises(FieldsetTemplateTemplateIdMissing) as ex:
        service._create_instance(
            name='Fieldset',
            is_shared=False,
            shared_fieldset_id=shared_fieldset.id,
        )

    # assert
    assert ex.value.message == fs_messages.MSG_FS_0011


def test__create_instance__not_shared_no_shared_fieldset_id__raise_exception():

    """
    is_shared=False, shared_fieldset_id missing
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

    # act
    with pytest.raises(FieldsetTemplateSharedIdMissing) as ex:
        service._create_instance(
            name='Fieldset',
            is_shared=False,
            template_id=template.id,
        )

    # assert
    assert ex.value.message == fs_messages.MSG_FS_0010


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


def test_partial_update_name__ok(mocker):

    """Call `partial_update` with default parameters"""

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    template = create_test_template(user=owner, tasks_count=1)
    template.tasks.get(number=1)
    fieldset = create_test_fieldset_template(
        account=account,
        template=template,
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


def test_partial_update_fields_ok(mocker):
    """Verify fields update logic for existing and new fields"""

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    template = create_test_template(user=owner, tasks_count=1)
    template.tasks.get(number=1)
    fieldset = create_test_fieldset_template(
        account=account,
        template=template,
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
    template.tasks.get(number=1)
    fieldset = create_test_fieldset_template(
        account=account,
        template=template,
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


def test_delete__used_by_kickoff_deleted_record__ok():

    """
    Fieldset previously linked to kickoff but now cleared → deleted
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
    )
    fieldset.kickoff = None
    fieldset.save(update_fields=['kickoff'])
    fieldset.refresh_from_db()
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


def test_delete__used_by_task_deleted_record__ok():

    """
    Fieldset previously linked to task but now cleared → deleted
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user, tasks_count=1)
    task = template.tasks.get(number=1)
    fieldset = FieldsetTemplate.objects.create(
        template=template,
        account=account,
        name='Fieldset',
        task=task,
    )
    fieldset.task = None
    fieldset.save(update_fields=['task'])
    fieldset.refresh_from_db()
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
    In use by kickoff (kickoff_id is set) → exception
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
        name='Fieldset',
        task=task_template,
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


def test_create_shared_fieldset__ok():

    """
    Default params
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    service = FieldSetTemplateService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    name = 'My Shared Fieldset'

    # act
    result = service.create_shared_fieldset(name=name)

    # assert
    assert result.name == name
    assert result.is_shared is True
    assert result.title == ''
    assert result.description == ''
    assert result.label_position == LabelPosition.TOP
    assert result.layout == FieldSetLayout.VERTICAL
    assert result.api_name
    assert result.template_id is None


def test__create_shared_fieldset__all_params__ok():

    """
    All params provided
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    service = FieldSetTemplateService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    name = 'Custom Fieldset'
    title = 'Custom Title'
    description = 'Custom description'
    api_name = 'fs-custom'
    label_position = LabelPosition.LEFT
    layout = FieldSetLayout.HORIZONTAL

    # act
    result = service.create_shared_fieldset(
        name=name,
        title=title,
        description=description,
        api_name=api_name,
        label_position=label_position,
        layout=layout,
    )

    # assert
    assert result.name == name
    assert result.title == title
    assert result.description == description
    assert result.api_name == api_name
    assert result.label_position == label_position
    assert result.layout == layout
    assert result.is_shared is True


def test__replace_api_names__fields_and_rules__ok(mocker):

    """
    Default params, fields and rules present
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    service = FieldSetTemplateService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    old_field_api = 'old-field-1'
    shared_fieldset_data = {
        'api_name': 'old-fs',
        'fields': [{'api_name': old_field_api, 'name': 'F 1'}],
        'rules': [{'api_name': 'old-rule-1', 'fields': [old_field_api]}],
    }
    new_fs_api = 'new-fs-1'
    new_field_api = 'new-field-1'
    new_rule_api = 'new-rule-1'
    create_api_name_mock = mocker.patch(
        'src.processes.services.templates.fieldsets.fieldset.create_api_name',
        side_effect=[new_fs_api, new_field_api, new_rule_api],
    )

    # act
    result = service._replace_api_names(
        shared_fieldset_data=shared_fieldset_data,
    )

    # assert
    assert result['api_name'] == new_fs_api
    assert result['fields'][0]['api_name'] == new_field_api
    assert result['rules'][0]['api_name'] == new_rule_api
    assert result['rules'][0]['fields'][0] == new_field_api
    assert create_api_name_mock.call_count == 3
    create_api_name_mock.assert_has_calls(
        [
            mocker.call(FieldsetTemplate.api_name_prefix),
            mocker.call(FieldTemplate.api_name_prefix),
            mocker.call(FieldsetTemplateRule.api_name_prefix),
        ],
        any_order=True,
    )


def test__replace_api_names__no_fields_key__ok(mocker):

    """
    No fields key
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    service = FieldSetTemplateService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    shared_fieldset_data = {'api_name': 'old-fs'}
    create_api_name_mock = mocker.patch(
        'src.processes.services.templates.fieldsets.fieldset.create_api_name',
        return_value='new-fs-1',
    )

    # act
    result = service._replace_api_names(
        shared_fieldset_data=shared_fieldset_data,
    )

    # assert
    assert result['fields'] == []
    create_api_name_mock.assert_called_once_with(
        FieldsetTemplate.api_name_prefix,
    )


def test__replace_api_names__empty_fields__ok(mocker):

    """
    Fields is empty list
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    service = FieldSetTemplateService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    shared_fieldset_data = {'api_name': 'old-fs', 'fields': []}
    create_api_name_mock = mocker.patch(
        'src.processes.services.templates.fieldsets.fieldset.create_api_name',
        return_value='new-fs-1',
    )

    # act
    result = service._replace_api_names(
        shared_fieldset_data=shared_fieldset_data,
    )

    # assert
    assert result['fields'] == []
    create_api_name_mock.assert_called_once_with(
        FieldsetTemplate.api_name_prefix,
    )


def test__replace_api_names__no_rules_key__ok(mocker):

    """
    No rules key
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    service = FieldSetTemplateService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    shared_fieldset_data = {'api_name': 'old-fs', 'fields': []}
    create_api_name_mock = mocker.patch(
        'src.processes.services.templates.fieldsets.fieldset.create_api_name',
        return_value='new-fs-1',
    )

    # act
    result = service._replace_api_names(
        shared_fieldset_data=shared_fieldset_data,
    )

    # assert
    assert result['rules'] == []
    create_api_name_mock.assert_called_once_with(
        FieldsetTemplate.api_name_prefix,
    )


def test__replace_api_names__empty_rules__ok(mocker):

    """
    Rules is empty list
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    service = FieldSetTemplateService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    shared_fieldset_data = {'api_name': 'old-fs', 'rules': []}
    create_api_name_mock = mocker.patch(
        'src.processes.services.templates.fieldsets.fieldset.create_api_name',
        return_value='new-fs-1',
    )

    # act
    result = service._replace_api_names(
        shared_fieldset_data=shared_fieldset_data,
    )

    # assert
    assert result['rules'] == []
    create_api_name_mock.assert_called_once_with(
        FieldsetTemplate.api_name_prefix,
    )


def test__replace_api_names__original_not_mutated__ok(mocker):

    """
    Original dict not mutated
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    service = FieldSetTemplateService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    old_field_api = 'old-field-1'
    shared_fieldset_data = {
        'api_name': 'old-fs',
        'fields': [{'api_name': old_field_api, 'name': 'F 1'}],
        'rules': [],
    }
    create_api_name_mock = mocker.patch(
        'src.processes.services.templates.fieldsets.fieldset.create_api_name',
        side_effect=['new-fs', 'new-field'],
    )

    # act
    service._replace_api_names(shared_fieldset_data=shared_fieldset_data)

    # assert
    assert shared_fieldset_data['api_name'] == 'old-fs'
    assert shared_fieldset_data['fields'][0]['api_name'] == old_field_api
    assert create_api_name_mock.call_count == 2


def test__get_new_fieldset_data__default_params__ok(mocker):

    """
    Default params
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    service = FieldSetTemplateService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    shared_fieldset_data = {'api_name': 'old-fs'}
    replace_api_names_mock = mocker.patch(
        'src.processes.services.templates.fieldsets.fieldset.'
        'FieldSetTemplateService._replace_api_names',
        return_value={'api_name': 'mocked-api', 'order': 3},
    )

    # act
    result = service.get_new_fieldset_data(
        shared_fieldset_data=shared_fieldset_data,
    )

    # assert
    assert 'order' not in result
    replace_api_names_mock.assert_called_once_with(shared_fieldset_data)


def test__get_new_fieldset_data__api_name_provided__ok(mocker):

    """
    api_name provided
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    service = FieldSetTemplateService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    shared_fieldset_data = {'api_name': 'old-fs'}
    override_api_name = 'custom-api'
    replace_api_names_mock = mocker.patch(
        'src.processes.services.templates.fieldsets.fieldset.'
        'FieldSetTemplateService._replace_api_names',
        return_value={'api_name': 'mocked-api'},
    )

    # act
    result = service.get_new_fieldset_data(
        shared_fieldset_data=shared_fieldset_data,
        api_name=override_api_name,
    )

    # assert
    assert result['api_name'] == override_api_name
    replace_api_names_mock.assert_called_once_with(shared_fieldset_data)


def test__get_new_fieldset_data__api_name_omitted__ok(mocker):

    """
    api_name omitted
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    service = FieldSetTemplateService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    shared_fieldset_data = {'api_name': 'old-fs'}
    mocked_api_name = 'mocked-api'
    replace_api_names_mock = mocker.patch(
        'src.processes.services.templates.fieldsets.fieldset.'
        'FieldSetTemplateService._replace_api_names',
        return_value={'api_name': mocked_api_name},
    )

    # act
    result = service.get_new_fieldset_data(
        shared_fieldset_data=shared_fieldset_data,
    )

    # assert
    assert result['api_name'] == mocked_api_name
    replace_api_names_mock.assert_called_once_with(shared_fieldset_data)


def test__get_new_fieldset_data__title_provided__ok(mocker):

    """
    title provided
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    service = FieldSetTemplateService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    shared_fieldset_data = {'api_name': 'old-fs'}
    override_title = 'Custom Title'
    replace_api_names_mock = mocker.patch(
        'src.processes.services.templates.fieldsets.fieldset.'
        'FieldSetTemplateService._replace_api_names',
        return_value={'api_name': 'api', 'title': 'Original'},
    )

    # act
    result = service.get_new_fieldset_data(
        shared_fieldset_data=shared_fieldset_data,
        title=override_title,
    )

    # assert
    assert result['title'] == override_title
    replace_api_names_mock.assert_called_once_with(shared_fieldset_data)


def test__get_new_fieldset_data__title_omitted__ok(mocker):

    """
    title omitted
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    service = FieldSetTemplateService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    shared_fieldset_data = {'api_name': 'old-fs'}
    original_title = 'Original Title'
    replace_api_names_mock = mocker.patch(
        'src.processes.services.templates.fieldsets.fieldset.'
        'FieldSetTemplateService._replace_api_names',
        return_value={'api_name': 'api', 'title': original_title},
    )

    # act
    result = service.get_new_fieldset_data(
        shared_fieldset_data=shared_fieldset_data,
    )

    # assert
    assert result['title'] == original_title
    replace_api_names_mock.assert_called_once_with(shared_fieldset_data)


def test__get_new_fieldset_data__description_provided__ok(mocker):

    """
    description provided
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    service = FieldSetTemplateService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    shared_fieldset_data = {'api_name': 'old-fs'}
    override_description = 'New description'
    replace_api_names_mock = mocker.patch(
        'src.processes.services.templates.fieldsets.fieldset.'
        'FieldSetTemplateService._replace_api_names',
        return_value={'api_name': 'api', 'description': 'Old desc'},
    )

    # act
    result = service.get_new_fieldset_data(
        shared_fieldset_data=shared_fieldset_data,
        description=override_description,
    )

    # assert
    assert result['description'] == override_description
    replace_api_names_mock.assert_called_once_with(shared_fieldset_data)


def test__get_new_fieldset_data__description_omitted__ok(mocker):

    """
    description omitted
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    service = FieldSetTemplateService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    shared_fieldset_data = {'api_name': 'old-fs'}
    original_description = 'Original description'
    replace_api_names_mock = mocker.patch(
        'src.processes.services.templates.fieldsets.fieldset.'
        'FieldSetTemplateService._replace_api_names',
        return_value={'api_name': 'api', 'description': original_description},
    )

    # act
    result = service.get_new_fieldset_data(
        shared_fieldset_data=shared_fieldset_data,
    )

    # assert
    assert result['description'] == original_description
    replace_api_names_mock.assert_called_once_with(shared_fieldset_data)


def test__get_new_fieldset_data__order_present__removed(mocker):

    """
    order present in data
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    service = FieldSetTemplateService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    shared_fieldset_data = {'api_name': 'old-fs', 'order': 5}
    replace_api_names_mock = mocker.patch(
        'src.processes.services.templates.fieldsets.fieldset.'
        'FieldSetTemplateService._replace_api_names',
        return_value={'api_name': 'api', 'order': 5},
    )

    # act
    result = service.get_new_fieldset_data(
        shared_fieldset_data=shared_fieldset_data,
    )

    # assert
    assert 'order' not in result
    replace_api_names_mock.assert_called_once_with(shared_fieldset_data)


def test__get_new_fieldset_data__no_order__ok(mocker):

    """
    order absent in data
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    service = FieldSetTemplateService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    shared_fieldset_data = {'api_name': 'old-fs'}
    replace_api_names_mock = mocker.patch(
        'src.processes.services.templates.fieldsets.fieldset.'
        'FieldSetTemplateService._replace_api_names',
        return_value={'api_name': 'api'},
    )

    # act
    result = service.get_new_fieldset_data(
        shared_fieldset_data=shared_fieldset_data,
    )

    # assert
    assert 'order' not in result
    replace_api_names_mock.assert_called_once_with(shared_fieldset_data)


def test__create_from_shared__default_params__ok(mocker):

    """
    Default optional params
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
    shared_fieldset_data = {'api_name': 'old-fs', 'name': 'Fieldset'}
    shared_fieldset_id = 42
    fieldset_data_from_mock = {'api_name': 'new-fs', 'name': 'Fieldset'}
    get_new_fieldset_data_mock = mocker.patch(
        'src.processes.services.templates.fieldsets.fieldset.'
        'FieldSetTemplateService.get_new_fieldset_data',
        return_value=fieldset_data_from_mock,
    )
    create_mock = mocker.patch(
        'src.processes.services.templates.fieldsets.fieldset.'
        'FieldSetTemplateService.create',
        return_value=mocker.Mock(),
    )

    # act
    result = service.create_from_shared(
        shared_fieldset_data=shared_fieldset_data,
        shared_fieldset_id=shared_fieldset_id,
        template_id=template.id,
    )

    # assert
    assert result is create_mock.return_value
    get_new_fieldset_data_mock.assert_called_once_with(
        shared_fieldset_data=shared_fieldset_data,
        api_name=None,
        title=None,
        description=None,
    )
    create_mock.assert_called_once_with(
        api_name='new-fs',
        name='Fieldset',
        is_shared=True,
        shared_fieldset_id=shared_fieldset_id,
        order=0,
        kickoff_id=None,
        task_id=None,
        template_id=template.id,
    )


def test__create_from_shared__all_params__ok(mocker):

    """
    All params provided
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user, tasks_count=1)
    kickoff = template.kickoff_instance
    task = template.tasks.get(number=1)
    service = FieldSetTemplateService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    shared_fieldset_data = {'api_name': 'old-fs', 'name': 'Fieldset'}
    shared_fieldset_id = 10
    api_name = 'custom-api'
    title = 'Custom Title'
    description = 'Custom desc'
    order = 3
    fieldset_data_from_mock = {'api_name': api_name, 'name': 'Fieldset'}
    get_new_fieldset_data_mock = mocker.patch(
        'src.processes.services.templates.fieldsets.fieldset.'
        'FieldSetTemplateService.get_new_fieldset_data',
        return_value=fieldset_data_from_mock,
    )
    create_mock = mocker.patch(
        'src.processes.services.templates.fieldsets.fieldset.'
        'FieldSetTemplateService.create',
        return_value=mocker.Mock(),
    )

    # act
    result = service.create_from_shared(
        shared_fieldset_data=shared_fieldset_data,
        shared_fieldset_id=shared_fieldset_id,
        template_id=template.id,
        order=order,
        kickoff_id=kickoff.id,
        task_id=task.id,
        api_name=api_name,
        title=title,
        description=description,
    )

    # assert
    assert result is create_mock.return_value
    get_new_fieldset_data_mock.assert_called_once_with(
        shared_fieldset_data=shared_fieldset_data,
        api_name=api_name,
        title=title,
        description=description,
    )
    create_mock.assert_called_once_with(
        api_name=api_name,
        name='Fieldset',
        is_shared=True,
        shared_fieldset_id=shared_fieldset_id,
        order=order,
        kickoff_id=kickoff.id,
        task_id=task.id,
        template_id=template.id,
    )


def test__partial_update_instance__no_kwargs__ok():

    """
    No kwargs
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user, tasks_count=1)
    fieldset = create_test_fieldset_template(
        account=account,
        template=template,
    )
    original_name = fieldset.name
    service = FieldSetTemplateService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=fieldset,
    )

    # act
    result = service.partial_update_instance()

    # assert
    assert result is fieldset
    fieldset.refresh_from_db()
    assert fieldset.name == original_name


def test__partial_update_instance__kwargs_provided__ok():

    """
    kwargs provided
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user, tasks_count=1)
    fieldset = create_test_fieldset_template(
        account=account,
        template=template,
    )
    new_name = 'Updated Fieldset Name'
    service = FieldSetTemplateService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=fieldset,
    )

    # act
    result = service.partial_update_instance(name=new_name)

    # assert
    assert result is not None
    fieldset.refresh_from_db()
    assert fieldset.name == new_name


def test__to_json__is_shared__ok(mocker):

    """
    is_shared=True
    """

    # arrange
    account = create_test_account()
    fieldset = FieldsetTemplate.objects.create(
        account=account,
        name='Shared FS',
        is_shared=True,
    )
    serializer_data = {'id': fieldset.id, 'name': 'Shared FS'}
    shared_fs_slz_mock = mocker.patch(
        'src.processes.serializers.templates.fieldset.'
        'SharedFieldsetTemplateSerializer',
    )
    shared_fs_slz_mock.return_value.data = serializer_data

    # act
    result = FieldSetTemplateService.to_json(fieldset=fieldset)

    # assert
    assert result == serializer_data
    shared_fs_slz_mock.assert_called_once_with(fieldset)


def test__to_json__not_shared__ok(mocker):

    """
    is_shared=False
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user, tasks_count=1)
    fieldset = create_test_fieldset_template(
        account=account,
        template=template,
    )
    serializer_data = {'id': fieldset.id, 'name': fieldset.name}
    fieldset_template_serializer_mock = mocker.patch(
        'src.processes.serializers.templates.fieldset.'
        'FieldsetTemplateSerializer',
    )
    fieldset_template_serializer_mock.return_value.data = serializer_data

    # act
    result = FieldSetTemplateService.to_json(fieldset=fieldset)

    # assert
    assert result == serializer_data
    fieldset_template_serializer_mock.assert_called_once_with(fieldset)
