import { EGraphNodeType, TGraphEdge, TGraphNode } from '../types';
import { CHECK_IF_FORK_PREFIX, isCheckIfJunctionId } from './graphConstants';
import {
  GRAPH_JUNCTION_SIZE,
  GRAPH_ROW_GAP,
  GRAPH_SKIP_LANE_GAP,
  GRAPH_SKIP_LANE_STEP,
  IGraphNodeBox,
  getGraphNodeBox,
} from './graphGeometry';

function gapJunctionY(gapTop: number): number {
  return gapTop + (GRAPH_ROW_GAP - GRAPH_JUNCTION_SIZE) / 2;
}

function checkIfSideX(box: IGraphNodeBox, pullLeft: boolean): number {
  return pullLeft
    ? box.x - GRAPH_SKIP_LANE_GAP - GRAPH_JUNCTION_SIZE / 2
    : box.right + GRAPH_SKIP_LANE_GAP - GRAPH_JUNCTION_SIZE / 2;
}

function isXTaken(x: number, taken: number[]): boolean {
  const centerX = x + GRAPH_JUNCTION_SIZE / 2;

  return taken.some((takenX) => Math.abs(takenX - centerX) < GRAPH_SKIP_LANE_STEP);
}

function placeCheckIfJunction(
  box: IGraphNodeBox,
  pull: number,
  takenXs: number[],
): { x: number; y: number } {
  const pullLeft = pull < 0;
  let x = checkIfSideX(box, pullLeft);

  if (isXTaken(x, takenXs)) {
    x = checkIfSideX(box, !pullLeft);
  }

  return {
    x,
    y: box.centerY - GRAPH_JUNCTION_SIZE / 2,
  };
}

export function alignJunctionNodes(nodes: TGraphNode[], edges: TGraphEdge[]): TGraphNode[] {
  const nodeById = new Map(nodes.map((node) => [node.id, node]));
  const forkXs: number[] = [];

  const withForks = nodes.map((node) => {
    if (node.type !== EGraphNodeType.Junction || !node.id.startsWith(CHECK_IF_FORK_PREFIX)) {
      return node;
    }

    const anchorEdge = edges.find((edge) => edge.target === node.id);
    const anchorNode = anchorEdge ? nodeById.get(anchorEdge.source) : undefined;

    if (!anchorNode) {
      return node;
    }

    const box = getGraphNodeBox(anchorNode);
    const pullEdges = edges.filter((edge) => edge.source === node.id);
    const pull = pullEdges.reduce((sum, edge) => {
      const peer = nodeById.get(edge.target);

      return sum + ((peer ? getGraphNodeBox(peer).centerX : box.centerX) - box.centerX);
    }, 0);
    const position = placeCheckIfJunction(box, pull, forkXs);
    forkXs.push(position.x + GRAPH_JUNCTION_SIZE / 2);

    return { ...node, position };
  });

  return withForks.map((node) => {
    if (node.type !== EGraphNodeType.Junction) {
      return node;
    }

    if (node.id.startsWith(CHECK_IF_FORK_PREFIX)) {
      return node;
    }

    const anchorEdge = node.data.kind === 'fork'
      ? edges.find((edge) => edge.target === node.id)
      : edges.find((edge) => edge.source === node.id);
    const anchorNodeId = node.data.kind === 'fork' ? anchorEdge?.source : anchorEdge?.target;
    const anchorNode = anchorNodeId ? nodeById.get(anchorNodeId) : undefined;

    if (!anchorNode) {
      return node;
    }

    const box = getGraphNodeBox(anchorNode);

    if (isCheckIfJunctionId(node.id)) {
      const pullEdges = edges.filter((edge) => edge.target === node.id);
      const pull = pullEdges.reduce((sum, edge) => {
        const peer = nodeById.get(edge.source);

        return sum + ((peer ? getGraphNodeBox(peer).centerX : box.centerX) - box.centerX);
      }, 0);

      return {
        ...node,
        position: placeCheckIfJunction(box, pull, forkXs),
      };
    }

    const y = node.data.kind === 'fork'
      ? gapJunctionY(box.bottom)
      : gapJunctionY(box.y - GRAPH_ROW_GAP);
    const x = box.centerX - GRAPH_JUNCTION_SIZE / 2;

    return {
      ...node,
      position: { x, y },
    };
  });
}
