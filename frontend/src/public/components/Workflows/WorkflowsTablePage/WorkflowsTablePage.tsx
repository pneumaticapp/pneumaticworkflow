import React from 'react';
import { IWorkflowsProps } from '../types';
import { WorkflowsTableContainer } from './WorkflowsTable';

export const WorkflowsTablePage = function Workflows({
  workflowsLoadingStatus,
  workflowsList,
  searchText,
  onSearch,
  loadWorkflowsList,
  openWorkflowLogPopup,
  removeWorkflowFromList,
}: IWorkflowsProps) {
  return (
    <WorkflowsTableContainer
      workflowsLoadingStatus={workflowsLoadingStatus}
      workflowsList={workflowsList}
      searchText={searchText}
      onSearch={onSearch}
      loadWorkflowsList={loadWorkflowsList}
      removeWorkflowFromList={removeWorkflowFromList}
      openWorkflowLogPopup={openWorkflowLogPopup}
    />
  );
};
