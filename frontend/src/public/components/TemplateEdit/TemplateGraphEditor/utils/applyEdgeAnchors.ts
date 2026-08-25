import { TGraphEdge, TGraphEdgePathKind, TGraphNode } from '../types';
import { isLaneRoutedGraphEdge } from './edgeStyles';
import { markDetourEdges, pickDetourSide } from './applyEdgeDetours';
import { assignEdgeHandles } from './assignEdgeHandles';
import { planObstacleDetours } from './graphPathCollision';
import {
  GRAPH_EDGE_SIDEWAYS_THRESHOLD,
  GRAPH_SKIP_LANE_GAP,
  GRAPH_SKIP_LANE_STEP,
  TGraphLaneSide,
  faceFromHandle,
  getGraphNodeBox,
  getHandleAnchor,
  getJunctionKind,
} from './graphGeometry';

interface IVerticalSpan {
  top: number;
  bottom: number;
}

function getEdgeSpan(source: TGraphNode, target: TGraphNode): IVerticalSpan {
  const sourceBox = getGraphNodeBox(source);
  const targetBox = getGraphNodeBox(target);

  return {
    top: Math.min(sourceBox.y, targetBox.y),
    bottom: Math.max(sourceBox.bottom, targetBox.bottom),
  };
}

function spansOverlap(first: IVerticalSpan, second: IVerticalSpan): boolean {
  return first.bottom > second.top && second.bottom > first.top;
}

function getLaneStartX(nodes: TGraphNode[], span: IVerticalSpan, side: TGraphLaneSide): number {
  const start = nodes.reduce((edge, node) => {
    const box = getGraphNodeBox(node);
    const overlapsSpan = box.bottom > span.top && box.y < span.bottom;

    if (!overlapsSpan) {
      return edge;
    }

    return side === 'right' ? Math.max(edge, box.right) : Math.min(edge, box.x);
  }, side === 'right' ? 0 : Number.POSITIVE_INFINITY);

  return side === 'right' ? start + GRAPH_SKIP_LANE_GAP : start - GRAPH_SKIP_LANE_GAP;
}

interface ITakenLane {
  span: IVerticalSpan;
  laneX: number;
}

function isLaneTaken(laneX: number, span: IVerticalSpan, taken: ITakenLane[]): boolean {
  return taken.some(
    (item) => spansOverlap(item.span, span) && Math.abs(item.laneX - laneX) < GRAPH_SKIP_LANE_STEP,
  );
}

function findFreeLane(startX: number, span: IVerticalSpan, taken: ITakenLane[], side: TGraphLaneSide): number {
  const step = side === 'right' ? GRAPH_SKIP_LANE_STEP : -GRAPH_SKIP_LANE_STEP;
  let laneX = startX;

  while (isLaneTaken(laneX, span, taken)) {
    laneX += step;
  }

  return laneX;
}

function assignSideLanes(nodes: TGraphNode[], edges: TGraphEdge[]): Map<string, number> {
  const nodeById = new Map(nodes.map((node) => [node.id, node]));
  const laneEdges = edges
    .filter((edge) => isLaneRoutedGraphEdge(edge) && nodeById.has(edge.source) && nodeById.has(edge.target))
    .map((edge) => ({
      edge,
      span: getEdgeSpan(nodeById.get(edge.source)!, nodeById.get(edge.target)!),
      side: (edge.data?.laneSide === 'left' ? 'left' : 'right') as TGraphLaneSide,
    }))
    .sort((first, second) => first.span.top - second.span.top || first.edge.id.localeCompare(second.edge.id));

  const lanes = new Map<string, number>();
  const taken: ITakenLane[] = [];

  laneEdges.forEach(({ edge, span, side }) => {
    const laneX = findFreeLane(getLaneStartX(nodes, span, side), span, taken, side);

    lanes.set(edge.id, laneX);
    taken.push({ span, laneX });
  });

  return lanes;
}

function withPathKind(edge: TGraphEdge, pathKind: TGraphEdgePathKind, extras?: Partial<TGraphEdge>): TGraphEdge {
  return {
    ...edge,
    ...extras,
    data: {
      ...edge.data,
      ...extras?.data,
      pathKind,
    },
  };
}

