import pytest

from src.processes.enums import FieldType
from src.processes.models.templates.fields import FieldTemplate
from src.processes.models.templates.fields import FieldTemplateSelection
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_dataset,
    create_test_owner,
    create_test_template,
)

pytestmark = pytest.mark.django_db


def test_list__kickoff_field_selection_type_has_selections(api_client):

    """
    GET /templates returns selections for a kickoff field
    with a selection type (e.g. DROPDOWN).
    FieldTemplateListSerializer.to_representation keeps 'selections'
    when field type is in TYPES_WITH_SELECTIONS.
    """

    # arrange
    user = create_test_owner()
    api_client.token_authenticate(user)
    template = create_test_template(
        user=user,
        tasks_count=1,
        is_active=True,
    )
    kickoff = template.kickoff_instance
    selection_field = FieldTemplate.objects.create(
        name='Dropdown field',
        type=FieldType.DROPDOWN,
        kickoff=kickoff,
        template=template,
        order=1,
        api_name='dropdown-field-1',
        account=user.account,
    )
    selection = FieldTemplateSelection.objects.create(
        field_template=selection_field,
        template=template,
        value='Option A',
        api_name='selection-1',
    )

    # act
    response = api_client.get('/templates')

    # assert
    assert response.status_code == 200
    fields = response.data[0]['kickoff']['fields']
    assert len(fields) == 1
    field_data = fields[0]
    assert field_data['type'] == FieldType.DROPDOWN
    assert 'selections' in field_data
    assert len(field_data['selections']) == 1
    assert field_data['selections'][0]['value'] == selection.value
    assert field_data['selections'][0]['api_name'] == selection.api_name


def test_list__kickoff_field_non_selection_type_no_selections_key(
    api_client,
):

    """
    GET /templates does NOT include 'selections' or 'dataset' keys for
    kickoff fields with a non-selection type (e.g. STRING).
    FieldTemplateListSerializer.to_representation strips these keys.
    """

    # arrange
    user = create_test_owner()
    api_client.token_authenticate(user)
    template = create_test_template(
        user=user,
        tasks_count=1,
        is_active=True,
    )
    kickoff = template.kickoff_instance
    FieldTemplate.objects.create(
        name='String field',
        type=FieldType.STRING,
        kickoff=kickoff,
        template=template,
        order=1,
        api_name='string-field-1',
        account=user.account,
    )

    # act
    response = api_client.get('/templates')

    # assert
    assert response.status_code == 200
    fields = response.data[0]['kickoff']['fields']
    assert len(fields) == 1
    field_data = fields[0]
    assert field_data['type'] == FieldType.STRING
    assert 'selections' not in field_data
    assert 'dataset' not in field_data


