import pytest
from src.processes.enums import (
    PredicateType,
    PredicateOperator,
    ConditionAction
)
from src.processes.utils.common import (
    get_tasks_parents,
)


def test_get_parents__task_without_conditions__ok():

    # arrange
    task_1_api_name = 'task-1'
    task_2_api_name = 'task-2'
    tasks_data = [
        {
            'number': 1,
            'name': 'Task 1',
            'api_name': task_1_api_name
        },
        {
            'number': 2,
            'name': 'Task 2',
            'api_name': task_2_api_name,
            'conditions': [
                {
                    'order': 1,
                    'action': ConditionAction.START_TASK,
                    'rules': [
                        {
                            'predicates': [
                                {
                                    'field_type': PredicateType.TASK,
                                    'operator': PredicateOperator.COMPLETED,
                                    'api_name': 'predicate-1',
                                    'field': task_1_api_name,
                                    'value': None,
                                }
                            ]
                        }
                    ]
                }
            ]
        }
    ]

    # act
    ancestors = get_tasks_parents(tasks_data)

    # assert
    assert ancestors[task_1_api_name] == []
    assert ancestors[task_2_api_name] == [task_1_api_name]


@pytest.mark.parametrize(
    'cond_action',
    (ConditionAction.SKIP_TASK, ConditionAction.END_WORKFLOW)
)
def test_get_parents__task_with_not_start_conditions__ok(cond_action):

    # arrange
    task_1_api_name = 'task-1'
    task_2_api_name = 'task-2'
    tasks_data = [
        {
            'number': 1,
            'name': 'Task 1',
            'api_name': task_1_api_name
        },
        {
            'number': 2,
            'name': 'Task 2',
            'api_name': task_2_api_name,
            'conditions': [
                {
                    'order': 1,
                    'action': cond_action,
                    'rules': [
                        {
                            'predicates': [
                                {
                                    'field_type': PredicateType.TASK,
                                    'operator': PredicateOperator.COMPLETED,
                                    'api_name': 'predicate-1',
                                    'field': task_1_api_name,
                                    'value': None,
                                }
                            ]
                        }
                    ]
                }
            ]
        }
    ]

    # act
    ancestors = get_tasks_parents(tasks_data)

    # assert
    assert ancestors[task_1_api_name] == []
    assert ancestors[task_2_api_name] == []


def test_get_parents__two_start_predicates__ok():

    # arrange
    task_1_api_name = 'task-1'
    task_2_api_name = 'task-2'
    task_3_api_name = 'task-3'
    tasks_data = [
        {
            'number': 1,
            'name': 'Task 1',
            'api_name': task_1_api_name,
            'conditions': [
                {
                    'order': 1,
                    'action': ConditionAction.START_TASK,
                    'rules': [
                        {
                            'predicates': [
                                {
                                    'field_type': PredicateType.TASK,
                                    'operator': PredicateOperator.COMPLETED,
                                    'field': task_2_api_name,
                                    'value': None,
                                },
                                {
                                    'field_type': PredicateType.TASK,
                                    'operator': PredicateOperator.COMPLETED,
                                    'field': task_3_api_name,
                                    'value': None,
                                }
                            ]
                        }
                    ]
                }
            ]
        },
        {
            'number': 2,
            'name': 'Task 2',
            'api_name': task_2_api_name
        },
        {
            'number': 3,
            'name': 'Task 3',
            'api_name': task_3_api_name
        }
    ]

    # act
    ancestors = get_tasks_parents(tasks_data)

    # assert
    assert ancestors[task_1_api_name] == [task_2_api_name, task_3_api_name]
    assert ancestors[task_2_api_name] == []
    assert ancestors[task_3_api_name] == []


def test_get_parents__linear_template__ok():

    # arrange
    task_1_api_name = 'task-1'
    task_2_api_name = 'task-2'
    tasks_data = [
        {
            'number': 1,
            'name': 'Task 1',
            'api_name': task_1_api_name,
            'conditions': [
                {
                    'order': 1,
                    'action': ConditionAction.START_TASK,
                    'rules': [
                        {
                            'predicates': [
                                {
                                    'field_type': PredicateType.KICKOFF,
                                    'operator': PredicateOperator.COMPLETED,
                                    'api_name': 'predicate-1',
                                    'field': None,
                                    'value': None,
                                }
                            ]
                        }
                    ]
                }
            ]
        },
        {
            'number': 2,
            'name': 'Task 2',
            'api_name': task_2_api_name,
            'conditions': [
                {
                    'order': 1,
                    'action': ConditionAction.START_TASK,
                    'rules': [
                        {
                            'predicates': [
                                {
                                    'field_type': PredicateType.TASK,
                                    'operator': PredicateOperator.COMPLETED,
                                    'api_name': 'predicate-1',
                                    'field': task_1_api_name,
                                    'value': None,
                                }
                            ]
                        }
                    ]
                }
            ]
        }
    ]

    # act
    ancestors = get_tasks_parents(tasks_data)

    # assert
    assert ancestors[task_1_api_name] == []
    assert ancestors[task_2_api_name] == [task_1_api_name]


def test_get_parents__deleted_task_in_conditions__skip():

    # arrange
    task_1_api_name = 'task-1'
    task_2_api_name = 'task-2'
    deleted_task_api_name = 'task-3'
    tasks_data = [
        {
            'number': 1,
            'name': 'Task 1',
            'api_name': task_1_api_name,
            'conditions': [
                {
                    'order': 1,
                    'action': ConditionAction.START_TASK,
                    'rules': [
                        {
                            'predicates': [
                                {
                                    'field_type': PredicateType.TASK,
                                    'operator': PredicateOperator.COMPLETED,
                                    'api_name': 'predicate-1',
                                    'field': deleted_task_api_name,
                                    'value': None,
                                }
                            ]
                        }
                    ]
                }
            ]
        },
        {
            'number': 2,
            'name': 'Task 2',
            'api_name': task_2_api_name,
            'conditions': [
                {
                    'order': 1,
                    'action': ConditionAction.START_TASK,
                    'rules': [
                        {
                            'predicates': [
                                {
                                    'field_type': PredicateType.TASK,
                                    'operator': PredicateOperator.COMPLETED,
                                    'api_name': 'predicate-1',
                                    'field': task_1_api_name,
                                    'value': None,
                                }
                            ]
                        }
                    ]
                }
            ]
        }
    ]

    # act
    ancestors = get_tasks_parents(tasks_data)

    # assert
    assert ancestors[task_1_api_name] == []
    assert ancestors[task_2_api_name] == [task_1_api_name]
