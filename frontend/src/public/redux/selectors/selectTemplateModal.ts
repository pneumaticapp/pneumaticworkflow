import type { IApplicationState } from '../store';

export const getTemplatesModalFilter = (state: IApplicationState): number[] => {
  return state.selectTemplateModal.templatesIdsFilter;
};
