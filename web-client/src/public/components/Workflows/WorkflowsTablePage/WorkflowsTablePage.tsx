import * as React from 'react';

import { WorkflowsTableContainer } from './WorkflowsTable';

import { IWorkflowsProps } from '../types';
import { EPageTitle } from '../../../constants/defaultValues';
import { PageTitle } from '../../PageTitle';

import styles from './WorkflowsTablePage.css';

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
    <>
      <div className={styles['container']}>
        <PageTitle titleId={EPageTitle.Workflows} className={styles['title']} withUnderline={false} />
      </div>
      <WorkflowsTableContainer
        workflowsLoadingStatus={workflowsLoadingStatus}
        workflowsList={workflowsList}
        searchText={searchText}
        onSearch={onSearch}
        loadWorkflowsList={loadWorkflowsList}
        removeWorkflowFromList={removeWorkflowFromList}
        openWorkflowLogPopup={openWorkflowLogPopup}
      />
    </>
  );
};
