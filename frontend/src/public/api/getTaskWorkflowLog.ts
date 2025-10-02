import { commonRequest } from './commonRequest';
import { getBrowserConfigEnv } from '../utils/getConfig';
import { EWorkflowsLogSorting, IWorkflowLogItem } from '../types/workflow';

export interface IGetTaskWorkflowLogConfig {
  taskId: number;
  sorting?: EWorkflowsLogSorting;
  comments?: boolean;
  isOnlyAttachmentsShown?: boolean;
}

const QS_BY_SORTING: { [key in EWorkflowsLogSorting]: string } = {
  [EWorkflowsLogSorting.New]: 'ordering=-created',
  [EWorkflowsLogSorting.Old]: 'ordering=created',
};

const QS_BY_COMMENTS = 'include_comments=false';

const QS_BY_ATTACHMENTS = 'only_attachments=true';

export function getTaskWorkflowLog({ taskId, sorting, comments, isOnlyAttachmentsShown }: IGetTaskWorkflowLogConfig) {
  const {
    api: { urls },
  } = getBrowserConfigEnv();

  return commonRequest<IWorkflowLogItem[]>(
    `${urls.taskWorkflowLog.replace(':id', String(taskId))}?${getQueryString({
      sorting,
      comments,
      isOnlyAttachmentsShown,
    })}`,
  );
}

function getQueryString({
  sorting = EWorkflowsLogSorting.New,
  comments = true,
  isOnlyAttachmentsShown = false,
}: Partial<IGetTaskWorkflowLogConfig>) {
  return [QS_BY_SORTING[sorting], !comments && QS_BY_COMMENTS, isOnlyAttachmentsShown && QS_BY_ATTACHMENTS]
    .filter(Boolean)
    .join('&');
}
