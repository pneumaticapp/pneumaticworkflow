import { Position } from 'reactflow';
import { TGraphEdgePathKind } from '../types';
import {
  GRAPH_EDGE_SIDEWAYS_THRESHOLD,
  TGraphFace,
  faceFromHandle,
  offsetAlongFace,
  snapOutOfStandoffStrip,
} from './graphGeometry';

interface IGraphEdgePathParams {
  sourceX: number;
  sourceY: number;
  targetX: number;
  targetY: number;
  pathKind?: TGraphEdgePathKind;
  laneX?: number;
  laneY?: number;
  sourceHandle?: string | null;
  targetHandle?: string | null;
  sourcePosition?: Position;
  targetPosition?: Position;
  sourceStandoff?: number;
  targetStandoff?: number;
}

export interface IGraphEdgePath {
  path: string;
  labelX: number;
  labelY: number;
}

interface IPoint {
  x: number;
  y: number;
}

const AXIS_EPSILON = 0.5;
export const GRAPH_EDGE_LABEL_OFFSET = 28;

function buildPath(points: IPoint[]): string {
  return points
    .map(({ x, y }, index) => `${index === 0 ? 'M' : 'L'} ${x},${y}`)
    .join(' ');
}

function withPath(points: IPoint[], label: IPoint): IGraphEdgePath {
  return {
    path: buildPath(points),
    labelX: label.x,
    labelY: label.y,
  };
}

function almostEqual(first: number, second: number): boolean {
  return Math.abs(first - second) < AXIS_EPSILON;
}

function isCollinear(previous: IPoint, current: IPoint, next: IPoint): boolean {
  const onVertical = almostEqual(previous.x, current.x) && almostEqual(current.x, next.x);
  const onHorizontal = almostEqual(previous.y, current.y) && almostEqual(current.y, next.y);

  return onVertical || onHorizontal;
}

function isBetweenOnAxis(previous: IPoint, current: IPoint, next: IPoint): boolean {
  if (almostEqual(previous.x, current.x) && almostEqual(current.x, next.x)) {
    const minY = Math.min(previous.y, next.y);
    const maxY = Math.max(previous.y, next.y);

    return current.y >= minY - AXIS_EPSILON && current.y <= maxY + AXIS_EPSILON;
  }

  if (almostEqual(previous.y, current.y) && almostEqual(current.y, next.y)) {
    const minX = Math.min(previous.x, next.x);
    const maxX = Math.max(previous.x, next.x);

    return current.x >= minX - AXIS_EPSILON && current.x <= maxX + AXIS_EPSILON;
  }

  return false;
}

function simplifyPoints(points: IPoint[]): IPoint[] {
  const unique: IPoint[] = [];

  points.forEach((point) => {
    const previous = unique[unique.length - 1];

    if (previous && almostEqual(previous.x, point.x) && almostEqual(previous.y, point.y)) {
      return;
    }

    unique.push(point);
  });

  const simplified: IPoint[] = [];

  unique.forEach((point, index) => {
    const previous = simplified[simplified.length - 1];
    const next = unique[index + 1];

    if (previous && next && isCollinear(previous, point, next) && isBetweenOnAxis(previous, point, next)) {
      return;
    }

    simplified.push(point);
  });

  return simplified.length >= 2 ? simplified : unique;
}

function faceFromPosition(position?: Position): TGraphFace | null {
  if (position === Position.Top) {
    return 'top';
  }

  if (position === Position.Bottom) {
    return 'bottom';
  }

  if (position === Position.Left) {
    return 'left';
  }

  if (position === Position.Right) {
    return 'right';
  }

  return null;
}

function resolveFaces(params: IGraphEdgePathParams): { sourceFace: TGraphFace; targetFace: TGraphFace } {
  if (params.pathKind === 'skip') {
    const fallback: TGraphFace = params.laneX != null && params.laneX < params.sourceX ? 'left' : 'right';

    return {
      sourceFace: params.sourceHandle ? faceFromHandle(params.sourceHandle) : fallback,
      targetFace: params.targetHandle ? faceFromHandle(params.targetHandle) : fallback,
    };
  }

  let sourceFace: TGraphFace;
  if (params.sourceHandle) {
    sourceFace = faceFromHandle(params.sourceHandle);
  } else {
    const fromPosition = faceFromPosition(params.sourcePosition);
    if (fromPosition) {
      sourceFace = fromPosition;
    } else if (params.pathKind === 'from-fork') {
      sourceFace = params.targetX >= params.sourceX ? 'right' : 'left';
    } else {
      sourceFace = 'bottom';
    }
  }
  const targetFace = params.targetHandle
    ? faceFromHandle(params.targetHandle)
    : (faceFromPosition(params.targetPosition) ?? 'top');

  return { sourceFace, targetFace };
}

