import { connect } from 'react-redux';
import { TaskCardWrapper } from './TaskCard';
import type { ITaskCardWrapperProps } from './TaskCard';
import {
  setTaskCompleted,
  setTaskReverted,
  setCurrentTask,
  addTaskPerformer,
  removeTaskPerformer,
  setCurrentTaskDueDate,
  deleteCurrentTaskDueDate,
  openSelectTemplateModal,
  changeTaskWorkflowLogViewSettings,
  changeTaskWorkflowLog,
  sendTaskWorkflowLogComments,
  toggleTaskSkippedTasksVisibility,
} from '../../redux/actions';
import { ETaskCardState } from '../../redux/task/types';
import { openWorkflowLogPopup, clearWorkflow } from '../../redux/workflows/slice';
import type { RootState } from '../../redux/store';
import { getNotDeletedUsers } from '../../utils/users';

type TStoreProps = Pick<
  ITaskCardWrapperProps,
  'task' | 'workflowLog' | 'workflow' | 'isWorkflowLoading' | 'status' | 'accountId' | 'users' | 'authUser'
>;
type TDispatchProps = Pick<
  ITaskCardWrapperProps,
  | 'setTaskCompleted'
  | 'setTaskReverted'
  | 'changeTaskWorkflowLogViewSettings'
  | 'sendTaskWorkflowLogComments'
  | 'toggleTaskSkippedTasksVisibility'
  | 'setCurrentTask'
  | 'changeTaskWorkflowLog'
  | 'clearWorkflow'
  | 'addTaskPerformer'
  | 'removeTaskPerformer'
  | 'openWorkflowLogPopup'
  | 'setDueDate'
  | 'deleteDueDate'
  | 'openSelectTemplateModal'
>;

export function mapStateToProps({
  authUser,
  task: { data: task, status, workflowLog, workflow, isWorkflowLoading },
  accounts: { users },
}: RootState): TStoreProps {
  const taskStatus = task?.isCompleted ? ETaskCardState.Completed : status;

  return {
    accountId: authUser.account.id || -1,
    task,
    workflowLog,
    workflow,
    isWorkflowLoading,
    status: taskStatus,
    users: getNotDeletedUsers(users),
    authUser,
  };
}

export const mapDispatchToProps: TDispatchProps = {
  setTaskCompleted,
  setTaskReverted,
  changeTaskWorkflowLogViewSettings,
  sendTaskWorkflowLogComments,
  toggleTaskSkippedTasksVisibility,
  setCurrentTask,
  changeTaskWorkflowLog,
  clearWorkflow,
  addTaskPerformer,
  removeTaskPerformer,
  openWorkflowLogPopup,
  setDueDate: setCurrentTaskDueDate,
  deleteDueDate: deleteCurrentTaskDueDate,
  openSelectTemplateModal,
};

export const TaskCardContainer = connect(mapStateToProps, mapDispatchToProps)(TaskCardWrapper);