function pathKindForHandles(
  source: TGraphNode,
  sourceHandle: string,
  targetHandle: string,
  isDetour: boolean,
  deltaX: number,
): TGraphEdgePathKind {
  if (isDetour) {
    return 'skip';
  }

  if (getJunctionKind(source) && Math.abs(deltaX) > GRAPH_EDGE_SIDEWAYS_THRESHOLD) {
    return 'from-fork';
  }

  const sourceFace = faceFromHandle(sourceHandle);
  const targetFace = faceFromHandle(targetHandle);

  if (sourceFace === 'bottom' && targetFace === 'top') {
    return Math.abs(deltaX) <= GRAPH_EDGE_SIDEWAYS_THRESHOLD ? 'straight' : 'from-task';
  }

  return 'from-task';
}

function routePass(nodes: TGraphNode[], edges: TGraphEdge[]): TGraphEdge[] {
  const nodeById = new Map(nodes.map((node) => [node.id, node]));
  const sideLanes = assignSideLanes(nodes, edges);
  const handles = assignEdgeHandles(nodes, edges);

  return edges.map((edge) => {
    const source = nodeById.get(edge.source);
    const target = nodeById.get(edge.target);
    const assigned = handles.get(edge.id);

    if (!source || !target || !assigned) {
      return edge;
    }

    const isDetour = isLaneRoutedGraphEdge(edge);
    const deltaX = getGraphNodeBox(target).centerX - getGraphNodeBox(source).centerX;
    const kind = pathKindForHandles(
      source,
      assigned.sourceHandle,
      assigned.targetHandle,
      isDetour,
      deltaX,
    );

    return withPathKind(edge, kind, {
      sourceHandle: assigned.sourceHandle,
      targetHandle: assigned.targetHandle,
      data: {
        ...edge.data,
        laneX: isDetour ? sideLanes.get(edge.id) : undefined,
        laneY: undefined,
        sourceAnchor: getHandleAnchor(source, assigned.sourceHandle),
        targetAnchor: getHandleAnchor(target, assigned.targetHandle),
        sourceHandle: assigned.sourceHandle,
        targetHandle: assigned.targetHandle,
      },
    });
  });
}

function withVerticalDetours(
  nodes: TGraphNode[],
  edges: TGraphEdge[],
  xIds: Set<string>,
): TGraphEdge[] {
  const nodeById = new Map(nodes.map((node) => [node.id, node]));

  return edges.map((edge) => {
    if (!xIds.has(edge.id) || isLaneRoutedGraphEdge(edge)) {
      return edge;
    }

    const source = nodeById.get(edge.source);
    const target = nodeById.get(edge.target);

    if (!source || !target) {
      return edge;
    }

    return {
      ...edge,
      data: {
        ...edge.data,
        isLaneRouted: true,
        laneSide: pickDetourSide(source, target, nodes),
      },
    };
  });
}

function withGutterDetours(
  edges: TGraphEdge[],
  gutters: Map<string, { laneX: number; laneY?: number }>,
): TGraphEdge[] {
  return edges.map((edge) => {
    const detour = gutters.get(edge.id);

    if (!detour) {
      return edge;
    }

    return {
      ...edge,
      data: {
        ...edge.data,
        laneX: detour.laneX,
        laneY: detour.laneY,
        isLaneRouted: undefined,
        laneSide: undefined,
        pathKind: edge.data?.pathKind === 'skip' ? 'from-fork' : edge.data?.pathKind,
      },
    };
  });
}

export function applyEdgeAnchors(nodes: TGraphNode[], edges: TGraphEdge[]): TGraphEdge[] {
  let routed = markDetourEdges(nodes, edges);
  let laid = routePass(nodes, routed);
  const firstPlan = planObstacleDetours(nodes, laid);

  if (firstPlan.xIds.size > 0) {
    routed = withVerticalDetours(nodes, routed, firstPlan.xIds);
    laid = routePass(nodes, routed);
  }

  const gutterPlan = planObstacleDetours(nodes, laid);

  if (gutterPlan.gutters.size > 0) {
    laid = withGutterDetours(laid, gutterPlan.gutters);
  }

  return laid;
}
