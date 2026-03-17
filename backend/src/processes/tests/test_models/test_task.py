import pytest

from datetime import timedelta

from django.utils import timezone

from src.processes.enums import (
    DirectlyStatus,
    FieldType,
    PerformerType,
    TaskStatus,
)
from src.processes.models.workflows.fields import TaskField
from src.processes.models.workflows.task import Delay, TaskPerformer
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_group,
    create_test_owner,
    create_test_not_admin,
    create_test_workflow,
)

pytestmark = pytest.mark.django_db


def test_str__with_id_and_name__ok():
    """
    Returns formatted string with id and name
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    workflow = create_test_workflow(
        user=user,
        tasks_count=1,
    )
    task = workflow.tasks.get(number=1)

    # act
    result = str(task)

    # assert
    assert result == f'(Task {task.id}) {task.name}'


def test_get_active_delay__has_active_delay__ok():
    """
    Returns the first active delay from delay_set
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    workflow = create_test_workflow(
        user=user,
        tasks_count=1,
        with_delay=False,
    )
    task = workflow.tasks.get(number=1)

    # act
    result = task.get_active_delay()

    # assert
    assert result is None


def test_get_active_delay__no_active_delay__none():
    """
    No active delay — returns None
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    workflow = create_test_workflow(
        user=user,
        tasks_count=1,
    )
    task = workflow.tasks.get(number=1)

    # act
    result = task.get_active_delay()

    # assert
    assert result is None


def test_get_last_delay__has_delays__ok():
    """
    Returns the delay with latest start_date
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    workflow = create_test_workflow(
        user=user,
        tasks_count=1,
    )
    task = workflow.tasks.get(number=1)

    # act
    result = task.get_last_delay()

    # assert
    assert result is None


def test_get_last_delay__no_delays__none():
    """
    No delays — returns None
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    workflow = create_test_workflow(
        user=user,
        tasks_count=1,
    )
    task = workflow.tasks.get(number=1)

    # act
    result = task.get_last_delay()

    # assert
    assert result is None


def test_exclude_directly_deleted_taskperformer_set__called__ok():
    """
    Returns queryset with directly-deleted performers excluded
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    workflow = create_test_workflow(
        user=user,
        tasks_count=1,
    )
    task = workflow.tasks.get(number=1)

    # act
    result = task.exclude_directly_deleted_taskperformer_set()

    # assert
    assert result is not None


def test_get_raw_performers_api_names__has_performers__ok():
    """
    Returns set of api_names from raw_performers
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    workflow = create_test_workflow(
        user=user,
        tasks_count=1,
    )
    task = workflow.tasks.get(number=1)

    # act
    result = task._get_raw_performers_api_names()

    # assert
    assert isinstance(result, set)
    assert len(result) > 0


def test_get_raw_performers_api_names__no_performers__empty_set():
    """
    No raw performers — returns empty set
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    workflow = create_test_workflow(
        user=user,
        tasks_count=1,
    )
    task = workflow.tasks.get(number=1)
    task.raw_performers.all().delete()

    # act
    result = task._get_raw_performers_api_names()

    # assert
    assert result == set()


def test_get_raw_performer__with_user__ok():
    """
    Creates RawPerformer with user object
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    workflow = create_test_workflow(
        user=user,
        tasks_count=1,
    )
    task = workflow.tasks.get(number=1)
    api_name = 'rp-test-1'

    # act
    result = task._get_raw_performer(
        api_name=api_name,
        performer_type=PerformerType.USER,
        user=user,
    )

    # assert
    assert result.api_name == api_name
    assert result.type == PerformerType.USER
    assert result.account == task.account
    assert result.task == task
    assert result.workflow == task.workflow
    assert result.user == user


def test_get_raw_performer__with_user_id__ok(mocker):
    """
    Creates RawPerformer with user_id
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    workflow = create_test_workflow(
        user=user,
        tasks_count=1,
    )
    task = workflow.tasks.get(number=1)
    api_name = 'rp-test-2'
    raw_performer_init_mock = mocker.patch(
        'src.processes.models.workflows.raw_performer'
        '.RawPerformer.__init__',
        return_value=None,
    )

    # act
    task._get_raw_performer(
        api_name=api_name,
        performer_type=PerformerType.USER,
        user_id=user.id,
    )

    # assert
    raw_performer_init_mock.assert_called_once_with(
        account=task.account,
        task=task,
        workflow=task.workflow,
        field=None,
        api_name=api_name,
        type=PerformerType.USER,
    )


def test_get_raw_performer__with_group_id__ok(mocker):
    """
    Creates RawPerformer with group_id
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    workflow = create_test_workflow(
        user=user,
        tasks_count=1,
    )
    task = workflow.tasks.get(number=1)
    api_name = 'rp-test-3'
    group_id = 99
    raw_performer_init_mock = mocker.patch(
        'src.processes.models.workflows.raw_performer'
        '.RawPerformer.__init__',
        return_value=None,
    )

    # act
    task._get_raw_performer(
        api_name=api_name,
        performer_type=PerformerType.GROUP,
        group_id=group_id,
    )

    # assert
    raw_performer_init_mock.assert_called_once_with(
        account=task.account,
        task=task,
        workflow=task.workflow,
        field=None,
        api_name=api_name,
        type=PerformerType.GROUP,
    )


def test_get_raw_performer__with_field__ok(mocker):
    """
    Creates RawPerformer with field
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    workflow = create_test_workflow(
        user=user,
        tasks_count=1,
    )
    task = workflow.tasks.get(number=1)
    api_name = 'rp-test-4'
    field_mock = mocker.Mock()
    raw_performer_init_mock = mocker.patch(
        'src.processes.models.workflows.raw_performer'
        '.RawPerformer.__init__',
        return_value=None,
    )

    # act
    task._get_raw_performer(
        api_name=api_name,
        performer_type=PerformerType.FIELD,
        field=field_mock,
    )

    # assert
    raw_performer_init_mock.assert_called_once_with(
        account=task.account,
        task=task,
        workflow=task.workflow,
        field=field_mock,
        api_name=api_name,
        type=PerformerType.FIELD,
    )


