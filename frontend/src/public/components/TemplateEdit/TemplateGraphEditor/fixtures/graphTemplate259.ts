import { EExtraFieldType, IExtraField, ITemplateClient, ITemplateTaskClient } from '../../../../types/template';
import { createEmptyTaskDueDate } from '../../../../utils/dueDate/createEmptyTaskDueDate';
import {
  EConditionAction,
  EConditionLogicOperations,
  EConditionOperators,
  ICondition,
  TConditionRule,
} from '../../TaskForm/Conditions';
import { EStartingType } from '../../TaskForm/Conditions/utils/getDropdownOperators';

const COST_CENTER_FIELD = 'field-270bb2';
const AMOUNT_FIELD = 'field-093a2e';

const BRANCH_NAMES = [
  ['VP Approval MI Customer Support', 'President Approval MI Customer Support'],
  ['Director Approval Piano', 'VP Approval Piano', 'President Approval Piano'],
  [
    'Manager Approval Piano - Service',
    'Director and VP Approval Piano - Service',
    'President Approval Piano - Service',
  ],
  ['Director Approval WSP', 'VP Approval WSP', 'President Approval WSP'],
  ['Manager Approval CMP', 'Director Approval CMP', 'VP Approval CMP', 'President Approval CMP'],
  ['Manager Approval CX/DX', 'VP Approval CX/DX', 'President Approval CX/DX'],
  ['VP Approval AV Support', 'President Approval AV Support'],
  ['Manager Approval Technical Services', 'VP Approval Technical Services', 'President Approval Technical Services'],
  ['Manager Approval Service DC', 'VP Approval Service DC', 'President Approval Service DC'],
  ['Manager Approval Music School', 'VP Approval Music School', 'President Approval Music School'],
  [
    'Manager Approval National Education',
    'Manager 2 Approval National Education',
    'VP Approval National Education',
    'President Approval National Education',
  ],
  ['Manager Approval AV Mass Channel', 'VP Approval AV Mass Channel', 'President Approval AV Mass Channel'],
  ['Director Approval AV- Speciality', 'VP Approval AV- Speciality', 'President Approval AV- Speciality'],
  [
    'Manager Approval Building - Toronto DC',
    'Manager and VP Approval Building - Toronto DC',
    'President Approval Building - Toronto DC',
  ],
  [
    'Assistant Manager Approval Building - Vancouver DC',
    'Manager and Manager Approval Building - Vancouver DC',
    'Vice President Approval Building - Vancouver DC',
    'President Approval Building - Vancouver DC',
  ],
  ['VP Approval Others - Tak'],
  ['President Approval Others - Alberto Liason'],
  ['Director Approval CMP - CA', 'VP Approval CMP - CA', 'President Approval CMP - CA'],
] as const;

const TASK_API_NAMES = [
  'task-5f78eb',
  'task-23d8a7',
  'task-d22acd',
  'task-41abb4',
  'task-8ed8b8',
  'task-f5094b',
  'task-bbc83a',
  'task-467818',
  'task-5e090e',
  'task-a33811',
  'task-d13a72',
  'task-d55893',
  'task-e66a9a',
  'task-b49977',
  'task-3aebb6',
  'task-f5e94f',
  'task-428b4d',
  'task-87c802',
  'task-0378d6',
  'task-26d96c',
  'task-73193b',
  'task-03d955',
  'task-05396e',
  'task-2849a9',
  'task-72497c',
  'task-b8bb80',
  'task-c5ba54',
  'task-ef5a91',
  'task-eafaf4',
  'task-812adc',
  'task-d9c959',
  'task-26c8a7',
  'task-c0cb1e',
  'task-c7794c',
  'task-013a46',
  'task-933a92',
  'task-4508ce',
  'task-9a581e',
  'task-55eb38',
  'task-14ea3b',
  'task-dc6937',
  'task-c3bacd',
  'task-71fb64',
  'task-096802',
  'task-5c7920',
  'task-9ccb56',
  'task-c9f9f3',
  'task-247842',
  'task-ba6995',
  'task-66788f',
  'task-cmpca-dir',
  'task-cmpca-vp',
  'task-cmpca-pres',
  'task-c2daa4',
] as const;

