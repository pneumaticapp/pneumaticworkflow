import { GRAPH_SHOWCASE_TEMPLATE } from '../../fixtures/graphShowcaseTemplate';
import { EGraphNodeType, TGraphEdge, TGraphNode } from '../../types';
import { GRAPH_CARD_Z_INDEX } from '../graphGeometry';
import { KICKOFF_NODE_ID, templateToGraph } from '../templateToGraph';
import {
  applyGraphFocus,
  collectFocusIds,
  GRAPH_DIMMED_CLASS,
  GRAPH_FOCUSED_CLASS,
  GRAPH_HIGHLIGHTED_EDGE_CLASS,
} from '../applyGraphFocus';

function createNode(id: string, type: EGraphNodeType): TGraphNode {
  return {
    id,
    type,
    position: { x: 0, y: 0 },
    data: {},
  } as TGraphNode;
}

function createEdge(id: string, source: string, target: string): TGraphEdge {
  return { id, source, target };
}

describe('collectFocusIds', () => {
  const forkNodes: TGraphNode[] = [
    createNode('task-a', EGraphNodeType.Task),
    createNode('junction-fork-task-a', EGraphNodeType.Junction),
    createNode('task-b', EGraphNodeType.Task),
    createNode('task-c', EGraphNodeType.Task),
  ];
  const forkEdges: TGraphEdge[] = [
    createEdge('e1', 'task-a', 'junction-fork-task-a'),
    createEdge('e2', 'junction-fork-task-a', 'task-b'),
    createEdge('e3', 'junction-fork-task-a', 'task-c'),
  ];
  const joinNodes: TGraphNode[] = [
    createNode('task-a', EGraphNodeType.Task),
    createNode('task-b', EGraphNodeType.Task),
    createNode('junction-join-task-d', EGraphNodeType.Junction),
    createNode('task-d', EGraphNodeType.Task),
  ];
  const joinEdges: TGraphEdge[] = [
    createEdge('e1', 'task-a', 'junction-join-task-d'),
    createEdge('e2', 'task-b', 'junction-join-task-d'),
    createEdge('e3', 'junction-join-task-d', 'task-d'),
  ];

  it('should highlight every outgoing branch when the fork source is focused', () => {
    const { nodeIds, edgeIds } = collectFocusIds(forkNodes, forkEdges, 'task-a');

    expect(nodeIds).toEqual(new Set(['task-a', 'junction-fork-task-a', 'task-b', 'task-c']));
    expect(edgeIds).toEqual(new Set(['e1', 'e2', 'e3']));
  });

  it('should keep sibling fork branches dimmed when a branch card is focused', () => {
    const { nodeIds, edgeIds } = collectFocusIds(forkNodes, forkEdges, 'task-b');

    expect(nodeIds).toEqual(new Set(['task-b', 'junction-fork-task-a', 'task-a']));
    expect(edgeIds).toEqual(new Set(['e1', 'e2']));
  });

  it('should keep sibling join sources dimmed when one incoming card is focused', () => {
    const { nodeIds, edgeIds } = collectFocusIds(joinNodes, joinEdges, 'task-a');

    expect(nodeIds).toEqual(new Set(['task-a', 'junction-join-task-d', 'task-d']));
    expect(edgeIds).toEqual(new Set(['e1', 'e3']));
  });

  it('should highlight every incoming branch when the join target is focused', () => {
    const { nodeIds, edgeIds } = collectFocusIds(joinNodes, joinEdges, 'task-d');

    expect(nodeIds).toEqual(new Set(['task-d', 'junction-join-task-d', 'task-a', 'task-b']));
    expect(edgeIds).toEqual(new Set(['e1', 'e2', 'e3']));
  });

  it('should highlight the full ancestor and descendant chain, not only the next card', () => {
    const nodes: TGraphNode[] = [
      createNode('task-a', EGraphNodeType.Task),
      createNode('task-b', EGraphNodeType.Task),
      createNode('task-c', EGraphNodeType.Task),
    ];
    const edges: TGraphEdge[] = [
      createEdge('e1', 'task-a', 'task-b'),
      createEdge('e2', 'task-b', 'task-c'),
    ];

    const { nodeIds, edgeIds } = collectFocusIds(nodes, edges, 'task-a');

    expect(nodeIds).toEqual(new Set(['task-a', 'task-b', 'task-c']));
    expect(edgeIds).toEqual(new Set(['e1', 'e2']));
  });

  it('should walk both branches of a fork-then-join', () => {
    const nodes: TGraphNode[] = [
      createNode('task-a', EGraphNodeType.Task),
      createNode('junction-fork-task-a', EGraphNodeType.Junction),
      createNode('task-side', EGraphNodeType.Task),
      createNode('junction-join-task-b', EGraphNodeType.Junction),
      createNode('task-b', EGraphNodeType.Task),
    ];
    const edges: TGraphEdge[] = [
      createEdge('e-out', 'task-a', 'junction-fork-task-a'),
      createEdge('e-main', 'junction-fork-task-a', 'task-side'),
      createEdge('e-side', 'junction-fork-task-a', 'junction-join-task-b'),
      createEdge('e-from-side', 'task-side', 'junction-join-task-b'),
      createEdge('e-in', 'junction-join-task-b', 'task-b'),
    ];

    const { nodeIds } = collectFocusIds(nodes, edges, 'task-a');

    expect(nodeIds.has('task-side')).toBe(true);
    expect(nodeIds.has('task-b')).toBe(true);
  });

  it('should keep a parallel sibling dimmed on the showcase graph', () => {
    const { nodes, edges } = templateToGraph(GRAPH_SHOWCASE_TEMPLATE);
    const { nodeIds } = collectFocusIds(nodes, edges, 'task-parallel-a');

    expect(nodeIds.has('task-parallel-a')).toBe(true);
    expect(nodeIds.has('task-join')).toBe(true);
    expect(nodeIds.has('task-long-title')).toBe(true);
    expect(nodeIds.has('task-url-title')).toBe(true);
    expect(nodeIds.has(KICKOFF_NODE_ID)).toBe(true);
    expect(nodeIds.has('task-parallel-b')).toBe(false);
  });

  it('should keep a skippable task on the linear start-after chain', () => {
    const { nodes, edges } = templateToGraph(GRAPH_SHOWCASE_TEMPLATE);
    const { nodeIds } = collectFocusIds(nodes, edges, 'task-skippable');

    expect(nodeIds.has('task-linear')).toBe(true);
    expect(nodeIds.has('task-skippable')).toBe(true);
    expect(nodeIds.has('task-url-title')).toBe(true);
    expect(edges.some((edge) => edge.source === 'task-linear' && edge.target === 'task-url-title')).toBe(false);
  });

  it('should reach every card of the showcase graph from the first one', () => {
    const { nodes, edges } = templateToGraph(GRAPH_SHOWCASE_TEMPLATE);
    const { nodeIds } = collectFocusIds(nodes, edges, KICKOFF_NODE_ID);
    const cardIds = nodes
      .filter((node) => node.type !== EGraphNodeType.Junction)
      .map((node) => node.id);

    expect(cardIds.every((id) => nodeIds.has(id))).toBe(true);
  });
});

