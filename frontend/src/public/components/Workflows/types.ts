import { IWorkflowsList } from '../../types/redux';
import { openSelectTemplateModal } from '../../redux/actions';
import {
  TLoadWorkflowsFilterStepsPayload,
  TOpenWorkflowLogPopupPayload,
  TRemoveWorkflowFromListPayload,
} from '../../redux/workflows/types';
import { IRunWorkflow } from '../WorkflowEditPopup/types';
import { ITemplateTitle } from '../../types/template';
import {
  EWorkflowsLoadingStatus,
  EWorkflowsSorting,
  EWorkflowsStatus,
  EWorkflowsView,
  ITemplateFilterItem,
  TUserCounter,
} from '../../types/workflow';
import { TUserListItem } from '../../types/user';
import { IGroup } from '../../redux/team/types';

export interface IWorkflowsProps {
  workflowsLoadingStatus: EWorkflowsLoadingStatus;
  workflowsList: IWorkflowsList;
  templatesFilter: ITemplateTitle[];
  tasksApiNamesFilter: string[];
  searchText: string;
  view: EWorkflowsView;
  onSearch(value: string): void;
  setTasksFilter(value: string[]): void;
  openRunWorkflowModal(payload: IRunWorkflow): void;
  loadWorkflowsList(id: number): void;
  openWorkflowLogPopup(payload: TOpenWorkflowLogPopupPayload): void;
  loadTemplatesTitles(): void;
  resetWorkflows(): void;
  openSelectTemplateModal: typeof openSelectTemplateModal;
  removeWorkflowFromList(payload: TRemoveWorkflowFromListPayload): void;
}

export interface IWorkflowsFiltersProps {
  sorting: EWorkflowsSorting;
  view: EWorkflowsView;
  areFiltersChanged: boolean;
  statusFilter: EWorkflowsStatus;
  templatesIdsFilter: number[];
  tasksApiNamesFilter: string[];
  performersIdsFilter: number[];
  performersGroupIdsFilter: number[];
  workflowStartersIdsFilter: number[];
  filterTemplates: ITemplateFilterItem[];
  areFilterTemplatesLoading?: boolean;
  users: TUserListItem[];
  groups: IGroup[];
  areUsersLoading?: boolean;
  isSubscribed: boolean;
  performersCounters: TUserCounter[];
  workflowStartersCounters: TUserCounter[];
  selectedFields: string[];
  loadTemplatesTitles(): void;
  loadTemplateSteps(payload: TLoadWorkflowsFilterStepsPayload): void;
  setTemplatesFilter(value: number[]): void;
  setTasksFilter(value: string[]): void;
  setPerformersFilter(value: number[]): void;
  setPerformersGroupFilter(value: number[]): void;
  setWorkflowStartersFilter(value: number[]): void;
  changeWorkflowsSorting(payload: EWorkflowsSorting): void;
  setStatusFilter(payload: EWorkflowsStatus): void;
  applyFilters(): void;
  clearFilters(): void;
  updateCurrentPerformersCounters(): void;
  updateWorkflowStartersCounters(): void;
  updateWorkflowsTemplateStepsCounters(): void;
}
