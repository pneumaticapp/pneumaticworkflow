import { EGraphViewMode } from '../../types';
import {
  GRAPH_VIEW_MODE_STORAGE_KEY,
  getGraphViewMode,
  saveGraphViewMode,
} from '../graphViewModeStorage';

describe('graphViewModeStorage', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('should return list view when nothing is stored', () => {
    expect(getGraphViewMode()).toBe(EGraphViewMode.List);
  });

  it('should persist and restore graph view mode', () => {
    saveGraphViewMode(EGraphViewMode.Graph);

    expect(localStorage.getItem(GRAPH_VIEW_MODE_STORAGE_KEY)).toBe(EGraphViewMode.Graph);
    expect(getGraphViewMode()).toBe(EGraphViewMode.Graph);
  });

  it('should persist list view mode', () => {
    saveGraphViewMode(EGraphViewMode.Graph);
    saveGraphViewMode(EGraphViewMode.List);

    expect(getGraphViewMode()).toBe(EGraphViewMode.List);
  });

  it('should ignore malformed storage values', () => {
    localStorage.setItem(GRAPH_VIEW_MODE_STORAGE_KEY, 'kanban');

    expect(getGraphViewMode()).toBe(EGraphViewMode.List);
  });
});
