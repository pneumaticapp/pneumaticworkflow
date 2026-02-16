import { createAction, createSlice, PayloadAction } from '@reduxjs/toolkit';
import { ETaskListStatus } from '../../components/Tasks/types';
import { IStoreTasks, ITaskList } from '../../types/redux';
import {
  ETaskListCompletionStatus,
  ETaskListCompleteSorting,
  ETaskListSorting,
  ITaskListItem,
  ITasksSettings,
  ITemplateStep,
} from '../../types/tasks';
import { ITemplateTitleBaseWithCount } from '../../types/template';
import { isObjectChanged } from '../../utils/helpers';
import { EGeneralActions } from '../general/actions';
import { TLoadFilterStepsPayload, TPatchTaskInListPayload, TShiftTaskListPayload } from './types';

const initTasksList = {
  count: 0,
  offset: 0,
  items: [],
} as ITaskList;

const initFilterValues = {
  templateIdFilter: null,
  taskApiNameFilter: null,
};

const initTasksSettings: ITasksSettings = {
  isHasFilter: false,
  completionStatus: ETaskListCompletionStatus.Active,
  sorting: ETaskListSorting.DateAsc,
  filterValues: initFilterValues,
  templateList: {
    items: [],
    isLoading: false,
  },
  templateStepList: {
    items: [],
    isLoading: false,
  },
};

export const initState: IStoreTasks = {
  taskList: initTasksList,
  taskListStatus: ETaskListStatus.WaitingForAction,
  taskListDetailedTaskId: null,
  tasksSearchText: '',
  tasksSettings: initTasksSettings,
  hasNewTasks: false,
  tasksCount: null,
};

function areFiltersChanged(state: ITasksSettings) {
  return isObjectChanged(initFilterValues, state.filterValues);
}

const tasksSlice = createSlice({
  name: 'tasks',
  initialState: initState,
  reducers: {
    setTaskListStatus: (state, action: PayloadAction<ETaskListStatus>) => {
      state.taskListStatus = action.payload;
    },


    changeTaskListSorting: (state, action: PayloadAction<ETaskListSorting | ETaskListCompleteSorting>) => {
      state.tasksSettings.sorting = action.payload;
    },

    changeTaskListCompletionStatus: (state, action: PayloadAction<ETaskListCompletionStatus>) => {
      state.tasksSettings.completionStatus = action.payload;
    },

    changeTaskList: (state, action: PayloadAction<{ taskList: ITaskList; emptyListStatus?: ETaskListStatus }>) => {
      const { taskList, emptyListStatus = ETaskListStatus.NoTasks } = action.payload;
      const taskListStatus = taskList.items.length === 0 ? emptyListStatus : ETaskListStatus.WaitingForAction;

      state.taskList = taskList;
      state.taskListStatus = taskListStatus;
    },

    setTaskListDetailedTaskId: (state, action: PayloadAction<number | null>) => {
      state.taskListDetailedTaskId = action.payload;
    },

    changeTasksSearchText: (state, action: PayloadAction<string>) => {
      state.tasksSearchText = action.payload;
    },

    changeTasksCount: (state, action: PayloadAction<number | null>) => {
      state.tasksCount = action.payload;
    },

    resetTasks: (state) => {
      state.taskList = initTasksList;
      state.taskListStatus = ETaskListStatus.WaitingForAction;
      state.hasNewTasks = false;
    },

    resetTasksFilters: (state) => {
      state.tasksSearchText = '';
      state.tasksSettings = initTasksSettings;
    },

    loadFilterTemplates: (state) => {
      state.tasksSettings.templateList.isLoading = true;
    },

    loadFilterTemplatesSuccess: (state, action: PayloadAction<ITemplateTitleBaseWithCount[]>) => {
      state.tasksSettings.templateList.isLoading = false;
      state.tasksSettings.templateList.items = action.payload;
    },

    loadFilterTemplatesFailed: (state) => {
      state.tasksSettings.templateList.isLoading = false;
    },
    setFilterTemplate: (state, action: PayloadAction<number | null>) => {
      state.tasksSettings.filterValues.templateIdFilter = action.payload;
      state.tasksSettings.filterValues.taskApiNameFilter = null;
      state.tasksSettings.templateStepList.items = [];
      state.tasksSettings.isHasFilter = areFiltersChanged(state.tasksSettings);
    },


    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    loadFilterSteps: (state, action: PayloadAction<TLoadFilterStepsPayload>) => {
      state.tasksSettings.templateStepList.isLoading = true;
      state.tasksSettings.isHasFilter = areFiltersChanged(state.tasksSettings);
    },

    loadFilterStepsSuccess: (state, action: PayloadAction<ITemplateStep[]>) => {
      state.tasksSettings.templateStepList.isLoading = false;
      state.tasksSettings.templateStepList.items = action.payload;
    },

    loadFilterStepsFailed: (state) => {
      state.tasksSettings.templateStepList.isLoading = false;
    },


    setFilterStep: (state, action: PayloadAction<string | null>) => {
      state.tasksSettings.filterValues.taskApiNameFilter = action.payload;
    },


    showNewTasksNotification: (state, action: PayloadAction<boolean>) => {
      state.hasNewTasks = action.payload;
    },

    clearFilters: (state) => {
      state.tasksSettings.isHasFilter = false;
      state.tasksSettings.filterValues = initFilterValues;
    },

    patchTaskInList: (state, action: PayloadAction<TPatchTaskInListPayload>) => {
      state.taskList.items.forEach((task, index, list) => {
        if (task.id === action.payload.taskId) {
          list[index] = { ...list[index], ...action.payload.task };
        }
      });
    },
  },
  extraReducers: (builder) => {
    builder.addCase(EGeneralActions.ClearAppFilters, (state) => {
      state.tasksSearchText = '';
      state.tasksSettings = initTasksSettings;
    });
  },
});

export const loadTasksCount = createAction<void>('tasks/loadTasksCount');
export const loadTaskList = createAction<number>('tasks/loadTaskList');
export const insertNewTask = createAction<ITaskListItem>('tasks/insertNewTask');
export const searchTasks = createAction<void>('tasks/searchTasks');
export const shiftTaskList = createAction<TShiftTaskListPayload>('tasks/shiftTaskList');

export const {
  setTaskListStatus,
  changeTaskListSorting,
  changeTaskListCompletionStatus,
  changeTaskList,
  setTaskListDetailedTaskId,
  changeTasksSearchText,
  changeTasksCount,
  resetTasks,
  resetTasksFilters,
  loadFilterTemplates,
  loadFilterTemplatesSuccess,
  loadFilterTemplatesFailed,
  setFilterTemplate,
  loadFilterSteps,
  loadFilterStepsSuccess,
  loadFilterStepsFailed,
  setFilterStep,
  showNewTasksNotification,
  clearFilters,
  patchTaskInList,
} = tasksSlice.actions;

export const enum ETaskListActions {
  ChannelAction = 'TASK_LIST_CHANNEL_ACTION',
}

export default tasksSlice.reducer;
