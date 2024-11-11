import { connect } from 'react-redux';
import { ITaskCardWrapperProps, TaskCardWrapper } from './TaskCard';
import {
  setTaskCompleted,
  setTaskReverted,
  setWorkflowFinished,
  ETaskStatus,
  setCurrentTask,
  clearWorkflow,
  addTaskPerformer,
  removeTaskPerformer,
  openWorkflowLogPopup,
  setCurrentTaskDueDate,
  deleteCurrentTaskDueDate,
  openSelectTemplateModal,
  changeTaskWorkflowLogViewSettings,
  changeTaskWorkflowLog,
  sendTaskWorkflowLogComments,
} from '../../redux/actions';
import { IApplicationState } from '../../types/redux';
import { getNotDeletedUsers } from '../../utils/users';

type TStoreProps = Pick<
  ITaskCardWrapperProps,
  'task' | 'workflowLog' | 'workflow' | 'isWorkflowLoading' | 'status' | 'accountId' | 'users' | 'authUser'
>;
type TDispatchProps = Pick<
  ITaskCardWrapperProps,
  | 'setTaskCompleted'
  | 'setTaskReverted'
  | 'setWorkflowFinished'
  | 'changeTaskWorkflowLogViewSettings'
  | 'sendTaskWorkflowLogComments'
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
}: IApplicationState): TStoreProps {
  const taskStatus = task?.isCompleted ? ETaskStatus.Completed : status;

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
  setWorkflowFinished,
  changeTaskWorkflowLogViewSettings,
  sendTaskWorkflowLogComments,
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