def test_list__kickoff_field_with_dataset(api_client):

    """
    GET /templates returns 'dataset' id for a kickoff field of a
    selection type that references a dataset.
    FieldTemplateListSerializer includes 'dataset' in the response.
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    api_client.token_authenticate(user)
    dataset = create_test_dataset(account=account)
    template = create_test_template(
        user=user,
        tasks_count=1,
        is_active=True,
    )
    kickoff = template.kickoff_instance
    FieldTemplate.objects.create(
        name='Dropdown with dataset',
        type=FieldType.DROPDOWN,
        kickoff=kickoff,
        template=template,
        order=1,
        api_name='dropdown-field-1',
        account=user.account,
        dataset=dataset,
    )

    # act
    response = api_client.get('/templates')

    # assert
    assert response.status_code == 200
    fields = response.data[0]['kickoff']['fields']
    assert len(fields) == 1
    field_data = fields[0]
    assert field_data['type'] == FieldType.DROPDOWN
    assert 'dataset' in field_data
    assert field_data['dataset'] == dataset.id


def test_list__kickoff_field_selection_type_no_dataset(api_client):

    """
    GET /templates returns dataset=None for a selection type kickoff field
    that has no dataset set.
    'dataset' key is present but None when field has selections.
    """

    # arrange
    user = create_test_owner()
    api_client.token_authenticate(user)
    template = create_test_template(
        user=user,
        tasks_count=1,
        is_active=True,
    )
    kickoff = template.kickoff_instance
    dropdown_field = FieldTemplate.objects.create(
        name='Dropdown field',
        type=FieldType.DROPDOWN,
        kickoff=kickoff,
        template=template,
        order=1,
        api_name='dropdown-field-1',
        account=user.account,
    )
    FieldTemplateSelection.objects.create(
        field_template=dropdown_field,
        template=template,
        value='Option A',
        api_name='selection-1',
    )

    # act
    response = api_client.get('/templates')

    # assert
    assert response.status_code == 200
    fields = response.data[0]['kickoff']['fields']
    assert len(fields) == 1
    field_data = fields[0]
    assert field_data['type'] == FieldType.DROPDOWN
    assert 'dataset' in field_data
    assert field_data['dataset'] is None


def test_list__kickoff_field_description_none_returns_empty_string(
    api_client,
):

    """
    GET /templates converts a None description to an empty string
    for kickoff fields in the list serializer.
    FieldTemplateListSerializer.to_representation coerces None -> ''.
    """

    # arrange
    user = create_test_owner()
    api_client.token_authenticate(user)
    template = create_test_template(
        user=user,
        tasks_count=1,
        is_active=True,
    )
    kickoff = template.kickoff_instance
    field = FieldTemplate.objects.create(
        name='Text field',
        type=FieldType.TEXT,
        kickoff=kickoff,
        template=template,
        order=1,
        api_name='text-field-1',
        account=user.account,
        description=None,
    )

    # act
    response = api_client.get('/templates')

    # assert
    assert response.status_code == 200
    fields = response.data[0]['kickoff']['fields']
    assert len(fields) == 1
    field_data = fields[0]
    assert field_data['api_name'] == field.api_name
    assert field_data['description'] == ''


def test_list__kickoff_field_description_non_empty(api_client):

    """
    GET /templates returns the actual description string
    when it is set on a kickoff field.
    """

    # arrange
    user = create_test_owner()
    api_client.token_authenticate(user)
    description = 'Some description text'
    template = create_test_template(
        user=user,
        tasks_count=1,
        is_active=True,
    )
    kickoff = template.kickoff_instance
    field = FieldTemplate.objects.create(
        name='Text field',
        type=FieldType.TEXT,
        kickoff=kickoff,
        template=template,
        order=1,
        api_name='text-field-1',
        account=user.account,
        description=description,
    )

    # act
    response = api_client.get('/templates')

    # assert
    assert response.status_code == 200
    fields = response.data[0]['kickoff']['fields']
    assert len(fields) == 1
    field_data = fields[0]
    assert field_data['api_name'] == field.api_name
    assert field_data['description'] == description


@pytest.mark.parametrize(
    'field_type', FieldType.TYPES_WITH_SELECTIONS,
)
def test_list__kickoff_field_all_selection_types_include_selections(
    field_type,
    api_client,
):

    """
    GET /templates includes 'selections' and 'dataset' keys for all
    field types in TYPES_WITH_SELECTIONS (DROPDOWN, CHECKBOX, RADIO).
    """

    # arrange
    user = create_test_owner()
    api_client.token_authenticate(user)
    template = create_test_template(
        user=user,
        tasks_count=1,
        is_active=True,
    )
    kickoff = template.kickoff_instance
    field = FieldTemplate.objects.create(
        name='Selection field',
        type=field_type,
        kickoff=kickoff,
        template=template,
        order=1,
        api_name='field-1',
        account=user.account,
    )
    selection = FieldTemplateSelection.objects.create(
        field_template=field,
        template=template,
        value='Value 1',
        api_name='selection-1',
    )

    # act
    response = api_client.get('/templates')

    # assert
    assert response.status_code == 200
    fields = response.data[0]['kickoff']['fields']
    assert len(fields) == 1
    field_data = fields[0]
    assert field_data['type'] == field_type
    assert 'selections' in field_data
    assert 'dataset' in field_data
    assert field_data['selections'][0]['value'] == selection.value


def test_list__kickoff_field_required_fields_present(api_client):

    """
    GET /templates returns all expected fields from
    FieldTemplateListSerializer: name, type, is_required, is_hidden,
    description, api_name, and order.
    """

    # arrange
    user = create_test_owner()
    api_client.token_authenticate(user)
    template = create_test_template(
        user=user,
        tasks_count=1,
        is_active=True,
    )
    kickoff = template.kickoff_instance
    field = FieldTemplate.objects.create(
        name='Required field',
        type=FieldType.NUMBER,
        description='Field desc',
        kickoff=kickoff,
        template=template,
        order=3,
        api_name='number-field-1',
        account=user.account,
        is_required=True,
        is_hidden=False,
    )

    # act
    response = api_client.get('/templates')

    # assert
    assert response.status_code == 200
    fields = response.data[0]['kickoff']['fields']
    assert len(fields) == 1
    field_data = fields[0]
    assert field_data['name'] == field.name
    assert field_data['type'] == FieldType.NUMBER
    assert field_data['is_required'] is True
    assert field_data['is_hidden'] is False
    assert field_data['description'] == field.description
    assert field_data['api_name'] == field.api_name
    assert field_data['order'] == field.order


def test_list__kickoff_field_multiple_selections_ordered(api_client):

    """
    GET /templates returns all selections of a kickoff field
    in the correct order (ordered by pk per FieldTemplateSelection Meta).
    """

    # arrange
    user = create_test_owner()
    api_client.token_authenticate(user)
    template = create_test_template(
        user=user,
        tasks_count=1,
        is_active=True,
    )
    kickoff = template.kickoff_instance
    field = FieldTemplate.objects.create(
        name='Radio field',
        type=FieldType.RADIO,
        kickoff=kickoff,
        template=template,
        order=1,
        api_name='radio-field-1',
        account=user.account,
    )
    selection_1 = FieldTemplateSelection.objects.create(
        field_template=field,
        template=template,
        value='First',
        api_name='selection-1',
    )
    selection_2 = FieldTemplateSelection.objects.create(
        field_template=field,
        template=template,
        value='Second',
        api_name='selection-2',
    )

    # act
    response = api_client.get('/templates')

    # assert
    assert response.status_code == 200
    fields = response.data[0]['kickoff']['fields']
    assert len(fields) == 1
    field_data = fields[0]
    assert len(field_data['selections']) == 2
    assert field_data['selections'][0]['api_name'] == selection_1.api_name
    assert field_data['selections'][0]['value'] == 'First'
    assert field_data['selections'][1]['api_name'] == selection_2.api_name
    assert field_data['selections'][1]['value'] == 'Second'


def test_list__kickoff_field_non_selection_types_no_dataset_key(
    api_client,
):

    """
    GET /templates does NOT expose 'dataset' in the response for
    non-selection field types even when the field model has dataset set.
    FieldTemplateListSerializer.to_representation strips 'dataset'
    for non-selection types.
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    api_client.token_authenticate(user)
    dataset = create_test_dataset(account=account)
    template = create_test_template(
        user=user,
        tasks_count=1,
        is_active=True,
    )
    kickoff = template.kickoff_instance
    FieldTemplate.objects.create(
        name='Text field',
        type=FieldType.TEXT,
        kickoff=kickoff,
        template=template,
        order=1,
        api_name='text-field-1',
        account=user.account,
        dataset=dataset,
    )

    # act
    response = api_client.get('/templates')

    # assert
    assert response.status_code == 200
    fields = response.data[0]['kickoff']['fields']
    assert len(fields) == 1
    field_data = fields[0]
    assert field_data['type'] == FieldType.TEXT
    assert 'dataset' not in field_data
    assert 'selections' not in field_data


