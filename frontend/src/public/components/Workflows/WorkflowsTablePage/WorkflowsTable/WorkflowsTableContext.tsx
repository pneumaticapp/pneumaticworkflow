import type { RefObject } from 'react';
import { createContext, useContext } from 'react';
import type { ITableViewContainerRef } from './types';

interface WorkflowsTableContextValue {
  ref: RefObject<ITableViewContainerRef> | null;
  isTableWiderThanScreen: boolean;
}

const WorkflowsTableContext = createContext<WorkflowsTableContextValue | null>(null);

export const WorkflowsTableProvider = WorkflowsTableContext.Provider;

export const useWorkflowsTableRef = () => {
  const context = useContext(WorkflowsTableContext);
  return context?.ref || null;
};

export const useIsTableWiderThanScreen = () => {
  const context = useContext(WorkflowsTableContext);
  return context?.isTableWiderThanScreen || false;
};
