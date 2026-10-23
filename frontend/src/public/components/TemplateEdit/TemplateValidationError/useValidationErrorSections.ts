import { useSelector } from 'react-redux';

import { getTemplateValidationErrors } from '../../../redux/selectors/templateValidation';
import type { ETaskFormParts } from '../types';

export function useValidationErrorSections(taskUuid: string): ETaskFormParts[] {
  const validationErrors = useSelector(getTemplateValidationErrors);

  return validationErrors
    .filter(({ target }) => target.taskUuid === taskUuid && target.section)
    .map(({ target }) => target.section as ETaskFormParts);
}