def test_list__kickoff_multiple_fields_ordered_by_order_desc(api_client):

    """
    GET /templates returns kickoff fields ordered by order descending
    (per FieldTemplate Meta: ordering = ['-order']).
    """

    # arrange
    user = create_test_owner()
    api_client.token_authenticate(user)
    template = create_test_template(
        user=user,
        tasks_count=1,
        is_active=True,
    )
    kickoff = template.kickoff_instance
    field_order_1 = FieldTemplate.objects.create(
        name='Field order 1',
        type=FieldType.STRING,
        kickoff=kickoff,
        template=template,
        order=1,
        api_name='string-field-1',
        account=user.account,
    )
    field_order_3 = FieldTemplate.objects.create(
        name='Field order 3',
        type=FieldType.NUMBER,
        kickoff=kickoff,
        template=template,
        order=3,
        api_name='number-field-1',
        account=user.account,
    )
    field_order_2 = FieldTemplate.objects.create(
        name='Field order 2',
        type=FieldType.TEXT,
        kickoff=kickoff,
        template=template,
        order=2,
        api_name='text-field-1',
        account=user.account,
    )

    # act
    response = api_client.get('/templates')

    # assert
    assert response.status_code == 200
    fields = response.data[0]['kickoff']['fields']
    assert len(fields) == 3
    assert fields[0]['api_name'] == field_order_3.api_name
    assert fields[1]['api_name'] == field_order_2.api_name
    assert fields[2]['api_name'] == field_order_1.api_name


def test_list__kickoff_field_is_hidden_true(api_client):

    """
    GET /templates correctly serializes is_hidden=True
    for a kickoff field of a non-selection type.
    """

    # arrange
    user = create_test_owner()
    api_client.token_authenticate(user)
    template = create_test_template(
        user=user,
        tasks_count=1,
        is_active=True,
    )
    kickoff = template.kickoff_instance
    field = FieldTemplate.objects.create(
        name='Hidden field',
        type=FieldType.STRING,
        kickoff=kickoff,
        template=template,
        order=1,
        api_name='string-field-1',
        account=user.account,
        is_hidden=True,
        is_required=False,
    )

    # act
    response = api_client.get('/templates')

    # assert
    assert response.status_code == 200
    fields = response.data[0]['kickoff']['fields']
    assert len(fields) == 1
    field_data = fields[0]
    assert field_data['api_name'] == field.api_name
    assert field_data['is_hidden'] is True
    assert field_data['is_required'] is False
