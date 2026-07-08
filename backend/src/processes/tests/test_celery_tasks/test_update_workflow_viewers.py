import pytest

from src.processes.tasks.update_workflow import (
    update_workflow_viewers,
)
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_owner,
    create_test_template,
    create_test_workflow,
)

pytestmark = pytest.mark.django_db


def test_update_workflow_viewers__calls_set_viewers_and_sync__ok(mocker):
    """Task must invoke set_viewers() for each workflow AND
    dispatch sync_workflow_attachment_permissions afterwards."""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(
        user=user,
        is_active=True,
        tasks_count=1,
    )
    workflow_1 = create_test_workflow(user=user, template=template)
    workflow_2 = create_test_workflow(user=user, template=template)

    set_viewers_mock = mocker.patch(
        'src.processes.tasks.update_workflow'
        '.WorkflowPermissionService.set_viewers',
    )
    sync_att_mock = mocker.patch(
        'src.processes.tasks.update_workflow'
        '.sync_workflow_attachment_permissions',
    )

    # act
    update_workflow_viewers([workflow_1.id, workflow_2.id])

    # assert
    assert set_viewers_mock.call_count == 2
    assert sync_att_mock.delay.call_count == 2
    called_ids = {
        c[0][0] for c in sync_att_mock.delay.call_args_list
    }
    assert called_ids == {workflow_1.id, workflow_2.id}


def test_update_workflow_viewers__skips_deleted_workflows__ok(mocker):
    """Soft-deleted workflows must be skipped: neither set_viewers()
    nor sync task must run for them."""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(
        user=user,
        is_active=True,
        tasks_count=1,
    )
    active_wf = create_test_workflow(user=user, template=template)
    deleted_wf = create_test_workflow(user=user, template=template)
    deleted_wf.is_deleted = True
    deleted_wf.save(update_fields=['is_deleted'])

    set_viewers_mock = mocker.patch(
        'src.processes.tasks.update_workflow'
        '.WorkflowPermissionService.set_viewers',
    )
    sync_att_mock = mocker.patch(
        'src.processes.tasks.update_workflow'
        '.sync_workflow_attachment_permissions',
    )

    # act
    update_workflow_viewers([active_wf.id, deleted_wf.id])

    # assert
    assert set_viewers_mock.call_count == 1
    sync_att_mock.delay.assert_called_once_with(active_wf.id)


def test_update_workflow_viewers__empty_ids__no_calls(mocker):
    """No workflow ids -> no permission recalculation or sync."""

    # arrange
    set_viewers_mock = mocker.patch(
        'src.processes.tasks.update_workflow'
        '.WorkflowPermissionService.set_viewers',
    )
    sync_att_mock = mocker.patch(
        'src.processes.tasks.update_workflow'
        '.sync_workflow_attachment_permissions',
    )

    # act
    update_workflow_viewers([])

    # assert
    set_viewers_mock.assert_not_called()
    sync_att_mock.delay.assert_not_called()
