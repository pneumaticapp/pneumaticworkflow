import { getGraphEdgePath, GRAPH_EDGE_LABEL_OFFSET, resolveGraphEdgePathKind } from '../getGraphEdgePath';

describe('resolveGraphEdgePathKind', () => {
  it('should keep from-task even when the ends are nearly aligned', () => {
    expect(resolveGraphEdgePathKind(100, 104, 'from-task')).toBe('from-task');
  });

  it('should keep from-fork even when the ends are nearly aligned', () => {
    expect(resolveGraphEdgePathKind(100, 104, 'from-fork')).toBe('from-fork');
  });

  it('should keep skip even when the ends share an x', () => {
    expect(resolveGraphEdgePathKind(100, 100, 'skip')).toBe('skip');
  });
});

describe('getGraphEdgePath', () => {
  it('should keep a vertical edge as a straight line', () => {
    const { path } = getGraphEdgePath({
      sourceX: 120,
      sourceY: 10,
      targetX: 120,
      targetY: 90,
      sourceHandle: 'source-bottom',
      targetHandle: 'target-top',
    });

    expect(path).toBe('M 120,10 L 120,90');
  });

  it('should keep an offset stem as one turn at the destination, not a stair in the gap', () => {
    const { path } = getGraphEdgePath({
      sourceX: 120,
      sourceY: 10,
      targetX: 124,
      targetY: 90,
      sourceHandle: 'source-bottom',
      targetHandle: 'target-top',
    });

    expect(path).toBe('M 120,10 L 120,90 L 124,90');
    expect(path).not.toMatch(/[QCAS]/);
  });

  it('should drop down from a task before turning into a side handle', () => {
    const { path, labelX } = getGraphEdgePath({
      sourceX: 20,
      sourceY: 40,
      targetX: 120,
      targetY: 120,
      sourceHandle: 'source-bottom',
      targetHandle: 'target-left',
    });

    expect(path).toBe('M 20,40 L 20,120 L 120,120');
    expect(labelX).toBe(20);
  });

  it('should leave a slightly offset fork sideways instead of drawing a diagonal', () => {
    const { path } = getGraphEdgePath({
      sourceX: 120,
      sourceY: 40,
      targetX: 124,
      targetY: 120,
      sourceHandle: 'source-right',
      targetHandle: 'target-top',
    });

    expect(path).toBe('M 120,40 L 124,40 L 124,120');
  });

  it('should leave a fork sideways before dropping onto the top of the card', () => {
    const { path } = getGraphEdgePath({
      sourceX: 120,
      sourceY: 40,
      targetX: 280,
      targetY: 160,
      pathKind: 'from-fork',
      sourceHandle: 'source-right',
      targetHandle: 'target-top',
    });

    expect(path).toBe('M 120,40 L 280,40 L 280,160');
  });

  it('should still turn at the junction when a fork is given bottom and top handles', () => {
    const { path } = getGraphEdgePath({
      sourceX: 120,
      sourceY: 80,
      targetX: 280,
      targetY: 40,
      pathKind: 'from-fork',
      sourceHandle: 'source-bottom',
      targetHandle: 'target-top',
    });

    expect(path).toBe('M 120,80 L 280,80 L 280,40');
  });

  it('should draw square corners without arcs', () => {
    const { path } = getGraphEdgePath({
      sourceX: 20,
      sourceY: 40,
      targetX: 120,
      targetY: 120,
      sourceHandle: 'source-bottom',
      targetHandle: 'target-top',
    });

    expect(path).not.toMatch(/[QCAS]/);
  });

  it('should use the skip lane as the vertical segment', () => {
    const { path, labelX } = getGraphEdgePath({
      sourceX: 120,
      sourceY: 40,
      targetX: 120,
      targetY: 200,
      pathKind: 'skip',
      laneX: 340,
    });

    expect(path).toBe('M 120,40 L 340,40 L 340,200 L 120,200');
    expect(labelX).toBe(120 + GRAPH_EDGE_LABEL_OFFSET);
  });

  it('should turn in a column gutter instead of running under a card', () => {
    const { path } = getGraphEdgePath({
      sourceX: 40,
      sourceY: 80,
      targetX: 400,
      targetY: 160,
      pathKind: 'from-fork',
      laneX: 120,
      laneY: 20,
    });

    expect(path).toBe('M 40,80 L 120,80 L 120,20 L 400,20 L 400,160');
  });

  it('should connect facing side handles with one turn at the target', () => {
    const { path } = getGraphEdgePath({
      sourceX: 100,
      sourceY: 50,
      targetX: 300,
      targetY: 80,
      sourceHandle: 'source-right',
      targetHandle: 'target-left',
    });

    expect(path).toBe('M 100,50 L 300,50 L 300,80');
  });

  it('should keep a nearly level side connection straight', () => {
    const { path } = getGraphEdgePath({
      sourceX: 100,
      sourceY: 50,
      targetX: 300,
      targetY: 54,
      sourceHandle: 'source-right',
      targetHandle: 'target-left',
    });

    expect(path).toBe('M 100,50 L 300,50 L 300,54');
  });

  it('should leave a fork sideways before dropping into a side handle', () => {
    const { path } = getGraphEdgePath({
      sourceX: 100,
      sourceY: 50,
      targetX: 300,
      targetY: 80,
      pathKind: 'from-fork',
      sourceHandle: 'source-right',
      targetHandle: 'target-left',
    });

    expect(path).toBe('M 100,50 L 300,50 L 300,80');
  });

  it('should not drop through a card when the trunk is on the far side of the handle', () => {
    const { path } = getGraphEdgePath({
      sourceX: 360,
      sourceY: 40,
      targetX: 300,
      targetY: 120,
      sourceHandle: 'source-right',
      targetHandle: 'target-left',
    });

    expect(path).toBe('M 360,40 L 360,120 L 300,120');
  });

  it('should leave and enter a card with a Miro-style standoff before turning', () => {
    const { path } = getGraphEdgePath({
      sourceX: 100,
      sourceY: 50,
      targetX: 300,
      targetY: 80,
      sourceHandle: 'source-right',
      targetHandle: 'target-left',
      sourceStandoff: 10,
      targetStandoff: 10,
    });

    expect(path).toBe('M 100,50 L 290,50 L 290,80 L 300,80');
  });

  it('should wrap around a card when the target sits behind the exit', () => {
    const { path } = getGraphEdgePath({
      sourceX: 100,
      sourceY: 50,
      targetX: 80,
      targetY: 120,
      sourceHandle: 'source-right',
      targetHandle: 'target-left',
      sourceStandoff: 10,
    });

    expect(path).toBe('M 100,50 L 110,50 L 110,120 L 80,120');
  });

  it('should keep a left standoff when a gutter sits on the start x', () => {
    const { path } = getGraphEdgePath({
      sourceX: 100,
      sourceY: 50,
      targetX: 300,
      targetY: 80,
      sourceHandle: 'source-left',
      sourceStandoff: 20,
      laneX: 100,
      laneY: 20,
    });

    expect(path.startsWith('M 100,50 L 80,50')).toBe(true);
  });

  it('should enter a card with a perpendicular standoff, not along the edge', () => {
    const { path } = getGraphEdgePath({
      sourceX: 40,
      sourceY: 40,
      targetX: 200,
      targetY: 120,
      sourceHandle: 'source-bottom',
      targetHandle: 'target-left',
      targetStandoff: 32,
      laneX: 40,
      laneY: 80,
    });

    expect(path).toContain('L 168,120 L 200,120');
    expect(path).not.toContain('L 200,80 L 200,120');
  });

  it('should not glance up a card edge when the source sits on the handle x', () => {
    const { path } = getGraphEdgePath({
      sourceX: 200,
      sourceY: 200,
      targetX: 200,
      targetY: 80,
      sourceHandle: 'source-top',
      targetHandle: 'target-left',
      targetStandoff: 32,
    });

    expect(path).toContain('L 168,80 L 200,80');
    expect(path).not.toMatch(/L 200,\d+ L 200,/);
  });

  it('should wrap past a join on the outer standoff before entering the side', () => {
    const { path } = getGraphEdgePath({
      sourceX: 40,
      sourceY: 40,
      targetX: 200,
      targetY: 120,
      sourceHandle: 'source-left',
      targetHandle: 'target-right',
      sourceStandoff: 20,
      targetStandoff: 32,
      laneX: 20,
      laneY: 80,
    });

    expect(path).toContain('L 232,80');
    expect(path).toContain('L 232,120 L 200,120');
  });

  it('should not glance along a card edge when the lane sits a few pixels inside the standoff', () => {
    const { path } = getGraphEdgePath({
      sourceX: 204,
      sourceY: 240,
      targetX: 200,
      targetY: 120,
      sourceHandle: 'source-top',
      targetHandle: 'target-left',
      targetStandoff: 32,
      laneX: 204,
      laneY: 200,
    });

    expect(path).toContain('L 168,120 L 200,120');
    expect(path).not.toMatch(/L 20[0-4],\d+ L 20[0-4],/);
  });
});
