import { ETaskListCompletionStatus, ETaskStatus } from '../../../types/tasks';

interface IShouldRemoveTaskOnDeletedParams {
  status: ETaskStatus;
  completionStatus: ETaskListCompletionStatus;
}

/**
 * Active deletions always update the list.
 * Non-active deletions only apply on the Completed tab to avoid wiping a
 * card just re-added via task_created (return/revert WS race).
 */
export function shouldRemoveTaskOnDeleted({
  status,
  completionStatus,
}: IShouldRemoveTaskOnDeletedParams): boolean {
  if (status === ETaskStatus.Active) {
    return true;
  }

  return completionStatus === ETaskListCompletionStatus.Completed;
}

export function shouldDecrementCounterOnDeleted(status: ETaskStatus): boolean {
  return status === ETaskStatus.Active;
}
