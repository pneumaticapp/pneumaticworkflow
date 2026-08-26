import { EExtraFieldType, ITemplateClient, ITemplateTaskClient } from '../../../../../types/template';
import { createEmptyTaskDueDate } from '../../../../../utils/dueDate/createEmptyTaskDueDate';
import { EConditionAction, EConditionLogicOperations, EConditionOperators } from '../../../TaskForm/Conditions';
import { EStartingType } from '../../../TaskForm/Conditions/utils/getDropdownOperators';
import { GRAPH_SHOWCASE_TEMPLATE } from '../../fixtures/graphShowcaseTemplate';
import { GRAPH_WEAVE_TEMPLATE } from '../../fixtures/graphWeaveTemplate';
import { EGraphNodeType, TGraphEdge, TGraphNode } from '../../types';
import { buildTemplateGraph } from '../buildTemplateGraph';
import { getGraphEdgeLine, isLaneRoutedGraphEdge } from '../edgeStyles';
import { getGraphEdgePath } from '../getGraphEdgePath';
import { GRAPH_EDGE_STANDOFF, getGraphNodeBox, getHandleAnchor } from '../graphGeometry';

interface IPoint {
  x: number;
  y: number;
}

interface ISegment {
  edgeId: string;
  a: IPoint;
  b: IPoint;
}

