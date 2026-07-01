import * as React from 'react';
import { createContext, useCallback, useContext, useEffect, useMemo, useRef } from 'react';
import { FormikProvider, useFormik, useFormikContext } from 'formik';
import { useDispatch } from 'react-redux';

import { ITemplate } from '../../types/template';
import { patchTemplate } from '../../redux/actions';

type TSetFieldValue = (field: string, value: unknown, shouldValidate?: boolean) => void;
type TSetValues = (values: ITemplate, shouldValidate?: boolean) => void;

interface ITemplateFieldContextValue {
  values: ITemplate;
  setFieldValue: TSetFieldValue;
  setValues: TSetValues;
}

interface ITemplatePersistContextValue {
  consumePendingChanges(): Partial<ITemplate>;
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
  const formik = useFormik<ITemplate>({
    initialValues,
    enableReinitialize: true,
    onSubmit: () => undefined,
  });

  const dirtyRef = useRef(false);

  const setFieldValue = useCallback<TSetFieldValue>(
    (field, value, shouldValidate) => {
      dirtyRef.current = true;
      formik.setFieldValue(field, value, shouldValidate);
    },
    [formik],
  );

  const setValues = useCallback<TSetValues>(
    (values, shouldValidate) => {
      dirtyRef.current = true;
      formik.setValues(values, shouldValidate);
    },
    [formik],
  );

  return { formik, setFieldValue, setValues, dirtyRef };
}

interface ITemplateFormProps {
  formik: ReturnType<typeof useFormik<ITemplate>>;
  setFieldValue: TSetFieldValue;
  setValues: TSetValues;
  dirtyRef: React.MutableRefObject<boolean>;
  children: React.ReactNode;
}

/**
 * Bundles the Formik provider, the wrapped-setter context, and the single
 * persist provider so `TemplateEdit` only has to render `<TemplateForm .../>`.
 */
export function TemplateForm({ formik, setFieldValue, setValues, dirtyRef, children }: ITemplateFormProps) {
  const { values } = formik;
  const fieldContextValue = useMemo<ITemplateFieldContextValue>(
    () => ({ values, setFieldValue, setValues }),
    [values, setFieldValue, setValues],
  );

  return (
    <FormikProvider value={formik}>
      <TemplateFieldContext.Provider value={fieldContextValue}>
        <TemplateFormPersistProvider dirtyRef={dirtyRef}>{children}</TemplateFormPersistProvider>
      </TemplateFieldContext.Provider>
    </FormikProvider>
  );
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

// Keep in sync with `patchTemplateSaga` in redux/template/saga.ts. The saga
// flips `isActive` to false server-side whenever a non-activation field changes
// and only reflects it back to Formik via a Redux `setTemplate` reinitialize.
// Mirroring that decision here lets Formik (and the controls that read from it
// via `useTemplateField`) deactivate immediately, instead of staying "active"
// through the persist flush + saga + reinitialize round-trip.
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

interface ITemplateFormPersistProviderProps {
  dirtyRef: React.MutableRefObject<boolean>;
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
 * When a user edit touches a non-activation field, we also flip `isActive` to
 * false in Formik right away — the saga makes the same call server-side, but
 * only reinitializes Formik after the save round-trip, so without this the
 * controls would keep rendering the template as active (no draft warning, no
 * enable button) until Redux catches up.
 */
export function TemplateFormPersistProvider({ dirtyRef, children }: ITemplateFormPersistProviderProps) {
  const { values, setFieldValue } = useFormikContext<ITemplate>();
  const dispatch = useDispatch();
  const previousValuesRef = useRef<ITemplate>(values);
  const valuesRef = useRef(values);
  const dispatchRef = useRef(dispatch);
  const dirtyRefRef = useRef(dirtyRef);
  const setFieldValueRef = useRef(setFieldValue);

  valuesRef.current = values;
  dispatchRef.current = dispatch;
  dirtyRefRef.current = dirtyRef;
  setFieldValueRef.current = setFieldValue;

  const consumePendingChanges = useCallback(() => {
    if (previousValuesRef.current === valuesRef.current) {
      return {};
    }

    const changedFields = getChangedFields(previousValuesRef.current, valuesRef.current);
    const isUserEdit = dirtyRefRef.current.current;
    previousValuesRef.current = valuesRef.current;
    dirtyRefRef.current.current = false;

    return isUserEdit ? changedFields : {};
  }, []);

  const flushPersist = useCallback(() => {
    const previousValues = previousValuesRef.current;
    const changedFields = consumePendingChanges();

    if (Object.keys(changedFields).length > 0) {
      if (shouldDeactivateTemplate(changedFields, previousValues)) {
        setFieldValueRef.current('isActive', false, false);
      }

      dispatchRef.current(patchTemplate({ changedFields }));
    }
  }, [consumePendingChanges]);

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
    () => ({ consumePendingChanges }),
    [consumePendingChanges],
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
