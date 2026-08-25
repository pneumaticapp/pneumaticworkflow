import {
  GRAPH_POSITIONS_STORAGE_KEY,
  getGraphNodePositions,
  saveGraphNodePosition,
} from '../graphPositionsStorage';

describe('graphPositionsStorage', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('should save positions separately for each template', () => {
    saveGraphNodePosition(10, 'task-1', { x: 100, y: 200 });
    saveGraphNodePosition(20, 'task-1', { x: 300, y: 400 });

    expect(getGraphNodePositions(10)).toEqual({ 'task-1': { x: 100, y: 200 } });
    expect(getGraphNodePositions(20)).toEqual({ 'task-1': { x: 300, y: 400 } });
  });

  it('should preserve positions of other nodes when saving', () => {
    saveGraphNodePosition(10, 'task-1', { x: 100, y: 200 });
    saveGraphNodePosition(10, 'task-2', { x: 300, y: 400 });

    expect(getGraphNodePositions(10)).toEqual({
      'task-1': { x: 100, y: 200 },
      'task-2': { x: 300, y: 400 },
    });
  });

  it('should ignore malformed storage values and invalid positions', () => {
    localStorage.setItem(
      GRAPH_POSITIONS_STORAGE_KEY,
      JSON.stringify({
        10: {
          valid: { x: 10, y: 20 },
          invalidX: { x: '10', y: 20 },
          invalidY: { x: 10, y: null },
        },
      }),
    );

    expect(getGraphNodePositions(10)).toEqual({ valid: { x: 10, y: 20 } });

    localStorage.setItem(GRAPH_POSITIONS_STORAGE_KEY, '{broken');

    expect(getGraphNodePositions(10)).toEqual({});
  });

  it('should not persist positions for a template without an id', () => {
    saveGraphNodePosition(undefined, 'task-1', { x: 100, y: 200 });

    expect(localStorage.getItem(GRAPH_POSITIONS_STORAGE_KEY)).toBeNull();
    expect(getGraphNodePositions()).toEqual({});
  });
});