def test_get_raw_performer__workflow_starter_no_user__ok(mocker):
    """
    Creates RawPerformer without user or group (WORKFLOW_STARTER)
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    workflow = create_test_workflow(
        user=user,
        tasks_count=1,
    )
    task = workflow.tasks.get(number=1)
    api_name = 'rp-test-5'
    raw_performer_init_mock = mocker.patch(
        'src.processes.models.workflows.raw_performer'
        '.RawPerformer.__init__',
        return_value=None,
    )

    # act
    task._get_raw_performer(
        api_name=api_name,
        performer_type=PerformerType.WORKFLOW_STARTER,
    )

    # assert
    raw_performer_init_mock.assert_called_once_with(
        account=task.account,
        task=task,
        workflow=task.workflow,
        field=None,
        api_name=api_name,
        type=PerformerType.WORKFLOW_STARTER,
    )


def test_reset_delay__delay_with_pk__ok():
    """
    delay is provided and has a pk — resets dates and saves
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    workflow = create_test_workflow(
        user=user,
        tasks_count=1,
    )
    task = workflow.tasks.get(number=1)
    delay = Delay.objects.create(
        task=task,
        workflow=workflow,
        duration=timedelta(hours=1),
    )

    # act
    result = task.reset_delay(delay=delay)

    # assert
    result.refresh_from_db()
    assert result.estimated_end_date is None
    assert result.start_date is None
    assert result.end_date is None


def test_reset_delay__no_delay_arg_fetched_from_db__ok():
    """
    delay is None — fetches from DB, resets and saves
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    workflow = create_test_workflow(
        user=user,
        tasks_count=1,
    )
    task = workflow.tasks.get(number=1)
    delay = Delay.objects.create(
        task=task,
        workflow=workflow,
        duration=timedelta(hours=1),
        start_date=timezone.now(),
    )
    delay.refresh_from_db()
    assert delay.estimated_end_date is not None

    # act
    result = task.reset_delay()

    # assert
    result.refresh_from_db()
    assert result.estimated_end_date is None
    assert result.start_date is None
    assert result.end_date is None


def test_reset_delay__no_delay_in_db__none():
    """
    delay is None, no delay in DB — returns None
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    workflow = create_test_workflow(
        user=user,
        tasks_count=1,
    )
    task = workflow.tasks.get(number=1)

    # act
    result = task.reset_delay()

    # assert
    assert result is None


def test_reset_delay__delay_without_pk__skip():
    """
    delay is provided but pk is falsy — does nothing, returns delay
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    workflow = create_test_workflow(
        user=user,
        tasks_count=1,
    )
    task = workflow.tasks.get(number=1)
    delay = Delay(
        task=task,
        workflow=workflow,
        duration=timedelta(hours=1),
    )

    # act
    result = task.reset_delay(delay=delay)

    # assert
    assert result is delay
    assert delay.pk is None


def test_webhook_payload__normal__ok(mocker):
    """
    Returns dict with task data and workflow payload merged
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    workflow = create_test_workflow(
        user=user,
        tasks_count=1,
    )
    task = workflow.tasks.get(number=1)
    task_data = {'id': task.id, 'name': task.name}
    workflow_payload = {'workflow_id': workflow.id}
    task_serializer_mock = mocker.patch(
        'src.processes.serializers.workflows.task'
        '.TaskSerializer',
    )
    task_serializer_mock.return_value.data = task_data
    workflow_webhook_payload_mock = mocker.patch(
        'src.processes.models.workflows.workflow'
        '.Workflow.webhook_payload',
        return_value=workflow_payload,
    )

    # act
    result = task.webhook_payload()

    # assert
    task_serializer_mock.assert_called_once_with(instance=task)
    workflow_webhook_payload_mock.assert_called_once_with()
    assert result == {'task': {**task_data, **workflow_payload}}


def test_get_default_performer__workflow_starter_set__ok():
    """
    workflow_starter is set — returns it
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    workflow = create_test_workflow(
        user=user,
        tasks_count=1,
    )
    task = workflow.tasks.get(number=1)

    # act
    result = task.get_default_performer()

    # assert
    assert result == user


def test_get_default_performer__no_starter_account_owner_exists__ok():
    """
    workflow_starter is None, account owner exists — returns owner
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    workflow = create_test_workflow(
        user=user,
        tasks_count=1,
        is_external=True,
    )
    task = workflow.tasks.get(number=1)

    # act
    result = task.get_default_performer()

    # assert
    assert result == user