function closeOnAxis(first: number, second: number): boolean {
  return Math.abs(first - second) <= GRAPH_EDGE_SIDEWAYS_THRESHOLD;
}

function isFacingSides(
  sourceFace: TGraphFace,
  targetFace: TGraphFace,
  sourceX: number,
  targetX: number,
): boolean {
  return (sourceFace === 'right' && targetFace === 'left' && sourceX <= targetX)
    || (sourceFace === 'left' && targetFace === 'right' && sourceX >= targetX);
}

function isOutwardX(face: TGraphFace, fromX: number, toX: number): boolean {
  if (face === 'right') {
    return toX >= fromX;
  }

  if (face === 'left') {
    return toX <= fromX;
  }

  return true;
}

function nudgeLaneX(
  laneX: number,
  startX: number,
  standoffX: number,
  face: TGraphFace,
): number {
  if (face === 'right' && laneX > startX && laneX < standoffX) {
    return standoffX;
  }

  if (face === 'left' && laneX < startX && laneX > standoffX) {
    return standoffX;
  }

  return laneX;
}

function pullRoutingOffStrip(points: IPoint[], handleX: number, standoffX: number): IPoint[] {
  if (points.length < 2 || almostEqual(handleX, standoffX)) {
    return points;
  }

  const result: IPoint[] = [];

  points.forEach((point, index) => {
    const isEnd = index === 0 || index === points.length - 1;
    const snappedX = isEnd ? point.x : snapOutOfStandoffStrip(point.x, handleX, standoffX);

    if (!isEnd && !almostEqual(snappedX, point.x)) {
      const previous = result[result.length - 1];

      if (previous && !almostEqual(previous.y, point.y) && !almostEqual(previous.x, snappedX)) {
        result.push({ x: snappedX, y: previous.y });
      }
    }

    result.push({ x: snappedX, y: point.y });
  });

  return result;
}

function forcePerpendicularDock(
  points: IPoint[],
  dock: IPoint,
  standoff: IPoint,
  face: TGraphFace,
): IPoint[] {
  if ((face !== 'left' && face !== 'right') || points.length === 0) {
    return points;
  }

  const body = [...points];
  const last = body[body.length - 1];

  if (last && almostEqual(last.x, dock.x) && almostEqual(last.y, dock.y)) {
    body.pop();
  }

  const tail = body[body.length - 1] ?? standoff;

  return simplifyPoints([
    ...body,
    { x: standoff.x, y: tail.y },
    standoff,
    dock,
  ]);
}

function orthogonalPoints(
  sourceX: number,
  sourceY: number,
  sourceFace: TGraphFace,
  targetX: number,
  targetY: number,
  targetFace: TGraphFace,
  laneX?: number,
  pathKind?: TGraphEdgePathKind,
): IPoint[] {
  if ((sourceFace === 'right' && targetFace === 'right' || sourceFace === 'left' && targetFace === 'left')
    && laneX != null) {
    return simplifyPoints([
      { x: sourceX, y: sourceY },
      { x: laneX, y: sourceY },
      { x: laneX, y: targetY },
      { x: targetX, y: targetY },
    ]);
  }

  const enterFromSide = targetFace === 'left' || targetFace === 'right';
  const leaveFromSide = pathKind === 'from-fork' || sourceFace === 'left' || sourceFace === 'right';

  if (isFacingSides(sourceFace, targetFace, sourceX, targetX)) {
    if (closeOnAxis(sourceY, targetY)) {
      return [
        { x: sourceX, y: sourceY },
        { x: targetX, y: sourceY },
      ];
    }

    return simplifyPoints([
      { x: sourceX, y: sourceY },
      { x: targetX, y: sourceY },
      { x: targetX, y: targetY },
    ]);
  }

  if (leaveFromSide) {
    if (almostEqual(sourceY, targetY)) {
      return [
        { x: sourceX, y: sourceY },
        { x: targetX, y: targetY },
      ];
    }

    if (isOutwardX(sourceFace, sourceX, targetX)) {
      return simplifyPoints([
        { x: sourceX, y: sourceY },
        { x: targetX, y: sourceY },
        { x: targetX, y: targetY },
      ]);
    }

    return simplifyPoints([
      { x: sourceX, y: sourceY },
      { x: sourceX, y: targetY },
      { x: targetX, y: targetY },
    ]);
  }

  if (enterFromSide) {
    if (almostEqual(sourceY, targetY)) {
      return [
        { x: sourceX, y: sourceY },
        { x: targetX, y: targetY },
      ];
    }

    return simplifyPoints([
      { x: sourceX, y: sourceY },
      { x: sourceX, y: targetY },
      { x: targetX, y: targetY },
    ]);
  }

  if (almostEqual(sourceX, targetX) || almostEqual(sourceY, targetY)) {
    return [
      { x: sourceX, y: sourceY },
      { x: targetX, y: targetY },
    ];
  }

  return simplifyPoints([
    { x: sourceX, y: sourceY },
    { x: sourceX, y: targetY },
    { x: targetX, y: targetY },
  ]);
}

