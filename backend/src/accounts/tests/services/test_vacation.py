from datetime import timedelta

import pytest
from django.utils import timezone

from src.accounts.enums import AbsenceStatus, UserGroupType
from src.accounts.models import UserGroup, UserVacation
from src.accounts.serializers.user import UserWebsocketSerializer
from src.accounts.services.vacation import VacationDelegationService
from src.processes.enums import (
    DirectlyStatus,
    PerformerType,
    TaskStatus,
    WorkflowEventType,
    WorkflowStatus,
)
from src.processes.models.workflows.event import WorkflowEvent
from src.processes.models.workflows.task import Delay, TaskPerformer
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_admin,
    create_test_group,
    create_test_not_admin,
    create_test_owner,
    create_test_template,
    create_test_workflow,
)
from src.processes.services.workflow_action import WorkflowActionService
from src.processes.services.workflow_permissions import (
    WorkflowPermissionService,
)


pytestmark = pytest.mark.django_db


def test_sync_members__replaces_vacation_view__ok(mocker):

    # arrange
    schedule_sync_mock = mocker.patch(
        'src.accounts.services.vacation.'
        'schedule_sync_workflow_attachment_permissions',
    )
    account = create_test_account()
    owner = create_test_owner(account=account)
    sub1 = create_test_admin(
        account=account,
        email='s1@pneumatic.app',
    )
    sub2 = create_test_admin(
        account=account,
        email='s2@pneumatic.app',
    )
    workflow = create_test_workflow(user=owner)
    service = VacationDelegationService(user=owner)
    service.sync_members(
        wf_ids={workflow.id},
        substitute_user_ids=[sub1.id],
        user_id=owner.id,
    )
    schedule_sync_mock.reset_mock()

    # act
    service.sync_members(
        wf_ids={workflow.id},
        substitute_user_ids=[sub2.id],
        user_id=owner.id,
    )

    # assert
    perm_svc = WorkflowPermissionService(workflow)
    assert not perm_svc.has_view(user=sub1)
    assert perm_svc.has_view(user=sub2)
    schedule_sync_mock.assert_called_once_with(workflow.id)


def test_init__default__ok():

    """
    Init with user sets self.user.
    """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)

    # act
    service = VacationDelegationService(user=owner)

    # assert
    assert service.user == owner


def test_activate__creates_group__ok(mocker):

    """
    Creates personal group with substitutes.
    """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    substitute = create_test_admin(
        account=account,
        email='sub@pneumatic.app',
    )
    template = create_test_template(
        user=owner,
        tasks_count=1,
        is_active=True,
    )
    create_test_workflow(
        user=owner,
        template=template,
    )

    # act
    task_delegation_event_mock = mocker.patch(
        'src.processes.services.events.'
        'WorkflowEventService.task_delegation_event',
    )
    service = VacationDelegationService(user=owner)
    service.activate(substitute_user_ids=[substitute.id])

    # assert
    owner.refresh_from_db()
    group = owner.vacation.substitute_group
    assert group is not None
    assert group.type == UserGroupType.PERSONAL
    assert group.account_id == account.id
    assert list(
        group.users.values_list('id', flat=True),
    ) == [substitute.id]
    task_delegation_event_mock.assert_called_once_with(
        task=mocker.ANY,
        user=owner,
        substitute_group=group,
    )


def test_activate__does_not_freeze_performers__ok(mocker):

    """
    Activate does NOT freeze user performers (DELEGATED removed).
    User performer stays NO_STATUS; group performer created alongside.
    """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    substitute = create_test_admin(
        account=account,
        email='sub@pneumatic.app',
    )
    template = create_test_template(
        user=owner,
        tasks_count=1,
        is_active=True,
    )
    workflow = create_test_workflow(
        user=owner,
        template=template,
    )
    task_delegation_event_mock = mocker.patch(
        'src.processes.services.events.'
        'WorkflowEventService.task_delegation_event',
    )

    # act
    service = VacationDelegationService(user=owner)
    service.activate(substitute_user_ids=[substitute.id])

    # assert
    performer = TaskPerformer.objects.get(
        task__workflow=workflow,
        task__status=TaskStatus.ACTIVE,
        user_id=owner.id,
        type=PerformerType.USER,
    )
    assert performer.directly_status == DirectlyStatus.NO_STATUS
    group_perf = TaskPerformer.objects.filter(
        task__workflow=workflow,
        task__status=TaskStatus.ACTIVE,
        type=PerformerType.GROUP,
    ).first()
    assert group_perf is not None

    task_delegation_event_mock.assert_called_once_with(
        task=mocker.ANY,
        user=owner,
        substitute_group=mocker.ANY,
    )


def test_activate__adds_group_perf__ok(mocker):

    """
    Adds GROUP performer for substitute group via bulk_create.
    """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    substitute = create_test_admin(
        account=account,
        email='sub@pneumatic.app',
    )
    template = create_test_template(
        user=owner,
        tasks_count=1,
        is_active=True,
    )
    workflow = create_test_workflow(
        user=owner,
        template=template,
    )
    task_delegation_event_mock = mocker.patch(
        'src.processes.services.events.'
        'WorkflowEventService.task_delegation_event',
    )

    # act
    service = VacationDelegationService(user=owner)
    service.activate(substitute_user_ids=[substitute.id])

    # assert
    owner.refresh_from_db()
    group_perf_exists = TaskPerformer.objects.filter(
        task__workflow=workflow,
        task__status=TaskStatus.ACTIVE,
        type=PerformerType.GROUP,
        group=owner.vacation.substitute_group,
    ).exists()
    assert group_perf_exists is True
    task_delegation_event_mock.assert_called_once_with(
        task=mocker.ANY,
        user=owner,
        substitute_group=owner.vacation.substitute_group,
    )


def test_activate__skip_deleted__ok(mocker):

    """
    Skips DELETED performers.
    """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    substitute = create_test_admin(
        account=account,
        email='sub@pneumatic.app',
    )
    template = create_test_template(
        user=owner,
        tasks_count=1,
        is_active=True,
    )
    workflow = create_test_workflow(
        user=owner,
        template=template,
    )
    task = workflow.tasks.get(status=TaskStatus.ACTIVE)
    TaskPerformer.objects.filter(
        task=task,
        user_id=owner.id,
        type=PerformerType.USER,
    ).update(directly_status=DirectlyStatus.DELETED)
    task_delegation_event_mock = mocker.patch(
        'src.processes.services.events.'
        'WorkflowEventService.task_delegation_event',
    )

    # act
    service = VacationDelegationService(user=owner)
    service.activate(substitute_user_ids=[substitute.id])

    # assert
    performer = TaskPerformer.objects.get(
        task=task,
        user_id=owner.id,
        type=PerformerType.USER,
    )
    assert performer.directly_status == DirectlyStatus.DELETED
    task_delegation_event_mock.assert_not_called()


def test_activate__group_tasks__ok(mocker):

    """
    Handles group tasks (user in regular group).
    """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    member = create_test_admin(
        account=account,
        email='member@pneumatic.app',
    )
    substitute = create_test_admin(
        account=account,
        email='sub@pneumatic.app',
    )
    regular_group = create_test_group(
        account=account,
        name='Dev Team',
        users=[owner, member],
    )
    template = create_test_template(
        user=member,
        tasks_count=1,
        is_active=True,
    )
    workflow = create_test_workflow(
        user=member,
        template=template,
    )
    task = workflow.tasks.get(status=TaskStatus.ACTIVE)

    # add group performer to task
    TaskPerformer.objects.create(
        task=task,
        type=PerformerType.GROUP,
        group=regular_group,
    )

    # remove any USER performer for owner (test group path)
    TaskPerformer.objects.filter(
        task=task,
        user_id=owner.id,
        type=PerformerType.USER,
    ).delete()
    task_delegation_event_mock = mocker.patch(
        'src.processes.services.events.'
        'WorkflowEventService.task_delegation_event',
    )

    # act
    service = VacationDelegationService(user=owner)
    service.activate(substitute_user_ids=[substitute.id])

    # assert
    owner.refresh_from_db()
    sub_group = owner.vacation.substitute_group
    sub_perf_exists = TaskPerformer.objects.filter(
        task=task,
        type=PerformerType.GROUP,
        group=sub_group,
    ).exists()
    assert sub_perf_exists is True
    task_delegation_event_mock.assert_called_once_with(
        task=task,
        user=owner,
        substitute_group=sub_group,
    )


