import pytest
from django.contrib.auth import get_user_model
from src.authentication.enums import AuthTokenType
from src.processes.models.workflows.workflow import Workflow
from src.processes.models.workflows.task import TaskPerformer
from src.processes.services.versioning.schemas import TemplateSchemaV1
from src.processes.services.versioning.versioning import (
    TemplateVersioningService,
)
from src.processes.tasks.update_workflow import update_workflows
from src.processes.tests.fixtures import (
    create_test_user,
    create_test_group,
    create_test_template,
    create_test_workflow,
)
from src.processes.enums import (
    PerformerType,
)


UserModel = get_user_model()
pytestmark = pytest.mark.django_db


def test_update_workflows__ok(api_client):

    user = create_test_user()
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

    update_workflows(
        template_id=template.id,
        version=template.version,
        updated_by=user.id,
        auth_type=AuthTokenType.USER,
        is_superuser=True,
    )

    workflow = Workflow.objects.get(id=workflow_id)
    task = workflow.tasks.get(number=1)
    assert workflow.version == template.version
    assert task.name == 'New task name'


def test_update_workflows__add_group__ok():
    # arrange
    user = create_test_user()
    another_user = create_test_user(
        account=user.account,
        email='another@pneumatic.app',
    )
    group = create_test_group(user.account, users=[another_user])
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


def test_update_workflows__template_version_difference__ok(api_client):
    user = create_test_user()
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

    update_workflows(
        template_id=template.id,
        version=template.version-1,
        updated_by=user.id,
        auth_type=AuthTokenType.USER,
        is_superuser=True,
    )
    workflow.refresh_from_db()
    assert workflow.version == version
    task.refresh_from_db()
    assert task.name == task_name


def test_update_workflows__process_version_difference__ok(api_client):
    user = create_test_user()
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

    update_workflows(
        template_id=template.id,
        version=template.version,
        updated_by=user.id,
        auth_type=AuthTokenType.USER,
        is_superuser=True,
    )
    workflow.refresh_from_db()

    assert workflow.version == version
    task.refresh_from_db()
    assert task.name == task_name
