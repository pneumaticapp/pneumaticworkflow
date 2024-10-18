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
import { isArrayWithItems, isObjectChanged } from '../../utils/helpers';
import { EGeneralActions, TGeneralActions } from '../actions';
import { getWorkflowViewStorageState, setWorkflowViewStorageState } from '../../utils/workflows/filters';

const INIT_WORKFLOWS_LIST = {
  count: -1,
  offset: 0,
  items: [],
} as IWorkflowsList;

export const INITIAL_WORKFLOWS_FILTERS: IWorkflowsSettings['values'] = {
  statusFilter: EWorkflowsStatus.All,
  templatesIdsFilter: [],
  stepsIdsFilter: [],
  performersIdsFilter: [],
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
    templateList: {
      items: [],
      isLoading: false,
    },
    counters: {
      workflowStartersCounters: [],
      performersCounters: [],
    },
  },
  isUrgent: false,
};

export const reducer = (state = INIT_STATE, action: TWorkflowsActions | TGeneralActions): IStoreWorkflows => {
  switch (action.type) {
    case EWorkflowsActions.OpenWorkflowLogPopup:
      return produce(state, (draftState) => {
        draftState.workflowLog.isOpen = true;
        draftState.workflowLog.workflowId = action.payload.workflowId;
      });
    case EWorkflowsActions.CloseWorkflowLogPopup:
      return produce(state, (draftState) => {
        draftState.workflowLog.isOpen = false;
        draftState.workflowLog.isOnlyAttachmentsShown = false;
      });
    case EWorkflowsActions.ChangeWorkflowsSorting:
      return produce(state, (draftState) => {
        draftState.workflowsSettings.sorting = action.payload;
      });
    case EWorkflowsActions.ChangeWorkflow:
      return produce(state, (draftState) => {
        draftState.workflow = action.payload;
      });
    case EWorkflowsActions.ChangeWorkflowsList:
      return produce(state, (draftState) => {
        draftState.workflowsList = action.payload;
        draftState.workflowsLoadingStatus = isArrayWithItems(action.payload.items)
          ? EWorkflowsLoadingStatus.Loaded
          : EWorkflowsLoadingStatus.EmptyList;
      });
    case EWorkflowsActions.ChangeWorkflowLog:
      return produce(state, (draftState) => {
        draftState.workflowLog = { ...state.workflowLog, ...action.payload };
      });

    case EWorkflowsActions.UpdateWorkflowLogItem:
      return produce(state, (draftState) => {
        const index = draftState.workflowLog.items.findIndex((item) => item.id === action.payload.id);

        if (index !== -1) {
          draftState.workflowLog.items[index] = action.payload;
        } else {
          draftState.workflowLog.items = [action.payload, ...draftState.workflowLog.items];
        }
      });

    case EWorkflowsActions.ChangeWorkflowLogViewSettings:
      return produce(state, (draftState) => {
        draftState.workflowLog.isCommentsShown = action.payload.comments;
        draftState.workflowLog.isOnlyAttachmentsShown = action.payload.isOnlyAttachmentsShown;
        draftState.workflowLog.sorting = action.payload.sorting;
      });
    case EWorkflowsActions.ChangeWorkflowsSearchText:
      return {
        ...state,
        workflowsLoadingStatus: EWorkflowsLoadingStatus.LoadingList,
        workflowsSearchText: action.payload,
      };
    case EWorkflowsActions.SetWorkflowIsLoading:
      return produce(state, (draftState) => {
        draftState.isWorkflowLoading = action.payload;
      });
    case EWorkflowsActions.LoadWorkflowsList:
      return {
        ...state,
        workflowsLoadingStatus:
          action.payload === 0 ? EWorkflowsLoadingStatus.LoadingList : EWorkflowsLoadingStatus.LoadingNextPage,
      };
    case EWorkflowsActions.LoadWorkflow:
      return produce(state, (draftState) => {
        draftState.workflowLog.workflowId = action.payload;
      });
    case EWorkflowsActions.LoadWorkflowsListFailed:
      return {
        ...state,
        workflowsLoadingStatus: EWorkflowsLoadingStatus.Loaded,
      };
    case EWorkflowsActions.EditWorkflow:
      return { ...state, saving: true };
    case EWorkflowsActions.EditWorkflowSuccess:
      return { ...state, saving: false };
    case EWorkflowsActions.LoadFilterTemplates:
      return produce(state, (draftState) => {
        draftState.workflowsSettings.templateList.isLoading = true;
      });
    case EWorkflowsActions.LoadFilterTemplatesSuccess:
      return produce(state, (draftState) => {
        draftState.workflowsSettings.templateList.isLoading = false;
        draftState.workflowsSettings.templateList.items = action.payload.map((template, index) => ({
          ...template,
          steps: draftState.workflowsSettings.templateList.items[index]?.steps || [],
          areStepsLoading: false,
        }));
      });
    case EWorkflowsActions.LoadFilterTemplatesFailed:
      return produce(state, (draftState) => {
        draftState.workflowsSettings.templateList.isLoading = false;
      });
    case EWorkflowsActions.LoadFilterSteps: {
      const templateIndex = state.workflowsSettings.templateList.items.findIndex((template) => {
        return template.id === action.payload.templateId;
      });

      if (templateIndex === -1) {
        return state;
      }

      return produce(state, (draftState) => {
        draftState.workflowsSettings.templateList.items[templateIndex].areStepsLoading = true;
      });
    }
    case EWorkflowsActions.LoadFilterStepsSuccess: {
      const templateIndex = state.workflowsSettings.templateList.items.findIndex((template) => {
        return template.id === action.payload.templateId;
      });
      if (templateIndex === -1) {
        return state;
      }

      return produce(state, (draftState) => {
        draftState.workflowsSettings.templateList.items[templateIndex].areStepsLoading = false;
        draftState.workflowsSettings.templateList.items[templateIndex].steps = action.payload.steps;
      });
    }
    case EWorkflowsActions.LoadFilterStepsFailed: {
      const templateIndex = state.workflowsSettings.templateList.items.findIndex((template) => {
        return template.id === action.payload.templateId;
      });

      if (templateIndex === -1) {
        return state;
      }

      return produce(state, (draftState) => {
        draftState.workflowsSettings.templateList.items[templateIndex].areStepsLoading = false;
      });
    }
    case EWorkflowsActions.SetFilterStatus:
      return updateWorkflowsFilterValue(state, 'statusFilter', action.payload);
    case EWorkflowsActions.SetFilterTemplate:
      return updateWorkflowsFilterValue(state, 'templatesIdsFilter', action.payload);
    case EWorkflowsActions.SetFilterTemplateSteps:
      return updateWorkflowsFilterValue(state, 'stepsIdsFilter', action.payload);
    case EWorkflowsActions.SetFilterPerformers:
      return updateWorkflowsFilterValue(state, 'performersIdsFilter', action.payload);
    case EWorkflowsActions.SetFilterWorkflowStarters:
      return updateWorkflowsFilterValue(state, 'workflowStartersIdsFilter', action.payload);
    case EWorkflowsActions.SetIsEditWorkflowName:
      return produce(state, (draftState) => {
        draftState.workflowEdit.isWorkflowNameEditing = action.payload;
      });
    case EWorkflowsActions.SetIsEditKickoff:
      return produce(state, (draftState) => {
        draftState.workflowEdit.isKickoffEditing = action.payload;
      });
    case EWorkflowsActions.SetIsSavingWorkflowName:
      return produce(state, (draftState) => {
        draftState.workflowEdit.isWorkflowNameSaving = action.payload;
      });
    case EWorkflowsActions.SetIsSavingKickoff:
      return produce(state, (draftState) => {
        draftState.workflowEdit.isKickoffSaving = action.payload;
      });
    case EWorkflowsActions.SetWorkflowEdit:
      return produce(state, (draftState) => {
        draftState.workflowEdit.workflow = action.payload;
      });
    case EWorkflowsActions.ResetWorkflows:
      return produce(state, (draftState) => {
        draftState.workflowsList = INIT_WORKFLOWS_LIST;
        draftState.workflowLog.isOpen = false;
      });
    case EWorkflowsActions.ClearFilters:
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
          })
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

    default:
      return { ...state };
  }
};

const updateWorkflowsFilterValue = <T extends keyof IWorkflowsSettings['values']>(
  state: IStoreWorkflows,
  filter: T,
  newValue: IWorkflowsSettings['values'][T],
) => {
  return produce(state, (draftState) => {
    draftState.workflowsSettings.values[filter] = newValue;
    draftState.workflowsSettings.areFiltersChanged = checkFiltersChanged(draftState);
  });
};

const checkFiltersChanged = (state: IStoreWorkflows) => {
  return isObjectChanged(INITIAL_WORKFLOWS_FILTERS, state.workflowsSettings.values);
};
