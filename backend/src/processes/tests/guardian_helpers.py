"""
Guardian permission test helpers.

Provides assertion utilities for verifying workflow-level permissions
during the M2M-to-Guardian migration.
Uses direct UserObjectPermission queries for consistency with
production code (avoids guardian.shortcuts which relies on
auth.Group, incompatible with custom UserGroup FK).
"""

from django.contrib.contenttypes.models import ContentType

from src.permissions.models import UserObjectPermission
from src.processes.enums import WorkflowPermission


def _viewer_ids(workflow):
    ct = ContentType.objects.get_for_model(workflow)
    return set(
        UserObjectPermission.objects.filter(
            permission__codename=WorkflowPermission.VIEW,
            content_type=ct,
            object_pk=str(workflow.pk),
        ).values_list('user_id', flat=True),
    )


def _manager_ids(workflow):
    ct = ContentType.objects.get_for_model(workflow)
    return set(
        UserObjectPermission.objects.filter(
            permission__codename=WorkflowPermission.CHANGE,
            content_type=ct,
            object_pk=str(workflow.pk),
        ).values_list('user_id', flat=True),
    )


def assert_guardian_view(workflow, user, msg=''):
    """Assert user has Guardian view_workflow permission."""
    assert user.id in _viewer_ids(workflow), (
        f'User {user.id} should have view_workflow on '
        f'Workflow {workflow.id}. {msg}'
    )


def assert_no_guardian_view(workflow, user, msg=''):
    """Assert user does NOT have view_workflow permission."""
    assert user.id not in _viewer_ids(workflow), (
        f'User {user.id} should NOT have view_workflow on '
        f'Workflow {workflow.id}. {msg}'
    )


def assert_guardian_manage(workflow, user, msg=''):
    """Assert user has Guardian change_workflow permission."""
    assert user.id in _manager_ids(workflow), (
        f'User {user.id} should have change_workflow on '
        f'Workflow {workflow.id}. {msg}'
    )


def assert_guardian_viewer_count(workflow, expected_count):
    """Assert exact number of users with view_workflow."""
    actual = len(_viewer_ids(workflow))
    assert actual == expected_count, (
        f'Expected {expected_count} viewers, got {actual} '
        f'on Workflow {workflow.id}'
    )


def assert_guardian_manager_count(workflow, expected_count):
    """Assert exact number of users with change_workflow."""
    actual = len(_manager_ids(workflow))
    assert actual == expected_count, (
        f'Expected {expected_count} managers, got {actual} '
        f'on Workflow {workflow.id}'
    )
