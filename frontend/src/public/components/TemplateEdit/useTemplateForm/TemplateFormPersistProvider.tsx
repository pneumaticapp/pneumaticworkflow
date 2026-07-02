import * as React from 'react';
import { useCallback, useEffect, useMemo, useRef } from 'react';
import { useFormikContext } from 'formik';
import { useDispatch } from 'react-redux';

import { ITemplate } from '../../../types/template';
import { patchTemplate } from '../../../redux/actions';
import { TemplatePersistContext } from './contexts';
import { getChangedFields, getUnconsumedPendingEdits } from './templateFormUtils';
import { ITemplatePersistContextValue, TSetValues } from './types';

interface ITemplateFormPersistProviderProps {
  dirtyRef: React.MutableRefObject<boolean>;
  pendingUserEditsRef: React.MutableRefObject<Partial<ITemplate>>;
  persistBaselineSyncRef: React.MutableRefObject<((reduxTemplate: ITemplate) => void) | null>;
  setValues: TSetValues;
  children: React.ReactNode;
}

/**
 * Single save point for every user edit on the Edit Template page.
 *
 * On each Formik values change we compute a shallow top-level diff and — only
 * when the change was initiated by a user via the wrapped `setFieldValue`/
 * `setValues` (i.e. `dirtyRef` is true) — dispatch `patchTemplate`. The
 * `patchTemplate` saga owns the actual debounce + API call. External
 * reinitializes (template load, save response with server-stamped fields,
 * owners normalization, ...) update `previousValuesRef` but never dispatch, so
 * they cannot cause a save loop.
 *
 * When a user edit touches a non-activation field, the wrapped `setFieldValue`/
 * `setValues` flip `isActive` to false in Formik synchronously (see
 * `applyImmediateDeactivation`) so controls like `RouteLeavingGuard` react
 * immediately. The saga makes the same call server-side but only reinitializes
 * Formik after the save round-trip.
 *
 * On unmount the values effect cleanup calls `flushPersist` so edits made just
 * before leaving the page are not lost. Call `abandonPendingChanges` before
 * navigating away after "Discard changes" so those edits are not re-dispatched.
 */
export function TemplateFormPersistProvider({
  dirtyRef,
  pendingUserEditsRef,
  persistBaselineSyncRef,
  setValues,
  children,
}: ITemplateFormPersistProviderProps) {
  const { values } = useFormikContext<ITemplate>();
  const dispatch = useDispatch();
  const previousValuesRef = useRef<ITemplate>(values);
  const valuesRef = useRef(values);
  const dispatchRef = useRef(dispatch);
  const dirtyRefRef = useRef(dirtyRef);
  const pendingUserEditsRefRef = useRef(pendingUserEditsRef);
  const persistBaselineSyncRefRef = useRef(persistBaselineSyncRef);
  const setValuesRef = useRef(setValues);

  valuesRef.current = values;
  dispatchRef.current = dispatch;
  dirtyRefRef.current = dirtyRef;
  pendingUserEditsRefRef.current = pendingUserEditsRef;
  persistBaselineSyncRefRef.current = persistBaselineSyncRef;
  setValuesRef.current = setValues;

  useEffect(() => {
    persistBaselineSyncRefRef.current.current = (reduxTemplate) => {
      // Baseline must mirror the latest Redux snapshot for every field so
      // server-stamped or normalized values (dateUpdated, owners, ...) are not
      // diffed as user edits on the next flush.
      previousValuesRef.current = { ...reduxTemplate };
    };

    return () => {
      persistBaselineSyncRefRef.current.current = null;
    };
  }, []);

  const consumedPendingRef = useRef<{
    previousBaseline: ITemplate;
    isUserEdit: boolean;
    pendingUserEdits: Partial<ITemplate>;
  } | null>(null);

  const takePendingChanges = useCallback((trackForRevert = false) => {
    if (previousValuesRef.current === valuesRef.current) {
      return {};
    }

    const changedFields = getChangedFields(previousValuesRef.current, valuesRef.current);
    const isUserEdit = dirtyRefRef.current.current;

    if (trackForRevert && isUserEdit && Object.keys(changedFields).length > 0) {
      consumedPendingRef.current = {
        previousBaseline: previousValuesRef.current,
        isUserEdit,
        pendingUserEdits: { ...pendingUserEditsRefRef.current.current },
      };
    }

    previousValuesRef.current = valuesRef.current;
    dirtyRefRef.current.current = false;

    if (isUserEdit && Object.keys(changedFields).length > 0 && !trackForRevert) {
      pendingUserEditsRefRef.current.current = {};
    }

    return isUserEdit ? changedFields : {};
  }, []);

  const consumePendingChanges = useCallback(() => takePendingChanges(true), [takePendingChanges]);

  const confirmConsumedChanges = useCallback(() => {
    const consumed = consumedPendingRef.current;

    if (consumed) {
      pendingUserEditsRefRef.current.current = getUnconsumedPendingEdits(
        consumed.pendingUserEdits,
        pendingUserEditsRefRef.current.current,
      );
    }

    consumedPendingRef.current = null;
  }, []);

  const flushPersist = useCallback(() => {
    const changedFields = takePendingChanges();

    if (Object.keys(changedFields).length > 0) {
      dispatchRef.current(patchTemplate({ changedFields }));
    }
  }, [takePendingChanges]);

  const revertConsumedChanges = useCallback(() => {
    const consumed = consumedPendingRef.current;

    if (!consumed) {
      return;
    }

    previousValuesRef.current = consumed.previousBaseline;
    consumedPendingRef.current = null;

    // Restoring the baseline does not change Formik `values`, so the values
    // effect won't re-run. Re-apply the current values through the wrapped
    // setter so dirty state, pending edits, and the autosave effect stay aligned.
    if (consumed.isUserEdit && previousValuesRef.current !== valuesRef.current) {
      setValuesRef.current({ ...valuesRef.current }, false);
    }
  }, []);

  const abandonPendingChanges = useCallback(() => {
    previousValuesRef.current = valuesRef.current;
    dirtyRefRef.current.current = false;
    pendingUserEditsRefRef.current.current = {};
    consumedPendingRef.current = null;
  }, []);

  useEffect(() => {
    if (previousValuesRef.current === values) {
      return undefined;
    }

    const timeoutId = window.setTimeout(() => {
      flushPersist();
    }, 0);

    return () => {
      window.clearTimeout(timeoutId);
      flushPersist();
    };
  }, [values, flushPersist]);

  const persistContextValue = useMemo<ITemplatePersistContextValue>(
    () => ({
      consumePendingChanges,
      confirmConsumedChanges,
      revertConsumedChanges,
      abandonPendingChanges,
    }),
    [consumePendingChanges, confirmConsumedChanges, revertConsumedChanges, abandonPendingChanges],
  );

  return (
    <TemplatePersistContext.Provider value={persistContextValue}>
      {children as React.ReactElement}
    </TemplatePersistContext.Provider>
  );
}
