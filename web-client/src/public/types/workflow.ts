import { IAccount, TUserId } from './user';
import { TUploadedFile } from '../utils/uploadFiles';
import { ITask, ITemplateStep } from './tasks';
import { IKickoff, IExtraField, ITemplateTitle, ETemplateOwnerType, RawPerformer } from './template';
import { EProgressbarColor } from '../components/ProgressBar';

export type WorkflowWithDateFields = {
  dueDate: string | null;
  dateCreated: string;
  dateCompleted: string | null;
};

export type WorkflowWithTspFields = {
  dueDateTsp: number | null;
  dateCreatedTsp: number;
  dateCompletedTsp: number | null;
};

export type WorkflowWithTsp<T> = Omit<T, keyof WorkflowWithDateFields> & WorkflowWithTspFields;

export type TWorkflowDetailsResponse = WorkflowWithTsp<IWorkflowDetails>;

export interface IWorkflowDetails {
  id: number;
  ancestorTaskId?: number;
  name: string;
  description: string;
  template: IWorkflowTemplate | null;
  owners: number[];
  activeCurrentTask: number;
  activeTasksCount: number;
  currentTask: TWorkflowTask;
  tasksCount: number;
  finalizable: boolean;
  isLegacyTemplate: boolean;
  isExternal: boolean;
  isUrgent: boolean;
  legacyTemplateName: string;
  status: EWorkflowStatus;
  kickoff: IWorkflowDetailsKickoff;
  passedTasks: Array<IPassedTask>;
  dateCompleted: string | null;
  dateCreated: string;
  workflowStarter: number | null;
  dueDate: string | null;
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
}

export interface IWorkflowTaskItem {
  id: number;
  name: string;
  api_name: string;
  number: number;
  description: string;
  dueDateTsp: number | null;
  dateStartedTsp: number | null;
  dateCompletedTsp: number | null;
  status: EWorkflowTaskStatus;
  performers: RawPerformer[];
  checklistsTotal: number;
  checklistsMarked: number;
  delay: IWorkflowTaskDelay | null;
  overdue?: boolean;
  color?: EProgressbarColor;
}

export type TWorkflowResponse = WorkflowWithTsp<IWorkflow>;

export interface IWorkflow {
  id: number;
  name: string;
  status: EWorkflowStatus;
  ancestorTaskId?: number;
  tasksCount: number;
  currentTask: number;
  activeTasksCount: number;
  activeCurrentTask: number;
  owners: number[];
  isExternal: boolean;
  template: IWorkflowTemplate | null;
  task: TWorkflowTask;
  tasks: IWorkflowTaskItem[];
  isLegacyTemplate: boolean;
  legacyTemplateName: string;
  passedTasks: IPassedTask[];
  isUrgent: boolean;
  dateCompleted: string | null;
  finalizable: boolean;
  workflowStarter: number | null;
  dueDate: string | null;
  dueDateTsp?: number | null;
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
  templateTaskId: number;
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
  templateList: {
    items: ITemplateFilterItem[];
    isLoading: boolean;
  };
  counters: {
    workflowStartersCounters: TUserCounter[];
    performersCounters: TUserCounter[];
  };
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
