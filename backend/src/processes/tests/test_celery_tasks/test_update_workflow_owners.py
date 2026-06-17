import pytest
from django.contrib.auth import get_user_model

from src.processes.enums import (
    DirectlyStatus,
    OwnerType,
    PerformerType,
)
from src.processes.models.templates.owner import TemplateOwner
from src.processes.models.workflows.task import TaskPerformer
from src.processes.tasks.update_workflow import (
    update_workflow_owners,
)
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_group,
    create_test_template,
    create_test_user,
    create_test_workflow,
)
from src.processes.services.workflow_permissions import (
    WorkflowPermissionService,
)

UserModel = get_user_model()
pytestmark = pytest.mark.django_db


def test__delete_group_owner_only__ok():
    """
    When deleting a group, an owner of the group type
    is deleted in template, and owner user is deleted in workflow.
    """

    # arrange
    account = create_test_account()
    user = create_test_user(account=account)
    template = create_test_template(
        user=user,
        is_active=True,
        tasks_count=1,
    )
    TemplateOwner.objects.all().delete()
    group = create_test_group(account, users=[user])
    TemplateOwner.objects.create(
        template=template,
        account=account,
        type=OwnerType.GROUP,
        group_id=group.id,
    )
    workflow = create_test_workflow(
        user=user,
        template=template,
    )
    group.delete()

    # act
    update_workflow_owners([template.id])

    # assert
    assert len(WorkflowPermissionService.get_owner_ids(workflow)) == 0


def test__add_template_owner_is_deleted__ok():
    """
    Verifies that soft-deleted template owners (is_deleted=True)
    are not propagated to workflow owners and members
    """
    # arrange
    account = create_test_account()
    user = create_test_user(account=account)
    template = create_test_template(
        user=user,
        is_active=True,
        tasks_count=1,
    )
    TemplateOwner.objects.all().delete()
    group = create_test_group(account, users=[user])
    workflow = create_test_workflow(
        user=user,
        template=template,
    )
    task = workflow.tasks.get(number=1)
    task.performers.all().delete()
    TemplateOwner.objects.create(
        template=template,
        account=account,
        type=OwnerType.GROUP,
        group_id=group.id,
        is_deleted=True,
    )

    # act
    update_workflow_owners([template.id])

    # assert
    assert len(WorkflowPermissionService.get_owner_ids(workflow)) == 0
    assert len(WorkflowPermissionService.get_viewer_ids(workflow)) == 0


def test__delete_group_owner_user_owner_persists_same_user__ok():
    """
    There are 2 owner types in the template. When deleting a group,
       the user owner (same user) persists in workflow.
    """

    # arrange
    account = create_test_account()
    user = create_test_user(account=account)
    template = create_test_template(
        user=user,
        is_active=True,
        tasks_count=1,
    )
    group_to_delete = create_test_group(account, users=[user])
    TemplateOwner.objects.create(
        template=template,
        account=account,
        type=OwnerType.GROUP,
        group_id=group_to_delete.id,
    )
    workflow = create_test_workflow(
        user=user,
        template=template,
    )
    group_to_delete.delete()

    # act
    update_workflow_owners([template.id])

    # assert
    assert len(WorkflowPermissionService.get_owner_ids(workflow)) == 1
    assert WorkflowPermissionService.has_manage(user, workflow)


def test__delete_group_owner_user_owner_persists_different_user__ok():
    """
    There are 2 owner types in the template. When deleting a group,
    the user owner (different user) persists in workflow.
    """

    # arrange
    account = create_test_account()
    user = create_test_user(account=account)
    user_2 = create_test_user(account=account, email='test1@test.test')
    template = create_test_template(
        user_2,
        is_active=True,
        tasks_count=1,
    )
    group_to_delete = create_test_group(account, users=[user])
    TemplateOwner.objects.create(
        template=template,
        account=account,
        type=OwnerType.GROUP,
        group_id=group_to_delete.id,
    )
    workflow = create_test_workflow(
        user=user_2,
        template=template,
    )
    group_to_delete.delete()

    # act
    update_workflow_owners([template.id])

    # assert
    assert len(WorkflowPermissionService.get_owner_ids(workflow)) == 1
    assert WorkflowPermissionService.has_manage(user_2, workflow)


