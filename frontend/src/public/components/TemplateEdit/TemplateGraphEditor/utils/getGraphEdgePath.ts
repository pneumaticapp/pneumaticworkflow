import { Position } from 'reactflow';
import { TGraphEdgePathKind } from '../types';
import { GRAPH_EDGE_SIDEWAYS_THRESHOLD, TGraphFace, faceFromHandle } from './graphGeometry';

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

    if (previous && next && isCollinear(previous, point, next)) {
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

    return simplifyPoints([
      { x: sourceX, y: sourceY },
      { x: targetX, y: sourceY },
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
  if (params.laneX != null && params.pathKind !== 'skip') {
    const midY = params.laneY ?? params.targetY;
    const points = simplifyPoints([
      { x: params.sourceX, y: params.sourceY },
      { x: params.laneX, y: params.sourceY },
      { x: params.laneX, y: midY },
      { x: params.targetX, y: midY },
      { x: params.targetX, y: params.targetY },
    ]);

    return withPath(points, labelAtStart(points));
  }

  const { sourceFace, targetFace } = resolveFaces(params);
  const points = orthogonalPoints(
    params.sourceX,
    params.sourceY,
    sourceFace,
    params.targetX,
    params.targetY,
    targetFace,
    params.laneX,
    params.pathKind,
  );

  return withPath(points, labelAtStart(points));
}
