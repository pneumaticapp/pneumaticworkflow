import type { EGraphViewMode } from '../../types/template';

export interface ITemplateGraphViewState {
  viewMode: EGraphViewMode;
  selectedTaskApiName: string | null;
}
