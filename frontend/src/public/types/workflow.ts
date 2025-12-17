import { IAccount, TUserId } from './user';
import { TUploadedFile } from '../utils/uploadFiles';
import { ITask, ITemplateStep, TaskWithTsp } from './tasks';
import {
  IKickoff,
  IExtraField,
  ITemplateTitle,
  ETemplateOwnerType,
  RawPerformer,
  ITableViewFields,
  TTemplatePreset,
} from './template';
import { EProgressbarColor } from '../components/Workflows/utils/getWorfkflowClientProperties';

export type WorkflowWithDateFields = {
  dueDate: string | null;
  dateCreated: string;
  dateCompleted: string | null;
  tasks: IWorkflowTaskItem[];
};

export type WorkflowWithTspFields = {
  dueDateTsp: number | null;
  dateCreatedTsp: number;
  dateCompletedTsp: number | null;
  tasks: TaskWithTsp<IWorkflowTaskItem>[];
};

export type WorkflowWithTsp<T> = Omit<T, keyof WorkflowWithDateFields> &
  WorkflowWithTspFields & {
    tasks: TaskWithTsp<IWorkflowTaskItem>[];
  };

export type TWorkflowDetailsResponse = WorkflowWithTsp<IWorkflowDetails>;
export interface IWorkflowClientProperties {
  tasks: IWorkflowTaskClient[];
  completedTasks: IWorkflowTaskClient[];

  areMultipleTasks: boolean;
  namesMultipleTasks: Record<string, string>;
  oneActiveTaskName?: string | null;
  selectedUsers: RawPerformer[];

  tasksCountWithoutSkipped: number;
  minDelay: IWorkflowTaskDelay | null;
  areOverdueTasks: boolean;
  oldestDeadline: string | null;
}
export interface IWorkflowDetails {
  id: number;
  name: string;
  owners: number[];
  status: EWorkflowStatus;
  dateCreated: string;
  dateCompleted: string | null;
  dueDate: string | null;
  isLegacyTemplate: boolean;
  legacyTemplateName: string;
  isExternal: boolean;
  isUrgent: boolean;
  workflowStarter: number | null;
  template: IWorkflowTemplate | null;
  tasks: IWorkflowTaskItem[];

  ancestorTaskId?: number;
  finalizable: boolean;

  description: string;
  kickoff: IWorkflowDetailsKickoff;
}

export interface IWorkflowEditData {
  name?: string;
  kickoff?: IKickoff | null;
}

export interface IWorkflowEdit {
  workflow: IWorkflowEditData;
  isWorkflowNameEditing: boolean;
  isWorkflowNameSaving: boolean;
  isKickoffEditing: boolean;
  isKickoffSaving: boolean;
}

export interface IWorkflowDetailsKickoff {
  id: number;
  description: string | null;
  output: IExtraField[];
}

export interface IWorkflowLogItem {
  id: number;
  workflowId: number;
  created: string;
  status: string;
  task: IWorkflowLogTask | null;
  text: string | null;
  type: EWorkflowLogEvent;
  userId: number | null;
  delay: IWorkflowDelay | null;
  targetUserId: number | null;
  targetGroupId: number | null;
  attachments: [];
  watched: { date: string; userId: Pick<IAccount, 'id'> }[];
  reactions: { [value: string]: Pick<IAccount, 'id'>[] };
}

export interface IWorkflowDelay {
  duration: string;
  endDate: string | null;
  estimatedEndDate: string;
  id: number;
  startDate: string;
}

export interface IWorkflowLogTask
  extends Pick<ITask, 'id' | 'name' | 'description' | 'output' | 'performers' | 'dueDate'> {
  number: number;
  delay: IWorkflowDelay | null;
}

export type TWorkflowTask = Pick<
  ITask,
  'id' | 'name' | 'performers' | 'dateStarted' | 'dueDate' | 'checklistsMarked' | 'checklistsTotal'
> & {
  delay: IWorkflowDelay | null;
  number: number;
};

export interface IWorkflowTaskDelay {
  duration: string;
  startDate: string;
  endDate: string;
  estimatedEndDate: string;
  estimatedEndDateTsp: number | null;
}

export interface IWorkflowTaskClient extends IWorkflowTaskItem {
  overdue: boolean;
  color: EProgressbarColor | null;
}

export interface IWorkflowTaskItem {
  id: number;
  name: string;
  apiName: string;
  number: number;
  description: string;
  dueDate: string | null;
  dateStarted: string | null;
  dateCompleted: string | null;
  status: EWorkflowTaskStatus;
  performers: RawPerformer[];
  checklistsTotal: number;
  checklistsMarked: number;
  delay: IWorkflowTaskDelay | null;
}

export type TWorkflowResponse = WorkflowWithTsp<IWorkflow>;

export interface IWorkflowClient extends Omit<IWorkflow, 'tasks'>, IWorkflowClientProperties {}
export interface IWorkflowDetailsClient extends Omit<IWorkflowDetails, 'tasks'>, IWorkflowClientProperties {}

