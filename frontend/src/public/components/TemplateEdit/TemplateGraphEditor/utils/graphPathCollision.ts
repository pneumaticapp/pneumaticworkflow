import { TGraphEdge, TGraphNode } from '../types';
import { isConditionalGraphEdge } from './edgeStyles';
import { isCheckIfStemEdge } from './graphConstants';
import { getGraphEdgePath } from './getGraphEdgePath';
import {
  GRAPH_EDGE_STANDOFF,
  GRAPH_LANE_CLEARANCE,
  GRAPH_ROW_GAP,
  GRAPH_SKIP_LANE_GAP,
  GRAPH_SKIP_LANE_STEP,
  faceFromHandle,
  getGraphNodeBox,
  getHandleAnchor,
  isCardNode,
  offsetAlongFace,
  sharesStemX,
  snapOutOfStandoffStrip,
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
  targetStandoff?: number;
}

/**
 * An alley already handed to another edge. `at` is the fixed axis value, `from`/`to` the extent
 * along the other axis, so two edges may reuse one alley where their runs do not overlap.
 */
export interface ILaneReservation {
  at: number;
  from: number;
  to: number;
}

export interface ILaneSpan {
  from: number;
  to: number;
}

/** A reservation owned by an edge, so a re-routed edge is not blocked by its own old alley. */
interface ITaggedLane extends ILaneReservation {
  edgeId: string;
}

function overlapLength(first: ILaneSpan, second: ILaneSpan): number {
  const start = Math.max(Math.min(first.from, first.to), Math.min(second.from, second.to));
  const end = Math.min(Math.max(first.from, first.to), Math.max(second.from, second.to));

  return end - start;
}

function rangesOverlap(first: ILaneSpan, second: ILaneSpan): boolean {
  return overlapLength(first, second) > 0;
}

function isLaneReserved(at: number, span: ILaneSpan, taken: ILaneReservation[], pitch: number): boolean {
  return taken.some((lane) => Math.abs(lane.at - at) < pitch && rangesOverlap(span, lane));
}

function byDistanceTo(preferred: number) {
  return (first: number, second: number): number => Math.abs(first - preferred) - Math.abs(second - preferred);
}

function dedupe(values: number[]): number[] {
  return values.filter((value, index) => values.findIndex((other) => Math.abs(other - value) < 0.5) === index);
}

export function parseGraphPath(path: string): IPathSegment[] {
  const tokens: string[] = path.match(/[MLQ][^MLQ]*/g) ?? [];
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
    maxX > box.x + CARD_HIT_INSET &&
    minX < box.right - CARD_HIT_INSET &&
    maxY > box.y + CARD_HIT_INSET &&
    minY < box.bottom - CARD_HIT_INSET
  );
}

/** A vertical run sitting exactly on a card side reads as a border, not as a line. */
export function segmentGlancesCard(segment: IPathSegment, card: TGraphNode): boolean {
  if (!isVerticalSegment(segment)) {
    return false;
  }

  const box = getGraphNodeBox(card);
  const onSide = Math.abs(segment.a.x - box.x) < 0.5 || Math.abs(segment.a.x - box.right) < 0.5;
  const minY = Math.min(segment.a.y, segment.b.y);
  const maxY = Math.max(segment.a.y, segment.b.y);

  return onSide && Math.min(maxY, box.bottom) - Math.max(minY, box.y) > CARD_HIT_INSET;
}

export function segmentCrowdsCard(segment: IPathSegment, card: TGraphNode): boolean {
  const box = getGraphNodeBox(card);
  const pad = GRAPH_SKIP_LANE_GAP;
  const minX = Math.min(segment.a.x, segment.b.x);
  const maxX = Math.max(segment.a.x, segment.b.x);
  const minY = Math.min(segment.a.y, segment.b.y);
  const maxY = Math.max(segment.a.y, segment.b.y);

  return maxX > box.x - pad && minX < box.right + pad && maxY > box.y - pad && minY < box.bottom + pad;
}

