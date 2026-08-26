import { EExtraFieldType, ITemplateClient, ITemplateTaskClient } from '../../../../../types/template';
import { createEmptyTaskDueDate } from '../../../../../utils/dueDate/createEmptyTaskDueDate';
import { EConditionAction, EConditionLogicOperations, EConditionOperators } from '../../../TaskForm/Conditions';
import { EStartingType } from '../../../TaskForm/Conditions/utils/getDropdownOperators';
import { GRAPH_SHOWCASE_TEMPLATE } from '../../fixtures/graphShowcaseTemplate';
import { EGraphNodeType } from '../../types';
import { applyDagreLayout, GRAPH_JUNCTION_SIZE, GRAPH_NODE_WIDTH } from '../applyDagreLayout';
import { GRAPH_CARD_Z_INDEX, GRAPH_COLUMN_GAP } from '../graphGeometry';
import { EMPTY_CONNECTED_HANDLES } from '../applyConnectedHandles';
import { buildTemplateGraph } from '../buildTemplateGraph';
import { getGraphEdgeLine, isSkipGraphEdge } from '../edgeStyles';
import { KICKOFF_NODE_ID, KICKOFF_START_AFTER, templateToGraph } from '../templateToGraph';

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

describe('templateToGraph', () => {
  it('should build a kickoff node and a default edge without arrow markers', () => {
    const { nodes, edges } = templateToGraph(createTemplate());

    expect(nodes[0].id).toBe(KICKOFF_NODE_ID);
    expect(edges).toHaveLength(1);
    expect(edges[0].markerEnd).toBeUndefined();
    expect(edges[0].sourceHandle).toBe('source-bottom');
    expect(edges[0].targetHandle).toBe('target-top');
    expect(edges[0].data?.isConditional).toBe(false);
  });

  it('should keep a start-condition incoming edge as a gray start-after line', () => {
    const { edges } = templateToGraph(
      createTemplate({
        tasks: [
          createTask({
            conditions: [
              {
                apiName: 'condition-start',
                order: 1,
                action: EConditionAction.StartTask,
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
      }),
    );

    expect(edges[0].data?.isConditional).toBe(false);
    expect(edges[0].data?.summary).toBeUndefined();
    expect(edges[0].data?.startAfter).toEqual([KICKOFF_START_AFTER]);
    expect(getGraphEdgeLine(edges[0])).toBe('solid');
    expect(edges[0].className).toBeUndefined();
    expect(edges[0].style).toEqual(
      expect.objectContaining({
        stroke: 'var(--pneumatic-color-black32)',
      }),
    );
  });

  it('should expose only handles that have connected edges', () => {
    const { nodes } = buildTemplateGraph(
      createTemplate({
        tasks: [
          createTask({ apiName: 'task-1', number: 1, uuid: 'uuid-1' }),
          createTask({ apiName: 'task-2', number: 2, uuid: 'uuid-2' }),
        ],
      }),
    );
    const kickoff = nodes.find((node) => node.id === KICKOFF_NODE_ID);
    const firstTask = nodes.find((node) => node.id === 'task-1');
    const lastTask = nodes.find((node) => node.id === 'task-2');

    expect(kickoff && 'handles' in kickoff.data ? kickoff.data.handles : null).toEqual({
      ...EMPTY_CONNECTED_HANDLES,
      hasSourceBottom: true,
    });
    expect(firstTask && 'handles' in firstTask.data ? firstTask.data.handles : null).toEqual({
      ...EMPTY_CONNECTED_HANDLES,
      hasTargetTop: true,
      hasSourceBottom: true,
    });
    expect(lastTask && 'handles' in lastTask.data ? lastTask.data.handles : null).toEqual({
      ...EMPTY_CONNECTED_HANDLES,
      hasTargetTop: true,
    });
  });

  it('should draw a dashed check-if line from the field owner without changing start-after', () => {
    const { nodes, edges } = templateToGraph(
      createTemplate({
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
          createTask({ apiName: 'task-2', name: 'Next', number: 2, uuid: 'uuid-2' }),
        ],
      }),
    );
    const startAfter = edges.filter((edge) => !edge.data?.isConditional);
    const checkIf = edges.filter((edge) => edge.data?.isConditional);

    expect(edges.filter((edge) => isSkipGraphEdge(edge))).toHaveLength(0);
    expect(nodes.some((node) => node.id === 'junction-join-task-1')).toBe(false);
    expect(startAfter.some((edge) => edge.source === 'kickoff' && edge.target === 'task-2')).toBe(false);
    expect(startAfter.some((edge) => edge.source === 'kickoff' && edge.target === 'task-1')).toBe(true);
    expect(startAfter.some((edge) => edge.source === 'task-1' && edge.target === 'task-2')).toBe(true);
    expect(startAfter.every((edge) => getGraphEdgeLine(edge) === 'solid')).toBe(true);
    expect(checkIf).toHaveLength(1);
    expect(checkIf[0].source).toBe('kickoff');
    expect(checkIf[0].target).toBe('task-1');
    expect(getGraphEdgeLine(checkIf[0])).toBe('dashed');
    expect(checkIf[0].data?.clauses?.[0].fieldLabel).toBe('Client');
  });

  it('should draw a start-after edge only from the listed task, not from transitive ancestors', () => {
    const { nodes, edges } = templateToGraph(
      createTemplate({
        tasks: [
          createTask({ apiName: 'task-a', name: 'First', number: 1, uuid: 'uuid-a' }),
          createTask({
            apiName: 'task-b',
            name: 'Second',
            number: 2,
            uuid: 'uuid-b',
            ancestors: ['task-a'],
          }),
          createTask({
            apiName: 'task-c',
            name: 'Third',
            number: 3,
            uuid: 'uuid-c',
            ancestors: ['task-a', 'task-b'],
            conditions: [
              {
                apiName: 'start-after-b',
                order: 1,
                action: EConditionAction.StartTask,
                rules: [
                  {
                    ruleApiName: 'rule-1',
                    predicateApiName: 'predicate-1',
                    field: 'task-b',
                    fieldType: EStartingType.Task,
                    operator: EConditionOperators.Completed,
                    logicOperation: EConditionLogicOperations.And,
                  },
                ],
              },
            ],
          }),
        ],
      }),
    );
    const intoC = edges.filter((edge) => edge.target === 'task-c');

    expect(intoC).toHaveLength(1);
    expect(intoC[0].source).toBe('task-b');
    expect(intoC[0].data?.startAfter).toEqual(['Second']);
    expect(edges.some((edge) => edge.source === 'task-a' && edge.target === 'task-c')).toBe(false);
    expect(nodes.some((node) => node.id === 'junction-join-task-c')).toBe(false);
  });

  it('should drop an implied ancestor from a start-after list that already names its descendant', () => {
    const { nodes, edges } = templateToGraph(
      createTemplate({
        tasks: [
          createTask({ apiName: 'task-a', name: 'First', number: 1, uuid: 'uuid-a' }),
          createTask({
            apiName: 'task-b',
            name: 'Second',
            number: 2,
            uuid: 'uuid-b',
            ancestors: ['task-a'],
          }),
          createTask({
            apiName: 'task-c',
            name: 'Third',
            number: 3,
            uuid: 'uuid-c',
            conditions: [
              {
                apiName: 'start-after-two',
                order: 1,
                action: EConditionAction.StartTask,
                rules: [
                  {
                    ruleApiName: 'rule-a',
                    predicateApiName: 'predicate-a',
                    field: 'task-a',
                    fieldType: EStartingType.Task,
                    operator: EConditionOperators.Completed,
                    logicOperation: EConditionLogicOperations.And,
                  },
                  {
                    ruleApiName: 'rule-b',
                    predicateApiName: 'predicate-b',
                    field: 'task-b',
                    fieldType: EStartingType.Task,
                    operator: EConditionOperators.Completed,
                    logicOperation: EConditionLogicOperations.And,
                  },
                ],
              },
            ],
          }),
        ],
      }),
    );
    const intoC = edges.filter((edge) => edge.target === 'task-c');

    expect(intoC).toHaveLength(1);
    expect(intoC[0].source).toBe('task-b');
    expect(edges.some((edge) => edge.source === 'task-a' && edge.target === 'task-c')).toBe(false);
    expect(nodes.some((node) => node.id === 'junction-join-task-c')).toBe(false);
    expect(nodes.some((node) => node.id === 'junction-fork-task-a')).toBe(false);
  });

  it('should drop transitive ancestors when start-after rules are empty', () => {
    const { nodes, edges } = templateToGraph(
      createTemplate({
        tasks: [
          createTask({ apiName: 'task-a', number: 1, uuid: 'uuid-a' }),
          createTask({ apiName: 'task-b', number: 2, uuid: 'uuid-b', ancestors: ['task-a'] }),
          createTask({
            apiName: 'task-c',
            number: 3,
            uuid: 'uuid-c',
            ancestors: ['task-a', 'task-b'],
          }),
        ],
      }),
    );
    const intoC = edges.filter((edge) => edge.target === 'task-c');

    expect(intoC).toHaveLength(1);
    expect(intoC[0].source).toBe('task-b');
    expect(nodes.some((node) => node.id === 'junction-join-task-c')).toBe(false);
  });

  it('should keep a start-condition sibling on the same gray fork as a plain successor', () => {
    const { nodes, edges } = templateToGraph(
      createTemplate({
        tasks: [
          createTask({ apiName: 'task-a', number: 1, uuid: 'uuid-a' }),
          createTask({ apiName: 'task-b', number: 2, uuid: 'uuid-b', ancestors: ['task-a'] }),
          createTask({
            apiName: 'task-c',
            number: 3,
            uuid: 'uuid-c',
            ancestors: ['task-a'],
            conditions: [
              {
                apiName: 'condition-start',
                order: 1,
                action: EConditionAction.StartTask,
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
      }),
    );
    const fork = nodes.find((node) => node.id === 'junction-fork-task-a');
    const toB = edges.find((edge) => edge.target === 'task-b');
    const toC = edges.find((edge) => edge.target === 'task-c');

    expect(fork).toBeDefined();
    expect(toB?.source).toBe('junction-fork-task-a');
    expect(toC?.source).toBe('junction-fork-task-a');
    expect(toB?.data?.isConditional).toBe(false);
    expect(toC?.data?.isConditional).toBe(false);
    expect(toC?.data?.isLaneRouted).toBeUndefined();
    expect(getGraphEdgeLine(toB!)).toBe('solid');
    expect(getGraphEdgeLine(toC!)).toBe('solid');
  });

  it('should insert a fork node when a task has two parallel successors', () => {
    const { nodes, edges } = templateToGraph(
      createTemplate({
        tasks: [
          createTask({ apiName: 'task-a', number: 1, uuid: 'uuid-a' }),
          createTask({ apiName: 'task-b', number: 2, uuid: 'uuid-b', ancestors: ['task-a'] }),
          createTask({ apiName: 'task-c', number: 3, uuid: 'uuid-c', ancestors: ['task-a'] }),
        ],
      }),
    );

    const fork = nodes.find((node) => node.id === 'junction-fork-task-a');

    expect(fork).toBeDefined();
    expect(fork?.type).toBe(EGraphNodeType.Junction);
    expect(fork && 'kind' in fork.data ? fork.data.kind : null).toBe('fork');
    expect(edges.some((edge) => edge.source === 'task-a' && edge.target === 'junction-fork-task-a')).toBe(true);
    expect(edges.filter((edge) => edge.source === 'junction-fork-task-a')).toHaveLength(2);
    expect(edges.some((edge) => edge.source === 'task-a' && edge.target === 'task-b')).toBe(false);
    const stem = edges.find((edge) => edge.source === 'task-a' && edge.target === 'junction-fork-task-a');
    const branches = edges.filter((edge) => edge.source === 'junction-fork-task-a');

    expect(stem?.data?.startAfter).toEqual(['Prepare Layout']);
    expect(branches.every((edge) => !edge.data?.startAfter?.length)).toBe(true);
  });

  it('should insert a join node when a task has two ancestors', () => {
    const { nodes, edges } = templateToGraph(
      createTemplate({
        tasks: [
          createTask({ apiName: 'task-a', number: 1, uuid: 'uuid-a' }),
          createTask({ apiName: 'task-b', number: 2, uuid: 'uuid-b', ancestors: ['task-a'] }),
          createTask({ apiName: 'task-c', number: 3, uuid: 'uuid-c', ancestors: ['task-a'] }),
          createTask({
            apiName: 'task-d',
            number: 4,
            uuid: 'uuid-d',
            ancestors: ['task-b', 'task-c'],
          }),
        ],
      }),
    );

    const join = nodes.find((node) => node.id === 'junction-join-task-d');

    expect(join).toBeDefined();
    expect(join && 'kind' in join.data ? join.data.kind : null).toBe('join');
    expect(edges.filter((edge) => edge.target === 'junction-join-task-d')).toHaveLength(2);
    expect(edges.some((edge) => edge.source === 'junction-join-task-d' && edge.target === 'task-d')).toBe(true);
    expect(edges.some((edge) => edge.source === 'task-b' && edge.target === 'task-d')).toBe(false);
    const intoJoin = edges.filter((edge) => edge.target === 'junction-join-task-d');
    const afterJoin = edges.find((edge) => edge.source === 'junction-join-task-d');

    expect(intoJoin.every((edge) => Boolean(edge.data?.startAfter?.length))).toBe(true);
    expect(afterJoin?.data?.startAfter).toBeUndefined();
  });

  it('should map the showcase template to start-after stems and a check-if line', () => {
    const { nodes, edges } = templateToGraph(GRAPH_SHOWCASE_TEMPLATE);
    const taskIds = nodes.filter((node) => node.type === EGraphNodeType.Task).map((node) => node.id);
    const startAfter = edges.filter((edge) => !edge.data?.isConditional);
    const checkIf = edges.filter((edge) => edge.data?.isConditional);

    expect(nodes.some((node) => node.id === KICKOFF_NODE_ID)).toBe(true);
    expect(taskIds).toEqual([
      'task-linear',
      'task-skippable',
      'task-url-title',
      'task-parallel-a',
      'task-parallel-b',
      'task-join',
      'task-long-title',
    ]);
    expect(nodes.some((node) => node.id === 'junction-fork-task-url-title')).toBe(true);
    expect(nodes.some((node) => node.id === 'junction-join-task-join')).toBe(true);
    expect(nodes.some((node) => node.id === 'junction-join-task-skippable')).toBe(false);
    expect(nodes.some((node) => node.id === 'junction-fork-task-linear')).toBe(false);
    expect(nodes.some((node) => node.id === 'junction-join-task-url-title')).toBe(false);
    expect(edges.filter((edge) => isSkipGraphEdge(edge))).toHaveLength(0);
    expect(startAfter.every((edge) => getGraphEdgeLine(edge) === 'solid')).toBe(true);
    expect(startAfter.every((edge) => edge.style?.stroke === 'var(--pneumatic-color-black32)')).toBe(true);
    expect(checkIf).toHaveLength(1);
    expect(checkIf[0].source).toBe(KICKOFF_NODE_ID);
    expect(checkIf[0].target).toBe('task-skippable');
    expect(getGraphEdgeLine(checkIf[0])).toBe('dashed');
    const cards = nodes.filter((node) => node.type !== EGraphNodeType.Junction);

    expect(cards.every((node) => (node.zIndex ?? 0) >= GRAPH_CARD_Z_INDEX)).toBe(true);
    expect(checkIf[0].zIndex ?? 0).toBeLessThan(GRAPH_CARD_Z_INDEX);
  });
});

describe('applyDagreLayout', () => {
  it('should place tasks below the kickoff node', () => {
    const { nodes, edges } = templateToGraph(createTemplate());
    const layouted = applyDagreLayout(nodes, edges);
    const kickoff = layouted.find((node) => node.id === KICKOFF_NODE_ID);
    const task = layouted.find((node) => node.id === 'task-1');

    expect(kickoff).toBeDefined();
    expect(task).toBeDefined();
    expect(task!.position.y).toBeGreaterThan(kickoff!.position.y);
  });

  it('should place sibling nodes on the same row', () => {
    const { nodes, edges } = templateToGraph(
      createTemplate({
        tasks: [
          createTask({ apiName: 'task-a', number: 1, uuid: 'uuid-a' }),
          createTask({
            apiName: 'task-b',
            number: 2,
            uuid: 'uuid-b',
            ancestors: ['task-a'],
          }),
          createTask({
            apiName: 'task-c',
            number: 3,
            uuid: 'uuid-c',
            ancestors: ['task-a'],
          }),
        ],
      }),
    );
    const layouted = applyDagreLayout(nodes, edges);
    const taskB = layouted.find((node) => node.id === 'task-b');
    const taskC = layouted.find((node) => node.id === 'task-c');

    expect(taskB!.position.y).toBe(taskC!.position.y);
    expect(taskB!.position.x).not.toBe(taskC!.position.x);
  });

  it('should keep the longest flow on one vertical and send shorter branches aside', () => {
    const { nodes, edges } = templateToGraph(
      createTemplate({
        tasks: [
          createTask({ apiName: 'task-a', number: 1, uuid: 'uuid-a' }),
          createTask({ apiName: 'task-b1', number: 2, uuid: 'uuid-b1', ancestors: ['task-a'] }),
          createTask({ apiName: 'task-b2', number: 3, uuid: 'uuid-b2', ancestors: ['task-b1'] }),
          createTask({ apiName: 'task-c', number: 4, uuid: 'uuid-c', ancestors: ['task-a'] }),
        ],
      }),
    );
    const layouted = applyDagreLayout(nodes, edges);
    const centerX = (id: string) => {
      const node = layouted.find((item) => item.id === id);

      return (node?.position.x ?? 0) + (node?.width ?? GRAPH_NODE_WIDTH) / 2;
    };

    expect(centerX('kickoff')).toBe(centerX('task-a'));
    expect(centerX('task-a')).toBe(centerX('task-b1'));
    expect(centerX('task-b1')).toBe(centerX('task-b2'));
    expect(centerX('task-c')).toBeLessThan(centerX('task-b1'));
  });

  it('should fan side branches from the stem to the left and right', () => {
    const { nodes, edges } = templateToGraph(
      createTemplate({
        tasks: [
          createTask({ apiName: 'task-a', number: 1, uuid: 'uuid-a' }),
          createTask({ apiName: 'task-short', number: 2, uuid: 'uuid-short', ancestors: ['task-a'] }),
          createTask({ apiName: 'task-mid-1', number: 3, uuid: 'uuid-mid-1', ancestors: ['task-a'] }),
          createTask({ apiName: 'task-mid-2', number: 4, uuid: 'uuid-mid-2', ancestors: ['task-mid-1'] }),
          createTask({ apiName: 'task-long-1', number: 5, uuid: 'uuid-long-1', ancestors: ['task-a'] }),
          createTask({ apiName: 'task-long-2', number: 6, uuid: 'uuid-long-2', ancestors: ['task-long-1'] }),
          createTask({ apiName: 'task-long-3', number: 7, uuid: 'uuid-long-3', ancestors: ['task-long-2'] }),
        ],
      }),
    );
    const layouted = applyDagreLayout(nodes, edges);
    const centerX = (id: string) => {
      const node = layouted.find((item) => item.id === id);

      return (node?.position.x ?? 0) + (node?.width ?? GRAPH_NODE_WIDTH) / 2;
    };

    expect(centerX('task-a')).toBe(centerX('task-long-1'));
    expect(centerX('task-short')).toBeLessThan(centerX('task-long-1'));
    expect(centerX('task-mid-1')).toBeGreaterThan(centerX('task-long-1'));
    expect(centerX('task-mid-1')).toBe(centerX('task-mid-2'));
    expect(centerX('task-long-1')).toBe(centerX('task-long-3'));
  });

  it('should keep a check-if partner on the same side of the stem as its source card', () => {
    const { nodes, edges } = templateToGraph(
      createTemplate({
        tasks: [
          createTask({ apiName: 'task-a', number: 1, uuid: 'uuid-a' }),
          createTask({
            apiName: 'task-left',
            number: 2,
            uuid: 'uuid-left',
            ancestors: ['task-a'],
            fields: [
              {
                apiName: 'left-field',
                name: 'Flag',
                type: EExtraFieldType.String,
                order: 0,
                userId: null,
                groupId: null,
              },
            ],
          }),
          createTask({
            apiName: 'task-mid',
            number: 3,
            uuid: 'uuid-mid',
            ancestors: ['task-a'],
            conditions: [
              {
                apiName: 'mid-skip',
                order: 1,
                action: EConditionAction.SkipTask,
                rules: [
                  {
                    ruleApiName: 'mid-skip-rule',
                    predicateApiName: 'mid-skip-predicate',
                    field: 'left-field',
                    operator: EConditionOperators.Exist,
                    logicOperation: EConditionLogicOperations.And,
                  },
                ],
              },
            ],
          }),
          createTask({ apiName: 'task-long-1', number: 4, uuid: 'uuid-long-1', ancestors: ['task-a'] }),
          createTask({ apiName: 'task-long-2', number: 5, uuid: 'uuid-long-2', ancestors: ['task-long-1'] }),
          createTask({ apiName: 'task-long-3', number: 6, uuid: 'uuid-long-3', ancestors: ['task-long-2'] }),
        ],
      }),
    );
    const layouted = applyDagreLayout(nodes, edges);
    const centerX = (id: string) => {
      const node = layouted.find((item) => item.id === id);

      return (node?.position.x ?? 0) + (node?.width ?? GRAPH_NODE_WIDTH) / 2;
    };

    expect(centerX('task-left')).toBeLessThan(centerX('task-a'));
    expect(centerX('task-mid')).toBeLessThan(centerX('task-a'));
    expect(Math.sign(centerX('task-mid') - centerX('task-a'))).toBe(
      Math.sign(centerX('task-left') - centerX('task-a')),
    );
  });

  it('should grow nested extras of a side branch outward, not through the stem', () => {
    const { nodes, edges } = templateToGraph(
      createTemplate({
        tasks: [
          createTask({ apiName: 'task-a', number: 1, uuid: 'uuid-a' }),
          createTask({ apiName: 'task-short', number: 2, uuid: 'uuid-short', ancestors: ['task-a'] }),
          createTask({ apiName: 'task-mid-1', number: 3, uuid: 'uuid-mid-1', ancestors: ['task-a'] }),
          createTask({ apiName: 'task-mid-2', number: 4, uuid: 'uuid-mid-2', ancestors: ['task-mid-1'] }),
          createTask({ apiName: 'task-mid-side', number: 5, uuid: 'uuid-mid-side', ancestors: ['task-mid-1'] }),
          createTask({ apiName: 'task-long-1', number: 6, uuid: 'uuid-long-1', ancestors: ['task-a'] }),
          createTask({ apiName: 'task-long-2', number: 7, uuid: 'uuid-long-2', ancestors: ['task-long-1'] }),
          createTask({ apiName: 'task-long-3', number: 8, uuid: 'uuid-long-3', ancestors: ['task-long-2'] }),
        ],
      }),
    );
    const layouted = applyDagreLayout(nodes, edges);
    const centerX = (id: string) => {
      const node = layouted.find((item) => item.id === id);

      return (node?.position.x ?? 0) + (node?.width ?? GRAPH_NODE_WIDTH) / 2;
    };

    expect(centerX('task-mid-1')).toBeGreaterThan(centerX('task-long-1'));
    expect(centerX('task-mid-2')).toBe(centerX('task-mid-1'));
    expect(centerX('task-mid-side')).toBeGreaterThan(centerX('task-mid-1'));
  });

  it('should keep extras from jumping over a tree already occupying the other side', () => {
    const { nodes, edges } = templateToGraph(
      createTemplate({
        tasks: [
          createTask({ apiName: 'task-a', number: 1, uuid: 'uuid-a' }),
          createTask({ apiName: 'task-leaf', number: 2, uuid: 'uuid-leaf', ancestors: ['task-a'] }),
          createTask({ apiName: 'task-right-1', number: 3, uuid: 'uuid-right-1', ancestors: ['task-a'] }),
          createTask({ apiName: 'task-right-2', number: 4, uuid: 'uuid-right-2', ancestors: ['task-right-1'] }),
          createTask({ apiName: 'task-right-3', number: 5, uuid: 'uuid-right-3', ancestors: ['task-right-2'] }),
          createTask({ apiName: 'task-stem-1', number: 6, uuid: 'uuid-stem-1', ancestors: ['task-a'] }),
          createTask({ apiName: 'task-stem-2', number: 7, uuid: 'uuid-stem-2', ancestors: ['task-stem-1'] }),
          createTask({ apiName: 'task-stem-3', number: 8, uuid: 'uuid-stem-3', ancestors: ['task-stem-2'] }),
          createTask({ apiName: 'task-stem-4', number: 9, uuid: 'uuid-stem-4', ancestors: ['task-stem-3'] }),
          createTask({ apiName: 'task-extra-a', number: 10, uuid: 'uuid-extra-a', ancestors: ['task-stem-2'] }),
          createTask({ apiName: 'task-extra-b', number: 11, uuid: 'uuid-extra-b', ancestors: ['task-stem-2'] }),
          createTask({ apiName: 'task-extra-c', number: 12, uuid: 'uuid-extra-c', ancestors: ['task-stem-2'] }),
        ],
      }),
    );
    const layouted = applyDagreLayout(nodes, edges);
    const centerX = (id: string) => {
      const node = layouted.find((item) => item.id === id);

      return (node?.position.x ?? 0) + (node?.width ?? GRAPH_NODE_WIDTH) / 2;
    };

    expect(centerX('task-right-3')).toBeGreaterThan(centerX('task-stem-3'));
    expect(centerX('task-extra-a')).toBeLessThan(centerX('task-stem-3'));
    expect(centerX('task-extra-b')).toBeLessThan(centerX('task-stem-3'));
    expect(centerX('task-extra-c')).toBeLessThan(centerX('task-stem-3'));
  });

  it('should keep kickoff extras in the adjacent columns around the stem', () => {
    const { nodes, edges } = templateToGraph(
      createTemplate({
        tasks: [
          createTask({ apiName: 'task-1', number: 1, uuid: 'uuid-1', ancestors: ['kickoff'] }),
          createTask({ apiName: 'task-2', number: 2, uuid: 'uuid-2', ancestors: ['task-1'] }),
          createTask({ apiName: 'task-3', number: 3, uuid: 'uuid-3', ancestors: ['task-2'] }),
          createTask({ apiName: 'task-4', number: 4, uuid: 'uuid-4', ancestors: ['task-3'] }),
          createTask({ apiName: 'task-5', number: 5, uuid: 'uuid-5', ancestors: ['kickoff'] }),
          createTask({ apiName: 'task-6', number: 6, uuid: 'uuid-6', ancestors: ['kickoff'] }),
          createTask({ apiName: 'task-7', number: 7, uuid: 'uuid-7', ancestors: ['task-4'] }),
          createTask({ apiName: 'task-8', number: 8, uuid: 'uuid-8', ancestors: ['task-4'] }),
          createTask({ apiName: 'task-9', number: 9, uuid: 'uuid-9', ancestors: ['task-5'] }),
          createTask({ apiName: 'task-10', number: 10, uuid: 'uuid-10', ancestors: ['task-2'] }),
          createTask({ apiName: 'task-11', number: 11, uuid: 'uuid-11', ancestors: ['task-2'] }),
          createTask({ apiName: 'task-12', number: 12, uuid: 'uuid-12', ancestors: ['task-2'] }),
          createTask({ apiName: 'task-13', number: 13, uuid: 'uuid-13', ancestors: ['task-9'] }),
        ],
      }),
    );
    const layouted = applyDagreLayout(nodes, edges);
    const centerX = (id: string) => {
      const node = layouted.find((item) => item.id === id);

      return (node?.position.x ?? 0) + (node?.width ?? GRAPH_NODE_WIDTH) / 2;
    };
    const pitch = GRAPH_NODE_WIDTH + GRAPH_COLUMN_GAP;

    expect(centerX('task-6')).toBe(centerX('task-1') - pitch);
    expect(centerX('task-5')).toBe(centerX('task-1') + pitch);
    expect(centerX('task-13')).toBe(centerX('task-5'));
    expect(centerX('task-10')).toBeLessThan(centerX('task-1'));
    expect(centerX('task-11')).toBeLessThan(centerX('task-1'));
    expect(centerX('task-12')).toBeLessThan(centerX('task-1'));
  });

  it('should keep a side branch stacked in its own column', () => {
    const { nodes, edges } = templateToGraph(
      createTemplate({
        tasks: [
          createTask({ apiName: 'task-a', number: 1, uuid: 'uuid-a' }),
          createTask({ apiName: 'task-b', number: 2, uuid: 'uuid-b', ancestors: ['task-a'] }),
          createTask({ apiName: 'task-c1', number: 3, uuid: 'uuid-c1', ancestors: ['task-a'] }),
          createTask({ apiName: 'task-c2', number: 4, uuid: 'uuid-c2', ancestors: ['task-c1'] }),
        ],
      }),
    );
    const layouted = applyDagreLayout(nodes, edges);
    const centerX = (id: string) => {
      const node = layouted.find((item) => item.id === id);

      return (node?.position.x ?? 0) + (node?.width ?? GRAPH_NODE_WIDTH) / 2;
    };

    expect(centerX('task-a')).toBe(centerX('task-c1'));
    expect(centerX('task-c1')).toBe(centerX('task-c2'));
    expect(centerX('task-b')).not.toBe(centerX('task-c1'));
  });

  it('should place a fork node between the parent and parallel children', () => {
    const { nodes, edges } = templateToGraph(
      createTemplate({
        tasks: [
          createTask({ apiName: 'task-a', number: 1, uuid: 'uuid-a' }),
          createTask({ apiName: 'task-b', number: 2, uuid: 'uuid-b', ancestors: ['task-a'] }),
          createTask({ apiName: 'task-c', number: 3, uuid: 'uuid-c', ancestors: ['task-a'] }),
        ],
      }),
    );
    const layouted = applyDagreLayout(nodes, edges);
    const taskA = layouted.find((node) => node.id === 'task-a');
    const taskB = layouted.find((node) => node.id === 'task-b');
    const fork = layouted.find((node) => node.id === 'junction-fork-task-a');

    expect(fork).toBeDefined();
    expect(fork!.position.y).toBeGreaterThan(taskA!.position.y);
    expect(fork!.position.y).toBeLessThan(taskB!.position.y);

    const parentCenter = taskA!.position.x + GRAPH_NODE_WIDTH / 2;
    const forkCenter = fork!.position.x + GRAPH_JUNCTION_SIZE / 2;

    expect(forkCenter).toBe(parentCenter);
  });

  it('should put cards of the same nesting depth on one row', () => {
    const { nodes, edges } = templateToGraph(
      createTemplate({
        tasks: [
          createTask({ apiName: 'task-a', number: 1, uuid: 'uuid-a' }),
          createTask({ apiName: 'task-b', number: 2, uuid: 'uuid-b', ancestors: ['task-a'] }),
          createTask({ apiName: 'task-c', number: 3, uuid: 'uuid-c', ancestors: ['task-a'] }),
          createTask({ apiName: 'task-d', number: 4, uuid: 'uuid-d', ancestors: ['task-c'] }),
          createTask({ apiName: 'task-e', number: 5, uuid: 'uuid-e', ancestors: ['task-b'] }),
        ],
      }),
    );
    const layouted = applyDagreLayout(nodes, edges);
    const taskD = layouted.find((node) => node.id === 'task-d');
    const taskE = layouted.find((node) => node.id === 'task-e');
    const taskC = layouted.find((node) => node.id === 'task-c');

    expect(taskD!.position.y).toBe(taskE!.position.y);
    expect(taskC!.position.x).toBe(taskD!.position.x);
    expect(Math.abs(taskE!.position.x - taskD!.position.x)).toBe(GRAPH_NODE_WIDTH + GRAPH_COLUMN_GAP);
  });
});
