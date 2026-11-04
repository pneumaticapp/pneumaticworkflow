import type { RootState } from '../store';
import { EGraphViewMode } from '../../types/template';

export const selectTemplateViewMode = (state: RootState): EGraphViewMode => state.templateGraphView.viewMode;

export const selectTemplateSelectedTaskApiName = (state: RootState): string | null =>
  state.templateGraphView.selectedTaskApiName;

export const selectIsGraphCanvas = (state: RootState): boolean =>
  state.templateGraphView.viewMode === EGraphViewMode.Graph;
