import { IGraphState, TGraphEdge, TGraphNode } from '../types';
import { getGraphEdgeVisual, isConditionalGraphEdge } from './edgeStyles';
import { CHECK_IF_FORK_PREFIX, CHECK_IF_JOIN_PREFIX } from './graphConstants';
import { GRAPH_EDGE_Z_INDEX, isCardNode } from './graphGeometry';
import { createJunctionNode } from './insertJunctionNodes';

function joinIdForCheckIf(cardId: string): string {
  return `${CHECK_IF_JOIN_PREFIX}${cardId}`;
}

function forkIdForCheckIf(sourceId: string): string {
  return `${CHECK_IF_FORK_PREFIX}${sourceId}`;
}

function createCheckIfEdge(source: string, target: string, suffix: string): TGraphEdge {
  return {
    id: `edge-${source}-${target}-checkif-${suffix}`,
    source,
    target,
    type: 'smoothstep',
    zIndex: GRAPH_EDGE_Z_INDEX,
    data: { isConditional: true },
    labelShowBg: false,
    ...getGraphEdgeVisual(true),
  };
}

function attachIncomingJoins(
  nodes: TGraphNode[],
  checkIfEdges: TGraphEdge[],
  cardIds: Set<string>,
): IGraphState {
  const leftover: TGraphEdge[] = [];
  const byTarget = new Map<string, TGraphEdge[]>();

  checkIfEdges.forEach((edge) => {
    if (!cardIds.has(edge.target)) {
      leftover.push(edge);

      return;
    }

    const list = byTarget.get(edge.target) ?? [];
    list.push(edge);
    byTarget.set(edge.target, list);
  });

  let nextNodes = [...nodes];
  const nextCheckIf: TGraphEdge[] = [...leftover];

  byTarget.forEach((list, cardId) => {
    if (list.length < 2) {
      nextCheckIf.push(...list);

      return;
    }

    const joinId = joinIdForCheckIf(cardId);
    nextNodes = [...nextNodes, createJunctionNode(joinId, 'join')];
    nextCheckIf.push(
      ...list.map((edge) => ({ ...edge, target: joinId })),
      createCheckIfEdge(joinId, cardId, 'in'),
    );
  });

  return { nodes: nextNodes, edges: nextCheckIf };
}

function attachOutgoingForks(
  nodes: TGraphNode[],
  edges: TGraphEdge[],
  cardIds: Set<string>,
): IGraphState {
  const bySource = new Map<string, TGraphEdge[]>();

  edges.forEach((edge) => {
    if (!isConditionalGraphEdge(edge) || !cardIds.has(edge.source)) {
      return;
    }

    const list = bySource.get(edge.source) ?? [];
    list.push(edge);
    bySource.set(edge.source, list);
  });

  let nextNodes = [...nodes];
  let nextEdges = [...edges];

  bySource.forEach((list, sourceId) => {
    if (list.length < 2) {
      return;
    }

    const forkId = forkIdForCheckIf(sourceId);
    const forkedIds = new Set(list.map((edge) => edge.id));
    nextNodes = [...nextNodes, createJunctionNode(forkId, 'fork')];
    nextEdges = [
      ...nextEdges.filter((edge) => !forkedIds.has(edge.id)),
      createCheckIfEdge(sourceId, forkId, 'out'),
      ...list.map((edge) => ({ ...edge, source: forkId })),
    ];
  });

  return { nodes: nextNodes, edges: nextEdges };
}

/**
 * Check If never shares a gray stem join. One line docks on the card side;
 * several lines to the same card meet at an orange-only join, then one stem.
 */
export function attachCheckIfJunctions(
  nodes: TGraphNode[],
  stemEdges: TGraphEdge[],
  checkIfEdges: TGraphEdge[],
): IGraphState {
  if (checkIfEdges.length === 0) {
    return { nodes, edges: stemEdges };
  }

  const cardIds = new Set(nodes.filter(isCardNode).map((node) => node.id));
  const joined = attachIncomingJoins(nodes, checkIfEdges, cardIds);

  return attachOutgoingForks(joined.nodes, [...stemEdges, ...joined.edges], cardIds);
}
