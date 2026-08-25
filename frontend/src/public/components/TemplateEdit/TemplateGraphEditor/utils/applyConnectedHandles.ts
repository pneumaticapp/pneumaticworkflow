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
  hasTargetBottom: false,
  hasTargetLeft: false,
  hasTargetRight: false,
  hasSourceTop: false,
  hasSourceBottom: false,
  hasSourceLeft: false,
  hasSourceRight: false,
};

const SOURCE_HANDLE_FLAGS: Record<string, keyof IConnectedHandles> = {
  'source-top': 'hasSourceTop',
  'source-bottom': 'hasSourceBottom',
  'source-left': 'hasSourceLeft',
  'source-right': 'hasSourceRight',
  'source-skip': 'hasSourceRight',
};

const TARGET_HANDLE_FLAGS: Record<string, keyof IConnectedHandles> = {
  'target-top': 'hasTargetTop',
  'target-bottom': 'hasTargetBottom',
  'target-left': 'hasTargetLeft',
  'target-right': 'hasTargetRight',
  'target-skip': 'hasTargetRight',
};

export function collectConnectedHandles(nodeId: string, edges: TGraphEdge[]): IConnectedHandles {
  return edges.reduce<IConnectedHandles>((handles, edge) => {
    if (edge.source === nodeId) {
      const flag = SOURCE_HANDLE_FLAGS[edge.sourceHandle ?? 'source-bottom'] ?? 'hasSourceBottom';

      return { ...handles, [flag]: true };
    }

    if (edge.target === nodeId) {
      const flag = TARGET_HANDLE_FLAGS[edge.targetHandle ?? 'target-top'] ?? 'hasTargetTop';

      return { ...handles, [flag]: true };
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
