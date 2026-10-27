import type { IApplicationState } from '../../types/redux';

export const getTemplateValidationErrors = (state: IApplicationState) => state.templateValidation.errors;

export const getTemplateValidationBatchId = (state: IApplicationState) => state.templateValidation.batchId;

export const getTemplateValidationFocusApiName = (state: IApplicationState) =>
  state.templateValidation.focusElementApiName;
