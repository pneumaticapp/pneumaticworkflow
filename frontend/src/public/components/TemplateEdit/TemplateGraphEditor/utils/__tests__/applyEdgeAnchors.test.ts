import { ITemplateClient, ITemplateTaskClient } from '../../../../../types/template';
import { createEmptyTaskDueDate } from '../../../../../utils/dueDate/createEmptyTaskDueDate';
import { EConditionAction, EConditionLogicOperations, EConditionOperators } from '../../../TaskForm/Conditions';
import { EStartingType } from '../../../TaskForm/Conditions/utils/getDropdownOperators';
import { GRAPH_SHOWCASE_TEMPLATE } from '../../fixtures/graphShowcaseTemplate';
import { EGraphNodeType, TGraphEdge, TGraphNode } from '../../types';
import { buildTemplateGraph } from '../buildTemplateGraph';
import { isLaneRoutedGraphEdge, isSkipGraphEdge } from '../edgeStyles';
import { GRAPH_NODE_HEIGHT, GRAPH_NODE_WIDTH, getHandleAnchor } from '../graphGeometry';
import { applyEdgeAnchors } from '../applyEdgeAnchors';
import { applyMovedCard } from '../routeGraph';
import { getGraphEdgePath } from '../getGraphEdgePath';
import { classifyCardHit } from '../graphPathCollision';

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
      description: '',
      fields: [],
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

function layoutGraph(template: ITemplateClient) {
  return buildTemplateGraph(template);
}

