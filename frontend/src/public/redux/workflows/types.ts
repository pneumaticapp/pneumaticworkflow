import type { IRuntimeKickoffClient, ITemplateStep, TOrderedFields } from '../../types/template';
import type {
  EWorkflowsLoadingStatus,
  IWorkflowClient,
  IWorkflowDetailsClient,
  IWorkflowEdit,
  IWorkflowsSettings,
} from '../../types/workflow';
import type { IWorkflowLog } from '../types';

export type TOpenWorkflowLogPopupPayload = {
  workflowId: number;
  redirectTo404IfNotFound?: boolean;
  shouldSetWorkflowDetailUrl?: boolean;
};

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
  kickoff?: IRuntimeKickoffClient | null;
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

export interface IStartWorkflowPayload {
  id: number;
  name: string;
  kickoff: {
    [key: string]: string;
  } | null;
  ancestorTaskId?: number;
  isUrgent?: boolean;
  dueDateTsp?: number | null;
}

export interface IWorkflowsList {
  count: number;
  offset: number;
  items: IWorkflowClient[];
}

export interface IWorkflowsTuneViewModal {
  isOpen: boolean;
}

export interface IStoreWorkflows {
  workflowsLoadingStatus: EWorkflowsLoadingStatus;
  isWorkflowLoading: boolean;
  workflow: IWorkflowDetailsClient | null;
  workflowLog: IWorkflowLog;
  workflowEdit: IWorkflowEdit;
  workflowsSettings: IWorkflowsSettings;
  workflowsSearchText: string;
  workflowsList: IWorkflowsList;
  WorkflowsTuneViewModal: IWorkflowsTuneViewModal;
}
