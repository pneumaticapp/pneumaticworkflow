import type { ETaskFormParts } from '../../components/TemplateEdit/types';

export interface ITemplateValidationErrorTarget {
  taskUuid: string | null;
  section: ETaskFormParts | null;
  elementApiName: string;
}

export interface ITemplateValidationErrorMatch {
  target: ITemplateValidationErrorTarget;
  entity: unknown;
}

export interface ITemplateValidationError {
  apiName: string;
  message: string;
  target: ITemplateValidationErrorTarget;
  entitySnapshot: string;
}

export interface ITemplateValidationStore {
  errors: ITemplateValidationError[];
  batchId: number;
  focusApiName: string | null;
}
