import {
  GRAPH_POSITIONS_STORAGE_KEY,
  clearGraphNodePositions,
  getGraphNodePositions,
  hasGraphNodePositions,
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

  it('should report stored positions only for templates that have them', () => {
    expect(hasGraphNodePositions(10)).toBe(false);

    saveGraphNodePosition(10, 'task-1', { x: 100, y: 200 });

    expect(hasGraphNodePositions(10)).toBe(true);
    expect(hasGraphNodePositions(20)).toBe(false);
    expect(hasGraphNodePositions()).toBe(false);
  });

  it('should clear positions of one template only', () => {
    saveGraphNodePosition(10, 'task-1', { x: 100, y: 200 });
    saveGraphNodePosition(20, 'task-1', { x: 300, y: 400 });

    clearGraphNodePositions(10);

    expect(getGraphNodePositions(10)).toEqual({});
    expect(hasGraphNodePositions(10)).toBe(false);
    expect(getGraphNodePositions(20)).toEqual({ 'task-1': { x: 300, y: 400 } });
  });

  it('should keep the storage untouched when clearing without a template id', () => {
    saveGraphNodePosition(10, 'task-1', { x: 100, y: 200 });

    clearGraphNodePositions();

    expect(getGraphNodePositions(10)).toEqual({ 'task-1': { x: 100, y: 200 } });
  });

  it('should not persist positions for a template without an id', () => {
    saveGraphNodePosition(undefined, 'task-1', { x: 100, y: 200 });

    expect(localStorage.getItem(GRAPH_POSITIONS_STORAGE_KEY)).toBeNull();
    expect(getGraphNodePositions()).toEqual({});
  });
});
