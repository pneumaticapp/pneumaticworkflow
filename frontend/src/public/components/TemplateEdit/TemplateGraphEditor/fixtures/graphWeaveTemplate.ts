import {
  EExtraFieldType,
  ETaskPerformerType,
  IExtraField,
  ITemplateClient,
  ITemplateTaskClient,
  ITemplateTaskPerformer,
} from '../../../../types/template';
import { createEmptyTaskDueDate } from '../../../../utils/dueDate/createEmptyTaskDueDate';
import {
  EConditionAction,
  EConditionLogicOperations,
  EConditionOperators,
  ICondition,
} from '../../TaskForm/Conditions';

const EMPTY_TEMPLATE_BASE: ITemplateClient = {
  name: 'Graph weave showcase',
  description: 'Cross-column Check If lines that meet and cross',
  isActive: false,
  finalizable: false,
  completionNotification: false,
  reminderNotification: false,
  dateUpdated: null,
  updatedBy: null,
  owners: [],
  kickoff: { description: '', fields: [], fieldsets: [] },
  tasks: [],
  isPublic: false,
  publicUrl: null,
  publicSuccessUrl: null,
  isEmbedded: false,
  embedUrl: null,
  wfNameTemplate: null,
  tasksCount: 0,
  performersCount: 0,
};

function createField(apiName: string, name: string): IExtraField {
  return {
    apiName,
    name,
    type: EExtraFieldType.String,
    order: 0,
    userId: null,
    groupId: null,
  };
}

function createPerformer(prefix: string): ITemplateTaskPerformer {
  return {
    label: 'Alex',
    type: ETaskPerformerType.User,
    sourceId: '1',
    apiName: `${prefix}-performer`,
  };
}

function createSkipFromField(apiName: string, field: string): ICondition {
  return {
    apiName,
    order: 1,
    action: EConditionAction.SkipTask,
    rules: [
      {
        ruleApiName: `${apiName}-rule`,
        predicateApiName: `${apiName}-predicate`,
        field,
        operator: EConditionOperators.Exist,
        logicOperation: EConditionLogicOperations.And,
      },
    ],
  };
}

function createTask(
  overrides: Partial<ITemplateTaskClient> & Pick<ITemplateTaskClient, 'apiName' | 'name' | 'number'>,
): ITemplateTaskClient {
  return {
    description: '',
    requireCompletionByAll: false,
    skipForStarter: false,
    fields: [],
    fieldsets: [],
    rawPerformers: [createPerformer(overrides.apiName)],
    delay: null,
    rawDueDate: createEmptyTaskDueDate(),
    conditions: [],
    uuid: `${overrides.apiName}-uuid`,
    checklists: [],
    revertTask: null,
    ancestors: [],
    ...overrides,
  };
}

/**
 * Two columns with Check If that meet on one card and cross the stem:
 * 1 → 2 → 3 (stem) and 1 → 7 → 8 → 5 (left branch).
 * Task 5 collects SkipTask from 7, 8 and 2; Task 3 from 7; Task 8 from 2.
 */
export function getGraphWeaveTemplate(base: ITemplateClient = EMPTY_TEMPLATE_BASE): ITemplateClient {
  const tasks: ITemplateTaskClient[] = [
    createTask({
      apiName: 'task-1',
      name: 'New Step',
      number: 1,
    }),
    createTask({
      apiName: 'task-2',
      name: 'New Step 2',
      number: 2,
      ancestors: ['task-1'],
      fields: [createField('flag-2', 'Flag 2')],
    }),
    createTask({
      apiName: 'task-3',
      name: 'New Step 3',
      number: 3,
      ancestors: ['task-2'],
      conditions: [createSkipFromField('skip-3-from-7', 'flag-7')],
    }),
    createTask({
      apiName: 'task-7',
      name: 'New Step 7',
      number: 7,
      ancestors: ['task-1'],
      fields: [createField('flag-7', 'Flag 7')],
    }),
    createTask({
      apiName: 'task-8',
      name: 'New Step 8',
      number: 8,
      ancestors: ['task-7'],
      fields: [createField('flag-8', 'Flag 8')],
      conditions: [createSkipFromField('skip-8-from-2', 'flag-2')],
    }),
    createTask({
      apiName: 'task-5',
      name: 'New Step 5',
      number: 5,
      ancestors: ['task-8'],
      conditions: [
        createSkipFromField('skip-5-from-7', 'flag-7'),
        { ...createSkipFromField('skip-5-from-8', 'flag-8'), order: 2 },
        { ...createSkipFromField('skip-5-from-2', 'flag-2'), order: 3 },
      ],
    }),
  ];

  return {
    ...base,
    name: 'Graph weave showcase',
    description: 'Cross-column Check If lines that meet and cross',
    kickoff: {
      description: '',
      fields: [],
      fieldsets: [],
    },
    tasks,
    tasksCount: tasks.length,
    performersCount: tasks.filter((task) => task.rawPerformers.length > 0).length,
  };
}

export const GRAPH_WEAVE_TEMPLATE = getGraphWeaveTemplate();
