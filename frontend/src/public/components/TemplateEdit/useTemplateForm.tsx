import * as React from 'react';
import { createContext, useCallback, useContext, useEffect, useMemo, useRef } from 'react';
import { FormikProvider, useFormik, useFormikContext } from 'formik';
import { useDispatch } from 'react-redux';

import { ITemplate, ITemplateTask, IKickoff } from '../../types/template';
import { patchTemplate } from '../../redux/actions';
import { cleanTemplateReferences } from '../../utils/template';

type TSetFieldValue = (field: string, value: unknown, shouldValidate?: boolean) => void;
type TSetValues = (values: ITemplate, shouldValidate?: boolean) => void;

interface ITemplateFieldContextValue {
  values: ITemplate;
  setFieldValue: TSetFieldValue;
  setValues: TSetValues;
}

interface ITemplatePersistContextValue {
  consumePendingChanges(): Partial<ITemplate>;
  /** Clears a revert snapshot after an explicit `patchTemplate` succeeds. */
  confirmConsumedChanges(): void;
  /** Restores the persist baseline when an explicit `patchTemplate` fails. */
  revertConsumedChanges(): void;
  /** Drops uncommitted edits without dispatching (e.g. after "Discard changes"). */
  abandonPendingChanges(): void;
}

const TemplateFieldContext = createContext<ITemplateFieldContextValue | null>(null);
const TemplatePersistContext = createContext<ITemplatePersistContextValue | null>(null);

export { TemplateFieldContext };

/**
 * Access the root Edit Template form state + the wrapped setters.
 *
 * `setFieldValue` / `setValues` mark the form as user-dirty before delegating
 * to Formik, so `TemplateFormPersistProvider` knows which value changes come
 * from user edits (and should be saved) vs. external reinitializes from the
 * server (which must not re-trigger a save — otherwise the server-stamped
 * `dateUpdated`/`publicUrl` fields would cause an infinite save loop).
 *
 * Use this instead of `useFormikContext().setFieldValue` everywhere on the
 * Edit Template page so saving stays centralized.
 */
export function useTemplateField(): ITemplateFieldContextValue {
  const ctx = useContext(TemplateFieldContext);

  if (!ctx) {
    throw new Error('useTemplateField must be used inside the Edit Template form provider');
  }

  return ctx;
}

export function useTemplatePersist(): ITemplatePersistContextValue {
  const ctx = useContext(TemplatePersistContext);

  if (!ctx) {
    throw new Error('useTemplatePersist must be used inside the Edit Template form provider');
  }

  return ctx;
}

function setNestedFieldValue(obj: ITemplate, path: string, value: unknown): ITemplate {
  const taskPathMatch = path.match(/^tasks\.(\d+)(?:\.(.+))?$/);

  if (taskPathMatch) {
    const index = Number(taskPathMatch[1]);
    const taskField = taskPathMatch[2];
    const tasks = [...obj.tasks];

    if (!taskField) {
      tasks[index] = value as ITemplateTask;
    } else {
      tasks[index] = {
        ...tasks[index],
        [taskField]: value,
      };
    }

    return { ...obj, tasks };
  }

  return { ...obj, [path]: value };
}

function applyPendingEdits(initialValues: ITemplate, pendingEdits: Partial<ITemplate>): ITemplate {
  if (Object.keys(pendingEdits).length === 0) {
    return initialValues;
  }

  let mergedValues: ITemplate = { ...initialValues, ...pendingEdits };

  if (pendingEdits.tasks && initialValues.tasks) {
    mergedValues = {
      ...mergedValues,
      tasks: mergePreservedTasks(initialValues.tasks, pendingEdits.tasks),
    };
  }

  return mergedValues;
}

function overlayPendingEdits(formikValues: ITemplate, pendingEdits: Partial<ITemplate>): ITemplate {
  if (Object.keys(pendingEdits).length === 0) {
    return formikValues;
  }

  return applyPendingEdits(formikValues, pendingEdits);
}

