from src.processes.utils.common import (
    get_tasks_ancestors,
)


def test_get_tasks_ancestors__ok():

    # arrange
    tasks_parents = {
        'task_0': [],
        'task_1': ['task_0'],
        'task_2': ['task_1'],
        'task_3': ['task_2', 'task_1'],
        'task_4': ['task_3'],
    }

    # act
    result = get_tasks_ancestors(tasks_parents)

    # assert
    assert result == {
        'task_0': set(),
        'task_1': {'task_0'},
        'task_2': {'task_1', 'task_0'},
        'task_3': {'task_2', 'task_1', 'task_0'},
        'task_4': {'task_3', 'task_2', 'task_1', 'task_0'},
    }
