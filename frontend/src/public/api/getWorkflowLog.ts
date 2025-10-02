import { commonRequest } from './commonRequest';
import { getBrowserConfigEnv } from '../utils/getConfig';
import { EWorkflowsLogSorting, IWorkflowLogItem } from '../types/workflow';

export interface IGetWorkflowLogConfig {
  workflowId: number;
  sorting?: EWorkflowsLogSorting;
  comments?: boolean;
  isOnlyAttachmentsShown?: boolean;
}

const QS_BY_SORTING: {[key in EWorkflowsLogSorting]: string} = {
  [EWorkflowsLogSorting.New]: 'ordering=-created',
  [EWorkflowsLogSorting.Old]: 'ordering=created',
};

const QS_BY_COMMENTS = 'include_comments=false';

const QS_BY_ATTACHMENTS = 'only_attachments=true';

export function getWorkflowLog({workflowId, sorting, comments, isOnlyAttachmentsShown }: IGetWorkflowLogConfig) {
  const {
    api: { urls },
  } = getBrowserConfigEnv();

  return commonRequest<IWorkflowLogItem[]>(
    `${urls.workflowLog.replace(':id', String(workflowId))}?${getQueryString({ sorting, comments, isOnlyAttachmentsShown })}`,
  );
}

function getQueryString({
  sorting = EWorkflowsLogSorting.New,
  comments = true,
  isOnlyAttachmentsShown = false,
}: Partial<IGetWorkflowLogConfig>) {
  return [
    QS_BY_SORTING[sorting],
    !comments && QS_BY_COMMENTS,
    isOnlyAttachmentsShown && QS_BY_ATTACHMENTS,
  ].filter(Boolean).join('&');
}
