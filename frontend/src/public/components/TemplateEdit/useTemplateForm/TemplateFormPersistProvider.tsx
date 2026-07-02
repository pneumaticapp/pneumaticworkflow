import * as React from 'react';
import { useCallback, useEffect, useMemo, useRef } from 'react';
import { useFormikContext } from 'formik';
import { useDispatch } from 'react-redux';

import { ITemplate } from '../../../types/template';
import { patchTemplate, setTemplateStatus } from '../../../redux/actions';
import { ETemplateStatus } from '../../../types/redux';
import {
  abandonAutosavePersistRequests,
  allocateAutosavePersistRequestId,
  isAutosavePersistRequestCurrent,
} from '../../../redux/template/persistRequest';
import { TemplatePersistContext, useTemplateField } from './contexts';
import { getChangedFields, getUnconsumedPendingEdits } from './templateFormUtils';
import { ITemplatePersistContextValue } from './types';

interface ITemplateFormPersistProviderProps {
  dirtyRef: React.MutableRefObject<boolean>;
  pendingUserEditsRef: React.MutableRefObject<Partial<ITemplate>>;
  persistBaselineSyncRef: React.MutableRefObject<((reduxTemplate: ITemplate) => void) | null>;
  children: React.ReactNode;
}

type TConsumedPending = {
  previousBaseline: ITemplate;
  isUserEdit: boolean;
  pendingUserEdits: Partial<ITemplate>;
  explicitFields?: Partial<ITemplate>;
  /** Formik snapshot covered by the in-flight autosave patch. */
  dispatchedValues?: ITemplate;
};

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
  const { setValues } = useTemplateField();
  const dispatch = useDispatch();
  const latestReduxBaselineRef = useRef<ITemplate | null>(null);
  const previousValuesRef = useRef<ITemplate>(values);
  const valuesRef = useRef(values);
  const dispatchRef = useRef(dispatch);
  const dirtyRefRef = useRef(dirtyRef);
  const pendingUserEditsRefRef = useRef(pendingUserEditsRef);
  const persistBaselineSyncRefRef = useRef(persistBaselineSyncRef);
  const consumedPendingRef = useRef<TConsumedPending | null>(null);
  const retryExplicitPatchRef = useRef<Partial<ITemplate>>({});
  const pendingDispatchRef = useRef<{ requestId: number; dispatchedValues: ITemplate } | null>(null);
  const flushPersistRef = useRef<() => void>(() => undefined);
  const setValuesRef = useRef(setValues);

  valuesRef.current = values;
  dispatchRef.current = dispatch;
  dirtyRefRef.current = dirtyRef;
  pendingUserEditsRefRef.current = pendingUserEditsRef;
  persistBaselineSyncRefRef.current = persistBaselineSyncRef;
  setValuesRef.current = setValues;

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
      latestReduxBaselineRef.current = reduxTemplate;
      previousValuesRef.current = { ...reduxTemplate };
    };

    return () => {
      persistBaselineSyncRefRef.current.current = null;
    };
  }, []);

  const takePendingChanges = useCallback((mode: 'flush' | 'consume') => {
    if (previousValuesRef.current === valuesRef.current) {
      return {};
    }

    const changedFields = getChangedFields(previousValuesRef.current, valuesRef.current);
    const isUserEdit = dirtyRefRef.current.current;

    if (isUserEdit && Object.keys(changedFields).length > 0) {
      consumedPendingRef.current = {
        previousBaseline: previousValuesRef.current,
        isUserEdit,
        pendingUserEdits: { ...pendingUserEditsRefRef.current.current },
        ...(mode === 'flush' ? { dispatchedValues: valuesRef.current } : {}),
      };
    }

    // Explicit submit flows advance the baseline immediately so the autosave
    // effect does not re-dispatch the same diff while the patch is in flight.
    if (mode === 'consume') {
      previousValuesRef.current = valuesRef.current;
    }

    return isUserEdit ? changedFields : {};
  }, []);

  const getRetryExplicitPatch = useCallback(() => retryExplicitPatchRef.current, []);

  const confirmConsumedChanges = useCallback(() => {
    const consumed = consumedPendingRef.current;

    if (consumed) {
      pendingUserEditsRefRef.current.current = getUnconsumedPendingEdits(
        consumed.pendingUserEdits,
        pendingUserEditsRefRef.current.current,
      );
    }

    consumedPendingRef.current = null;
    retryExplicitPatchRef.current = {};
    // Prefer the latest Redux snapshot from `persistBaselineSyncRef` (server-
    // stamped fields). Until Redux reinitializes Formik after save, fall back
    // to the in-flight Formik snapshot so post-save edits diff correctly.
    previousValuesRef.current = latestReduxBaselineRef.current
      ? { ...latestReduxBaselineRef.current }
      : (consumed?.dispatchedValues ?? valuesRef.current);

    if (Object.keys(pendingUserEditsRefRef.current.current).length === 0) {
      dirtyRefRef.current.current = false;
    }

    if (previousValuesRef.current !== valuesRef.current) {
      flushPersistRef.current();
    }
  }, []);

  const revertConsumedChanges = useCallback(() => {
    const consumed = consumedPendingRef.current;

    if (!consumed) {
      return;
    }

    previousValuesRef.current = consumed.previousBaseline;
    pendingUserEditsRefRef.current.current = { ...consumed.pendingUserEdits };
    dirtyRefRef.current.current = consumed.isUserEdit;

    if (consumed.explicitFields && Object.keys(consumed.explicitFields).length > 0) {
      retryExplicitPatchRef.current = { ...consumed.explicitFields };
    }

    consumedPendingRef.current = null;

    let valuesChangedByExplicitRevert = false;

    if (consumed.explicitFields) {
      let revertedValues: ITemplate = { ...valuesRef.current };

      (Object.keys(consumed.explicitFields) as (keyof ITemplate)[]).forEach((key) => {
        if (valuesRef.current[key] !== consumed.previousBaseline[key]) {
          valuesChangedByExplicitRevert = true;
        }
        revertedValues = {
          ...revertedValues,
          [key]: consumed.previousBaseline[key],
        };
      });

      if (valuesChangedByExplicitRevert) {
        setValuesRef.current(revertedValues);
      }
    }

    // When explicit fields (e.g. isActive) were reverted in Formik, the values
    // effect will re-queue autosave. Otherwise consumed user edits are still
    // visible but no longer match the restored baseline — flush now so they
    // are not stranded without autosave (e.g. failed activation in
    // TemplateControlls never flips isActive in Formik before the patch).
    if (previousValuesRef.current !== valuesRef.current && !valuesChangedByExplicitRevert) {
      flushPersistRef.current();
    }
  }, []);

  const consumePendingChanges = useCallback((explicitFields?: Partial<ITemplate>) => {
    const changedFields = takePendingChanges('consume');

    if (explicitFields && Object.keys(explicitFields).length > 0) {
      if (consumedPendingRef.current) {
        consumedPendingRef.current.explicitFields = explicitFields;
      } else {
        consumedPendingRef.current = {
          previousBaseline: previousValuesRef.current,
          isUserEdit: false,
          pendingUserEdits: {},
          explicitFields,
        };
        previousValuesRef.current = valuesRef.current;
      }
    }

    return changedFields;
  }, [takePendingChanges]);

  const flushPersist = useCallback(() => {
    if (previousValuesRef.current === valuesRef.current) {
      return;
    }

    // Skip duplicate flushes for the same Formik snapshot while a patch is
    // already queued. A newer edit changes `valuesRef`, which supersedes the
    // in-flight patch via `takeLatest` and bumps `persistRequestIdRef`.
    if (pendingDispatchRef.current?.dispatchedValues === valuesRef.current) {
      return;
    }

    const changedFields = takePendingChanges('flush');

    if (Object.keys(changedFields).length > 0) {
      const requestId = allocateAutosavePersistRequestId();
      pendingDispatchRef.current = { requestId, dispatchedValues: valuesRef.current };
      dispatchRef.current(
        patchTemplate({
          changedFields,
          requestId,
          onSuccess: () => {
            if (!isAutosavePersistRequestCurrent(requestId)) {
              return;
            }
            pendingDispatchRef.current = null;
            confirmConsumedChanges();
          },
          onFailed: () => {
            if (!isAutosavePersistRequestCurrent(requestId)) {
              return;
            }
            pendingDispatchRef.current = null;
            revertConsumedChanges();
          },
        }),
      );
    }
  }, [takePendingChanges, confirmConsumedChanges, revertConsumedChanges]);

  flushPersistRef.current = flushPersist;

  const abandonPendingChanges = useCallback(() => {
    abandonAutosavePersistRequests();
    // Cancel a debounced autosave saga (`takeLatest`) without enqueueing a save.
    dispatchRef.current(setTemplateStatus(ETemplateStatus.Saved));
    dispatchRef.current(patchTemplate({ changedFields: {} }));
    previousValuesRef.current = valuesRef.current;
    dirtyRefRef.current.current = false;
    pendingUserEditsRefRef.current.current = {};
    consumedPendingRef.current = null;
    retryExplicitPatchRef.current = {};
    pendingDispatchRef.current = null;
  }, []);

  useEffect(() => {
    if (previousValuesRef.current === values) {
      return undefined;
    }

    if (
      dirtyRefRef.current.current
      && Object.keys(getChangedFields(previousValuesRef.current, values)).length > 0
    ) {
      dispatchRef.current(setTemplateStatus(ETemplateStatus.Saving));
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
      getRetryExplicitPatch,
      confirmConsumedChanges,
      revertConsumedChanges,
      abandonPendingChanges,
    }),
    [consumePendingChanges, getRetryExplicitPatch, confirmConsumedChanges, revertConsumedChanges, abandonPendingChanges],
  );

  return (
    <TemplatePersistContext.Provider value={persistContextValue}>
      {children as React.ReactElement}
    </TemplatePersistContext.Provider>
  );
}
