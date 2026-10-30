import { EGraphViewMode } from '../../../components/TemplateEdit/TemplateGraphEditor/types';
import { getGraphViewMode } from '../../../components/TemplateEdit/TemplateGraphEditor/utils/graphViewModeStorage';
import reducer, { resetGraphView, setSelectedTask, setViewMode } from '../slice';

describe('templateGraphView slice', () => {
  const initialState = {
    viewMode: EGraphViewMode.List,
    selectedTaskApiName: null,
  };

  beforeEach(() => {
    localStorage.clear();
  });

  it('should return the initial state', () => {
    expect(reducer(undefined, { type: 'unknown' })).toEqual(initialState);
  });

  it('should set graph view mode, clear selected task and persist the choice', () => {
    const stateWithTask = {
      viewMode: EGraphViewMode.List,
      selectedTaskApiName: 'task-1',
    };

    const result = reducer(stateWithTask, setViewMode(EGraphViewMode.Graph));

    expect(result).toEqual({
      viewMode: EGraphViewMode.Graph,
      selectedTaskApiName: null,
    });
    expect(getGraphViewMode()).toBe(EGraphViewMode.Graph);
  });

  it('should set selected task api name', () => {
    const result = reducer(initialState, setSelectedTask('task-2'));

    expect(result.selectedTaskApiName).toBe('task-2');
  });

  it('should reset selected task and restore the stored view mode', () => {
    reducer(initialState, setViewMode(EGraphViewMode.Graph));

    const dirtyState = {
      viewMode: EGraphViewMode.Graph,
      selectedTaskApiName: 'task-3',
    };

    const result = reducer(dirtyState, resetGraphView());

    expect(result).toEqual({
      viewMode: EGraphViewMode.Graph,
      selectedTaskApiName: null,
    });
  });

  it('should reset to list view when nothing is stored', () => {
    const dirtyState = {
      viewMode: EGraphViewMode.Graph,
      selectedTaskApiName: 'task-3',
    };

    const result = reducer(dirtyState, resetGraphView());

    expect(result).toEqual(initialState);
  });
});
