import {
  EDGE_STYLE_CONDITIONAL,
  EDGE_STYLE_DEFAULT,
  getGraphEdgeVisual,
  GRAPH_EDGE_CLASS_CONDITIONAL,
  isConditionalGraphEdge,
  isSkipGraphEdge,
} from '../edgeStyles';

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
});

describe('isConditionalGraphEdge', () => {
  it('should treat a check-if edge as conditional', () => {
    expect(
      isConditionalGraphEdge({
        id: 'edge-kickoff-task-1-checkif-0',
        source: 'kickoff',
        target: 'task-1',
        data: { isConditional: true, summary: 'Client exists' },
      }),
    ).toBe(true);
  });

  it('should not treat a skip-lane start-after edge as conditional', () => {
    expect(
      isConditionalGraphEdge({
        id: 'edge-task-linear-task-url-title-skip-0',
        source: 'task-linear',
        target: 'task-url-title',
        sourceHandle: 'source-skip',
      }),
    ).toBe(false);
  });

  it('should not treat a default edge as conditional', () => {
    expect(
      isConditionalGraphEdge({
        id: 'edge-kickoff-task-1-0',
        source: 'kickoff',
        target: 'task-1',
        data: { isConditional: false },
      }),
    ).toBe(false);
  });
});

describe('getGraphEdgeVisual', () => {
  it('should return a gray solid line for a default connection', () => {
    expect(getGraphEdgeVisual(false)).toEqual({
      style: EDGE_STYLE_DEFAULT,
    });
  });

  it('should return an orange dashed line for a condition connection', () => {
    expect(getGraphEdgeVisual(true)).toEqual({
      className: GRAPH_EDGE_CLASS_CONDITIONAL,
      style: EDGE_STYLE_CONDITIONAL,
    });
  });
});
