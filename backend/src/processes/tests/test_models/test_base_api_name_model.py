import pytest

from src.processes.models.workflows.fieldset import FieldSet
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_fieldset,
    create_test_owner,
    create_test_workflow,
)

pytestmark = pytest.mark.django_db


def test_update_or_create__existing_fieldset__api_name_preserved():

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(
        user=owner,
        tasks_count=1,
    )
    task = workflow.tasks.get(number=1)
    fieldset = create_test_fieldset(
        workflow=workflow,
        task=task,
        name='Original fieldset',
        api_name='existing-fieldset',
    )

    # act
    updated, created = FieldSet.objects.update_or_create(
        workflow=workflow,
        task=task,
        api_name=fieldset.api_name,
        defaults={'name': 'Updated fieldset'},
    )

    # assert
    updated.refresh_from_db()
    assert created is False
    assert updated.pk == fieldset.pk
    assert updated.name == 'Updated fieldset'
    assert updated.api_name == fieldset.api_name
