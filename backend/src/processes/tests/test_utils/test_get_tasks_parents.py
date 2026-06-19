import pytest

from src.processes.enums import (
    ConditionAction,
    PredicateOperator,
    PredicateType,
)
from src.processes.utils.common import (
    get_tasks_parents,
)


class TestCompletedTaskOperator:

    def test_get_parents__task_without_conditions__ok(self):

        # arrange
        task_1_api_name = 'task-1'
        task_2_api_name = 'task-2'
        condition = {
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
                        },
                    ],
                },
            ],
        }
        tasks_data = [
            {
                'number': 1,
                'name': 'Task 1',
                'api_name': task_1_api_name,
            },
            {
                'number': 2,
                'name': 'Task 2',
                'api_name': task_2_api_name,
                'conditions': [condition],
            },
        ]

        # act
        ancestors = get_tasks_parents(tasks_data)

        # assert
        assert ancestors[task_1_api_name] == []
        assert ancestors[task_2_api_name] == [task_1_api_name]

    @pytest.mark.parametrize(
        'cond_action',
        (ConditionAction.SKIP_TASK, ConditionAction.END_WORKFLOW),
    )
    def test_get_parents__task_with_not_start_conditions__ok(
        self,
        cond_action,
    ):

        # arrange
        task_1_api_name = 'task-1'
        task_2_api_name = 'task-2'
        condition = {
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
                        },
                    ],
                },
            ],
        }
        tasks_data = [
            {
                'number': 1,
                'name': 'Task 1',
                'api_name': task_1_api_name,
            },
            {
                'number': 2,
                'name': 'Task 2',
                'api_name': task_2_api_name,
                'conditions': [condition],
            },
        ]

        # act
        ancestors = get_tasks_parents(tasks_data)

        # assert
        assert ancestors[task_1_api_name] == []
        assert ancestors[task_2_api_name] == []

    def test_get_parents__two_start_predicates__ok(self):

        # arrange
        task_1_api_name = 'task-1'
        task_2_api_name = 'task-2'
        task_3_api_name = 'task-3'
        condition = {
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
                        },
                    ],
                },
            ],
        }
        tasks_data = [
            {
                'number': 1,
                'name': 'Task 1',
                'api_name': task_1_api_name,
                'conditions': [condition],
            },
            {
                'number': 2,
                'name': 'Task 2',
                'api_name': task_2_api_name,
            },
            {
                'number': 3,
                'name': 'Task 3',
                'api_name': task_3_api_name,
            },
        ]

        # act
        ancestors = get_tasks_parents(tasks_data)

        # assert
        assert ancestors[task_1_api_name] == [task_2_api_name, task_3_api_name]
        assert ancestors[task_2_api_name] == []
        assert ancestors[task_3_api_name] == []

    def test_get_parents__linear_template__ok(self):

        # arrange
        task_1_api_name = 'task-1'
        task_2_api_name = 'task-2'
        condition_1 = {
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
                        },
                    ],
                },
            ],
        }
        condition_2 = {
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
                        },
                    ],
                },
            ],
        }
        tasks_data = [
            {
                'number': 1,
                'name': 'Task 1',
                'api_name': task_1_api_name,
                'conditions': [condition_1],
            },
            {
                'number': 2,
                'name': 'Task 2',
                'api_name': task_2_api_name,
                'conditions': [condition_2],
            },
        ]

        # act
        ancestors = get_tasks_parents(tasks_data)

        # assert
        assert ancestors[task_1_api_name] == []
        assert ancestors[task_2_api_name] == [task_1_api_name]

    def test_get_parents__deleted_task_in_conditions__skip(self):

        # arrange
        task_1_api_name = 'task-1'
        task_2_api_name = 'task-2'
        deleted_task_api_name = 'task-3'
        condition_1 = {
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
                        },
                    ],
                },
            ],
        }

        condition_2 = {
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
                        },
                    ],
                },
            ],
        }
        tasks_data = [
            {
                'number': 1,
                'name': 'Task 1',
                'api_name': task_1_api_name,
                'conditions': [condition_1],
            },
            {
                'number': 2,
                'name': 'Task 2',
                'api_name': task_2_api_name,
                'conditions': [condition_2],
            },
        ]

        # act
        ancestors = get_tasks_parents(tasks_data)

        # assert
        assert ancestors[task_1_api_name] == []
        assert ancestors[task_2_api_name] == [task_1_api_name]


