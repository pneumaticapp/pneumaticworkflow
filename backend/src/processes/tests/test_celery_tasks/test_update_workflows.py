import pytest
from django.contrib.auth import get_user_model

from src.authentication.enums import AuthTokenType
from src.processes.enums import (
    OwnerType,
    PerformerType,
    WorkflowStatus,
)
from src.processes.models.templates.owner import TemplateOwner
from src.processes.models.workflows.task import TaskPerformer
from src.processes.models.workflows.workflow import Workflow
from src.processes.services.versioning.schemas import TemplateSchemaV1
from src.processes.services.versioning.versioning import (
    TemplateVersioningService,
)
from src.processes.services.workflow_permissions import (
    WorkflowPermissionService,
)
from src.processes.tasks.update_workflow import update_workflows
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_admin,
    create_test_group,
    create_test_owner,
    create_test_template,
    create_test_workflow,
)

UserModel = get_user_model()
pytestmark = pytest.mark.django_db


def test_update_workflows__ok(api_client):

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(
        user=user,
        is_active=True,
        tasks_count=1,
    )
    api_client.token_authenticate(user)
    workflow_id = api_client.post(
        f'/templates/{template.id}/run',
        data={
            'name': 'Test workflow',
        },
    ).data['id']
    first_task = template.tasks.get(number=1)
    first_task.name = 'New task name'
    first_task.save()
    template.version += 1
    template.save()
    TemplateVersioningService(TemplateSchemaV1).save(template)

    # act
    update_workflows(
        template_id=template.id,
        version=template.version,
        updated_by=user.id,
        auth_type=AuthTokenType.USER,
        is_superuser=True,
    )

    # assert
    workflow = Workflow.objects.get(id=workflow_id)
    task = workflow.tasks.get(number=1)
    assert workflow.version == template.version
    assert task.name == 'New task name'