export function getEdgePathSegments(edge: TGraphEdge, source: TGraphNode, target: TGraphNode): IPathSegment[] {
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
    sourceStandoff: edge.data?.sourceStandoff,
    targetStandoff: edge.data?.targetStandoff,
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

function withGutterPath(edge: TGraphEdge, laneX: number, laneY?: number, targetStandoff?: number): TGraphEdge {
  return {
    ...edge,
    data: {
      ...edge.data,
      laneX,
      laneY,
      targetStandoff: targetStandoff ?? edge.data?.targetStandoff,
      pathKind: edge.data?.pathKind === 'skip' ? 'from-fork' : edge.data?.pathKind,
    },
  };
}

function firstObstacleNearX(fromX: number, toX: number, y: number, cards: TGraphNode[]): number | null {
  const goingRight = toX >= fromX;
  const hits = cards.filter((card) => segmentHitsCard({ a: { x: fromX, y }, b: { x: toX, y } }, card));

  if (hits.length === 0) {
    return null;
  }

  if (goingRight) {
    return Math.min(...hits.map((card) => getGraphNodeBox(card).x));
  }

  return Math.max(...hits.map((card) => getGraphNodeBox(card).right));
}

const GUTTER_SEARCH_STEPS = 24;
/** Comfortable spacing first, then progressively tighter, and finally overlap as a last resort. */
const LANE_PITCH_LADDER = [GRAPH_SKIP_LANE_STEP, GRAPH_LANE_CLEARANCE, GRAPH_LANE_CLEARANCE / 2, 0];

/** Columns worth trying for the first turn, starting at the gutter before the nearest obstacle. */
export function listGutterCandidates(
  fromX: number,
  toX: number,
  fromY: number,
  nodes: TGraphNode[],
  ignoreIds: Set<string>,
): number[] {
  const cards = nodes.filter((node) => isCardNode(node) && !ignoreIds.has(node.id));
  const goingRight = toX >= fromX;
  const nearX = firstObstacleNearX(fromX, toX, fromY, cards);
  const limitX = nearX == null ? (fromX + toX) / 2 : nearX;
  const minOut = goingRight ? fromX + GRAPH_EDGE_STANDOFF : fromX - GRAPH_EDGE_STANDOFF;
  const preferred = goingRight
    ? Math.min(limitX - GRAPH_SKIP_LANE_GAP, Math.max(minOut, (fromX + limitX) / 2))
    : Math.max(limitX + GRAPH_SKIP_LANE_GAP, Math.min(minOut, (fromX + limitX) / 2));
  const direction = goingRight ? -GRAPH_SKIP_LANE_STEP : GRAPH_SKIP_LANE_STEP;
  const candidates = [preferred];

  for (let step = 1; step <= GUTTER_SEARCH_STEPS; step += 1) {
    candidates.push(preferred + direction * step);
    candidates.push(preferred - direction * step);
  }

  return dedupe(candidates);
}

export function isGutterFree(
  laneX: number,
  from: IPathPoint,
  span: ILaneSpan,
  nodes: TGraphNode[],
  ignoreIds: Set<string>,
  taken: ILaneReservation[],
  pitch: number = GRAPH_SKIP_LANE_STEP,
): boolean {
  if (isLaneReserved(laneX, span, taken, pitch)) {
    return false;
  }

  const cards = nodes.filter((node) => isCardNode(node) && !ignoreIds.has(node.id));
  const reach = { a: from, b: { x: laneX, y: from.y } };
  const run = { a: { x: laneX, y: span.from }, b: { x: laneX, y: span.to } };

  return !cards.some(
    (card) => segmentHitsCard(reach, card) || segmentHitsCard(run, card) || segmentGlancesCard(run, card),
  );
}

export function pickTreeGutterX(
  fromX: number,
  toX: number,
  fromY: number,
  nodes: TGraphNode[],
  ignoreIds: Set<string>,
  taken: ILaneReservation[] = [],
): number | null {
  const from = { x: fromX, y: fromY };
  const span = { from: fromY, to: fromY };

  return (
    listGutterCandidates(fromX, toX, fromY, nodes, ignoreIds).find((laneX) =>
      isGutterFree(laneX, from, span, nodes, ignoreIds, taken),
    ) ?? null
  );
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
    (y > interval.top + CARD_HIT_INSET && y < interval.bottom - CARD_HIT_INSET) ||
    Math.abs(y - interval.top) < BORDER_GLUE ||
    Math.abs(y - interval.bottom) < BORDER_GLUE
  );
}

