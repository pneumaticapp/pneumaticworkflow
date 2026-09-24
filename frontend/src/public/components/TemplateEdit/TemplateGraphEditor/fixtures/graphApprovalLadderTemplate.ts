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
  name: 'Graph approval ladder',
  description: 'Dense cross-column Check If traffic between a source column and an approval chain',
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

const SOURCE_NAMES = [
  'Approval National',
  'Regional Education',
  'Approval National Education',
  'District Education',
  'Approval Regional',
];

const APPROVAL_NAMES = ['Manager Approval CMP', 'Director Approval CMP', 'VP Approval CMP', 'President Approval CMP'];

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

function createSkipFromField(apiName: string, field: string, order: number): ICondition {
  return {
    apiName,
    order,
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

function createSourceColumn(): ITemplateTaskClient[] {
  return SOURCE_NAMES.map((name, index) =>
    createTask({
      apiName: `source-${index + 1}`,
      name,
      number: index + 1,
      ancestors: index === 0 ? [] : [`source-${index}`],
      fields: [createField(`source-flag-${index + 1}`, `Flag ${index + 1}`)],
    }),
  );
}

/** Approval N carries N * 2 - 1 conditions, so the dashed traffic grows down the ladder. */
function createApprovalChain(): ITemplateTaskClient[] {
  return APPROVAL_NAMES.map((name, index) => {
    const conditionCount = index * 2 + 1;

    return createTask({
      apiName: `approval-${index + 1}`,
      name,
      number: SOURCE_NAMES.length + index + 1,
      ancestors: index === 0 ? ['source-1'] : [`approval-${index}`],
      conditions: Array.from({ length: conditionCount }, (_, ruleIndex) =>
        createSkipFromField(
          `skip-approval-${index + 1}-${ruleIndex + 1}`,
          `source-flag-${(ruleIndex % SOURCE_NAMES.length) + 1}`,
          ruleIndex + 1,
        ),
      ),
    });
  });
}

/**
 * Two parallel columns joined by many Check If lines: a source column that owns the fields and
 * an approval ladder whose cards each skip on a growing set of those fields. Reproduces the dense
 * dashed traffic where detour lanes crowd each other and dive under cards.
 */
export function getGraphApprovalLadderTemplate(base: ITemplateClient = EMPTY_TEMPLATE_BASE): ITemplateClient {
  const tasks = [...createSourceColumn(), ...createApprovalChain()];

  return {
    ...base,
    tasks,
    tasksCount: tasks.length,
    performersCount: tasks.filter((task) => task.rawPerformers.length > 0).length,
  };
}

export const GRAPH_APPROVAL_LADDER_TEMPLATE = getGraphApprovalLadderTemplate();
