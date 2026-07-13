"""
Guardian permission test helpers.

Provides assertion utilities for verifying workflow-level permissions
during the M2M-to-Guardian migration.
"""

from guardian.shortcuts import get_users_with_perms

from src.processes.enums import WorkflowPermission


def assert_guardian_view(workflow, user, msg=''):
    """Assert user has Guardian view_workflow permission."""
    viewers = get_users_with_perms(
        workflow,
        only_with_perms_in=[WorkflowPermission.VIEW],
    )
    assert viewers.filter(id=user.id).exists(), (
        f'User {user.id} should have view_workflow on '
        f'Workflow {workflow.id}. {msg}'
    )


def assert_no_guardian_view(workflow, user, msg=''):
    """Assert user does NOT have Guardian view_workflow permission."""
    viewers = get_users_with_perms(
        workflow,
        only_with_perms_in=[WorkflowPermission.VIEW],
    )
    assert not viewers.filter(id=user.id).exists(), (
        f'User {user.id} should NOT have view_workflow on '
        f'Workflow {workflow.id}. {msg}'
    )


def assert_guardian_manage(workflow, user, msg=''):
    """Assert user has Guardian change_workflow permission."""
    managers = get_users_with_perms(
        workflow,
        only_with_perms_in=[WorkflowPermission.CHANGE],
    )
    assert managers.filter(id=user.id).exists(), (
        f'User {user.id} should have change_workflow on '
        f'Workflow {workflow.id}. {msg}'
    )


def assert_guardian_viewer_count(workflow, expected_count):
    """Assert exact number of users with view_workflow permission."""
    viewers = get_users_with_perms(
        workflow,
        only_with_perms_in=[WorkflowPermission.VIEW],
    )
    actual = viewers.count()
    assert actual == expected_count, (
        f'Expected {expected_count} viewers, got {actual} '
        f'on Workflow {workflow.id}'
    )


def assert_guardian_manager_count(workflow, expected_count):
    """Assert exact number of users with change_workflow permission."""
    managers = get_users_with_perms(
        workflow,
        only_with_perms_in=[WorkflowPermission.CHANGE],
    )
    actual = managers.count()
    assert actual == expected_count, (
        f'Expected {expected_count} managers, got {actual} '
        f'on Workflow {workflow.id}'
    )
