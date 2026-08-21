import { EGraphNodeType, TGraphNode, TGraphEdge } from '../types';

export const GRAPH_NODE_WIDTH = 304;
export const GRAPH_NODE_HEIGHT = 112;
export const GRAPH_JUNCTION_SIZE = 8;
const HORIZONTAL_GAP = 100;
const VERTICAL_GAP = 64;
const JUNCTION_GAP = 48;

interface INodeSize {
  width: number;
  height: number;
}

function getNodeSize(node: TGraphNode): INodeSize {
  if (node.type === EGraphNodeType.Junction) {
    return { width: GRAPH_JUNCTION_SIZE, height: GRAPH_JUNCTION_SIZE };
  }

  return { width: GRAPH_NODE_WIDTH, height: GRAPH_NODE_HEIGHT };
}

function computeLevels(nodes: TGraphNode[], edges: TGraphEdge[]): Map<string, number> {
  const successors = new Map<string, string[]>();
  const predecessors = new Map<string, string[]>();

  nodes.forEach((n) => {
    successors.set(n.id, []);
    predecessors.set(n.id, []);
  });

  edges.forEach((e) => {
    successors.get(e.source)?.push(e.target);
    predecessors.get(e.target)?.push(e.source);
  });

  const levels = new Map<string, number>();
  const queue: string[] = [];

  nodes.forEach((n) => {
    if ((predecessors.get(n.id) ?? []).length === 0) {
      levels.set(n.id, 0);
      queue.push(n.id);
    }
  });

  while (queue.length > 0) {
    const nodeId = queue.shift()!;
    const currentLevel = levels.get(nodeId)!;

    (successors.get(nodeId) ?? []).forEach((successorId) => {
      const existingLevel = levels.get(successorId) ?? -1;

      if (currentLevel + 1 > existingLevel) {
        levels.set(successorId, currentLevel + 1);
        queue.push(successorId);
      }
    });
  }

  nodes.forEach((n) => {
    if (!levels.has(n.id)) levels.set(n.id, 0);
  });

  return levels;
}

function snapJunctionX(
  nodes: TGraphNode[],
  edges: TGraphEdge[],
  posMap: Map<string, { x: number; y: number }>,
): void {
  const nodeById = new Map(nodes.map((node) => [node.id, node]));

  nodes.forEach((node) => {
    if (node.type !== EGraphNodeType.Junction) return;

    const pos = posMap.get(node.id);
    if (!pos) return;

    if (node.data.kind === 'fork') {
      const incoming = edges.find((edge) => edge.target === node.id);
      if (!incoming) return;
      const parent = nodeById.get(incoming.source);
      const parentPos = posMap.get(incoming.source);
      if (!parent || !parentPos) return;
      const parentSize = getNodeSize(parent);
      posMap.set(node.id, {
        x: parentPos.x + parentSize.width / 2 - GRAPH_JUNCTION_SIZE / 2,
        y: pos.y,
      });

      return;
    }

    const outgoing = edges.find((edge) => edge.source === node.id);
    if (!outgoing) return;
    const child = nodeById.get(outgoing.target);
    const childPos = posMap.get(outgoing.target);
    if (!child || !childPos) return;
    const childSize = getNodeSize(child);
    posMap.set(node.id, {
      x: childPos.x + childSize.width / 2 - GRAPH_JUNCTION_SIZE / 2,
      y: pos.y,
    });
  });
}

export function applyDagreLayout(nodes: TGraphNode[], edges: TGraphEdge[]): TGraphNode[] {
  if (nodes.length === 0) return nodes;

  const nodeById = new Map(nodes.map((node) => [node.id, node]));
  const levels = computeLevels(nodes, edges);
  const byLevel = new Map<number, string[]>();

  nodes.forEach((n) => {
    const level = levels.get(n.id) ?? 0;

    if (!byLevel.has(level)) byLevel.set(level, []);
    byLevel.get(level)!.push(n.id);
  });

  const sortedLevels = [...byLevel.keys()].sort((a, b) => a - b);
  let maxRowWidth = 0;

  sortedLevels.forEach((level) => {
    const nodesAtLevel = byLevel.get(level) ?? [];
    const rowWidth = nodesAtLevel.reduce((sum, nodeId, idx) => {
      const size = getNodeSize(nodeById.get(nodeId)!);

      return sum + size.width + (idx > 0 ? HORIZONTAL_GAP : 0);
    }, 0);

    if (rowWidth > maxRowWidth) maxRowWidth = rowWidth;
  });

  const posMap = new Map<string, { x: number; y: number }>();
  let currentY = 0;

  sortedLevels.forEach((level, levelIndex) => {
    const nodesAtLevel = byLevel.get(level) ?? [];
    const sizes = nodesAtLevel.map((nodeId) => getNodeSize(nodeById.get(nodeId)!));
    const rowHeight = Math.max(...sizes.map((size) => size.height));
    const rowWidth = sizes.reduce((sum, size, idx) => sum + size.width + (idx > 0 ? HORIZONTAL_GAP : 0), 0);
    const startX = (maxRowWidth - rowWidth) / 2;
    let offsetX = startX;

    nodesAtLevel.forEach((nodeId, idx) => {
      posMap.set(nodeId, {
        x: offsetX,
        y: currentY + (rowHeight - sizes[idx].height) / 2,
      });
      offsetX += sizes[idx].width + HORIZONTAL_GAP;
    });

    const nextLevelIds = sortedLevels[levelIndex + 1] != null ? byLevel.get(sortedLevels[levelIndex + 1]) ?? [] : [];
    const currentIsJunction = nodesAtLevel.every((id) => nodeById.get(id)?.type === EGraphNodeType.Junction);
    const nextIsJunction = nextLevelIds.length > 0
      && nextLevelIds.every((id) => nodeById.get(id)?.type === EGraphNodeType.Junction);
    const gap = currentIsJunction || nextIsJunction ? JUNCTION_GAP : VERTICAL_GAP;
    currentY += rowHeight + (nextLevelIds.length > 0 ? gap : 0);
  });

  snapJunctionX(nodes, edges, posMap);

  return nodes.map((node) => {
    const size = getNodeSize(node);

    return {
      ...node,
      position: posMap.get(node.id) ?? node.position,
      width: size.width,
      height: size.height,
      style: {
        ...node.style,
        width: size.width,
        height: size.height,
      },
    };
  });
}
