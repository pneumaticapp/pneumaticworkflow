import { EMPTY_CONNECTED_HANDLES, applyConnectedHandles, collectConnectedHandles } from '../applyConnectedHandles';
import { EGraphNodeType, TGraphEdge, TGraphNode } from '../../types';

describe('collectConnectedHandles', () => {
  it('should mark only handles that have an edge', () => {
    const edges: TGraphEdge[] = [
      { id: 'e1', source: 'kickoff', target: 'task-1', sourceHandle: 'source-bottom', targetHandle: 'target-top' },
      { id: 'e2', source: 'task-1', target: 'task-2', sourceHandle: 'source-right', targetHandle: 'target-left' },
    ];

    expect(collectConnectedHandles('kickoff', edges)).toEqual({
      ...EMPTY_CONNECTED_HANDLES,
      hasSourceBottom: true,
    });
    expect(collectConnectedHandles('task-1', edges)).toEqual({
      ...EMPTY_CONNECTED_HANDLES,
      hasTargetTop: true,
      hasSourceRight: true,
    });
    expect(collectConnectedHandles('task-2', edges)).toEqual({
      ...EMPTY_CONNECTED_HANDLES,
      hasTargetLeft: true,
    });
  });
});

describe('applyConnectedHandles', () => {
  it('should attach handle flags to cards and skip junctions', () => {
    const nodes = [
      { id: 'kickoff', type: EGraphNodeType.Kickoff, position: { x: 0, y: 0 }, data: {} },
      { id: 'task-1', type: EGraphNodeType.Task, position: { x: 0, y: 0 }, data: {} },
      { id: 'junction-fork-kickoff', type: EGraphNodeType.Junction, position: { x: 0, y: 0 }, data: { kind: 'fork' } },
    ] as TGraphNode[];
    const edges: TGraphEdge[] = [
      { id: 'e1', source: 'kickoff', target: 'junction-fork-kickoff', sourceHandle: 'source-bottom', targetHandle: 'target-top' },
    ];

    const next = applyConnectedHandles({ nodes, edges });
    const kickoff = next.nodes.find((node) => node.id === 'kickoff');
    const junction = next.nodes.find((node) => node.id === 'junction-fork-kickoff');

    expect(kickoff && 'handles' in kickoff.data ? kickoff.data.handles : null).toEqual({
      ...EMPTY_CONNECTED_HANDLES,
      hasSourceBottom: true,
    });
    expect(junction && 'handles' in junction.data ? junction.data.handles : undefined).toBeUndefined();
  });
});
