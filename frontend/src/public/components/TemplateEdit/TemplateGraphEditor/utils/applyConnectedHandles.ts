import {
  EGraphNodeType,
  IConnectedHandles,
  IGraphState,
  TGraphEdge,
  TGraphNode,
  TKickoffNode,
  TTaskNode,
} from '../types';

export const EMPTY_CONNECTED_HANDLES: IConnectedHandles = {
  hasTargetTop: false,
  hasSourceBottom: false,
  hasSourceSkip: false,
  hasTargetSkip: false,
};

export function collectConnectedHandles(nodeId: string, edges: TGraphEdge[]): IConnectedHandles {
  return edges.reduce<IConnectedHandles>((handles, edge) => {
    if (edge.source === nodeId) {
      if (edge.sourceHandle === 'source-skip') {
        return { ...handles, hasSourceSkip: true };
      }

      return { ...handles, hasSourceBottom: true };
    }

    if (edge.target === nodeId) {
      if (edge.targetHandle === 'target-skip') {
        return { ...handles, hasTargetSkip: true };
      }

      return { ...handles, hasTargetTop: true };
    }

    return handles;
  }, { ...EMPTY_CONNECTED_HANDLES });
}

function withConnectedHandles<TNode extends TTaskNode | TKickoffNode>(
  node: TNode,
  edges: TGraphEdge[],
): TNode {
  return {
    ...node,
    data: {
      ...node.data,
      handles: collectConnectedHandles(node.id, edges),
    },
  };
}

export function applyConnectedHandles({ nodes, edges }: IGraphState): IGraphState {
  const nextNodes: TGraphNode[] = nodes.map((node) => {
    if (node.type === EGraphNodeType.Kickoff) {
      return withConnectedHandles(node as TKickoffNode, edges);
    }

    if (node.type === EGraphNodeType.Task) {
      return withConnectedHandles(node as TTaskNode, edges);
    }

    return node;
  });

  return { nodes: nextNodes, edges };
}