def test_get_default_performer__no_starter_no_owner__raise_exception(
    mocker,
):
    """
    Both workflow_starter and account owner are absent — raises Exception
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    workflow = create_test_workflow(
        user=user,
        tasks_count=1,
        is_external=True,
    )
    task = workflow.tasks.get(number=1)
    workflow_starter_mock = mocker.patch.object(
        type(workflow),
        'workflow_starter',
        new_callable=lambda: property(lambda self: None),
    )
    account_users_mock = mocker.Mock(
        filter=mocker.Mock(
            return_value=mocker.Mock(first=lambda: None),
        ),
    )
    account_mock = mocker.patch(
        'src.processes.models.workflows.workflow'
        '.Workflow.account',
        new_callable=mocker.PropertyMock,
        return_value=mocker.Mock(users=account_users_mock),
    )

    # act
    with pytest.raises(Exception) as ex:
        task.get_default_performer()

    # assert
    assert str(ex.value) == (
        'Invalid workflow: '
        'Workflow starter or account owner must be set!'
    )
    assert workflow_starter_mock is not None
    assert account_mock is not None


def test_get_raw_performers_fields_dict__field_type_new__ok(mocker):
    """
    Templates with FIELD type not in existent api_names — fetches dict
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    workflow = create_test_workflow(
        user=user,
        tasks_count=1,
    )
    task = workflow.tasks.get(number=1)
    field_api_name = 'user-field-1'
    template = {
        'api_name': 'rp-new-1',
        'type': PerformerType.FIELD,
        'field': {'api_name': field_api_name},
    }
    raw_performers_templates = [template]
    existent_api_names = set()
    field_mock = mocker.Mock(api_name=field_api_name)
    get_fields_as_dict_mock = mocker.patch(
        'src.processes.models.workflows.workflow'
        '.Workflow.get_fields_as_dict',
        return_value={field_api_name: field_mock},
    )

    # act
    result = task._get_raw_performers_fields_dict(
        raw_performers_templates=raw_performers_templates,
        existent_raw_performer_api_names=existent_api_names,
    )

    # assert
    get_fields_as_dict_mock.assert_called_once_with(
        tasks_filter_kwargs={'task__number__lt': task.number},
        fields_filter_kwargs={
            'type': 'user',
            'api_name__in': {field_api_name},
        },
        dict_key='api_name',
    )
    assert result == {field_api_name: field_mock}


def test_get_raw_performers_fields_dict__field_type_already_exists__empty(
    mocker,
):
    """
    Templates with FIELD type already in existent api_names — empty dict
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    workflow = create_test_workflow(
        user=user,
        tasks_count=1,
    )
    task = workflow.tasks.get(number=1)
    existing_api_name = 'rp-existing-1'
    template = {
        'api_name': existing_api_name,
        'type': PerformerType.FIELD,
        'field': {'api_name': 'user-field-1'},
    }
    raw_performers_templates = [template]
    existent_api_names = {existing_api_name}
    get_fields_as_dict_mock = mocker.patch(
        'src.processes.models.workflows.workflow'
        '.Workflow.get_fields_as_dict',
    )

    # act
    result = task._get_raw_performers_fields_dict(
        raw_performers_templates=raw_performers_templates,
        existent_raw_performer_api_names=existent_api_names,
    )

    # assert
    get_fields_as_dict_mock.assert_not_called()
    assert result == {}


def test_get_raw_performers_fields_dict__non_field_type__empty(mocker):
    """
    Templates with non-FIELD type — returns empty dict, no DB call
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    workflow = create_test_workflow(
        user=user,
        tasks_count=1,
    )
    task = workflow.tasks.get(number=1)
    template = {
        'api_name': 'rp-user-1',
        'type': PerformerType.USER,
        'field': None,
    }
    raw_performers_templates = [template]
    existent_api_names = set()
    get_fields_as_dict_mock = mocker.patch(
        'src.processes.models.workflows.workflow'
        '.Workflow.get_fields_as_dict',
    )

    # act
    result = task._get_raw_performers_fields_dict(
        raw_performers_templates=raw_performers_templates,
        existent_raw_performer_api_names=existent_api_names,
    )

    # assert
    get_fields_as_dict_mock.assert_not_called()
    assert result == {}


def test_get_raw_performers_fields_dict__empty_templates__empty(mocker):
    """
    No templates at all — returns empty dict
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    workflow = create_test_workflow(
        user=user,
        tasks_count=1,
    )
    task = workflow.tasks.get(number=1)
    get_fields_as_dict_mock = mocker.patch(
        'src.processes.models.workflows.workflow'
        '.Workflow.get_fields_as_dict',
    )

    # act
    result = task._get_raw_performers_fields_dict(
        raw_performers_templates=[],
        existent_raw_performer_api_names=set(),
    )

    # assert
    get_fields_as_dict_mock.assert_not_called()
    assert result == {}


def test_add_raw_performer__with_user__ok(mocker):
    """
    Valid call with user — creates and returns raw performer
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    workflow = create_test_workflow(
        user=user,
        tasks_count=1,
    )
    task = workflow.tasks.get(number=1)
    api_name = 'rp-add-1'
    raw_performer_mock = mocker.Mock()
    get_raw_performer_mock = mocker.patch(
        'src.processes.models.workflows.task.Task'
        '._get_raw_performer',
        return_value=raw_performer_mock,
    )

    # act
    result = task.add_raw_performer(
        user=user,
        api_name=api_name,
    )

    # assert
    get_raw_performer_mock.assert_called_once_with(
        api_name=api_name,
        performer_type=PerformerType.USER,
        user=user,
        group_id=None,
        user_id=None,
        field=None,
    )
    raw_performer_mock.save.assert_called_once_with()
    assert result is raw_performer_mock


