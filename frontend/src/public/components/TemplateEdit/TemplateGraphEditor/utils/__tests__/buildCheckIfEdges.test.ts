import { EExtraFieldType, ITemplateClient, ITemplateTaskClient } from '../../../../../types/template';
import { createEmptyTaskDueDate } from '../../../../../utils/dueDate/createEmptyTaskDueDate';
import { EConditionAction, EConditionLogicOperations, EConditionOperators } from '../../../TaskForm/Conditions';
import { EStartingType } from '../../../TaskForm/Conditions/utils/getDropdownOperators';
import { getGraphEdgeLine } from '../edgeStyles';
import { KICKOFF_NODE_ID } from '../graphConstants';
import { GRAPH_CARD_Z_INDEX } from '../graphGeometry';
import { buildCheckIfEdges } from '../buildCheckIfEdges';

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
    name: 'New Template',
    description: '',
    isActive: false,
    finalizable: false,
    completionNotification: false,
    reminderNotification: false,
    dateUpdated: null,
    updatedBy: null,
    owners: [],
    kickoff: {
      description: '<p>Kickoff text</p>',
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

describe('buildCheckIfEdges', () => {
  it('should draw a dashed check-if line from the kickoff field owner', () => {
    const template = createTemplate({
      tasks: [
        createTask({
          conditions: [
            {
              apiName: 'condition-1',
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
      ],
    });
    const edges = buildCheckIfEdges(template, template.tasks, new Set(['task-1']));

    expect(edges).toHaveLength(1);
    expect(edges[0].source).toBe(KICKOFF_NODE_ID);
    expect(edges[0].target).toBe('task-1');
    expect(edges[0].data?.isConditional).toBe(true);
    expect(edges[0].data?.clauses).toEqual([
      {
        fieldLabel: 'Client',
        operator: EConditionOperators.Exist,
        value: undefined,
        logicOperation: EConditionLogicOperations.And,
      },
    ]);
    expect(getGraphEdgeLine(edges[0])).toBe('dashed');
    expect(edges[0].zIndex ?? 0).toBeLessThan(GRAPH_CARD_Z_INDEX);
  });

  it('should draw a dashed line from a completed task named in check-if', () => {
    const template = createTemplate({
      tasks: [
        createTask({ apiName: 'task-a', name: 'First', number: 1, uuid: 'uuid-a' }),
        createTask({
          apiName: 'task-b',
          name: 'Second',
          number: 2,
          uuid: 'uuid-b',
          conditions: [
            {
              apiName: 'end-if',
              order: 1,
              action: EConditionAction.EndProcess,
              rules: [
                {
                  ruleApiName: 'rule-1',
                  predicateApiName: 'predicate-1',
                  field: 'task-a',
                  fieldType: EStartingType.Task,
                  operator: EConditionOperators.Completed,
                  logicOperation: EConditionLogicOperations.And,
                },
              ],
            },
          ],
        }),
      ],
    });
    const edges = buildCheckIfEdges(template, template.tasks, new Set(['task-a', 'task-b']));

    expect(edges).toHaveLength(1);
    expect(edges[0].source).toBe('task-a');
    expect(edges[0].target).toBe('task-b');
    expect(edges[0].data?.clauses?.[0].fieldLabel).toBe('First');
    expect(edges[0].data?.clauses?.[0].operator).toBe(EConditionOperators.Completed);
  });

  it('should skip a check-if rule whose field cannot be resolved', () => {
    const template = createTemplate({
      kickoff: { description: '', fields: [], fieldsets: [] },
      tasks: [
        createTask({
          conditions: [
            {
              apiName: 'condition-1',
              order: 1,
              action: EConditionAction.SkipTask,
              rules: [
                {
                  ruleApiName: 'rule-1',
                  predicateApiName: 'predicate-1',
                  field: 'missing-field',
                  operator: EConditionOperators.Exist,
                  logicOperation: EConditionLogicOperations.And,
                },
              ],
            },
          ],
        }),
      ],
    });

    expect(buildCheckIfEdges(template, template.tasks, new Set(['task-1']))).toHaveLength(0);
  });

  it('should not draw a self-loop when a task checks its own field', () => {
    const template = createTemplate({
      tasks: [
        createTask({
          fields: [
            {
              apiName: 'own-field',
              name: 'Own',
              type: EExtraFieldType.String,
              order: 0,
              userId: null,
              groupId: null,
            },
          ],
          conditions: [
            {
              apiName: 'condition-1',
              order: 1,
              action: EConditionAction.SkipTask,
              rules: [
                {
                  ruleApiName: 'rule-1',
                  predicateApiName: 'predicate-1',
                  field: 'own-field',
                  operator: EConditionOperators.Exist,
                  logicOperation: EConditionLogicOperations.And,
                },
              ],
            },
          ],
        }),
      ],
    });

    expect(buildCheckIfEdges(template, template.tasks, new Set(['task-1']))).toHaveLength(0);
  });

  it('should merge check-if rules that share a source card', () => {
    const template = createTemplate({
      tasks: [
        createTask({
          conditions: [
            {
              apiName: 'skip',
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
                {
                  ruleApiName: 'rule-2',
                  predicateApiName: 'predicate-2',
                  field: 'field-1',
                  operator: EConditionOperators.Equal,
                  value: 'Acme',
                  logicOperation: EConditionLogicOperations.Or,
                },
              ],
            },
          ],
        }),
      ],
    });
    const edges = buildCheckIfEdges(template, template.tasks, new Set(['task-1']));

    expect(edges).toHaveLength(1);
    expect(edges[0].data?.clauses).toHaveLength(2);
    expect(edges[0].data?.summary).toContain('Client');
  });
});
