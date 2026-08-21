import { EExtraFieldType, ITemplateClient, ITemplateTaskClient } from '../../../../../types/template';
import { createEmptyTaskDueDate } from '../../../../../utils/dueDate/createEmptyTaskDueDate';
import { EConditionAction, EConditionLogicOperations, EConditionOperators } from '../../../TaskForm/Conditions';
import { GRAPH_SHOWCASE_TEMPLATE } from '../../fixtures/graphShowcaseTemplate';
import { EGraphNodeType } from '../../types';
import { applyDagreLayout, GRAPH_JUNCTION_SIZE, GRAPH_NODE_WIDTH } from '../applyDagreLayout';
import { GRAPH_EDGE_CLASS_SKIP } from '../edgeStyles';
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

  it('should expose only handles that have connected edges', () => {
    const { nodes } = templateToGraph(
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
      hasTargetTop: false,
      hasSourceBottom: true,
      hasSourceSkip: false,
      hasTargetSkip: false,
    });
    expect(firstTask && 'handles' in firstTask.data ? firstTask.data.handles : null).toEqual({
      hasTargetTop: true,
      hasSourceBottom: true,
      hasSourceSkip: false,
      hasTargetSkip: false,
    });
    expect(lastTask && 'handles' in lastTask.data ? lastTask.data.handles : null).toEqual({
      hasTargetTop: true,
      hasSourceBottom: false,
      hasSourceSkip: false,
      hasTargetSkip: false,
    });
  });

  it('should mark skip edges as conditional', () => {
    const { edges } = templateToGraph(
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

    const skipEdge = edges.find((edge) => edge.id.includes('skip'));

    expect(skipEdge).toBeDefined();
    expect(skipEdge?.data?.isConditional).toBe(true);
    expect(skipEdge?.className).toBe('graph-edge--skip');
    expect(skipEdge?.style).toEqual(
      expect.objectContaining({
        stroke: 'var(--pneumatic-color-link)',
        strokeDasharray: '6 4',
      }),
    );
  });

  it('should insert fork and join nodes for a skippable task', () => {
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

    expect(nodes.some((node) => node.id === 'junction-fork-kickoff')).toBe(true);
    expect(nodes.some((node) => node.id === 'junction-join-task-2')).toBe(true);
    expect(edges.some((edge) => edge.source === 'kickoff' && edge.target === 'task-2')).toBe(false);
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
  });

  it('should map the showcase template to every edge variant', () => {
    const { nodes, edges } = templateToGraph(GRAPH_SHOWCASE_TEMPLATE);
    const skipEdges = edges.filter((edge) => edge.className === GRAPH_EDGE_CLASS_SKIP);
    const taskIds = nodes.filter((node) => node.type === EGraphNodeType.Task).map((node) => node.id);

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
    expect(nodes.some((node) => node.id === 'junction-fork-task-linear')).toBe(true);
    expect(nodes.some((node) => node.id === 'junction-join-task-url-title')).toBe(true);
    expect(nodes.some((node) => node.id === 'junction-fork-task-url-title')).toBe(true);
    expect(nodes.some((node) => node.id === 'junction-join-task-join')).toBe(true);
    expect(skipEdges.length).toBeGreaterThan(0);
    expect(skipEdges.every((edge) => edge.data?.isConditional)).toBe(true);
    expect(skipEdges.every((edge) => edge.style?.stroke === 'var(--pneumatic-color-link)')).toBe(true);
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
});