def test_add_raw_performer__with_user_id__ok(mocker):
    """
    Valid call with user_id — creates and returns raw performer
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    workflow = create_test_workflow(
        user=user,
        tasks_count=1,
    )
    task = workflow.tasks.get(number=1)
    api_name = 'rp-add-2'
    raw_performer_mock = mocker.Mock()
    get_raw_performer_mock = mocker.patch(
        'src.processes.models.workflows.task.Task'
        '._get_raw_performer',
        return_value=raw_performer_mock,
    )

    # act
    result = task.add_raw_performer(
        user_id=user.id,
        api_name=api_name,
    )

    # assert
    get_raw_performer_mock.assert_called_once_with(
        api_name=api_name,
        performer_type=PerformerType.USER,
        user=None,
        group_id=None,
        user_id=user.id,
        field=None,
    )
    raw_performer_mock.save.assert_called_once_with()
    assert result is raw_performer_mock


def test_add_raw_performer__with_group_id__ok(mocker):
    """
    Valid call with group_id — creates and returns raw performer
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    workflow = create_test_workflow(
        user=user,
        tasks_count=1,
    )
    task = workflow.tasks.get(number=1)
    api_name = 'rp-add-3'
    group_id = 42
    raw_performer_mock = mocker.Mock()
    get_raw_performer_mock = mocker.patch(
        'src.processes.models.workflows.task.Task'
        '._get_raw_performer',
        return_value=raw_performer_mock,
    )

    # act
    result = task.add_raw_performer(
        group_id=group_id,
        api_name=api_name,
        performer_type=PerformerType.GROUP,
    )

    # assert
    get_raw_performer_mock.assert_called_once_with(
        api_name=api_name,
        performer_type=PerformerType.GROUP,
        user=None,
        group_id=group_id,
        user_id=None,
        field=None,
    )
    raw_performer_mock.save.assert_called_once_with()
    assert result is raw_performer_mock


def test_add_raw_performer__with_field__ok(mocker):
    """
    Valid call with field — creates and returns raw performer
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    workflow = create_test_workflow(
        user=user,
        tasks_count=1,
    )
    task = workflow.tasks.get(number=1)
    api_name = 'rp-add-4'
    field_mock = mocker.Mock()
    raw_performer_mock = mocker.Mock()
    get_raw_performer_mock = mocker.patch(
        'src.processes.models.workflows.task.Task'
        '._get_raw_performer',
        return_value=raw_performer_mock,
    )

    # act
    result = task.add_raw_performer(
        field=field_mock,
        api_name=api_name,
        performer_type=PerformerType.FIELD,
    )

    # assert
    get_raw_performer_mock.assert_called_once_with(
        api_name=api_name,
        performer_type=PerformerType.FIELD,
        user=None,
        group_id=None,
        user_id=None,
        field=field_mock,
    )
    raw_performer_mock.save.assert_called_once_with()
    assert result is raw_performer_mock


def test_add_raw_performer__workflow_starter_no_user__ok(mocker):
    """
    WORKFLOW_STARTER type with no user/field — creates raw performer
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    workflow = create_test_workflow(
        user=user,
        tasks_count=1,
    )
    task = workflow.tasks.get(number=1)
    api_name = 'rp-add-5'
    raw_performer_mock = mocker.Mock()
    get_raw_performer_mock = mocker.patch(
        'src.processes.models.workflows.task.Task'
        '._get_raw_performer',
        return_value=raw_performer_mock,
    )

    # act
    result = task.add_raw_performer(
        api_name=api_name,
        performer_type=PerformerType.WORKFLOW_STARTER,
    )

    # assert
    get_raw_performer_mock.assert_called_once_with(
        api_name=api_name,
        performer_type=PerformerType.WORKFLOW_STARTER,
        user=None,
        group_id=None,
        user_id=None,
        field=None,
    )
    raw_performer_mock.save.assert_called_once_with()
    assert result is raw_performer_mock


def test_add_raw_performer__no_user_no_field__raise_exception():
    """
    Not WORKFLOW_STARTER, no user/group/field/user_id — raises Exception
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    workflow = create_test_workflow(
        user=user,
        tasks_count=1,
    )
    task = workflow.tasks.get(number=1)

    # act
    with pytest.raises(Exception) as ex:
        task.add_raw_performer(
            performer_type=PerformerType.USER,
        )

    # assert
    assert str(ex.value) == (
        'Raw performer should be linked with field or user'
    )


def test_delete_orphaned_performers__orphan_users__ok():
    """
    Orphaned performers with USER type — deletes and returns user_ids
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    workflow = create_test_workflow(
        user=user,
        tasks_count=1,
    )
    task = workflow.tasks.get(number=1)
    task.update_performers()
    task.raw_performers.all().delete()

    # act
    deleted_user_ids, deleted_group_ids = (
        task._delete_orphaned_performers()
    )

    # assert
    assert user.id in deleted_user_ids
    assert deleted_group_ids == []