const TEMPLATE_BASE: ITemplateClient = {
  id: 259,
  name: 'ZZMIG26 B repaired copy',
  description: '',
  isActive: true,
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
  wfNameTemplate: '{{template-name}}-CN {{workflow-id}} –{{date}}',
  tasksCount: 0,
  performersCount: 0,
};

function taskApiName(number: number): string {
  const apiName = TASK_API_NAMES[number - 1];

  if (!apiName) {
    throw new Error(`Missing template 259 task API name for task ${number}`);
  }

  return apiName;
}

function createField(apiName: string, name: string, type: EExtraFieldType): IExtraField {
  return { apiName, name, type, order: 0, userId: null, groupId: null };
}

function createRule(apiName: string, field: string, fieldType: EExtraFieldType | EStartingType): TConditionRule {
  return {
    ruleApiName: `${apiName}-rule`,
    predicateApiName: `${apiName}-predicate`,
    field,
    fieldType,
    operator: EConditionOperators.Exist,
    logicOperation: EConditionLogicOperations.And,
  };
}

function createSkipCondition(apiName: string, predecessors: string[]): ICondition {
  const rules: TConditionRule[] = [createRule(`${apiName}-cost`, COST_CENTER_FIELD, EExtraFieldType.String)];

  predecessors.forEach((predecessor, index) => {
    rules.push(
      createRule(`${apiName}-amount-${index}`, AMOUNT_FIELD, EExtraFieldType.Number),
      createRule(`${apiName}-task-${index}`, predecessor, EStartingType.Task),
    );
  });

  return {
    apiName,
    order: 2,
    action: EConditionAction.SkipTask,
    rules,
  };
}

function createTask(
  apiName: string,
  name: string,
  number: number,
  ancestors: string[],
  conditionPredecessors: string[] = [],
): ITemplateTaskClient {
  return {
    apiName,
    name,
    number,
    description: '',
    requireCompletionByAll: false,
    skipForStarter: number > 2,
    fields: [],
    fieldsets: [],
    rawPerformers: [],
    delay: null,
    rawDueDate: createEmptyTaskDueDate(),
    conditions: number > 2 ? [createSkipCondition(`${apiName}-skip`, conditionPredecessors)] : [],
    uuid: `${apiName}-uuid`,
    checklists: [],
    revertTask: null,
    ancestors,
  };
}

function createBranch(names: readonly string[], startNumber: number): ITemplateTaskClient[] {
  return names.map((name, index) => {
    const apiName = taskApiName(startNumber + index);
    const branchAncestors = Array.from({ length: index }, (_, ancestorIndex) =>
      taskApiName(startNumber + ancestorIndex),
    );

    return createTask(
      apiName,
      name,
      startNumber + index,
      [...branchAncestors, taskApiName(2), taskApiName(1)],
      branchAncestors,
    );
  });
}

export function getGraphTemplate259(base: ITemplateClient = TEMPLATE_BASE): ITemplateClient {
  const initiate = createTask(taskApiName(1), 'Initiate Process', 1, []);
  initiate.fields = [
    createField(COST_CENTER_FIELD, 'Profit/Cost Center', EExtraFieldType.String),
    createField(AMOUNT_FIELD, 'Credit Amount ($) Before Tax', EExtraFieldType.Number),
  ];

  const generate = createTask(taskApiName(2), 'generate-code', 2, [taskApiName(1)]);
  let nextNumber = 3;
  const branches = BRANCH_NAMES.flatMap((names) => {
    const branch = createBranch(names, nextNumber);
    nextNumber += names.length;

    return branch;
  });
  const allBeforeSap = [initiate, generate, ...branches];
  const sapReference = createTask(
    taskApiName(54),
    'SAP Reference',
    54,
    allBeforeSap.map((task) => task.apiName),
  );
  sapReference.conditions = [];
  const tasks = [...allBeforeSap, sapReference];

  return {
    ...base,
    tasks,
    tasksCount: tasks.length,
  };
}

/**
 * Routing-equivalent fixture for template 259. Descriptions, performers and form fields that do
 * not own conditions are omitted; task order, branch lengths, joins and Check If sources match the
 * supplied production payload.
 */
export const GRAPH_TEMPLATE_259 = getGraphTemplate259();