function mergePreservedTasks(
  incomingTasks: ITemplateTask[],
  preservedTasks: ITemplateTask[],
): ITemplateTask[] {
  const preservedByUuid = new Map(preservedTasks.map((task) => [task.uuid, task]));

  const mergedIncoming = incomingTasks.map((incoming) => {
    const preserved = preservedByUuid.get(incoming.uuid);

    if (!preserved || preserved === incoming) {
      return preserved || incoming;
    }

    const onlyAncestorsDiffer = (Object.keys(preserved) as (keyof ITemplateTask)[]).every(
      (key) => key === 'ancestors' || preserved[key] === incoming[key],
    );

    return onlyAncestorsDiffer ? { ...preserved, ancestors: incoming.ancestors } : preserved;
  });

  const incomingUuids = new Set(incomingTasks.map((task) => task.uuid));
  const preservedOnlyTasks = preservedTasks.filter((task) => !incomingUuids.has(task.uuid));

  return [...mergedIncoming, ...preservedOnlyTasks];
}

function getKickoffFieldApiNames(kickoff: IKickoff): string[] {
  return (kickoff.fields || [])
    .map((field) => field.apiName)
    .filter(Boolean)
    .sort();
}

function didKickoffFieldsChange(previous: IKickoff, next: IKickoff): boolean {
  const previousNames = getKickoffFieldApiNames(previous);
  const nextNames = getKickoffFieldApiNames(next);

  return previousNames.length !== nextNames.length
    || previousNames.some((name, index) => name !== nextNames[index]);
}

function shouldRunReferenceCleanup(field: string, previous: ITemplate, next: ITemplate): boolean {
  if (field === 'tasks' || field.startsWith('tasks.')) {
    return true;
  }

  if (field === 'kickoff') {
    return didKickoffFieldsChange(previous.kickoff, next.kickoff);
  }

  return false;
}

function applyReferenceCleanup(template: ITemplate): ITemplate {
  const cleaned = cleanTemplateReferences(template);
  const wfNameTemplate = template.wfNameTemplate == null && cleaned.wfNameTemplate === ''
    ? template.wfNameTemplate
    : cleaned.wfNameTemplate;

  return {
    ...template,
    tasks: cleaned.tasks,
    wfNameTemplate,
  };
}

function getChangedFields(previous: ITemplate, next: ITemplate): Partial<ITemplate> {
  const changedFields: Partial<ITemplate> = {};

  (Object.keys(next) as (keyof ITemplate)[]).forEach((key) => {
    if (previous[key] !== next[key]) {
      (changedFields[key] as ITemplate[keyof ITemplate]) = next[key];
    }
  });

  return changedFields;
}

/**
 * Root Formik context for the whole Edit Template page.
 *
 * The entire `ITemplate` (name, description, kickoff, tasks, owners, share
 * settings, toggles, ...) lives in a single Formik state. Every field binds to
 * it via `useTemplateField`; nothing dispatches Redux field updates from
 * individual inputs anymore. Saving happens from one place only —
 * `TemplateFormPersistProvider` — which dispatches a single `patchTemplate`
 * action for user edits (the saga then debounces + saves). Explicit "submit"
 * flows (e.g. activating the template) still go through `patchTemplate` with
 * callbacks, so both onChange and submit share one save path.
 */