interface IGap {
  lo: number;
  hi: number;
}

const MIN_GAP_HEIGHT = 8;

/**
 * A row gap fits several parallel alleys, not just its midline. Packing it by lane step is what
 * keeps a crowded graph from pushing later edges out to a corridor above or below the whole tree.
 */
function gapSlots(gap: IGap): number[] {
  const first = gap.lo + GRAPH_LANE_CLEARANCE;
  const last = gap.hi - GRAPH_LANE_CLEARANCE;

  if (last < first) {
    return gap.hi - gap.lo >= MIN_GAP_HEIGHT ? [(gap.lo + gap.hi) / 2] : [];
  }

  const slots: number[] = [];

  for (let y = first; y <= last + 0.5; y += GRAPH_LANE_CLEARANCE) {
    slots.push(y);
  }

  return slots;
}

function buildGaps(occupied: IYInterval[], preferredY: number): IGap[] {
  if (occupied.length === 0) {
    return [{ lo: preferredY - GRAPH_ROW_GAP, hi: preferredY + GRAPH_ROW_GAP }];
  }

  const gaps: IGap[] = [{ lo: occupied[0].top - GRAPH_ROW_GAP * 2, hi: occupied[0].top }];

  occupied.forEach((interval, index) => {
    const next = occupied[index + 1];

    if (next) {
      gaps.push({ lo: interval.bottom, hi: next.top });
    }
  });

  const last = occupied[occupied.length - 1];
  gaps.push({ lo: last.bottom, hi: last.bottom + GRAPH_ROW_GAP * 2 });

  return gaps;
}

/** Horizontal alleys the edge can cross on, nearest to `preferredY` first. */
export function listClearYs(
  fromX: number,
  toX: number,
  preferredY: number,
  nodes: TGraphNode[],
  ignoreIds: Set<string>,
  taken: ILaneReservation[],
  pitch: number = GRAPH_SKIP_LANE_STEP,
): number[] {
  const cards = nodes.filter((node) => isCardNode(node) && !ignoreIds.has(node.id));
  const occupied = mergeYIntervals(occupiedYIntervals(cards, fromX, toX));
  const span = { from: fromX, to: toX };

  const isFree = (y: number): boolean =>
    !isLaneReserved(y, span, taken, pitch) &&
    !occupied.some((interval) => yCollidesInterval(y, interval)) &&
    !cards.some((card) => segmentHitsCard({ a: { x: fromX, y }, b: { x: toX, y } }, card));

  const candidates = [preferredY, ...buildGaps(occupied, preferredY).flatMap(gapSlots)];

  return dedupe(candidates).filter(isFree).sort(byDistanceTo(preferredY));
}

export function pickClearY(
  fromX: number,
  toX: number,
  preferredY: number,
  nodes: TGraphNode[],
  ignoreIds: Set<string>,
  taken: ILaneReservation[] = [],
): number | null {
  return listClearYs(fromX, toX, preferredY, nodes, ignoreIds, taken)[0] ?? null;
}

function clampLaneToFace(laneX: number, sourceFace: string, exitX: number): number {
  if (sourceFace === 'left') {
    return Math.min(laneX, exitX);
  }

  if (sourceFace === 'right') {
    return Math.max(laneX, exitX);
  }

  return laneX;
}

interface IDetourContext {
  edge: TGraphEdge;
  source: TGraphNode;
  target: TGraphNode;
  nodes: TGraphNode[];
  ignoreIds: Set<string>;
}

/** Runs worth recording as occupied: anything a neighbour could visibly merge with. */
const LANE_REGISTER_MIN = GRAPH_LANE_CLEARANCE;
/**
 * Runs worth rejecting a candidate over. Docking runs are the standoff itself and every line
 * entering the same junction shares one by design, so they never count as a conflict.
 */
const LANE_CONFLICT_MIN = GRAPH_EDGE_STANDOFF + 1;

