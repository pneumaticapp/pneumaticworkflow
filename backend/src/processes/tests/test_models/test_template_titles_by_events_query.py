import pytest

from src.executor import RawSqlExecutor
from src.processes.enums import WorkflowEventType
from src.processes.queries import (
    HighlightsQuery,
    TemplateTitlesByEventsQuery,
)
from src.processes.tests.fixtures import (
    create_test_event,
    create_test_owner,
    create_test_template,
    create_test_workflow,
)

pytestmark = pytest.mark.django_db


def test_event_types__both_queries__the_same_whitelist():

    """ The highlights feed and the template titles of the same feed
        used to hold two copies of the list, and they drifted apart.
        Their composition has to stay equal, not merely similar. """

    # act
    highlights = set(HighlightsQuery.event_types)
    titles = set(TemplateTitlesByEventsQuery.event_types)

    # assert
    assert highlights == titles
    assert titles == set(WorkflowEventType.HIGHLIGHT_TYPES)


def test_get_sql__event_types__every_type_as_a_parameter():

    """ The whitelist became a tuple when the two copies were merged,
        and _to_sql_list has to bind a tuple the way it bound a list:
        one placeholder and one parameter per type. """

    # arrange
    user = create_test_owner()
    query = TemplateTitlesByEventsQuery(user=user)

    # act
    sql, params = query.get_sql()
    event_params = {
        key: value for key, value in params.items()
        if key.startswith('event_type')
    }

    # assert
    assert set(event_params.values()) == set(
        WorkflowEventType.HIGHLIGHT_TYPES,
    )
    assert len(event_params) == len(WorkflowEventType.HIGHLIGHT_TYPES)
    assert '%(event_type_0)s' in sql


def test_get_sql__event_of_a_whitelisted_type__template_returned():

    # arrange
    user = create_test_owner()
    template = create_test_template(user=user, is_active=True)
    workflow = create_test_workflow(user=user, template=template)
    create_test_event(
        workflow=workflow,
        user=user,
        type_event=WorkflowEventType.RUN,
    )
    query = TemplateTitlesByEventsQuery(user=user)

    # act
    data = list(RawSqlExecutor.fetch(*query.get_sql()))

    # assert
    assert data == [
        {'id': template.id, 'name': template.name, 'count': 1},
    ]


def test_get_sql__sub_workflow_run_event__template_returned():

    """ SUB_WORKFLOW_RUN is in the whitelist and was the type missing
        from CHOICES until P2-T2. """

    # arrange
    user = create_test_owner()
    template = create_test_template(user=user, is_active=True)
    workflow = create_test_workflow(user=user, template=template)
    create_test_event(
        workflow=workflow,
        user=user,
        type_event=WorkflowEventType.SUB_WORKFLOW_RUN,
    )
    query = TemplateTitlesByEventsQuery(user=user)

    # act
    data = list(RawSqlExecutor.fetch(*query.get_sql()))

    # assert
    assert len(data) == 1
    assert data[0]['id'] == template.id


@pytest.mark.parametrize(
    'type_event',
    [
        WorkflowEventType.TASK_DELAY,
        WorkflowEventType.TASK_DELEGATION,
        WorkflowEventType.TASK_START,
    ],
)
def test_get_sql__event_hidden_from_the_feed__nothing_returned(
    type_event,
):

    # arrange
    user = create_test_owner()
    template = create_test_template(user=user, is_active=True)
    workflow = create_test_workflow(user=user, template=template)
    create_test_event(
        workflow=workflow,
        user=user,
        type_event=type_event,
    )
    query = TemplateTitlesByEventsQuery(user=user)

    # act
    data = list(RawSqlExecutor.fetch(*query.get_sql()))

    # assert
    assert data == []


def test_get_sql__event_of_another_user__nothing_returned():

    # arrange
    user = create_test_owner()
    other_user = create_test_owner(email='other@test.test')
    template = create_test_template(user=user, is_active=True)
    workflow = create_test_workflow(user=user, template=template)
    create_test_event(
        workflow=workflow,
        user=user,
        type_event=WorkflowEventType.RUN,
    )
    query = TemplateTitlesByEventsQuery(user=other_user)

    # act
    data = list(RawSqlExecutor.fetch(*query.get_sql()))

    # assert
    assert data == []
