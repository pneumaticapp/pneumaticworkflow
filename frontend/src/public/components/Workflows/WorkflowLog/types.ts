import type { IChangeWorkflowLogViewSettingsPayload, ISendWorkflowLogComment } from '../../../redux/types';
import type { ETaskStatus } from '../../../types/tasks';
import type { EWorkflowsLogSorting, EWorkflowStatus, IWorkflowLogItem } from '../../../types/workflow';

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