def test_activate__no_user_groups__ok(mocker):

    """
    No group tasks when user has no regular groups.
    """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    substitute = create_test_admin(
        account=account,
        email='sub@pneumatic.app',
    )
    template = create_test_template(
        user=owner,
        tasks_count=1,
        is_active=True,
    )
    create_test_workflow(
        user=owner,
        template=template,
    )
    task_delegation_event_mock = mocker.patch(
        'src.processes.services.events.'
        'WorkflowEventService.task_delegation_event',
    )
    service = VacationDelegationService(user=owner)

    # act
    service.activate(substitute_user_ids=[substitute.id])

    # assert
    owner.refresh_from_db()
    user = UserVacation.objects.get(user=owner)
    assert user.absence_status == AbsenceStatus.VACATION
    task_delegation_event_mock.assert_called_once_with(
        task=mocker.ANY,
        user=owner,
        substitute_group=mocker.ANY,
    )


def test_activate__adds_members__ok(mocker):

    """
    Grants substitutes view_workflow permission via Guardian.
    """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    substitute = create_test_admin(
        account=account,
        email='sub@pneumatic.app',
    )
    template = create_test_template(
        user=owner,
        tasks_count=1,
        is_active=True,
    )
    workflow = create_test_workflow(
        user=owner,
        template=template,
    )
    task_delegation_event_mock = mocker.patch(
        'src.processes.services.events.'
        'WorkflowEventService.task_delegation_event',
    )

    # act
    service = VacationDelegationService(user=owner)
    service.activate(substitute_user_ids=[substitute.id])

    # assert
    assert WorkflowPermissionService(workflow).has_view(user=substitute)
    task_delegation_event_mock.assert_called_once_with(
        task=mocker.ANY,
        user=owner,
        substitute_group=mocker.ANY,
    )


def test_activate__preserves_notif_settings__ok(mocker):

    """
    Activate does NOT mute notification settings.
    Notifications are skipped at send time based on
    absence_status instead of mutating user fields.
    """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    substitute = create_test_admin(
        account=account,
        email='sub@pneumatic.app',
    )
    template = create_test_template(
        user=owner,
        tasks_count=1,
        is_active=True,
    )
    create_test_workflow(
        user=owner,
        template=template,
    )
    mocker.patch(
        'src.processes.services.events.'
        'WorkflowEventService.task_delegation_event',
    )

    original_new_tasks = owner.is_new_tasks_subscriber
    original_complete_tasks = owner.is_complete_tasks_subscriber

    # act
    service = VacationDelegationService(user=owner)
    service.activate(substitute_user_ids=[substitute.id])

    # assert
    owner.refresh_from_db()
    assert owner.is_new_tasks_subscriber == original_new_tasks
    assert owner.is_complete_tasks_subscriber == original_complete_tasks


def test_activate__sets_status__ok(mocker):

    """
    Sets absence_status to VACATION.
    """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    substitute = create_test_admin(
        account=account,
        email='sub@pneumatic.app',
    )
    template = create_test_template(
        user=owner,
        tasks_count=1,
        is_active=True,
    )
    create_test_workflow(
        user=owner,
        template=template,
    )
    task_delegation_event_mock = mocker.patch(
        'src.processes.services.events.'
        'WorkflowEventService.task_delegation_event',
    )

    # act
    service = VacationDelegationService(user=owner)
    service.activate(substitute_user_ids=[substitute.id])

    # assert
    owner.refresh_from_db()
    user = UserVacation.objects.get(user=owner)
    assert user.absence_status == AbsenceStatus.VACATION
    task_delegation_event_mock.assert_called_once_with(
        task=mocker.ANY,
        user=owner,
        substitute_group=mocker.ANY,
    )


def test_activate__sets_sick_leave__ok(mocker):

    """
    Sets absence_status to SICK_LEAVE when specified.
    """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    substitute = create_test_admin(
        account=account,
        email='sub@pneumatic.app',
    )
    template = create_test_template(
        user=owner,
        tasks_count=1,
        is_active=True,
    )
    create_test_workflow(
        user=owner,
        template=template,
    )
    mocker.patch(
        'src.processes.services.events.'
        'WorkflowEventService.task_delegation_event',
    )

    # act
    service = VacationDelegationService(user=owner)
    service.activate(
        substitute_user_ids=[substitute.id],
        absence_status=AbsenceStatus.SICK_LEAVE,
    )

    # assert
    owner.refresh_from_db()
    user = UserVacation.objects.get(user=owner)
    assert user.absence_status == AbsenceStatus.SICK_LEAVE


def test_activate__sets_sub_group__ok(mocker):

    """
    Sets vacation_substitute_group FK.
    """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    substitute = create_test_admin(
        account=account,
        email='sub@pneumatic.app',
    )
    template = create_test_template(
        user=owner,
        tasks_count=1,
        is_active=True,
    )
    create_test_workflow(
        user=owner,
        template=template,
    )
    task_delegation_event_mock = mocker.patch(
        'src.processes.services.events.'
        'WorkflowEventService.task_delegation_event',
    )

    # act
    service = VacationDelegationService(user=owner)
    service.activate(substitute_user_ids=[substitute.id])

    # assert
    owner.refresh_from_db()
    assert owner.vacation.substitute_group is not None
    assert owner.vacation.substitute_group.type == (
        UserGroupType.PERSONAL
    )
    task_delegation_event_mock.assert_called_once_with(
        task=mocker.ANY,
        user=owner,
        substitute_group=owner.vacation.substitute_group,
    )


def test_activate__update_existing__ok(mocker):

    """
    Updates substitutes when vacation is already active.
    """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    sub1 = create_test_admin(
        account=account,
        email='sub1@pneumatic.app',
    )
    sub2 = create_test_admin(
        account=account,
        email='sub2@pneumatic.app',
    )
    template = create_test_template(
        user=owner,
        tasks_count=1,
        is_active=True,
    )
    create_test_workflow(
        user=owner,
        template=template,
    )
    mocker.patch(
        'src.processes.services.events.'
        'WorkflowEventService.task_delegation_event',
    )

    # activate first time
    service = VacationDelegationService(user=owner)
    service.activate(substitute_user_ids=[sub1.id])
    owner.refresh_from_db()
    group_id = owner.vacation.substitute_group_id

    # act — update substitutes
    service.activate(substitute_user_ids=[sub2.id])

    # assert
    owner.refresh_from_db()

    # same group is reused
    assert owner.vacation.substitute_group_id == group_id

    # sub2 is now the only member
    members = list(
        owner.vacation.substitute_group.users
        .values_list('id', flat=True),
    )
    assert members == [sub2.id]


def test_activate__update_existing__status__ok(mocker):

    """
    Updates absence_status on re-activation.
    """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    substitute = create_test_admin(
        account=account,
        email='sub@pneumatic.app',
    )
    template = create_test_template(
        user=owner,
        tasks_count=1,
        is_active=True,
    )
    create_test_workflow(
        user=owner,
        template=template,
    )
    mocker.patch(
        'src.processes.services.events.'
        'WorkflowEventService.task_delegation_event',
    )
    service = VacationDelegationService(user=owner)
    service.activate(
        substitute_user_ids=[substitute.id],
        absence_status=AbsenceStatus.VACATION,
    )

    # act
    service.activate(
        substitute_user_ids=[substitute.id],
        absence_status=AbsenceStatus.SICK_LEAVE,
    )

    # assert
    owner.refresh_from_db()
    user = UserVacation.objects.get(user=owner)
    assert user.absence_status == AbsenceStatus.SICK_LEAVE


def test_activate__active_user_with_group__ok(mocker):

    """
    Reuses existing group if user is ACTIVE but has a scheduled vacation
    (substitute_group_id exists).
    """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    substitute = create_test_admin(
        account=account,
        email='sub1@pneumatic.app',
    )
    mocker.patch(
        'src.processes.services.events.'
        'WorkflowEventService.task_delegation_event',
    )
    service = VacationDelegationService(user=owner)

    group = UserGroup.objects.create(
        name='Substitutes',
        type=UserGroupType.PERSONAL,
        account=account,
    )
    UserVacation.objects.create(
        user=owner,
        account=account,
        substitute_group=group,
    )
    vacation = UserVacation.objects.get(user=owner)
    vacation.absence_status = AbsenceStatus.ACTIVE
    vacation.save(update_fields=['absence_status'])

    # act
    service.activate(substitute_user_ids=[substitute.id])

    # assert
    owner.refresh_from_db()

    assert owner.vacation.substitute_group_id == group.id


