import { useCallback, useRef } from 'react';
import { useFormik } from 'formik';

import { ITemplateClient } from '../../../types/template';
import { applyImmediateDeactivation } from './templateFormDeactivation';
import { applyReferenceCleanup, shouldRunReferenceCleanup } from './templateFormReferenceCleanup';
import {
  applyPendingEdits,
  getChangedFields,
  hasTemplateIdentityChanged,
  overlayPendingEdits,
  resolveTemplateIdentity,
  setNestedFieldValue,
} from './templateFormUtils';
import { TSetFieldValue, TSetValues } from './types';

/**
 * Root Formik context for the whole Edit Template page.
 *
 * The entire template (name, description, kickoff, tasks, owners, share
 * settings, toggles, ...) lives in a single Formik state. Every field binds to
 * it via `useTemplateField`; nothing dispatches Redux field updates from
 * individual inputs anymore. Saving happens from one place only —
 * `TemplateFormPersistProvider` — which dispatches a single `patchTemplate`
 * action for user edits (the saga then debounces + saves). Explicit "submit"
 * flows (e.g. activating the template) still go through `patchTemplate` with
 * callbacks, so both onChange and submit share one save path.
 */
export function useTemplateForm(
  initialValues: ITemplateClient,
  templateIdentityKey?: string | number,
) {
  const dirtyRef = useRef(false);
  const pendingUserEditsRef = useRef<Partial<ITemplateClient>>({});
  const lastSyncedInitialValuesRef = useRef(initialValues);
  const persistBaselineSyncRef = useRef<((reduxTemplate: ITemplateClient) => void) | null>(null);
  const resolvedIdentity = resolveTemplateIdentity(initialValues, templateIdentityKey);
  const lastTemplateIdentityRef = useRef(resolvedIdentity);

  const formik = useFormik<ITemplateClient>({
    initialValues,
    enableReinitialize: false,
    onSubmit: () => undefined,
  });
  const formikRef = useRef(formik);
  formikRef.current = formik;

  if (hasTemplateIdentityChanged(lastTemplateIdentityRef.current, resolvedIdentity)) {
    dirtyRef.current = false;
    pendingUserEditsRef.current = {};
    lastSyncedInitialValuesRef.current = initialValues;
    lastTemplateIdentityRef.current = resolvedIdentity;
    formik.resetForm({ values: initialValues });
  }

  // Redux `template` updates must be merged into Formik without discarding edits
  // that still live only in the form (e.g. typed while a save is in flight).
  // Wrapped setters accumulate those edits in `pendingUserEditsRef` because a
  // Redux snapshot can land in the same render and overwrite Formik state.
  if (lastSyncedInitialValuesRef.current !== initialValues) {
    const rawPending = dirtyRef.current ? pendingUserEditsRef.current : {};

    if (Object.keys(rawPending).length > 0) {
      const mergedValues = applyPendingEdits(initialValues, rawPending, lastSyncedInitialValuesRef.current);

      pendingUserEditsRef.current = getChangedFields(initialValues, mergedValues);
      dirtyRef.current = true;

      // Optimistic `setTemplate` from autosave can land while the user is still
      // typing. Skip a redundant Formik write when the merged snapshot already
      // matches what the form is showing.
      const resyncDiff = getChangedFields(formik.values, mergedValues);
      if (Object.keys(resyncDiff).length > 0) {
        formik.setValues(mergedValues, false);
      }

      persistBaselineSyncRef.current?.(initialValues);
    } else {
      pendingUserEditsRef.current = {};
      dirtyRef.current = false;
      formik.resetForm({ values: initialValues });
      persistBaselineSyncRef.current?.(initialValues);
    }

    lastSyncedInitialValuesRef.current = initialValues;
  }

  const setFieldValue = useCallback<TSetFieldValue>(
    (field, value, shouldValidate) => {
      const currentFormik = formikRef.current;
      dirtyRef.current = true;
      const currentValues = overlayPendingEdits(
        currentFormik.values,
        pendingUserEditsRef.current,
        lastSyncedInitialValuesRef.current,
      );
      let nextValues = setNestedFieldValue(currentValues, field, value);
      const runCleanup = shouldRunReferenceCleanup(field, currentValues, nextValues);

      if (runCleanup) {
        nextValues = applyReferenceCleanup(nextValues);
      }

      nextValues = applyImmediateDeactivation(currentValues, nextValues);
      pendingUserEditsRef.current = getChangedFields(lastSyncedInitialValuesRef.current, nextValues);

      if (runCleanup || nextValues.isActive !== currentValues.isActive) {
        currentFormik.setValues(nextValues, shouldValidate);
      } else {
        currentFormik.setFieldValue(field, value, shouldValidate);
      }
    },
    [],
  );

  const setValues = useCallback<TSetValues>(
    (values, shouldValidate) => {
      const currentFormik = formikRef.current;
      dirtyRef.current = true;
      const currentValues = overlayPendingEdits(
        currentFormik.values,
        pendingUserEditsRef.current,
        lastSyncedInitialValuesRef.current,
      );
      const nextValues = applyImmediateDeactivation(currentValues, values);
      pendingUserEditsRef.current = getChangedFields(lastSyncedInitialValuesRef.current, nextValues);
      currentFormik.setValues(nextValues, shouldValidate);
    },
    [],
  );

  return { formik, setFieldValue, setValues, dirtyRef, pendingUserEditsRef, persistBaselineSyncRef };
}
