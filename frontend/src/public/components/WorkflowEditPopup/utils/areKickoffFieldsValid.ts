/* prettier-ignore */
import { hasFieldError } from '../../TemplateEdit/ExtraFields/utils/getFieldValidator';
import { isArrayWithItems } from '../../../utils/helpers';
import type { IExtraField } from '../../../types/template';
import { EExtraFieldMode } from '../../../types/template';

export const checkExtraFieldsAreValid = <T extends IExtraField[]>(fields?: T) => {
  if (!fields || !isArrayWithItems(fields)) {
    return true;
  }

  const numberOfErrorFields = fields.filter((field) => hasFieldError(field, EExtraFieldMode.ProcessRun)).length;

  return numberOfErrorFields === 0;
};