def test_activate__update_existing__creates_perfs__ok(mocker):

    """
    Auto-start: _update_existing creates group performers
    when none exist yet (first activation with pre-configured
    group) and emits delegation events for direct tasks.
    """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    substitute = create_test_admin(
        account=account,
        email='sub@pneumatic.app',
    )
    template = create_test_template(
        user=owner,
        tasks_count=1,
        is_active=True,
    )
    workflow = create_test_workflow(
        user=owner,
        template=template,
    )
    task = workflow.tasks.get(status=TaskStatus.ACTIVE)
    task_delegation_event_mock = mocker.patch(
        'src.processes.services.events.'
        'WorkflowEventService.task_delegation_event',
    )

    # Pre-configure vacation with substitute group (UI setup)
    group = UserGroup.objects.create(
        name='Substitutes',
        type=UserGroupType.PERSONAL,
        account=account,
    )
    UserVacation.objects.create(
        user=owner,
        account=account,
        substitute_group=group,
    )

    # act
    service = VacationDelegationService(user=owner)
    service.activate(substitute_user_ids=[substitute.id])

    # assert
    owner.refresh_from_db()
    user = UserVacation.objects.get(user=owner)
    assert user.absence_status == AbsenceStatus.VACATION
    group_perf_exists = TaskPerformer.objects.filter(
        task=task,
        type=PerformerType.GROUP,
        group=group,
    ).exists()
    assert group_perf_exists is True
    assert WorkflowPermissionService(workflow).has_view(user=substitute)
    task_delegation_event_mock.assert_called_once_with(
        task=task,
        user=owner,
        substitute_group=group,
    )


def test_activate__update_existing__creates_grp_perfs__ok(
    mocker,
):

    """
    Auto-start _update_existing creates group performers
    for tasks where the user participates via regular group
    (no direct USER performer).
    """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    member = create_test_admin(
        account=account,
        email='member@pneumatic.app',
    )
    substitute = create_test_admin(
        account=account,
        email='sub@pneumatic.app',
    )
    regular_group = create_test_group(
        account=account,
        name='Dev Team',
        users=[owner, member],
    )
    template = create_test_template(
        user=member,
        tasks_count=1,
        is_active=True,
    )
    workflow = create_test_workflow(
        user=member,
        template=template,
    )
    task = workflow.tasks.get(status=TaskStatus.ACTIVE)

    # add group performer to task
    TaskPerformer.objects.create(
        task=task,
        type=PerformerType.GROUP,
        group=regular_group,
    )

    # remove any USER performer for owner (test group path)
    TaskPerformer.objects.filter(
        task=task,
        user_id=owner.id,
        type=PerformerType.USER,
    ).delete()

    task_delegation_event_mock = mocker.patch(
        'src.processes.services.events.'
        'WorkflowEventService.task_delegation_event',
    )

    # Pre-configure vacation with substitute group
    sub_group = UserGroup.objects.create(
        name='Substitutes',
        type=UserGroupType.PERSONAL,
        account=account,
    )
    UserVacation.objects.create(
        user=owner,
        account=account,
        substitute_group=sub_group,
    )

    # act
    service = VacationDelegationService(user=owner)
    service.activate(substitute_user_ids=[substitute.id])

    # assert
    sub_perf_exists = TaskPerformer.objects.filter(
        task=task,
        type=PerformerType.GROUP,
        group=sub_group,
    ).exists()
    assert sub_perf_exists is True
    task_delegation_event_mock.assert_called_once_with(
        task=task,
        user=owner,
        substitute_group=sub_group,
    )


def test_activate__update_existing__filters_completed_tasks__ok(mocker):

    """
    Completed tasks and soft-deleted performers are ignored when updating.
    """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    substitute = create_test_admin(account=account, email='sub1@pneumatic.app')

    template = create_test_template(
        user=owner,
        tasks_count=2,
        is_active=True,
    )
    workflow = create_test_workflow(user=owner, template=template)

    task1 = workflow.tasks.order_by('number').first()
    task2 = workflow.tasks.order_by('number').last()

    task1.status = TaskStatus.COMPLETED
    task1.save(update_fields=['status'])

    task2.status = TaskStatus.ACTIVE
    task2.save(update_fields=['status'])

    TaskPerformer.objects.filter(task=task1).update(is_completed=True)

    mocker.patch(
        'src.processes.services.events.'
        'WorkflowEventService.task_delegation_event',
    )
    notify_mock = mocker.patch(
        'src.accounts.services.vacation.'
        'send_vacation_delegation_notification.delay',
    )

    group = UserGroup.objects.create(
        name='Substitutes',
        type=UserGroupType.PERSONAL,
        account=account,
    )
    UserVacation.objects.create(
        user=owner,
        account=account,
        substitute_group=group,
    )

    TaskPerformer.objects.create(
        task=task1,
        group=group,
        type=PerformerType.GROUP,
        is_completed=True,
        directly_status=DirectlyStatus.CREATED,
    )
    TaskPerformer.objects.create(
        task=task2,
        group=group,
        type=PerformerType.GROUP,
        is_completed=False,
        directly_status=DirectlyStatus.DELETED,
    )

    vacation = UserVacation.objects.get(user=owner)
    vacation.absence_status = AbsenceStatus.VACATION
    vacation.save(update_fields=['absence_status'])

    service = VacationDelegationService(user=owner)

    # act
    service.activate(substitute_user_ids=[substitute.id])

    # assert
    notify_mock.assert_called_once_with(
        user_id=substitute.id,
        user_email=substitute.email,
        user_first_name=substitute.first_name,
        account_id=owner.account_id,
        tasks_count=1,
        vacation_owner_name=owner.get_full_name(),
    )


def test_activate__no_active_tasks__ok(mocker):

    """
    No crash when no active/delayed tasks exist.
    """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    substitute = create_test_admin(
        account=account,
        email='sub@pneumatic.app',
    )
    mocker.patch(
        'src.processes.services.events.'
        'WorkflowEventService.task_delegation_event',
    )

    # act
    service = VacationDelegationService(user=owner)
    service.activate(substitute_user_ids=[substitute.id])

    # assert
    owner.refresh_from_db()
    user = UserVacation.objects.get(user=owner)
    assert user.absence_status == AbsenceStatus.VACATION
    assert owner.vacation.substitute_group is not None


def test_deactivate__unfreezes__ok(mocker):

    """
    Unfreezes DELEGATED performers to NO_STATUS.
    """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    substitute = create_test_admin(
        account=account,
        email='sub@pneumatic.app',
    )
    template = create_test_template(
        user=owner,
        tasks_count=1,
        is_active=True,
    )
    workflow = create_test_workflow(
        user=owner,
        template=template,
    )
    mocker.patch(
        'src.processes.services.events.'
        'WorkflowEventService.task_delegation_event',
    )
    service = VacationDelegationService(user=owner)
    service.activate(substitute_user_ids=[substitute.id])

    # act
    service.deactivate()

    # assert
    performer = TaskPerformer.objects.get(
        task__workflow=workflow,
        task__status=TaskStatus.ACTIVE,
        user_id=owner.id,
        type=PerformerType.USER,
    )
    assert performer.directly_status == DirectlyStatus.NO_STATUS


def test_deactivate__deletes_group__ok(mocker):

    """
    Deletes substitute group (cascade).
    """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    substitute = create_test_admin(
        account=account,
        email='sub@pneumatic.app',
    )
    template = create_test_template(
        user=owner,
        tasks_count=1,
        is_active=True,
    )
    create_test_workflow(
        user=owner,
        template=template,
    )
    mocker.patch(
        'src.processes.services.events.'
        'WorkflowEventService.task_delegation_event',
    )
    service = VacationDelegationService(user=owner)
    service.activate(substitute_user_ids=[substitute.id])
    owner.refresh_from_db()
    group_id = owner.vacation.substitute_group_id

    # act
    service.deactivate()

    # assert
    assert not UserGroup.objects.filter(id=group_id).exists()


def test_deactivate__no_group__ok():

    """
    No error when vacation_substitute_group is None.
    """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)

    # act
    service = VacationDelegationService(user=owner)
    service.deactivate()

    # assert
    owner.refresh_from_db()
    assert not UserVacation.objects.filter(user=owner).exists()


def test_deactivate__preserves_notif_settings__ok(mocker):

    """
    Preserves existing notification settings through activate/deactivate cycle.
    """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    substitute = create_test_admin(
        account=account,
        email='sub@pneumatic.app',
    )
    template = create_test_template(
        user=owner,
        tasks_count=1,
        is_active=True,
    )
    create_test_workflow(
        user=owner,
        template=template,
    )
    mocker.patch(
        'src.processes.services.events.'
        'WorkflowEventService.task_delegation_event',
    )

    original_new_tasks = owner.is_new_tasks_subscriber
    original_complete_tasks = owner.is_complete_tasks_subscriber

    service = VacationDelegationService(user=owner)
    service.activate(substitute_user_ids=[substitute.id])

    # act
    service.deactivate()

    # assert
    owner.refresh_from_db()
    assert owner.is_new_tasks_subscriber == original_new_tasks
    assert owner.is_complete_tasks_subscriber == original_complete_tasks


