import { IApplicationState } from '../../types/redux';

export const getTemplatesModalFilter = (state: IApplicationState): number[] => {
  return state.selectTemplateModal.templatesIdsFilter;
};
