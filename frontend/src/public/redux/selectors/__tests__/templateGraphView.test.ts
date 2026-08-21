import { IApplicationState } from '../../../types/redux';
import { EGraphViewMode } from '../../../components/TemplateEdit/TemplateGraphEditor/types';
import { selectIsGraphCanvas, selectTemplateSelectedTaskApiName, selectTemplateViewMode } from '../templateGraphView';

const createMockState = (viewMode: EGraphViewMode, selectedTaskApiName: string | null = null): IApplicationState =>
  ({
    templateGraphView: {
      viewMode,
      selectedTaskApiName,
    },
  } as IApplicationState);

describe('templateGraphView selectors', () => {
  it('should return list view mode from store', () => {
    const result = selectTemplateViewMode(createMockState(EGraphViewMode.List));

    expect(result).toBe(EGraphViewMode.List);
  });

  it('should return graph view mode from store', () => {
    const result = selectTemplateViewMode(createMockState(EGraphViewMode.Graph));

    expect(result).toBe(EGraphViewMode.Graph);
  });

  it('should return the selected task api name', () => {
    const result = selectTemplateSelectedTaskApiName(createMockState(EGraphViewMode.Graph, 'task-1'));

    expect(result).toBe('task-1');
  });

  it('should treat graph mode as canvas even when a task is selected', () => {
    expect(selectIsGraphCanvas(createMockState(EGraphViewMode.Graph))).toBe(true);
    expect(selectIsGraphCanvas(createMockState(EGraphViewMode.Graph, 'task-1'))).toBe(true);
    expect(selectIsGraphCanvas(createMockState(EGraphViewMode.List))).toBe(false);
  });
});
