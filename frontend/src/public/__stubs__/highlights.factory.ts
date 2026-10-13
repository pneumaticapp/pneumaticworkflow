import { IHighlightsItem } from '../types/highlights';
import { EWorkflowLogEvent, EWorkflowStatus } from '../types/workflow';

export const makeHighlightsItem = (
  type: EWorkflowLogEvent = EWorkflowLogEvent.WorkflowRun,
  overrides: Partial<IHighlightsItem> = {},
): IHighlightsItem => ({
  id: 1,
  type,
  task: {
    id: 10,
    name: 'Test Task',
    number: 1,
    process: 100,
    delay: null,
    output: [],
    fieldsets: [],
    dueDate: null,
  },
  text: '',
  attachments: [],
  created: '2024-01-01T00:00:00Z',
  user: { id: 1 },
  workflow: {
    id: 100,
    name: 'Test Workflow',
    currentTask: 1,
    tasksCount: 3,
    template: { id: 1, name: 'Template', count: 0 },
    isLegacyTemplate: false,
    legacyTemplateName: '',
    status: EWorkflowStatus.Running,
    kickoff: null,
    isExternal: false,
  },
  userId: 1,
  targetUserId: null,
  targetGroupId: null,
  delay: null,
  ...overrides,
});
