import { EGraphViewMode } from '../../../components/TemplateEdit/TemplateGraphEditor/types';
import reducer, { resetGraphView, setSelectedTask, setViewMode } from '../slice';

describe('templateGraphView slice', () => {
  const initialState = {
    viewMode: EGraphViewMode.List,
    selectedTaskApiName: null,
  };

  it('should return the initial state', () => {
    expect(reducer(undefined, { type: 'unknown' })).toEqual(initialState);
  });

  it('should set graph view mode and clear selected task', () => {
    const stateWithTask = {
      viewMode: EGraphViewMode.List,
      selectedTaskApiName: 'task-1',
    };

    const result = reducer(stateWithTask, setViewMode(EGraphViewMode.Graph));

    expect(result).toEqual({
      viewMode: EGraphViewMode.Graph,
      selectedTaskApiName: null,
    });
  });

  it('should set selected task api name', () => {
    const result = reducer(initialState, setSelectedTask('task-2'));

    expect(result.selectedTaskApiName).toBe('task-2');
  });

  it('should reset view mode and selected task', () => {
    const dirtyState = {
      viewMode: EGraphViewMode.Graph,
      selectedTaskApiName: 'task-3',
    };

    const result = reducer(dirtyState, resetGraphView());

    expect(result).toEqual(initialState);
  });
});
