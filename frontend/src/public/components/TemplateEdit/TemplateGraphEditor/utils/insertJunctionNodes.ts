import { EGraphNodeType, IGraphState, TGraphEdge, TGraphNode, TJunctionKind } from '../types';
import { GRAPH_JUNCTION_SIZE } from './applyDagreLayout';
import { EDGE_STYLE_DEFAULT, GRAPH_EDGE_CLASS_SKIP, isSkipGraphEdge } from './edgeStyles';

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

function createPlainEdge(source: string, target: string, suffix: string): TGraphEdge {
  return {
    id: `edge-${source}-${target}-${suffix}`,
    source,
    target,
    sourceHandle: 'source-bottom',
    targetHandle: 'target-top',
    type: 'smoothstep',
    data: { isConditional: false },
    labelShowBg: false,
    style: EDGE_STYLE_DEFAULT,
  };
}

function groupBy(edges: TGraphEdge[], key: 'source' | 'target'): Map<string, TGraphEdge[]> {
  const map = new Map<string, TGraphEdge[]>();

  edges.forEach((edge) => {
    const id = edge[key];
    const list = map.get(id) ?? [];
    list.push(edge);
    map.set(id, list);
  });

  return map;
}

export function insertJunctionNodes(nodes: TGraphNode[], edges: TGraphEdge[]): IGraphState {
  const outgoing = groupBy(edges, 'source');
  const incoming = groupBy(edges, 'target');
  const forkBySource = new Map<string, string>();
  const joinByTarget = new Map<string, string>();
  const junctionNodes: TGraphNode[] = [];

  outgoing.forEach((list, sourceId) => {
    if (list.length < 2) return;
    const forkId = `junction-fork-${sourceId}`;
    forkBySource.set(sourceId, forkId);
    junctionNodes.push(createJunctionNode(forkId, 'fork'));
  });

  incoming.forEach((list, targetId) => {
    if (list.length < 2) return;
    const joinId = `junction-join-${targetId}`;
    joinByTarget.set(targetId, joinId);
    junctionNodes.push(createJunctionNode(joinId, 'join'));
  });

  if (junctionNodes.length === 0) {
    return { nodes, edges };
  }

  const nextEdges: TGraphEdge[] = [];

  forkBySource.forEach((forkId, sourceId) => {
    nextEdges.push(createPlainEdge(sourceId, forkId, 'out'));
  });

  joinByTarget.forEach((joinId, targetId) => {
    const originals = incoming.get(targetId) ?? [];
    const summaryEdge = originals.find((edge) => edge.data?.summary && !isSkipGraphEdge(edge));
    nextEdges.push({
      ...createPlainEdge(joinId, targetId, 'in'),
      data: summaryEdge?.data ?? { isConditional: false },
      style: EDGE_STYLE_DEFAULT,
    });
  });

  edges.forEach((edge) => {
    const source = forkBySource.get(edge.source) ?? edge.source;
    const target = joinByTarget.get(edge.target) ?? edge.target;
    const isSkip = isSkipGraphEdge(edge);
    const isJoinInbound = joinByTarget.has(edge.target) && !isSkip;

    nextEdges.push({
      ...edge,
      source,
      target,
      sourceHandle: 'source-bottom',
      targetHandle: 'target-top',
      className: isSkip ? GRAPH_EDGE_CLASS_SKIP : edge.className,
      data: isJoinInbound ? { isConditional: false } : edge.data,
      style: isJoinInbound ? EDGE_STYLE_DEFAULT : edge.style,
    });
  });

  return {
    nodes: [...nodes, ...junctionNodes],
    edges: nextEdges,
  };
}
