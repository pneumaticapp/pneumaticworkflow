import { useEffect, useRef } from 'react';
import { useSelector } from 'react-redux';

import { getTemplateValidationBatchId, getTemplateValidationErrors } from '../../../redux/selectors/templateValidation';

export function useOpenOnValidationError(taskUuid: string | null, open: () => void) {
  const validationErrors = useSelector(getTemplateValidationErrors);
  const batchId = useSelector(getTemplateValidationBatchId);
  const handledBatchIdRef = useRef<number | null>(null);
  const openRef = useRef(open);
  openRef.current = open;

  useEffect(() => {
    if (handledBatchIdRef.current === batchId) return;
    if (!validationErrors.some(({ target }) => target.taskUuid === taskUuid)) return;

    handledBatchIdRef.current = batchId;
    openRef.current();
  }, [validationErrors, batchId, taskUuid]);
}