function longRuns(
  segments: IPathSegment[],
  minLength: number,
): { xRuns: ILaneReservation[]; yRuns: ILaneReservation[] } {
  const xRuns: ILaneReservation[] = [];
  const yRuns: ILaneReservation[] = [];

  segments.forEach((segment) => {
    if (Math.hypot(segment.b.x - segment.a.x, segment.b.y - segment.a.y) < minLength) {
      return;
    }

    if (isVerticalSegment(segment)) {
      xRuns.push({ at: segment.a.x, from: segment.a.y, to: segment.b.y });
    }

    if (isHorizontalSegment(segment)) {
      yRuns.push({ at: segment.a.y, from: segment.a.x, to: segment.b.x });
    }
  });

  return { xRuns, yRuns };
}

/** Alleys the settled edges already run along, so a detour does not land on top of a neighbour. */
function collectLaneUsage(
  nodes: TGraphNode[],
  edges: TGraphEdge[],
  skipIds: Set<string>,
): { xLanes: ITaggedLane[]; yLanes: ITaggedLane[] } {
  const nodeById = new Map(nodes.map((node) => [node.id, node]));
  const xLanes: ITaggedLane[] = [];
  const yLanes: ITaggedLane[] = [];

  edges.forEach((edge) => {
    const source = nodeById.get(edge.source);
    const target = nodeById.get(edge.target);

    if (!source || !target || skipIds.has(edge.id)) {
      return;
    }

    const { xRuns, yRuns } = longRuns(getEdgePathSegments(edge, source, target), LANE_REGISTER_MIN);
    xRuns.forEach((run) => xLanes.push({ ...run, edgeId: edge.id }));
    yRuns.forEach((run) => yLanes.push({ ...run, edgeId: edge.id }));
  });

  return { xLanes, yLanes };
}

/**
 * Try each free alley pair and keep the first whose rebuilt path clears every card and every
 * alley a neighbour already uses. Validating the finished path, rather than the planned alleys
 * alone, also covers the run the line makes before its first turn.
 */
function searchDetour(
  context: IDetourContext,
  laneXs: number[],
  to: IPathPoint,
  taken: { xLanes: ILaneReservation[]; yLanes: ILaneReservation[] },
  pitch: number,
): IGutterDetour | null {
  const { edge, source, target, nodes, ignoreIds } = context;

  const isClean = (laneX: number, laneY: number): boolean => {
    const candidate = withGutterPath(edge, laneX, laneY === to.y ? undefined : laneY);

    if (classifyCardHit(candidate, source, target, nodes)) {
      return false;
    }

    const { xRuns, yRuns } = longRuns(getEdgePathSegments(candidate, source, target), LANE_CONFLICT_MIN);

    return (
      !xRuns.some((run) => isLaneReserved(run.at, run, taken.xLanes, pitch)) &&
      !yRuns.some((run) => isLaneReserved(run.at, run, taken.yLanes, pitch))
    );
  };

  return laneXs.reduce<IGutterDetour | null>((found, laneX) => {
    if (found) {
      return found;
    }

    const clean = listClearYs(laneX, to.x, to.y, nodes, ignoreIds, taken.yLanes, pitch).find((laneY) =>
      isClean(laneX, laneY),
    );

    if (clean == null) {
      return null;
    }

    return clean === to.y ? { laneX } : { laneX, laneY: clean };
  }, null);
}

/** Edges whose current path cuts a card, split by the axis of the offending run. */
function classifyDetours(
  nodes: TGraphNode[],
  edges: TGraphEdge[],
  nodeById: Map<string, TGraphNode>,
): { xIds: Set<string>; gutterEdges: TGraphEdge[] } {
  const xIds = new Set<string>();
  const gutterEdges: TGraphEdge[] = [];

  edges.forEach((edge) => {
    const source = nodeById.get(edge.source);
    const target = nodeById.get(edge.target);

    if (!source || !target) {
      return;
    }

    if (edge.data?.isLaneRouted && !isConditionalGraphEdge(edge)) {
      return;
    }

    if (isCheckIfStemEdge(source.id, target.id)) {
      return;
    }

    let hit = classifyCardHit(edge, source, target, nodes);

    if (hit === 'vertical' && isConditionalGraphEdge(edge)) {
      hit = 'horizontal';
    }

    if (hit === 'vertical') {
      xIds.add(edge.id);

      return;
    }

    if (hit === 'horizontal') {
      gutterEdges.push(edge);
    }
  });

  return { xIds, gutterEdges };
}

