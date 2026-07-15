import { put } from 'redux-saga/effects';

import { revertTask } from '../../../api/revertTask';
import { NotificationManager } from '../../../components/UI/Notifications';
import { ETaskCardViewMode } from '../../../components/TaskCard';
import { removeOutputFromLocalStorage } from '../../../components/TaskCard/utils/storageOutputs';
import {
  ETaskStatus,
  setCurrentTaskStatus,
  setTaskReverted as createSetTaskRevertedAction,
} from '../actions';
import { setTaskReverted } from '../saga';
import { getAuthUser } from '../../selectors/user';

jest.mock('../../../api/revertTask');
jest.mock('../../../components/TaskCard/utils/storageOutputs');
jest.mock('../../../components/UI/Notifications', () => ({
  NotificationManager: {
    success: jest.fn(),
    warning: jest.fn(),
  },
}));

describe('task saga', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('clears stored output when reverting a task fails', () => {
    const taskId = 42;
    const error = new Error('Revert failed');
    const action = createSetTaskRevertedAction({
      taskId,
      viewMode: ETaskCardViewMode.Single,
      comment: '',
    });
    const generator = setTaskReverted(action);

    generator.next();
    generator.next({ authUser: { id: 1 } } as ReturnType<typeof getAuthUser>);
    generator.next();
    const finallyEffect = generator.throw(error).value;

    expect(revertTask).toHaveBeenCalledWith({ id: taskId, comment: '' });
    expect(NotificationManager.warning).toHaveBeenCalledWith({
      title: 'tasks.task-fail-revert',
      message: error.message,
    });
    expect(removeOutputFromLocalStorage).toHaveBeenCalledWith(taskId);
    expect(finallyEffect).toEqual(put(setCurrentTaskStatus(ETaskStatus.WaitingForAction)));
  });
});
