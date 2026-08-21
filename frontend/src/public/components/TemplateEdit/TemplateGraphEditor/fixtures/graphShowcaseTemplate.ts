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

const KICKOFF_FIELD_API_NAME = 'kickoff-client';

const EMPTY_TEMPLATE_BASE: ITemplateClient = {
  name: 'Graph edges showcase',
  description: 'All graph edge and node variants for visual QA',
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

function createFields(prefix: string, count: number): IExtraField[] {
  return Array.from({ length: count }, (_, index) => ({
    apiName: `${prefix}-field-${index + 1}`,
    name: `Field ${index + 1}`,
    type: EExtraFieldType.String,
    order: index,
    userId: null,
    groupId: null,
  }));
}

function createPerformer(prefix: string, label: string): ITemplateTaskPerformer {
  return {
    label,
    type: ETaskPerformerType.User,
    sourceId: '1',
    apiName: `${prefix}-performer`,
  };
}

function createFieldCondition(apiName: string, action: EConditionAction, field: string): ICondition {
  return {
    apiName,
    order: 1,
    action,
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
    rawPerformers: [],
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

export function getGraphShowcaseTemplate(base: ITemplateClient = EMPTY_TEMPLATE_BASE): ITemplateClient {
  const tasks: ITemplateTaskClient[] = [
    createTask({
      apiName: 'task-linear',
      name: 'Prepare Layout',
      number: 1,
      rawPerformers: [createPerformer('task-linear', 'Alex')],
      fields: createFields('task-linear', 6),
      conditions: [createFieldCondition('task-linear-start', EConditionAction.StartTask, KICKOFF_FIELD_API_NAME)],
    }),
    createTask({
      apiName: 'task-skippable',
      name: 'Review Copy',
      number: 2,
      rawPerformers: [createPerformer('task-skippable', 'Alex')],
      fields: createFields('task-skippable', 6),
      conditions: [
        createFieldCondition('task-skippable-start', EConditionAction.StartTask, KICKOFF_FIELD_API_NAME),
        createFieldCondition('task-skippable-skip', EConditionAction.SkipTask, KICKOFF_FIELD_API_NAME),
      ],
    }),
    createTask({
      apiName: 'task-url-title',
      name: 'https://www.figma.com/design/template-2',
      number: 3,
      rawPerformers: [createPerformer('task-url-title', 'Alex')],
      fields: createFields('task-url-title', 1),
    }),
    createTask({
      apiName: 'task-parallel-a',
      name: 'Design Left Branch',
      number: 4,
      ancestors: ['task-url-title'],
      rawPerformers: [createPerformer('task-parallel-a', 'Alex')],
      fields: createFields('task-parallel-a', 2),
    }),
    createTask({
      apiName: 'task-parallel-b',
      name: 'Design Right Branch',
      number: 5,
      ancestors: ['task-url-title'],
      rawPerformers: [createPerformer('task-parallel-b', 'Alex')],
    }),
    createTask({
      apiName: 'task-join',
      name: 'Merge Branches',
      number: 6,
      ancestors: ['task-parallel-a', 'task-parallel-b'],
      rawPerformers: [createPerformer('task-join', 'Alex')],
      fields: createFields('task-join', 1),
      conditions: [createFieldCondition('task-join-start', EConditionAction.StartTask, KICKOFF_FIELD_API_NAME)],
    }),
    createTask({
      apiName: 'task-long-title',
      name: 'Prepare Layout For Development And Review With Stakeholders',
      number: 7,
    }),
  ];

  return {
    ...base,
    name: 'Graph edges showcase',
    description: 'All graph edge and node variants for visual QA',
    kickoff: {
      description: '<p>Collect the brief before the first task starts.</p>',
      fields: [
        {
          apiName: KICKOFF_FIELD_API_NAME,
          name: 'Client',
          type: EExtraFieldType.String,
          order: 0,
          userId: null,
          groupId: null,
        },
      ],
      fieldsets: [],
    },
    tasks,
    tasksCount: tasks.length,
    performersCount: tasks.filter((task) => task.rawPerformers.length > 0).length,
  };
}

export const GRAPH_SHOWCASE_TEMPLATE = getGraphShowcaseTemplate();
