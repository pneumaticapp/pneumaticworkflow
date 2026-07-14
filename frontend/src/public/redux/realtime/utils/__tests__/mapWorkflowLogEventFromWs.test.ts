import { EWorkflowLogEvent, IWorkflowLogItem } from '../../../../types/workflow';
import { ERealtimeEnvelopeType } from '../../types';
import { mapWsEnvelopeToWorkflowLogItem } from '../mapWorkflowLogEventFromWs';

describe('mapWsEnvelopeToWorkflowLogItem', () => {
  it('returns event_created payload as IWorkflowLogItem', () => {
    const data: IWorkflowLogItem = {
      id: 10,
      created: '2024-01-01T00:00:00Z',
      type: EWorkflowLogEvent.TaskComment,
      workflowId: 5,
      userId: 42,
      targetUserId: null,
      targetGroupId: null,
      status: 'created',
      text: 'Hello',
      task: {
        id: 7,
        name: 'Review',
        number: 1,
        description: '',
        output: [],
        performers: [],
        dueDate: '2024-01-02T00:00:00Z',
        delay: null,
      },
      delay: null,
      watched: [],
      reactions: {},
    };

    const result = mapWsEnvelopeToWorkflowLogItem({
      id: 'ws-1',
      dateCreatedTsp: 1_700_000_000,
      type: ERealtimeEnvelopeType.EVENT_CREATED,
      data,
    });

    expect(result).toBe(data);
    expect(result?.userId).toBe(42);
    expect(result?.text).toBe('Hello');
    expect(result?.type).toBe(EWorkflowLogEvent.TaskComment);
  });

  it('returns event_created without task payload', () => {
    const data: IWorkflowLogItem = {
      id: 11,
      created: '2024-01-01T00:00:00Z',
      type: EWorkflowLogEvent.WorkflowComplete,
      workflowId: 5,
      userId: 42,
      targetUserId: null,
      targetGroupId: null,
      status: 'created',
      text: null,
      task: null,
      delay: null,
      watched: [],
      reactions: {},
    };

    const result = mapWsEnvelopeToWorkflowLogItem({
      id: 'ws-2',
      dateCreatedTsp: 1_700_000_000,
      type: ERealtimeEnvelopeType.EVENT_CREATED,
      data,
    });

    expect(result).toBe(data);
    expect(result?.task).toBeNull();
    expect(result?.type).toBe(EWorkflowLogEvent.WorkflowComplete);
  });

  it('returns event_updated payload as IWorkflowLogItem', () => {
    const data: IWorkflowLogItem = {
      id: 12,
      created: '2024-01-01T00:00:00Z',
      type: EWorkflowLogEvent.TaskComment,
      workflowId: 5,
      userId: 42,
      targetUserId: null,
      targetGroupId: null,
      status: 'updated',
      text: 'Updated',
      task: null,
      delay: null,
      watched: [{ date: '2024-01-01T01:00:00Z', userId: 3 }],
      reactions: { '👍': [3] },
    };

    const result = mapWsEnvelopeToWorkflowLogItem({
      id: 'ws-3',
      dateCreatedTsp: 1_700_000_000,
      type: ERealtimeEnvelopeType.EVENT_UPDATED,
      data,
    });

    expect(result).toBe(data);
    expect(result?.status).toBe('updated');
  });
});
