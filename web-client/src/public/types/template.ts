/* eslint-disable */
/* prettier-ignore */

import { EIntegrations } from './integrations';
import {
  EConditionAction,
  EConditionOperators,
  ICondition,
  TConditionPredicateValue,
} from '../components/TemplateEdit/TaskForm/Conditions';
import { TUploadedFile } from '../utils/uploadFiles';

export interface ITemplate {
  id?: number;
  name: string;
  description: string;
  isActive: boolean;
  finalizable: boolean;
  dateUpdated: string | null;
  updatedBy: number | null;
  templateOwners: number[];
  kickoff: IKickoff;
  tasks: ITemplateTask[];
  isPublic: boolean;
  publicUrl: string | null;
  publicSuccessUrl: string | null;
  isEmbedded: boolean;
  embedUrl: string | null;
  wfNameTemplate: string | null;
}

export interface ITemplateTask {
  id?: number;
  apiName: string;
  number: number;
  name: string;
  description: string;
  delay: string | null;
  rawDueDate: IDueDate;
  requireCompletionByAll: boolean;
  rawPerformers: ITemplateTaskPerformer[];
  fields: IExtraField[];
  uuid: string;
  conditions: ICondition[];
  checklists: TOutputChecklist[];
}

export type TDueDateRuleTarget = 'field' | 'workflow started' | 'task started' | 'task completed';
export type TDueDateRulePreposition = 'before' | 'after';
type IDueDateRuleAPI =
  | 'before field'
  | 'after workflow started'
  | 'after task started'
  | 'after task completed'
  | 'after field';

export type IDueDate = {
  apiName: string;
  duration: string | null;
  durationMonths: number | null;
  rulePreposition: TDueDateRulePreposition;
  ruleTarget: TDueDateRuleTarget | null;
  sourceId: string | null;
};

export type TOutputChecklist = {
  apiName: string;
  selections: TOutputChecklistItem[];
};

export type TOutputChecklistItem = {
  apiName: string;
  value: string;
};

export interface ITemplateTaskPerformer {
  id?: number;
  label: string;
  type: ETaskPerformerType;
  sourceId: string | null;
}

export enum ETaskPerformerType {
  User = 'user',
  OutputUser = 'field',
  WorkflowStarter = 'workflow_starter',
  UserGroup = 'group',
}

export interface ITemplateResponse extends Omit<ITemplate, 'id' | 'tasks'> {
  id: number;
  tasks: ITemplateTaskResponse[];
}

export interface ITemplateTaskResponse extends Omit<ITemplateTask,
| 'uuid'
| 'conditions'
| 'rawDueDate'
| 'apiName'
| 'id'> {
  id: number;
  conditions: IConditionResponse[];
  rawDueDate: IDueDateAPI | null;
  dueIn?: string | null; // deprecated
  apiName?: string;
}

export interface ITemplateRequest extends Omit<ITemplate, 'tasks'> {
  tasks: ITemplateTaskRequest[];
}

export interface ITemplateTaskRequest extends Omit<ITemplateTask,
  | 'uuid'
  | 'conditions'
  | 'rawDueDate'> {
  conditions: IConditionResponse[];
  rawDueDate: IDueDateAPI | null;
}

export interface IConditionResponse {
  id?: number;
  apiName: string;
  order: number;
  rules: IConditionRuleResponse[];
  action: EConditionAction;
}

export interface IDueDateAPI {
  apiName: string;
  duration: string;
  durationMonths: number;
  rule: IDueDateRuleAPI;
  sourceId: string | null;
}

export interface IConditionRuleResponse {
  id?: number;
  apiName: string;
  predicates: TConditionRulePredicateResponse[];
}

export type TConditionRulePredicateResponse = {
  id?: number;
  apiName: string;
  field: string;
  operator: EConditionOperators;
} & TConditionPredicateValue;

export interface IKickoff {
  id?: number;
  description: string;
  fields: IExtraField[];
}

export interface ITemplateListItem {
  id: number;
  isActive: boolean;
  isPublic: boolean;
  publicUrl?: string;
  name: string;
  description?: string;
  tasksCount: number;
  performersCount: number;
  templateOwners: number[];
  kickoff: IKickoff | null;
}

export interface IExtraField {
  id?: number;
  apiName: string;
  description?: string;
  isRequired?: boolean;
  name: string;
  type: EExtraFieldType;
  value?: TExtraFieldValue;
  selections?: IExtraFieldSelection[];
  attachments?: TUploadedFile[];
  order: number;
}

export type TExtraFieldValue = TExtraFieldSingleValue | TExtraFieldMultipleValue | null;

export type TExtraFieldSingleValue = string;
export type TExtraFieldMultipleValue = string[];

export interface IExtraFieldSelection {
  id?: number;
  apiName: string;
  isSelected?: boolean;
  value: string;
  key?: number;
}

export enum EExtraFieldType {
  Text = 'text',
  String = 'string',
  Date = 'date',
  Url = 'url',
  Checkbox = 'checkbox',
  Radio = 'radio',
  Creatable = 'dropdown',
  File = 'file',
  User = 'user',
}

export enum EExtraFieldMode {
  Kickoff = 'style_kickoff',
  ProcessRun = 'style_process-run',
}

export interface ISystemTemplate {
  id: number;
  name: string;
  order: number;
  description?: string;
  category?: number;
}

export interface ITemplateTitle {
  id: number;
  name: string;
}

export enum ETemplateTitleWorkflowStatuses {
  running = 'running',
  delayed = 'delayed',
  done = 'done',
}

export type TTemplateIntegrationStats = Record<EIntegrations, boolean>;
export type TTemplateIntegrationStatsApi = TTemplateIntegrationStats & {
  id: number;
};

export enum ETemplateParts {
  Integrations = 'integrations',
  Share = 'share',
  Zapier = 'zapier',
  API = 'api',
  Webhook = 'webhook',
}

export type TAITemplateGenerationStatus = 'initial' | 'generating' | 'generated';

export type TTemplateWithTasksOnly = Pick<ITemplate, 'name'> & {
  tasks: Pick<ITemplateTask, 'name' | 'description'>[]
};