const SAME_LANE_EPSILON = 1;

function sharesLane(run: ILaneReservation, settled: ILaneReservation[]): boolean {
  return settled.some(
    (lane) => Math.abs(lane.at - run.at) < SAME_LANE_EPSILON && overlapLength(run, lane) >= LANE_CONFLICT_MIN,
  );
}

/**
 * Lines fanning out of one junction clear every card yet can still run down the same column for
 * hundreds of pixels, reading as a single line. The first one keeps the column, the rest are
 * handed to the detour planner so they pick their own.
 */
function findCrowdedEdges(
  nodes: TGraphNode[],
  edges: TGraphEdge[],
  nodeById: Map<string, TGraphNode>,
  pending: Set<string>,
): TGraphEdge[] {
  const xLanes: ILaneReservation[] = [];
  const yLanes: ILaneReservation[] = [];
  const crowded: TGraphEdge[] = [];

  edges.forEach((edge) => {
    const source = nodeById.get(edge.source);
    const target = nodeById.get(edge.target);

    if (!source || !target || pending.has(edge.id) || isCheckIfStemEdge(source.id, target.id)) {
      return;
    }

    const { xRuns, yRuns } = longRuns(getEdgePathSegments(edge, source, target), LANE_CONFLICT_MIN);

    if (xRuns.some((run) => sharesLane(run, xLanes)) || yRuns.some((run) => sharesLane(run, yLanes))) {
      crowded.push(edge);

      return;
    }

    xLanes.push(...xRuns);
    yLanes.push(...yRuns);
  });

  return crowded;
}

export function planObstacleDetours(
  nodes: TGraphNode[],
  edges: TGraphEdge[],
): { xIds: Set<string>; gutters: Map<string, IGutterDetour> } {
  const nodeById = new Map(nodes.map((node) => [node.id, node]));
  const gutters = new Map<string, IGutterDetour>();
  const { xIds, gutterEdges } = classifyDetours(nodes, edges, nodeById);
  const hitting = new Set([...xIds, ...gutterEdges.map((edge) => edge.id)]);
  const crowded = findCrowdedEdges(nodes, edges, nodeById, hitting);
  const moving = [...gutterEdges, ...crowded];
  const pending = new Set([...xIds, ...moving.map((edge) => edge.id)]);
  const { xLanes, yLanes } = collectLaneUsage(nodes, edges, pending);

  moving.forEach((edge) => {
    const source = nodeById.get(edge.source)!;
    const target = nodeById.get(edge.target)!;
    const from = edge.data?.sourceAnchor ?? getHandleAnchor(source, edge.sourceHandle);
    const to = edge.data?.targetAnchor ?? getHandleAnchor(target, edge.targetHandle);
    const sourceFace = faceFromHandle(edge.data?.sourceHandle ?? edge.sourceHandle);
    const targetFace = faceFromHandle(edge.data?.targetHandle ?? edge.targetHandle);
    const fromExit = offsetAlongFace(from, sourceFace, edge.data?.sourceStandoff ?? 0);
    const entry = offsetAlongFace(to, targetFace, edge.data?.targetStandoff ?? GRAPH_EDGE_STANDOFF);
    const ignoreIds = new Set([source.id, target.id]);
    const span = { from: fromExit.y, to: to.y };
    const context = { edge, source, target, nodes, ignoreIds };

    // The face clamp and the standoff snap move a column, so candidates are adjusted before the
    // reservation check; filtering first would collapse every option onto one occupied alley.
    const laneXs = dedupe(
      listGutterCandidates(fromExit.x, to.x, fromExit.y, nodes, ignoreIds).map((gutterX) => {
        const laneX = clampLaneToFace(gutterX, sourceFace, fromExit.x);

        return targetFace === 'left' || targetFace === 'right' ? snapOutOfStandoffStrip(laneX, to.x, entry.x) : laneX;
      }),
    );

    const planWith = (pitch: number): IGutterDetour | null => {
      const free = laneXs.filter((laneX) => isGutterFree(laneX, fromExit, span, nodes, ignoreIds, xLanes, pitch));

      return searchDetour(context, free, to, { xLanes, yLanes }, pitch);
    };

    // A crowded gutter is better served by lines running closer together than by two lines
    // landing on the very same alley, so the spacing requirement is relaxed step by step.
    const detour = LANE_PITCH_LADDER.reduce<IGutterDetour | null>((found, pitch) => found ?? planWith(pitch), null);

    if (!detour) {
      return;
    }

    gutters.set(edge.id, detour);

    const settled = withGutterPath(edge, detour.laneX, detour.laneY);
    const { xRuns, yRuns } = longRuns(getEdgePathSegments(settled, source, target), LANE_REGISTER_MIN);
    xRuns.forEach((run) => xLanes.push({ ...run, edgeId: edge.id }));
    yRuns.forEach((run) => yLanes.push({ ...run, edgeId: edge.id }));
  });

  return { xIds, gutters };
}