export function useTemplateForm(initialValues: ITemplate) {
  const dirtyRef = useRef(false);
  const pendingUserEditsRef = useRef<Partial<ITemplate>>({});
  const lastSyncedInitialValuesRef = useRef(initialValues);
  const persistBaselineSyncRef = useRef<((reduxTemplate: ITemplate, currentValues: ITemplate) => void) | null>(null);

  const formik = useFormik<ITemplate>({
    initialValues,
    enableReinitialize: false,
    onSubmit: () => undefined,
  });

  // Redux `template` updates must be merged into Formik without discarding edits
  // that still live only in the form (e.g. typed while a save is in flight).
  // Wrapped setters accumulate those edits in `pendingUserEditsRef` because a
  // Redux snapshot can land in the same render and overwrite Formik state.
  if (lastSyncedInitialValuesRef.current !== initialValues) {
    const rawPending = dirtyRef.current ? pendingUserEditsRef.current : {};

    if (Object.keys(rawPending).length > 0) {
      const mergedValues = applyPendingEdits(initialValues, rawPending);

      pendingUserEditsRef.current = getChangedFields(initialValues, mergedValues);
      dirtyRef.current = true;
      formik.setValues(mergedValues, false);
      persistBaselineSyncRef.current?.(initialValues, mergedValues);
    } else {
      pendingUserEditsRef.current = {};
      dirtyRef.current = false;
      formik.resetForm({ values: initialValues });
    }

    lastSyncedInitialValuesRef.current = initialValues;
  }

  const setFieldValue = useCallback<TSetFieldValue>(
    (field, value, shouldValidate) => {
      dirtyRef.current = true;
      const currentValues = overlayPendingEdits(formik.values, pendingUserEditsRef.current);
      let nextValues = setNestedFieldValue(currentValues, field, value);
      const runCleanup = shouldRunReferenceCleanup(field, currentValues, nextValues);

      if (runCleanup) {
        nextValues = applyReferenceCleanup(nextValues);
      }

      nextValues = applyImmediateDeactivation(currentValues, nextValues);
      pendingUserEditsRef.current = getChangedFields(lastSyncedInitialValuesRef.current, nextValues);

      if (runCleanup || nextValues.isActive !== currentValues.isActive) {
        formik.setValues(nextValues, shouldValidate);
      } else {
        formik.setFieldValue(field, value, shouldValidate);
      }
    },
    [formik],
  );

  const setValues = useCallback<TSetValues>(
    (values, shouldValidate) => {
      dirtyRef.current = true;
      const currentValues = overlayPendingEdits(formik.values, pendingUserEditsRef.current);
      const nextValues = applyImmediateDeactivation(currentValues, values);
      pendingUserEditsRef.current = getChangedFields(lastSyncedInitialValuesRef.current, nextValues);
      formik.setValues(nextValues, shouldValidate);
    },
    [formik, formik.values],
  );

  return { formik, setFieldValue, setValues, dirtyRef, pendingUserEditsRef, persistBaselineSyncRef };
}

interface ITemplateFormProps {
  formik: ReturnType<typeof useFormik<ITemplate>>;
  setFieldValue: TSetFieldValue;
  setValues: TSetValues;
  dirtyRef: React.MutableRefObject<boolean>;
  pendingUserEditsRef: React.MutableRefObject<Partial<ITemplate>>;
  persistBaselineSyncRef: React.MutableRefObject<((reduxTemplate: ITemplate, currentValues: ITemplate) => void) | null>;
  children: React.ReactNode;
}

/**
 * Bundles the Formik provider, the wrapped-setter context, and the single
 * persist provider so `TemplateEdit` only has to render `<TemplateForm .../>`.
 */
export function TemplateForm({
  formik,
  setFieldValue,
  setValues,
  dirtyRef,
  pendingUserEditsRef,
  persistBaselineSyncRef,
  children,
}: ITemplateFormProps) {
  const { values } = formik;
  const fieldContextValue = useMemo<ITemplateFieldContextValue>(
    () => ({ values, setFieldValue, setValues }),
    [values, setFieldValue, setValues],
  );

  return (
    <FormikProvider value={formik}>
      <TemplateFieldContext.Provider value={fieldContextValue}>
        <TemplateFormPersistProvider
          dirtyRef={dirtyRef}
          pendingUserEditsRef={pendingUserEditsRef}
          persistBaselineSyncRef={persistBaselineSyncRef}
        >
          {children}
        </TemplateFormPersistProvider>
      </TemplateFieldContext.Provider>
    </FormikProvider>
  );
}

// Keep in sync with `patchTemplateSaga` in redux/template/saga.ts. The saga
// flips `isActive` to false server-side whenever a non-activation field changes
// and only reflects it back to Formik via a Redux `setTemplate` reinitialize.
// `applyImmediateDeactivation` mirrors that decision in the wrapped setters so
// Formik (and controls like `RouteLeavingGuard` that read from it) deactivate
// on the same tick as the edit instead of waiting for the deferred persist flush.
const NON_DEACTIVATIVE_FIELDS: (keyof ITemplate)[] = ['isActive', 'isPublic', 'publicUrl'];

