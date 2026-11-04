import type { RootState } from '../store';

export const getTemplatesModalFilter = (state: RootState): number[] => {
  return state.selectTemplateModal.templatesIdsFilter;
};
