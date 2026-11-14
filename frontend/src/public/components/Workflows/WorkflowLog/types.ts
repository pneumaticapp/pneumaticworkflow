import type { IChangeWorkflowLogViewSettingsPayload, ISendWorkflowLogComment } from '../../../redux/types';
import type { ETaskStatus } from '../../../types/tasks';
import type {
  EWorkflowLogEvent,
  EWorkflowsLogSorting,
  EWorkflowStatus,
  IWorkflowLogItem,
  IWorkflowLogTask,
} from '../../../types/workflow';

export type TWorkflowLogTheme = 'white' | 'beige';

export interface IWorkflowLogProps {
  theme: TWorkflowLogTheme;
  items: IWorkflowLogItem[];
  sorting: EWorkflowsLogSorting;
  isCommentsShown: boolean;
  isCommentFieldHidden?: boolean;
  isOnlyAttachmentsShown: boolean;
  isSkippedTasksShown: boolean;
  workflowId: number | null;
  includeHeader: boolean;
  workflowStatus: EWorkflowStatus;
  isLogMinimized?: boolean;
  isLoading?: boolean;
  minimizedLogMaxEvents?: number;
  areTasksClickable?: boolean;
  areRightTogglesHidden?: boolean;
  changeWorkflowLogViewSettings(payload: IChangeWorkflowLogViewSettingsPayload): void;
  toggleSkippedTasksVisibility(): void;
  sendComment({ text, taskId }: ISendWorkflowLogComment): void;
  onClickTask?(): void;
  onUnmount?(): void;
  isInTaskCard?: boolean;
  taskId?: number;
  taskStatus?: ETaskStatus;
}

export interface IWorkflowLogDelayProps extends Pick<IWorkflowLogItem, 'delay'> {
  theme: TWorkflowLogTheme;
  task?: IWorkflowLogTask | null;
  type?: EWorkflowLogEvent;
}

export interface IWorkflowLogTaskSkippedProps extends Pick<IWorkflowLogItem, 'task'> {
  theme: TWorkflowLogTheme;
}

export interface IWorkflowLogTaskStartProps extends Pick<IWorkflowLogItem, 'task' | 'created' | 'id'> {
  logItems: IWorkflowLogItem[];
  sorting: EWorkflowsLogSorting;
  areTasksClickable?: boolean;
  theme: TWorkflowLogTheme;
  onClickTask?(): void;
}

export interface IWorkflowSkippedTaskProps extends Pick<IWorkflowLogItem, 'task'> {
  areTasksClickable?: boolean;
  theme: TWorkflowLogTheme;
  onClickTask?(): void;
}

export interface IWorkflowLogSkeletonProps {
  className?: string;
  theme?: TWorkflowLogTheme;
}
