import { EGraphNodeType, TGraphEdge, TGraphNode } from '../../types';
import {
  applyGraphFocus,
  collectFocusIds,
  GRAPH_DIMMED_CLASS,
  GRAPH_FOCUSED_CLASS,
  GRAPH_HIGHLIGHTED_EDGE_CLASS,
} from '../applyGraphFocus';
import { GRAPH_EDGE_CLASS_SKIP } from '../edgeStyles';

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
  it('should include direct neighbors and expand through a junction', () => {
    const nodes: TGraphNode[] = [
      createNode('task-a', EGraphNodeType.Task),
      createNode('junction-fork-task-a', EGraphNodeType.Junction),
      createNode('task-b', EGraphNodeType.Task),
      createNode('task-c', EGraphNodeType.Task),
    ];
    const edges: TGraphEdge[] = [
      createEdge('e1', 'task-a', 'junction-fork-task-a'),
      createEdge('e2', 'junction-fork-task-a', 'task-b'),
      createEdge('e3', 'junction-fork-task-a', 'task-c'),
    ];

    const { nodeIds, edgeIds } = collectFocusIds(nodes, edges, 'task-a');

    expect(nodeIds).toEqual(new Set(['task-a', 'junction-fork-task-a', 'task-b', 'task-c']));
    expect(edgeIds).toEqual(new Set(['e1', 'e2', 'e3']));
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

  it('should dim nodes and edges outside the focused path', () => {
    const nodes: TGraphNode[] = [
      createNode('task-a', EGraphNodeType.Task),
      createNode('task-b', EGraphNodeType.Task),
      createNode('task-c', EGraphNodeType.Task),
    ];
    const edges: TGraphEdge[] = [
      createEdge('e1', 'task-a', 'task-b'),
      createEdge('e2', 'task-b', 'task-c'),
    ];

    const { nodes: nextNodes, edges: nextEdges } = applyGraphFocus(nodes, edges, 'task-a');

    expect(nextNodes.find((node) => node.id === 'task-c')?.className).toBe(GRAPH_DIMMED_CLASS);
    expect(nextEdges.find((edge) => edge.id === 'e2')?.className).toBe(GRAPH_DIMMED_CLASS);
  });

  it('should keep skip edges orange when they are highlighted', () => {
    const nodes: TGraphNode[] = [
      createNode('task-a', EGraphNodeType.Task),
      createNode('task-b', EGraphNodeType.Task),
    ];
    const edges: TGraphEdge[] = [
      {
        id: 'edge-task-a-task-b-skip-0',
        source: 'task-a',
        target: 'task-b',
        className: GRAPH_EDGE_CLASS_SKIP,
        style: {
          stroke: 'var(--pneumatic-color-link)',
          strokeDasharray: '6 4',
        },
      },
    ];

    const { edges: nextEdges } = applyGraphFocus(nodes, edges, 'task-a');

    expect(nextEdges[0].className).toBe(`${GRAPH_EDGE_CLASS_SKIP} ${GRAPH_HIGHLIGHTED_EDGE_CLASS}`);
    expect(nextEdges[0].style).toEqual(
      expect.objectContaining({
        stroke: 'var(--pneumatic-color-link-hover)',
        strokeWidth: 2,
        strokeDasharray: '6 4',
      }),
    );
  });
});
