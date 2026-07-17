import { select, put } from 'redux-saga/effects';

import { handleRemoveTask } from '../saga';
import { changeTasksCount } from '../slice';
import { getTotalTasksCount } from '../../selectors/tasks';
import { getCurrentTask } from '../../selectors/task';
import { checkSomeRouteIsActive } from '../../../utils/history';

jest.mock('../../../utils/history', () => ({
  checkSomeRouteIsActive: jest.fn(),
  history: { push: jest.fn(), replace: jest.fn() },
}));

jest.mock('../../../utils/logger', () => ({
  logger: { info: jest.fn(), error: jest.fn() },
}));

jest.mock('../../../components/UI/Notifications', () => ({
  NotificationManager: {
    success: jest.fn(),
    warning: jest.fn(),
    notifyApiError: jest.fn(),
  },
}));

const mockCheckRoute = checkSomeRouteIsActive as jest.Mock;

describe('handleRemoveTask', () => {
  afterEach(() => {
    jest.clearAllMocks();
  });

  it('decrements counter when shouldDecrementCounter=true', () => {
    const gen = handleRemoveTask(42, true);

    expect(gen.next().value).toEqual(
      select(getTotalTasksCount),
    );
    expect(gen.next(5 as any).value).toEqual(
      put(changeTasksCount(4)),
    );

    mockCheckRoute.mockReturnValue(false);
    expect(gen.next().done).toBe(true);
  });

  it('does not decrement when totalTasksCount is null', () => {
    const gen = handleRemoveTask(42, true);

    expect(gen.next().value).toEqual(
      select(getTotalTasksCount),
    );

    mockCheckRoute.mockReturnValue(false);
    expect(gen.next(null as any).done).toBe(true);
  });

  it('skips counter when shouldDecrementCounter=false', () => {
    const gen = handleRemoveTask(42, false);

    mockCheckRoute.mockReturnValue(false);
    expect(gen.next().done).toBe(true);
  });

  it('defaults shouldDecrementCounter to true', () => {
    const gen = handleRemoveTask(42);

    expect(gen.next().value).toEqual(
      select(getTotalTasksCount),
    );
    expect(gen.next(10 as any).value).toEqual(
      put(changeTasksCount(9)),
    );

    mockCheckRoute.mockReturnValue(false);
    expect(gen.next().done).toBe(true);
  });

  it('selects currentTask and removes from list on tasks route', () => {
    const gen = handleRemoveTask(42, false);

    mockCheckRoute.mockReturnValue(true);

    expect(gen.next().value).toEqual(
      select(getCurrentTask),
    );

    const step = gen.next({ id: 99 } as any);
    expect(step.done).toBe(false);

    expect(gen.next().done).toBe(true);
  });
});
