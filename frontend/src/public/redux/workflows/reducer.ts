/* eslint-disable indent */
import produce from 'immer';
import { IWorkflowsList, IStoreWorkflows } from '../../types/redux';
import { EWorkflowsActions, TWorkflowsActions } from './actions';
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
import { getWorkflowViewStorageState, setWorkflowViewStorageState } from '../../utils/workflows/filters';

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
    case EWorkflowsActions.ApplyFilters:
      return produce(state, (draftState) => {
        draftState.workflowsLoadingStatus = EWorkflowsLoadingStatus.LoadingList;
      });

    case EWorkflowsActions.ClearWorkflow:
      return produce(state, (draftState) => {
        draftState.workflow = null;
        draftState.workflowEdit = INIT_WORKFLOW_EDIT;
      });
    case EWorkflowsActions.SetCurrentPerformersCounters:
      return produce(state, (draftState) => {
        draftState.workflowsSettings.counters.performersCounters = action.payload;
      });
    case EWorkflowsActions.SetWorkflowStartersCounters:
      return produce(state, (draftState) => {
        draftState.workflowsSettings.counters.workflowStartersCounters = action.payload;
      });
    case EWorkflowsActions.SetWorkflowsTemplateStepsCounters: {
      return produce(state, (draftState) => {
        draftState.workflowsSettings.templateList.items.forEach((template) => {
          template.steps.forEach((step) => {
            const stepCountInfo = action.payload.find(({ templateTaskId }) => templateTaskId === step.id);
            step.count = stepCountInfo ? stepCountInfo.workflowsCount : 0;
          });
        });
      });
    }
    case EWorkflowsActions.PatchWorkflowInList: {
      const newListItems = state.workflowsList.items.map((workflow) => {
        if (workflow.id !== action.payload.workflowId) {
          return workflow;
        }

        return { ...workflow, ...action.payload.changedFields };
      });

      return produce(state, (draftState) => {
        draftState.workflowsList.items = newListItems;
      });
    }
    case EWorkflowsActions.PatchWorkflowDetailed: {
      return produce(state, (draftState) => {
        if (draftState.workflow?.id === action.payload.workflowId) {
          draftState.workflow = { ...draftState.workflow, ...action.payload.changedFields };
        }
      });
    }
    case EWorkflowsActions.RemoveWorkflowFromList: {
      const { items: workflowsItems, count: workflowsCount, offset: workflowsOffset } = state.workflowsList;

      const newWorkflows = workflowsItems.filter((workflow) => workflow.id !== action.payload.workflowId);
      const isWorkflowRemoved = newWorkflows.length !== workflowsItems.length;

      if (!isWorkflowRemoved) {
        return state;
      }

      const newWorkflowsList = {
        items: newWorkflows,
        count: workflowsCount - 1,
        offset: workflowsOffset - 1,
      };

      return { ...state, workflowsList: newWorkflowsList };
    }
    case EWorkflowsActions.SetWorkflowsView: {
      return produce(state, (draftState) => {
        setWorkflowViewStorageState(action.payload);
        draftState.workflowsSettings.view = action.payload;
      });
    }
    case EWorkflowsActions.OpenTuneViewModal:
      return produce(state, (draftState) => {
        draftState.WorkflowsTuneViewModal.isOpen = true;
      });

    case EWorkflowsActions.CloseTuneViewModal:
      return produce(state, (draftState) => {
        draftState.WorkflowsTuneViewModal.isOpen = false;
      });

    case EWorkflowsActions.SetFilterSelectedFields:
      return produce(state, (draftState) => {
        draftState.workflowsSettings.selectedFields = action.payload;
      });

    case EWorkflowsActions.SetLastLoadedTemplateId:
      return produce(state, (draftState) => {
        draftState.workflowsSettings.lastLoadedTemplateIdForTable = action.payload;
      });
    case EWorkflowsActions.SetWorkflowsPresetsRedux:
      return produce(state, (draftState) => {
        draftState.workflowsSettings.presets = action.payload;
      });

    default:
      return { ...state };
  }
};
