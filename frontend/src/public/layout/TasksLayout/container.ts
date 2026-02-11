import { connect } from 'react-redux';

import { IApplicationState } from '../../types/redux';
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

import { ITasksLayoutDispatchProps, ITasksLayoutStoreProps, TasksLayoutComponent } from './TasksLayout';

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
}: IApplicationState): ITasksLayoutStoreProps => {
  return {
    isHasFilter,
    sorting,
    filterTemplates: templateList.items,
    filterSteps: templateStepList.items,
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
