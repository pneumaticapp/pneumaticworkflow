import { connect } from 'react-redux';
import { IApplicationState } from '../../types/redux';
import { ITasksProps, Tasks } from './Tasks';
import {
  loadTaskList,
  changeTasksSorting,
  resetTasks,
  setTaskListDetailedTaskId,
  changeTasksSearchText,
  loadCurrentTask,
  setTasksFilterTemplate,
  setTasksFilterStep,
  showNewTasksNotification,
  searchTasks,
  openSelectTemplateModal,
  resetTasksFilters,
  changeTasksCompleteStatus,
} from '../../redux/actions';
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
  | 'stepIdFilter'
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
      filterValues: { templateIdFilter, stepIdFilter },
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
    stepIdFilter,
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
      defaultAction: changeTasksCompleteStatus(ETaskListCompletionStatus.Active),
      createAction: changeTasksCompleteStatus,
      getQueryParamByProp: (value) => value,
    },
    {
      propName: 'taskSorting',
      queryParamName: 'sorting',
      defaultAction: changeTasksSorting(ETaskListSorting.DateAsc),
      createAction: changeTasksSorting,
      getQueryParamByProp: (value) => value,
    },
    {
      propName: 'templateIdFilter',
      queryParamName: 'template',
      defaultAction: setTasksFilterTemplate(null),
      createAction: (queryParam) => {
        const stepId = Number(queryParam);
        if (Number.isInteger(stepId)) {
          return setTasksFilterTemplate(stepId);
        }

        return setTasksFilterTemplate(null);
      },
      getQueryParamByProp: String,
    },
    {
      propName: 'stepIdFilter',
      queryParamName: 'template-step',
      defaultAction: setTasksFilterStep(null),
      createAction: (queryParam) => {
        const stepId = Number(queryParam);
        if (Number.isInteger(stepId)) {
          return setTasksFilterStep(stepId);
        }

        return setTasksFilterStep(null);
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
