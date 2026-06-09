import pytest

from src.processes.enums import (
    FieldSetLayout,
    FieldSetRuleType,
    FieldType,
    LabelPosition,
)
from src.processes.models.templates.fieldset import (
    FieldsetTemplate,
    FieldsetTemplateRule,
)
from src.processes.models.templates.fields import (
    FieldTemplate,
    FieldTemplateSelection,
)
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_fieldset_template,
    create_test_owner,
    create_test_template,
)

pytestmark = pytest.mark.django_db


def test_clone__fieldset_copied__ok(api_client):

    """Cloning a template copies its FieldsetTemplate
    to the new template with correct attributes."""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    api_client.token_authenticate(user)
    template = create_test_template(user=user, tasks_count=1)
    fieldset = create_test_fieldset_template(
        account=account,
        template=template,
        name='My Fieldset',
        description='Some description',
        label_position=LabelPosition.LEFT,
        layout=FieldSetLayout.HORIZONTAL,
    )

    # act
    response = api_client.post(f'/templates/{template.id}/clone')

    # assert
    assert response.status_code == 200
    new_template_id = response.data['id']
    assert new_template_id != template.id

    field_clones = FieldsetTemplate.objects.filter(
        template_id=new_template_id,
    )
    assert field_clones.count() == 1
    fieldset_clone = field_clones.first()
    assert fieldset_clone.name == fieldset.name
    assert fieldset_clone.api_name == fieldset.api_name
    assert fieldset_clone.description == fieldset.description
    assert fieldset_clone.label_position == fieldset.label_position
    assert fieldset_clone.layout == fieldset.layout
    assert fieldset_clone.account_id == account.id


def test_clone__fieldset_with_fields__ok(api_client):

    """Cloning copies FieldTemplate records
    belonging to the fieldset."""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    api_client.token_authenticate(user)
    template = create_test_template(user=user, tasks_count=1)
    fieldset = create_test_fieldset_template(
        account=account,
        template=template,
        name='Fieldset with fields',
    )
    field_1 = fieldset.fields.first()
    # fixture creates one STRING field; add a second one
    field_2 = FieldTemplate.objects.create(
        template=template,
        fieldset=fieldset,
        account=account,
        name='Second field',
        type=FieldType.NUMBER,
        order=2,
        is_required=False,
        is_hidden=True,
    )

    # act
    response = api_client.post(f'/templates/{template.id}/clone')

    # assert
    assert response.status_code == 200
    new_template_id = response.data['id']
    fieldset_clone = FieldsetTemplate.objects.get(template_id=new_template_id)
    field_clones = FieldTemplate.objects.filter(
        fieldset=fieldset_clone,
    ).order_by('order')
    assert field_clones.count() == 2

    field_1_clone = field_clones[0]
    assert field_1_clone.name == field_1.name
    assert field_1_clone.api_name == field_1.api_name
    assert field_1_clone.type == field_1.type
    assert field_1_clone.order == field_1.order
    assert field_1_clone.template_id == new_template_id
    assert field_1_clone.kickoff is None
    assert field_1_clone.task is None

    field_2_clone = field_clones[1]
    assert field_2_clone.name == field_2.name
    assert field_2_clone.api_name == field_2.api_name
    assert field_2_clone.type == field_2.type
    assert field_2_clone.order == field_2.order
    assert field_2_clone.is_hidden == field_2.is_hidden


def test_clone__fieldset_with_selections__ok(api_client):

    """Cloning copies FieldTemplateSelection records
    for dropdown fields in a fieldset."""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    api_client.token_authenticate(user)
    template = create_test_template(user=user, tasks_count=1)
    fieldset = create_test_fieldset_template(
        account=account,
        template=template,
        name='Fieldset with dropdown',
    )
    # Replace the default STRING field with a DROPDOWN + selections
    fieldset.fields.all().delete()
    field = FieldTemplate.objects.create(
        template=template,
        fieldset=fieldset,
        account=account,
        name='Dropdown field',
        type=FieldType.DROPDOWN,
        order=1,
    )
    selection_1 = FieldTemplateSelection.objects.create(
        template=template,
        field_template=field,
        value='Option A',
    )
    selection_2 = FieldTemplateSelection.objects.create(
        template=template,
        field_template=field,
        value='Option B',
    )

    # act
    response = api_client.post(f'/templates/{template.id}/clone')

    # assert
    assert response.status_code == 200
    new_template_id = response.data['id']
    fieldset_clone = FieldsetTemplate.objects.get(template_id=new_template_id)
    field_clone = FieldTemplate.objects.get(fieldset=fieldset_clone)
    selections_clone = FieldTemplateSelection.objects.filter(
        field_template=field_clone,
    ).order_by('value')
    assert selections_clone.count() == 2
    assert selections_clone[0].value == selection_1.value
    assert selections_clone[0].template_id == new_template_id
    assert selections_clone[0].api_name == selection_1.api_name

    assert selections_clone[1].value == selection_2.value
    assert selections_clone[1].template_id == new_template_id
    assert selections_clone[1].api_name == selection_2.api_name


