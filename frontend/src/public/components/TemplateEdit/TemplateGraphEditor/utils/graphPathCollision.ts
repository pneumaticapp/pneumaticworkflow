import { TGraphEdge, TGraphNode } from '../types';
import { getGraphEdgePath } from './getGraphEdgePath';
import {
  GRAPH_ROW_GAP,
  GRAPH_SKIP_LANE_GAP,
  GRAPH_SKIP_LANE_STEP,
  getGraphNodeBox,
  getHandleAnchor,
  isCardNode,
  sharesStemX,
} from './graphGeometry';

export const CARD_HIT_INSET = 2;

export interface IPathPoint {
  x: number;
  y: number;
}

export interface IPathSegment {
  a: IPathPoint;
  b: IPathPoint;
}

export interface IGutterDetour {
  laneX: number;
  laneY?: number;
}

export function parseGraphPath(path: string): IPathSegment[] {
  const tokens = path.match(/[MLQ][^MLQ]*/g) ?? [];
  const segments: IPathSegment[] = [];
  let cursor: IPathPoint = { x: 0, y: 0 };

  tokens.forEach((token) => {
    const command = token[0];
    const numbers = (token.slice(1).match(/-?\d+(\.\d+)?/g) ?? []).map(Number);

    if (command === 'M') {
      cursor = { x: numbers[0], y: numbers[1] };

      return;
    }

    if (command === 'L') {
      const next = { x: numbers[0], y: numbers[1] };
      segments.push({ a: cursor, b: next });
      cursor = next;
    }
  });

  return segments;
}

export function isVerticalSegment(segment: IPathSegment): boolean {
  return Math.abs(segment.a.x - segment.b.x) < 0.5;
}

export function isHorizontalSegment(segment: IPathSegment): boolean {
  return Math.abs(segment.a.y - segment.b.y) < 0.5;
}

