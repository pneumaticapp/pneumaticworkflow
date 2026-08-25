import { EGraphNodeType, TGraphEdge, TGraphNode } from '../types';
import { GRAPH_JUNCTION_SIZE, GRAPH_ROW_GAP, getGraphNodeBox } from './graphGeometry';

function gapJunctionY(gapTop: number): number {
  return gapTop + (GRAPH_ROW_GAP - GRAPH_JUNCTION_SIZE) / 2;
}

export function alignJunctionNodes(nodes: TGraphNode[], edges: TGraphEdge[]): TGraphNode[] {
  const nodeById = new Map(nodes.map((node) => [node.id, node]));

  return nodes.map((node) => {
    if (node.type !== EGraphNodeType.Junction) {
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
    const y = node.data.kind === 'fork'
      ? gapJunctionY(box.bottom)
      : gapJunctionY(box.y - GRAPH_ROW_GAP);

    return {
      ...node,
      position: {
        x: box.centerX - GRAPH_JUNCTION_SIZE / 2,
        y,
      },
    };
  });
}
