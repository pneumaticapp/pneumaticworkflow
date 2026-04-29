import pytest

from src.processes.enums import (
    FieldType,
    PerformerType,
    TaskStatus,
)
from src.processes.models.hierarchy import (
    TaskHierarchyContext,
    TaskTemplateHierarchyConfig,
)
from src.processes.models.workflows.fields import (
    FieldSelection,
    TaskField,
)
from src.processes.services.hierarchy import HierarchyService
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_owner,
    create_test_not_admin,
    create_test_template,
    create_test_workflow,
)

pytestmark = pytest.mark.django_db


# ==========================================
# get_config_for_task
# ==========================================


def test_get_config__has_config__ok():

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    template = create_test_template(
        user=owner,
        is_active=True,
    )
    task_template = template.tasks.first()
    workflow = create_test_workflow(
        user=owner,
        template=template,
    )
    task = workflow.tasks.get(
        api_name=task_template.api_name,
    )
    config = TaskTemplateHierarchyConfig.objects.create(
        task_template=task_template,
        account=account,
        max_depth=5,
    )

    # act
    result = HierarchyService.get_config_for_task(
        task=task,
    )

    # assert
    assert result is not None
    assert result.id == config.id
    assert result.max_depth == 5


def test_get_config__no_config__none():

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    task = workflow.tasks.first()

    # act
    result = HierarchyService.get_config_for_task(
        task=task,
    )

    # assert
    assert result is None


def test_get_config__deleted__none():

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    template = create_test_template(
        user=owner,
        is_active=True,
    )
    task_template = template.tasks.first()
    workflow = create_test_workflow(
        user=owner,
        template=template,
    )
    task = workflow.tasks.get(
        api_name=task_template.api_name,
    )
    TaskTemplateHierarchyConfig.objects.create(
        task_template=task_template,
        account=account,
        max_depth=3,
        is_deleted=True,
    )

    # act
    result = HierarchyService.get_config_for_task(
        task=task,
    )

    # assert
    assert result is None


# ==========================================
# get_context
# ==========================================


def test_get_context__has_context__ok():

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    task = workflow.tasks.first()
    context = TaskHierarchyContext.objects.create(
        task=task,
        account=account,
        base_api_name=task.api_name,
        current_depth=1,
        max_depth=5,
    )

    # act
    result = HierarchyService.get_context(task=task)

    # assert
    assert result is not None
    assert result.id == context.id
    assert result.current_depth == 1


def test_get_context__no_context__none():

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    task = workflow.tasks.first()

    # act
    result = HierarchyService.get_context(task=task)

    # assert
    assert result is None


# ==========================================
# should_spawn_next
# ==========================================


def test_should_spawn__no_config_no_ctx__none():

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    task = workflow.tasks.first()

    # act
    result = HierarchyService.should_spawn_next(
        task=task,
    )

    # assert
    assert result is None


def test_should_spawn__depth_reached__none():

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    task = workflow.tasks.first()
    TaskHierarchyContext.objects.create(
        task=task,
        account=account,
        base_api_name=task.api_name,
        current_depth=3,
        max_depth=3,
    )

    # act
    result = HierarchyService.should_spawn_next(
        task=task,
    )

    # assert
    assert result is None


def test_should_spawn__no_anchor_user__none():

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    template = create_test_template(
        user=owner,
        is_active=True,
        tasks_count=1,
    )
    task_template = template.tasks.first()
    TaskTemplateHierarchyConfig.objects.create(
        task_template=task_template,
        account=account,
        max_depth=5,
    )
    workflow = create_test_workflow(
        user=owner,
        template=template,
    )
    task = workflow.tasks.first()

    # remove raw performers to simulate no anchor
    task.raw_performers.all().delete()

    # act
    result = HierarchyService.should_spawn_next(
        task=task,
    )

    # assert
    assert result is None


