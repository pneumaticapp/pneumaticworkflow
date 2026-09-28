import { useCallback } from 'react';
import { useDispatch } from 'react-redux';

import { patchTemplate, saveTemplate } from '../../../redux/actions';
import { useTemplatePersist } from './contexts';

// Retry from the Formik state: Redux can hold a stale snapshot and drop in-flight edits.
export function useTemplateSaveRetry(): () => void {
  const dispatch = useDispatch();
  const { consumePendingChanges, getRetryExplicitPatch, confirmConsumedChanges, revertConsumedChanges } =
    useTemplatePersist();

  return useCallback(() => {
    const pendingChanges = consumePendingChanges();
    const changedFields = {
      ...pendingChanges,
      ...getRetryExplicitPatch(),
    };

    if (Object.keys(changedFields).length > 0) {
      dispatch(
        patchTemplate({
          changedFields,
          onSuccess: confirmConsumedChanges,
          onFailed: revertConsumedChanges,
        }),
      );
      return;
    }

    dispatch(saveTemplate());
  }, [consumePendingChanges, confirmConsumedChanges, dispatch, getRetryExplicitPatch, revertConsumedChanges]);
}