def test__delete_group_owner_with_users_user_owner_persists__ok():
    """There are 2 owner types in the template. When deleting a group with
       users, the user owner persists in workflow."""

    # arrange
    account = create_test_account()
    user = create_test_user(account=account)
    user_2 = create_test_user(account=account, email='test1@test.test')
    user_3 = create_test_user(account=account, email='test2@test.test')
    template = create_test_template(
        user=user,
        is_active=True,
        tasks_count=1,
    )
    group_to_delete = create_test_group(account, users=[user_2, user_3])
    TemplateOwner.objects.create(
        template=template,
        account=account,
        type=OwnerType.GROUP,
        group_id=group_to_delete.id,
    )
    workflow = create_test_workflow(
        user=user_2,
        template=template,
    )
    group_to_delete.delete()

    # act
    update_workflow_owners([template.id])

    # assert
    assert len(WorkflowPermissionService.get_owner_ids(workflow)) == 1
    assert WorkflowPermissionService.has_manage(user, workflow)


def test__delete_one_group_owner_user_owner_persists_empty_group__ok():
    """There are 2 group owners in the template. When deleting one group,
       the user owner persists, second group is empty."""

    # arrange
    account = create_test_account()
    user = create_test_user(account=account)
    user_2 = create_test_user(account=account, email='test1@test.test')
    user_3 = create_test_user(account=account, email='test2@test.test')
    template = create_test_template(
        user=user,
        is_active=True,
        tasks_count=1,
    )
    group_to_delete = create_test_group(account, users=[user_2, user_3])
    group = create_test_group(name='group 2', account=account)
    TemplateOwner.objects.create(
        template=template,
        account=account,
        type=OwnerType.GROUP,
        group_id=group_to_delete.id,
    )
    TemplateOwner.objects.create(
        template=template,
        account=account,
        type=OwnerType.GROUP,
        group_id=group.id,
    )
    workflow = create_test_workflow(
        user=user_2,
        template=template,
    )
    group_to_delete.delete()

    # act
    update_workflow_owners([template.id])

    # assert
    assert len(WorkflowPermissionService.get_owner_ids(workflow)) == 1
    assert WorkflowPermissionService.has_manage(user, workflow)


def test__delete_one_group_owner_other_group_owner_persists__ok():
    """There are 2 group owners in the template. When deleting one group,
       the other group owner and its user persist in workflow."""

    # arrange
    account = create_test_account()
    user = create_test_user(account=account)
    user_2 = create_test_user(account=account, email='test1@test.test')
    template = create_test_template(
        user=user,
        is_active=True,
        tasks_count=1,
    )
    TemplateOwner.objects.filter(user_id=user.id).delete()
    group = create_test_group(account, users=[user])
    group_to_delete = create_test_group(
        name='group 2',
        account=account,
        users=[user_2],
    )
    TemplateOwner.objects.create(
        template=template,
        account=account,
        type=OwnerType.GROUP,
        group_id=group_to_delete.id,
    )
    TemplateOwner.objects.create(
        template=template,
        account=account,
        type=OwnerType.GROUP,
        group_id=group.id,
    )
    workflow = create_test_workflow(
        user=user,
        template=template,
    )
    group_to_delete.delete()

    # act
    update_workflow_owners([template.id])

    # assert
    assert len(WorkflowPermissionService.get_owner_ids(workflow)) == 1
    assert WorkflowPermissionService.has_manage(user, workflow)


def test__delete_group_owner_other_template_unchanged__ok():
    """When deleting a group owner in one template, the other template
       and its workflow remain unchanged."""

    # arrange
    account = create_test_account()
    user = create_test_user(account=account)
    template = create_test_template(
        user=user,
        is_active=True,
        tasks_count=1,
    )
    template_2 = create_test_template(
        user=user,
        is_active=True,
        tasks_count=1,
    )
    TemplateOwner.objects.filter(user_id=user.id).delete()
    group = create_test_group(account, users=[user])
    TemplateOwner.objects.create(
        template=template,
        account=account,
        type=OwnerType.GROUP,
        group_id=group.id,
    )
    group_to_delete = create_test_group(account, name='group 2', users=[user])
    TemplateOwner.objects.create(
        template=template_2,
        account=account,
        type=OwnerType.GROUP,
        group_id=group_to_delete.id,
    )
    workflow = create_test_workflow(
        user=user,
        template=template,
    )
    workflow_2 = create_test_workflow(
        user=user,
        template=template_2,
    )
    group_to_delete.delete()

    # act
    update_workflow_owners([template_2.id])

    # assert
    assert len(WorkflowPermissionService.get_owner_ids(template)) == 1
    assert template.owners.get(group_id=group.id)
    assert len(WorkflowPermissionService.get_owner_ids(workflow)) == 1
    assert WorkflowPermissionService.has_manage(user, workflow)
    assert len(WorkflowPermissionService.get_owner_ids(template_2)) == 0
    assert len(WorkflowPermissionService.get_owner_ids(workflow_2)) == 0