def test_should_spawn__no_manager__none():

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    template = create_test_template(
        user=owner,
        is_active=True,
        tasks_count=1,
    )
    task_template = template.tasks.first()
    TaskTemplateHierarchyConfig.objects.create(
        task_template=task_template,
        account=account,
        max_depth=5,
    )
    workflow = create_test_workflow(
        user=owner,
        template=template,
    )
    task = workflow.tasks.first()

    # act
    result = HierarchyService.should_spawn_next(
        task=task,
    )

    # assert
    assert result is None


def test_should_spawn__has_mgr__return_user():

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    mgr = create_test_not_admin(
        account=account,
        email='manager@pneumatic.app',
    )
    owner.manager = mgr
    owner.save(update_fields=['manager'])

    template = create_test_template(
        user=owner,
        is_active=True,
        tasks_count=1,
    )
    task_template = template.tasks.first()
    TaskTemplateHierarchyConfig.objects.create(
        task_template=task_template,
        account=account,
        max_depth=5,
    )
    workflow = create_test_workflow(
        user=owner,
        template=template,
    )
    task = workflow.tasks.first()

    # act
    result = HierarchyService.should_spawn_next(
        task=task,
    )

    # assert
    assert result is not None
    assert result.id == owner.id


def test_should_spawn__ctx_under_limit__return_user():

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    mgr = create_test_not_admin(
        account=account,
        email='manager2@pneumatic.app',
    )
    owner.manager = mgr
    owner.save(update_fields=['manager'])

    workflow = create_test_workflow(user=owner)
    task = workflow.tasks.first()

    # add raw_performer for owner
    task.add_raw_performer(
        user=owner,
        performer_type=PerformerType.USER,
    )

    TaskHierarchyContext.objects.create(
        task=task,
        account=account,
        base_api_name=task.api_name,
        current_depth=2,
        max_depth=5,
    )

    # act
    result = HierarchyService.should_spawn_next(
        task=task,
    )

    # assert
    assert result is not None
    assert result.id == owner.id


def test_should_spawn__unlimited_depth__return_user():

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    mgr = create_test_not_admin(
        account=account,
        email='mgr_unlim@pneumatic.app',
    )
    owner.manager = mgr
    owner.save(update_fields=['manager'])

    workflow = create_test_workflow(user=owner)
    task = workflow.tasks.first()

    # add raw_performer for owner
    task.add_raw_performer(
        user=owner,
        performer_type=PerformerType.USER,
    )

    # max_depth=None means unlimited
    TaskHierarchyContext.objects.create(
        task=task,
        account=account,
        base_api_name=task.api_name,
        current_depth=40,
        max_depth=None,
    )

    # act
    result = HierarchyService.should_spawn_next(
        task=task,
    )

    # assert
    assert result is not None
    assert result.id == owner.id


# ==========================================
# create_hierarchy_task
# ==========================================


