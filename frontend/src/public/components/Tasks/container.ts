import { connect } from 'react-redux';
import { IApplicationState } from '../../types/redux';
import { ITasksProps, Tasks } from './Tasks';
import { loadCurrentTask, openSelectTemplateModal } from '../../redux/actions';
import {
  changeTaskListSorting,
  changeTaskListCompletionStatus,
  setTaskListDetailedTaskId,
  changeTasksSearchText,
  resetTasks,
  resetTasksFilters,
  setFilterTemplate,
  setFilterStep,
  showNewTasksNotification,
  loadTaskList,
  searchTasks,
} from '../../redux/tasks/slice';
import { withSyncedQueryString } from '../../HOCs/withSyncedQueryString';
import { ETaskListCompletionStatus, ETaskListSorting } from '../../types/tasks';
import { checkHasTopBar } from '../TopNav/utils/checkHasTopBar';

type TTasksStoreProps = Pick<
  ITasksProps,
  | 'taskList'
  | 'detailedTaskId'
  | 'detailedTask'
  | 'taskSorting'
  | 'completionStatus'
  | 'templateIdFilter'
  | 'taskApiNameFilter'
  | 'taskListStatus'
  | 'withPaywall'
  | 'hasNewTasks'
  | 'searchText'
  | 'isAdmin'
>;
type TTasksDispatchProps = Pick<
  ITasksProps,
  | 'loadTaskList'
  | 'resetTasks'
  | 'loadDetailedTask'
  | 'setDetailedTaskId'
  | 'changeSearchText'
  | 'showNewTasksNotification'
  | 'openSelectTemplateModal'
  | 'searchTasks'
>;

export function mapStateToProps({
  tasks: {
    taskList,
    taskListStatus,
    taskListDetailedTaskId,
    hasNewTasks,
    tasksSearchText,
    tasksSettings: {
      sorting,
      completionStatus,
      filterValues: { templateIdFilter, taskApiNameFilter },
    },
  },
  task: { data: detailedTask },
  authUser: {
    account: { billingPlan, isBlocked },
    isAdmin,
    isSupermode,
  },
}: IApplicationState): TTasksStoreProps {
  const withPaywall = checkHasTopBar(Boolean(isBlocked), billingPlan, Boolean(isSupermode));

  return {
    withPaywall,
    detailedTask,
    detailedTaskId: taskListDetailedTaskId,
    taskList,
    taskListStatus,
    taskSorting: sorting,
    completionStatus,
    templateIdFilter,
    taskApiNameFilter,
    hasNewTasks,
    searchText: tasksSearchText,
    isAdmin: Boolean(isAdmin),
  };
}

export const mapDispatchToProps: TTasksDispatchProps = {
  loadTaskList,
  resetTasks,
  loadDetailedTask: loadCurrentTask,
  setDetailedTaskId: setTaskListDetailedTaskId,
  changeSearchText: changeTasksSearchText,
  showNewTasksNotification,
  openSelectTemplateModal,
  searchTasks,
};

const SyncedTasks = withSyncedQueryString<TTasksStoreProps>(
  [
    {
      propName: 'completionStatus',
      queryParamName: 'status',
      defaultAction: changeTaskListCompletionStatus(ETaskListCompletionStatus.Active),
      createAction: changeTaskListCompletionStatus,
      getQueryParamByProp: (value) => value,
    },
    {
      propName: 'taskSorting',
      queryParamName: 'sorting',
      defaultAction: changeTaskListSorting(ETaskListSorting.DateAsc),
      createAction: changeTaskListSorting,
      getQueryParamByProp: (value) => value,
    },
    {
      propName: 'templateIdFilter',
      queryParamName: 'template',
      defaultAction: setFilterTemplate(null),
      createAction: (queryParam) => {
        const stepId = Number(queryParam);
        if (Number.isInteger(stepId)) {
          return setFilterTemplate(stepId);
        }

        return setFilterTemplate(null);
      },
      getQueryParamByProp: String,
    },
    {
      propName: 'taskApiNameFilter',
      queryParamName: 'template-task',
      defaultAction: setFilterStep(null),
      createAction: (queryParam) => {
        const taskApiNAme = queryParam;
        if (taskApiNAme) {
          return setFilterStep(taskApiNAme);
        }

        return setFilterStep(null);
      },
      getQueryParamByProp: String,
    },
  ],
  resetTasksFilters(),
)(Tasks);

export const TasksContainer = connect<TTasksStoreProps, TTasksDispatchProps>(
  mapStateToProps,
  mapDispatchToProps,
)(SyncedTasks);
