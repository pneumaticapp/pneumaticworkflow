import { call } from 'redux-saga/effects';

import { routeRealtimeEvent } from '../utils/routeRealtimeEvent';
import { handleRemoveTask } from '../../tasks/saga';
import { ERealtimeEnvelopeType, IRealtimeWsEnvelope } from '../types';
import { ETaskStatus } from '../../../types/tasks';

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

describe('routeRealtimeEvent — task_deleted counter logic', () => {
  afterEach(() => {
    jest.clearAllMocks();
  });

  it('TASK_DELETED with active status passes true', () => {
    const envelope = {
      id: '1',
      dateCreatedTsp: 0,
      type: ERealtimeEnvelopeType.TASK_DELETED,
      data: {
        id: 42,
        name: 'Task',
        workflowName: 'WF',
        status: ETaskStatus.Active,
      },
    } as IRealtimeWsEnvelope;

    const gen = routeRealtimeEvent(envelope);
    const step = gen.next();

    expect(step.value).toEqual(
      call(handleRemoveTask, 42, true),
    );
  });

  it('TASK_DELETED with completed status passes false', () => {
    const envelope = {
      id: '2',
      dateCreatedTsp: 0,
      type: ERealtimeEnvelopeType.TASK_DELETED,
      data: {
        id: 43,
        name: 'Task',
        workflowName: 'WF',
        status: ETaskStatus.Completed,
      },
    } as IRealtimeWsEnvelope;

    const gen = routeRealtimeEvent(envelope);
    const step = gen.next();

    expect(step.value).toEqual(
      call(handleRemoveTask, 43, false),
    );
  });

  it('TASK_DELETED with snoozed status passes false', () => {
    const envelope = {
      id: '3',
      dateCreatedTsp: 0,
      type: ERealtimeEnvelopeType.TASK_DELETED,
      data: {
        id: 44,
        name: 'Task',
        workflowName: 'WF',
        status: ETaskStatus.Snoozed,
      },
    } as IRealtimeWsEnvelope;

    const gen = routeRealtimeEvent(envelope);
    const step = gen.next();

    expect(step.value).toEqual(
      call(handleRemoveTask, 44, false),
    );
  });

  it('TASK_COMPLETED always passes true', () => {
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

    expect(step.value).toEqual(
      call(handleRemoveTask, 45, true),
    );
  });
});
