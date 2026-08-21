import { GRAPH_EDGE_CLASS_SKIP, isSkipGraphEdge } from '../edgeStyles';

describe('isSkipGraphEdge', () => {
  it('should detect a skip suffix without matching skippable task ids', () => {
    expect(
      isSkipGraphEdge({
        id: 'edge-task-linear-task-url-title-skip-0',
        source: 'task-linear',
        target: 'task-url-title',
        sourceHandle: 'source-skip',
      }),
    ).toBe(true);

    expect(
      isSkipGraphEdge({
        id: 'edge-task-linear-task-skippable-0',
        source: 'task-linear',
        target: 'task-skippable',
      }),
    ).toBe(false);

    expect(
      isSkipGraphEdge({
        id: 'edge-task-skippable-task-url-title-0',
        source: 'task-skippable',
        target: 'task-url-title',
      }),
    ).toBe(false);
  });

  it('should detect a remapped skip edge by class name', () => {
    expect(
      isSkipGraphEdge({
        id: 'edge-task-linear-task-url-title-skip-0',
        source: 'junction-fork-task-linear',
        target: 'junction-join-task-url-title',
        className: GRAPH_EDGE_CLASS_SKIP,
      }),
    ).toBe(true);
  });
});
