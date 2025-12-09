import { TUploadedFile } from '../../utils/uploadFiles';

import { ITemplateStep } from '../../types/tasks';
import { IKickoff, TOrderedFields } from '../../types/template';
import { EWorkflowsLogSorting, IWorkflowClient } from '../../types/workflow';

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
export type TEditWorkflowPayload = {
  typeChange?: string;
  name?: string;
  kickoff?: IKickoff | null;
  isUrgent?: boolean;
  dueDate?: string | null;
  workflowId: number;
  dueDateTsp?: number | null;
};

export type TSetWorkflowResumedPayload = {
  workflowId: number;
  onSuccess?(): void;
};

export type TSetWorkflowFinishedPayload = {
  workflowId: number;
  onWorkflowEnded?(): void;
};

export interface ISendWorkflowLogComment {
  text: string;
  attachments: TUploadedFile[];
  taskId?: number;
}

export type TDeleteWorkflowPayload = {
  workflowId: number;
  onSuccess?(): void;
};

export type TReturnWorkflowToTaskPayload = {
  workflowId: number;
  taskId: number;
  onSuccess?(): void;
};

export type TCloneWorkflowPayload = {
  workflowId: number;
  workflowName: string;
  templateId?: number;
};

export type TSnoozeWorkflowPayload = {
  workflowId: number;
  date: string;
  onSuccess?(workflow: IWorkflowClient): void;
};

export interface ISaveWorkflowsPresetPayload {
  orderedFields: TOrderedFields[];
  type: 'personal' | 'account';
  templateId: number;
}
