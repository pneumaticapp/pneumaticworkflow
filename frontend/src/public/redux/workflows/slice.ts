import { createAction, createSlice, PayloadAction } from '@reduxjs/toolkit';

import { isDesktop } from '../../utils/media';
import { getWorkflowViewStorageState, setWorkflowViewStorageState } from '../../utils/workflows/filters';
import { isArrayWithItems, isObjectChanged } from '../../utils/helpers';

import { EGeneralActions } from '../general/actions';

import { IDeleteReaction } from '../../api/workflows/deleteReactionComment';
import { ICreateReaction } from '../../api/workflows/createReactionComment';
import { IWatchedComment } from '../../api/workflows/watchedComment';
import { IDeleteComment } from '../../api/workflows/deleteComment';
import { IEditComment } from '../../api/workflows/editComment';

import { IStoreWorkflows, IWorkflowLog, IWorkflowsList } from '../../types/redux';
import { IKickoff, ITemplateTitleBaseWithCount, TTemplatePreset } from '../../types/template';
import { ITemplateStep } from '../../types/tasks';
import {
  EWorkflowsLoadingStatus,
  EWorkflowsLogSorting,
  EWorkflowsSorting,
  EWorkflowsStatus,
  EWorkflowsView,
  IWorkflowClient,
  IWorkflowDetailsClient,
  IWorkflowEditData,
  IWorkflowLogItem,
  IWorkflowsSettings,
  TTemplateStepCounter,
  TUserCounter,
} from '../../types/workflow';

import {
  IChangeWorkflowLogViewSettingsPayload,
  ISaveWorkflowsPresetPayload,
  ISendWorkflowLogComment,
  TCloneWorkflowPayload,
  TDeleteWorkflowPayload,
  TEditWorkflowPayload,
  TLoadWorkflowsFilterStepsPayload,
  TOpenWorkflowLogPopupPayload,
  TRemoveWorkflowFromListPayload,
  TReturnWorkflowToTaskPayload,
  TSetWorkflowFinishedPayload,
  TSetWorkflowResumedPayload,
  TSnoozeWorkflowPayload,
} from './types';

const initialWorkflowsList = {
  count: -1,
  offset: 0,
  items: [],
} as IWorkflowsList;

export const initialWorkflowsFilters: IWorkflowsSettings['values'] = {
  statusFilter: EWorkflowsStatus.Running,
  templatesIdsFilter: [],
  tasksApiNamesFilter: [],
  performersIdsFilter: [],
  performersGroupIdsFilter: [],
  workflowStartersIdsFilter: [],
};

const initialWorkflowEdit = {
  workflow: {
    name: '',
    kickoff: { description: '', fields: [] } as IKickoff,
  },
  isWorkflowNameEditing: false,
  isKickoffEditing: false,
  isKickoffSaving: false,
  isWorkflowNameSaving: false,
};

