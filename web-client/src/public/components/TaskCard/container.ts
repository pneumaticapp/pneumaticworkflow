import { connect } from 'react-redux';
import { ITaskCardWrapperProps, TaskCardWrapper } from './TaskCard';
import {
  setTaskCompleted,
  setTaskReverted,
  setWorkflowFinished,
  changeWorkflowLogViewSettings,
  sendWorkflowLogComments,
  ETaskStatus,
  setCurrentTask,
  changeWorkflowLog,
  clearWorkflow,
  addTaskPerformer,
  removeTaskPerformer,
  openWorkflowLogPopup,
  setCurrentTaskDueDate,
  deleteCurrentTaskDueDate,
  openSelectTemplateModal,
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
  | 'changeWorkflowLogViewSettings'
  | 'sendWorkflowLogComments'
  | 'setCurrentTask'
  | 'changeWorkflowLog'
  | 'clearWorkflow'
  | 'addTaskPerformer'
  | 'removeTaskPerformer'
  | 'openWorkflowLogPopup'
  | 'setDueDate'
  | 'deleteDueDate'
  | 'openSelectTemplateModal'
>;

export function mapStateToProps({
  workflows: { workflowLog, workflow, isWorkflowLoading },
  authUser,
  task: { data: task, status },
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
  changeWorkflowLogViewSettings,
  sendWorkflowLogComments,
  setCurrentTask,
  changeWorkflowLog,
  clearWorkflow,
  addTaskPerformer,
  removeTaskPerformer,
  openWorkflowLogPopup,
  setDueDate: setCurrentTaskDueDate,
  deleteDueDate: deleteCurrentTaskDueDate,
  openSelectTemplateModal,
};

export const TaskCardContainer = connect(mapStateToProps, mapDispatchToProps)(TaskCardWrapper);
