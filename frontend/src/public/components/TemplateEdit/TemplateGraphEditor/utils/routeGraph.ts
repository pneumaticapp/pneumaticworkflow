import { Node } from 'reactflow';
import { IGraphState, TGraphEdge, TGraphNode } from '../types';
import { alignJunctionNodes } from './alignJunctionNodes';
import { applyConnectedHandles } from './applyConnectedHandles';
import { applyEdgeAnchors } from './applyEdgeAnchors';

/**
 * Positions junctions, then picks handles, orthogonal paths and side-lane detours.
 * Topology (which cards exist and how they connect) must already be in `nodes` / `edges`.
 */
export function routeGraph(nodes: TGraphNode[], edges: TGraphEdge[]): IGraphState {
  const positionedNodes = alignJunctionNodes(nodes, edges);
  const anchoredEdges = applyEdgeAnchors(positionedNodes, edges);

  return applyConnectedHandles({ nodes: positionedNodes, edges: anchoredEdges });
}

export function applyMovedCard(
  nodes: TGraphNode[],
  edges: TGraphEdge[],
  movedNode: Node,
): IGraphState {
  const nextNodes = nodes.map((node) => (
    node.id === movedNode.id
      ? {
        ...node,
        position: movedNode.position,
        dragging: movedNode.dragging,
        width: movedNode.width ?? node.width,
        height: movedNode.height ?? node.height,
      }
      : node
  ));

  return routeGraph(nextNodes, edges);
}
