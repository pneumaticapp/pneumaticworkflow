import * as React from 'react';
import { useCallback, useEffect, useMemo, useRef } from 'react';
import { useFormikContext } from 'formik';
import { useDispatch } from 'react-redux';

import { ITemplate } from '../../../types/template';
import { patchTemplate } from '../../../redux/actions';
import { TemplatePersistContext } from './contexts';
import { getChangedFields, getUnconsumedPendingEdits } from './templateFormUtils';
import { ITemplatePersistContextValue } from './types';

interface ITemplateFormPersistProviderProps {
  dirtyRef: React.MutableRefObject<boolean>;
  pendingUserEditsRef: React.MutableRefObject<Partial<ITemplate>>;
  persistBaselineSyncRef: React.MutableRefObject<((reduxTemplate: ITemplate) => void) | null>;
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

  valuesRef.current = values;
  dispatchRef.current = dispatch;
  dirtyRefRef.current = dirtyRef;
  pendingUserEditsRefRef.current = pendingUserEditsRef;
  persistBaselineSyncRefRef.current = persistBaselineSyncRef;

  useEffect(() => {
    persistBaselineSyncRefRef.current.current = (reduxTemplate) => {
      // While an explicit submit has consumed pending edits and is waiting for
      // confirm/revert, keep the pre-submit baseline so a Redux reinitialize from
      // the in-flight patch does not collapse the diff we need to restore.
      if (consumedPendingRef.current) {
        return;
      }

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

    // Explicit submit flows (activate/deactivate) consume pending edits before
    // `patchTemplate` returns. Keep the form dirty until confirm/revert so a
    // Redux reinitialize from the in-flight patch does not reset Formik and
    // drop the consumed-but-unsaved edits.
    if (!trackForRevert) {
      dirtyRefRef.current.current = false;
    }

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

    if (Object.keys(pendingUserEditsRefRef.current.current).length === 0) {
      dirtyRefRef.current.current = false;
    }
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
    pendingUserEditsRefRef.current.current = { ...consumed.pendingUserEdits };
    dirtyRefRef.current.current = consumed.isUserEdit;
    consumedPendingRef.current = null;

    // Formik `values` are unchanged, so the `[values]` effect will not re-run.
    // Re-queue autosave directly against the restored baseline instead of
    // relying on `setValues`, which would diff against a Redux snapshot that may
    // already include the consumed (but unsaved) fields from the failed patch.
    if (consumed.isUserEdit && previousValuesRef.current !== valuesRef.current) {
      flushPersist();
    }
  }, [flushPersist]);

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