def test_deactivate__notifs_default__ok():

    """
    Defaults notifications to True when saved is None.
    """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    owner.save()

    # act
    service = VacationDelegationService(user=owner)
    service.deactivate()

    # assert
    owner.refresh_from_db()
    assert owner.is_new_tasks_subscriber is True
    assert owner.is_complete_tasks_subscriber is True


def test_deactivate__resets_status__ok(mocker):

    """
    Resets absence_status to ACTIVE.
    """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    substitute = create_test_admin(
        account=account,
        email='sub@pneumatic.app',
    )
    template = create_test_template(
        user=owner,
        tasks_count=1,
        is_active=True,
    )
    create_test_workflow(
        user=owner,
        template=template,
    )
    mocker.patch(
        'src.processes.services.events.'
        'WorkflowEventService.task_delegation_event',
    )
    service = VacationDelegationService(user=owner)
    service.activate(substitute_user_ids=[substitute.id])

    # act
    service.deactivate()

    # assert
    owner.refresh_from_db()
    assert not UserVacation.objects.filter(user=owner).exists()


def test_deactivate__clears_fields__ok(mocker):

    """
    Clears vacation dates and saved fields.
    """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    substitute = create_test_admin(
        account=account,
        email='sub@pneumatic.app',
    )
    template = create_test_template(
        user=owner,
        tasks_count=1,
        is_active=True,
    )
    create_test_workflow(
        user=owner,
        template=template,
    )
    mocker.patch(
        'src.processes.services.events.'
        'WorkflowEventService.task_delegation_event',
    )
    service = VacationDelegationService(user=owner)
    service.activate(substitute_user_ids=[substitute.id])

    # act
    service.deactivate()

    # assert
    owner.refresh_from_db()
    assert not UserVacation.objects.filter(user=owner).exists()


def test_deactivate__cleans_group_performers__ok(mocker):

    """
    Deactivate removes substitute group performers and
    restores the user to ACTIVE status.
    """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    substitute = create_test_admin(
        account=account,
        email='sub@pneumatic.app',
    )
    template = create_test_template(
        user=owner,
        tasks_count=2,
        is_active=True,
    )
    workflow = create_test_workflow(
        user=owner,
        template=template,
    )
    mocker.patch(
        'src.processes.services.events.'
        'WorkflowEventService.task_delegation_event',
    )
    service = VacationDelegationService(user=owner)
    service.activate(substitute_user_ids=[substitute.id])

    # act
    service.deactivate()

    # assert
    group_perfs = TaskPerformer.objects.filter(
        task__workflow=workflow,
        type=PerformerType.GROUP,
    )
    assert group_perfs.count() == 0

    owner.refresh_from_db()
    assert not UserVacation.objects.filter(user=owner).exists()


def test_deactivate__revokes_vacation_and_group_view__ok(mocker):

    # arrange
    schedule_sync_mock = mocker.patch(
        'src.accounts.services.vacation.'
        'schedule_sync_workflow_attachment_permissions',
    )
    send_user_updated_mock = mocker.patch(
        'src.accounts.services.vacation.'
        'send_user_updated_notification.delay',
    )
    mocker.patch(
        'src.processes.services.events.'
        'WorkflowEventService.task_delegation_event',
    )
    account = create_test_account()
    owner = create_test_owner(account=account)
    substitute = create_test_admin(
        account=account,
        email='sub_rev@pneumatic.app',
    )
    template = create_test_template(
        user=owner,
        tasks_count=1,
        is_active=True,
    )
    workflow = create_test_workflow(
        user=owner,
        template=template,
    )
    service = VacationDelegationService(user=owner)
    service.activate(substitute_user_ids=[substitute.id])
    schedule_sync_mock.reset_mock()
    send_user_updated_mock.reset_mock()

    # act
    service.deactivate()

    # assert
    perm_svc = WorkflowPermissionService(workflow)
    assert not perm_svc.has_view(user=substitute)
    schedule_sync_mock.assert_called_once_with(workflow.id)
    send_user_updated_mock.assert_called_once_with(
        logging=owner.account.log_api_requests,
        account_id=owner.account_id,
        user_data=mocker.ANY,
    )


def test_activate__update_replaces_subs__ok(mocker):

    """
    Re-activating with different substitutes replaces old members
    while keeping the same group.
    """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    sub1 = create_test_admin(
        account=account,
        email='sub1@pneumatic.app',
    )
    sub2 = create_test_admin(
        account=account,
        email='sub2@pneumatic.app',
    )
    sub3 = create_test_admin(
        account=account,
        email='sub3@pneumatic.app',
    )
    template = create_test_template(
        user=owner,
        tasks_count=1,
        is_active=True,
    )
    workflow = create_test_workflow(
        user=owner,
        template=template,
    )
    mocker.patch(
        'src.processes.services.events.'
        'WorkflowEventService.task_delegation_event',
    )
    mocker.patch(
        'src.storage.tasks.schedule_sync_workflow_attachment_permissions',
    )

    # activate with sub1, sub2
    service = VacationDelegationService(user=owner)
    service.activate(
        substitute_user_ids=[sub1.id, sub2.id],
    )
    owner.refresh_from_db()
    group_id = owner.vacation.substitute_group_id

    # act
    service.activate(
        substitute_user_ids=[sub2.id, sub3.id],
    )

    # assert — same group, new members
    owner.refresh_from_db()
    assert owner.vacation.substitute_group_id == group_id
    member_ids = set(
        owner.vacation.substitute_group.users
        .values_list('id', flat=True),
    )
    assert member_ids == {sub2.id, sub3.id}

    # Removed substitute must lose VACATION view
    perm_svc = WorkflowPermissionService(workflow)
    assert not perm_svc.has_view(user=sub1)
    assert perm_svc.has_view(user=sub2)
    assert perm_svc.has_view(user=sub3)


def test_clear_sub_groups__removes_user__ok():

    """
    Removes user from personal groups.
    """

    # arrange
    account = create_test_account()
    _owner = create_test_owner(account=account)
    sub = create_test_admin(
        account=account,
        email='sub@pneumatic.app',
    )
    sub2 = create_test_admin(
        account=account,
        email='sub2@pneumatic.app',
    )
    group = UserGroup.objects.create(
        name='Substitutes Test',
        type=UserGroupType.PERSONAL,
        account=account,
    )
    group.users.set([sub.id, sub2.id])

    # act
    VacationDelegationService.clear_substitute_groups(
        user=sub,
    )

    # assert
    assert not group.users.filter(id=sub.id).exists()
    assert group.users.filter(id=sub2.id).exists()


def test_clear_sub_groups__empty__deactivates(mocker):

    """
    Auto-deactivates vacation when group becomes empty.
    """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    sub = create_test_admin(
        account=account,
        email='sub@pneumatic.app',
    )
    template = create_test_template(
        user=owner,
        tasks_count=1,
        is_active=True,
    )
    create_test_workflow(
        user=owner,
        template=template,
    )
    mocker.patch(
        'src.processes.services.events.'
        'WorkflowEventService.task_delegation_event',
    )
    service = VacationDelegationService(user=owner)
    service.activate(substitute_user_ids=[sub.id])
    owner.refresh_from_db()
    assert owner.is_absent is True

    # act
    VacationDelegationService.clear_substitute_groups(
        user=sub,
    )

    # assert
    owner.refresh_from_db()
    assert not UserVacation.objects.filter(user=owner).exists()


def test_clear_sub_groups__no_groups__ok():

    """
    No error when user not in any personal groups.
    """

    # arrange
    account = create_test_account()
    user = create_test_admin(
        account=account,
        email='user@pneumatic.app',
    )

    # act
    VacationDelegationService.clear_substitute_groups(
        user=user,
    )

    # assert — no exception raised, user has no personal groups
    personal_groups = UserGroup.objects.filter(
        type=UserGroupType.PERSONAL,
        users=user,
    )
    assert personal_groups.count() == 0


def test_activate__sends_notification__ok(mocker):

    """
    Sends delegation notification to substitutes.
    """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    substitute = create_test_admin(
        account=account,
        email='sub@pneumatic.app',
    )
    template = create_test_template(
        user=owner,
        tasks_count=1,
        is_active=True,
    )
    create_test_workflow(
        user=owner,
        template=template,
    )
    mocker.patch(
        'src.processes.services.events.'
        'WorkflowEventService.task_delegation_event',
    )
    send_notif_mock = mocker.patch(
        'src.accounts.services.vacation.'
        'send_vacation_delegation_notification.delay',
    )

    # act
    service = VacationDelegationService(user=owner)
    service.activate(substitute_user_ids=[substitute.id])

    # assert
    send_notif_mock.assert_called_once_with(
        user_id=substitute.id,
        user_email=substitute.email,
        user_first_name=substitute.first_name,
        account_id=account.id,
        tasks_count=1,
        vacation_owner_name=owner.get_full_name(),
    )


