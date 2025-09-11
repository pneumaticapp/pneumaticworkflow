import React, { createContext, useContext } from 'react';
import { TableViewContainerRef } from '.';

interface WorkflowsTableContextValue {
  ref: React.RefObject<TableViewContainerRef> | null;
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
