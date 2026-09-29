import { useCallback, useEffect, useMemo, useRef } from 'react';
import { useFormikContext } from 'formik';
import { useDispatch } from 'react-redux';

import { ITemplateClient } from '../../../types/template';
import { patchTemplate, setTemplateStatus } from '../../../redux/actions';
import { ETemplateStatus } from '../../../types/redux';
import {
  abandonAutosavePersistRequests,
  allocateAutosavePersistRequest,
  closeAutosavePersistScope,
  createAutosavePersistScope,
  isAutosavePersistRequestCurrent,
  TAutosavePersistRequest,
} from '../../../redux/template/persistRequest';
import { useTemplateField } from './contexts';
import { getChangedFields, getUnconsumedPendingEdits } from './templateFormUtils';
import { ITemplateFormPersistProviderProps, ITemplatePersistContextValue } from './types';

export const TEMPLATE_FORM_PERSIST_DEBOUNCE_MS = 350;

type TConsumedPending = {
  previousBaseline: ITemplateClient;
  isUserEdit: boolean;
  pendingUserEdits: Partial<ITemplateClient>;
  explicitFields?: Partial<ITemplateClient>;
  dispatchedValues?: ITemplateClient;
};

// External Formik reinitializes never dispatch a save, so they cannot cause a save loop.
export function useTemplatePersistContextValue({
  dirtyRef,
  pendingUserEditsRef,
  persistBaselineSyncRef,
}: Omit<ITemplateFormPersistProviderProps, 'children'>) {
  const { values } = useFormikContext<ITemplateClient>();
  const { setValues } = useTemplateField();
  const dispatch = useDispatch();
  const latestReduxBaselineRef = useRef<ITemplateClient | null>(null);
  const previousValuesRef = useRef<ITemplateClient>(values);
  const valuesRef = useRef(values);
  const dispatchRef = useRef(dispatch);
  const dirtyRefRef = useRef(dirtyRef);
  const pendingUserEditsRefRef = useRef(pendingUserEditsRef);
  const persistBaselineSyncRefRef = useRef(persistBaselineSyncRef);
  const consumedPendingRef = useRef<TConsumedPending | null>(null);
  const retryExplicitPatchRef = useRef<Partial<ITemplateClient>>({});
  const persistScopeRef = useRef(createAutosavePersistScope());
  const pendingDispatchRef = useRef<{
    requestId: TAutosavePersistRequest;
    dispatchedValues: ITemplateClient;
  } | null>(null);
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
      // While an explicit submit waits for confirm/revert, keep the pre-submit baseline.
      if (consumedPendingRef.current) {
        return;
      }

      // Mirror the latest Redux snapshot so server-stamped fields are not diffed as user edits.
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

    // Advance the baseline immediately so autosave does not re-dispatch the same diff.
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
    const latestBaseline = latestReduxBaselineRef.current;
    const savedValues = consumed?.dispatchedValues ?? valuesRef.current;
    const hasNewerReduxBaseline = latestBaseline && latestBaseline !== consumed?.previousBaseline;

    // Fall back to the dispatched form snapshot when the Redux baseline is still pre-edit.
    previousValuesRef.current = hasNewerReduxBaseline ? { ...latestBaseline } : savedValues;

    if (Object.keys(pendingUserEditsRefRef.current.current).length === 0) {
      dirtyRefRef.current.current = false;
    }

    if (previousValuesRef.current !== valuesRef.current) {
      flushPersistRef.current();
    }
  }, []);

  const revertConsumedChanges = useCallback((requeue = true) => {
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
      let revertedValues: ITemplateClient = { ...valuesRef.current };

      (Object.keys(consumed.explicitFields) as (keyof ITemplateClient)[]).forEach((key) => {
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
        // A failed explicit save is a system revert, not a user edit.
        pendingUserEditsRefRef.current.current = { ...consumed.pendingUserEdits };
        dirtyRefRef.current.current = consumed.isUserEdit;
      }
    }

    // Flush consumed user edits that no longer match the restored baseline so they are not stranded.
    if (requeue && previousValuesRef.current !== valuesRef.current && !valuesChangedByExplicitRevert) {
      flushPersistRef.current();
    }
  }, []);

  const consumePendingChanges = useCallback(
    (explicitFields?: Partial<ITemplateClient>) => {
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

        if (explicitFields.isActive === true && pendingUserEditsRefRef.current.current.isActive === false) {
          const pendingWithoutInactiveFlag = { ...pendingUserEditsRefRef.current.current };
          delete pendingWithoutInactiveFlag.isActive;
          pendingUserEditsRefRef.current.current = pendingWithoutInactiveFlag;
        }
      }

      return changedFields;
    },
    [takePendingChanges],
  );

  const flushPersist = useCallback(() => {
    if (previousValuesRef.current === valuesRef.current) {
      return;
    }

    // Skip duplicate flushes for a snapshot the queued patch already covers.
    if (pendingDispatchRef.current?.dispatchedValues === valuesRef.current) {
      return;
    }

    const changedFields = takePendingChanges('flush');

    if (Object.keys(changedFields).length > 0) {
      const requestId = allocateAutosavePersistRequest(persistScopeRef.current);
      pendingDispatchRef.current = { requestId, dispatchedValues: valuesRef.current };
      dispatchRef.current(
        patchTemplate({
          changedFields,
          requestId,
          templateSnapshot: valuesRef.current,
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
            // A failed save is retried explicitly, not re-dispatched here.
            revertConsumedChanges(false);
          },
        }),
      );
    }
  }, [takePendingChanges, confirmConsumedChanges, revertConsumedChanges]);

  flushPersistRef.current = flushPersist;

  const abandonPendingChanges = useCallback(() => {
    abandonAutosavePersistRequests(persistScopeRef.current);
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

    if (dirtyRefRef.current.current && Object.keys(getChangedFields(previousValuesRef.current, values)).length > 0) {
      dispatchRef.current(setTemplateStatus(ETemplateStatus.Saving));
    }

    const timeoutId = window.setTimeout(() => {
      flushPersist();
    }, TEMPLATE_FORM_PERSIST_DEBOUNCE_MS);

    return () => {
      window.clearTimeout(timeoutId);
    };
  }, [values, flushPersist]);

  useEffect(
    () => () => {
      flushPersistRef.current();
      closeAutosavePersistScope(persistScopeRef.current);
    },
    [],
  );

  const persistContextValue = useMemo<ITemplatePersistContextValue>(
    () => ({
      consumePendingChanges,
      getRetryExplicitPatch,
      confirmConsumedChanges,
      revertConsumedChanges,
      abandonPendingChanges,
    }),
    [
      consumePendingChanges,
      getRetryExplicitPatch,
      confirmConsumedChanges,
      revertConsumedChanges,
      abandonPendingChanges,
    ],
  );

  return persistContextValue;
}