export const initialState: IStoreWorkflows = {
  workflowsList: initialWorkflowsList,
  workflowsLoadingStatus: EWorkflowsLoadingStatus.Loaded,
  workflow: null,
  isWorkflowLoading: false,
  workflowEdit: initialWorkflowEdit,
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
    values: initialWorkflowsFilters,
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

const checkFiltersChanged = (state: IStoreWorkflows) => {
  return isObjectChanged(initialWorkflowsFilters, state.workflowsSettings.values);
};

const updateWorkflowsFilterValue = <T extends keyof IWorkflowsSettings['values']>(
  state: IStoreWorkflows,
  filter: T,
  value: IWorkflowsSettings['values'][T],
) => {
  state.workflowsSettings.values[filter] = value;
  state.workflowsSettings.areFiltersChanged = checkFiltersChanged(state);
};

const workflowsSlice = createSlice({
  name: 'workflows',
  initialState,
  reducers: {
    openWorkflowLogPopup: (state, action: PayloadAction<TOpenWorkflowLogPopupPayload>) => {
      state.workflowLog.isOpen = true;
      state.workflowLog.workflowId = action.payload.workflowId;
    },
    closeWorkflowLogPopup: (state) => {
      state.workflowLog.isOpen = false;
      state.workflowLog.isOnlyAttachmentsShown = false;
    },
    changeWorkflowsSorting: (state, action: PayloadAction<EWorkflowsSorting>) => {
      state.workflowsSettings.sorting = action.payload;
    },
    changeWorkflow: (state, action: PayloadAction<IWorkflowDetailsClient | null>) => {
      state.workflow = action.payload;
    },
    changeWorkflowsList: (state, action: PayloadAction<IWorkflowsList>) => {
      state.workflowsList = action.payload;
      state.workflowsLoadingStatus = isArrayWithItems(action.payload.items)
        ? EWorkflowsLoadingStatus.Loaded
        : EWorkflowsLoadingStatus.EmptyList;
    },
    changeWorkflowLog: (state, action: PayloadAction<Partial<IWorkflowLog>>) => {
      state.workflowLog = { ...state.workflowLog, ...action.payload };
    },
    updateWorkflowLogItem: (state, action: PayloadAction<IWorkflowLogItem>) => {
      const index = state.workflowLog.items.findIndex((item) => item.id === action.payload.id);

      if (index !== -1) {
        state.workflowLog.items[index] = action.payload;
      } else {
        state.workflowLog.items = [action.payload, ...state.workflowLog.items];
      }
    },
    changeWorkflowLogViewSettings: (state, action: PayloadAction<IChangeWorkflowLogViewSettingsPayload>) => {
      state.workflowLog.isCommentsShown = action.payload.comments;
      state.workflowLog.isOnlyAttachmentsShown = action.payload.isOnlyAttachmentsShown;
      state.workflowLog.sorting = action.payload.sorting;
    },
    changeWorkflowsSearchText: (state, action: PayloadAction<string>) => {
      state.workflowsLoadingStatus = EWorkflowsLoadingStatus.LoadingList;
      state.workflowsSearchText = action.payload;
    },
    setWorkflowIsLoading: (state, action: PayloadAction<boolean>) => {
      state.isWorkflowLoading = action.payload;
    },
    loadWorkflowsList: (state, action: PayloadAction<number>) => {
      state.workflowsLoadingStatus =
        action.payload === 0 ? EWorkflowsLoadingStatus.LoadingList : EWorkflowsLoadingStatus.LoadingNextPage;
    },
    loadWorkflow: (state, action: PayloadAction<number | null>) => {
      state.workflowLog.workflowId = action.payload;
    },
    loadWorkflowsListFailed: (state) => {
      state.workflowsLoadingStatus = EWorkflowsLoadingStatus.Loaded;
    },
    loadFilterTemplates: (state) => {
      state.workflowsSettings.templateList.isLoading = true;
    },
    loadFilterTemplatesSuccess: (state, action: PayloadAction<ITemplateTitleBaseWithCount[]>) => {
      state.workflowsSettings.templateList.isLoading = false;
      state.workflowsSettings.templateList.items = action.payload.map(
        (template, index) => ({
          ...template,
          steps: state.workflowsSettings.templateList.items[index]?.steps || [],
          areStepsLoading: false,
        }),
      );
    },
    loadFilterTemplatesFailed: (state) => {
      state.workflowsSettings.templateList.isLoading = false;
    },
    loadFilterSteps: (state, action: PayloadAction<TLoadWorkflowsFilterStepsPayload>) => {
      const templateIndex = state.workflowsSettings.templateList.items.findIndex((template) => {
        return template.id === action.payload.templateId;
      });

      if (templateIndex === -1) {
        return;
      }

      state.workflowsSettings.templateList.items[templateIndex].areStepsLoading = true;
    },
    loadFilterStepsSuccess: (state, action: PayloadAction<{ templateId: number; steps: ITemplateStep[] }>) => {
      const templateIndex = state.workflowsSettings.templateList.items.findIndex((template) => {
        return template.id === action.payload.templateId;
      });
      if (templateIndex === -1) {
        return;
      }

      state.workflowsSettings.templateList.items[templateIndex].areStepsLoading = false;
      state.workflowsSettings.templateList.items[templateIndex].steps = action.payload.steps;
    },
    loadFilterStepsFailed: (state, action: PayloadAction<{ templateId: number }>) => {
      const templateIndex = state.workflowsSettings.templateList.items.findIndex((template) => {
        return template.id === action.payload.templateId;
      });

      if (templateIndex === -1) {
        return;
      }

      state.workflowsSettings.templateList.items[templateIndex].areStepsLoading = false;
    },
    setFilterStatus: (state, action: PayloadAction<EWorkflowsStatus>) => {
      updateWorkflowsFilterValue(state, 'statusFilter', action.payload);
    },

    setFilterTemplate: (state, action: PayloadAction<(number | undefined)[]>) => {
      const filtered = action.payload.filter((id): id is number => id !== undefined);
      updateWorkflowsFilterValue(state, 'templatesIdsFilter', filtered);
    },

    setFilterTemplateTasks: (state, action: PayloadAction<string[]>) => {
      updateWorkflowsFilterValue(state, 'tasksApiNamesFilter', action.payload);

    },
    setFilterPerformers: (state, action: PayloadAction<number[]>) => {
      updateWorkflowsFilterValue(state, 'performersIdsFilter', action.payload);
    },
    setFilterPerformersGroup: (state, action: PayloadAction<number[]>) => {
      updateWorkflowsFilterValue(state, 'performersGroupIdsFilter', action.payload);
    },
    setFilterWorkflowStarters: (state, action: PayloadAction<number[]>) => {
      updateWorkflowsFilterValue(state, 'workflowStartersIdsFilter', action.payload);
    },

    setIsEditWorkflowName: (state, action: PayloadAction<boolean>) => {
      state.workflowEdit.isWorkflowNameEditing = action.payload;
    },
    setIsEditKickoff: (state, action: PayloadAction<boolean>) => {
      state.workflowEdit.isKickoffEditing = action.payload;
    },
    setIsSavingWorkflowName: (state, action: PayloadAction<boolean>) => {
      state.workflowEdit.isWorkflowNameSaving = action.payload;
    },
    setIsSavingKickoff: (state, action: PayloadAction<boolean>) => {
      state.workflowEdit.isKickoffSaving = action.payload;
    },
    setWorkflowEdit: (state, action: PayloadAction<IWorkflowEditData>) => {
      state.workflowEdit.workflow = action.payload;
    },
    resetWorkflows: (state) => {
      state.workflowsList = initialWorkflowsList;
      state.workflowLog.isOpen = false;
    },
    clearFilters: (state) => {
      state.workflowsSettings.values = initialWorkflowsFilters;
      state.workflowsSettings.areFiltersChanged = false;
      state.workflowsSettings.sorting = EWorkflowsSorting.DateDesc;
      state.workflowsLoadingStatus = EWorkflowsLoadingStatus.LoadingList;
      state.workflowsSearchText = '';
    },
    applyFilters: (state) => {
      state.workflowsLoadingStatus = EWorkflowsLoadingStatus.LoadingList;
    },
    clearWorkflow: (state) => {
      state.workflow = null;
      state.workflowEdit = initialWorkflowEdit;
    },
    setCurrentPerformersCounters: (state, action: PayloadAction<TUserCounter[]>) => {
      state.workflowsSettings.counters.performersCounters = action.payload;
    },
    setWorkflowStartersCounters: (state, action: PayloadAction<TUserCounter[]>) => {
      state.workflowsSettings.counters.workflowStartersCounters = action.payload;
    },
    setWorkflowsTemplateStepsCounters: (state, action: PayloadAction<TTemplateStepCounter[]>) => {
      state.workflowsSettings.templateList.items.forEach((template) => {
        template.steps.forEach((step) => {
          const stepCountInfo = action.payload.find(({ templateTaskApiName }) => templateTaskApiName === step.apiName);
          step.count = stepCountInfo ? stepCountInfo.workflowsCount : 0;
        });
      });
    },
    patchWorkflowInList: (state, action: PayloadAction<{ workflowId: number; changedFields: Partial<IWorkflowClient> }>) => {
      const newListItems = state.workflowsList.items.map((workflow) => {
        if (workflow.id !== action.payload.workflowId) {
          return workflow;
        }

        return { ...workflow, ...action.payload.changedFields };
      });

      state.workflowsList.items = newListItems;
    },
    patchWorkflowDetailed: (state, action: PayloadAction<{ workflowId: number; changedFields: Partial<IWorkflowDetailsClient> }>) => {
      if (state.workflow?.id === action.payload.workflowId) {
        state.workflow = { ...state.workflow, ...action.payload.changedFields };
      }
    },
    removeWorkflowFromList: (state, action: PayloadAction<TRemoveWorkflowFromListPayload>) => {
      const { items: workflowsItems, count: workflowsCount, offset: workflowsOffset } = state.workflowsList;

      const newWorkflows = workflowsItems.filter((workflow) => workflow.id !== action.payload.workflowId);
      const isWorkflowRemoved = newWorkflows.length !== workflowsItems.length;

      if (!isWorkflowRemoved) {
        return;
      }

      const newWorkflowsList = {
        items: newWorkflows,
        count: workflowsCount - 1,
        offset: workflowsOffset - 1,
      };

      state.workflowsList = newWorkflowsList;
    },
    setWorkflowsView: (state, action: PayloadAction<EWorkflowsView>) => {
      setWorkflowViewStorageState(action.payload);
      state.workflowsSettings.view = action.payload;
    },
    openTuneViewModal: (state) => {
      state.WorkflowsTuneViewModal.isOpen = true;
    },
    closeTuneViewModal: (state) => {
      state.WorkflowsTuneViewModal.isOpen = false;
    },
    setFilterSelectedFields: (state, action: PayloadAction<string[]>) => {
      state.workflowsSettings.selectedFields = action.payload;
    },
    setLastLoadedTemplateId: (state, action: PayloadAction<string | null>) => {
      state.workflowsSettings.lastLoadedTemplateIdForTable = action.payload;
    },
    setWorkflowsPresetsRedux: (state, action: PayloadAction<TTemplatePreset[]>) => {
      state.workflowsSettings.presets = action.payload;
    },
  },
  extraReducers: (builder) => {
    builder.addCase(EGeneralActions.ClearAppFilters, (state) => {
      state.workflowsSettings.values = initialWorkflowsFilters;
      state.workflowsSettings.areFiltersChanged = false;
      state.workflowsSettings.sorting = EWorkflowsSorting.DateDesc;
      state.workflowsLoadingStatus = EWorkflowsLoadingStatus.LoadingList;
      state.workflowsSearchText = '';
    });
  },
});

export const deleteReactionComment = createAction<IDeleteReaction>('workflows/deleteReactionComment');
export const createReactionComment = createAction<ICreateReaction>('workflows/createReactionComment');
export const watchedComment = createAction<IWatchedComment>('workflows/watchedComment');
export const editWorkflowSuccess = createAction<void>('workflows/editWorkflowSuccess');
export const editWorkflow = createAction<TEditWorkflowPayload>('workflows/editWorkflow');
export const setWorkflowResumed = createAction<TSetWorkflowResumedPayload>('workflows/setWorkflowResumed');
export const setWorkflowFinished = createAction<TSetWorkflowFinishedPayload>('workflows/setWorkflowFinished');
export const sendWorkflowLogComments = createAction<ISendWorkflowLogComment>('workflows/sendWorkflowLogComments');
export const deleteWorkflowAction = createAction<TDeleteWorkflowPayload>('workflows/deleteWorkflowAction');
export const returnWorkflowToTaskAction = createAction<TReturnWorkflowToTaskPayload>(
  'workflows/returnWorkflowToTaskAction',
);
export const cloneWorkflowAction = createAction<TCloneWorkflowPayload>('workflows/cloneWorkflowAction');
export const updateCurrentPerformersCounters = createAction<void>('workflows/updateCurrentPerformersCounters');
export const updateWorkflowStartersCounters = createAction<void>('workflows/updateWorkflowStartersCounters');
export const updateWorkflowsTemplateStepsCounters = createAction<void>(
  'workflows/updateWorkflowsTemplateStepsCounters',
);
export const snoozeWorkflow = createAction<TSnoozeWorkflowPayload>('workflows/snoozeWorkflow');
export const deleteComment = createAction<IDeleteComment>('workflows/deleteComment');
export const editComment = createAction<IEditComment>('workflows/editComment');
export const saveWorkflowsPreset = createAction<ISaveWorkflowsPresetPayload>('workflows/saveWorkflowsPreset');

export const {
  openWorkflowLogPopup,
  closeWorkflowLogPopup,
  changeWorkflowsSorting,
  changeWorkflow,
  changeWorkflowsList,
  changeWorkflowLog,
  updateWorkflowLogItem,
  changeWorkflowLogViewSettings,
  changeWorkflowsSearchText,
  setWorkflowIsLoading,
  loadWorkflowsList,
  loadWorkflow,
  loadWorkflowsListFailed,
  loadFilterTemplates,
  loadFilterTemplatesSuccess,
  loadFilterTemplatesFailed,
  loadFilterSteps,
  loadFilterStepsSuccess,
  loadFilterStepsFailed,
  setFilterStatus,
  setFilterTemplate,
  setFilterTemplateTasks,
  setFilterPerformers,
  setFilterPerformersGroup,
  setFilterWorkflowStarters,
  setIsEditWorkflowName,
  setIsEditKickoff,
  setIsSavingWorkflowName,
  setIsSavingKickoff,
  setWorkflowEdit,
  resetWorkflows,
  clearFilters,
  applyFilters,
  clearWorkflow,
  setCurrentPerformersCounters,
  setWorkflowStartersCounters,
  setWorkflowsTemplateStepsCounters,
  patchWorkflowInList,
  patchWorkflowDetailed,
  removeWorkflowFromList,
  setWorkflowsView,
  openTuneViewModal,
  closeTuneViewModal,
  setFilterSelectedFields,
  setLastLoadedTemplateId,
  setWorkflowsPresetsRedux,
} = workflowsSlice.actions;

export default workflowsSlice.reducer;
