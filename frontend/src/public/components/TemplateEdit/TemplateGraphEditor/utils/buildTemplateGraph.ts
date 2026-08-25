import { ITemplateClient } from '../../../../types/template';
import { IGraphState, TGraphNodePositions } from '../types';
import { applyDagreLayout } from './applyDagreLayout';
import { applyStoredPositions } from './applyStoredPositions';
import { routeGraph } from './routeGraph';
import { templateToGraph } from './templateToGraph';

/**
 * 1. Topology: cards and start-after edges, plus fork/join nodes.
 * 2. Layout: rank the DAG, then overlay saved card positions.
 * 3. Route: align junctions, pick handles and orthogonal / detour paths.
 */
export function buildTemplateGraph(
  template: ITemplateClient,
  storedPositions: TGraphNodePositions = {},
): IGraphState {
  const { nodes: topologyNodes, edges: topologyEdges } = templateToGraph(template);
  const autoLayoutNodes = applyDagreLayout(topologyNodes, topologyEdges);
  const positionedNodes = applyStoredPositions(autoLayoutNodes, topologyEdges, storedPositions);

  return routeGraph(positionedNodes, topologyEdges);
}