def test_activate__no_tasks__skip_notif__ok(mocker):

    """
    No notification when no tasks are delegated.
    """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    substitute = create_test_admin(
        account=account,
        email='sub@pneumatic.app',
    )
    mocker.patch(
        'src.processes.services.events.'
        'WorkflowEventService.task_delegation_event',
    )
    send_notif_mock = mocker.patch(
        'src.accounts.services.vacation.'
        'send_vacation_delegation_notification.delay',
    )

    # act
    service = VacationDelegationService(user=owner)
    service.activate(substitute_user_ids=[substitute.id])

    # assert
    send_notif_mock.assert_not_called()


def test_activate_new__skips_completed_grp_perfs__ok(mocker):

    """
    _activate_new skips group performers with is_completed=True
    when building the set of tasks to delegate from regular groups.
    """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    member = create_test_admin(
        account=account,
        email='member@pneumatic.app',
    )
    substitute = create_test_admin(
        account=account,
        email='sub@pneumatic.app',
    )
    regular_group = create_test_group(
        account=account,
        name='Dev Team',
        users=[owner, member],
    )
    template = create_test_template(
        user=member,
        tasks_count=1,
        is_active=True,
    )
    workflow = create_test_workflow(
        user=member,
        template=template,
    )
    task = workflow.tasks.get(status=TaskStatus.ACTIVE)

    # add completed group performer to task
    TaskPerformer.objects.create(
        task=task,
        type=PerformerType.GROUP,
        group=regular_group,
        is_completed=True,
    )

    # remove USER performer for owner (test group path)
    TaskPerformer.objects.filter(
        task=task,
        user_id=owner.id,
        type=PerformerType.USER,
    ).delete()

    event_mock = mocker.patch(
        'src.processes.services.events.'
        'WorkflowEventService.task_delegation_event',
    )

    # act
    service = VacationDelegationService(user=owner)
    service.activate(substitute_user_ids=[substitute.id])

    # assert
    owner.refresh_from_db()
    sub_group = owner.vacation.substitute_group
    sub_perf_exists = TaskPerformer.objects.filter(
        task=task,
        type=PerformerType.GROUP,
        group=sub_group,
    ).exists()
    assert sub_perf_exists is False
    event_mock.assert_not_called()


def test_update_existing__skips_completed_grp_perfs__ok(
    mocker,
):

    """
    _update_existing skips group performers with
    is_completed=True when scanning regular groups.
    """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    member = create_test_admin(
        account=account,
        email='member@pneumatic.app',
    )
    substitute = create_test_admin(
        account=account,
        email='sub@pneumatic.app',
    )
    regular_group = create_test_group(
        account=account,
        name='Dev Team',
        users=[owner, member],
    )
    template = create_test_template(
        user=member,
        tasks_count=1,
        is_active=True,
    )
    workflow = create_test_workflow(
        user=member,
        template=template,
    )
    task = workflow.tasks.get(status=TaskStatus.ACTIVE)

    # add completed group performer to task
    TaskPerformer.objects.create(
        task=task,
        type=PerformerType.GROUP,
        group=regular_group,
        is_completed=True,
    )

    # remove USER performer for owner
    TaskPerformer.objects.filter(
        task=task,
        user_id=owner.id,
        type=PerformerType.USER,
    ).delete()

    event_mock = mocker.patch(
        'src.processes.services.events.'
        'WorkflowEventService.task_delegation_event',
    )

    # Pre-configure vacation with substitute group
    sub_group = UserGroup.objects.create(
        name='Substitutes',
        type=UserGroupType.PERSONAL,
        account=account,
    )
    UserVacation.objects.create(
        user=owner,
        account=account,
        substitute_group=sub_group,
    )

    # act
    service = VacationDelegationService(user=owner)
    service.activate(substitute_user_ids=[substitute.id])

    # assert
    sub_perf_exists = TaskPerformer.objects.filter(
        task=task,
        type=PerformerType.GROUP,
        group=sub_group,
    ).exists()
    assert sub_perf_exists is False
    event_mock.assert_not_called()


def test_update_existing__skips_non_running_wf__ok(mocker):

    """
    _update_existing does not include workflow IDs from
    non-RUNNING workflows in existing_wf_ids.
    Substitutes are not added as members to done workflows.
    """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    substitute = create_test_admin(
        account=account,
        email='sub@pneumatic.app',
    )

    sub_group = UserGroup.objects.create(
        name='Substitutes',
        type=UserGroupType.PERSONAL,
        account=account,
    )
    sub_group.users.add(substitute)
    UserVacation.objects.create(
        user=owner,
        account=account,
        substitute_group=sub_group,
    )

    # Create a DONE workflow with existing substitute
    # group performer
    template = create_test_template(
        user=owner,
        tasks_count=1,
        is_active=True,
    )
    done_wf = create_test_workflow(
        user=owner,
        template=template,
        status=WorkflowStatus.DONE,
    )
    done_task = done_wf.tasks.first()
    done_task.status = TaskStatus.ACTIVE
    done_task.save(update_fields=['status'])

    TaskPerformer.objects.create(
        task=done_task,
        group=sub_group,
        type=PerformerType.GROUP,
    )

    event_mock = mocker.patch(
        'src.processes.services.events.'
        'WorkflowEventService.task_delegation_event',
    )

    # act
    service = VacationDelegationService(user=owner)
    service.activate(substitute_user_ids=[substitute.id])

    # assert
    assert not WorkflowPermissionService(done_wf).has_view(user=substitute)
    event_mock.assert_not_called()


def test_get_unique_group_name__no_collision__ok():

    """
    Returns base name when no collision exists.
    """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    service = VacationDelegationService(user=owner)
    base_name = 'Substitutes Test User'

    # act
    result = service._get_unique_group_name(
        base_name=base_name,
    )

    # assert
    assert result == base_name


def test_get_unique_group_name__collision__ok():

    """
    Appends (2) suffix when base name collides.
    """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    service = VacationDelegationService(user=owner)
    base_name = 'Substitutes Test User'

    UserGroup.include_personal.create(
        name=base_name,
        type=UserGroupType.PERSONAL,
        account=account,
    )

    # act
    result = service._get_unique_group_name(
        base_name=base_name,
    )

    # assert
    assert result == f'{base_name} (2)'


def test_activate__sends_ws_user_updated__ok(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    substitute = create_test_admin(
        account=account,
        email='sub@pneumatic.app',
    )
    template = create_test_template(
        user=owner,
        tasks_count=1,
        is_active=True,
    )
    create_test_workflow(
        user=owner,
        template=template,
    )
    mocker.patch(
        'src.processes.services.events.'
        'WorkflowEventService.task_delegation_event',
    )
    mocker.patch(
        'src.accounts.services.vacation.'
        'send_vacation_delegation_notification.delay',
    )
    ws_mock = mocker.patch(
        'src.accounts.services.vacation.'
        'send_user_updated_notification.delay',
    )

    # act
    service = VacationDelegationService(user=owner)
    service.activate(substitute_user_ids=[substitute.id])

    # assert
    owner.refresh_from_db()
    ws_mock.assert_called_once_with(
        logging=account.log_api_requests,
        account_id=account.id,
        user_data=UserWebsocketSerializer(owner).data,
    )


def test_deactivate__sends_ws_user_updated__ok(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    substitute = create_test_admin(
        account=account,
        email='sub@pneumatic.app',
    )
    template = create_test_template(
        user=owner,
        tasks_count=1,
        is_active=True,
    )
    create_test_workflow(
        user=owner,
        template=template,
    )
    mocker.patch(
        'src.processes.services.events.'
        'WorkflowEventService.task_delegation_event',
    )
    mocker.patch(
        'src.accounts.services.vacation.'
        'send_vacation_delegation_notification.delay',
    )
    mocker.patch(
        'src.accounts.services.vacation.'
        'send_user_updated_notification.delay',
    )
    service = VacationDelegationService(user=owner)
    service.activate(substitute_user_ids=[substitute.id])

    ws_mock = mocker.patch(
        'src.accounts.services.vacation.'
        'send_user_updated_notification.delay',
    )

    # act
    service.deactivate()

    # assert
    owner.refresh_from_db()
    ws_mock.assert_called_once_with(
        logging=account.log_api_requests,
        account_id=account.id,
        user_data=UserWebsocketSerializer(owner).data,
    )


def test_skip_tasks_for_starter__substitute_is_starter__skipped(mocker):

    """
    Workflow starter is a substitute: the task is passed
    to WorkflowActionService on behalf of the account owner.
    """

    # arrange
    account = create_test_account()
    account_owner = create_test_owner(account=account)
    vacation_user = create_test_admin(account=account)
    starter = create_test_not_admin(account=account)
    group = UserGroup.objects.create(
        name='Substitutes',
        type=UserGroupType.PERSONAL,
        account=account,
    )
    group.users.add(starter)
    workflow = create_test_workflow(
        user=starter,
        tasks_count=1,
    )
    task = workflow.tasks.get(number=1)
    task.skip_for_starter = True
    task.save(update_fields=['skip_for_starter'])
    workflow_action_service_init_mock = mocker.patch.object(
        WorkflowActionService,
        attribute='__init__',
        return_value=None,
    )
    skip_delegated_task_for_starter_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '.skip_delegated_task_for_starter',
        return_value=True,
    )
    service = VacationDelegationService(user=vacation_user)

    # act
    result = service._skip_tasks_for_starter(
        group=group,
        task_ids={task.id},
    )

    # assert
    assert result == {task.id}
    workflow_action_service_init_mock.assert_called_once_with(
        user=account_owner,
        workflow=workflow,
    )
    skip_delegated_task_for_starter_mock.assert_called_once_with(task=task)


def test_skip_tasks_for_starter__task_not_skipped__empty(mocker):

    """
    WorkflowActionService did not skip the task
    (e.g. RCBA with other performers).
    """

    # arrange
    account = create_test_account()
    account_owner = create_test_owner(account=account)
    vacation_user = create_test_admin(account=account)
    starter = create_test_not_admin(account=account)
    group = UserGroup.objects.create(
        name='Substitutes',
        type=UserGroupType.PERSONAL,
        account=account,
    )
    group.users.add(starter)
    workflow = create_test_workflow(
        user=starter,
        tasks_count=1,
    )
    task = workflow.tasks.get(number=1)
    task.skip_for_starter = True
    task.save(update_fields=['skip_for_starter'])
    workflow_action_service_init_mock = mocker.patch.object(
        WorkflowActionService,
        attribute='__init__',
        return_value=None,
    )
    skip_delegated_task_for_starter_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '.skip_delegated_task_for_starter',
        return_value=False,
    )
    service = VacationDelegationService(user=vacation_user)

    # act
    result = service._skip_tasks_for_starter(
        group=group,
        task_ids={task.id},
    )

    # assert
    assert result == set()
    workflow_action_service_init_mock.assert_called_once_with(
        user=account_owner,
        workflow=workflow,
    )
    skip_delegated_task_for_starter_mock.assert_called_once_with(task=task)


