import { GRAPH_SHOWCASE_TEMPLATE } from '../../fixtures/graphShowcaseTemplate';
import { EGraphNodeType } from '../../types';
import { buildTemplateGraph } from '../buildTemplateGraph';
import { GRAPH_JUNCTION_SIZE, GRAPH_NODE_WIDTH } from '../graphGeometry';

describe('applyStoredPositions', () => {
  it('should merge stored card positions into the automatic layout', () => {
    const graph = buildTemplateGraph(GRAPH_SHOWCASE_TEMPLATE, {
      'task-linear': { x: 750, y: 420 },
      missing: { x: 1, y: 2 },
    });

    expect(graph.nodes.find((node) => node.id === 'task-linear')?.position).toEqual({ x: 750, y: 420 });
    expect(graph.nodes.some((node) => node.id === 'missing')).toBe(false);
    expect(graph.nodes.find((node) => node.id === 'task-skippable')?.position).toBeDefined();
  });

  it('should ignore stored positions for junction nodes', () => {
    const initialGraph = buildTemplateGraph(GRAPH_SHOWCASE_TEMPLATE);
    const junction = initialGraph.nodes.find((node) => node.type === EGraphNodeType.Junction);

    expect(junction).toBeDefined();

    const graph = buildTemplateGraph(GRAPH_SHOWCASE_TEMPLATE, {
      [junction!.id]: { x: 999, y: 999 },
    });

    expect(graph.nodes.find((node) => node.id === junction!.id)?.position).toEqual(junction!.position);
  });

  it('should align a fork junction with its moved parent card', () => {
    const movedX = 600;
    const graph = buildTemplateGraph(GRAPH_SHOWCASE_TEMPLATE, {
      'task-url-title': { x: movedX, y: 500 },
    });
    const forkEdge = graph.edges.find((edge) => edge.source === 'task-url-title'
      && graph.nodes.find((node) => node.id === edge.target)?.type === EGraphNodeType.Junction);
    const fork = graph.nodes.find((node) => node.id === forkEdge?.target);

    expect(fork?.position.x).toBe(movedX + GRAPH_NODE_WIDTH / 2 - GRAPH_JUNCTION_SIZE / 2);
  });

  it('should recalculate edge anchors after applying a stored position', () => {
    const graph = buildTemplateGraph(GRAPH_SHOWCASE_TEMPLATE, {
      'task-linear': { x: 1_000, y: 300 },
    });
    const incomingEdge = graph.edges.find((edge) => edge.target === 'task-linear');

    expect(incomingEdge?.data?.pathKind).not.toBe('straight');
  });
});