class TestSkippedTaskOperator:

    def test_get_parents__task_without_conditions__ok(self):

        # arrange
        task_1_api_name = 'task-1'
        task_2_api_name = 'task-2'
        tasks_data = [
            {
                'number': 1,
                'name': 'Task 1',
                'api_name': task_1_api_name,
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
                                        'operator': PredicateOperator.SKIPPED,
                                        'api_name': 'predicate-1',
                                        'field': task_1_api_name,
                                        'value': None,
                                    },
                                ],
                            },
                        ],
                    },
                ],
            },
        ]

        # act
        ancestors = get_tasks_parents(tasks_data)

        # assert
        assert ancestors[task_1_api_name] == []
        assert ancestors[task_2_api_name] == [task_1_api_name]

    @pytest.mark.parametrize(
        'cond_action',
        (ConditionAction.SKIP_TASK, ConditionAction.END_WORKFLOW),
    )
    def test_get_parents__task_with_not_start_conditions__ok(
        self,
        cond_action,
    ):

        # arrange
        task_1_api_name = 'task-1'
        task_2_api_name = 'task-2'
        tasks_data = [
            {
                'number': 1,
                'name': 'Task 1',
                'api_name': task_1_api_name,
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
                                        'operator': PredicateOperator.SKIPPED,
                                        'api_name': 'predicate-1',
                                        'field': task_1_api_name,
                                        'value': None,
                                    },
                                ],
                            },
                        ],
                    },
                ],
            },
        ]

        # act
        ancestors = get_tasks_parents(tasks_data)

        # assert
        assert ancestors[task_1_api_name] == []
        assert ancestors[task_2_api_name] == []

    def test_get_parents__two_start_predicates__ok(self):

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
                                        'operator': PredicateOperator.SKIPPED,
                                        'field': task_2_api_name,
                                        'value': None,
                                    },
                                    {
                                        'field_type': PredicateType.TASK,
                                        'operator': PredicateOperator.SKIPPED,
                                        'field': task_3_api_name,
                                        'value': None,
                                    },
                                ],
                            },
                        ],
                    },
                ],
            },
            {
                'number': 2,
                'name': 'Task 2',
                'api_name': task_2_api_name,
            },
            {
                'number': 3,
                'name': 'Task 3',
                'api_name': task_3_api_name,
            },
        ]

        # act
        ancestors = get_tasks_parents(tasks_data)

        # assert
        assert ancestors[task_1_api_name] == [task_2_api_name, task_3_api_name]
        assert ancestors[task_2_api_name] == []
        assert ancestors[task_3_api_name] == []

    def test_get_parents__linear_template__ok(self):

        # arrange
        task_1_api_name = 'task-1'
        task_2_api_name = 'task-2'
        condition_1 = {
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
                        },
                    ],
                },
            ],
        }
        condition_2 = {
            'order': 1,
            'action': ConditionAction.START_TASK,
            'rules': [
                {
                    'predicates': [
                        {
                            'field_type': PredicateType.TASK,
                            'operator': PredicateOperator.SKIPPED,
                            'api_name': 'predicate-1',
                            'field': task_1_api_name,
                            'value': None,
                        },
                    ],
                },
            ],
        }
        tasks_data = [
            {
                'number': 1,
                'name': 'Task 1',
                'api_name': task_1_api_name,
                'conditions': [condition_1],
            },
            {
                'number': 2,
                'name': 'Task 2',
                'api_name': task_2_api_name,
                'conditions': [condition_2],
            },
        ]

        # act
        ancestors = get_tasks_parents(tasks_data)

        # assert
        assert ancestors[task_1_api_name] == []
        assert ancestors[task_2_api_name] == [task_1_api_name]

    def test_get_parents__deleted_task_in_conditions__skip(self):

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
                                        'operator': PredicateOperator.SKIPPED,
                                        'api_name': 'predicate-1',
                                        'field': deleted_task_api_name,
                                        'value': None,
                                    },
                                ],
                            },
                        ],
                    },
                ],
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
                                        'operator': PredicateOperator.SKIPPED,
                                        'api_name': 'predicate-1',
                                        'field': task_1_api_name,
                                        'value': None,
                                    },
                                ],
                            },
                        ],
                    },
                ],
            },
        ]

        # act
        ancestors = get_tasks_parents(tasks_data)

        # assert
        assert ancestors[task_1_api_name] == []
        assert ancestors[task_2_api_name] == [task_1_api_name]


