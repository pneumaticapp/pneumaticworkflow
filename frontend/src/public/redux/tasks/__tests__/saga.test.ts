import { put } from 'redux-saga/effects';

import { ITaskListItem } from '../../../types/tasks';
import { handleAddTask, handleRemoveTask } from '../saga';
import { loadTasksCount } from '../slice';

describe('task websocket counter updates', () => {
  it('reloads the count when a task is added', () => {
    const generator = handleAddTask({} as ITaskListItem);

    expect(generator.next().value).toEqual(put(loadTasksCount()));
  });

  it('reloads the count when a task is removed', () => {
    const generator = handleRemoveTask(1);

    expect(generator.next().value).toEqual(put(loadTasksCount()));
  });
});
