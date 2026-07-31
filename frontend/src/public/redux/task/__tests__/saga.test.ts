import { setTaskCompleted, updatePerformersSaga } from '../saga';
import { ETaskActions, TSetTaskCompleted } from '../actions';
import { ETaskPerformerType, ETemplateOwnerType } from '../../../types/template';
import { addTaskAiPerformer } from '../../../api/addTaskAiPerformer';
import { removeTaskAiPerformer } from '../../../api/removeTaskAiPerformer';
import { ETaskCardViewMode } from '../../../components/TaskCard';
import { completeTask } from '../../../api/completeTask';
import { fieldsetsStorage } from '../../../components/TaskCard/utils/storageOutputs';

jest.mock('../../../api/completeTask', () => ({
  completeTask: jest.fn(),
}));

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

describe('updatePerformersSaga — AI performers', () => {
  const TASK_ID = 7;
  const AGENT_ID = 3;

  const makeAction = (type: ETaskActions.AddTaskPerformer | ETaskActions.RemoveTaskPerformer) =>
    ({
      type,
      payload: {
        taskId: TASK_ID,
        userId: {
          sourceId: AGENT_ID,
          type: ETaskPerformerType.AiAgent as unknown as ETemplateOwnerType,
        },
      },
    } as Parameters<typeof updatePerformersSaga>[0]);

  const getFetchCallEffect = (saga: Generator) => {
    saga.next(); // select(getUsers)
    saga.next([] as unknown as undefined); // optimistic list update
    const fetchGen = saga.next().value as Generator;
    return fetchGen.next().value as { payload: { fn: unknown; args: unknown[] } };
  };

  it('adding an AI agent calls the AI performer API', () => {
    const saga = updatePerformersSaga(makeAction(ETaskActions.AddTaskPerformer));

    const effect = getFetchCallEffect(saga);

    expect(effect.payload.fn).toBe(addTaskAiPerformer);
    expect(effect.payload.args).toEqual([TASK_ID, AGENT_ID]);
  });

  it('removing an AI agent calls the AI performer API', () => {
    const saga = updatePerformersSaga(makeAction(ETaskActions.RemoveTaskPerformer));

    const effect = getFetchCallEffect(saga);

    expect(effect.payload.fn).toBe(removeTaskAiPerformer);
    expect(effect.payload.args).toEqual([TASK_ID, AGENT_ID]);
  });
});