def test_delete_orphaned_performers__orphan_groups__ok():
    """
    Orphaned performers with GROUP type — deletes and returns group_ids
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    workflow = create_test_workflow(
        user=user,
        tasks_count=1,
    )
    task = workflow.tasks.get(number=1)
    group = create_test_group(account=user.account)
    task.add_raw_performer(
        group_id=group.id,
        performer_type=PerformerType.GROUP,
    )
    task.update_performers()
    task.raw_performers.filter(
        type=PerformerType.GROUP,
    ).delete()

    # act
    _, deleted_group_ids = (
        task._delete_orphaned_performers()
    )

    # assert
    assert group.id in deleted_group_ids


def test_delete_orphaned_performers__no_orphans__empty_lists():
    """
    No orphaned performers — returns empty lists, no delete called
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    workflow = create_test_workflow(
        user=user,
        tasks_count=1,
    )
    task = workflow.tasks.get(number=1)
    task.update_performers()

    # act
    deleted_user_ids, deleted_group_ids = (
        task._delete_orphaned_performers()
    )

    # assert
    assert deleted_user_ids == []
    assert deleted_group_ids == []


def test_delete_orphaned_performers__mixed_types__ok():
    """
    Mixed USER and GROUP orphans — returns both ids lists
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    workflow = create_test_workflow(
        user=user,
        tasks_count=1,
    )
    task = workflow.tasks.get(number=1)
    group = create_test_group(account=user.account)
    task.add_raw_performer(
        group_id=group.id,
        performer_type=PerformerType.GROUP,
    )
    task.update_performers()
    task.raw_performers.all().delete()

    # act
    deleted_user_ids, deleted_group_ids = (
        task._delete_orphaned_performers()
    )

    # assert
    assert user.id in deleted_user_ids
    assert group.id in deleted_group_ids


def test_delete_raw_performer__deleted__calls_delete_orphaned(mocker):
    """
    Raw performer deleted (count > 0) — calls _delete_orphaned_performers
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    workflow = create_test_workflow(
        user=user,
        tasks_count=1,
    )
    task = workflow.tasks.get(number=1)
    delete_orphaned_mock = mocker.patch(
        'src.processes.models.workflows.task.Task'
        '._delete_orphaned_performers',
        return_value=([], []),
    )

    # act
    task.delete_raw_performer(
        user=user,
        performer_type=PerformerType.USER,
    )

    # assert
    delete_orphaned_mock.assert_called_once_with()


def test_delete_raw_performer__not_deleted__skip_orphan_check(mocker):
    """
    No raw performer deleted (count == 0) — skips _delete_orphaned
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    workflow = create_test_workflow(
        user=user,
        tasks_count=1,
    )
    task = workflow.tasks.get(number=1)
    second_user = create_test_not_admin(
        account=user.account,
    )
    delete_orphaned_mock = mocker.patch(
        'src.processes.models.workflows.task.Task'
        '._delete_orphaned_performers',
        return_value=([], []),
    )

    # act
    task.delete_raw_performer(
        user=second_user,
        performer_type=PerformerType.USER,
    )

    # assert
    delete_orphaned_mock.assert_not_called()


def test_delete_raw_performers__called__ok(mocker):
    """
    Calls parent delete_raw_performers and _delete_orphaned_performers
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    workflow = create_test_workflow(
        user=user,
        tasks_count=1,
    )
    task = workflow.tasks.get(number=1)
    delete_orphaned_mock = mocker.patch(
        'src.processes.models.workflows.task.Task'
        '._delete_orphaned_performers',
        return_value=([], []),
    )

    # act
    task.delete_raw_performers()

    # assert
    delete_orphaned_mock.assert_called_once_with()


def test_can_be_completed__already_completed__false():
    """
    Task is already completed — returns False immediately
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    workflow = create_test_workflow(
        user=user,
        tasks_count=1,
    )
    task = workflow.tasks.get(number=1)
    task.status = TaskStatus.COMPLETED
    task.save(update_fields=['status'])

    # act
    result = task.can_be_completed()

    # assert
    assert result is False


def test_can_be_completed__not_by_all_one_completed__true():
    """
    require_completion_by_all=False, one completed performer — True
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    workflow = create_test_workflow(
        user=user,
        tasks_count=1,
    )
    task = workflow.tasks.get(number=1)
    task.status = TaskStatus.ACTIVE
    task.require_completion_by_all = False
    task.save(update_fields=['status', 'require_completion_by_all'])
    task.update_performers()
    task.taskperformer_set.update(is_completed=True)

    # act
    result = task.can_be_completed()

    # assert
    assert result is True


def test_can_be_completed__not_by_all_none_completed__false():
    """
    require_completion_by_all=False, no completed performers — False
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    workflow = create_test_workflow(
        user=user,
        tasks_count=1,
    )
    task = workflow.tasks.get(number=1)
    task.status = TaskStatus.ACTIVE
    task.require_completion_by_all = False
    task.save(update_fields=['status', 'require_completion_by_all'])
    task.update_performers()
    task.taskperformer_set.update(is_completed=False)

    # act
    result = task.can_be_completed()

    # assert
    assert result is False


def test_can_be_completed__by_all_all_completed__true():
    """
    require_completion_by_all=True, no incompleted performers — True
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    workflow = create_test_workflow(
        user=user,
        tasks_count=1,
    )
    task = workflow.tasks.get(number=1)
    task.status = TaskStatus.ACTIVE
    task.require_completion_by_all = True
    task.save(update_fields=['status', 'require_completion_by_all'])
    task.update_performers()
    task.taskperformer_set.update(is_completed=True)

    # act
    result = task.can_be_completed()

    # assert
    assert result is True


