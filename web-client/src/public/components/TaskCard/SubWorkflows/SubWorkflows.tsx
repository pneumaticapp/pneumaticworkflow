import React, { useState } from 'react';
import classnames from 'classnames';

import { IWorkflowControllsProps, WorkflowControlls } from '../../Workflows/WorkflowControlls';
import { IWorkflow } from '../../../types/workflow';
import { Dropdown, Tooltip } from '../../UI';
import { MoreIcon, UrgentColorIcon } from '../../icons';
import { isArrayWithItems } from '../../../utils/helpers';

import { TLoadCurrentTaskPayload, TOpenWorkflowLogPopupPayload } from '../../../redux/actions';
import { WorkflowsProgress } from '../../Workflows/WorkflowsProgress';

import styles from './SubWorkflows.css';

export interface TSubWorkflowsProps {
  ancestorTaskId: number;
  workflows: IWorkflow[];
  loadCurrentTask(payload: TLoadCurrentTaskPayload): void;
  openWorkflowLogPopup(payload: TOpenWorkflowLogPopupPayload): void;
}

export function SubWorkflows({ workflows, ancestorTaskId, loadCurrentTask, openWorkflowLogPopup }: TSubWorkflowsProps) {
  const handleUpdateTask = () => loadCurrentTask({ taskId: ancestorTaskId });

  return (
    <div className={styles['embeded-workflows']}>
      {workflows.map((workflow) => (
        <SubWorkflowItem
          workflow={workflow}
          onWorkflowEnded={handleUpdateTask}
          onWorkflowSnoozed={handleUpdateTask}
          onWorkflowDeleted={handleUpdateTask}
          onWorkflowResumed={handleUpdateTask}
          handleOpenModal={() => openWorkflowLogPopup({ workflowId: workflow.id })}
        />
      ))}
    </div>
  );
}

type TSubWorkflowProps = Pick<
  IWorkflowControllsProps,
  'onWorkflowDeleted' | 'onWorkflowEnded' | 'onWorkflowResumed' | 'onWorkflowSnoozed' | 'onWorkflowReturn'
> & {
  workflow: IWorkflow;
  handleOpenModal(): void;
};

function SubWorkflowItem({
  workflow,
  onWorkflowDeleted,
  onWorkflowEnded,
  onWorkflowResumed,
  onWorkflowSnoozed,
  onWorkflowReturn,
  handleOpenModal,
}: TSubWorkflowProps) {
  const [isUrgent, setIsUrgent] = useState(workflow.isUrgent);

  const renderDropdown = () => {
    return (
      <WorkflowControlls
        workflow={workflow}
        onWorkflowEnded={onWorkflowEnded}
        onWorkflowSnoozed={onWorkflowSnoozed}
        onWorkflowDeleted={onWorkflowDeleted}
        onWorkflowResumed={onWorkflowResumed}
        onWorkflowReturn={onWorkflowReturn}
        onChangeUrgent={setIsUrgent}
      >
        {(controllOptions) => {
          if (!isArrayWithItems(controllOptions)) {
            return null;
          }

          return (
            <Dropdown
              renderToggle={(isOpen) => (
                <MoreIcon className={classnames(styles['workflow-embeded__more'], isOpen && styles['is-active'])} />
              )}
              options={controllOptions}
              direction="right"
            />
          );
        }}
      </WorkflowControlls>
    );
  };

  return (
    <div className={styles['embeded-workflows__item']}>
      <div className={styles['workflow-embeded']}>
        <div className={styles['workflow-embeded__content']}>
          <div className={styles['workflow-embeded__dropdown']}>{renderDropdown()}</div>
          <div className={styles['workflow-embeded__urgent']}>{isUrgent && <UrgentColorIcon />}</div>
          <Tooltip
            content={
              <div>
                <b>{workflow.template?.name}</b>
                <br></br>
                {workflow.name}
              </div>
            }
            containerClassName={styles['workflow-embeded__title']}
          >
            <button type="button" onClick={() => handleOpenModal()}>
              {workflow.name}
            </button>
          </Tooltip>
        </div>
        <div className={styles['workflow-embeded__progress']}>
          <WorkflowsProgress workflow={workflow} />
        </div>
      </div>
    </div>
  );
}