describe('applyEdgeAnchors', () => {
  it('should leave a linear edge on the top and bottom handles', () => {
    const { edges } = layoutGraph(createTemplate());

    expect(edges).toHaveLength(1);
    expect(edges[0].sourceHandle).toBe('source-bottom');
    expect(edges[0].targetHandle).toBe('target-top');
    expect(edges[0].data?.pathKind).toBe('straight');
    expect(edges[0].data?.laneX).toBeUndefined();
  });

  it('should keep the longest fork child on the stem and send the other sideways', () => {
    const { nodes, edges } = layoutGraph(
      createTemplate({
        tasks: [
          createTask({ apiName: 'task-a', number: 1, uuid: 'uuid-a' }),
          createTask({ apiName: 'task-b', number: 2, uuid: 'uuid-b', ancestors: ['task-a'] }),
          createTask({ apiName: 'task-c', number: 3, uuid: 'uuid-c', ancestors: ['task-a'] }),
        ],
      }),
    );
    const forkEdges = edges.filter((edge) => edge.source === 'junction-fork-task-a');
    const intoB = forkEdges.find((edge) => edge.target === 'task-b');
    const intoC = forkEdges.find((edge) => edge.target === 'task-c');

    expect(forkEdges).toHaveLength(2);
    expect(intoB?.sourceHandle).toBe('source-bottom');
    expect(intoB?.targetHandle).toBe('target-top');
    expect(intoB?.data?.pathKind).toBe('straight');
    expect(intoC?.sourceHandle).toBe('source-left');
    expect(intoC?.targetHandle).toBe('target-top');
    expect(intoC?.data?.pathKind).toBe('from-fork');

    const taskA = nodes.find((node) => node.id === 'task-a');
    const taskB = nodes.find((node) => node.id === 'task-b');
    const taskC = nodes.find((node) => node.id === 'task-c');

    expect(taskA && taskB && taskA.position.x).toBe(taskB?.position.x);
    expect(taskC?.position.x).toBeLessThan(taskB?.position.x ?? 0);
  });

  it('should enter a join from the sides', () => {
    const { edges } = layoutGraph(
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

    const joinEdges = edges.filter((edge) => edge.target === 'junction-join-task-d');
    const fromB = joinEdges.find((edge) => edge.source === 'task-b');
    const fromC = joinEdges.find((edge) => edge.source === 'task-c');

    expect(joinEdges).toHaveLength(2);
    expect(fromB?.sourceHandle).toBe('source-bottom');
    expect(fromB?.targetHandle).toBe('target-top');
    expect(fromC?.sourceHandle).toBe('source-bottom');
    expect(fromC?.targetHandle).toBe('target-left');
    expect(joinEdges.every((edge) => edge.data?.pathKind === 'from-task' || edge.data?.pathKind === 'straight')).toBe(true);
  });

  it('should keep check-if conditions off the graph and on the stem handles', () => {
    const { edges } = layoutGraph(
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

    expect(edges.filter((edge) => isSkipGraphEdge(edge))).toHaveLength(0);
    expect(edges).toHaveLength(2);
    expect(edges.every((edge) => edge.sourceHandle === 'source-bottom')).toBe(true);
    expect(edges.every((edge) => edge.targetHandle === 'target-top')).toBe(true);
    expect(edges.every((edge) => edge.data?.pathKind === 'straight')).toBe(true);
    expect(edges.every((edge) => edge.data?.laneX === undefined)).toBe(true);
  });

  it('should keep showcase skippable tasks on the column instead of a side lane', () => {
    const { edges } = layoutGraph(GRAPH_SHOWCASE_TEMPLATE);

    expect(edges.filter((edge) => isSkipGraphEdge(edge))).toHaveLength(0);
    expect(edges.every((edge) => edge.data?.pathKind !== 'skip')).toBe(true);
    expect(edges.every((edge) => edge.data?.laneX === undefined)).toBe(true);
  });

  it('should not detour around a card that already stands between an ancestor and a descendant', () => {
    const { nodes, edges } = layoutGraph(
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
    const intoC = edges.filter((edge) => edge.target === 'task-c' || edge.target === 'junction-join-task-c');

    expect(edges.find((edge) => isLaneRoutedGraphEdge(edge))).toBeUndefined();
    expect(nodes.some((node) => node.id === 'junction-join-task-c')).toBe(false);
    expect(nodes.some((node) => node.id === 'junction-fork-task-a')).toBe(false);
    expect(intoC.some((edge) => edge.source === 'task-b')).toBe(true);
    expect(edges.some((edge) => edge.source === 'task-a' && (edge.target === 'task-c' || edge.target === 'junction-join-task-c'))).toBe(false);
  });

  it('should skip around a card that sits on a vertical stem', () => {
    const card = (id: string, x: number, y: number): TGraphNode => ({
      id,
      type: EGraphNodeType.Task,
      position: { x, y },
      width: GRAPH_NODE_WIDTH,
      height: GRAPH_NODE_HEIGHT,
      data: {},
    } as TGraphNode);
    const stem: TGraphEdge = {
      id: 'edge-a-c',
      source: 'task-a',
      target: 'task-c',
      sourceHandle: 'source-bottom',
      targetHandle: 'target-top',
      type: 'smoothstep',
      data: {},
    };
    const routed = applyEdgeAnchors(
      [card('task-a', 0, 0), card('blocker', 0, 140), card('task-c', 0, 300)],
      [stem],
    );

    expect(routed[0].data?.pathKind).toBe('skip');
    expect(typeof routed[0].data?.laneX).toBe('number');
  });

  it('should lift a side branch over a card instead of cutting through it', () => {
    const card = (id: string, x: number, y: number): TGraphNode => ({
      id,
      type: EGraphNodeType.Task,
      position: { x, y },
      width: GRAPH_NODE_WIDTH,
      height: GRAPH_NODE_HEIGHT,
      data: {},
    } as TGraphNode);
    const junction = (id: string, x: number, y: number, kind: 'fork' | 'join'): TGraphNode => ({
      id,
      type: EGraphNodeType.Junction,
      position: { x, y },
      width: 8,
      height: 8,
      data: { kind },
    });
    const fork = junction('fork', 148, 200, 'fork');
    const join = junction('join', 596, 280, 'join');
    const blocker = card('blocker', 280, 160);
    const routed = applyEdgeAnchors(
      [fork, join, blocker],
      [{
        id: 'edge-fork-join',
        source: 'fork',
        target: 'join',
        sourceHandle: 'source-right',
        targetHandle: 'target-top',
        type: 'smoothstep',
        data: {},
      }],
    );

    expect(routed[0].data?.pathKind).toBe('from-fork');
    expect(typeof routed[0].data?.laneX).toBe('number');
    expect(classifyCardHit(routed[0], fork, join, [fork, join, blocker])).toBeNull();

    const gutter = routed[0].data?.laneX ?? 0;
    const forkX = fork.position.x + 4;
    expect(gutter).toBeGreaterThan(forkX);
    expect(gutter).toBeLessThan(blocker.position.x);
    expect(routed[0].data?.laneY == null || routed[0].data.laneY < blocker.position.y).toBe(true);

    const from = routed[0].data?.sourceAnchor;
    const to = routed[0].data?.targetAnchor;
    const { path } = getGraphEdgePath({
      sourceX: from!.x,
      sourceY: from!.y,
      targetX: to!.x,
      targetY: to!.y,
      pathKind: routed[0].data?.pathKind,
      laneX: routed[0].data?.laneX,
      laneY: routed[0].data?.laneY,
      sourceHandle: routed[0].sourceHandle,
      targetHandle: routed[0].targetHandle,
    });
    expect(path).toContain(`L ${gutter},${from!.y}`);
    expect(path).not.toMatch(new RegExp(`L ${forkX},`));
  });

  it('should keep a crowded side branch in the tree gutters, not around the whole graph', () => {
    const card = (id: string, x: number, y: number): TGraphNode => ({
      id,
      type: EGraphNodeType.Task,
      position: { x, y },
      width: GRAPH_NODE_WIDTH,
      height: GRAPH_NODE_HEIGHT,
      data: {},
    } as TGraphNode);
    const junction = (id: string, x: number, y: number, kind: 'fork' | 'join'): TGraphNode => ({
      id,
      type: EGraphNodeType.Junction,
      position: { x, y },
      width: 8,
      height: 8,
      data: { kind },
    });
    const fork = junction('fork', 592, 652, 'fork');
    const routed = applyEdgeAnchors(
      [
        fork,
        card('task-3', 444, 776),
        card('task-13', 888, 600),
        card('task-10', 888, 776),
        card('task-12', 1332, 776),
      ],
      [
        {
          id: 'to-side',
          source: 'fork',
          target: 'task-10',
          sourceHandle: 'source-right',
          targetHandle: 'target-top',
          type: 'smoothstep',
          data: {},
        },
        {
          id: 'to-far',
          source: 'fork',
          target: 'task-12',
          sourceHandle: 'source-right',
          targetHandle: 'target-top',
          type: 'smoothstep',
          data: {},
        },
      ],
    );
    const toSide = routed.find((edge) => edge.id === 'to-side');
    const toFar = routed.find((edge) => edge.id === 'to-far');

    expect(toSide?.data?.pathKind).toBe('from-fork');
    expect(toSide?.data?.isLaneRouted).toBeFalsy();
    expect(toSide?.data?.laneX == null || toSide.data.laneX > 0).toBe(true);
    expect(toFar?.data?.pathKind).toBe('from-fork');
    expect(toFar?.data?.laneY == null || toFar.data.laneY > 0).toBe(true);

    const farPath = getGraphEdgePath({
      sourceX: toFar!.data!.sourceAnchor!.x,
      sourceY: toFar!.data!.sourceAnchor!.y,
      targetX: toFar!.data!.targetAnchor!.x,
      targetY: toFar!.data!.targetAnchor!.y,
      pathKind: toFar?.data?.pathKind,
      laneX: toFar?.data?.laneX,
      laneY: toFar?.data?.laneY,
      sourceHandle: toFar?.sourceHandle,
      targetHandle: toFar?.targetHandle,
    }).path;

    expect(farPath).not.toMatch(/,-64/);
    expect(farPath).not.toMatch(/L -32,/);
  });

  it('should keep the nearer fork branch on the bottom when both children sit on one side', () => {
    const initial = layoutGraph(
      createTemplate({
        tasks: [
          createTask({ apiName: 'task-a', number: 1, uuid: 'uuid-a' }),
          createTask({ apiName: 'task-b', number: 2, uuid: 'uuid-b', ancestors: ['task-a'] }),
          createTask({ apiName: 'task-c', number: 3, uuid: 'uuid-c', ancestors: ['task-a'] }),
        ],
      }),
    );
    const fork = initial.nodes.find((node) => node.id === 'junction-fork-task-a');
    const taskB = initial.nodes.find((node) => node.id === 'task-b');
    const taskC = initial.nodes.find((node) => node.id === 'task-c');

    expect(fork).toBeDefined();
    expect(taskB).toBeDefined();
    expect(taskC).toBeDefined();

    const afterB = applyMovedCard(initial.nodes, initial.edges, {
      ...taskB!,
      position: { x: fork!.position.x + 40, y: taskB!.position.y },
    });
    const afterC = applyMovedCard(afterB.nodes, afterB.edges, {
      ...taskC!,
      position: { x: fork!.position.x + 360, y: taskC!.position.y },
    });
    const handles = afterC.edges
      .filter((edge) => edge.source === 'junction-fork-task-a')
      .map((edge) => edge.sourceHandle)
      .sort();

    expect(handles).toEqual(['source-bottom', 'source-right']);
  });

  it('should keep a slightly offset stacked fork child on the stem', () => {
    const initial = layoutGraph(
      createTemplate({
        tasks: [
          createTask({ apiName: 'task-a', number: 1, uuid: 'uuid-a' }),
          createTask({ apiName: 'task-b', number: 2, uuid: 'uuid-b', ancestors: ['task-a'] }),
          createTask({ apiName: 'task-c', number: 3, uuid: 'uuid-c', ancestors: ['task-a'] }),
        ],
      }),
    );
    const fork = initial.nodes.find((node) => node.id === 'junction-fork-task-a');
    const taskB = initial.nodes.find((node) => node.id === 'task-b');

    expect(fork).toBeDefined();
    expect(taskB).toBeDefined();

    const next = applyMovedCard(initial.nodes, initial.edges, {
      ...taskB!,
      position: { x: taskB!.position.x - 24, y: taskB!.position.y },
    });
    const intoB = next.edges.find((edge) => edge.source === 'junction-fork-task-a' && edge.target === 'task-b');
    const forkAnchor = getHandleAnchor(next.nodes.find((node) => node.id === 'junction-fork-task-a')!, 'source-bottom');

    expect(intoB?.sourceHandle).toBe('source-bottom');
    expect(intoB?.data?.sourceAnchor).toEqual(forkAnchor);
  });

  it('should enter a side-by-side successor from the facing side', () => {
    const initial = layoutGraph(
      createTemplate({
        tasks: [
          createTask({ apiName: 'task-1', number: 1, uuid: 'uuid-1' }),
          createTask({ apiName: 'task-2', number: 2, uuid: 'uuid-2' }),
        ],
      }),
    );
    const first = initial.nodes.find((node) => node.id === 'task-1');
    const second = initial.nodes.find((node) => node.id === 'task-2');

    expect(first).toBeDefined();
    expect(second).toBeDefined();

    const next = applyMovedCard(initial.nodes, initial.edges, {
      ...second!,
      position: { x: first!.position.x + 420, y: first!.position.y },
    });
    const edge = next.edges.find((item) => item.source === 'task-1' && item.target === 'task-2');

    expect(edge?.sourceHandle).toBe('source-right');
    expect(edge?.targetHandle).toBe('target-left');
    expect(edge?.data?.sourceAnchor).toEqual(getHandleAnchor(next.nodes.find((node) => node.id === 'task-1')!, 'source-right'));
    expect(edge?.data?.targetAnchor).toEqual(getHandleAnchor(next.nodes.find((node) => node.id === 'task-2')!, 'target-left'));
  });

  it('should drop an offset fork child onto the top handle', () => {
    const initial = layoutGraph(
      createTemplate({
        tasks: [
          createTask({ apiName: 'task-a', number: 1, uuid: 'uuid-a' }),
          createTask({ apiName: 'task-b', number: 2, uuid: 'uuid-b', ancestors: ['task-a'] }),
          createTask({ apiName: 'task-c', number: 3, uuid: 'uuid-c', ancestors: ['task-a'] }),
        ],
      }),
    );
    const fork = initial.nodes.find((node) => node.id === 'junction-fork-task-a');
    const taskC = initial.nodes.find((node) => node.id === 'task-c');

    expect(fork).toBeDefined();
    expect(taskC).toBeDefined();

    const next = applyMovedCard(initial.nodes, initial.edges, {
      ...taskC!,
      position: { x: fork!.position.x + 280, y: taskC!.position.y },
    });
    const intoC = next.edges.find((edge) => edge.target === 'task-c');
    const forkNode = next.nodes.find((node) => node.id === 'junction-fork-task-a');

    expect(intoC?.targetHandle).toBe('target-top');
    expect(intoC?.sourceHandle).not.toBe('source-bottom');
    expect(intoC?.data?.sourceAnchor).toEqual(getHandleAnchor(forkNode!, intoC?.sourceHandle));
    expect(intoC?.data?.targetAnchor).toEqual(getHandleAnchor(next.nodes.find((node) => node.id === 'task-c')!, 'target-top'));
  });

  it('should branch from the fork point even when the child card sits higher', () => {
    const initial = layoutGraph(
      createTemplate({
        tasks: [
          createTask({ apiName: 'task-a', number: 1, uuid: 'uuid-a' }),
          createTask({ apiName: 'task-b', number: 2, uuid: 'uuid-b', ancestors: ['task-a'] }),
          createTask({ apiName: 'task-c', number: 3, uuid: 'uuid-c', ancestors: ['task-a'] }),
        ],
      }),
    );
    const fork = initial.nodes.find((node) => node.id === 'junction-fork-task-a');
    const taskC = initial.nodes.find((node) => node.id === 'task-c');

    expect(fork).toBeDefined();
    expect(taskC).toBeDefined();

    const next = applyMovedCard(initial.nodes, initial.edges, {
      ...taskC!,
      position: { x: fork!.position.x + 280, y: fork!.position.y - 80 },
    });
    const intoC = next.edges.find((edge) => edge.target === 'task-c');
    const forkNode = next.nodes.find((node) => node.id === 'junction-fork-task-a')!;
    const forkAnchor = getHandleAnchor(forkNode, intoC?.sourceHandle);
    const cardAnchor = getHandleAnchor(next.nodes.find((node) => node.id === 'task-c')!, intoC?.targetHandle);
    const { path } = getGraphEdgePath({
      sourceX: forkAnchor.x,
      sourceY: forkAnchor.y,
      targetX: cardAnchor.x,
      targetY: cardAnchor.y,
      pathKind: intoC?.data?.pathKind,
      sourceHandle: intoC?.sourceHandle,
      targetHandle: intoC?.targetHandle,
    });

    expect(intoC?.data?.pathKind).toBe('from-fork');
    expect(path).toContain(`M ${forkAnchor.x},${forkAnchor.y} L ${cardAnchor.x},${forkAnchor.y}`);
  });

  it('should leave the fork below a card at the fork centre, not at the child top', () => {
    const { nodes, edges } = layoutGraph(
      createTemplate({
        tasks: [
          createTask({ apiName: 'task-2', number: 2, uuid: 'uuid-2' }),
          createTask({ apiName: 'task-3', number: 3, uuid: 'uuid-3', ancestors: ['task-2'] }),
          createTask({ apiName: 'task-4', number: 4, uuid: 'uuid-4', ancestors: ['task-3'] }),
          createTask({ apiName: 'task-5', number: 5, uuid: 'uuid-5', ancestors: ['task-2'] }),
          createTask({
            apiName: 'task-6',
            number: 6,
            uuid: 'uuid-6',
            ancestors: ['task-3', 'task-5'],
          }),
        ],
      }),
    );
    const fork = nodes.find((node) => node.id === 'junction-fork-task-3');
    const join = nodes.find((node) => node.id === 'junction-join-task-6');
    const side = edges.find((edge) => edge.source === 'junction-fork-task-3' && edge.target === 'junction-join-task-6');
    const forkAnchor = getHandleAnchor(fork!, side?.sourceHandle);

    expect(fork).toBeDefined();
    expect(join).toBeDefined();
    expect(side?.data?.pathKind).toBe('from-fork');
    expect(side?.data?.sourceAnchor).toEqual(forkAnchor);
    expect(getGraphEdgePath({
      sourceX: side!.data!.sourceAnchor!.x,
      sourceY: side!.data!.sourceAnchor!.y,
      targetX: side!.data!.targetAnchor!.x,
      targetY: side!.data!.targetAnchor!.y,
      pathKind: side?.data?.pathKind,
      laneX: side?.data?.laneX,
      sourceHandle: side?.data?.sourceHandle ?? side?.sourceHandle,
      targetHandle: side?.data?.targetHandle ?? side?.targetHandle,
    }).path.startsWith(
      `M ${forkAnchor.x},${forkAnchor.y} L ${side!.data!.targetAnchor!.x},${forkAnchor.y}`,
    )).toBe(true);
  });
});
