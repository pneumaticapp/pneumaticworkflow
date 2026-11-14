import type { ITemplateListItem } from '../../types/template';

export interface ISelectTemplateModalStore {
  isOpen: boolean;
  ancestorTaskId: number | null;
  isLoading: boolean;
  items: ITemplateListItem[];
  templatesIdsFilter: number[];
}