def test_can_be_completed__by_all_some_incompleted__false():
    """
    require_completion_by_all=True, some incompleted performers — False
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    workflow = create_test_workflow(
        user=user,
        tasks_count=1,
    )
    task = workflow.tasks.get(number=1)
    task.status = TaskStatus.ACTIVE
    task.require_completion_by_all = True
    task.save(update_fields=['status', 'require_completion_by_all'])
    task.update_performers()
    task.taskperformer_set.update(is_completed=False)

    # act
    result = task.can_be_completed()

    # assert
    assert result is False


def test_get_revert_tasks__revert_task_set__ok():
    """
    revert_task is set — filters by revert_task api_name
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    workflow = create_test_workflow(
        user=user,
        tasks_count=2,
    )
    task_1 = workflow.tasks.get(number=1)
    task_2 = workflow.tasks.get(number=2)
    task_2.revert_task = task_1.api_name
    task_2.save(update_fields=['revert_task'])

    # act
    result = task_2.get_revert_tasks()

    # assert
    assert task_1 in result


def test_get_revert_tasks__parents_set__ok():
    """
    revert_task is None, parents set — filters by parents api_names
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    workflow = create_test_workflow(
        user=user,
        tasks_count=2,
    )
    task_1 = workflow.tasks.get(number=1)
    task_2 = workflow.tasks.get(number=2)
    task_2.revert_task = None
    task_2.parents = [task_1.api_name]
    task_2.save(update_fields=['revert_task', 'parents'])

    # act
    result = task_2.get_revert_tasks()

    # assert
    assert task_1 in result


def test_get_revert_tasks__no_revert_no_parents__empty():
    """
    Both revert_task and parents are empty/None — returns empty list
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    workflow = create_test_workflow(
        user=user,
        tasks_count=1,
    )
    task = workflow.tasks.get(number=1)
    task.revert_task = None
    task.parents = []
    task.save(update_fields=['revert_task', 'parents'])

    # act
    result = task.get_revert_tasks()

    # assert
    assert list(result) == []


def test_get_data_for_list__date_started_set__ok(mocker):
    """
    date_started is set — includes timestamp in serialized data
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    workflow = create_test_workflow(
        user=user,
        tasks_count=1,
    )
    task = workflow.tasks.get(number=1)
    now = timezone.now()
    task.date_started = now
    task.save(update_fields=['date_started'])
    task_list_serializer_mock = mocker.patch(
        'src.processes.serializers.workflows.task'
        '.TaskListSerializer',
    )
    task_list_serializer_mock.return_value.data = {}

    # act
    task.get_data_for_list()

    # assert
    task_list_serializer_mock.assert_called_once()
    call_kwargs = task_list_serializer_mock.call_args
    instance_arg = call_kwargs[1]['instance']
    assert instance_arg.date_started_tsp == now.timestamp()


def test_get_data_for_list__no_date_started__none_tsp(mocker):
    """
    date_started is None — date_started_tsp is None
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    workflow = create_test_workflow(
        user=user,
        tasks_count=1,
    )
    task = workflow.tasks.get(number=1)
    task.date_started = None
    task.save(update_fields=['date_started'])
    task_list_serializer_mock = mocker.patch(
        'src.processes.serializers.workflows.task'
        '.TaskListSerializer',
    )
    task_list_serializer_mock.return_value.data = {}

    # act
    task.get_data_for_list()

    # assert
    task_list_serializer_mock.assert_called_once()
    call_kwargs = task_list_serializer_mock.call_args
    instance_arg = call_kwargs[1]['instance']
    assert instance_arg.date_started_tsp is None


def test_get_data_for_list__date_completed_set__ok(mocker):
    """
    date_completed is set — includes timestamp in data
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    workflow = create_test_workflow(
        user=user,
        tasks_count=1,
    )
    task = workflow.tasks.get(number=1)
    now = timezone.now()
    task.date_completed = now
    task.save(update_fields=['date_completed'])
    task_list_serializer_mock = mocker.patch(
        'src.processes.serializers.workflows.task'
        '.TaskListSerializer',
    )
    task_list_serializer_mock.return_value.data = {}

    # act
    task.get_data_for_list()

    # assert
    task_list_serializer_mock.assert_called_once()
    call_kwargs = task_list_serializer_mock.call_args
    instance_arg = call_kwargs[1]['instance']
    assert instance_arg.date_completed_tsp == now.timestamp()


def test_get_data_for_list__due_date_set__ok(mocker):
    """
    due_date is set — includes timestamp in data
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    workflow = create_test_workflow(
        user=user,
        tasks_count=1,
    )
    task = workflow.tasks.get(number=1)
    due = timezone.now() + timedelta(days=1)
    task.due_date = due
    task.save(update_fields=['due_date'])
    task_list_serializer_mock = mocker.patch(
        'src.processes.serializers.workflows.task'
        '.TaskListSerializer',
    )
    task_list_serializer_mock.return_value.data = {}

    # act
    task.get_data_for_list()

    # assert
    task_list_serializer_mock.assert_called_once()
    call_kwargs = task_list_serializer_mock.call_args
    instance_arg = call_kwargs[1]['instance']
    assert instance_arg.due_date_tsp == due.timestamp()


