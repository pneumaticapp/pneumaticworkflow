import { IWorkflow } from './workflow';
import { IExtraField , ITemplateTitle } from './template';

export type TTaskWorkflow = Pick<IWorkflow, 'id' | 'name' | 'currentTask' | 'status' | 'dateCompleted'> & {
  templateName: string;
};
export interface ITask {
  id: number;
  name: string;
  output: IExtraField[];
  description: string | null;
  workflow: TTaskWorkflow;
  performers: number[];
  containsComments: boolean;
  requireCompletionByAll?: boolean;
  isCompleted: boolean;
  dateStarted: string;
  dateStartedTsp: string;
  dateCompleted: string | null;
  dateCompletedTsp: string | null;
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
}

export type TTaskChecklist = {
  id: number;
  apiName: string;
  items: TTaskChecklistsItems;
  checkedItems: number;
  totalItems: number;
};

export type TTaskChecklistsItems = {
  [apiName in string]: TTaskChecklistsItem;
}

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
}

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
