import React, { useState } from 'react';
import classnames from 'classnames';
import { useIntl } from 'react-intl';

import { ETaskStatus } from '../../redux/actions';
import { EWorkflowStatus } from '../../types/workflow';
import { useCheckDevice } from '../../hooks/useCheckDevice';
import { Button } from '../UI/Buttons/Button';
import { Tooltip } from '../UI';
import { DateFormat } from '../UI/DateFormat';
import { DoneInfoIcon, PlayLogoIcon, ReturnTaskInfoIcon, ReturnToIcon } from '../icons';
import { ReturnModal } from './ReturnModal';
import { ETaskCardViewMode, TTaskActionsProps } from './types';

import styles from './TaskCard.css';

export function TaskActions({
  task,
  viewMode,
  status,
  outputValues,
  flushOutputs,
  isOutputUploading,
  setTaskCompleted,
  setTaskReverted,
  openSelectTemplateModal,
}: TTaskActionsProps) {
  const { formatMessage } = useIntl();
  const { isMobile } = useCheckDevice();
  const [isReturnModalOpen, setIsReturnModalOpen] = useState(false);
  const { id: taskId, dateStarted, dateCompleted } = task;
  const isSubmitting = status === ETaskStatus.Completing || status === ETaskStatus.Returning;
  const isActionBlocked = isOutputUploading || isSubmitting;

  const handleReturnTask = (comment: string) => {
    if (isActionBlocked) return;

    flushOutputs();
    setTaskReverted({
      taskId,
      viewMode,
      comment,
      clearOutputTaskIds: [taskId, ...task.revertTasks.map(({ id }) => id)],
    });
    setIsReturnModalOpen(false);
  };

  if (task.isReadOnlyViewer) return null;

  if (status === ETaskStatus.Completed || task.workflow.status === EWorkflowStatus.Finished) {
    const completedAt = dateCompleted || task.workflow.dateCompleted;
    return (
      <div className={styles.completed}>
        <DoneInfoIcon />
        <p className={styles['completed__text']}>
          {completedAt ? (
            <>
              {formatMessage({ id: 'task.completed-with-date' })}
              <span className={styles['completed__text-date']}><DateFormat date={completedAt} /></span>
            </>
          ) : formatMessage({ id: 'task.completed' })}
        </p>
      </div>
    );
  }

  if (!dateStarted && !dateCompleted) {
    return (
      <div className={styles.returned}>
        <ReturnTaskInfoIcon />
        <p className={styles['returned__text']}>{formatMessage({ id: 'task.returned' })}</p>
      </div>
    );
  }

  const embeddedWorkflowsComplete = task.subWorkflows.every(
    ({ status: workflowStatus }) => workflowStatus === EWorkflowStatus.Finished,
  );
  const actionsDisabled = !embeddedWorkflowsComplete || isActionBlocked;
  const completeButton = (
    <Button
      isLoading={status === ETaskStatus.Completing}
      onClick={() => {
        if (actionsDisabled) return;
        flushOutputs();
        setTaskCompleted({ taskId, viewMode, output: outputValues });
      }}
      label={formatMessage({ id: 'processes.complete-task' })}
      size="md"
      disabled={actionsDisabled}
      buttonStyle="yellow"
    />
  );

  return (
    <>
      <ReturnModal
        isOpen={isReturnModalOpen}
        isConfirmDisabled={isActionBlocked}
        onClose={() => setIsReturnModalOpen(false)}
        onConfirm={handleReturnTask}
      />
      <div className={classnames(styles.buttons, 'no-print')}>
        <div className={styles['buttons__complete']}>
          {embeddedWorkflowsComplete ? completeButton : (
            <Tooltip content={formatMessage({ id: 'task.need-complete-embedded-processes' })}>
              <div>{completeButton}</div>
            </Tooltip>
          )}
        </div>
        {viewMode !== ETaskCardViewMode.Guest && task.revertTasks.length > 0 && (
          <Tooltip content={embeddedWorkflowsComplete
            ? formatMessage({ id: 'tasks.task-return-hint' })
            : formatMessage({ id: 'task.need-return-embedded-processes' })}
          >
            <div>
              <Button
                disabled={actionsDisabled}
                onClick={() => setIsReturnModalOpen(true)}
                label={isMobile ? undefined : formatMessage({ id: 'processes.return-task' })}
                icon={isMobile ? ReturnToIcon : undefined}
                buttonStyle="transparent-black"
                className={styles['buttons__return']}
                size="md"
                isLoading={status === ETaskStatus.Returning}
              />
            </div>
          </Tooltip>
        )}
        {viewMode !== ETaskCardViewMode.Guest && (
          <Tooltip content={formatMessage({ id: 'task.delegate' })}>
            <Button
              disabled={isActionBlocked}
              onClick={() => openSelectTemplateModal({ ancestorTaskId: taskId })}
              icon={PlayLogoIcon}
              buttonStyle="transparent-black"
              className={styles['buttons__return']}
              size="md"
              isLoading={status === ETaskStatus.Returning}
            />
          </Tooltip>
        )}
      </div>
    </>
  );
}