describe('applyGraphFocus', () => {
  it('should leave nodes unchanged when nothing is focused', () => {
    const nodes = [createNode('task-a', EGraphNodeType.Task)];
    const edges = [createEdge('e1', 'task-a', 'task-b')];

    expect(applyGraphFocus(nodes, edges, null)).toEqual({ nodes, edges });
  });

  it('should mark the focused card and highlight connected edges', () => {
    const nodes: TGraphNode[] = [
      createNode('task-a', EGraphNodeType.Task),
      createNode('task-b', EGraphNodeType.Task),
    ];
    const edges: TGraphEdge[] = [createEdge('e1', 'task-a', 'task-b')];

    const { nodes: nextNodes, edges: nextEdges } = applyGraphFocus(nodes, edges, 'task-a');

    expect(nextNodes[0].className).toBe(GRAPH_FOCUSED_CLASS);
    expect(nextNodes[1].className).toBe('');
    expect(nextEdges[0].className).toBe(GRAPH_HIGHLIGHTED_EDGE_CLASS);
    expect(nextEdges[0].style).toEqual(
      expect.objectContaining({
        stroke: 'var(--pneumatic-color-black100)',
        strokeWidth: 2,
      }),
    );
  });

  it('should dim nodes and edges outside the focused dependency path', () => {
    const nodes: TGraphNode[] = [
      createNode('task-a', EGraphNodeType.Task),
      createNode('task-b', EGraphNodeType.Task),
      createNode('task-c', EGraphNodeType.Task),
      createNode('task-d', EGraphNodeType.Task),
    ];
    const edges: TGraphEdge[] = [
      createEdge('e1', 'task-a', 'task-b'),
      createEdge('e2', 'task-b', 'task-c'),
      createEdge('e3', 'task-d', 'task-c'),
    ];

    const { nodes: nextNodes, edges: nextEdges } = applyGraphFocus(nodes, edges, 'task-a');

    expect(nextNodes.find((node) => node.id === 'task-c')?.className).toBe('');
    expect(nextNodes.find((node) => node.id === 'task-d')?.className).toBe(GRAPH_DIMMED_CLASS);
    expect(nextEdges.find((edge) => edge.id === 'e2')?.className).toBe(GRAPH_HIGHLIGHTED_EDGE_CLASS);
    expect(nextEdges.find((edge) => edge.id === 'e3')?.className).toBe(GRAPH_DIMMED_CLASS);
  });

  it('should pass the focus state to the edge labels', () => {
    const nodes: TGraphNode[] = [
      createNode('task-a', EGraphNodeType.Task),
      createNode('task-b', EGraphNodeType.Task),
      createNode('task-c', EGraphNodeType.Task),
    ];
    const edges: TGraphEdge[] = [
      createEdge('e1', 'task-a', 'task-b'),
      createEdge('e2', 'task-c', 'task-b'),
    ];

    const { edges: nextEdges } = applyGraphFocus(nodes, edges, 'task-a');

    expect(nextEdges.find((edge) => edge.id === 'e1')?.data?.focus).toBe('highlighted');
    expect(nextEdges.find((edge) => edge.id === 'e2')?.data?.focus).toBe('dimmed');
  });

  it('should thicken a highlighted gray line', () => {
    const nodes: TGraphNode[] = [
      createNode('task-a', EGraphNodeType.Task),
      createNode('task-b', EGraphNodeType.Task),
    ];
    const edges: TGraphEdge[] = [
      {
        id: 'edge-task-a-task-b-0',
        source: 'task-a',
        target: 'task-b',
        style: {
          stroke: 'var(--pneumatic-color-black32)',
        },
      },
    ];

    const { edges: nextEdges } = applyGraphFocus(nodes, edges, 'task-a');

    expect(nextEdges[0].className).toBe(GRAPH_HIGHLIGHTED_EDGE_CLASS);
    expect(nextEdges[0].style).toEqual(
      expect.objectContaining({
        stroke: 'var(--pneumatic-color-black100)',
        strokeWidth: 2,
      }),
    );
  });

  it('should keep a highlighted check-if line below cards', () => {
    const nodes: TGraphNode[] = [
      { ...createNode('task-a', EGraphNodeType.Task), zIndex: GRAPH_CARD_Z_INDEX },
      { ...createNode('task-b', EGraphNodeType.Task), zIndex: GRAPH_CARD_Z_INDEX },
    ];
    const edges: TGraphEdge[] = [
      {
        id: 'edge-check-if',
        source: 'task-a',
        target: 'task-b',
        zIndex: 0,
        data: { isConditional: true, summary: 'Client exists' },
      },
    ];

    const { edges: nextEdges } = applyGraphFocus(nodes, edges, 'task-a');

    expect(nextEdges[0].className).toContain(GRAPH_HIGHLIGHTED_EDGE_CLASS);
    expect(nextEdges[0].zIndex ?? 0).toBeLessThan(GRAPH_CARD_Z_INDEX);
  });
});