def test_update_workflows__add_group__ok():

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    another_user = create_test_admin(
        account=account,
        email='another@pneumatic.app',
    )
    group = create_test_group(
        account=account,
        users=[another_user],
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

    first_task = template.tasks.get(number=1)
    first_task.add_raw_performer(
        group=group,
        performer_type=PerformerType.GROUP,
    )
    first_task.save()
    template.version += 1
    template.save()
    TemplateVersioningService(TemplateSchemaV1).save(template)

    # act
    update_workflows(
        template_id=template.id,
        version=template.version,
        updated_by=user.id,
        auth_type=AuthTokenType.USER,
        is_superuser=True,
    )

    # assert
    workflow = Workflow.objects.get(id=workflow.id)
    task = workflow.tasks.get(number=1)
    performers = TaskPerformer.objects.filter(task=task)
    group_performer = performers.filter(
        type=PerformerType.GROUP,
        group_id=group.id,
    ).first()
    assert workflow.version == template.version
    assert group_performer is not None
    assert group_performer.group_id == group.id


def test_update_workflows__template_version_difference__ok(
    api_client,
):

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(
        user=user,
        is_active=True,
        tasks_count=1,
    )
    api_client.token_authenticate(user)
    workflow_id = api_client.post(
        f'/templates/{template.id}/run',
        data={
            'name': 'Test workflow',
        },
    ).data['id']
    workflow = Workflow.objects.get(id=workflow_id)
    version = workflow.version
    task = workflow.tasks.get(number=1)
    task_name = task.name

    first_task = template.tasks.get(number=1)
    first_task.name = 'New task name'
    first_task.save()
    template.version += 1
    template.save()
    TemplateVersioningService(TemplateSchemaV1).save(template)

    # act
    update_workflows(
        template_id=template.id,
        version=template.version - 1,
        updated_by=user.id,
        auth_type=AuthTokenType.USER,
        is_superuser=True,
    )

    # assert
    workflow.refresh_from_db()
    assert workflow.version == version
    task.refresh_from_db()
    assert task.name == task_name


def test_update_workflows__process_version_difference__ok(
    api_client,
):

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(
        user=user,
        is_active=True,
        tasks_count=1,
    )
    api_client.token_authenticate(user)
    workflow_id = api_client.post(
        f'/templates/{template.id}/run',
        data={
            'name': 'Test workflow',
        },
    ).data['id']
    workflow = Workflow.objects.get(id=workflow_id)
    workflow.version += 5
    workflow.save()
    version = workflow.version
    task = workflow.tasks.get(number=1)
    task_name = task.name

    first_task = template.tasks.get(number=1)
    first_task.name = 'New task name'
    first_task.save()
    template.version += 1
    template.save()
    TemplateVersioningService(TemplateSchemaV1).save(template)

    # act
    update_workflows(
        template_id=template.id,
        version=template.version,
        updated_by=user.id,
        auth_type=AuthTokenType.USER,
        is_superuser=True,
    )

    # assert
    workflow.refresh_from_db()
    assert workflow.version == version
    task.refresh_from_db()
    assert task.name == task_name


def test_update_workflows__done_wf__sets_owners_and_sync(
    mocker,
):

    # arrange
    schedule_sync_mock = mocker.patch(
        'src.processes.tasks.update_workflow.'
        'schedule_sync_workflow_attachment_permissions',
    )
    account = create_test_account()
    owner = create_test_owner(account=account)
    new_owner = create_test_admin(
        account=account,
        email='new_owner@pneumatic.app',
    )
    template = create_test_template(
        user=owner,
        is_active=True,
        tasks_count=1,
    )
    workflow = create_test_workflow(
        user=owner,
        template=template,
    )
    workflow.status = WorkflowStatus.DONE
    workflow.save(update_fields=['status'])
    old_version = workflow.version
    TemplateOwner.objects.create(
        template=template,
        account=account,
        type=OwnerType.USER,
        user_id=new_owner.id,
    )
    template.version += 1
    template.save()
    TemplateVersioningService(TemplateSchemaV1).save(template)

    # act
    update_workflows(
        template_id=template.id,
        version=template.version,
        updated_by=owner.id,
        auth_type=AuthTokenType.USER,
        is_superuser=False,
    )

    # assert
    workflow.refresh_from_db()
    assert workflow.version == old_version
    perm_svc = WorkflowPermissionService(workflow)
    assert perm_svc.has_change(user=owner)
    assert perm_svc.has_change(user=new_owner)
    schedule_sync_mock.assert_called_once_with(workflow.id)


def test_update_workflows__skips_current_continues_others(
    mocker,
):

    # arrange
    schedule_sync_mock = mocker.patch(
        'src.processes.tasks.update_workflow.'
        'schedule_sync_workflow_attachment_permissions',
    )
    account = create_test_account()
    owner = create_test_owner(account=account)
    template = create_test_template(
        user=owner,
        is_active=True,
        tasks_count=1,
    )
    wf_current = create_test_workflow(
        user=owner,
        template=template,
    )
    wf_outdated = create_test_workflow(
        user=owner,
        template=template,
    )
    first_task = template.tasks.get(number=1)
    first_task.name = 'Updated task name'
    first_task.save()
    template.version += 1
    template.save()
    TemplateVersioningService(TemplateSchemaV1).save(template)
    wf_current.version = template.version
    wf_current.save(update_fields=['version'])

    # act
    update_workflows(
        template_id=template.id,
        version=template.version,
        updated_by=owner.id,
        auth_type=AuthTokenType.USER,
        is_superuser=False,
    )

    # assert
    wf_current.refresh_from_db()
    wf_outdated.refresh_from_db()
    assert wf_current.version == template.version
    assert wf_outdated.version == template.version
    outdated_task = wf_outdated.tasks.get(number=1)
    assert outdated_task.name == 'Updated task name'
    schedule_sync_mock.assert_not_called()