function labelAtStart(points: IPoint[]): IPoint {
  if (points.length < 2) {
    return points[0] ?? { x: 0, y: 0 };
  }

  for (let index = 0; index < points.length - 1; index += 1) {
    const from = points[index];
    const to = points[index + 1];
    const dx = to.x - from.x;
    const dy = to.y - from.y;
    const distance = Math.hypot(dx, dy);

    if (distance >= GRAPH_EDGE_LABEL_OFFSET) {
      const ratio = GRAPH_EDGE_LABEL_OFFSET / distance;

      return {
        x: from.x + dx * ratio,
        y: from.y + dy * ratio,
      };
    }
  }

  const from = points[0];
  const to = points[1];
  const dx = to.x - from.x;
  const dy = to.y - from.y;
  const distance = Math.hypot(dx, dy);

  if (distance < 1) {
    return from;
  }

  const ratio = Math.min(GRAPH_EDGE_LABEL_OFFSET / distance, 0.45);

  return {
    x: from.x + dx * ratio,
    y: from.y + dy * ratio,
  };
}

export function resolveGraphEdgePathKind(
  sourceX: number,
  targetX: number,
  pathKind?: TGraphEdgePathKind,
): TGraphEdgePathKind {
  if (pathKind === 'skip' || pathKind === 'from-fork' || pathKind === 'from-task') {
    return pathKind;
  }

  if (Math.abs(targetX - sourceX) <= GRAPH_EDGE_SIDEWAYS_THRESHOLD) {
    return 'straight';
  }

  return pathKind ?? 'from-task';
}

export function getGraphEdgePath(params: IGraphEdgePathParams): IGraphEdgePath {
  const { sourceFace, targetFace } = resolveFaces(params);
  const start = { x: params.sourceX, y: params.sourceY };
  const end = { x: params.targetX, y: params.targetY };
  const exit = offsetAlongFace(start, sourceFace, params.sourceStandoff ?? 0);
  const entry = offsetAlongFace(end, targetFace, params.targetStandoff ?? 0);

  const dockOnSide = targetFace === 'left' || targetFace === 'right';

  if (params.laneX != null) {
    const midY = params.laneY ?? entry.y;
    let laneX = nudgeLaneX(
      nudgeLaneX(params.laneX, start.x, exit.x, sourceFace),
      end.x,
      entry.x,
      targetFace,
    );

    if (dockOnSide) {
      laneX = snapOutOfStandoffStrip(laneX, end.x, entry.x);
    }

    const points = forcePerpendicularDock(
      simplifyPoints(pullRoutingOffStrip([
        start,
        exit,
        { x: laneX, y: exit.y },
        { x: laneX, y: midY },
        { x: entry.x, y: midY },
        entry,
        end,
      ], end.x, entry.x)),
      end,
      entry,
      targetFace,
    );

    return withPath(points, labelAtStart(points));
  }

  const routeExitX = dockOnSide ? snapOutOfStandoffStrip(exit.x, end.x, entry.x) : exit.x;
  const mid = orthogonalPoints(
    routeExitX,
    exit.y,
    sourceFace,
    entry.x,
    entry.y,
    targetFace,
    params.laneX,
    params.pathKind,
  );
  const points = forcePerpendicularDock(
    simplifyPoints(pullRoutingOffStrip([start, exit, ...mid, end], end.x, entry.x)),
    end,
    entry,
    targetFace,
  );

  return withPath(points, labelAtStart(points));
}
