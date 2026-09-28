import React, { createContext, useContext } from 'react';

import { ITaskFormScopeProviderProps, ITemplateFieldContextValue, ITemplatePersistContextValue } from './types';

export const TemplateFieldContext = createContext<ITemplateFieldContextValue | null>(null);
const TemplatePersistContext = createContext<ITemplatePersistContextValue | null>(null);
const TaskFormScopeContext = createContext<string | null>(null);

// The wrapped setters mark the form as user-dirty so the persist provider does not save server reinitializes (infinite save loop).
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

export function TaskFormScopeProvider({ taskUuid, children }: ITaskFormScopeProviderProps) {
  return <TaskFormScopeContext.Provider value={taskUuid}>{children}</TaskFormScopeContext.Provider>;
}

export function useTaskFormScope(): string {
  const taskUuid = useContext(TaskFormScopeContext);

  if (taskUuid === null) {
    throw new Error('useTaskForm must be used inside <TaskFormScopeProvider>');
  }

  return taskUuid;
}