def test_get_data_for_list__serializer_called__ok(mocker):
    """
    Returns serialized data from TaskListSerializer
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    workflow = create_test_workflow(
        user=user,
        tasks_count=1,
    )
    task = workflow.tasks.get(number=1)
    expected_data = {'id': task.id}
    task_list_serializer_mock = mocker.patch(
        'src.processes.serializers.workflows.task'
        '.TaskListSerializer',
    )
    task_list_serializer_mock.return_value.data = expected_data

    # act
    result = task.get_data_for_list()

    # assert
    task_list_serializer_mock.assert_called_once()
    assert result == expected_data


def test_update_raw_performers_from_task_template__dict_input__ok(
    mocker,
):
    """
    task_template is dict — uses raw_performers from dict directly
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    workflow = create_test_workflow(
        user=user,
        tasks_count=1,
    )
    task = workflow.tasks.get(number=1)
    existing_api_name = (
        task._get_raw_performers_api_names().pop()
    )
    template_dict = {
        'raw_performers': [
            {
                'api_name': existing_api_name,
                'type': PerformerType.USER,
                'user_id': user.id,
                'group_id': None,
                'field': None,
            },
        ],
    }
    get_raw_performer_mock = mocker.patch(
        'src.processes.models.workflows.task.Task'
        '._get_raw_performer',
    )

    # act
    task.update_raw_performers_from_task_template(
        task_template=template_dict,
    )

    # assert
    get_raw_performer_mock.assert_not_called()


def test_update_raw_performers_from_task_template__no_changes__skip(
    mocker,
):
    """
    No new and no deleted performers — no bulk_create/delete called
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    workflow = create_test_workflow(
        user=user,
        tasks_count=1,
    )
    task = workflow.tasks.get(number=1)
    existing_api_name = (
        task._get_raw_performers_api_names().pop()
    )
    template_dict = {
        'raw_performers': [
            {
                'api_name': existing_api_name,
                'type': PerformerType.USER,
                'user_id': user.id,
                'group_id': None,
                'field': None,
            },
        ],
    }
    get_raw_performer_mock = mocker.patch(
        'src.processes.models.workflows.task.Task'
        '._get_raw_performer',
    )

    # act
    task.update_raw_performers_from_task_template(
        task_template=template_dict,
    )

    # assert
    get_raw_performer_mock.assert_not_called()


def test_update_raw_performers_from_tmpl__new_performers__bulk_created(
    mocker,
):
    """
    New raw performers (non-FIELD type) created via _get_raw_performer
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    workflow = create_test_workflow(
        user=user,
        tasks_count=1,
    )
    task = workflow.tasks.get(number=1)
    task.raw_performers.all().delete()
    new_api_name = 'rp-brand-new-1'
    template_dict = {
        'raw_performers': [
            {
                'api_name': new_api_name,
                'type': PerformerType.USER,
                'user_id': user.id,
                'group_id': None,
                'field': None,
            },
        ],
    }
    real_rp = task._get_raw_performer(
        api_name=new_api_name,
        performer_type=PerformerType.USER,
        user_id=user.id,
    )
    get_raw_performer_mock = mocker.patch(
        'src.processes.models.workflows.task.Task'
        '._get_raw_performer',
        return_value=real_rp,
    )
    bulk_create_mock = mocker.patch(
        'src.processes.models.workflows.raw_performer'
        '.RawPerformer.objects.bulk_create',
    )

    # act
    task.update_raw_performers_from_task_template(
        task_template=template_dict,
    )

    # assert
    get_raw_performer_mock.assert_called_once_with(
        performer_type=PerformerType.USER,
        user_id=user.id,
        group_id=None,
        field=None,
        api_name=new_api_name,
    )
    bulk_create_mock.assert_called_once_with([real_rp])


def test_update_raw_performers_from_tmpl__existing_api_name__not_duped(
    mocker,
):
    """
    Existing api_name in template — not re-created, removed from deletion
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    workflow = create_test_workflow(
        user=user,
        tasks_count=1,
    )
    task = workflow.tasks.get(number=1)
    existing_api_name = (
        task._get_raw_performers_api_names().pop()
    )
    template_dict = {
        'raw_performers': [
            {
                'api_name': existing_api_name,
                'type': PerformerType.USER,
                'user_id': user.id,
                'group_id': None,
                'field': None,
            },
        ],
    }
    get_raw_performer_mock = mocker.patch(
        'src.processes.models.workflows.task.Task'
        '._get_raw_performer',
    )

    # act
    task.update_raw_performers_from_task_template(
        task_template=template_dict,
    )

    # assert
    get_raw_performer_mock.assert_not_called()
    assert task.raw_performers.filter(
        api_name=existing_api_name,
    ).exists()


def test_update_raw_performers_from_tmpl__orphans__deleted(
    mocker,
):
    """
    Orphaned raw performers are deleted when absent from template
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    workflow = create_test_workflow(
        user=user,
        tasks_count=1,
    )
    task = workflow.tasks.get(number=1)
    orphan_api_name = (
        task._get_raw_performers_api_names().pop()
    )
    template_dict = {'raw_performers': []}
    get_raw_performer_mock = mocker.patch(
        'src.processes.models.workflows.task.Task'
        '._get_raw_performer',
    )

    # act
    task.update_raw_performers_from_task_template(
        task_template=template_dict,
    )

    # assert
    get_raw_performer_mock.assert_not_called()
    assert not task.raw_performers.filter(
        api_name=orphan_api_name,
    ).exists()


