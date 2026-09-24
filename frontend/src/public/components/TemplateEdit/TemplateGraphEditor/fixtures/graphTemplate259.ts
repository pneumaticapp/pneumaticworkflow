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

function createSkipCondition(apiName: string, predecessor?: string): ICondition {
  const rules: TConditionRule[] = [createRule(`${apiName}-cost`, COST_CENTER_FIELD, EExtraFieldType.String)];

  if (predecessor) {
    rules.push(
      createRule(`${apiName}-amount`, AMOUNT_FIELD, EExtraFieldType.Number),
      createRule(`${apiName}-task`, predecessor, EStartingType.Task),
    );
  }

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
  predecessor?: string,
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
    conditions: number > 2 ? [createSkipCondition(`${apiName}-skip`, predecessor)] : [],
    uuid: `${apiName}-uuid`,
    checklists: [],
    revertTask: null,
    ancestors,
  };
}

function createBranch(names: readonly string[], startNumber: number): ITemplateTaskClient[] {
  return names.map((name, index) => {
    const apiName = `template-259-task-${startNumber + index}`;
    const previous = index === 0 ? undefined : `template-259-task-${startNumber + index - 1}`;
    const branchAncestors = Array.from(
      { length: index },
      (_, ancestorIndex) => `template-259-task-${startNumber + ancestorIndex}`,
    );

    return createTask(
      apiName,
      name,
      startNumber + index,
      [...branchAncestors, 'template-259-task-2', 'template-259-task-1'],
      previous,
    );
  });
}

export function getGraphTemplate259(base: ITemplateClient = TEMPLATE_BASE): ITemplateClient {
  const initiate = createTask('template-259-task-1', 'Initiate Process', 1, []);
  initiate.fields = [
    createField(COST_CENTER_FIELD, 'Profit/Cost Center', EExtraFieldType.String),
    createField(AMOUNT_FIELD, 'Credit Amount ($) Before Tax', EExtraFieldType.Number),
  ];

  const generate = createTask('template-259-task-2', 'generate-code', 2, ['template-259-task-1']);
  let nextNumber = 3;
  const branches = BRANCH_NAMES.flatMap((names) => {
    const branch = createBranch(names, nextNumber);
    nextNumber += names.length;

    return branch;
  });
  const allBeforeSap = [initiate, generate, ...branches];
  const sapReference = createTask(
    'template-259-task-54',
    'SAP Reference',
    54,
    allBeforeSap.map((task) => task.apiName),
  );
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
