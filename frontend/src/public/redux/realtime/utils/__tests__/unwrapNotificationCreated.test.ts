import { ERealtimeEnvelopeType } from '../../types';
import { unwrapNotificationCreatedEnvelope } from '../unwrapNotificationCreated';

describe('unwrapNotificationCreatedEnvelope', () => {
  it('unwraps notification_created into mappable notification envelope', () => {
    const result = unwrapNotificationCreatedEnvelope({
      id: 'ws-2',
      dateCreatedTsp: 1_700_000_000,
      type: ERealtimeEnvelopeType.NOTIFICATION_CREATED,
      data: {
        id: 99,
        author: 12,
        type: 'comment',
        datetimeTsp: 1_700_000_000,
        status: 'new',
        text: 'Mention in task',
        task: { id: 3, name: 'Task' },
        workflow: { id: 8, name: 'Workflow' },
      },
    });

    expect(result).toEqual({
      type: 'comment',
      data: {
        id: 99,
        author: 12,
        type: 'comment',
        datetimeTsp: 1_700_000_000,
        status: 'new',
        text: 'Mention in task',
        task: { id: 3, name: 'Task' },
        workflow: { id: 8, name: 'Workflow' },
      },
    });
  });

  it('returns null for unknown nested notification type', () => {
    const result = unwrapNotificationCreatedEnvelope({
      id: 'ws-3',
      dateCreatedTsp: 1_700_000_000,
      type: ERealtimeEnvelopeType.NOTIFICATION_CREATED,
      data: {
        id: 1,
        author: 1,
        type: 'unknown_type' as 'comment',
        datetimeTsp: 1_700_000_000,
        status: 'new',
        text: '',
        task: { id: 1, name: 'Task' },
        workflow: { id: 1, name: 'Workflow' },
      },
    });

    expect(result).toBeNull();
  });
});