def test_create_task__first_clone__ok(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    mgr = create_test_not_admin(
        account=account,
        email='mgr_clone@pneumatic.app',
    )
    owner.manager = mgr
    owner.save(update_fields=['manager'])

    template = create_test_template(
        user=owner,
        is_active=True,
        tasks_count=1,
    )
    task_template = template.tasks.first()
    TaskTemplateHierarchyConfig.objects.create(
        task_template=task_template,
        account=account,
        max_depth=5,
    )
    workflow = create_test_workflow(
        user=owner,
        template=template,
    )
    task = workflow.tasks.first()
    base_api_name = task.api_name
    markdown_clear_mock = mocker.patch(
        'src.processes.services.hierarchy'
        '.MarkdownService.clear',
        return_value='',
    )

    # act
    clone = HierarchyService.create_hierarchy_task(
        source_task=task,
        anchor_user=owner,
    )

    # assert
    assert clone is not None
    assert clone.api_name == f'{base_api_name}-h2'
    assert clone.status == TaskStatus.PENDING
    assert clone.number == task.number
    assert '(L2)' in clone.name

    # context created for source and clone
    src_ctx = TaskHierarchyContext.objects.get(
        task=task,
    )
    assert src_ctx.current_depth == 1
    assert src_ctx.base_api_name == base_api_name

    clone_ctx = TaskHierarchyContext.objects.get(
        task=clone,
    )
    assert clone_ctx.current_depth == 2
    assert clone_ctx.base_api_name == base_api_name
    assert clone_ctx.max_depth == 5

    # performer is the manager
    perf = clone.raw_performers.first()
    assert perf.user_id == mgr.id
    markdown_clear_mock.assert_called_once_with(
        task.description_template,
    )


def test_create_task__chained_clone__ok(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    mgr = create_test_not_admin(
        account=account,
        email='mgr_chain@pneumatic.app',
    )
    owner.manager = mgr
    owner.save(update_fields=['manager'])

    workflow = create_test_workflow(user=owner)
    task = workflow.tasks.first()
    base_api = task.api_name
    markdown_clear_mock = mocker.patch(
        'src.processes.services.hierarchy'
        '.MarkdownService.clear',
        return_value='',
    )

    # simulate existing chain context (depth 2)
    TaskHierarchyContext.objects.create(
        task=task,
        account=account,
        base_api_name=base_api,
        current_depth=2,
        max_depth=10,
    )

    # act
    clone = HierarchyService.create_hierarchy_task(
        source_task=task,
        anchor_user=owner,
    )

    # assert
    assert clone.api_name == f'{base_api}-h3'
    assert '(L3)' in clone.name

    clone_ctx = TaskHierarchyContext.objects.get(
        task=clone,
    )
    assert clone_ctx.current_depth == 3
    assert clone_ctx.base_api_name == base_api
    markdown_clear_mock.assert_called_once_with(
        task.description_template,
    )


def test_create_task__appends_source_fields__ok(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    mgr = create_test_not_admin(
        account=account,
        email='mgr_fields@pneumatic.app',
    )
    owner.manager = mgr
    owner.save(update_fields=['manager'])

    template = create_test_template(
        user=owner,
        is_active=True,
        tasks_count=1,
    )
    task_template = template.tasks.first()
    TaskTemplateHierarchyConfig.objects.create(
        task_template=task_template,
        account=account,
    )
    workflow = create_test_workflow(
        user=owner,
        template=template,
    )
    task = workflow.tasks.first()
    task.description_template = 'Original desc\n'
    task.clear_description = 'Original desc\n'
    task.save(update_fields=['description_template', 'clear_description'])
    markdown_clear_mock = mocker.patch(
        'src.processes.services.hierarchy'
        '.MarkdownService.clear',
        return_value='Original desc\n',
    )

    # add an output field with a selection
    TaskField.objects.create(
        account=account,
        workflow=workflow,
        task=task,
        api_name='approval-field-1',
        name='Decision',
        type=FieldType.RADIO,
        order=0,
        value='Approve',
        clear_value='Approve',
        markdown_value='Approve',
    )

    # act
    clone = HierarchyService.create_hierarchy_task(
        source_task=task,
        anchor_user=owner,
    )

    # assert
    clone_fields = TaskField.objects.filter(
        task=clone,
    )
    assert clone_fields.count() == 1
    clone_field = clone_fields.first()
    assert clone_field.name == 'Approval'
    assert clone_field.type == FieldType.RADIO

    # selections cloned
    clone_sels = FieldSelection.objects.filter(
        field=clone_field,
    )
    assert clone_sels.count() == 2
    assert clone_sels.filter(value='Approved').exists()
    assert clone_sels.filter(value='Rejected').exists()

    assert 'Original desc' in clone.description_template
    assert '**Decision**: Approve' in clone.description_template
    assert '- Decision: Approve' in clone.clear_description

    markdown_clear_mock.assert_called_once_with(
        task.description_template,
    )


def test_create_task__no_fields__ok(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    mgr = create_test_not_admin(
        account=account,
        email='mgr_nofld@pneumatic.app',
    )
    owner.manager = mgr
    owner.save(update_fields=['manager'])

    template = create_test_template(
        user=owner,
        is_active=True,
        tasks_count=1,
    )
    task_template = template.tasks.first()
    TaskTemplateHierarchyConfig.objects.create(
        task_template=task_template,
        account=account,
    )
    workflow = create_test_workflow(
        user=owner,
        template=template,
    )
    task = workflow.tasks.first()
    markdown_clear_mock = mocker.patch(
        'src.processes.services.hierarchy'
        '.MarkdownService.clear',
        return_value='',
    )

    # act
    clone = HierarchyService.create_hierarchy_task(
        source_task=task,
        anchor_user=owner,
    )

    # assert
    clone_fields = TaskField.objects.filter(
        task=clone,
    )
    assert clone_fields.count() == 1
    clone_field = clone_fields.first()
    assert clone_field.name == 'Approval'
    assert clone_field.type == FieldType.RADIO
    markdown_clear_mock.assert_called_once_with(
        task.description_template,
    )


# ==========================================
# build_approval_chain_summaries
# ==========================================


def test_build_summaries__no_ctx__empty():

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)

    # act
    result = (
        HierarchyService
        .build_approval_chain_summaries(
            workflow=workflow,
        )
    )

    # assert
    assert result == {}


def test_build_summaries__completed_tasks__ok():

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    task = workflow.tasks.first()
    task.status = TaskStatus.COMPLETED
    task.save(update_fields=['status'])

    TaskHierarchyContext.objects.create(
        task=task,
        account=account,
        base_api_name='step-approval',
        current_depth=1,
        max_depth=3,
    )

    # add output field with value
    TaskField.objects.create(
        account=account,
        workflow=workflow,
        task=task,
        api_name='decision-h1',
        name='Decision',
        type=FieldType.STRING,
        value='Approved',
        order=0,
    )

    # act
    result = (
        HierarchyService
        .build_approval_chain_summaries(
            workflow=workflow,
        )
    )

    # assert
    assert 'step-approval' in result
    summary = result['step-approval']
    assert 'Level 1' in summary
    assert 'Decision: Approved' in summary


def test_build_summaries__skip_non_completed__ok():

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(
        user=owner,
        tasks_count=2,
    )
    tasks = list(
        workflow.tasks.order_by('number'),
    )

    # first task completed
    tasks[0].status = TaskStatus.COMPLETED
    tasks[0].save(update_fields=['status'])
    TaskHierarchyContext.objects.create(
        task=tasks[0],
        account=account,
        base_api_name='step-x',
        current_depth=1,
    )

    # second task active (not completed)
    tasks[1].status = TaskStatus.ACTIVE
    tasks[1].save(update_fields=['status'])
    TaskHierarchyContext.objects.create(
        task=tasks[1],
        account=account,
        base_api_name='step-x',
        current_depth=2,
    )

    # act
    result = (
        HierarchyService
        .build_approval_chain_summaries(
            workflow=workflow,
        )
    )

    # assert
    summary = result.get('step-x', '')
    assert 'Level 1' in summary
    assert 'Level 2' not in summary


def test_build_summaries__empty_value__dash():

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    task = workflow.tasks.first()
    task.status = TaskStatus.COMPLETED
    task.save(update_fields=['status'])

    TaskHierarchyContext.objects.create(
        task=task,
        account=account,
        base_api_name='step-null',
        current_depth=1,
    )

    # field with empty value (default '')
    TaskField.objects.create(
        account=account,
        workflow=workflow,
        task=task,
        api_name='empty-field',
        name='Notes',
        type=FieldType.STRING,
        order=0,
    )

    # act
    result = (
        HierarchyService
        .build_approval_chain_summaries(
            workflow=workflow,
        )
    )

    # assert
    assert 'step-null' in result
    summary = result['step-null']
    assert 'Notes: \u2014' in summary


# ==========================================
# _truncate_api_name
# ==========================================


def test_truncate__short__unchanged():

    # arrange
    base = 'task-1'
    suffix = '-h2'

    # act
    result = HierarchyService._truncate_api_name(
        base=base,
        suffix=suffix,
    )

    # assert
    assert result == 'task-1-h2'


def test_truncate__overflow__trimmed():

    # arrange
    base = 'a' * 198

    # act
    result = HierarchyService._truncate_api_name(
        base=base,
        suffix='-h2',
        max_length=200,
    )

    # assert
    assert len(result) == 200
    assert result.endswith('-h2')
