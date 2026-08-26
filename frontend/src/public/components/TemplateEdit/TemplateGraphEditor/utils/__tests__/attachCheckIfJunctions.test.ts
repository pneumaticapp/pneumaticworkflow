import { EExtraFieldType, ITemplateClient, ITemplateTaskClient } from '../../../../../types/template';
import { createEmptyTaskDueDate } from '../../../../../utils/dueDate/createEmptyTaskDueDate';
import { EConditionAction, EConditionLogicOperations, EConditionOperators } from '../../../TaskForm/Conditions';
import { KICKOFF_NODE_ID, templateToGraph } from '../templateToGraph';

function createTask(overrides: Partial<ITemplateTaskClient> = {}): ITemplateTaskClient {
  return {
    apiName: 'task-1',
    name: 'Prepare Layout',
    description: '',
    number: 1,
    requireCompletionByAll: false,
    skipForStarter: false,
    fields: [],
    fieldsets: [],
    rawPerformers: [],
    delay: null,
    rawDueDate: createEmptyTaskDueDate(),
    conditions: [],
    uuid: 'uuid-1',
    checklists: [],
    revertTask: null,
    ancestors: [],
    ...overrides,
  };
}

function createTemplate(overrides: Partial<ITemplateClient> = {}): ITemplateClient {
  return {
    name: 'Template',
    description: '',
    isActive: false,
    finalizable: false,
    completionNotification: false,
    reminderNotification: false,
    dateUpdated: null,
    updatedBy: null,
    owners: [],
    kickoff: {
      description: '',
      fields: [
        {
          apiName: 'field-1',
          name: 'Client',
          type: EExtraFieldType.String,
          order: 0,
          userId: null,
          groupId: null,
        },
      ],
      fieldsets: [],
    },
    tasks: [createTask()],
    isPublic: false,
    publicUrl: null,
    publicSuccessUrl: null,
    isEmbedded: false,
    embedUrl: null,
    wfNameTemplate: null,
    tasksCount: 1,
    performersCount: 0,
    ...overrides,
  };
}

describe('attachCheckIfJunctions', () => {
  it('should dock a check-if line on the target card, not on the gray stem join', () => {
    const { nodes, edges } = templateToGraph(
      createTemplate({
        tasks: [
          createTask({
            conditions: [
              {
                apiName: 'skip-1',
                order: 1,
                action: EConditionAction.SkipTask,
                rules: [
                  {
                    ruleApiName: 'rule-1',
                    predicateApiName: 'predicate-1',
                    field: 'field-1',
                    operator: EConditionOperators.Exist,
                    logicOperation: EConditionLogicOperations.And,
                  },
                ],
              },
            ],
          }),
          createTask({ apiName: 'task-2', number: 2, uuid: 'uuid-2' }),
        ],
      }),
    );
    const checkIf = edges.filter((edge) => edge.data?.isConditional);
    const startAfter = edges.filter((edge) => !edge.data?.isConditional);

    expect(nodes.some((node) => node.id === 'junction-join-task-1')).toBe(false);
    expect(checkIf).toHaveLength(1);
    expect(checkIf[0].target).toBe('task-1');
    expect(startAfter.some((edge) => edge.source === KICKOFF_NODE_ID && edge.target === 'task-1')).toBe(true);
  });

  it('should share one join when two check-if lines arrive at the same card', () => {
    const { edges } = templateToGraph(
      createTemplate({
        tasks: [
          createTask({
            apiName: 'task-a',
            number: 1,
            uuid: 'uuid-a',
            fields: [
              {
                apiName: 'flag-a',
                name: 'Flag A',
                type: EExtraFieldType.String,
                order: 0,
                userId: null,
                groupId: null,
              },
            ],
          }),
          createTask({
            apiName: 'task-b',
            number: 2,
            uuid: 'uuid-b',
            ancestors: ['task-a'],
            conditions: [
              {
                apiName: 'skip-from-kickoff',
                order: 1,
                action: EConditionAction.SkipTask,
                rules: [
                  {
                    ruleApiName: 'rule-k',
                    predicateApiName: 'pred-k',
                    field: 'field-1',
                    operator: EConditionOperators.Exist,
                    logicOperation: EConditionLogicOperations.And,
                  },
                ],
              },
              {
                apiName: 'skip-from-a',
                order: 2,
                action: EConditionAction.SkipTask,
                rules: [
                  {
                    ruleApiName: 'rule-a',
                    predicateApiName: 'pred-a',
                    field: 'flag-a',
                    operator: EConditionOperators.Exist,
                    logicOperation: EConditionLogicOperations.And,
                  },
                ],
              },
            ],
          }),
        ],
      }),
    );
    const intoJoin = edges.filter((edge) => (
      edge.target === 'junction-join-checkif-task-b' && edge.data?.isConditional
    ));

    expect(intoJoin).toHaveLength(2);
    expect(intoJoin.map((edge) => edge.source).sort()).toEqual([KICKOFF_NODE_ID, 'task-a']);
    expect(edges.some((edge) => (
      edge.source === 'junction-join-checkif-task-b'
      && edge.target === 'task-b'
      && edge.data?.isConditional
    ))).toBe(true);
    expect(edges.some((edge) => edge.target === 'junction-join-task-b' && edge.data?.isConditional)).toBe(false);
  });
});
