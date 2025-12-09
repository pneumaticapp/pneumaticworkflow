/* eslint-disable indent */
import produce from 'immer';
import { IWorkflowsList, IStoreWorkflows } from '../../types/redux';
import { TWorkflowsActions } from './actions';
import {
  EWorkflowsLogSorting,
  EWorkflowsSorting,
  IWorkflowLogItem,
  IWorkflowsSettings,
  EWorkflowsStatus,
  EWorkflowsView,
  EWorkflowsLoadingStatus,
} from '../../types/workflow';
import { IKickoff } from '../../types/template';
import { isDesktop } from '../../utils/media';
import { EGeneralActions, TGeneralActions } from '../actions';
import { getWorkflowViewStorageState } from '../../utils/workflows/filters';

const INIT_WORKFLOWS_LIST = {
  count: -1,
  offset: 0,
  items: [],
} as IWorkflowsList;

export const INITIAL_WORKFLOWS_FILTERS: IWorkflowsSettings['values'] = {
  statusFilter: EWorkflowsStatus.Running,
  templatesIdsFilter: [],
  stepsIdsFilter: [],
  performersIdsFilter: [],
  performersGroupIdsFilter: [],
  workflowStartersIdsFilter: [],
};

const INIT_WORKFLOW_EDIT = {
  workflow: {
    name: '',
    kickoff: { description: '', fields: [] } as IKickoff,
  },
  isWorkflowNameEditing: false,
  isKickoffEditing: false,
  isKickoffSaving: false,
  isWorkflowNameSaving: false,
};

export const INIT_STATE: IStoreWorkflows = {
  workflowsList: INIT_WORKFLOWS_LIST,
  workflowsLoadingStatus: EWorkflowsLoadingStatus.Loaded,
  workflow: null,
  isWorkflowLoading: false,
  workflowEdit: INIT_WORKFLOW_EDIT,
  workflowLog: {
    items: [] as IWorkflowLogItem[],
    isCommentsShown: true,
    isOnlyAttachmentsShown: false,
    sorting: EWorkflowsLogSorting.New,
    isOpen: false,
    isLoading: false,
    workflowId: null,
  },
  workflowsSearchText: '',
  workflowsSettings: {
    view: getWorkflowViewStorageState() || (isDesktop() ? EWorkflowsView.Table : EWorkflowsView.Grid),
    areFiltersChanged: false,
    sorting: EWorkflowsSorting.DateDesc,
    values: INITIAL_WORKFLOWS_FILTERS,
    selectedFields: [],
    presets: [],
    templateList: {
      items: [],
      isLoading: false,
    },
    counters: {
      workflowStartersCounters: [],
      performersCounters: [],
    },
    lastLoadedTemplateIdForTable: null,
  },
  WorkflowsTuneViewModal: {
    isOpen: false,
  },
};

export const reducer = (state = INIT_STATE, action: TWorkflowsActions | TGeneralActions): IStoreWorkflows => {
  switch (action.type) {
    case EGeneralActions.ClearAppFilters:
      return produce(state, (draftState) => {
        draftState.workflowsSettings.values = INITIAL_WORKFLOWS_FILTERS;
        draftState.workflowsSettings.areFiltersChanged = false;
        draftState.workflowsSettings.sorting = EWorkflowsSorting.DateDesc;
        draftState.workflowsLoadingStatus = EWorkflowsLoadingStatus.LoadingList;
        draftState.workflowsSearchText = '';
      });

    default:
      return { ...state };
  }
};