export function segmentHitsCard(segment: IPathSegment, card: TGraphNode): boolean {
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

export function segmentCrowdsCard(segment: IPathSegment, card: TGraphNode): boolean {
  const box = getGraphNodeBox(card);
  const pad = GRAPH_SKIP_LANE_GAP;
  const minX = Math.min(segment.a.x, segment.b.x);
  const maxX = Math.max(segment.a.x, segment.b.x);
  const minY = Math.min(segment.a.y, segment.b.y);
  const maxY = Math.max(segment.a.y, segment.b.y);

  return (
    maxX > box.x - pad
    && minX < box.right + pad
    && maxY > box.y - pad
    && minY < box.bottom + pad
  );
}

export function getEdgePathSegments(
  edge: TGraphEdge,
  source: TGraphNode,
  target: TGraphNode,
): IPathSegment[] {
  const from = edge.data?.sourceAnchor ?? getHandleAnchor(source, edge.sourceHandle);
  const to = edge.data?.targetAnchor ?? getHandleAnchor(target, edge.targetHandle);
  const { path } = getGraphEdgePath({
    sourceX: from.x,
    sourceY: from.y,
    targetX: to.x,
    targetY: to.y,
    pathKind: edge.data?.pathKind,
    laneX: edge.data?.laneX,
    laneY: edge.data?.laneY,
    sourceHandle: edge.data?.sourceHandle ?? edge.sourceHandle,
    targetHandle: edge.data?.targetHandle ?? edge.targetHandle,
  });

  return parseGraphPath(path);
}

function foreignCards(nodes: TGraphNode[], sourceId: string, targetId: string): TGraphNode[] {
  return nodes.filter((node) => isCardNode(node) && node.id !== sourceId && node.id !== targetId);
}

export function classifyCardHit(
  edge: TGraphEdge,
  source: TGraphNode,
  target: TGraphNode,
  nodes: TGraphNode[],
): 'vertical' | 'horizontal' | null {
  const cards = foreignCards(nodes, source.id, target.id);
  const segments = getEdgePathSegments(edge, source, target);
  const hits = segments.filter((segment) => cards.some((card) => segmentHitsCard(segment, card)));

  if (hits.length === 0) {
    return null;
  }

  if (hits.some(isVerticalSegment) && !edge.data?.isLaneRouted) {
    if (sharesStemX(getGraphNodeBox(source), getGraphNodeBox(target))) {
      return 'vertical';
    }

    return 'horizontal';
  }

  if (hits.some(isHorizontalSegment)) {
    return 'horizontal';
  }

  return 'vertical';
}

function withGutterPath(
  edge: TGraphEdge,
  laneX: number,
  laneY?: number,
): TGraphEdge {
  return {
    ...edge,
    data: {
      ...edge.data,
      laneX,
      laneY,
      pathKind: edge.data?.pathKind === 'skip' ? 'from-fork' : edge.data?.pathKind,
    },
  };
}

function firstObstacleNearX(
  fromX: number,
  toX: number,
  y: number,
  cards: TGraphNode[],
): number | null {
  const goingRight = toX >= fromX;
  const hits = cards.filter((card) => segmentHitsCard(
    { a: { x: fromX, y }, b: { x: toX, y } },
    card,
  ));

  if (hits.length === 0) {
    return null;
  }

  if (goingRight) {
    return Math.min(...hits.map((card) => getGraphNodeBox(card).x));
  }

  return Math.max(...hits.map((card) => getGraphNodeBox(card).right));
}

export function pickTreeGutterX(
  fromX: number,
  toX: number,
  fromY: number,
  nodes: TGraphNode[],
  ignoreIds: Set<string>,
  takenXs: number[],
): number {
  const cards = nodes.filter((node) => isCardNode(node) && !ignoreIds.has(node.id));
  const goingRight = toX >= fromX;
  const nearX = firstObstacleNearX(fromX, toX, fromY, cards);
  const limitX = nearX == null ? (fromX + toX) / 2 : nearX;
  const preferred = goingRight
    ? Math.min(limitX - GRAPH_SKIP_LANE_GAP, Math.max(fromX, (fromX + limitX) / 2))
    : Math.max(limitX + GRAPH_SKIP_LANE_GAP, Math.min(fromX, (fromX + limitX) / 2));

  const isFree = (x: number): boolean => {
    if (takenXs.some((taken) => Math.abs(taken - x) < GRAPH_SKIP_LANE_STEP)) {
      return false;
    }

    const reach = { a: { x: fromX, y: fromY }, b: { x, y: fromY } };

    return !cards.some((card) => segmentHitsCard(reach, card));
  };

  if (isFree(preferred)) {
    return preferred;
  }

  const direction = goingRight ? -GRAPH_SKIP_LANE_STEP : GRAPH_SKIP_LANE_STEP;
  let x = preferred;

  for (let step = 0; step < 24; step += 1) {
    x += direction;

    if (isFree(x)) {
      return x;
    }
  }

  return preferred;
}

interface IYInterval {
  top: number;
  bottom: number;
}

const BORDER_GLUE = 4;

function occupiedYIntervals(cards: TGraphNode[], fromX: number, toX: number): IYInterval[] {
  const minX = Math.min(fromX, toX);
  const maxX = Math.max(fromX, toX);

  return cards
    .map((card) => getGraphNodeBox(card))
    .filter((box) => maxX > box.x + CARD_HIT_INSET && minX < box.right - CARD_HIT_INSET)
    .map((box) => ({ top: box.y, bottom: box.bottom }))
    .sort((first, second) => first.top - second.top);
}

function mergeYIntervals(intervals: IYInterval[]): IYInterval[] {
  return intervals.reduce<IYInterval[]>((merged, current) => {
    const last = merged[merged.length - 1];

    if (last && current.top <= last.bottom) {
      last.bottom = Math.max(last.bottom, current.bottom);

      return merged;
    }

    merged.push({ ...current });

    return merged;
  }, []);
}

function yCollidesInterval(y: number, interval: IYInterval): boolean {
  return (
    (y > interval.top + CARD_HIT_INSET && y < interval.bottom - CARD_HIT_INSET)
    || Math.abs(y - interval.top) < BORDER_GLUE
    || Math.abs(y - interval.bottom) < BORDER_GLUE
  );
}

export function pickClearY(
  fromX: number,
  toX: number,
  preferredY: number,
  nodes: TGraphNode[],
  ignoreIds: Set<string>,
  takenYs: number[],
): number {
  const cards = nodes.filter((node) => isCardNode(node) && !ignoreIds.has(node.id));
  const occupied = mergeYIntervals(occupiedYIntervals(cards, fromX, toX));

  const isFree = (y: number): boolean => (
    !takenYs.some((taken) => Math.abs(taken - y) < GRAPH_SKIP_LANE_STEP)
    && !occupied.some((interval) => yCollidesInterval(y, interval))
    && !cards.some((card) => segmentHitsCard({ a: { x: fromX, y }, b: { x: toX, y } }, card))
  );

  if (isFree(preferredY)) {
    return preferredY;
  }

  if (occupied.length === 0) {
    return preferredY;
  }

  const gaps: { lo: number; hi: number }[] = [
    { lo: occupied[0].top - GRAPH_ROW_GAP, hi: occupied[0].top },
  ];

  occupied.forEach((interval, index) => {
    const next = occupied[index + 1];

    if (next) {
      gaps.push({ lo: interval.bottom, hi: next.top });
    }
  });

  const last = occupied[occupied.length - 1];
  gaps.push({ lo: last.bottom, hi: last.bottom + GRAPH_ROW_GAP });

  const candidates = gaps
    .filter((gap) => gap.hi - gap.lo >= 8)
    .map((gap) => (gap.lo + gap.hi) / 2)
    .sort((first, second) => Math.abs(first - preferredY) - Math.abs(second - preferredY));

  return candidates.find(isFree) ?? preferredY;
}

export function planObstacleDetours(
  nodes: TGraphNode[],
  edges: TGraphEdge[],
): { xIds: Set<string>; gutters: Map<string, IGutterDetour> } {
  const nodeById = new Map(nodes.map((node) => [node.id, node]));
  const xIds = new Set<string>();
  const gutters = new Map<string, IGutterDetour>();
  const takenXs: number[] = [];
  const takenYs: number[] = [];

  edges.forEach((edge) => {
    const source = nodeById.get(edge.source);
    const target = nodeById.get(edge.target);

    if (!source || !target || edge.data?.isLaneRouted) {
      return;
    }

    const hit = classifyCardHit(edge, source, target, nodes);

    if (hit === 'vertical') {
      xIds.add(edge.id);

      return;
    }

    if (hit !== 'horizontal') {
      return;
    }

    const from = edge.data?.sourceAnchor ?? getHandleAnchor(source, edge.sourceHandle);
    const to = edge.data?.targetAnchor ?? getHandleAnchor(target, edge.targetHandle);
    const ignoreIds = new Set([source.id, target.id]);
    const laneX = pickTreeGutterX(from.x, to.x, from.y, nodes, ignoreIds, takenXs);
    const laneY = pickClearY(laneX, to.x, to.y, nodes, ignoreIds, takenYs);
    const detour: IGutterDetour = laneY === to.y
      ? { laneX }
      : { laneX, laneY };
    const candidate = withGutterPath(edge, detour.laneX, detour.laneY);

    if (classifyCardHit(candidate, source, target, nodes)) {
      const liftedY = pickClearY(laneX, to.x, from.y, nodes, ignoreIds, takenYs);
      detour.laneY = liftedY === to.y ? undefined : liftedY;
    }

    gutters.set(edge.id, detour);
    takenXs.push(detour.laneX);

    if (detour.laneY != null) {
      takenYs.push(detour.laneY);
    }
  });

  return { xIds, gutters };
}
