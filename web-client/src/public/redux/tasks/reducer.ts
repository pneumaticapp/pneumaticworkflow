/* eslint-disable */
/* prettier-ignore */
import produce from 'immer';
import { ITaskList, IStoreTasks } from '../../types/redux';
import { ETaskListActions, TTaskListActions } from './actions';
import {
  ETaskListCompletionStatus as ETaskListCompletionStatus,
  ETaskListSorting,
  ITasksSettings,
} from '../../types/tasks';
import { ETaskListStatus } from '../../components/Tasks/types';
import { isObjectChanged } from '../../utils/helpers';
import { EGeneralActions, TGeneralActions } from '../actions';

const INIT_TASKS_LIST = {
  count: 0,
  offset: 0,
  items: [],
} as ITaskList;

const INIT_FILTER_VALUES = {
  templateIdFilter: null,
  stepIdFilter: null,
};

const INIT_TASKS_SETTINGS: ITasksSettings = {
  isHasFilter: false,
  completionStatus: ETaskListCompletionStatus.Active,
  sorting: ETaskListSorting.DateAsc,
  filterValues: INIT_FILTER_VALUES,
  templateList: {
    items: [],
    isLoading: false,
  },
  templateStepList: {
    items: [],
    isLoading: false,
  },
};

export const INIT_STATE: IStoreTasks = {
  taskList: INIT_TASKS_LIST,
  taskListStatus: ETaskListStatus.WaitingForAction,
  taskListDetailedTaskId: null,
  tasksSearchText: '',
  tasksSettings: INIT_TASKS_SETTINGS,
  hasNewTasks: false,
  tasksCount: null,
};

export const reducer = (state = INIT_STATE, action: TTaskListActions | TGeneralActions): IStoreTasks => {
  switch (action.type) {
    case ETaskListActions.SetTaskListStatus:
      return { ...state, taskListStatus: action.payload };

    case ETaskListActions.ChangeTaskListSorting:
      return produce(state, (draftState) => {
        draftState.tasksSettings.sorting = action.payload;
      });

    case ETaskListActions.ChangeTaskListСompletionStatus:
      return produce(state, (draftState) => {
        draftState.tasksSettings.completionStatus = action.payload;
      });

    case ETaskListActions.ChangeTaskList: {
      const { taskList, emptyListStatus = ETaskListStatus.NoTasks } = action.payload;
      const taskListStatus = taskList.items.length === 0 ? emptyListStatus : ETaskListStatus.WaitingForAction;

      return { ...state, taskList, taskListStatus };
    }

    case ETaskListActions.SetTaskListDetailedTaskId:
      return { ...state, taskListDetailedTaskId: action.payload };

    case ETaskListActions.ChangeTasksSearchText:
      return {
        ...state,
        tasksSearchText: action.payload,
      };

    case ETaskListActions.ChangeTasksCount:
      return { ...state, tasksCount: action.payload };

    case ETaskListActions.ResetTasks:
      return {
        ...state,
        taskList: INIT_TASKS_LIST,
        taskListStatus: ETaskListStatus.WaitingForAction,
        hasNewTasks: false,
      };

    case ETaskListActions.ResetTasksFilters:
    case EGeneralActions.ClearAppFilters:
      return {
        ...state,
        tasksSearchText: '',
        tasksSettings: INIT_TASKS_SETTINGS,
      };

    case ETaskListActions.LoadFilterTemplates:
      return produce(state, (draftState) => {
        draftState.tasksSettings.templateList.isLoading = true;
      });

    case ETaskListActions.LoadFilterTemplatesSuccess:
      return produce(state, (draftState) => {
        draftState.tasksSettings.templateList.isLoading = false;
        draftState.tasksSettings.templateList.items = action.payload;
      });

    case ETaskListActions.LoadFilterTemplatesFailed:
      return produce(state, (draftState) => {
        draftState.tasksSettings.templateList.isLoading = false;
      });

    case ETaskListActions.SetFilterTemplate: {
      return produce(state, (draftState) => {
        draftState.tasksSettings.filterValues.templateIdFilter = action.payload;
        draftState.tasksSettings.filterValues.stepIdFilter = null;
        draftState.tasksSettings.templateStepList.items = [];

        draftState.tasksSettings.isHasFilter = areFiltersChanged(draftState.tasksSettings);
      });
    }

    case ETaskListActions.LoadFilterSteps:
      return produce(state, (draftState) => {
        draftState.tasksSettings.templateStepList.isLoading = true;

        draftState.tasksSettings.isHasFilter = areFiltersChanged(draftState.tasksSettings);
      });
    case ETaskListActions.LoadFilterStepsSuccess:
      return produce(state, (draftState) => {
        draftState.tasksSettings.templateStepList.isLoading = false;
        draftState.tasksSettings.templateStepList.items = action.payload;
      });
    case ETaskListActions.LoadFilterStepsFailed:
      return produce(state, (draftState) => {
        draftState.tasksSettings.templateStepList.isLoading = false;
      });
    case ETaskListActions.SetFilterStep:
      return produce(state, (draftState) => {
        draftState.tasksSettings.filterValues.stepIdFilter = action.payload;
      });
    case ETaskListActions.ShowNewTasksNotification:
      return { ...state, hasNewTasks: action.payload };

    case ETaskListActions.ClearFilters:
      return produce(state, (draftState) => {
        draftState.tasksSettings.isHasFilter = false;
        draftState.tasksSettings.filterValues = INIT_FILTER_VALUES;
      });
    case ETaskListActions.PatchTaskInList:
      return produce(state, (draftState) => {
        draftState.taskList.items.forEach((task, index, list) => {
          if (task.id === action.payload.taskId) {
            list[index] = { ...list[index], ...action.payload.task };
          }
        })
      });

    default:
      return { ...state };
  }
};

function areFiltersChanged(state: ITasksSettings) {
  return isObjectChanged(INIT_FILTER_VALUES, state.filterValues);
}
