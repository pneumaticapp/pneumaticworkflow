import { EGraphNodeType, TGraphEdge, TGraphNode } from '../types';
import {
  EDGE_STYLE_FOCUSED,
  EDGE_STYLE_SKIP_FOCUSED,
  GRAPH_EDGE_CLASS_SKIP,
  isSkipGraphEdge,
} from './edgeStyles';

export const GRAPH_DIMMED_CLASS = 'graph-item--dimmed';
export const GRAPH_FOCUSED_CLASS = 'graph-item--focused';
export const GRAPH_HIGHLIGHTED_EDGE_CLASS = 'graph-item--highlighted';

export function collectFocusIds(
  nodes: TGraphNode[],
  edges: TGraphEdge[],
  focusedId: string,
): { nodeIds: Set<string>; edgeIds: Set<string> } {
  const junctionIds = new Set(
    nodes.filter((node) => node.type === EGraphNodeType.Junction).map((node) => node.id),
  );
  const nodeIds = new Set<string>([focusedId]);
  const edgeIds = new Set<string>();
  const queue = [focusedId];

  while (queue.length > 0) {
    const current = queue.shift()!;

    edges.forEach((edge) => {
      if (edge.source !== current && edge.target !== current) return;
      if (edgeIds.has(edge.id)) return;

      edgeIds.add(edge.id);
      const other = edge.source === current ? edge.target : edge.source;

      if (nodeIds.has(other)) return;
      nodeIds.add(other);

      if (junctionIds.has(other)) {
        queue.push(other);
      }
    });
  }

  return { nodeIds, edgeIds };
}

function getNodeFocusClass(
  nodeId: string,
  focusedId: string,
  nodeIds: Set<string>,
): string {
  if (nodeId === focusedId) {
    return GRAPH_FOCUSED_CLASS;
  }

  if (nodeIds.has(nodeId)) {
    return '';
  }

  return GRAPH_DIMMED_CLASS;
}

export function applyGraphFocus(
  nodes: TGraphNode[],
  edges: TGraphEdge[],
  focusedId: string | null,
): { nodes: TGraphNode[]; edges: TGraphEdge[] } {
  if (!focusedId) {
    return { nodes, edges };
  }

  const { nodeIds, edgeIds } = collectFocusIds(nodes, edges, focusedId);

  return {
    nodes: nodes.map((node) => ({
      ...node,
      className: getNodeFocusClass(node.id, focusedId, nodeIds),
    })),
    edges: edges.map((edge) => {
      const isHighlighted = edgeIds.has(edge.id);
      const isSkip = isSkipGraphEdge(edge);
      const focusClass = isHighlighted ? GRAPH_HIGHLIGHTED_EDGE_CLASS : GRAPH_DIMMED_CLASS;

      return {
        ...edge,
        className: [isSkip ? GRAPH_EDGE_CLASS_SKIP : undefined, focusClass].filter(Boolean).join(' '),
        zIndex: isHighlighted ? 1001 : edge.zIndex,
        style: isHighlighted
          ? {
            ...edge.style,
            ...(isSkip ? EDGE_STYLE_SKIP_FOCUSED : EDGE_STYLE_FOCUSED),
          }
          : edge.style,
      };
    }),
  };
}