def test_skip_tasks_for_starter__several_tasks__only_skipped_ids(mocker):

    """
    Only IDs of the tasks skipped by WorkflowActionService
    are returned.
    """

    # arrange
    account = create_test_account()
    account_owner = create_test_owner(account=account)
    vacation_user = create_test_admin(account=account)
    starter = create_test_not_admin(account=account)
    group = UserGroup.objects.create(
        name='Substitutes',
        type=UserGroupType.PERSONAL,
        account=account,
    )
    group.users.add(starter)
    workflow_1 = create_test_workflow(
        user=starter,
        tasks_count=1,
    )
    task_1 = workflow_1.tasks.get(number=1)
    task_1.skip_for_starter = True
    task_1.save(update_fields=['skip_for_starter'])
    workflow_2 = create_test_workflow(
        user=starter,
        tasks_count=1,
    )
    task_2 = workflow_2.tasks.get(number=1)
    task_2.skip_for_starter = True
    task_2.save(update_fields=['skip_for_starter'])
    workflow_action_service_init_mock = mocker.patch.object(
        WorkflowActionService,
        attribute='__init__',
        return_value=None,
    )
    skip_delegated_task_for_starter_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '.skip_delegated_task_for_starter',
        side_effect=[True, False],
    )
    service = VacationDelegationService(user=vacation_user)

    # act
    result = service._skip_tasks_for_starter(
        group=group,
        task_ids={task_1.id, task_2.id},
    )

    # assert
    assert result == {task_1.id}
    assert workflow_action_service_init_mock.call_count == 2
    workflow_action_service_init_mock.assert_has_calls(
        [
            mocker.call(
                user=account_owner,
                workflow=workflow_1,
            ),
            mocker.call(
                user=account_owner,
                workflow=workflow_2,
            ),
        ],
    )
    assert skip_delegated_task_for_starter_mock.call_count == 2
    skip_delegated_task_for_starter_mock.assert_has_calls(
        [
            mocker.call(task=task_1),
            mocker.call(task=task_2),
        ],
    )


def test_skip_tasks_for_starter__starter_not_substitute__not_called(mocker):

    # arrange
    account = create_test_account()
    vacation_user = create_test_admin(account=account)
    starter = create_test_not_admin(account=account)
    substitute = create_test_admin(
        account=account,
        email='sub@pneumatic.app',
    )
    group = UserGroup.objects.create(
        name='Substitutes',
        type=UserGroupType.PERSONAL,
        account=account,
    )
    group.users.add(substitute)
    workflow = create_test_workflow(
        user=starter,
        tasks_count=1,
    )
    task = workflow.tasks.get(number=1)
    task.skip_for_starter = True
    task.save(update_fields=['skip_for_starter'])
    skip_delegated_task_for_starter_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '.skip_delegated_task_for_starter',
    )
    service = VacationDelegationService(user=vacation_user)

    # act
    result = service._skip_tasks_for_starter(
        group=group,
        task_ids={task.id},
    )

    # assert
    assert result == set()
    skip_delegated_task_for_starter_mock.assert_not_called()


def test_skip_tasks_for_starter__not_skip_flag__not_called(mocker):

    # arrange
    account = create_test_account()
    vacation_user = create_test_admin(account=account)
    starter = create_test_not_admin(account=account)
    group = UserGroup.objects.create(
        name='Substitutes',
        type=UserGroupType.PERSONAL,
        account=account,
    )
    group.users.add(starter)
    workflow = create_test_workflow(
        user=starter,
        tasks_count=1,
    )
    task = workflow.tasks.get(number=1)
    skip_delegated_task_for_starter_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '.skip_delegated_task_for_starter',
    )
    service = VacationDelegationService(user=vacation_user)

    # act
    result = service._skip_tasks_for_starter(
        group=group,
        task_ids={task.id},
    )

    # assert
    assert result == set()
    skip_delegated_task_for_starter_mock.assert_not_called()


def test_skip_tasks_for_starter__empty_task_ids__empty(mocker):

    # arrange
    account = create_test_account()
    vacation_user = create_test_admin(account=account)
    group = UserGroup.objects.create(
        name='Substitutes',
        type=UserGroupType.PERSONAL,
        account=account,
    )
    workflow_action_service_init_mock = mocker.patch.object(
        WorkflowActionService,
        attribute='__init__',
        return_value=None,
    )
    service = VacationDelegationService(user=vacation_user)

    # act
    result = service._skip_tasks_for_starter(
        group=group,
        task_ids=set(),
    )

    # assert
    assert result == set()
    workflow_action_service_init_mock.assert_not_called()


def test_skip_tasks_for_starter__completed_wf__not_called(mocker):

    """
    The workflow is completed by the skip of the previous task
    of this workflow (e.g. by the "end workflow" condition),
    its active task is not skipped.
    """

    # arrange
    account = create_test_account()
    create_test_owner(account=account)
    vacation_user = create_test_admin(account=account)
    starter = create_test_not_admin(account=account)
    group = UserGroup.objects.create(
        name='Substitutes',
        type=UserGroupType.PERSONAL,
        account=account,
    )
    group.users.add(starter)
    workflow = create_test_workflow(
        user=starter,
        tasks_count=1,
        status=WorkflowStatus.DONE,
    )
    task = workflow.tasks.get(number=1)
    task.skip_for_starter = True
    task.save(update_fields=['skip_for_starter'])
    workflow_action_service_init_mock = mocker.patch.object(
        WorkflowActionService,
        attribute='__init__',
        return_value=None,
    )
    skip_delegated_task_for_starter_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '.skip_delegated_task_for_starter',
    )
    service = VacationDelegationService(user=vacation_user)

    # act
    result = service._skip_tasks_for_starter(
        group=group,
        task_ids={task.id},
    )

    # assert
    assert result == set()
    workflow_action_service_init_mock.assert_not_called()
    skip_delegated_task_for_starter_mock.assert_not_called()