export function planCheckIfCardWraps(nodes: TGraphNode[], edges: TGraphEdge[]): Map<string, IGutterDetour> {
  const nodeById = new Map(nodes.map((node) => [node.id, node]));
  const takenY: ILaneReservation[] = [];

  edges.forEach((edge) => {
    if (isConditionalGraphEdge(edge)) {
      return;
    }

    const source = nodeById.get(edge.source);
    const target = nodeById.get(edge.target);

    if (!source || !target) {
      return;
    }

    getEdgePathSegments(edge, source, target).forEach((segment) => {
      if (isHorizontalSegment(segment) && Math.abs(segment.a.x - segment.b.x) > GRAPH_SKIP_LANE_STEP) {
        takenY.push({ at: segment.a.y, from: segment.a.x, to: segment.b.x });
      }
    });
  });

  const wraps = new Map<string, IGutterDetour>();
  const candidates = edges
    .filter((edge) => {
      const target = nodeById.get(edge.target);

      return Boolean(
        target &&
        isConditionalGraphEdge(edge) &&
        isCardNode(target) &&
        !isCheckIfStemEdge(edge.source, edge.target) &&
        !edge.data?.isLaneRouted &&
        edge.data?.laneX == null,
      );
    })
    .sort((first, second) => first.id.localeCompare(second.id));

  candidates.forEach((edge) => {
    const source = nodeById.get(edge.source);
    const target = nodeById.get(edge.target);

    if (!source || !target) {
      return;
    }

    const from = edge.data?.sourceAnchor ?? getHandleAnchor(source, edge.sourceHandle);
    const to = edge.data?.targetAnchor ?? getHandleAnchor(target, edge.targetHandle);
    const sourceFace = faceFromHandle(edge.data?.sourceHandle ?? edge.sourceHandle);
    const targetFace = faceFromHandle(edge.data?.targetHandle ?? edge.targetHandle);
    const fromExit = offsetAlongFace(from, sourceFace, edge.data?.sourceStandoff ?? 0);
    const entry = offsetAlongFace(to, targetFace, edge.data?.targetStandoff ?? GRAPH_EDGE_STANDOFF);
    const sourceBox = getGraphNodeBox(source);
    const targetBox = getGraphNodeBox(target);
    let preferredY = fromExit.y;

    if (sourceBox.bottom <= targetBox.y) {
      preferredY = (sourceBox.bottom + targetBox.y) / 2;
    } else if (targetBox.bottom <= sourceBox.y) {
      preferredY = (targetBox.bottom + sourceBox.y) / 2;
    }

    const ignoreIds = new Set([source.id, target.id]);
    let laneX = fromExit.x;

    if (targetFace === 'left' || targetFace === 'right') {
      laneX = snapOutOfStandoffStrip(laneX, to.x, entry.x);
    }

    const laneY = pickClearY(laneX, to.x, preferredY, nodes, ignoreIds, takenY);

    if (laneY == null) {
      return;
    }

    wraps.set(edge.id, { laneX, laneY });
    takenY.push({ at: laneY, from: laneX, to: to.x });
  });

  return wraps;
}
