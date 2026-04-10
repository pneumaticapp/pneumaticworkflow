import { IApplicationState } from '../../types/redux';

export const selectExtraFieldLabelsBesideForTemplate = (
  state: IApplicationState,
  templateId: number | undefined,
): boolean => {
  if (templateId === undefined) {
    return false;
  }

  return state.template.extraFieldLabelsBesideByTemplateId[templateId] === true;
};
