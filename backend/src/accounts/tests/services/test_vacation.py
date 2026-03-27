import pytest

from src.accounts.enums import AbsenceStatus, UserGroupType
from src.accounts.models import UserGroup
from src.accounts.services.vacation import VacationDelegationService
from src.processes.enums import (
    DirectlyStatus,
    PerformerType,
    TaskStatus,
)
from src.processes.models.workflows.task import TaskPerformer
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_admin,
    create_test_group,
    create_test_owner,
    create_test_template,
    create_test_workflow,
)


pytestmark = pytest.mark.django_db


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
    group = owner.vacation_substitute_group
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


def test_activate__freezes_performers__ok(mocker):

    """
    Freezes USER performers to DELEGATED via bulk update.
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
    assert performer.directly_status == DirectlyStatus.DELEGATED
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
        group=owner.vacation_substitute_group,
    ).exists()
    assert group_perf_exists is True
    task_delegation_event_mock.assert_called_once_with(
        task=mocker.ANY,
        user=owner,
        substitute_group=owner.vacation_substitute_group,
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
    sub_group = owner.vacation_substitute_group
    sub_perf_exists = TaskPerformer.objects.filter(
        task=task,
        type=PerformerType.GROUP,
        group=sub_group,
    ).exists()
    assert sub_perf_exists is True
    task_delegation_event_mock.assert_not_called()


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

    # act
    service = VacationDelegationService(user=owner)
    service.activate(substitute_user_ids=[substitute.id])

    # assert
    owner.refresh_from_db()
    assert owner.absence_status == AbsenceStatus.VACATION
    task_delegation_event_mock.assert_called_once_with(
        task=mocker.ANY,
        user=owner,
        substitute_group=mocker.ANY,
    )


def test_activate__adds_members__ok(mocker):

    """
    Adds substitutes to workflow.members.
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
    assert workflow.members.filter(id=substitute.id).exists()
    task_delegation_event_mock.assert_called_once_with(
        task=mocker.ANY,
        user=owner,
        substitute_group=mocker.ANY,
    )


def test_activate__mutes_notifs__ok(mocker):

    """
    Mutes notifications and saves originals.
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
    assert owner.is_new_tasks_subscriber is False
    assert owner.is_complete_tasks_subscriber is False
    assert owner._saved_is_new_tasks_subscriber is True
    assert owner._saved_is_complete_tasks_subscriber is True
    task_delegation_event_mock.assert_called_once_with(
        task=mocker.ANY,
        user=owner,
        substitute_group=mocker.ANY,
    )


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
    assert owner.absence_status == AbsenceStatus.VACATION
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
    assert owner.absence_status == AbsenceStatus.SICK_LEAVE


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
    assert owner.vacation_substitute_group is not None
    assert owner.vacation_substitute_group.type == (
        UserGroupType.PERSONAL
    )
    task_delegation_event_mock.assert_called_once_with(
        task=mocker.ANY,
        user=owner,
        substitute_group=owner.vacation_substitute_group,
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
    group_id = owner.vacation_substitute_group_id

    # act — update substitutes
    service.activate(substitute_user_ids=[sub2.id])

    # assert
    owner.refresh_from_db()

    # same group is reused
    assert owner.vacation_substitute_group_id == group_id

    # sub2 is now the only member
    members = list(
        owner.vacation_substitute_group.users
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

    # act — switch to SICK_LEAVE
    service.activate(
        substitute_user_ids=[substitute.id],
        absence_status=AbsenceStatus.SICK_LEAVE,
    )

    # assert
    owner.refresh_from_db()
    assert owner.absence_status == AbsenceStatus.SICK_LEAVE


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
    assert owner.absence_status == AbsenceStatus.VACATION
    assert owner.vacation_substitute_group is not None


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
    task_delegation_event_mock = mocker.patch(
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
    task_delegation_event_mock.assert_called_once_with(
        task=mocker.ANY,
        user=owner,
        substitute_group=mocker.ANY,
    )


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
    task_delegation_event_mock = mocker.patch(
        'src.processes.services.events.'
        'WorkflowEventService.task_delegation_event',
    )
    service = VacationDelegationService(user=owner)
    service.activate(substitute_user_ids=[substitute.id])
    owner.refresh_from_db()
    group_id = owner.vacation_substitute_group_id

    # act
    service.deactivate()

    # assert
    assert not UserGroup.objects.filter(id=group_id).exists()
    task_delegation_event_mock.assert_called_once_with(
        task=mocker.ANY,
        user=owner,
        substitute_group=mocker.ANY,
    )


def test_deactivate__no_group__ok():

    """
    No error when vacation_substitute_group is None.
    """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    assert owner.vacation_substitute_group is None

    # act
    service = VacationDelegationService(user=owner)
    service.deactivate()

    # assert
    owner.refresh_from_db()
    assert owner.absence_status == AbsenceStatus.ACTIVE


def test_deactivate__restores_notifs__ok(mocker):

    """
    Restores notifications from saved values.
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
    service.activate(substitute_user_ids=[substitute.id])

    # act
    service.deactivate()

    # assert
    owner.refresh_from_db()
    assert owner.is_new_tasks_subscriber is True
    assert owner.is_complete_tasks_subscriber is True
    assert owner._saved_is_new_tasks_subscriber is None
    assert owner._saved_is_complete_tasks_subscriber is None
    task_delegation_event_mock.assert_called_once_with(
        task=mocker.ANY,
        user=owner,
        substitute_group=mocker.ANY,
    )


def test_deactivate__notifs_default__ok():

    """
    Defaults notifications to True when saved is None.
    """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    owner._saved_notify_about_tasks = None
    owner._saved_is_new_tasks_subscriber = None
    owner._saved_is_complete_tasks_subscriber = None
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
    task_delegation_event_mock = mocker.patch(
        'src.processes.services.events.'
        'WorkflowEventService.task_delegation_event',
    )
    service = VacationDelegationService(user=owner)
    service.activate(substitute_user_ids=[substitute.id])

    # act
    service.deactivate()

    # assert
    owner.refresh_from_db()
    assert owner.absence_status == AbsenceStatus.ACTIVE
    task_delegation_event_mock.assert_called_once_with(
        task=mocker.ANY,
        user=owner,
        substitute_group=mocker.ANY,
    )


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
    task_delegation_event_mock = mocker.patch(
        'src.processes.services.events.'
        'WorkflowEventService.task_delegation_event',
    )
    service = VacationDelegationService(user=owner)
    service.activate(substitute_user_ids=[substitute.id])

    # act
    service.deactivate()

    # assert
    owner.refresh_from_db()
    assert owner.vacation_start_date is None
    assert owner.vacation_end_date is None
    assert owner.vacation_substitute_group is None
    assert owner._saved_notify_about_tasks is None
    assert owner._saved_is_new_tasks_subscriber is None
    assert owner._saved_is_complete_tasks_subscriber is None
    task_delegation_event_mock.assert_called_once_with(
        task=mocker.ANY,
        user=owner,
        substitute_group=mocker.ANY,
    )


def test_clear_sub_groups__removes_user__ok():

    """
    Removes user from personal groups.
    """

    # arrange
    account = create_test_account()
    create_test_owner(account=account)
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
    assert owner.absence_status == AbsenceStatus.ACTIVE
    assert owner.vacation_substitute_group is None


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

    # assert — no exception raised
    assert True


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
