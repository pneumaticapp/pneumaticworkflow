import { connect } from 'react-redux';

import type { RootState } from '../../redux/store';
import {
  changeTaskListSorting,
  changeTaskListCompletionStatus,
  loadFilterTemplates,
  setFilterTemplate,
  loadFilterSteps,
  setFilterStep,
  clearFilters,
} from '../../redux/tasks/slice';
import { closeWorkflowLogPopup } from '../../redux/workflows/slice';

import type { ITasksLayoutDispatchProps, ITasksLayoutStoreProps } from './TasksLayout';
import { TasksLayoutComponent } from './TasksLayout';

const mapStateToProps = ({
  tasks: {
    tasksSettings: {
      sorting,
      isHasFilter,
      completionStatus,
      filterValues: { templateIdFilter, taskApiNameFilter },
      templateList,
      templateStepList,
    },
  },
}: RootState): ITasksLayoutStoreProps => {
  return {
    isHasFilter,
    sorting,
    filterTemplates: templateList.items,
    filterSteps: templateStepList.items,
    areFilterTemplatesLoading: templateList.isLoading,
    areFilterStepsLoading: templateStepList.isLoading,
    templateIdFilter,
    taskApiNameFilter,
    completionStatus,
  };
};

const mapDispatchToProps: ITasksLayoutDispatchProps = {
  loadFilterTemplates,
  loadFilterSteps,
  setFilterTemplate,
  setFilterStep,
  clearFilters,
  closeWorkflowLogPopup,
  changeTaskListCompletionStatus,
  changeTaskListSorting,
};

export const TasksLayoutContainer = connect<ITasksLayoutStoreProps, ITasksLayoutDispatchProps>(
  mapStateToProps,
  mapDispatchToProps,
)(TasksLayoutComponent);
