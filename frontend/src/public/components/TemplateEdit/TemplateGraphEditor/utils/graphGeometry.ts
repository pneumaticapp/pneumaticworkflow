import { EGraphNodeType, TGraphNode, TJunctionKind, TJunctionNode } from '../types';

export const GRAPH_NODE_WIDTH = 304;
export const GRAPH_NODE_HEIGHT = 112;
export const GRAPH_JUNCTION_SIZE = 8;
export const GRAPH_EDGE_SIDEWAYS_THRESHOLD = 8;
export const GRAPH_COLUMN_GAP = 140;
export const GRAPH_ROW_GAP = 64;
export const GRAPH_SKIP_LANE_GAP = 32;
export const GRAPH_SKIP_LANE_STEP = 32;

export const GRAPH_HANDLE = {
  SourceTop: 'source-top',
  SourceBottom: 'source-bottom',
  SourceLeft: 'source-left',
  SourceRight: 'source-right',
  SourceSkip: 'source-right',
  TargetTop: 'target-top',
  TargetBottom: 'target-bottom',
  TargetLeft: 'target-left',
  TargetRight: 'target-right',
  TargetSkip: 'target-right',
} as const;

export type TGraphFace = 'top' | 'bottom' | 'left' | 'right';
export type TGraphLaneSide = 'left' | 'right';

export function faceFromHandle(handle?: string | null): TGraphFace {
  if (!handle) {
    return 'bottom';
  }

  if (handle.includes('top')) {
    return 'top';
  }

  if (handle.includes('left')) {
    return 'left';
  }

  if (handle.includes('right') || handle.includes('skip')) {
    return 'right';
  }

  return 'bottom';
}

export function handleForFace(role: 'source' | 'target', face: TGraphFace): string {
  return `${role}-${face}`;
}

export interface IGraphNodeBox {
  x: number;
  y: number;
  width: number;
  height: number;
  centerX: number;
  centerY: number;
  right: number;
  bottom: number;
}

export function isJunctionNode(node: TGraphNode): node is TJunctionNode {
  return node.type === EGraphNodeType.Junction;
}

export function isCardNode(node: TGraphNode): boolean {
  return node.type === EGraphNodeType.Task || node.type === EGraphNodeType.Kickoff;
}

export function getJunctionKind(node: TGraphNode): TJunctionKind | null {
  return isJunctionNode(node) ? node.data.kind : null;
}

export function getGraphNodeBox(node: TGraphNode): IGraphNodeBox {
  const width = node.width ?? (isJunctionNode(node) ? GRAPH_JUNCTION_SIZE : GRAPH_NODE_WIDTH);
  const height = node.height ?? (isJunctionNode(node) ? GRAPH_JUNCTION_SIZE : GRAPH_NODE_HEIGHT);
  const { x, y } = node.position;

  return {
    x,
    y,
    width,
    height,
    centerX: x + width / 2,
    centerY: y + height / 2,
    right: x + width,
    bottom: y + height,
  };
}

export interface IGraphHandleAnchor {
  x: number;
  y: number;
}

export function getHandleAnchor(node: TGraphNode, handleId?: string | null): IGraphHandleAnchor {
  const box = getGraphNodeBox(node);

  if (isJunctionNode(node)) {
    return { x: box.centerX, y: box.centerY };
  }

  const face = faceFromHandle(handleId);

  if (face === 'top') {
    return { x: box.centerX, y: box.y };
  }

  if (face === 'left') {
    return { x: box.x, y: box.centerY };
  }

  if (face === 'right') {
    return { x: box.right, y: box.centerY };
  }

  return { x: box.centerX, y: box.bottom };
}

export function overlapsHorizontally(first: IGraphNodeBox, second: IGraphNodeBox): boolean {
  const inset = GRAPH_EDGE_SIDEWAYS_THRESHOLD;

  return first.right - inset > second.x && second.right - inset > first.x;
}

export function sharesStemX(first: IGraphNodeBox, second: IGraphNodeBox): boolean {
  return Math.abs(first.centerX - second.centerX) <= GRAPH_EDGE_SIDEWAYS_THRESHOLD;
}

/** True when the origin's vertical line would hit `box`. */
export function isHorizontallyOver(origin: IGraphNodeBox, box: IGraphNodeBox): boolean {
  const inset = GRAPH_EDGE_SIDEWAYS_THRESHOLD;

  return origin.centerX > box.x + inset && origin.centerX < box.right - inset;
}

export function preferredFaces(source: TGraphNode, target: TGraphNode): { source: TGraphFace; target: TGraphFace } {
  const from = getGraphNodeBox(source);
  const to = getGraphNodeBox(target);
  const gapBelow = to.y - from.bottom;
  const gapAbove = from.y - to.bottom;
  const facing: { source: TGraphFace; target: TGraphFace } = to.centerX >= from.centerX
    ? { source: 'right', target: 'left' }
    : { source: 'left', target: 'right' };
  const onStem = isJunctionNode(source)
    ? sharesStemX(from, to) || isHorizontallyOver(from, to)
    : (overlapsHorizontally(from, to) || isCardNode(source));

  if (gapBelow >= 0) {
    if (onStem) {
      return { source: 'bottom', target: 'top' };
    }

    return { source: facing.source, target: 'top' };
  }

  if (gapAbove >= 0) {
    if (onStem) {
      return { source: 'top', target: 'bottom' };
    }

    return { source: facing.source, target: 'bottom' };
  }

  return facing;
}
