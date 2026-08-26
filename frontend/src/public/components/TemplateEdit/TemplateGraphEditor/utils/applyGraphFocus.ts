import { TGraphEdge, TGraphEdgeFocus, TGraphNode } from '../types';
import {
  EDGE_STYLE_CONDITIONAL_FOCUSED,
  EDGE_STYLE_FOCUSED,
  GRAPH_EDGE_CLASS_CONDITIONAL,
  isConditionalGraphEdge,
} from './edgeStyles';

export const GRAPH_DIMMED_CLASS = 'graph-item--dimmed';
export const GRAPH_FOCUSED_CLASS = 'graph-item--focused';
export const GRAPH_HIGHLIGHTED_EDGE_CLASS = 'graph-item--highlighted';

type TWalkDirection = 'upstream' | 'downstream';

interface IEdgeIndex {
  incoming: Map<string, TGraphEdge[]>;
  outgoing: Map<string, TGraphEdge[]>;
}

function indexEdges(edges: TGraphEdge[]): IEdgeIndex {
  const incoming = new Map<string, TGraphEdge[]>();
  const outgoing = new Map<string, TGraphEdge[]>();

  edges.forEach((edge) => {
    const outgoingList = outgoing.get(edge.source) ?? [];
    outgoingList.push(edge);
    outgoing.set(edge.source, outgoingList);

    const incomingList = incoming.get(edge.target) ?? [];
    incomingList.push(edge);
    incoming.set(edge.target, incomingList);
  });

  return { incoming, outgoing };
}

function walkDependencyPath(
  startId: string,
  direction: TWalkDirection,
  index: IEdgeIndex,
  nodeIds: Set<string>,
  edgeIds: Set<string>,
): void {
  const queue = [startId];
  const visited = new Set<string>([startId]);

  while (queue.length > 0) {
    const currentId = queue.shift();
    if (!currentId) {
      break;
    }

    let nextEdges = index.incoming.get(currentId) ?? [];
    if (direction === 'downstream') {
      nextEdges = index.outgoing.get(currentId) ?? [];
    }

    nextEdges.forEach((edge) => {
      edgeIds.add(edge.id);
      const nextId = direction === 'downstream' ? edge.target : edge.source;
      nodeIds.add(nextId);

      if (visited.has(nextId)) {
        return;
      }

      visited.add(nextId);
      queue.push(nextId);
    });
  }
}

export function collectFocusIds(
  nodes: TGraphNode[],
  edges: TGraphEdge[],
  focusedId: string,
): { nodeIds: Set<string>; edgeIds: Set<string> } {
  const hasFocusedNode = nodes.some((node) => node.id === focusedId);
  if (!hasFocusedNode) {
    return { nodeIds: new Set<string>(), edgeIds: new Set<string>() };
  }

  const nodeIds = new Set<string>([focusedId]);
  const edgeIds = new Set<string>();
  const index = indexEdges(edges);

  walkDependencyPath(focusedId, 'downstream', index, nodeIds, edgeIds);
  walkDependencyPath(focusedId, 'upstream', index, nodeIds, edgeIds);

  return { nodeIds, edgeIds };
}

function getNodeFocusClass(nodeId: string, focusedId: string, nodeIds: Set<string>): string {
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
      const isConditional = isConditionalGraphEdge(edge);
      const focusClass = isHighlighted ? GRAPH_HIGHLIGHTED_EDGE_CLASS : GRAPH_DIMMED_CLASS;
      const focus: TGraphEdgeFocus = isHighlighted ? 'highlighted' : 'dimmed';

      return {
        ...edge,
        className: [isConditional ? GRAPH_EDGE_CLASS_CONDITIONAL : undefined, focusClass]
          .filter(Boolean)
          .join(' '),
        // Labels live outside the edge element, so they follow the state through the edge data.
        data: { ...edge.data, focus },
        style: isHighlighted
          ? {
            ...edge.style,
            ...(isConditional ? EDGE_STYLE_CONDITIONAL_FOCUSED : EDGE_STYLE_FOCUSED),
          }
          : edge.style,
      };
    }),
  };
}
