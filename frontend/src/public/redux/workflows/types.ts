import { EWorkflowsLogSorting } from '../../types/workflow';

export type TOpenWorkflowLogPopupPayload = {
  workflowId: number;
  redirectTo404IfNotFound?: boolean;
  shouldSetWorkflowDetailUrl?: boolean;
};

export interface IChangeWorkflowLogViewSettingsPayload {
  id: number;
  sorting: EWorkflowsLogSorting;
  comments: boolean;
  isOnlyAttachmentsShown: boolean;
}
