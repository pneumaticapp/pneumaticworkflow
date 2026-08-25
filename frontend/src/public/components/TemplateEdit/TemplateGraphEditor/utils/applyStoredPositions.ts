import { TGraphEdge, TGraphNode, TGraphNodePositions } from '../types';
import { alignJunctionNodes } from './alignJunctionNodes';
import { isCardNode } from './graphGeometry';

export { alignJunctionNodes } from './alignJunctionNodes';

export function applyStoredPositions(
  nodes: TGraphNode[],
  edges: TGraphEdge[],
  positions: TGraphNodePositions,
): TGraphNode[] {
  const positionedNodes = nodes.map((node) => {
    const storedPosition = isCardNode(node) ? positions[node.id] : undefined;

    return storedPosition ? { ...node, position: storedPosition } : node;
  });

  return alignJunctionNodes(positionedNodes, edges);
}