export interface IWorkflow {
  id: number;
  name: string;
  owners: number[];
  status: EWorkflowStatus;
  dateCreated: string;
  dateCompleted: string | null;
  dueDate: string | null;
  isLegacyTemplate: boolean;
  legacyTemplateName: string;
  isExternal: boolean;
  isUrgent: boolean;
  workflowStarter: number | null;
  template: IWorkflowTemplate | null;
  tasks: IWorkflowTaskItem[];
  fields?: ITableViewFields[];

  ancestorTaskId?: number;
  finalizable: boolean;

  workflowSnoosed?: IWorkflowTaskDelay | null;
}

export interface IPassedTask {
  id: number;
  name: string;
  number: number;
}

export enum EWorkflowStatus {
  Running = 0,
  Finished = 1,
  Aborted = 2,
  Snoozed = 3,
}

export enum EWorkflowTaskStatus {
  Pending = 'pending',
  Active = 'active',
  Completed = 'completed',
  Snoozed = 'snoozed',
}

export interface IWorkflowTemplate {
  id: number;
  name: string;
  isActive: boolean;
  wfNameTemplate: string | null;
}

export enum EMoveDirections {
  Up = 'up',
  Down = 'down',
}

export interface ITaskCommentItem {
  author: TUserId | null;
  text: string;
  dateCreated: string;
  type: ECommentType;
  saving?: boolean;
  failed?: boolean;
  id?: number;
  attachments: TUploadedFile[];
}

export interface ITaskCommentAttachmentRequest {
  id: number;
}

export enum EWorkflowsLogSorting {
  New = 'new',
  Old = 'old',
}

export enum EWorkflowLogAttachmentsModes {
  Timeline = 'timeline',
  Attachments = 'attachments',
}

export enum EWorkflowsSorting {
  DateAsc = 'date-asc',
  DateDesc = 'date-desc',
  Overdue = 'overdue',
  Urgent = 'urgent',
}

export enum ETemplatesSorting {
  DateAsc = 'date-asc',
  DateDesc = 'date-desc',
  NameAsc = 'name-asc',
  NameDesc = 'name-desc',
  UsageAsc = 'usage-asc',
  UsageDesc = 'usage-desc',
}

export enum ECommentType {
  Comment = 0,
  Reverted = 1,
  Finish = 2,
}

export enum EDashboardActivityAction {
  Comment = 0,
  Reverted = 1,
}

export enum EWorkflowLogEvent {
  WorkflowRun = 0,
  WorkflowComplete = 1,
  TaskStart = 2,
  TaskComplete = 3,
  TaskRevert = 4,
  TaskComment = 5,
  WorkflowFinished = 6,
  WorkflowSnoozed = 7,
  WorkflowsReturned = 8,
  TaskSkipped = 9,
  WorkflowEndedOnCondition = 10,
  WorkflowIsUrgent = 11,
  WorkflowIsNotUrgent = 12,
  TaskSkippedDueLackAssignedPerformers = 13,
  AddedPerformer = 14,
  RemovedPerformer = 15,
  WorkflowResumed = 16,
  WorkflowSnoozedManually = 17,
  DueDateChanged = 18,
  AddedPerformerGroup = 20,
  RemovedPerformerGroup = 21,
  TaskSnoozed = 22,
}

export enum EIconTitles {
  Completed = 'Task completed',
  Commented = 'Commented',
  Reverted = 'Task returned',
}

export enum EWorkflowsStatus {
  All = 'all-statuses',
  Running = 'running',
  Snoozed = 'snoozed',
  Completed = 'done',
}

export enum EInputNameBackgroundColor {
  White = 'color_white',
  OrchidWhite = 'color_orchid-white',
}

export type TTemplateStepFilter = ITemplateStep & {
  count?: number;
  apiName?: string; // optional and missing from ITemplateStep?
};

export type ITemplateFilterItem = ITemplateTitle & {
  steps: TTemplateStepFilter[];
  areStepsLoading: boolean;
};

export type TUserCounter = {
  sourceId: number;
  workflowsCount: number;
  type: ETemplateOwnerType;
};

export type TTemplateStepCounter = {
  templateTaskApiName: string;
  workflowsCount: number;
};

export interface IWorkflowsSettings {
  view: EWorkflowsView;
  sorting: EWorkflowsSorting;
  areFiltersChanged: boolean;
  values: {
    statusFilter: EWorkflowsStatus;
    templatesIdsFilter: number[];
    stepsIdsFilter: number[];
    performersIdsFilter: number[];
    performersGroupIdsFilter: number[];
    workflowStartersIdsFilter: number[];
  };
  presets: TTemplatePreset[];
  selectedFields: string[];
  templateList: {
    items: ITemplateFilterItem[];
    isLoading: boolean;
  };
  counters: {
    workflowStartersCounters: TUserCounter[];
    performersCounters: TUserCounter[];
  };
  lastLoadedTemplateIdForTable: string | null;
}

export enum EWorkflowsView {
  Table = 'table',
  Grid = 'grid',
}

export enum EWorkflowsLoadingStatus {
  Loaded = 'list-loaded',
  LoadingList = 'list-loading',
  LoadingNextPage = 'loading-next-page',
  EmptyList = 'list-empty',
}

export interface IDropdownMenuProps {
  renderedOptions: React.ReactNode;
  isWide: boolean;
  level: number;
  direction?: 'right' | 'left';
  className?: string;
  renderMenuContent?(renderedOptions: React.ReactNode): React.ReactNode;
}
