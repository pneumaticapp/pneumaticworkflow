import { IWorkflowsList } from '../../types/redux';
import {
  openSelectTemplateModal,
  TLoadWorkflowsFilterStepsPayload,
  TOpenWorkflowLogPopupPayload,
  TRemoveWorkflowFromListPayload,
} from '../../redux/actions';
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

export interface IWorkflowsProps {
  workflowsLoadingStatus: EWorkflowsLoadingStatus;
  workflowsList: IWorkflowsList;
  templatesFilter: ITemplateTitle[];
  stepsIdsFilter: number[];
  searchText: string;
  view: EWorkflowsView;
  onSearch(value: string): void;
  setStepsFilter(value: number[]): void;
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
  stepsIdsFilter: number[];
  performersIdsFilter: number[];
  workflowStartersIdsFilter: number[];
  filterTemplates: ITemplateFilterItem[];
  areFilterTemplatesLoading?: boolean;
  users: TUserListItem[];
  areUsersLoading?: boolean;
  isSubscribed: boolean;
  performersCounters: TUserCounter[];
  workflowStartersCounters: TUserCounter[];
  loadTemplatesTitles(): void;
  loadTemplateSteps(payload: TLoadWorkflowsFilterStepsPayload): void;
  setTemplatesFilter(value: number[]): void;
  setStepsFilter(value: number[]): void;
  setPerformersFilter(value: number[]): void;
  setWorkflowStartersFilter(value: number[]): void;
  changeWorkflowsSorting(payload: EWorkflowsSorting): void;
  setStatusFilter(payload: EWorkflowsStatus): void;
  applyFilters(): void;
  clearFilters(): void;
  updateCurrentPerformersCounters(): void;
  updateWorkflowStartersCounters(): void;
  updateWorkflowsTemplateStepsCounters(): void;
}
