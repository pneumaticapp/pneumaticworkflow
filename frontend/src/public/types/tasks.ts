import { IWorkflow, IWorkflowClient, WorkflowWithTsp } from './workflow';
import { IExtraField, ITemplateTitle, RawPerformer } from './template';

export type TTaskWorkflow = Pick<IWorkflow, 'id' | 'name' | 'status' | 'dateCompleted'> & {
  templateName: string;
};

export type TaskWithDateFields = {
  dueDate: string | null;
  dateStarted: string;
  dateCompleted: string | null;
};

export type TaskWithTspFields = {
  dueDateTsp: number | null;
  dateStartedTsp: number;
  dateCompletedTsp: number | null;
};

export type TaskWithTsp<T> = Omit<T, keyof TaskWithDateFields> & TaskWithTspFields;

export type TFormatTaskDates = {
  output?: IExtraField[];
  subWorkflows?: WorkflowWithTsp<IWorkflow>[] | null;
  dueDateTsp?: number | null;
  dateStartedTsp?: number;
  dateCompletedTsp?: number | null;
};

export enum ETaskStatus {
  Pending = 'pending',
  Active = 'active',
  Completed = 'completed',
  Snoozed = 'snoozed',
  Skipped = 'skipped',
}

export interface ITaskRevertTask {
  id: number;
  name: string;
  apiName: string;
}

export interface ITask {
  id: number;
  name: string;
  output: IExtraField[];
  description: string | null;
  workflow: TTaskWorkflow;
  performers: RawPerformer[];
  containsComments: boolean;
  requireCompletionByAll?: boolean;
  isCompleted: boolean;
  dateStarted: string;
  dateCompleted: string | null;
  dueDate: string | null;
  isUrgent: boolean;
  subWorkflows: IWorkflowClient[];
  areChecklistsHandling: boolean;
  checklistsTotal: number;
  checklistsMarked: number;
  checklists: TTaskChecklists;
  status?: ETaskStatus;
  revertTasks: ITaskRevertTask[];
}

export type TTaskChecklists = {
  [apiName in string]: TTaskChecklist;
};

export type TTaskChecklist = {
  id: number;
  apiName: string;
  items: TTaskChecklistsItems;
  checkedItems: number;
  totalItems: number;
};

export type TTaskChecklistsItems = {
  [apiName in string]: TTaskChecklistsItem;
};

export type TTaskChecklistsItem = {
  id: number;
  apiName: string;
  isSelected: boolean;
};

export interface ITaskAPI
  extends Omit<ITask, 'checklists' | 'areChecklistsHandling' | 'dateStarted' | 'dateCompleted' | 'subWorkflows'> {
  checklists: {
    id: number;
    apiName: string;
    selections: {
      id: number;
      apiName: string;
      isSelected: boolean;
    }[];
  }[];
  dueDateTsp: number | null;
  dateStartedTsp: number;
  dateCompletedTsp: number | null;
  subWorkflows: WorkflowWithTsp<IWorkflow>[];
}
export type TTaskListItemResponse = TaskWithTsp<ITaskListItem>;

export interface ITaskListItem {
  id: number;
  name: string;
  workflowName: string;
  isUrgent: boolean;
  dateStarted: string;
  dueDate: string | null;
  dateCompleted: string | null;
  templateId: number;
  templateTaskApiName: string;
}

export enum ETaskListSorting {
  DateAsc = 'date-asc',
  DateDesc = 'date-desc',
  Overdue = 'overdue',
}

export enum ETaskListCompleteSorting {
  DateAsc = 'date-asc',
  DateDesc = 'date-desc',
}

export enum ETaskListCompletionStatus {
  Active = 'running',
  Completed = 'completed',
}

export interface ITasksSettings {
  isHasFilter: boolean;
  completionStatus: ETaskListCompletionStatus;
  sorting: ETaskListSorting | ETaskListCompleteSorting;
  filterValues: {
    templateIdFilter: number | null;
    taskApiNameFilter: string | null;
  };
  templateStepList: {
    items: ITemplateStep[];
    isLoading: boolean;
  };
  templateList: {
    items: ITemplateTitle[];
    isLoading: boolean;
  };
}

export interface ITemplateStep {
  id: number;
  name: string;
  number: number;
  apiName: string;
}
