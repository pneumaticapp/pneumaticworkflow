import { setTaskCompleted, setTaskReverted } from '../saga';
import {
  ETaskActions,
  TSetTaskCompleted,
  setTaskReverted as createSetTaskRevertedAction,
} from '../actions';
import { ETaskCardViewMode } from '../../../components/TaskCard';
import { completeTask } from '../../../api/completeTask';
import { revertTask } from '../../../api/revertTask';
import { fieldsetsStorage, outputStorage } from '../../../components/TaskCard/utils/storageOutputs';

jest.mock('../../../api/completeTask', () => ({
  completeTask: jest.fn(),
}));

jest.mock('../../../api/revertTask');

jest.mock('../../../components/TaskCard/utils/storageOutputs', () => ({
  outputStorage: { remove: jest.fn() },
  fieldsetsStorage: { remove: jest.fn() },
}));

jest.mock('../../../utils/mappers', () => ({
  mapOutputToCompleteTask: jest.fn((x) => x),
  getNormalizeOutputUsersToEmails: jest.fn((x) => x),
}));

jest.mock('../../../utils/logger', () => ({
  logger: { info: jest.fn(), error: jest.fn() },
}));

jest.mock('../../../components/UI/Notifications', () => ({
  NotificationManager: { success: jest.fn(), warning: jest.fn(), notifyApiError: jest.fn() },
}));

jest.mock('../../../utils/getErrorMessage', () => ({
  getErrorMessage: jest.fn(() => 'error'),
}));

jest.mock('../../../components/TaskCard', () => ({
  ETaskCardViewMode: {
    Single: 'single',
    List: 'list',
    Guest: 'guest',
  },
}));

jest.mock('../../../utils/history', () => ({
  history: { push: jest.fn(), replace: jest.fn() },
}));

describe('setTaskReverted — output draft cleanup', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('keeps field and fieldset drafts when reverting a task fails', () => {
    const taskId = 42;
    const generator = setTaskReverted(createSetTaskRevertedAction({
      taskId,
      viewMode: ETaskCardViewMode.Single,
      comment: '',
    }));

    generator.next();
    generator.next({ authUser: { id: 1 } } as any);
    generator.next();
    generator.throw(new Error('Revert failed'));

    expect(revertTask).toHaveBeenCalledWith({ id: taskId, comment: '' });
    expect(outputStorage.remove).not.toHaveBeenCalled();
    expect(fieldsetsStorage.remove).not.toHaveBeenCalled();
  });

  it('clears field and fieldset drafts after reverting succeeds', () => {
    const taskId = 42;
    const generator = setTaskReverted(createSetTaskRevertedAction({
      taskId,
      viewMode: ETaskCardViewMode.Single,
      comment: '',
    }));

    generator.next();
    generator.next({ authUser: { id: 1 } } as any);
    generator.next();
    generator.next();

    expect(outputStorage.remove).toHaveBeenCalledWith(taskId);
    expect(fieldsetsStorage.remove).toHaveBeenCalledWith(taskId);
  });
});

describe('setTaskCompleted — fieldsets draft cleanup', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  const TASK_ID = 42;

  const makeAction = (): TSetTaskCompleted => ({
    type: ETaskActions.SetTaskCompleted,
    payload: {
      taskId: TASK_ID,
      output: [],
      viewMode: ETaskCardViewMode.Single,
    },
  });

  const step = (gen: Generator, value?: unknown) => (gen.next as (v?: unknown) => IteratorResult<unknown>)(value);

  const stepThrow = (gen: Generator, error: Error) => (gen.throw as (e: Error) => IteratorResult<unknown>)(error);

  const advanceToCompleteTask = (action: TSetTaskCompleted) => {
    (completeTask as jest.Mock).mockReturnValue(Promise.resolve());

    const saga = setTaskCompleted(action);

    step(saga);
    step(saga, { authUser: { id: 1 } });

    step(saga);
    step(saga, { id: TASK_ID, areChecklistsHandling: false });

    step(saga, []);

    return saga;
  };

  it('clears fieldsets draft on successful complete', () => {
    const saga = advanceToCompleteTask(makeAction());

    step(saga);

    expect(fieldsetsStorage.remove).toHaveBeenCalledTimes(1);
    expect(fieldsetsStorage.remove).toHaveBeenCalledWith(TASK_ID);
  });

  it('does not clear fieldsets draft on complete error', () => {
    const saga = advanceToCompleteTask(makeAction());

    stepThrow(saga, new Error('API error'));

    expect(fieldsetsStorage.remove).not.toHaveBeenCalled();
  });
});