def test_clone__fieldset_with_rules__ok(api_client):

    """Cloning copies FieldsetTemplateRule records
    and preserves the rule-field M2M relationships."""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    api_client.token_authenticate(user)
    template = create_test_template(user=user, tasks_count=1)
    fieldset = create_test_fieldset_template(
        account=account,
        template=template,
        name='Fieldset with rules',
        rule_type=FieldSetRuleType.SUM_EQUAL,
        rule_value='100',
    )
    # fixture creates a NUMBER field + rule; link them via M2M
    field = fieldset.fields.first()
    rule = fieldset.rules.first()
    field.rules.add(rule)

    # act
    response = api_client.post(f'/templates/{template.id}/clone')

    # assert
    assert response.status_code == 200
    new_template_id = response.data['id']
    fieldset_clone = FieldsetTemplate.objects.get(template_id=new_template_id)

    rules_clone = FieldsetTemplateRule.objects.filter(fieldset=fieldset_clone)
    assert rules_clone.count() == 1
    rule_clone = rules_clone.first()
    assert rule_clone.type == rule.type
    assert rule_clone.value == rule.value
    assert rule_clone.id != rule.id
    assert rule_clone.api_name == rule.api_name

    field_clone = FieldTemplate.objects.get(fieldset=fieldset_clone)
    assert list(field_clone.rules.all()) == [rule_clone]


def test_clone__multiple_fieldsets__ok(api_client):

    """Cloning a template with multiple fieldsets
    copies all of them."""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    api_client.token_authenticate(user)
    template = create_test_template(user=user, tasks_count=1)
    fs_1 = create_test_fieldset_template(
        account=account,
        template=template,
        name='Fieldset One',
    )
    fs_2 = create_test_fieldset_template(
        account=account,
        template=template,
        name='Fieldset Two',
    )

    # act
    response = api_client.post(f'/templates/{template.id}/clone')

    # assert
    assert response.status_code == 200
    new_template_id = response.data['id']
    fieldset_clones = FieldsetTemplate.objects.filter(
        template_id=new_template_id,
    ).order_by('name')
    assert fieldset_clones.count() == 2
    assert fieldset_clones[0].name == fs_1.name
    assert fieldset_clones[0].api_name == fs_1.api_name
    assert fieldset_clones[0].fields.count() == 1

    assert fieldset_clones[1].name == fs_2.name
    assert fieldset_clones[1].api_name == fs_2.api_name
    assert fieldset_clones[1].fields.count() == 1


def test_clone__no_kickoff_task_links__ok(api_client):

    """Cloning does NOT create FieldsetTemplateKickoff
    or FieldsetTemplateTaskTemplate records."""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    api_client.token_authenticate(user)
    template = create_test_template(user=user, tasks_count=1)
    task = template.tasks.first()
    kickoff = template.kickoff_instance
    fieldset = create_test_fieldset_template(
        account=account,
        template=template,
        kickoff=kickoff,
        task=task,
        name='Linked fieldset',
    )

    # act
    response = api_client.post(f'/templates/{template.id}/clone')

    # assert
    assert response.status_code == 200
    new_template_id = response.data['id']
    fieldset_clone = FieldsetTemplate.objects.get(
        template_id=new_template_id,
    )

    assert not FieldsetTemplateKickoff.objects.filter(
        fieldset=fieldset_clone,
    ).exists()
    assert not FieldsetTemplateTaskTemplate.objects.filter(
        fieldset=fieldset_clone,
    ).exists()


def test_clone__no_fieldsets__ok(api_client):

    """Cloning a template without fieldsets still works
    and creates no fieldsets on the clone."""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    api_client.token_authenticate(user)
    template = create_test_template(user=user, tasks_count=1)

    # act
    response = api_client.post(f'/templates/{template.id}/clone')

    # assert
    assert response.status_code == 200
    new_template_id = response.data['id']
    assert not (
        FieldsetTemplate.objects.filter(template_id=new_template_id).exists()
    )


def test_clone__fieldset_rule_multi_fields__ok(api_client):

    """Cloning preserves a rule linked to multiple fields
    via M2M."""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    api_client.token_authenticate(user)
    template = create_test_template(user=user, tasks_count=1)
    fieldset = create_test_fieldset_template(
        account=account,
        template=template,
        name='Multi-field rule fieldset',
        rule_type=FieldSetRuleType.SUM_EQUAL,
        rule_value='200',
    )
    field_1 = fieldset.fields.first()
    # fixture creates one NUMBER field; add a second one
    field_2 = FieldTemplate.objects.create(
        template=template,
        fieldset=fieldset,
        account=account,
        name='Amount B',
        type=FieldType.NUMBER,
        order=2,
    )
    rule = fieldset.rules.first()
    # Link both fields to the rule
    for field in fieldset.fields.all():
        field.rules.add(rule)

    # act
    response = api_client.post(f'/templates/{template.id}/clone')

    # assert
    assert response.status_code == 200
    new_template_id = response.data['id']
    fieldset_clone = FieldsetTemplate.objects.get(template_id=new_template_id)

    rule_clone = FieldsetTemplateRule.objects.get(fieldset=fieldset_clone)
    assert rule_clone.value == rule.value
    assert rule_clone.type == rule.type
    assert rule_clone.api_name == rule.api_name

    rule_fields = rule_clone.fields.order_by('order')
    assert rule_fields.count() == 2
    assert rule_fields[0].api_name == field_1.api_name
    assert rule_fields[1].api_name == field_2.api_name
