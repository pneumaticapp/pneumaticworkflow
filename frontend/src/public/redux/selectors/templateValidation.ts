import type { RootState } from '../store';

export const getTemplateValidationErrors = (state: RootState) => state.templateValidation.errors;

export const getTemplateValidationBatchId = (state: RootState) => state.templateValidation.batchId;

export const getTemplateValidationFocusApiName = (state: RootState) => state.templateValidation.focusElementApiName;
