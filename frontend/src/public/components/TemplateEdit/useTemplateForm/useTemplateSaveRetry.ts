import { useCallback } from 'react';
import { useDispatch } from 'react-redux';

import { patchTemplate, saveTemplate } from '../../../redux/actions';
import { useTemplatePersist } from './contexts';

/**
 * Retries a failed template save using the current Formik state.
 *
 * Autosave reads from Redux, but user edits land in Formik first and only reach
 * Redux after `TemplateFormPersistProvider` flushes. Retrying with `saveTemplate`
 * alone can persist a stale Redux snapshot and drop in-flight Formik edits.
 */
export function useTemplateSaveRetry(): () => void {
  const dispatch = useDispatch();
  const {
    consumePendingChanges,
    getRetryExplicitPatch,
    confirmConsumedChanges,
    revertConsumedChanges,
  } = useTemplatePersist();

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
