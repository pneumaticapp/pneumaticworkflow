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

export function useTemplateForm(initialValues: ITemplateClient, templateIdentityKey?: string | number) {
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
    formik.resetForm({ values: initialValues });
  }
  lastTemplateIdentityRef.current = resolvedIdentity;

  // Edits made while a save is in flight live only in Formik and must survive Redux merges.
  if (lastSyncedInitialValuesRef.current !== initialValues) {
    const rawPending = dirtyRef.current ? pendingUserEditsRef.current : {};

    if (Object.keys(rawPending).length > 0) {
      const mergedValues = applyPendingEdits(initialValues, rawPending, lastSyncedInitialValuesRef.current);

      pendingUserEditsRef.current = getChangedFields(initialValues, mergedValues);
      dirtyRef.current = true;

      // Skip a redundant Formik write when the merged snapshot already matches the form.
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

  const setFieldValue = useCallback<TSetFieldValue>((field, value, shouldValidate) => {
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
  }, []);

  const setValues = useCallback<TSetValues>((values, shouldValidate) => {
    const currentFormik = formikRef.current;
    dirtyRef.current = true;
    const currentValues = overlayPendingEdits(
      currentFormik.values,
      pendingUserEditsRef.current,
      lastSyncedInitialValuesRef.current,
    );
    const updatedValues = typeof values === 'function' ? values(currentValues) : values;
    const nextValues = applyImmediateDeactivation(currentValues, updatedValues);
    pendingUserEditsRef.current = getChangedFields(lastSyncedInitialValuesRef.current, nextValues);
    currentFormik.setValues(nextValues, shouldValidate);
  }, []);

  return { formik, setFieldValue, setValues, dirtyRef, pendingUserEditsRef, persistBaselineSyncRef };
}