def test__delete_group_owner_different_account_unchanged__ok():
    """When deleting a group owner in one account, the template and
       workflow in another account remain unchanged."""

    # arrange
    account = create_test_account()
    user = create_test_user(account=account)
    template = create_test_template(
        user=user,
        is_active=True,
        tasks_count=1,
    )
    TemplateOwner.objects.filter(user_id=user.id).delete()
    group = create_test_group(account, users=[user])
    TemplateOwner.objects.create(
        template=template,
        account=account,
        type=OwnerType.GROUP,
        group_id=group.id,
    )
    workflow = create_test_workflow(
        user=user,
        template=template,
    )
    account_another = create_test_account()
    user_account_another = create_test_user(
        account=account_another,
        email='test1@test.test',
    )
    template_account_another = create_test_template(
        user_account_another,
        is_active=True,
        tasks_count=1,
    )
    TemplateOwner.objects.filter(
        type=OwnerType.USER,
        user_id=user_account_another.id,
    ).delete()
    group_to_delete = create_test_group(
        account,
        name='group 2',
        users=[user_account_another],
    )
    TemplateOwner.objects.create(
        template=template_account_another,
        account=account_another,
        type=OwnerType.GROUP,
        group_id=group_to_delete.id,
    )
    workflow_account_another = create_test_workflow(
        user=user_account_another,
        template=template_account_another,
    )
    group_to_delete.delete()

    # act
    update_workflow_owners([template_account_another.id])

    # assert
    assert len(WorkflowPermissionService.get_owner_ids(template)) == 1
    assert template.owners.get(group_id=group.id)
    assert len(WorkflowPermissionService.get_owner_ids(workflow)) == 1
    assert WorkflowPermissionService.has_manage(user, workflow)
    assert len(
        WorkflowPermissionService.get_owner_ids(
            template_account_another,
        ),
    ) == 0
    assert len(
        WorkflowPermissionService.get_owner_ids(
            workflow_account_another,
        ),
    ) == 0


def test__update_group_owner_user_in_owners_and_members__ok():

    # arrange
    account = create_test_account()
    user = create_test_user(account=account)
    template = create_test_template(
        user=user,
        is_active=True,
        tasks_count=1,
    )
    TemplateOwner.objects.filter(user_id=user.id).delete()
    group = create_test_group(account, users=[user])
    TemplateOwner.objects.create(
        template=template,
        account=account,
        type=OwnerType.GROUP,
        group_id=group.id,
    )
    workflow = create_test_workflow(
        user=user,
        template=template,
    )

    # act
    update_workflow_owners([template.id])

    # assert
    assert len(WorkflowPermissionService.get_owner_ids(workflow)) == 1
    assert WorkflowPermissionService.has_manage(user, workflow)
    assert len(WorkflowPermissionService.get_viewer_ids(workflow)) == 1
    assert WorkflowPermissionService.has_view(user, workflow)


def test__update_group_owner_new_user_one_owner_two_members__ok():
    """When a group owns a template and its users change, workflow has one
    owner and two members."""
    # arrange
    account = create_test_account()
    user = create_test_user(account=account)
    user_2 = create_test_user(
        account=account,
        email='master@test.test',
    )
    template = create_test_template(
        user=user,
        is_active=True,
        tasks_count=1,
    )
    TemplateOwner.objects.filter(user_id=user.id).delete()
    group = create_test_group(account, users=[user])
    TemplateOwner.objects.create(
        template=template,
        account=account,
        type=OwnerType.GROUP,
        group_id=group.id,
    )
    workflow = create_test_workflow(
        user=user,
        template=template,
    )
    group.users.set([user_2])
    group.save()

    # act
    update_workflow_owners([template.id])

    # assert
    assert len(WorkflowPermissionService.get_owner_ids(workflow)) == 1
    assert WorkflowPermissionService.has_manage(user_2, workflow)
    assert len(WorkflowPermissionService.get_viewer_ids(workflow)) == 2
    assert WorkflowPermissionService.has_view(user, workflow)
    assert WorkflowPermissionService.has_view(user_2, workflow)


