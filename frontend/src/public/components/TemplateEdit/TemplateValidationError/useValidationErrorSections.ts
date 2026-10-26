import { useRef } from 'react';
import { useSelector } from 'react-redux';

import { getTemplateValidationBatchId, getTemplateValidationErrors } from '../../../redux/selectors/templateValidation';
import type { ETaskFormParts } from '../types';

export function useValidationErrorSections(taskUuid: string) {
  const validationErrors = useSelector(getTemplateValidationErrors);
  const batchId = useSelector(getTemplateValidationBatchId);
  const sectionBatchIdsRef = useRef<Partial<Record<ETaskFormParts, number>>>({});

  const errorSections = validationErrors
    .filter(({ target }) => target.taskUuid === taskUuid && target.section)
    .map(({ target }) => target.section as ETaskFormParts);

  errorSections.forEach((section) => {
    sectionBatchIdsRef.current[section] = batchId;
  });

  return {
    errorSections,
    getSectionBatchId: (section: ETaskFormParts) => sectionBatchIdsRef.current[section] ?? 0,
  };
}