class TestCompletedOrSkippedTaskOperator:

    def test_get_parents__task_without_conditions__ok(self):

        # arrange
        task_1_api_name = 'task-1'
        task_2_api_name = 'task-2'
        conditions_1 = {
            'order': 1,
            'action': ConditionAction.START_TASK,
            'rules': [
                {
                    'predicates': [
                        {
                            'field_type': PredicateType.TASK,
                            'operator': PredicateOperator.COMPLETED_OR_SKIPPED,
                            'api_name': 'predicate-1',
                            'field': task_1_api_name,
                            'value': None,
                        },
                    ],
                },
            ],
        }

        tasks_data = [
            {
                'number': 1,
                'name': 'Task 1',
                'api_name': task_1_api_name,
            },
            {
                'number': 2,
                'name': 'Task 2',
                'api_name': task_2_api_name,
                'conditions': [conditions_1],
            },
        ]

        # act
        ancestors = get_tasks_parents(tasks_data)

        # assert
        assert ancestors[task_1_api_name] == []
        assert ancestors[task_2_api_name] == [task_1_api_name]

    @pytest.mark.parametrize(
        'cond_action',
        (ConditionAction.SKIP_TASK, ConditionAction.END_WORKFLOW),
    )
    def test_get_parents__task_with_not_start_conditions__ok(
        self,
        cond_action,
    ):

        # arrange
        task_1_api_name = 'task-1'
        task_2_api_name = 'task-2'
        condition_1 = {
            'order': 1,
            'action': cond_action,
            'rules': [
                {
                    'predicates': [
                        {
                            'field_type': PredicateType.TASK,
                            'operator': PredicateOperator.COMPLETED_OR_SKIPPED,
                            'api_name': 'predicate-1',
                            'field': task_1_api_name,
                            'value': None,
                        },
                    ],
                },
            ],
        }
        tasks_data = [
            {
                'number': 1,
                'name': 'Task 1',
                'api_name': task_1_api_name,
            },
            {
                'number': 2,
                'name': 'Task 2',
                'api_name': task_2_api_name,
                'conditions': [condition_1],
            },
        ]

        # act
        ancestors = get_tasks_parents(tasks_data)

        # assert
        assert ancestors[task_1_api_name] == []
        assert ancestors[task_2_api_name] == []

    def test_get_parents__two_start_predicates__ok(self):

        # arrange
        task_1_api_name = 'task-1'
        task_2_api_name = 'task-2'
        task_3_api_name = 'task-3'
        condition_1 = {
            'order': 1,
            'action': ConditionAction.START_TASK,
            'rules': [
                {
                    'predicates': [
                        {
                            'field_type': PredicateType.TASK,
                            'operator': PredicateOperator.COMPLETED_OR_SKIPPED,
                            'field': task_2_api_name,
                            'value': None,
                        },
                        {
                            'field_type': PredicateType.TASK,
                            'operator': PredicateOperator.COMPLETED_OR_SKIPPED,
                            'field': task_3_api_name,
                            'value': None,
                        },
                    ],
                },
            ],
        }
        tasks_data = [
            {
                'number': 1,
                'name': 'Task 1',
                'api_name': task_1_api_name,
                'conditions': [condition_1],
            },
            {
                'number': 2,
                'name': 'Task 2',
                'api_name': task_2_api_name,
            },
            {
                'number': 3,
                'name': 'Task 3',
                'api_name': task_3_api_name,
            },
        ]

        # act
        ancestors = get_tasks_parents(tasks_data)

        # assert
        assert ancestors[task_1_api_name] == [task_2_api_name, task_3_api_name]
        assert ancestors[task_2_api_name] == []
        assert ancestors[task_3_api_name] == []

    def test_get_parents__linear_template__ok(self):

        # arrange
        task_1_api_name = 'task-1'
        task_2_api_name = 'task-2'
        condition_1 = {
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
                        },
                    ],
                },
            ],
        }
        condition_2 = {
            'order': 1,
            'action': ConditionAction.START_TASK,
            'rules': [
                {
                    'predicates': [
                        {
                            'field_type': PredicateType.TASK,
                            'operator': PredicateOperator.COMPLETED_OR_SKIPPED,
                            'api_name': 'predicate-1',
                            'field': task_1_api_name,
                            'value': None,
                        },
                    ],
                },
            ],
        }
        tasks_data = [
            {
                'number': 1,
                'name': 'Task 1',
                'api_name': task_1_api_name,
                'conditions': [condition_1],
            },
            {
                'number': 2,
                'name': 'Task 2',
                'api_name': task_2_api_name,
                'conditions': [condition_2],
            },
        ]

        # act
        ancestors = get_tasks_parents(tasks_data)

        # assert
        assert ancestors[task_1_api_name] == []
        assert ancestors[task_2_api_name] == [task_1_api_name]

    def test_get_parents__deleted_task_in_conditions__skip(self):

        # arrange
        task_1_api_name = 'task-1'
        task_2_api_name = 'task-2'
        deleted_task_api_name = 'task-3'
        condition_1 = {
            'order': 1,
            'action': ConditionAction.START_TASK,
            'rules': [
                {
                    'predicates': [
                        {
                            'field_type': PredicateType.TASK,
                            'operator': PredicateOperator.COMPLETED_OR_SKIPPED,
                            'api_name': 'predicate-1',
                            'field': deleted_task_api_name,
                            'value': None,
                        },
                    ],
                },
            ],
        }
        condition_2 = {
            'order': 1,
            'action': ConditionAction.START_TASK,
            'rules': [
                {
                    'predicates': [
                        {
                            'field_type': PredicateType.TASK,
                            'operator': PredicateOperator.COMPLETED_OR_SKIPPED,
                            'api_name': 'predicate-1',
                            'field': task_1_api_name,
                            'value': None,
                        },
                    ],
                },
            ],
        }
        tasks_data = [
            {
                'number': 1,
                'name': 'Task 1',
                'api_name': task_1_api_name,
                'conditions': [condition_1],
            },
            {
                'number': 2,
                'name': 'Task 2',
                'api_name': task_2_api_name,
                'conditions': [condition_2],
            },
        ]

        # act
        ancestors = get_tasks_parents(tasks_data)

        # assert
        assert ancestors[task_1_api_name] == []
        assert ancestors[task_2_api_name] == [task_1_api_name]
