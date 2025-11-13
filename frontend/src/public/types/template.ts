import { EIntegrations } from './integrations';
import {
  EConditionAction,
  EConditionOperators,
  ICondition,
  TConditionPredicateValue,
} from '../components/TemplateEdit/TaskForm/Conditions';
import { TUploadedFile } from '../utils/uploadFiles';
import { TSystemField } from '../components/Workflows/WorkflowsTablePage/WorkflowsTable/types';

export interface ITemplate {
  id?: number;
  name: string;
  description: string;
  isActive: boolean;
  finalizable: boolean;
  dateUpdated: string | null;
  updatedBy: number | null;
  owners: ITemplateOwner[];
  kickoff: IKickoff;
  tasks: ITemplateTask[];
  isPublic: boolean;
  publicUrl: string | null;
  publicSuccessUrl: string | null;
  isEmbedded: boolean;
  embedUrl: string | null;
  wfNameTemplate: string | null;
  tasksCount: number;
  performersCount: number;
}

export interface ITemplateOwner {
  apiName: string;
  sourceId: string;
  type: ETemplateOwnerType;
}

export type TTransformedTask =
  | { apiName: string; name: string; needSteName: null; fields: TSystemField[] }
  | (Pick<ITemplateTask, 'apiName' | 'fields' | 'name'> & { needSteName?: boolean })
  | (Pick<IKickoff, 'fields'> & { apiName: string; name: string; needSteName: null });

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
  revertTask: string | null;
  ancestors: string[];
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
  label: string;
  type: ETaskPerformerType;
  sourceId: string | null;
  apiName: string;
}

export enum ETemplateOwnerType {
  User = 'user',
  UserGroup = 'group',
}

export enum ETaskPerformerType {
  User = 'user',
  OutputUser = 'field',
  WorkflowStarter = 'workflow_starter',
  UserGroup = 'group',
}

export interface ITemplateResponse extends Omit<ITemplate, 'id' | 'tasks' | 'tasksCount' | 'performersCount'> {
  id: number;
  tasks: ITemplateTaskResponse[];
}

export interface ITemplateTaskResponse
  extends Omit<ITemplateTask, 'uuid' | 'conditions' | 'rawDueDate' | 'apiName' | 'id'> {
  id: number;
  conditions: IConditionResponse[];
  rawDueDate: IDueDateAPI | null;
  dueIn?: string | null; // deprecated
  apiName?: string;
}

export interface ITemplateRequest extends Omit<ITemplate, 'tasks'> {
  tasks: ITemplateTaskRequest[];
}

export interface ITemplateTaskRequest extends Omit<ITemplateTask, 'uuid' | 'conditions' | 'rawDueDate'> {
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
  owners: number[];
  kickoff: IKickoff | null;
}

export interface ITableViewFields extends IExtraField {
  taskId: number | null;
  kickoffId: number | null;
  markdownValue: string;
  clearValue: string;
  userId: number;
  groupId: number;
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
  userId: number | null;
  groupId: number | null;
}

export type TExtraFieldValue = TExtraFieldSingleValue | TExtraFieldMultipleValue | TExtraFieldTimestampValue | null;

export type TExtraFieldSingleValue = string;
export type TExtraFieldMultipleValue = string[];
export type TExtraFieldTimestampValue = number;
export interface IExtraFieldSelection {
  apiName: string;
  isSelected?: boolean;
  value: string;
  key?: number;
}

export enum EExtraFieldType {
  Number = 'number',
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
  workflowsCount: number;
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
  tasks: Pick<ITemplateTask, 'name' | 'description'>[];
};

export interface RawPerformer {
  type: ETemplateOwnerType;
  sourceId: number;
}

export type TOrderedFields = {
  order: number;
  width: number;
  apiName: string;
};

export type TTemplatePreset = {
  id: number;
  name: string;
  author: number;
  dateCreatedTsp: number;
  isDefault: boolean;
  type: 'personal' | 'account';
  fields: TOrderedFields[];
};

export type TAddTemplatePreset = Omit<TTemplatePreset, 'id' | 'author' | 'dateCreatedTsp'>;
