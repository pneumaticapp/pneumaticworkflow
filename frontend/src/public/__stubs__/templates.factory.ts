import { IKickoffClient, ITemplateResponse, ITemplateTask, ITemplateTaskClient } from '../types/template';
import { createEmptyTaskDueDate } from '../utils/dueDate/createEmptyTaskDueDate';

export const makeTemplateTaskClient = (overrides: Partial<ITemplateTaskClient> = {}): ITemplateTaskClient => ({
  id: 1,
  apiName: 'task-1',
  name: 'Task',
  description: '',
  number: 1,
  rawPerformers: [],
  requireCompletionByAll: false,
  skipForStarter: false,
  fields: [],
  fieldsets: [],
  delay: null,
  rawDueDate: createEmptyTaskDueDate(),
  conditions: [],
  uuid: 'task-uuid',
  checklists: [],
  revertTask: null,
  ancestors: [],
  ...overrides,
});

export const makeTemplateTask = (overrides: Partial<ITemplateTask> = {}): ITemplateTask => ({
  apiName: 'task-1',
  number: 1,
  name: 'Task',
  description: '',
  delay: null,
  rawDueDate: createEmptyTaskDueDate(),
  requireCompletionByAll: false,
  skipForStarter: false,
  rawPerformers: [],
  fields: [],
  fieldsets: [],
  uuid: 'task-uuid',
  conditions: [],
  checklists: [],
  revertTask: null,
  ancestors: [],
  ...overrides,
});

export const makeKickoffClient = (overrides: Partial<IKickoffClient> = {}): IKickoffClient => ({
  description: '',
  fields: [],
  fieldsets: [],
  ...overrides,
});

export const makeTemplateResponse = (overrides: Partial<ITemplateResponse> = {}): ITemplateResponse => ({
  id: 1,
  name: 'Template',
  description: '',
  isActive: true,
  finalizable: false,
  completionNotification: false,
  reminderNotification: false,
  dateUpdated: null,
  updatedBy: null,
  owners: [],
  isPublic: false,
  publicUrl: null,
  publicSuccessUrl: null,
  isEmbedded: false,
  embedUrl: null,
  wfNameTemplate: null,
  tasks: [],
  kickoff: {
    description: '',
    fields: [],
    fieldsets: [],
  },
  ...overrides,
});
