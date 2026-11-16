import { EWorkflowStatus, TWorkflowDetailsKickoffResponse, TWorkflowDetailsResponse } from '../types/workflow';

export const makeWorkflowKickoffResponse = (
  overrides: Partial<TWorkflowDetailsKickoffResponse> = {},
): TWorkflowDetailsKickoffResponse => ({
  id: 1,
  description: '',
  output: [],
  fieldsets: [],
  ...overrides,
});

export const makeWorkflowResponse = (overrides: Partial<TWorkflowDetailsResponse> = {}): TWorkflowDetailsResponse => ({
  id: 1,
  name: 'Test Workflow',
  owners: [1],
  status: EWorkflowStatus.Running,
  isLegacyTemplate: false,
  legacyTemplateName: '',
  isExternal: false,
  isUrgent: false,
  workflowStarter: 1,
  template: null,
  tasks: [],
  finalizable: true,
  description: '',
  dueDateTsp: null,
  dateCreatedTsp: 1718400000,
  dateCompletedTsp: null,
  kickoff: makeWorkflowKickoffResponse(),
  ...overrides,
});
