import { EWorkflowLogEvent, IWorkflowLogItem } from '../types/workflow';

let nextEventId = 1;

export const resetLogEventId = () => {
  nextEventId = 1;
};

export const makeLogEvent = (
  type: EWorkflowLogEvent,
  overrides: Partial<IWorkflowLogItem> = {},
): IWorkflowLogItem => {
  const id = nextEventId;
  nextEventId += 1;

  return {
    id,
    workflowId: 100,
    created: '2024-01-01T00:00:00Z',
    status: '',
    task: {
      id: 1,
      name: 'Test Task',
      description: '',
      output: [],
      performers: [],
      dueDate: null,
      number: 1,
      delay: null,
    },
    text: null,
    type,
    userId: null,
    delay: null,
    targetUserId: null,
    targetGroupId: null,
    attachments: [],
    watched: [],
    reactions: {},
    ...overrides,
  };
};