def test__add_group_in_taskperformer__ok():
    # arrange
    account = create_test_account()
    user = create_test_user(account=account)
    user_in_group = create_test_user(
        account=account,
        email='groupuser@test.test',
    )
    template = create_test_template(
        user=user,
        is_active=True,
        tasks_count=1,
    )
    workflow = create_test_workflow(
        user=user,
        template=template,
    )
    group = create_test_group(account, users=[user_in_group])
    task = workflow.tasks.first()
    TaskPerformer.objects.create(
        task=task,
        group=group,
        type=PerformerType.GROUP,
    )

    # act
    update_workflow_owners([template.id])

    # assert
    assert WorkflowPermissionService.has_view(user_in_group, workflow)


def test__add_user_in_taskperformer__ok():
    # arrange
    account = create_test_account()
    user = create_test_user(account=account)
    task_performer_user = create_test_user(
        account=account,
        email='taskperformer@test.test',
    )
    template = create_test_template(
        user=user,
        is_active=True,
        tasks_count=1,
    )
    workflow = create_test_workflow(
        user=user,
        template=template,
    )
    task = workflow.tasks.first()
    TaskPerformer.objects.create(
        task=task,
        user=task_performer_user,
        type=PerformerType.USER,
    )

    # act
    update_workflow_owners([template.id])

    # assert
    assert WorkflowPermissionService.has_view(task_performer_user, workflow)


def test__add_group_and_user_in_taskperformer__ok():
    # arrange
    account = create_test_account()
    user = create_test_user(account=account)
    group_user = create_test_user(
        account=account,
        email='groupuser@test.test',
    )
    direct_user = create_test_user(
        account=account,
        email='directuser@test.test',
    )
    template = create_test_template(
        user=user,
        is_active=True,
        tasks_count=1,
    )
    workflow = create_test_workflow(
        user=user,
        template=template,
    )
    group = create_test_group(account, users=[group_user])
    task = workflow.tasks.first()
    TaskPerformer.objects.create(
        task=task,
        group=group,
        type=PerformerType.GROUP,
    )
    TaskPerformer.objects.create(
        task=task,
        user=direct_user,
        type=PerformerType.USER,
    )

    # act
    update_workflow_owners([template.id])

    # assert
    assert WorkflowPermissionService.has_view(group_user, workflow)
    assert WorkflowPermissionService.has_view(direct_user, workflow)


def test__add_user_in_owner_and_taskperformer__ok():
    # arrange
    account = create_test_account()
    user = create_test_user(account=account)
    common_user = create_test_user(
        account=account,
        email='common@test.test',
    )
    template = create_test_template(
        user=user,
        is_active=True,
        tasks_count=1,
    )
    TemplateOwner.objects.create(
        template=template,
        account=account,
        type=OwnerType.USER,
        user=common_user,
    )
    workflow = create_test_workflow(
        user=user,
        template=template,
    )
    task = workflow.tasks.first()
    TaskPerformer.objects.create(
        task=task,
        user=common_user,
        type=PerformerType.USER,
    )

    # act
    update_workflow_owners([template.id])

    # assert
    has_view = WorkflowPermissionService.has_view(
        common_user, workflow,
    )
    assert (1 if has_view else 0) == 1


def test__add_performer_with_status_deleted__ok():
    # arrange
    account = create_test_account()
    user = create_test_user(account=account)
    deleted_performer = create_test_user(
        account=account,
        email='deleted@test.test',
    )
    template = create_test_template(
        user=user,
        is_active=True,
        tasks_count=1,
    )
    workflow = create_test_workflow(
        user=user,
        template=template,
    )
    task = workflow.tasks.first()
    TaskPerformer.objects.create(
        task=task,
        user=deleted_performer,
        type=PerformerType.USER,
        directly_status=DirectlyStatus.DELETED,
    )

    # act
    update_workflow_owners([template.id])

    # assert
    assert not WorkflowPermissionService.has_view(deleted_performer, workflow)


def test__update_group_taskperformer_add_members__ok(api_client):
    # arrange
    account = create_test_account()
    user = create_test_user(account=account)
    user_in_group = create_test_user(
        account=account,
        email='groupuser@test.test',
    )
    template = create_test_template(
        user=user,
        is_active=True,
        tasks_count=1,
    )
    workflow = create_test_workflow(
        user=user,
        template=template,
    )
    group = create_test_group(account)
    task = workflow.tasks.first()
    TaskPerformer.objects.create(
        task=task,
        group=group,
        type=PerformerType.GROUP,
    )
    update_workflow_owners([template.id])
    group.users.set([user, user_in_group])
    group.save()

    # act
    update_workflow_owners([template.id])

    # assert
    assert WorkflowPermissionService.has_view(user_in_group, workflow)
