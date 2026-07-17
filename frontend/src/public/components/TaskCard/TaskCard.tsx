import React, { useCallback, useEffect, useRef, useState } from 'react';
import classnames from 'classnames';
import { useIntl } from 'react-intl';

import { ETaskStatus } from '../../redux/actions';
import { autoFocusFirstField } from '../../utils/autoFocusFirstField';
import { isEmptyArray } from '../../utils/helpers';
import { RichText } from '../RichText';
import { DueIn } from '../DueIn';
import { InfoIcon } from '../icons';
import { SubWorkflowsContainer } from './SubWorkflows';
import { HelpModal } from './HelpModal/HelpModal';
import { TaskCarkSkeleton } from './TaskCarkSkeleton';
import { createChecklistExtension, createProgressbarExtension } from './checklist';
import { TaskActions } from './TaskActions';
import { TaskCardHeader } from './TaskCardHeader';
import { TaskOutputFields } from './TaskOutputFields';
import { TaskPerformers } from './TaskPerformers';
import { TaskWorkflowLog } from './TaskWorkflowLog';
import { useTaskOutput } from './hooks/useTaskOutput';
import { ETaskCardViewMode, ITaskCardProps, ITaskCardWrapperProps } from './types';

import styles from './TaskCard.css';

export { ETaskCardViewMode } from './types';
export type { ITaskCardProps, ITaskCardWrapperProps } from './types';

export function TaskCard({
  task,
  viewMode,
  workflowLog,
  workflow,
  isWorkflowLoading,
  status,
  accountId,
  users,
  authUser,
  helpText,
  changeTaskWorkflowLog,
  setCurrentTask,
  setTaskCompleted,
  setTaskReverted,
  sendTaskWorkflowLogComments,
  changeTaskWorkflowLogViewSettings,
  toggleTaskSkippedTasksVisibility,
  clearWorkflow,
  addTaskPerformer,
  removeTaskPerformer,
  openWorkflowLogPopup,
  setDueDate,
  deleteDueDate,
  openSelectTemplateModal,
}: ITaskCardProps) {
  const { formatMessage } = useIntl();
  const wrapperRef = useRef<HTMLDivElement>(null);
  const [isHelpModalOpen, setIsHelpModalOpen] = useState(false);
  const [uploadingFieldNames, setUploadingFieldNames] = useState<Set<string>>(() => new Set());
  const {
    outputValues,
    fieldsetOutputValues,
    editField,
    editFieldsetField,
    flushOutputs,
  } = useTaskOutput(task);
  const helpTextLocal = helpText ?? workflow?.description ?? null;
  const isSubmitting = status === ETaskStatus.Completing || status === ETaskStatus.Returning;
  const handleUploadStateChange = useCallback((apiName: string, isUploading: boolean) => {
    setUploadingFieldNames((currentNames) => {
      const nextNames = new Set(currentNames);
      if (isUploading) nextNames.add(apiName);
      else nextNames.delete(apiName);

      return nextNames;
    });
  }, []);

  useEffect(() => {
    autoFocusFirstField(wrapperRef.current);

    return () => {
      setCurrentTask(null);
      clearWorkflow();
    };
  }, []);

  return (
    <>
      {helpTextLocal && (
        <HelpModal isOpen={isHelpModalOpen} onClose={() => setIsHelpModalOpen(false)} helpText={helpTextLocal} />
      )}
      <div
        ref={wrapperRef}
        className={classnames(styles.container, viewMode === ETaskCardViewMode.Guest && styles.container_guest)}
      >
        <TaskCardHeader
          task={task}
          viewMode={viewMode}
          workflowLog={workflowLog}
          openWorkflowLogPopup={openWorkflowLogPopup}
        />
        <div className={styles.description}>
          <RichText
            text={task.description}
            interactiveChecklists
            renderExtensions={[...createChecklistExtension(task), ...createProgressbarExtension(task)]}
            hideIcon
          />
        </div>
        <div className={styles.info}>
          <div className={styles.performers}>
            <TaskPerformers
              task={task}
              viewMode={viewMode}
              workflow={workflow}
              status={status}
              users={users}
              authUser={authUser}
              addTaskPerformer={addTaskPerformer}
              removeTaskPerformer={removeTaskPerformer}
            />
          </div>
          {viewMode !== ETaskCardViewMode.Guest && !task.isReadOnlyViewer && (
            <DueIn
              withTime
              timezone={authUser.timezone}
              dateFmt={authUser.dateFmt}
              dueDate={task.dueDate}
              onSave={setDueDate}
              onRemove={deleteDueDate}
              containerClassName={styles['due-in']}
              dateCompleted={task.dateCompleted || task.workflow.dateCompleted}
            />
          )}
          {task.isReadOnlyViewer && task.dueDate && (
            <DueIn
              withTime
              timezone={authUser.timezone}
              dateFmt={authUser.dateFmt}
              dueDate={task.dueDate}
              containerClassName={styles['due-in']}
              dateCompleted={task.dateCompleted || task.workflow.dateCompleted}
              readOnly
            />
          )}
        </div>
        <div className={classnames(
          styles['complete-form'],
          task.isReadOnlyViewer && styles['complete-form_readonly'],
        )}>
          {helpTextLocal && (
            <button
              type="button"
              className={classnames(styles['help-trigger'], 'no-print')}
              onClick={() => setIsHelpModalOpen(true)}
            >
              <span className={styles['help-trigger__label']}>
                {formatMessage({ id: 'task.help', defaultMessage: 'Help' })}
              </span>
              <InfoIcon className={styles['help-trigger__icon']} />
            </button>
          )}
          <TaskOutputFields
            accountId={accountId}
            outputValues={outputValues}
            fieldsetOutputValues={fieldsetOutputValues}
            status={status}
            taskId={task.id}
            editField={editField}
            editFieldsetField={editFieldsetField}
            isDisabled={isSubmitting}
            onUploadStateChange={handleUploadStateChange}
          />
          <TaskActions
            task={task}
            viewMode={viewMode}
            status={status}
            outputValues={outputValues}
            fieldsetOutputValues={fieldsetOutputValues}
            flushOutputs={flushOutputs}
            isOutputUploading={uploadingFieldNames.size > 0}
            setTaskCompleted={setTaskCompleted}
            setTaskReverted={setTaskReverted}
            openSelectTemplateModal={openSelectTemplateModal}
          />
          {viewMode !== ETaskCardViewMode.Guest && !isEmptyArray(task.subWorkflows) && (
            <SubWorkflowsContainer workflows={task.subWorkflows} ancestorTaskId={task.id} />
          )}
        </div>
        <TaskWorkflowLog
          task={task}
          viewMode={viewMode}
          workflowLog={workflowLog}
          workflow={workflow}
          status={status}
          isWorkflowLoading={isWorkflowLoading}
          changeTaskWorkflowLog={changeTaskWorkflowLog}
          sendTaskWorkflowLogComments={sendTaskWorkflowLogComments}
          changeTaskWorkflowLogViewSettings={changeTaskWorkflowLogViewSettings}
          toggleTaskSkippedTasksVisibility={toggleTaskSkippedTasksVisibility}
        />
      </div>
    </>
  );
}

export function TaskCardWrapper({ task, status, ...restProps }: ITaskCardWrapperProps) {
  if (status === ETaskStatus.Loading) return <TaskCarkSkeleton />;
  if (!task) return null;

  return <TaskCard task={task} status={status} {...restProps} />;
}
