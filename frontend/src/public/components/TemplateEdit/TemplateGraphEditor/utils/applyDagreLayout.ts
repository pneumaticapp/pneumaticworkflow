import { EGraphNodeType, TGraphNode, TGraphEdge } from '../types';
import { assignSpineLanes } from './assignSpineLanes';
import { isStemGraphEdge } from './edgeStyles';
import {
  GRAPH_JUNCTION_SIZE,
  GRAPH_LANE_PITCH,
  GRAPH_NODE_HEIGHT,
  GRAPH_NODE_WIDTH,
  GRAPH_ROW_GAP,
  isCardNode,
} from './graphGeometry';
import { alignJunctionNodes } from './alignJunctionNodes';

export { GRAPH_JUNCTION_SIZE, GRAPH_NODE_HEIGHT, GRAPH_NODE_WIDTH } from './graphGeometry';

const LANE_PITCH = GRAPH_LANE_PITCH;
const CARD_ROW_PITCH = GRAPH_NODE_HEIGHT + GRAPH_ROW_GAP;

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

/**
 * Nesting depth of cards: a junction does not add a row.
 * Sibling cards of the same depth share a Y, so a side branch cannot sit
 * on the fork's gap and stretch the line to a child on the next row.
 */
export function computeLevels(nodes: TGraphNode[], edges: TGraphEdge[]): Map<string, number> {
  const nodeById = new Map(nodes.map((node) => [node.id, node]));
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
      const successor = nodeById.get(successorId);
      const step = successor && isCardNode(successor) ? 1 : 0;
      const nextLevel = currentLevel + step;
      const existingLevel = levels.get(successorId) ?? -1;

      if (nextLevel > existingLevel) {
        levels.set(successorId, nextLevel);
        queue.push(successorId);
      }
    });
  }

  nodes.forEach((n) => {
    if (!levels.has(n.id)) levels.set(n.id, 0);
  });

  return levels;
}

export function applyDagreLayout(nodes: TGraphNode[], edges: TGraphEdge[]): TGraphNode[] {
  if (nodes.length === 0) return nodes;

  const stemEdges = edges.filter(isStemGraphEdge);
  const levels = computeLevels(nodes, stemEdges);
  const lanes = assignSpineLanes(nodes, edges, levels);
  const posMap = new Map<string, { x: number; y: number }>();

  nodes.forEach((node) => {
    if (!isCardNode(node)) {
      return;
    }

    const size = getNodeSize(node);
    const lane = lanes.get(node.id) ?? 0;
    const depth = levels.get(node.id) ?? 0;

    posMap.set(node.id, {
      x: lane * LANE_PITCH - size.width / 2,
      y: depth * CARD_ROW_PITCH,
    });
  });

  const minX = [...posMap.values()].reduce((min, point) => Math.min(min, point.x), 0);
  if (minX !== 0) {
    posMap.forEach((point) => {
      point.x -= minX;
    });
  }

  const positionedNodes = nodes.map((node) => {
    const size = getNodeSize(node);

    return {
      ...node,
      position: posMap.get(node.id) ?? { x: 0, y: 0 },
      width: size.width,
      height: size.height,
      style: {
        ...node.style,
        width: size.width,
        height: size.height,
      },
    };
  });

  return alignJunctionNodes(positionedNodes, stemEdges);
}
