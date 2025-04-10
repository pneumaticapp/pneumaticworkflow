import { IWorkflow } from './workflow';
import { IExtraField, ITemplateTitle, RawPerformer } from './template';

export type TTaskWorkflow = Pick<
  IWorkflow,
  'id' | 'name' | 'currentTask' | 'status' | 'dateCompleted' | 'dateCompletedTsp'
> & {
  templateName: string;
};

export type TFormatTaskDates = {
  output?: IExtraField[];
  subWorkflow?: (Omit<IWorkflow, 'dueDate'> & { dueDateTsp: number | null }) | null;
  dueDateTsp?: number | null;
};

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
  dateStartedTsp: string;
  dateCompleted: string | null;
  dateCompletedTsp: number | null;
  dueDate: string | null;
  isUrgent: boolean;
  subWorkflows: IWorkflow[];
  areChecklistsHandling: boolean;
  checklistsTotal: number;
  checklistsMarked: number;
  checklists: TTaskChecklists;
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

export interface ITaskAPI extends Omit<ITask, 'checklists' | 'areChecklistsHandling'> {
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
}

export type TTaskListItemResponse = Omit<ITaskListItem, 'dueDate'> & { dueDateTsp: number | null };

export interface ITaskListItem {
  id: number;
  name: string;
  workflowName: string;
  isUrgent: boolean;
  dateStarted: string;
  dueDate: string | null;
  dateCompleted: string | null;
  templateId: number;
  templateTaskId: number;
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
    stepIdFilter: number | null;
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
}