function createTask(overrides: Partial<ITemplateTaskClient> = {}): ITemplateTaskClient {
  return {
    apiName: 'task-1',
    name: 'Task',
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

function createCondition(apiName: string, action: EConditionAction) {
  return {
    apiName,
    order: 1,
    action,
    rules: [
      {
        ruleApiName: `${apiName}-rule`,
        predicateApiName: `${apiName}-predicate`,
        field: 'field-1',
        operator: EConditionOperators.Exist,
        logicOperation: EConditionLogicOperations.And,
      },
    ],
  };
}

function createSkipCondition(apiName: string) {
  return createCondition(apiName, EConditionAction.SkipTask);
}

function createStartCondition(apiName: string) {
  return createCondition(apiName, EConditionAction.StartTask);
}

function createTemplate(tasks: ITemplateTaskClient[]): ITemplateClient {
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
    kickoff: { description: '', fields: [], fieldsets: [] },
    tasks,
    isPublic: false,
    publicUrl: null,
    publicSuccessUrl: null,
    isEmbedded: false,
    embedUrl: null,
    wfNameTemplate: null,
    tasksCount: tasks.length,
    performersCount: 0,
  };
}

function getHandlePoint(node: TGraphNode, handleId?: string | null): IPoint {
  return getHandleAnchor(node, handleId);
}

function parseSegments(edgeId: string, path: string): ISegment[] {
  const tokens = path.match(/[MLQ][^MLQ]*/g) ?? [];
  const segments: ISegment[] = [];
  let cursor: IPoint = { x: 0, y: 0 };

  tokens.forEach((token) => {
    const command = token[0];
    const numbers = (token.slice(1).match(/-?\d+(\.\d+)?/g) ?? []).map(Number);

    if (command === 'M') {
      cursor = { x: numbers[0], y: numbers[1] };

      return;
    }

    if (command === 'L') {
      const next = { x: numbers[0], y: numbers[1] };
      segments.push({ edgeId, a: cursor, b: next });
      cursor = next;

      return;
    }

    cursor = { x: numbers[2], y: numbers[3] };
  });

  return segments;
}

function collectSegments(nodes: TGraphNode[], edges: TGraphEdge[]): ISegment[] {
  const nodeById = new Map(nodes.map((node) => [node.id, node]));

  return edges.flatMap((edge) => {
    const source = nodeById.get(edge.source);
    const target = nodeById.get(edge.target);

    if (!source || !target) {
      return [];
    }

    const from = getHandlePoint(source, edge.sourceHandle);
    const to = getHandlePoint(target, edge.targetHandle);
    const { path } = getGraphEdgePath({
      sourceX: from.x,
      sourceY: from.y,
      targetX: to.x,
      targetY: to.y,
      pathKind: edge.data?.pathKind,
      laneX: edge.data?.laneX,
      laneY: edge.data?.laneY,
      sourceHandle: edge.sourceHandle,
      targetHandle: edge.targetHandle,
      sourceStandoff: edge.data?.sourceStandoff,
      targetStandoff: edge.data?.targetStandoff,
    });

    return parseSegments(edge.id, path);
  });
}

/** A segment touching a card border is fine, so the box is shrunk before the check. */
const CARD_HIT_INSET = 2;

function crossesCard(segment: ISegment, card: TGraphNode): boolean {
  const box = getGraphNodeBox(card);
  const minX = Math.min(segment.a.x, segment.b.x);
  const maxX = Math.max(segment.a.x, segment.b.x);
  const minY = Math.min(segment.a.y, segment.b.y);
  const maxY = Math.max(segment.a.y, segment.b.y);

  return (
    maxX > box.x + CARD_HIT_INSET
    && minX < box.right - CARD_HIT_INSET
    && maxY > box.y + CARD_HIT_INSET
    && minY < box.bottom - CARD_HIT_INSET
  );
}

function findCardCrossings(nodes: TGraphNode[], edges: TGraphEdge[]): string[] {
  const cards = nodes.filter((node) => node.type !== EGraphNodeType.Junction);

  return collectSegments(nodes, edges).flatMap((segment) => cards
    .filter((card) => crossesCard(segment, card))
    .map((card) => `${segment.edgeId} over ${card.id}`));
}

function findEdgeGlances(nodes: TGraphNode[], edges: TGraphEdge[]): string[] {
  const cards = nodes.filter((node) => node.type !== EGraphNodeType.Junction);

  return collectSegments(nodes, edges).flatMap((segment) => {
    const isVertical = Math.abs(segment.a.x - segment.b.x) < 0.5;

    if (!isVertical) {
      return [];
    }

    const minY = Math.min(segment.a.y, segment.b.y);
    const maxY = Math.max(segment.a.y, segment.b.y);

    return cards
      .filter((card) => {
        const box = getGraphNodeBox(card);
        const onSide = Math.abs(segment.a.x - box.x) < 0.5 || Math.abs(segment.a.x - box.right) < 0.5;
        const overlap = getOverlapLength(minY, maxY, box.y, box.bottom);

        return onSide && overlap > 2;
      })
      .map((card) => `${segment.edgeId} along ${card.id}`);
  });
}

function hasCheckIfInfo(edge: TGraphEdge): boolean {
  return Boolean(edge.data?.isConditional);
}

function getOverlapLength(a1: number, a2: number, b1: number, b2: number): number {
  const start = Math.max(Math.min(a1, a2), Math.min(b1, b2));
  const end = Math.min(Math.max(a1, a2), Math.max(b1, b2));

  return end - start;
}

function findOverlaps(segments: ISegment[]): string[] {
  const overlaps: string[] = [];

  segments.forEach((first, index) => {
    segments.slice(index + 1).forEach((second) => {
      if (first.edgeId === second.edgeId) return;

      const isFirstVertical = Math.abs(first.a.x - first.b.x) < 0.5;
      const isSecondVertical = Math.abs(second.a.x - second.b.x) < 0.5;
      const isFirstHorizontal = Math.abs(first.a.y - first.b.y) < 0.5;
      const isSecondHorizontal = Math.abs(second.a.y - second.b.y) < 0.5;

      if (isFirstVertical && isSecondVertical && Math.abs(first.a.x - second.a.x) < 0.5) {
        if (getOverlapLength(first.a.y, first.b.y, second.a.y, second.b.y) > GRAPH_EDGE_STANDOFF) {
          overlaps.push(`${first.edgeId} | ${second.edgeId}`);
        }
      }

      if (isFirstHorizontal && isSecondHorizontal && Math.abs(first.a.y - second.a.y) < 0.5) {
        if (getOverlapLength(first.a.x, first.b.x, second.a.x, second.b.x) > 1) {
          overlaps.push(`${first.edgeId} | ${second.edgeId}`);
        }
      }
    });
  });

  return overlaps;
}

const MULTI_SKIP_TEMPLATE = createTemplate([
  createTask({ apiName: 'task-a', number: 1, uuid: 'a', conditions: [createSkipCondition('skip-a')] }),
  createTask({ apiName: 'task-b', number: 2, uuid: 'b', conditions: [createSkipCondition('skip-b')] }),
  createTask({ apiName: 'task-c', number: 3, uuid: 'c' }),
  createTask({ apiName: 'task-d', number: 4, uuid: 'd' }),
]);

const MIXED_FORK_TEMPLATE = createTemplate([
  createTask({ apiName: 'task-a', number: 1, uuid: 'a' }),
  createTask({ apiName: 'task-b', number: 2, uuid: 'b', ancestors: ['task-a'] }),
  createTask({
    apiName: 'task-c',
    number: 3,
    uuid: 'c',
    ancestors: ['task-a'],
    conditions: [createStartCondition('start-c')],
  }),
  createTask({ apiName: 'task-d', number: 4, uuid: 'd', ancestors: ['task-b', 'task-c'] }),
]);

const UNEVEN_BRANCH_TEMPLATE = createTemplate([
  createTask({ apiName: 'task-a', number: 1, uuid: 'a' }),
  createTask({ apiName: 'task-b1', number: 2, uuid: 'b1', ancestors: ['task-a'] }),
  createTask({ apiName: 'task-b2', number: 3, uuid: 'b2', ancestors: ['task-b1'] }),
  createTask({ apiName: 'task-c', number: 4, uuid: 'c', ancestors: ['task-a'] }),
  createTask({ apiName: 'task-d', number: 5, uuid: 'd', ancestors: ['task-b2', 'task-c'] }),
]);

const JOIN_TWO_PREVIOUS_TEMPLATE = createTemplate([
  createTask({ apiName: 'task-a', number: 1, uuid: 'a' }),
  createTask({ apiName: 'task-b', number: 2, uuid: 'b', ancestors: ['task-a'] }),
  createTask({
    apiName: 'task-c',
    number: 3,
    uuid: 'c',
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
]);

const CROSS_CHECK_IF_TEMPLATE = createTemplate([
  createTask({ apiName: 'task-a', number: 1, uuid: 'a', ancestors: ['kickoff'] }),
  createTask({
    apiName: 'task-side',
    number: 2,
    uuid: 'side',
    ancestors: ['kickoff'],
    fields: [
      {
        apiName: 'side-field',
        name: 'Flag',
        type: EExtraFieldType.String,
        order: 0,
        userId: null,
        groupId: null,
      },
    ],
  }),
  createTask({ apiName: 'task-b', number: 3, uuid: 'b', ancestors: ['task-a'] }),
  createTask({
    apiName: 'task-c',
    number: 4,
    uuid: 'c',
    ancestors: ['task-b'],
    conditions: [
      {
        apiName: 'skip-c',
        order: 1,
        action: EConditionAction.SkipTask,
        rules: [
          {
            ruleApiName: 'skip-c-rule',
            predicateApiName: 'skip-c-predicate',
            field: 'side-field',
            operator: EConditionOperators.Exist,
            logicOperation: EConditionLogicOperations.And,
          },
        ],
      },
    ],
  }),
]);

describe.each([
  ['showcase', GRAPH_SHOWCASE_TEMPLATE],
  ['weave check-if', GRAPH_WEAVE_TEMPLATE],
  ['consecutive skips', MULTI_SKIP_TEMPLATE],
  ['mixed fork', MIXED_FORK_TEMPLATE],
  ['uneven branches', UNEVEN_BRANCH_TEMPLATE],
  ['join two previous', JOIN_TWO_PREVIOUS_TEMPLATE],
  ['cross-column check-if', CROSS_CHECK_IF_TEMPLATE],
])('graph edge layout: %s', (_name, template) => {
  const { nodes, edges } = buildTemplateGraph(template);
  const cardNodes = nodes.filter((node) => node.type !== EGraphNodeType.Junction);
  const stemEdges = edges.filter((edge) => !isLaneRoutedGraphEdge(edge) && !edge.data?.isConditional);

  it('should keep a single incoming and a single outgoing stem on every card', () => {
    cardNodes.forEach((node) => {
      expect(stemEdges.filter((edge) => edge.target === node.id).length).toBeLessThanOrEqual(1);
      expect(stemEdges.filter((edge) => edge.source === node.id).length).toBeLessThanOrEqual(1);
    });
  });

  it('should branch stems only on junction nodes', () => {
    const branching = nodes.filter(
      (node) => stemEdges.filter((edge) => edge.source === node.id).length > 1
        || stemEdges.filter((edge) => edge.target === node.id).length > 1,
    );

    expect(branching.every((node) => node.type === EGraphNodeType.Junction)).toBe(true);
  });

  it('should keep gray and check-if off the same junction', () => {
    const joins = nodes.filter((node) => node.type === EGraphNodeType.Junction && 'kind' in node.data && node.data.kind === 'join');

    joins.forEach((join) => {
      const outbound = edges.filter((edge) => edge.source === join.id);
      const inbound = edges.filter((edge) => edge.target === join.id);
      const hasGrayIn = inbound.some((edge) => !edge.data?.isConditional);
      const hasOrangeIn = inbound.some((edge) => edge.data?.isConditional);

      expect(outbound).toHaveLength(1);
      expect(hasGrayIn && hasOrangeIn).toBe(false);

      if (hasGrayIn) {
        expect(getGraphEdgeLine(outbound[0])).toBe('solid');
      }

      if (hasOrangeIn) {
        expect(getGraphEdgeLine(outbound[0])).toBe('dashed');
      }
    });
  });

  it('should keep start-after lines gray and check-if lines dashed', () => {
    const startAfter = edges.filter((edge) => !edge.data?.isConditional);
    const checkIf = edges.filter((edge) => edge.data?.isConditional);

    expect(startAfter.every((edge) => getGraphEdgeLine(edge) === 'solid')).toBe(true);
    expect(checkIf.every((edge) => getGraphEdgeLine(edge) === 'dashed')).toBe(true);
  });

  it('should never put two edges on the same handle', () => {
    const anchors = new Map<string, number>();

    edges.forEach((edge) => {
      const outKey = `${edge.source}|${edge.sourceHandle}`;
      const inKey = `${edge.target}|${edge.targetHandle}`;
      anchors.set(outKey, (anchors.get(outKey) ?? 0) + 1);
      anchors.set(inKey, (anchors.get(inKey) ?? 0) + 1);
    });

    expect([...anchors.values()].every((count) => count === 1)).toBe(true);
  });

  it('should dock gray lines on the top and bottom of cards and check-if on the sides', () => {
    const cardIds = new Set(cardNodes.map((node) => node.id));
    const isVertical = (handle?: string | null) => Boolean(handle && (handle.includes('top') || handle.includes('bottom')));
    const isHorizontal = (handle?: string | null) => Boolean(handle && (handle.includes('left') || handle.includes('right')));

    edges.forEach((edge) => {
      if (cardIds.has(edge.source)) {
        if (edge.data?.isConditional) {
          expect(isHorizontal(edge.sourceHandle)).toBe(true);
        } else {
          expect(isVertical(edge.sourceHandle)).toBe(true);
        }
      }

      if (cardIds.has(edge.target)) {
        if (edge.data?.isConditional) {
          expect(isHorizontal(edge.targetHandle)).toBe(true);
        } else {
          expect(isVertical(edge.targetHandle)).toBe(true);
        }
      }
    });
  });

  it('should leave and enter cards with a standoff before turning', () => {
    const cardIds = new Set(cardNodes.map((node) => node.id));
    const isHorizontal = (handle?: string | null) => Boolean(
      handle && (handle.includes('left') || handle.includes('right')),
    );
    const byEdge = new Map<string, ISegment[]>();

    collectSegments(nodes, edges).forEach((segment) => {
      const list = byEdge.get(segment.edgeId) ?? [];
      list.push(segment);
      byEdge.set(segment.edgeId, list);
    });

    edges.forEach((edge) => {
      const segments = byEdge.get(edge.id);

      if (!segments || segments.length === 0) {
        return;
      }

      if (cardIds.has(edge.source) && isHorizontal(edge.sourceHandle)) {
        const first = segments[0];
        const run = Math.hypot(first.b.x - first.a.x, first.b.y - first.a.y);

        expect(run).toBeGreaterThanOrEqual(GRAPH_EDGE_STANDOFF);
        expect(Math.abs(first.a.y - first.b.y)).toBeLessThan(0.5);
      }

      if (cardIds.has(edge.target) && isHorizontal(edge.targetHandle)) {
        const last = segments[segments.length - 1];
        const run = Math.hypot(last.b.x - last.a.x, last.b.y - last.a.y);

        expect(run).toBeGreaterThanOrEqual(GRAPH_EDGE_STANDOFF);
        expect(Math.abs(last.a.y - last.b.y)).toBeLessThan(0.5);
      }
    });
  });

  it('should not run a vertical along a card side', () => {
    expect(findEdgeGlances(nodes, edges)).toEqual([]);
  });

  it('should not let two edges run along the same line', () => {
    expect(findOverlaps(collectSegments(nodes, edges))).toEqual([]);
  });

  it('should never run a line across a card', () => {
    expect(findCardCrossings(nodes, edges)).toEqual([]);
  });

  it('should keep every segment horizontal or vertical', () => {
    const diagonals = collectSegments(nodes, edges).filter((segment) => (
      Math.abs(segment.a.x - segment.b.x) > 0.5
      && Math.abs(segment.a.y - segment.b.y) > 0.5
    ));

    expect(diagonals).toEqual([]);
  });

  it('should describe check-if lines and keep start-after on the first gray segment', () => {
    const cardIds = new Set(cardNodes.map((node) => node.id));
    const outboundStartAfter = edges.filter((edge) => cardIds.has(edge.source) && !edge.data?.isConditional);
    const outboundCheckIf = edges.filter((edge) => cardIds.has(edge.source) && edge.data?.isConditional);

    expect(outboundStartAfter.every((edge) => !hasCheckIfInfo(edge))).toBe(true);
    expect(outboundStartAfter.every((edge) => Boolean(edge.data?.startAfter?.length))).toBe(true);
    expect(outboundCheckIf.every((edge) => hasCheckIfInfo(edge))).toBe(true);
  });

  it('should not repeat the description on segments after a junction', () => {
    const junctionIds = new Set(
      nodes.filter((node) => node.type === EGraphNodeType.Junction).map((node) => node.id),
    );
    const outbound = edges.filter((edge) => junctionIds.has(edge.source));
    const solidOutbound = outbound.filter((edge) => getGraphEdgeLine(edge) === 'solid');

    expect(solidOutbound.every((edge) => !hasCheckIfInfo(edge))).toBe(true);
    expect(solidOutbound.every((edge) => !edge.data?.startAfter?.length)).toBe(true);
  });
});
