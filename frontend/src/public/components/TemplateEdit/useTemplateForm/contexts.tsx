import * as React from 'react';
import { createContext, useContext } from 'react';

import {
  ITaskFormScopeProviderProps,
  ITemplateFieldContextValue,
  ITemplatePersistContextValue,
} from './types';

export const TemplateFieldContext = createContext<ITemplateFieldContextValue | null>(null);
const TemplatePersistContext = createContext<ITemplatePersistContextValue | null>(null);
const TaskFormScopeContext = createContext<string | null>(null);

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

export { TemplatePersistContext };

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
