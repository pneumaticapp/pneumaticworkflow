import type { TOpenModalPayload } from '../../redux/selectTemplateModal/actions';
import type {
  TAddTaskPerformerPayload,
  TRemoveTaskPerformerPayload,
  TSetTaskCompletedPayload,
  TSetTaskRevertedPayload,
} from '../../redux/task/actions';
import type { ETaskCardState } from '../../redux/task/types';
import type { IChangeWorkflowLogViewSettingsPayload, ISendWorkflowLogComment, IWorkflowLog } from '../../redux/types';
import type { TOpenWorkflowLogPopupPayload } from '../../redux/workflows/types';
import type { IFieldsetRuntime } from '../../types/fieldset';
import type { IExtraField } from '../../types/template';
import type { ETaskCardViewMode, ITask } from '../../types/tasks';
import type { TAuthUserResult, TUserListItem } from '../../types/user';
import type { IWorkflowDetails } from '../../types/workflow';

export interface ITaskCardProps {
  task: ITask;
  viewMode: ETaskCardViewMode;
  workflowLog: IWorkflowLog;
  workflow: IWorkflowDetails | null;
  status: ETaskCardState;
  isWorkflowLoading: boolean;
  accountId: number;
  users: TUserListItem[];
  authUser: TAuthUserResult;
  helpText?: string;
  addTaskPerformer(payload: TAddTaskPerformerPayload): void;
  removeTaskPerformer(payload: TRemoveTaskPerformerPayload): void;
  changeTaskWorkflowLog(value: Partial<IWorkflowLog>): void;
  setTaskCompleted(payload: TSetTaskCompletedPayload): void;
  setTaskReverted(payload: TSetTaskRevertedPayload): void;
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

export interface ITaskCardWrapperProps extends Omit<ITaskCardProps, 'task'> {
  task: ITask | null;
}

export type TTaskCardHeaderProps = Pick<ITaskCardProps, 'task' | 'viewMode' | 'workflowLog' | 'openWorkflowLogPopup'>;

export type TTaskPerformersProps = Pick<
  ITaskCardProps,
  'task' | 'viewMode' | 'workflow' | 'status' | 'users' | 'authUser' | 'addTaskPerformer' | 'removeTaskPerformer'
>;

export interface ITaskOutputFieldsProps {
  accountId: number;
  isDisabled: boolean;
  outputValues: IExtraField[];
  fieldsetOutputValues: IFieldsetRuntime[];
  status: ETaskCardState;
  taskId: number;
  editField(apiName: string): (changedProps: Partial<IExtraField>) => void;
  editFieldsetField(apiName: string): (changedProps: Partial<IExtraField>) => void;
  onUploadStateChange(apiName: string, isUploading: boolean): void;
}

export type TTaskActionsProps = Pick<
  ITaskCardProps,
  'task' | 'viewMode' | 'status' | 'setTaskCompleted' | 'setTaskReverted' | 'openSelectTemplateModal'
> & {
  flushOutputs(): void;
  isOutputUploading: boolean;
  outputValues: IExtraField[];
  fieldsetOutputValues: IFieldsetRuntime[];
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
