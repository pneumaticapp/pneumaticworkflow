import { EGraphNodeType, IGraphState, TGraphEdge, TGraphNode, TJunctionKind } from '../types';
import { getGraphEdgeVisual } from './edgeStyles';
import { GRAPH_HANDLE, GRAPH_JUNCTION_SIZE } from './graphGeometry';

type TEdgeEndpoint = 'source' | 'target';

function createJunctionNode(id: string, kind: TJunctionKind): TGraphNode {
  return {
    id,
    type: EGraphNodeType.Junction,
    position: { x: 0, y: 0 },
    draggable: false,
    selectable: false,
    zIndex: 10,
    data: { kind },
    width: GRAPH_JUNCTION_SIZE,
    height: GRAPH_JUNCTION_SIZE,
    style: { width: GRAPH_JUNCTION_SIZE, height: GRAPH_JUNCTION_SIZE },
  };
}

function createStemEdge(source: string, target: string, suffix: string): TGraphEdge {
  return {
    id: `edge-${source}-${target}-${suffix}`,
    source,
    target,
    sourceHandle: GRAPH_HANDLE.SourceBottom,
    targetHandle: GRAPH_HANDLE.TargetTop,
    type: 'smoothstep',
    data: { isConditional: false },
    labelShowBg: false,
    ...getGraphEdgeVisual(false),
  };
}

function groupBy(edges: TGraphEdge[], key: TEdgeEndpoint): Map<string, TGraphEdge[]> {
  const map = new Map<string, TGraphEdge[]>();

  edges.forEach((edge) => {
    const id = edge[key];
    map.set(id, [...(map.get(id) ?? []), edge]);
  });

  return map;
}

function uniqueLabels(labels: string[]): string[] {
  const seen = new Set<string>();

  return labels.filter((label) => {
    if (seen.has(label)) {
      return false;
    }

    seen.add(label);

    return true;
  });
}

function withoutBadge(edge: TGraphEdge): TGraphEdge {
  const { summary, startAfter, ...restData } = edge.data ?? {};

  return { ...edge, data: restData };
}

/**
 * A card keeps a single vertical stem. Extra incoming or outgoing links meet at a
 * fork or join so the card itself never has two edges on the same handle.
 * The start-after badge sits on the first segment leaving a card, before any fork.
 */
export function insertJunctionNodes(nodes: TGraphNode[], edges: TGraphEdge[]): IGraphState {
  const outgoing = groupBy(edges, 'source');
  const incoming = groupBy(edges, 'target');
  const forkBySource = new Map<string, string>();
  const joinByTarget = new Map<string, string>();
  const junctionNodes: TGraphNode[] = [];

  outgoing.forEach((list, sourceId) => {
    if (list.length < 2) {
      return;
    }

    const forkId = `junction-fork-${sourceId}`;
    forkBySource.set(sourceId, forkId);
    junctionNodes.push(createJunctionNode(forkId, 'fork'));
  });

  incoming.forEach((list, targetId) => {
    if (list.length < 2) {
      return;
    }

    const joinId = `junction-join-${targetId}`;
    joinByTarget.set(targetId, joinId);
    junctionNodes.push(createJunctionNode(joinId, 'join'));
  });

  if (junctionNodes.length === 0) {
    return { nodes, edges };
  }

  const nextEdges: TGraphEdge[] = [];

  forkBySource.forEach((forkId, sourceId) => {
    const branches = outgoing.get(sourceId) ?? [];
    const startAfter = uniqueLabels(branches.flatMap((edge) => edge.data?.startAfter ?? []));
    const stem = createStemEdge(sourceId, forkId, 'out');

    nextEdges.push({ ...stem, data: { ...stem.data, startAfter } });
  });

  joinByTarget.forEach((joinId, targetId) => {
    nextEdges.push(createStemEdge(joinId, targetId, 'in'));
  });

  edges.forEach((edge) => {
    const forkId = forkBySource.get(edge.source);
    const joinId = joinByTarget.get(edge.target);
    const segment = forkId ? withoutBadge(edge) : edge;

    nextEdges.push({
      ...segment,
      source: forkId ?? edge.source,
      target: joinId ?? edge.target,
      sourceHandle: GRAPH_HANDLE.SourceBottom,
      targetHandle: GRAPH_HANDLE.TargetTop,
      ...getGraphEdgeVisual(false),
    });
  });

  return {
    nodes: [...nodes, ...junctionNodes],
    edges: nextEdges,
  };
}
