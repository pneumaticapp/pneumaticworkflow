import { IWorkflowLogItem, IWorkflowLogTask } from '../../../../../types/workflow';

export type TWorkflowLogTaskCompleteProps = Pick<IWorkflowLogItem, 'userId' | 'created'>;

export interface IWorkflowLogTaskCompleteProps extends TWorkflowLogTaskCompleteProps {
  currentTask: IWorkflowLogTask | null;
  isOnlyAttachmentsShown?: boolean;
}