def test_skip_tasks_for_starter__two_tasks_one_wf__wf_running(mocker):

    """
    Active and delayed tasks of one workflow are delegated.
    The skip of the active task delays the workflow, the skip
    of the delayed task starts the next task: the workflow runs.
    """

    # arrange
    account = create_test_account()
    starter = create_test_owner(account=account)
    vacation_user = create_test_admin(account=account)
    group = UserGroup.objects.create(
        name='Substitutes',
        type=UserGroupType.PERSONAL,
        account=account,
    )
    group.users.add(starter)
    workflow = create_test_workflow(user=starter)
    task_1 = workflow.tasks.get(number=1)
    task_1.skip_for_starter = True
    task_1.save(update_fields=['skip_for_starter'])
    task_1.taskperformer_set.all().delete()
    TaskPerformer.objects.create(
        task_id=task_1.id,
        user_id=vacation_user.id,
    )
    TaskPerformer.objects.create(
        task_id=task_1.id,
        group_id=group.id,
        type=PerformerType.GROUP,
    )
    task_2 = workflow.tasks.get(number=2)
    task_2.skip_for_starter = True
    task_2.status = TaskStatus.DELAYED
    task_2.save(update_fields=['skip_for_starter', 'status'])
    Delay.objects.create(
        task=task_2,
        workflow=workflow,
        duration=timedelta(days=1),
        start_date=timezone.now(),
    )
    task_2.taskperformer_set.all().delete()
    TaskPerformer.objects.create(
        task_id=task_2.id,
        user_id=vacation_user.id,
    )
    TaskPerformer.objects.create(
        task_id=task_2.id,
        group_id=group.id,
        type=PerformerType.GROUP,
    )
    task_3 = workflow.tasks.get(number=3)
    task_1_data = task_1.get_data_for_list()
    task_2_data = task_2.get_data_for_list()
    after_create_actions_mock = mocker.patch(
        'src.processes.services.events.'
        'WorkflowEventService._after_create_actions',
    )
    send_task_deleted_notification_mock = mocker.patch(
        'src.notifications.tasks.send_task_deleted_notification.delay',
    )
    send_new_task_notification_mock = mocker.patch(
        'src.notifications.tasks.send_new_task_notification.delay',
    )
    send_new_task_websocket_mock = mocker.patch(
        'src.notifications.tasks.send_new_task_websocket.delay',
    )
    service = VacationDelegationService(user=vacation_user)

    # act
    result = service._skip_tasks_for_starter(
        group=group,
        task_ids={task_1.id, task_2.id},
    )

    # assert
    assert result == {task_1.id, task_2.id}
    task_1.refresh_from_db()
    task_2.refresh_from_db()
    task_3.refresh_from_db()
    workflow.refresh_from_db()
    assert task_1.status == TaskStatus.SKIPPED
    assert task_2.status == TaskStatus.SKIPPED
    assert task_3.status == TaskStatus.ACTIVE
    assert workflow.status == WorkflowStatus.RUNNING
    task_1_skip_event = WorkflowEvent.objects.get(
        task=task_1,
        type=WorkflowEventType.TASK_SKIP,
    )
    task_2_skip_event = WorkflowEvent.objects.get(
        task=task_2,
        type=WorkflowEventType.TASK_SKIP,
    )
    task_3_start_event = WorkflowEvent.objects.get(
        task=task_3,
        type=WorkflowEventType.TASK_START,
    )
    assert after_create_actions_mock.call_count == 3
    after_create_actions_mock.assert_has_calls(
        [
            mocker.call(task_1_skip_event),
            mocker.call(task_2_skip_event),
            mocker.call(task_3_start_event),
        ],
    )
    assert send_task_deleted_notification_mock.call_count == 2
    send_task_deleted_notification_mock.assert_has_calls(
        [
            mocker.call(
                task_id=task_1.id,
                recipients=[
                    (starter.id, starter.email),
                    (vacation_user.id, vacation_user.email),
                ],
                account_id=account.id,
                task_data=task_1_data,
            ),
            mocker.call(
                task_id=task_2.id,
                recipients=[
                    (starter.id, starter.email),
                    (vacation_user.id, vacation_user.email),
                ],
                account_id=account.id,
                task_data=task_2_data,
            ),
        ],
    )
    send_new_task_notification_mock.assert_called_once_with(
        logging=account.log_api_requests,
        account_id=account.id,
        recipients=[(starter.id, starter.email, True)],
        task_id=task_3.id,
        task_name=task_3.name,
        task_data=task_3.get_data_for_list(),
        task_description=task_3.description,
        workflow_name=workflow.name,
        template_name=workflow.get_template_name(),
        workflow_starter_name=starter.name,
        workflow_starter_photo=starter.photo,
        due_date_timestamp=None,
        logo_lg=account.logo_lg,
        is_returned=False,
    )
    send_new_task_websocket_mock.assert_called_once_with(
        logging=account.log_api_requests,
        task_id=task_3.id,
        recipients=[(starter.id, starter.email, True)],
        account_id=account.id,
        task_data=task_3.get_data_for_list(),
    )


def test_delegate_tasks__skipped_task__excluded_from_task_ids(mocker):

    """
    Skipped task keeps the delegation event
    but is not counted as delegated.
    """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    substitute = create_test_admin(account=account)
    group = UserGroup.objects.create(
        name='Substitutes',
        type=UserGroupType.PERSONAL,
        account=account,
    )
    group.users.add(substitute)
    workflow = create_test_workflow(
        user=owner,
        tasks_count=1,
    )
    task = workflow.tasks.get(number=1)
    task_delegation_event_mock = mocker.patch(
        'src.processes.services.events.'
        'WorkflowEventService.task_delegation_event',
    )
    skip_tasks_for_starter_mock = mocker.patch(
        'src.accounts.services.vacation.VacationDelegationService'
        '._skip_tasks_for_starter',
        return_value={task.id},
    )
    service = VacationDelegationService(user=owner)

    # act
    task_ids, wf_ids = service.delegate_tasks(group=group)

    # assert
    assert task_ids == set()
    assert wf_ids == {workflow.id}
    task_delegation_event_mock.assert_called_once_with(
        task=task,
        user=owner,
        substitute_group=group,
    )
    skip_tasks_for_starter_mock.assert_called_once_with(
        group=group,
        task_ids={task.id},
    )


def test_delegate_tasks__existing_task_ids__not_checked_for_skip(mocker):

    """
    Already delegated tasks are not checked again
    by the periodic delegation.
    """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    group = UserGroup.objects.create(
        name='Substitutes',
        type=UserGroupType.PERSONAL,
        account=account,
    )
    workflow = create_test_workflow(
        user=owner,
        tasks_count=1,
    )
    task = workflow.tasks.get(number=1)
    task_delegation_event_mock = mocker.patch(
        'src.processes.services.events.'
        'WorkflowEventService.task_delegation_event',
    )
    skip_tasks_for_starter_mock = mocker.patch(
        'src.accounts.services.vacation.VacationDelegationService'
        '._skip_tasks_for_starter',
        return_value=set(),
    )
    service = VacationDelegationService(user=owner)

    # act
    task_ids, wf_ids = service.delegate_tasks(
        group=group,
        existing_task_ids={task.id},
    )

    # assert
    assert task_ids == {task.id}
    assert wf_ids == set()
    task_delegation_event_mock.assert_not_called()
    skip_tasks_for_starter_mock.assert_called_once_with(
        group=group,
        task_ids=set(),
    )


def test_delegate_tasks__group_task_skipped__excluded_from_task_ids(mocker):

    """
    Skipped task of the user's regular group keeps
    the delegation event but is not counted as delegated.
    """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    member = create_test_admin(account=account)
    regular_group = create_test_group(
        account=account,
        users=[owner, member],
    )
    group = UserGroup.objects.create(
        name='Substitutes',
        type=UserGroupType.PERSONAL,
        account=account,
    )
    workflow = create_test_workflow(
        user=member,
        tasks_count=1,
    )
    task = workflow.tasks.get(number=1)
    TaskPerformer.objects.create(
        task_id=task.id,
        group_id=regular_group.id,
        type=PerformerType.GROUP,
    )
    task_delegation_event_mock = mocker.patch(
        'src.processes.services.events.'
        'WorkflowEventService.task_delegation_event',
    )
    skip_tasks_for_starter_mock = mocker.patch(
        'src.accounts.services.vacation.VacationDelegationService'
        '._skip_tasks_for_starter',
        return_value={task.id},
    )
    service = VacationDelegationService(user=owner)

    # act
    task_ids, wf_ids = service.delegate_tasks(group=group)

    # assert
    assert task_ids == set()
    assert wf_ids == {workflow.id}
    task_delegation_event_mock.assert_called_once_with(
        task=task,
        user=owner,
        substitute_group=group,
    )
    skip_tasks_for_starter_mock.assert_called_once_with(
        group=group,
        task_ids={task.id},
    )