def test_update_performers__single_user_raw_performer__ok():
    """
    Single raw_performer provided, USER type — creates TaskPerformer
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    workflow = create_test_workflow(
        user=user,
        tasks_count=1,
    )
    task = workflow.tasks.get(number=1)
    raw_performer = task.raw_performers.filter(
        type=PerformerType.USER,
    ).first()
    task.taskperformer_set.all().delete()

    # act
    created_user_ids, created_group_ids, _, _ = (
        task.update_performers(raw_performer=raw_performer)
    )

    # assert
    assert user.id in created_user_ids
    assert created_group_ids == []


def test_update_performers__user_performer_exists__no_duplicate():
    """
    USER raw_performer, TaskPerformer already exists — no duplicate
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    workflow = create_test_workflow(
        user=user,
        tasks_count=1,
    )
    task = workflow.tasks.get(number=1)
    task.update_performers()
    count_before = task.taskperformer_set.count()
    raw_performer = task.raw_performers.filter(
        type=PerformerType.USER,
    ).first()

    # act
    created_user_ids, _, _, _ = (
        task.update_performers(raw_performer=raw_performer)
    )

    # assert
    assert created_user_ids == []
    assert task.taskperformer_set.count() == count_before


def test_update_performers__group_raw_performer__ok():
    """
    GROUP type raw_performer — creates TaskPerformer with group
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    workflow = create_test_workflow(
        user=user,
        tasks_count=1,
    )
    task = workflow.tasks.get(number=1)
    group = create_test_group(account=user.account)
    task.add_raw_performer(
        group_id=group.id,
        performer_type=PerformerType.GROUP,
    )
    raw_performer = task.raw_performers.filter(
        type=PerformerType.GROUP,
    ).first()

    # act
    _, created_group_ids, _, _ = (
        task.update_performers(raw_performer=raw_performer)
    )

    # assert
    assert group.id in created_group_ids


def test_update_performers__workflow_starter__calls_get_default_performer(
    mocker,
):
    """
    WORKFLOW_STARTER type — calls get_default_performer
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    workflow = create_test_workflow(
        user=user,
        tasks_count=1,
        is_external=True,
    )
    task = workflow.tasks.get(number=1)
    task.add_raw_performer(
        performer_type=PerformerType.WORKFLOW_STARTER,
    )
    raw_performer = task.raw_performers.filter(
        type=PerformerType.WORKFLOW_STARTER,
    ).first()
    get_default_performer_mock = mocker.patch(
        'src.processes.models.workflows.task.Task'
        '.get_default_performer',
        return_value=user,
    )

    # act
    task.update_performers(raw_performer=raw_performer)

    # assert
    get_default_performer_mock.assert_called_once_with()


def test_update_performers__no_arg_uses_all_raw_performers__ok():
    """
    raw_performer not provided — uses all raw_performers queryset
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    workflow = create_test_workflow(
        user=user,
        tasks_count=1,
    )
    task = workflow.tasks.get(number=1)
    task.taskperformer_set.all().delete()

    # act
    created_user_ids, _, _, _ = task.update_performers()

    # assert
    assert user.id in created_user_ids


def test_update_performers__restore_field_performer__ok():
    """
    restore_performers=True, DELETED status, FIELD type — restores
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    workflow = create_test_workflow(
        user=user,
        tasks_count=1,
    )
    task = workflow.tasks.get(number=1)
    task.update_performers()
    TaskPerformer.objects.filter(
        task=task,
        user=user,
    ).update(
        directly_status=DirectlyStatus.DELETED,
    )
    field = TaskField.objects.create(
        task=task,
        workflow=workflow,
        account=user.account,
        name='User field',
        api_name='user-field-restore',
        type=FieldType.USER,
        user_id=user.id,
    )
    raw_performer = task.add_raw_performer(
        field=field,
        performer_type=PerformerType.FIELD,
    )

    # act
    task.update_performers(
        raw_performer=raw_performer,
        restore_performers=True,
    )

    # assert
    task_performer = TaskPerformer.objects.get(
        task=task,
        user=user,
    )
    assert task_performer.directly_status == DirectlyStatus.NO_STATUS


def test_update_performers__orphaned_deleted__ok():
    """
    Orphaned performers deleted via _delete_orphaned_performers
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    workflow = create_test_workflow(
        user=user,
        tasks_count=1,
    )
    task = workflow.tasks.get(number=1)
    task.update_performers()
    task.raw_performers.all().delete()

    # act
    _, _, deleted_user_ids, _ = task.update_performers()

    # assert
    assert user.id in deleted_user_ids


def test_update_performers__return_value__ok():
    """
    Returns tuple of 4 lists: created_user, created_group,
    deleted_user, deleted_group ids
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    workflow = create_test_workflow(
        user=user,
        tasks_count=1,
    )
    task = workflow.tasks.get(number=1)

    # act
    result = task.update_performers()

    # assert
    assert isinstance(result, tuple)
    assert len(result) == 4
    created_user_ids, created_group_ids, del_user_ids, del_group_ids = (
        result
    )
    assert isinstance(created_user_ids, list)
    assert isinstance(created_group_ids, list)
    assert isinstance(del_user_ids, list)
    assert isinstance(del_group_ids, list)
