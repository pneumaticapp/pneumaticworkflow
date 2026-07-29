import { call, select } from 'redux-saga/effects';

import { routeRealtimeEvent } from '../utils/routeRealtimeEvent';
import { handleRemoveTask } from '../../tasks/saga';
import { ERealtimeEnvelopeType, IRealtimeWsEnvelope } from '../types';
import { ETaskListCompletionStatus, ETaskStatus } from '../../../types/tasks';
import { getTasksSettings } from '../../selectors/tasks';

jest.mock('../../../utils/logger', () => ({
  logger: { info: jest.fn(), error: jest.fn() },
}));

jest.mock('../../../utils/history', () => ({
  checkSomeRouteIsActive: jest.fn(),
  history: { push: jest.fn(), replace: jest.fn() },
}));

jest.mock('../../../components/UI/Notifications', () => ({
  NotificationManager: {
    success: jest.fn(),
    warning: jest.fn(),
    notifyApiError: jest.fn(),
  },
}));

const createDeletedEnvelope = (
  id: number,
  status: ETaskStatus,
): IRealtimeWsEnvelope =>
  ({
    id: String(id),
    dateCreatedTsp: 0,
    type: ERealtimeEnvelopeType.TASK_DELETED,
    data: {
      id,
      name: 'Task',
      workflowName: 'WF',
      status,
    },
  }) as IRealtimeWsEnvelope;

describe('routeRealtimeEvent — task_deleted list updates', () => {
  afterEach(() => {
    jest.clearAllMocks();
  });

  it('TASK_DELETED with active status removes and decrements', () => {
    const gen = routeRealtimeEvent(createDeletedEnvelope(42, ETaskStatus.Active));

    expect(gen.next().value).toEqual(select(getTasksSettings));
    expect(gen.next({ completionStatus: ETaskListCompletionStatus.Active } as never).value).toEqual(
      call(handleRemoveTask, 42, true),
    );
    expect(gen.next().done).toBe(true);
  });

  it('TASK_DELETED with completed status removes on Completed tab without decrement', () => {
    const gen = routeRealtimeEvent(createDeletedEnvelope(43, ETaskStatus.Completed));

    expect(gen.next().value).toEqual(select(getTasksSettings));
    expect(
      gen.next({ completionStatus: ETaskListCompletionStatus.Completed } as never).value,
    ).toEqual(call(handleRemoveTask, 43, false));
    expect(gen.next().done).toBe(true);
  });

  it('TASK_DELETED with completed status skips Active tab (return/revert race)', () => {
    const gen = routeRealtimeEvent(createDeletedEnvelope(43, ETaskStatus.Completed));

    expect(gen.next().value).toEqual(select(getTasksSettings));
    expect(
      gen.next({ completionStatus: ETaskListCompletionStatus.Active } as never).done,
    ).toBe(true);
  });

  it('TASK_DELETED with snoozed status removes on Completed tab without decrement', () => {
    const gen = routeRealtimeEvent(createDeletedEnvelope(44, ETaskStatus.Snoozed));

    expect(gen.next().value).toEqual(select(getTasksSettings));
    expect(
      gen.next({ completionStatus: ETaskListCompletionStatus.Completed } as never).value,
    ).toEqual(call(handleRemoveTask, 44, false));
    expect(gen.next().done).toBe(true);
  });

  it('TASK_DELETED with snoozed status skips Active tab', () => {
    const gen = routeRealtimeEvent(createDeletedEnvelope(44, ETaskStatus.Snoozed));

    expect(gen.next().value).toEqual(select(getTasksSettings));
    expect(
      gen.next({ completionStatus: ETaskListCompletionStatus.Active } as never).done,
    ).toBe(true);
  });

  it('TASK_COMPLETED always removes and decrements', () => {
    const envelope = {
      id: '4',
      dateCreatedTsp: 0,
      type: ERealtimeEnvelopeType.TASK_COMPLETED,
      data: {
        id: 45,
        name: 'Task',
        workflowName: 'WF',
        dateCompletedTsp: 123,
        performers: [],
      },
    } as IRealtimeWsEnvelope;

    const gen = routeRealtimeEvent(envelope);
    const step = gen.next();

    expect(step.value).toEqual(call(handleRemoveTask, 45, true));
  });
});