def test_update_existing__skipped_task__excluded_from_task_ids(mocker):

    """
    The workflow starter becomes a substitute: the already
    delegated task is skipped and is not passed
    to delegate_tasks as delegated.
    """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    starter = create_test_admin(account=account)
    group = UserGroup.objects.create(
        name='Substitutes',
        type=UserGroupType.PERSONAL,
        account=account,
    )
    vacation = UserVacation.objects.create(
        user=owner,
        account=account,
        substitute_group=group,
    )
    workflow = create_test_workflow(
        user=starter,
        tasks_count=1,
    )
    task = workflow.tasks.get(number=1)
    TaskPerformer.objects.create(
        task_id=task.id,
        group_id=group.id,
        type=PerformerType.GROUP,
    )
    skip_tasks_for_starter_mock = mocker.patch(
        'src.accounts.services.vacation.VacationDelegationService'
        '._skip_tasks_for_starter',
        return_value={task.id},
    )
    delegate_tasks_mock = mocker.patch(
        'src.accounts.services.vacation.VacationDelegationService'
        '.delegate_tasks',
        return_value=(set(), set()),
    )
    sync_members_mock = mocker.patch(
        'src.accounts.services.vacation.VacationDelegationService'
        '.sync_members',
    )
    service = VacationDelegationService(user=owner)

    # act
    result = service._update_existing(
        vacation=vacation,
        substitute_user_ids=[starter.id],
        absence_status=AbsenceStatus.VACATION,
    )

    # assert
    assert result == set()
    skip_tasks_for_starter_mock.assert_called_once_with(
        group=group,
        task_ids={task.id},
    )
    delegate_tasks_mock.assert_called_once_with(
        group=group,
        existing_task_ids=set(),
    )
    sync_members_mock.assert_called_once_with(
        wf_ids={workflow.id},
        substitute_user_ids=[starter.id],
        user_id=owner.id,
    )


def test_activate__substitute_is_wf_starter__task_skipped(mocker):

    """
    The task has "skip for starter", the vacation user is the only
    performer and the workflow starter is the substitute.
    The task is skipped as if the starter were assigned directly,
    the workflow moves to the next task.
    """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    starter = create_test_admin(account=account)
    template = create_test_template(
        user=owner,
        tasks_count=2,
        is_active=True,
    )
    workflow = create_test_workflow(
        user=starter,
        template=template,
    )
    task_1 = workflow.tasks.get(number=1)
    task_1.skip_for_starter = True
    task_1.save(update_fields=['skip_for_starter'])
    task_1_data = task_1.get_data_for_list()
    task_2 = workflow.tasks.get(number=2)
    task_delegation_event_mock = mocker.patch(
        'src.processes.services.events.'
        'WorkflowEventService.task_delegation_event',
    )
    after_create_actions_mock = mocker.patch(
        'src.processes.services.events.'
        'WorkflowEventService._after_create_actions',
    )
    send_task_deleted_notification_mock = mocker.patch(
        'src.notifications.tasks.send_task_deleted_notification.delay',
    )
    send_new_task_notification_mock = mocker.patch(
        'src.notifications.tasks.send_new_task_notification.delay',
    )
    send_new_task_websocket_mock = mocker.patch(
        'src.notifications.tasks.send_new_task_websocket.delay',
    )
    send_vacation_delegation_notification_mock = mocker.patch(
        'src.accounts.services.vacation.'
        'send_vacation_delegation_notification.delay',
    )
    send_user_updated_notification_mock = mocker.patch(
        'src.accounts.services.vacation.'
        'send_user_updated_notification.delay',
    )
    service = VacationDelegationService(user=owner)

    # act
    service.activate(substitute_user_ids=[starter.id])

    # assert
    task_1.refresh_from_db()
    task_2.refresh_from_db()
    owner.refresh_from_db()
    assert task_1.status == TaskStatus.SKIPPED
    assert task_2.status == TaskStatus.ACTIVE
    substitute_group = owner.vacation.substitute_group
    task_delegation_event_mock.assert_called_once_with(
        task=task_1,
        user=owner,
        substitute_group=substitute_group,
    )
    skip_event = WorkflowEvent.objects.get(
        task=task_1,
        type=WorkflowEventType.TASK_SKIP,
    )
    start_event = WorkflowEvent.objects.get(
        task=task_2,
        type=WorkflowEventType.TASK_START,
    )
    assert after_create_actions_mock.call_count == 2
    after_create_actions_mock.assert_has_calls(
        [
            mocker.call(skip_event),
            mocker.call(start_event),
        ],
    )
    send_task_deleted_notification_mock.assert_called_once_with(
        task_id=task_1.id,
        recipients=[
            (owner.id, owner.email),
            (starter.id, starter.email),
        ],
        account_id=account.id,
        task_data=task_1_data,
    )
    send_new_task_notification_mock.assert_called_once_with(
        logging=account.log_api_requests,
        account_id=account.id,
        recipients=[(owner.id, owner.email, True)],
        task_id=task_2.id,
        task_name=task_2.name,
        task_data=task_2.get_data_for_list(),
        task_description=task_2.description,
        workflow_name=workflow.name,
        template_name=workflow.get_template_name(),
        workflow_starter_name=starter.name,
        workflow_starter_photo=starter.photo,
        due_date_timestamp=None,
        logo_lg=account.logo_lg,
        is_returned=False,
    )
    send_new_task_websocket_mock.assert_called_once_with(
        logging=account.log_api_requests,
        task_id=task_2.id,
        recipients=[(owner.id, owner.email, True)],
        account_id=account.id,
        task_data=task_2.get_data_for_list(),
    )

    # the only delegated task is skipped, nothing to notify about
    send_vacation_delegation_notification_mock.assert_not_called()
    send_user_updated_notification_mock.assert_called_once_with(
        logging=account.log_api_requests,
        account_id=account.id,
        user_data=UserWebsocketSerializer(owner).data,
    )


def test_activate__change_substitute_to_wf_starter__task_skipped(mocker):

    """
    Vacation is already active and the task is delegated.
    The workflow starter becomes the new substitute:
    the already delegated task is skipped.
    """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    substitute = create_test_admin(
        account=account,
        email='sub@pneumatic.app',
    )
    starter = create_test_admin(
        account=account,
        email='starter@pneumatic.app',
    )
    template = create_test_template(
        user=owner,
        tasks_count=1,
        is_active=True,
    )
    workflow = create_test_workflow(
        user=starter,
        template=template,
    )
    task = workflow.tasks.get(number=1)
    task.skip_for_starter = True
    task.save(update_fields=['skip_for_starter'])
    sub_group = UserGroup.objects.create(
        name='Substitutes',
        type=UserGroupType.PERSONAL,
        account=account,
    )
    sub_group.users.add(substitute)
    UserVacation.objects.create(
        user=owner,
        account=account,
        substitute_group=sub_group,
    )
    TaskPerformer.objects.create(
        task=task,
        group=sub_group,
        type=PerformerType.GROUP,
    )
    task_delegation_event_mock = mocker.patch(
        'src.processes.services.events.'
        'WorkflowEventService.task_delegation_event',
    )
    after_create_actions_mock = mocker.patch(
        'src.processes.services.events.'
        'WorkflowEventService._after_create_actions',
    )
    send_task_deleted_notification_mock = mocker.patch(
        'src.notifications.tasks.send_task_deleted_notification.delay',
    )
    send_vacation_delegation_notification_mock = mocker.patch(
        'src.accounts.services.vacation.'
        'send_vacation_delegation_notification.delay',
    )
    send_user_updated_notification_mock = mocker.patch(
        'src.accounts.services.vacation.'
        'send_user_updated_notification.delay',
    )
    task_data = task.get_data_for_list()
    service = VacationDelegationService(user=owner)

    # act
    service.activate(substitute_user_ids=[starter.id])

    # assert
    task.refresh_from_db()
    workflow.refresh_from_db()
    owner.refresh_from_db()
    assert task.status == TaskStatus.SKIPPED
    assert workflow.status == WorkflowStatus.DONE
    task_delegation_event_mock.assert_not_called()
    skip_event = WorkflowEvent.objects.get(
        task=task,
        type=WorkflowEventType.TASK_SKIP,
    )
    ended_event = WorkflowEvent.objects.get(
        workflow=workflow,
        type=WorkflowEventType.ENDED,
    )
    assert after_create_actions_mock.call_count == 2
    after_create_actions_mock.assert_has_calls(
        [
            mocker.call(skip_event),
            mocker.call(ended_event),
        ],
    )
    send_task_deleted_notification_mock.assert_called_once_with(
        task_id=task.id,
        recipients=[
            (owner.id, owner.email),
            (starter.id, starter.email),
        ],
        account_id=account.id,
        task_data=task_data,
    )
    send_vacation_delegation_notification_mock.assert_not_called()
    send_user_updated_notification_mock.assert_called_once_with(
        logging=account.log_api_requests,
        account_id=account.id,
        user_data=UserWebsocketSerializer(owner).data,
    )