function shouldDeactivateTemplate(
  changedFields: Partial<ITemplate>,
  previousTemplate: ITemplate,
): boolean {
  if (changedFields.isActive === true) {
    return false;
  }

  let shouldDeactivate = Object.keys(changedFields).some(
    (key) => !NON_DEACTIVATIVE_FIELDS.includes(key as keyof ITemplate),
  );

  if (Object.keys(changedFields).length === 1 && Object.prototype.hasOwnProperty.call(changedFields, 'kickoff')) {
    shouldDeactivate =
      changedFields.kickoff?.description === previousTemplate.kickoff.description
        ? shouldDeactivate
        : false;
  }

  return shouldDeactivate;
}

function applyImmediateDeactivation(previous: ITemplate, next: ITemplate): ITemplate {
  if (!previous.isActive) {
    return next;
  }

  const changedFields = getChangedFields(previous, next);

  if (shouldDeactivateTemplate(changedFields, previous)) {
    return { ...next, isActive: false };
  }

  return next;
}

interface ITemplateFormPersistProviderProps {
  dirtyRef: React.MutableRefObject<boolean>;
  pendingUserEditsRef: React.MutableRefObject<Partial<ITemplate>>;
  persistBaselineSyncRef: React.MutableRefObject<((reduxTemplate: ITemplate, currentValues: ITemplate) => void) | null>;
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
    persistBaselineSyncRefRef.current.current = (reduxTemplate, currentValues) => {
      const pendingEdits = pendingUserEditsRefRef.current.current;
      previousValuesRef.current = { ...currentValues };

      (Object.keys(pendingEdits) as (keyof ITemplate)[]).forEach((key) => {
        (previousValuesRef.current[key] as ITemplate[keyof ITemplate]) = reduxTemplate[key];
      });
    };

    return () => {
      persistBaselineSyncRefRef.current.current = null;
    };
  }, []);

  const consumedPendingRef = useRef<{ previousBaseline: ITemplate; isUserEdit: boolean } | null>(null);

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
    consumedPendingRef.current = null;
    pendingUserEditsRefRef.current.current = {};
  }, []);

  const revertConsumedChanges = useCallback(() => {
    const consumed = consumedPendingRef.current;

    if (!consumed) {
      return;
    }

    previousValuesRef.current = consumed.previousBaseline;
    dirtyRefRef.current.current = consumed.isUserEdit;
    pendingUserEditsRefRef.current.current = getChangedFields(
      consumed.previousBaseline,
      valuesRef.current,
    );
    consumedPendingRef.current = null;
  }, []);

  const abandonPendingChanges = useCallback(() => {
    previousValuesRef.current = valuesRef.current;
    dirtyRefRef.current.current = false;
    pendingUserEditsRefRef.current.current = {};
    consumedPendingRef.current = null;
  }, []);

  const flushPersist = useCallback(() => {
    const changedFields = takePendingChanges();

    if (Object.keys(changedFields).length > 0) {
      dispatchRef.current(patchTemplate({ changedFields }));
    }
  }, [takePendingChanges]);

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

const TaskFormScopeContext = createContext<string | null>(null);

interface ITaskFormScopeProviderProps {
  taskUuid: string;
  children: React.ReactNode;
}

/**
 * Scopes the task form sections to a single task inside the root `ITemplate`
 * Formik context. Descendants call `useTaskForm()` (no args) and get the
 * matching task + updaters bound to `tasks[index].<field>`.
 */
export function TaskFormScopeProvider({ taskUuid, children }: ITaskFormScopeProviderProps) {
  return <TaskFormScopeContext.Provider value={taskUuid}>{children}</TaskFormScopeContext.Provider>;
}

/**
 * Returns the uuid of the task currently scoped via `TaskFormScopeProvider`.
 * Throws if used outside the provider.
 */
export function useTaskFormScope(): string {
  const taskUuid = useContext(TaskFormScopeContext);

  if (taskUuid === null) {
    throw new Error('useTaskForm must be used inside <TaskFormScopeProvider>');
  }

  return taskUuid;
}
