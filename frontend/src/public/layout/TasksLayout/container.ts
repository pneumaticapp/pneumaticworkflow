import { connect } from 'react-redux';

import { IApplicationState } from '../../types/redux';
import {
  setTasksFilterTemplate,
  setTasksFilterStep,
  loadTasksFilterTemplates,
  loadTasksFilterSteps,
  clearTasksFilters,
  closeWorkflowLogPopup,
  changeTasksSorting,
  changeTasksCompleteStatus,
} from '../../redux/actions';
import {
  ITasksLayoutDispatchProps,
  ITasksLayoutStoreProps,
  TasksLayoutComponent,
} from './TasksLayout';

const mapStateToProps = ({
  tasks: {
    tasksSettings:
    {
      sorting,
      isHasFilter,
      completionStatus,
      filterValues: {
        templateIdFilter,
        stepIdFilter,
      },
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
    stepIdFilter,
    completionStatus,
  };
};

const mapDispatchToProps: ITasksLayoutDispatchProps = {
  loadTasksFilterTemplates,
  loadTasksFilterSteps,
  setTasksFilterTemplate,
  setTasksFilterStep,
  clearFilters: clearTasksFilters,
  closeWorkflowLogPopup,
  changeTasksCompleteStatus,
  changeTasksSorting,
};

export const TasksLayoutContainer = connect<ITasksLayoutStoreProps, ITasksLayoutDispatchProps>
(mapStateToProps, mapDispatchToProps)(TasksLayoutComponent);
