import pytest

from src.permissions import messages
from src.permissions.enums import (
    PermissionObjectType,
    PermissionSource,
)
from src.permissions.exceptions import (
    UserObjectPermissionServiceException,
)
from src.permissions.services import UserObjectPermissionService
from src.processes.enums import OwnerRole, OwnerType
from src.processes.models.templates.owner import TemplateOwner
from src.processes.services.workflow_permissions import (
    WorkflowPermissionService,
)
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_admin,
    create_test_group,
    create_test_not_admin,
    create_test_owner,
    create_test_template,
    create_test_workflow,
)

pytestmark = pytest.mark.django_db


def test_get_permissions__account_owner__all_true():

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner, tasks_count=1)
    service = UserObjectPermissionService(user=owner)

    # act
    result = service.get_permissions(
        obj_type=PermissionObjectType.WORKFLOW,
        obj_ids=[workflow.id],
    )

    # assert
    assert len(result) == 1
    assert result[0]['id'] == workflow.id
    assert result[0]['has_view'] is True
    assert result[0]['has_change'] is True


def test_get_permissions__account_owner_foreign_workflow__all_false():

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    foreign_account = create_test_account(name='Foreign')
    foreign_owner = create_test_owner(
        account=foreign_account,
        email='foreign@pneumatic.app',
    )
    workflow = create_test_workflow(user=foreign_owner, tasks_count=1)
    service = UserObjectPermissionService(user=owner)

    # act
    result = service.get_permissions(
        obj_type=PermissionObjectType.WORKFLOW,
        obj_ids=[workflow.id],
    )

    # assert
    assert len(result) == 1
    assert result[0]['id'] == workflow.id
    assert result[0]['has_view'] is False
    assert result[0]['has_change'] is False


def test_get_permissions__admin_template_owner__view_and_change():

    # arrange
    account = create_test_account()
    admin = create_test_admin(account=account)
    workflow = create_test_workflow(user=admin, tasks_count=1)
    service = UserObjectPermissionService(user=admin)

    # act
    result = service.get_permissions(
        obj_type=PermissionObjectType.WORKFLOW,
        obj_ids=[workflow.id],
    )

    # assert
    assert len(result) == 1
    assert result[0]['id'] == workflow.id
    assert result[0]['has_view'] is True
    assert result[0]['has_change'] is True


def test_get_permissions__admin_group_template_owner__view_and_change():

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    admin = create_test_admin(account=account)
    group = create_test_group(account, users=[admin])
    template = create_test_template(
        user=owner,
        is_active=True,
        tasks_count=1,
    )
    TemplateOwner.objects.create(
        role=OwnerRole.OWNER,
        template=template,
        account=account,
        type=OwnerType.GROUP,
        group=group,
    )
    workflow = create_test_workflow(user=owner, template=template)
    service = UserObjectPermissionService(user=admin)

    # act
    result = service.get_permissions(
        obj_type=PermissionObjectType.WORKFLOW,
        obj_ids=[workflow.id],
    )

    # assert
    assert len(result) == 1
    assert result[0]['id'] == workflow.id
    assert result[0]['has_view'] is True
    assert result[0]['has_change'] is True


def test_get_permissions__not_admin_template_owner__view_only():

    # arrange
    account = create_test_account()
    user = create_test_not_admin(account=account)
    workflow = create_test_workflow(user=user, tasks_count=1)
    service = UserObjectPermissionService(user=user)

    # act
    result = service.get_permissions(
        obj_type=PermissionObjectType.WORKFLOW,
        obj_ids=[workflow.id],
    )

    # assert
    assert len(result) == 1
    assert result[0]['id'] == workflow.id
    assert result[0]['has_view'] is True
    assert result[0]['has_change'] is False


def test_get_permissions__performer_view_grant__view_only():

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    admin = create_test_admin(account=account)
    workflow = create_test_workflow(user=owner, tasks_count=1)
    task = workflow.tasks.get(number=1)
    WorkflowPermissionService(workflow).grant_view(
        user=admin,
        source_type=PermissionSource.PERFORMER,
        source_id=task.id,
    )
    service = UserObjectPermissionService(user=admin)

    # act
    result = service.get_permissions(
        obj_type=PermissionObjectType.WORKFLOW,
        obj_ids=[workflow.id],
    )

    # assert
    assert len(result) == 1
    assert result[0]['id'] == workflow.id
    assert result[0]['has_view'] is True
    assert result[0]['has_change'] is False


def test_get_permissions__group_performer_view_grant__view_only():

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    admin = create_test_admin(account=account)
    group = create_test_group(account, users=[admin])
    workflow = create_test_workflow(user=owner, tasks_count=1)
    WorkflowPermissionService(workflow).grant_view(
        user=admin,
        source_type=PermissionSource.PERFORMER_GROUP,
        source_id=group.id,
    )
    service = UserObjectPermissionService(user=admin)

    # act
    result = service.get_permissions(
        obj_type=PermissionObjectType.WORKFLOW,
        obj_ids=[workflow.id],
    )

    # assert
    assert len(result) == 1
    assert result[0]['id'] == workflow.id
    assert result[0]['has_view'] is True
    assert result[0]['has_change'] is False


def test_get_permissions__template_viewer__view_only():

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    admin = create_test_admin(account=account)
    template = create_test_template(
        user=owner,
        is_active=True,
        tasks_count=1,
    )
    TemplateOwner.objects.create(
        role=OwnerRole.VIEWER,
        template=template,
        account=account,
        type=OwnerType.USER,
        user=admin,
    )
    workflow = create_test_workflow(user=owner, template=template)
    service = UserObjectPermissionService(user=admin)

    # act
    result = service.get_permissions(
        obj_type=PermissionObjectType.WORKFLOW,
        obj_ids=[workflow.id],
    )

    # assert
    assert len(result) == 1
    assert result[0]['id'] == workflow.id
    assert result[0]['has_view'] is True
    assert result[0]['has_change'] is False


