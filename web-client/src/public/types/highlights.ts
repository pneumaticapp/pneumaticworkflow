import { EWorkflowLogEvent, EWorkflowStatus, IWorkflowDelay, IWorkflowDetailsKickoff } from './workflow';
import { TUserId } from './user';
import { IExtraField, ITemplateTitle } from './template';

export interface IHighlightsItem {
  id: number;
  type: EWorkflowLogEvent;
  task: {
    id: number;
    name: string;
    number: number;
    process: number;
    delay: IWorkflowDelay | null;
    output: IExtraField[];
    dueDate: string | null;
  } | null;
  text: string;
  attachments: [];
  created: string;
  user: TUserId | null;
  workflow: {
    id: number;
    name: string;
    currentTask: number;
    tasksCount: number;
    template: ITemplateTitle | null;
    isLegacyTemplate: boolean;
    legacyTemplateName: string;
    status: EWorkflowStatus;
    kickoff: IWorkflowDetailsKickoff | null;
    isExternal: boolean;
  };
  userId: number | null;
  delay: IHighlightsDelay | null;
}

export interface IHighlightsDelay {
  duration: string;
  endDate: string | null;
  estimatedEndDate: string;
  id: number;
  startDate: string;
}

export enum EHighlightsFilterType {
  Templates = 'templates',
  Users = 'users',
}

export enum EHighlightsDateFilter {
  Month = 'month',
  Today = 'today',
  Week = 'week',
  Yesterday = 'yesterday',
  Custom = 'custom',
}

export type THighlightsDateFilter = EHighlightsDateFilter | null;
