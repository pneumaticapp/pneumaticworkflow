import React from 'react';

import { ETaskStatus } from '../../redux/actions';
import { EWorkflowsLogSorting, EWorkflowStatus } from '../../types/workflow';
import { WorkflowLog } from '../Workflows/WorkflowLog';
import { WorkflowLogSkeleton } from '../Workflows/WorkflowLog/WorkflowLogSkeleton';
import { ETaskCardViewMode, TTaskWorkflowLogProps } from './types';

const MINIMIZED_LOG_MAX_EVENTS = 5;

export function TaskWorkflowLog({
  task,
  viewMode,
  workflowLog,
  workflow,
  status,
  isWorkflowLoading,
  changeTaskWorkflowLog,
  sendTaskWorkflowLogComments,
  changeTaskWorkflowLogViewSettings,
  toggleTaskSkippedTasksVisibility,
}: TTaskWorkflowLogProps) {
  if (isWorkflowLoading) return <WorkflowLogSkeleton />;

  return (
    <WorkflowLog
      workflowStatus={workflow?.status || EWorkflowStatus.Running}
      theme="beige"
      isLoading={workflowLog.isLoading}
      items={workflowLog.items}
      sorting={workflowLog.sorting}
      isCommentsShown={workflowLog.isCommentsShown}
      isOnlyAttachmentsShown={workflowLog.isOnlyAttachmentsShown}
      isSkippedTasksShown={workflowLog.isSkippedTasksShown}
      workflowId={workflowLog.workflowId}
      includeHeader
      isLogMinimized={false}
      areTasksClickable={viewMode === ETaskCardViewMode.Single}
      minimizedLogMaxEvents={MINIMIZED_LOG_MAX_EVENTS}
      isCommentFieldHidden={viewMode === ETaskCardViewMode.Guest && status === ETaskStatus.Completed}
      areRightTogglesHidden
      sendComment={sendTaskWorkflowLogComments}
      changeWorkflowLogViewSettings={changeTaskWorkflowLogViewSettings}
      toggleSkippedTasksVisibility={toggleTaskSkippedTasksVisibility}
      onUnmount={() => changeTaskWorkflowLog({
        isOnlyAttachmentsShown: false,
        sorting: EWorkflowsLogSorting.New,
      })}
      isInTaskCard
      taskId={task.id}
      taskStatus={task.status}
    />
  );
}