def test_get_permissions__deleted_template_viewer__all_false():

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    admin = create_test_admin(account=account)
    template = create_test_template(
        user=owner,
        is_active=True,
        tasks_count=1,
    )
    TemplateOwner.objects.create(
        role=OwnerRole.VIEWER,
        template=template,
        account=account,
        type=OwnerType.USER,
        user=admin,
        is_deleted=True,
    )
    workflow = create_test_workflow(user=owner, template=template)
    service = UserObjectPermissionService(user=admin)

    # act
    result = service.get_permissions(
        obj_type=PermissionObjectType.WORKFLOW,
        obj_ids=[workflow.id],
    )

    # assert
    assert len(result) == 1
    assert result[0]['id'] == workflow.id
    assert result[0]['has_view'] is False
    assert result[0]['has_change'] is False


def test_get_permissions__starter_started_workflow__view_only():

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    admin = create_test_admin(account=account)
    template = create_test_template(
        user=owner,
        is_active=True,
        tasks_count=1,
    )
    TemplateOwner.objects.create(
        role=OwnerRole.STARTER,
        template=template,
        account=account,
        type=OwnerType.USER,
        user=admin,
    )
    workflow = create_test_workflow(user=owner, template=template)
    workflow.workflow_starter = admin
    workflow.save(update_fields=['workflow_starter'])
    service = UserObjectPermissionService(user=admin)

    # act
    result = service.get_permissions(
        obj_type=PermissionObjectType.WORKFLOW,
        obj_ids=[workflow.id],
    )

    # assert
    assert len(result) == 1
    assert result[0]['id'] == workflow.id
    assert result[0]['has_view'] is True
    assert result[0]['has_change'] is False


def test_get_permissions__starter_not_started_workflow__all_false():

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    admin = create_test_admin(account=account)
    template = create_test_template(
        user=owner,
        is_active=True,
        tasks_count=1,
    )
    TemplateOwner.objects.create(
        role=OwnerRole.STARTER,
        template=template,
        account=account,
        type=OwnerType.USER,
        user=admin,
    )
    workflow = create_test_workflow(user=owner, template=template)
    service = UserObjectPermissionService(user=admin)

    # act
    result = service.get_permissions(
        obj_type=PermissionObjectType.WORKFLOW,
        obj_ids=[workflow.id],
    )

    # assert
    assert len(result) == 1
    assert result[0]['id'] == workflow.id
    assert result[0]['has_view'] is False
    assert result[0]['has_change'] is False


def test_get_permissions__no_access__all_false():

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    admin = create_test_admin(account=account)
    workflow = create_test_workflow(user=owner, tasks_count=1)
    service = UserObjectPermissionService(user=admin)

    # act
    result = service.get_permissions(
        obj_type=PermissionObjectType.WORKFLOW,
        obj_ids=[workflow.id],
    )

    # assert
    assert len(result) == 1
    assert result[0]['id'] == workflow.id
    assert result[0]['has_view'] is False
    assert result[0]['has_change'] is False


def test_get_permissions__foreign_account__all_false():

    # arrange
    account = create_test_account()
    admin = create_test_admin(account=account)
    foreign_account = create_test_account(name='Foreign')
    foreign_owner = create_test_owner(
        account=foreign_account,
        email='foreign@pneumatic.app',
    )
    workflow = create_test_workflow(user=foreign_owner, tasks_count=1)
    service = UserObjectPermissionService(user=admin)

    # act
    result = service.get_permissions(
        obj_type=PermissionObjectType.WORKFLOW,
        obj_ids=[workflow.id],
    )

    # assert
    assert len(result) == 1
    assert result[0]['id'] == workflow.id
    assert result[0]['has_view'] is False
    assert result[0]['has_change'] is False


def test_get_permissions__not_existent_id__all_false():

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    service = UserObjectPermissionService(user=owner)

    # act
    result = service.get_permissions(
        obj_type=PermissionObjectType.WORKFLOW,
        obj_ids=[999999],
    )

    # assert
    assert len(result) == 1
    assert result[0]['id'] == 999999
    assert result[0]['has_view'] is False
    assert result[0]['has_change'] is False


def test_get_permissions__empty_ids__empty_list():

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    service = UserObjectPermissionService(user=owner)

    # act
    result = service.get_permissions(
        obj_type=PermissionObjectType.WORKFLOW,
        obj_ids=[],
    )

    # assert
    assert result == []


def test_get_permissions__multiple_ids__keep_order_and_dedupe():

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    admin = create_test_admin(account=account)
    workflow_1 = create_test_workflow(user=owner, tasks_count=1)
    workflow_2 = create_test_workflow(user=admin, tasks_count=1)
    service = UserObjectPermissionService(user=admin)

    # act
    result = service.get_permissions(
        obj_type=PermissionObjectType.WORKFLOW,
        obj_ids=[workflow_2.id, workflow_1.id, workflow_2.id],
    )

    # assert
    assert len(result) == 2
    assert result[0]['id'] == workflow_2.id
    assert result[0]['has_view'] is True
    assert result[0]['has_change'] is True
    assert result[1]['id'] == workflow_1.id
    assert result[1]['has_view'] is False
    assert result[1]['has_change'] is False


def test_get_permissions__unsupported_obj_type__raise_exception():

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    service = UserObjectPermissionService(user=owner)

    # act
    with pytest.raises(UserObjectPermissionServiceException) as ex:
        service.get_permissions(
            obj_type='template',
            obj_ids=[1],
        )

    # assert
    assert ex.value.message == messages.MSG_PM_0001('template')
