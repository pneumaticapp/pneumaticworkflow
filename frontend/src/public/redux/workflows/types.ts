import { ITemplateStep } from '../../types/tasks';
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

export type TLoadWorkflowsFilterStepsPayload = {
  templateId: number;
  onAfterLoaded?(steps: ITemplateStep[]): void;
};

export type TRemoveWorkflowFromListPayload = {
  workflowId: number | null;
};
