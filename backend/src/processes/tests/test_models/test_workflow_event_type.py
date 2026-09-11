from importlib import import_module

import pytest

from src.processes.enums import WorkflowEventType


def test_choices__every_declared_constant__has_a_label():

    """ A constant missing from CHOICES reaches the database anyway,
        the admin site and the API schema then show a bare number
        (P2-T2: SUB_WORKFLOW_RUN was such a constant). """

    # arrange
    declared = {
        value for name, value in vars(WorkflowEventType).items()
        if name.isupper() and isinstance(value, int)
    }

    # act
    labelled = {value for value, _ in WorkflowEventType.CHOICES}

    # assert
    assert declared - labelled == set()


def test_choices__labels__filled_and_unique():

    # act
    labels = [label for _, label in WorkflowEventType.CHOICES]

    # assert
    assert len(labels) == len(set(labels))
    assert '' not in labels


def test_choices__sub_workflow_run__has_a_label():

    # act
    labels = dict(WorkflowEventType.CHOICES)

    # assert
    assert labels[WorkflowEventType.SUB_WORKFLOW_RUN] == (
        'Sub-workflow started'
    )


def test_literals__every_declared_constant__accepted():

    """ A constant missing from LITERALS is rejected by the type
        checker for every service that passes it (P2-T2:
        TASK_DELEGATION was such a constant). """

    # arrange
    declared = {
        value for name, value in vars(WorkflowEventType).items()
        if name.isupper() and isinstance(value, int)
    }

    # act
    accepted = set(WorkflowEventType.LITERALS.__args__)

    # assert
    assert declared - accepted == set()


@pytest.mark.parametrize('hidden_type', (
    WorkflowEventType.TASK_START,
    WorkflowEventType.DELAY,
    WorkflowEventType.TASK_SKIP,
    WorkflowEventType.ENDED_BY_CONDITION,
    WorkflowEventType.TASK_SKIP_NO_PERFORMERS,
    WorkflowEventType.TASK_DELAY,
    WorkflowEventType.TASK_DELEGATION,
))
def test_highlight_types__hidden_type__excluded(hidden_type):

    """ The seven types the highlights feed hides on purpose. The
        frontend allow list (Highlights/FeedItem.tsx) leaves out the
        same ones, and widening the whitelist here alone only makes
        the query heavier. Listed as exclusions on purpose: repeating
        HIGHLIGHT_TYPES would compare the constant with a copy of
        itself. """

    # act
    included = hidden_type in WorkflowEventType.HIGHLIGHT_TYPES

    # assert
    assert included is False


def test_highlight_types__every_other_type__included():

    # arrange
    hidden = {
        WorkflowEventType.TASK_START,
        WorkflowEventType.DELAY,
        WorkflowEventType.TASK_SKIP,
        WorkflowEventType.ENDED_BY_CONDITION,
        WorkflowEventType.TASK_SKIP_NO_PERFORMERS,
        WorkflowEventType.TASK_DELAY,
        WorkflowEventType.TASK_DELEGATION,
    }
    declared = {
        value for name, value in vars(WorkflowEventType).items()
        if name.isupper() and isinstance(value, int)
    }

    # act
    missing = declared - hidden - set(WorkflowEventType.HIGHLIGHT_TYPES)

    # assert
    assert missing == set()


def test_highlight_types__composition__without_duplicates():

    # arrange
    declared = {
        value for name, value in vars(WorkflowEventType).items()
        if name.isupper() and isinstance(value, int)
    }

    # act
    types = WorkflowEventType.HIGHLIGHT_TYPES

    # assert
    assert len(types) == len(set(types))
    assert len(types) == len(declared) - 7


def test_choices__migration_0260__same_pairs_as_the_enum():

    """ The column of the database carries the choices of the last
        migration, not of the enum: a constant added to CHOICES
        without a migration shows a bare number in the admin site and
        leaves makemigrations with a pending change forever. """

    # arrange
    migration = import_module(
        'src.processes.migrations.0260_workflowevent_type_choices',
    )
    field = migration.Migration.operations[0].field

    # act
    migrated = tuple(tuple(pair) for pair in field.choices)

    # assert
    assert migrated == tuple(
        tuple(pair) for pair in WorkflowEventType.CHOICES
    )
