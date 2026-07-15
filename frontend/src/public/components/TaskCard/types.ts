import {
  ETaskStatus,
  TAddTaskPerformerPayload,
  TOpenModalPayload,
  TRemoveTaskPerformerPayload,
  TSetTaskCompletedPayload,
  TSetTaskRevertedPayload,
} from '../../redux/actions';
import {
  IChangeWorkflowLogViewSettingsPayload,
  ISendWorkflowLogComment,
  TOpenWorkflowLogPopupPayload,
  TSetWorkflowFinishedPayload,
} from '../../redux/workflows/types';
import { IAuthUser, IWorkflowLog } from '../../types/redux';
import { IExtraField } from '../../types/template';
import { ITask } from '../../types/tasks';
import { TUserListItem } from '../../types/user';
import { IWorkflowDetails } from '../../types/workflow';

export enum ETaskCardViewMode {
  Single = 'single',
  List = 'list',
  Guest = 'guest',
}

export interface ITaskCardProps {
  task: ITask;
  viewMode: ETaskCardViewMode;
  workflowLog: IWorkflowLog;
  workflow: IWorkflowDetails | null;
  status: ETaskStatus;
  isWorkflowLoading: boolean;
  accountId: number;
  users: TUserListItem[];
  authUser: IAuthUser;
  helpText?: string;
  addTaskPerformer(payload: TAddTaskPerformerPayload): void;
  removeTaskPerformer(payload: TRemoveTaskPerformerPayload): void;
  changeTaskWorkflowLog(value: Partial<IWorkflowLog>): void;
  setTaskCompleted(payload: TSetTaskCompletedPayload): void;
  setTaskReverted(payload: TSetTaskRevertedPayload): void;
  setWorkflowFinished(payload: TSetWorkflowFinishedPayload): void;
  sendTaskWorkflowLogComments(payload: ISendWorkflowLogComment): void;
  changeTaskWorkflowLogViewSettings(payload: IChangeWorkflowLogViewSettingsPayload): void;
  toggleTaskSkippedTasksVisibility(): void;
  setCurrentTask(task: ITask | null): void;
  clearWorkflow(): void;
  openWorkflowLogPopup(payload: TOpenWorkflowLogPopupPayload): void;
  setDueDate(date: string): void;
  deleteDueDate(): void;
  openSelectTemplateModal(payload: TOpenModalPayload): void;
}

export type ITaskCardWrapperProps = Omit<ITaskCardProps, 'task'> & {
  task: ITask | null;
};

export type TTaskCardHeaderProps = Pick<
  ITaskCardProps,
  'task' | 'viewMode' | 'workflowLog' | 'openWorkflowLogPopup'
>;

export type TTaskPerformersProps = Pick<
  ITaskCardProps,
  | 'task'
  | 'viewMode'
  | 'workflow'
  | 'status'
  | 'users'
  | 'authUser'
  | 'addTaskPerformer'
  | 'removeTaskPerformer'
>;

export interface ITaskOutputFieldsProps {
  accountId: number;
  isDisabled: boolean;
  outputValues: IExtraField[];
  status: ETaskStatus;
  taskId: number;
  editField(apiName: string): (changedProps: Partial<IExtraField>) => void;
  onUploadStateChange(apiName: string, isUploading: boolean): void;
}

export type TTaskActionsProps = Pick<
  ITaskCardProps,
  'task' | 'viewMode' | 'status' | 'setTaskCompleted' | 'setTaskReverted' | 'openSelectTemplateModal'
> & {
  flushOutputs(): void;
  isOutputUploading: boolean;
  outputValues: IExtraField[];
};

export type TTaskWorkflowLogProps = Pick<
  ITaskCardProps,
  | 'task'
  | 'viewMode'
  | 'workflowLog'
  | 'workflow'
  | 'status'
  | 'isWorkflowLoading'
  | 'changeTaskWorkflowLog'
  | 'sendTaskWorkflowLogComments'
  | 'changeTaskWorkflowLogViewSettings'
  | 'toggleTaskSkippedTasksVisibility'
>;
