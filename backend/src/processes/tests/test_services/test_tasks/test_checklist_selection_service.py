import pytest
from django.utils import timezone

from src.processes.models.workflows.checklist import ChecklistSelection
from src.processes.services.tasks.checklist_selection import (
    ChecklistSelectionService,
)
from src.processes.tests.fixtures import (
    create_checklist_template,
    create_test_account,
    create_test_owner,
    create_test_template,
    create_test_workflow,
)

pytestmark = pytest.mark.django_db


def test_mark__not_selected__return_true():

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    template = create_test_template(
        user=owner,
        is_active=True,
        tasks_count=1,
    )
    create_checklist_template(task_template=template.tasks.get(number=1))
    workflow = create_test_workflow(user=owner, template=template)
    task = workflow.tasks.get(number=1)
    selection = ChecklistSelection.objects.get(
        checklist=task.checklists.get(),
        api_name='cl-selection-1',
    )
    service = ChecklistSelectionService(instance=selection, user=owner)

    # act
    result = service.mark()

    # assert
    assert result is True
    selection.refresh_from_db()
    assert selection.is_selected is True
    assert selection.selected_user_id == owner.id
    task.refresh_from_db()
    assert task.checklists_marked == 1


def test_mark__already_selected__return_false():

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    template = create_test_template(
        user=owner,
        is_active=True,
        tasks_count=1,
    )
    create_checklist_template(task_template=template.tasks.get(number=1))
    workflow = create_test_workflow(user=owner, template=template)
    task = workflow.tasks.get(number=1)
    selection = ChecklistSelection.objects.get(
        checklist=task.checklists.get(),
        api_name='cl-selection-1',
    )
    date_selected = timezone.now()
    selection.date_selected = date_selected
    selection.selected_user_id = owner.id
    selection.save(update_fields=['date_selected', 'selected_user_id'])
    service = ChecklistSelectionService(instance=selection, user=owner)

    # act
    result = service.mark()

    # assert
    assert result is False
    selection.refresh_from_db()
    assert selection.date_selected == date_selected
    task.refresh_from_db()
    assert task.checklists_marked == 0


def test_unmark__selected__return_true():

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    template = create_test_template(
        user=owner,
        is_active=True,
        tasks_count=1,
    )
    create_checklist_template(task_template=template.tasks.get(number=1))
    workflow = create_test_workflow(user=owner, template=template)
    task = workflow.tasks.get(number=1)
    selection = ChecklistSelection.objects.get(
        checklist=task.checklists.get(),
        api_name='cl-selection-1',
    )
    selection.date_selected = timezone.now()
    selection.selected_user_id = owner.id
    selection.save(update_fields=['date_selected', 'selected_user_id'])
    task.checklists_marked = 1
    task.save(update_fields=['checklists_marked'])
    service = ChecklistSelectionService(instance=selection, user=owner)

    # act
    result = service.unmark()

    # assert
    assert result is True
    selection.refresh_from_db()
    assert selection.date_selected is None
    task.refresh_from_db()
    assert task.checklists_marked == 0


def test_unmark__not_selected__return_false():

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    template = create_test_template(
        user=owner,
        is_active=True,
        tasks_count=1,
    )
    create_checklist_template(task_template=template.tasks.get(number=1))
    workflow = create_test_workflow(user=owner, template=template)
    task = workflow.tasks.get(number=1)
    selection = ChecklistSelection.objects.get(
        checklist=task.checklists.get(),
        api_name='cl-selection-1',
    )
    service = ChecklistSelectionService(instance=selection, user=owner)

    # act
    result = service.unmark()

    # assert
    assert result is False
    selection.refresh_from_db()
    assert selection.date_selected is None
    assert selection.selected_user_id is None
