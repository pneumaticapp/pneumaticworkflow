import { EGraphNodeType, IGraphInsertTaskIntent, TGraphEdge, TGraphNode } from '../types';
import { isStemGraphEdge } from './edgeStyles';
import { isCardNode } from './graphGeometry';
import { KICKOFF_NODE_ID } from './graphConstants';

type TWalkDirection = 'up' | 'down';

interface IGrayIndex {
  incoming: Map<string, TGraphEdge[]>;
  outgoing: Map<string, TGraphEdge[]>;
}

function indexGrayEdges(edges: TGraphEdge[]): IGrayIndex {
  const incoming = new Map<string, TGraphEdge[]>();
  const outgoing = new Map<string, TGraphEdge[]>();

  edges.forEach((edge) => {
    if (!isStemGraphEdge(edge)) {
      return;
    }

    const outgoingList = outgoing.get(edge.source) ?? [];
    outgoingList.push(edge);
    outgoing.set(edge.source, outgoingList);

    const incomingList = incoming.get(edge.target) ?? [];
    incomingList.push(edge);
    incoming.set(edge.target, incomingList);
  });

  return { incoming, outgoing };
}

function neighborIds(edges: TGraphEdge[], walk: TWalkDirection): string[] {
  if (walk === 'up') {
    return edges.map((edge) => edge.source);
  }

  return edges.map((edge) => edge.target);
}

export function resolveStemCard(
  nodeId: string,
  nodesById: Map<string, TGraphNode>,
  index: IGrayIndex,
  walk: TWalkDirection,
  seen: Set<string> = new Set(),
): string | null {
  if (seen.has(nodeId)) {
    return null;
  }

  seen.add(nodeId);

  const node = nodesById.get(nodeId);
  if (!node) {
    return null;
  }

  if (isCardNode(node)) {
    return node.id;
  }

  const adjacent = walk === 'up'
    ? index.incoming.get(nodeId) ?? []
    : index.outgoing.get(nodeId) ?? [];
  const nextIds = neighborIds(adjacent, walk);

  if (nextIds.length !== 1) {
    return null;
  }

  return resolveStemCard(nextIds[0], nodesById, index, walk, seen);
}

export function resolveInsertEndpoints(
  edge: TGraphEdge,
  nodesById: Map<string, TGraphNode>,
  index: IGrayIndex,
): IGraphInsertTaskIntent | null {
  if (!isStemGraphEdge(edge)) {
    return null;
  }

  const afterId = resolveStemCard(edge.source, nodesById, index, 'up');
  const beforeId = resolveStemCard(edge.target, nodesById, index, 'down');

  if (!afterId || !beforeId || afterId === beforeId) {
    return null;
  }

  if (beforeId === KICKOFF_NODE_ID) {
    return null;
  }

  return {
    kind: 'insert',
    afterId,
    beforeId,
  };
}

export function applyGraphAddAffordances(
  nodes: TGraphNode[],
  edges: TGraphEdge[],
): { nodes: TGraphNode[]; edges: TGraphEdge[] } {
  const nodesById = new Map(nodes.map((node) => [node.id, node]));
  const index = indexGrayEdges(edges);

  const nextNodes: TGraphNode[] = nodes.map((node) => {
    if (!isCardNode(node)) {
      return node;
    }

    const outgoing = index.outgoing.get(node.id) ?? [];
    if (outgoing.length > 0) {
      return node;
    }

    const addTaskIntent = { kind: 'continue' as const, afterId: node.id };

    if (node.type === EGraphNodeType.Task) {
      return {
        ...node,
        data: {
          ...node.data,
          addTaskIntent,
        },
      };
    }

    if (node.type === EGraphNodeType.Kickoff) {
      return {
        ...node,
        data: {
          ...node.data,
          addTaskIntent,
        },
      };
    }

    return node;
  });

  const nextEdges: TGraphEdge[] = edges.map((edge) => {
    const addTaskIntent = resolveInsertEndpoints(edge, nodesById, index);
    if (!addTaskIntent) {
      return edge;
    }

    return {
      ...edge,
      data: {
        ...edge.data,
        addTaskIntent,
      },
    };
  });

  return { nodes: nextNodes, edges: nextEdges };
}
