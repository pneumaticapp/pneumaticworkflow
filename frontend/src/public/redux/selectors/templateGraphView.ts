import { IApplicationState } from '../../types/redux';
import { EGraphViewMode } from '../../components/TemplateEdit/TemplateGraphEditor/types';

export const selectTemplateViewMode = (state: IApplicationState): EGraphViewMode =>
  state.templateGraphView.viewMode;

export const selectTemplateSelectedTaskApiName = (state: IApplicationState): string | null =>
  state.templateGraphView.selectedTaskApiName;

export const selectIsGraphCanvas = (state: IApplicationState): boolean =>
  state.templateGraphView.viewMode === EGraphViewMode.Graph;
