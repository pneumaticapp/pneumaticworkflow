import pytest

from src.logs.events.enums import (
    EVENT_CLASSES,
    AccountEvents,
    EventCategory,
    TaskEvents,
    TemplateEvents,
    UserEvents,
    WorkflowEvents,
    event_names_of,
)
from src.processes.enums import WorkflowEventType


def test_event_names_of__events_class__constants_without_category():

    # arrange
    events_class = AccountEvents

    # act
    names = event_names_of(events_class=events_class)

    # assert
    assert names == (
        'account.update',
        'account.verify',
        'account.verification_resend',
        'tenant.create',
        'tenant.delete',
        'tenant.login_as',
    )


def test_event_names_of__invites_class__invites_among_user_events():

    # arrange
    events_class = UserEvents

    # act
    names = event_names_of(events_class=events_class)

    # assert
    assert 'user.login' in names
    assert 'invite.create' in names
    assert EventCategory.USERS not in names


def test_event_names_of__workflow_events__no_workflow_delay():

    """ A delay of the workflow is written as the delay of its task:
        the workflows category has no delay of its own. """

    # arrange
    events_class = WorkflowEvents

    # act
    names = event_names_of(events_class=events_class)

    # assert
    assert names == (
        'workflow.run',
        'workflow.complete',
        'workflow.ended',
        'workflow.revert',
        'workflow.ended_by_condition',
        'workflow.urgent',
        'workflow.not_urgent',
        'workflow.force_resume',
        'workflow.force_delay',
        'workflow.sub_workflow_run',
        'workflow.update',
        'workflow.terminate',
    )


def test_event_names_of__task_events__reactions_declared():

    # arrange
    events_class = TaskEvents

    # act
    names = event_names_of(events_class=events_class)

    # assert
    assert 'task.reaction_create' in names
    assert 'task.reaction_delete' in names


def test_event_names_of__template_events__create_and_update():

    """ A template is created or updated whatever its state: no
        separate type for a published template and a draft. """

    # arrange
    events_class = TemplateEvents

    # act
    names = event_names_of(events_class=events_class)

    # assert
    assert names == (
        'template.create',
        'template.update',
        'template.clone',
        'template.delete',
        'template.export',
        'template.draft_discard',
        'template.ai_generate',
        'template.library_fill',
        'template.library_import',
        'template_preset.create',
        'template_preset.update',
        'template_preset.delete',
        'template_preset.set_default',
        'fieldset.create',
        'fieldset.update',
        'fieldset.clone',
        'fieldset.delete',
    )


@pytest.mark.parametrize('events_class', EVENT_CLASSES)
def test_event_classes__every_class__category_is_declared(events_class):

    # arrange
    declared = EventCategory.VALUES

    # act
    category = events_class.CATEGORY

    # assert
    assert category in declared
    assert category != EventCategory.OTHER


def test_workflow_event_type__every_constant__has_a_journal_type():

    """ Every WorkflowEvent of the feed is written next to a record of
        the journal (AuditEventService is called beside
        WorkflowEventService), so a new constant of WorkflowEventType
        needs a row here and a type of the journal. The test fails on
        a constant without a row: the row is where the decision is
        made. """

    # arrange
    journal_type_by_workflow_event_type = {
        WorkflowEventType.RUN: WorkflowEvents.RUN,
        WorkflowEventType.COMPLETE: WorkflowEvents.COMPLETE,
        WorkflowEventType.ENDED: WorkflowEvents.ENDED,

        # A delay from the template is written as the delay of its task
        # (TASK_DELAY); workflow_delay_event has no caller.
        WorkflowEventType.DELAY: None,
        WorkflowEventType.REVERT: WorkflowEvents.REVERT,
        WorkflowEventType.ENDED_BY_CONDITION: (
            WorkflowEvents.ENDED_BY_CONDITION
        ),
        WorkflowEventType.URGENT: WorkflowEvents.URGENT,
        WorkflowEventType.NOT_URGENT: WorkflowEvents.NOT_URGENT,
        WorkflowEventType.FORCE_RESUME: WorkflowEvents.FORCE_RESUME,
        WorkflowEventType.FORCE_DELAY: WorkflowEvents.FORCE_DELAY,
        WorkflowEventType.SUB_WORKFLOW_RUN: WorkflowEvents.SUB_WORKFLOW_RUN,
        WorkflowEventType.TASK_START: TaskEvents.START,
        WorkflowEventType.TASK_COMPLETE: TaskEvents.COMPLETE,
        WorkflowEventType.TASK_REVERT: TaskEvents.REVERT,
        WorkflowEventType.COMMENT: TaskEvents.COMMENT,
        WorkflowEventType.TASK_SKIP: TaskEvents.SKIP,
        WorkflowEventType.TASK_SKIP_NO_PERFORMERS: (
            TaskEvents.SKIP_NO_PERFORMERS
        ),
        WorkflowEventType.TASK_PERFORMER_CREATED: (
            TaskEvents.PERFORMER_CREATED
        ),
        WorkflowEventType.TASK_PERFORMER_DELETED: (
            TaskEvents.PERFORMER_DELETED
        ),
        WorkflowEventType.DUE_DATE_CHANGED: TaskEvents.DUE_DATE_CHANGED,
        WorkflowEventType.TASK_PERFORMER_GROUP_CREATED: (
            TaskEvents.PERFORMER_GROUP_CREATED
        ),
        WorkflowEventType.TASK_PERFORMER_GROUP_DELETED: (
            TaskEvents.PERFORMER_GROUP_DELETED
        ),
        WorkflowEventType.TASK_DELAY: TaskEvents.DELAY,
        WorkflowEventType.TASK_DELEGATION: TaskEvents.DELEGATION,
    }
    journal_types = set(
        event_names_of(events_class=WorkflowEvents)
        + event_names_of(events_class=TaskEvents),
    )

    # act
    declared_workflow_event_types = {
        value for name, value in vars(WorkflowEventType).items()
        if name.isupper() and isinstance(value, int)
    }
    mapped_journal_types = {
        journal_type
        for journal_type in journal_type_by_workflow_event_type.values()
        if journal_type is not None
    }

    # assert
    assert set(journal_type_by_workflow_event_type) == (
        declared_workflow_event_types
    )
    assert mapped_journal_types <= journal_types
