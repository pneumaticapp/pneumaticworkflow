import * as React from 'react';
import classnames from 'classnames';
import { Link } from 'react-router-dom';

import { IDashboardCounterProps } from '../Counters';
import { EDashboardModes, IDashboardTask } from '../../../types/redux';
import { DashboardCounters } from '../Counters/DashboardCounters';
import { StepName } from '../../StepName';
import { getLinkToTasks } from '../../../utils/routes/getLinkToTasks';
import { getLinkToWorkflows } from '../../../utils/routes/getLinkToWorkflows';
import { EDashboardCounterType } from '../Counters/types';
import { ETaskListCompletionStatus, ETaskListSorting } from '../../../types/tasks';
import { EWorkflowsSorting, EWorkflowsStatus } from '../../../types/workflow';
import { getTotalTasksCount } from '../../../utils/dashboard';

import styles from './Breakdowns.css';

export interface ITaskItemProps {
  task: IDashboardTask;
  index: number;
  mode: EDashboardModes;
  templateId: number;
}

export function TaskItem({ task, index, mode, templateId }: ITaskItemProps) {
  const { useCallback } = React;

  const getRoute = useCallback(
    (counterType: EDashboardCounterType) => {
      const tasksRouteMap = {
        [EDashboardCounterType.Started]: getLinkToTasks({ templateId, stepId: task.id }),
        [EDashboardCounterType.InProgress]: getLinkToTasks({ templateId, stepId: task.id }),
        [EDashboardCounterType.Overdue]: getLinkToTasks({
          templateId,
          stepId: task.id,
          sorting: ETaskListSorting.Overdue,
        }),
        [EDashboardCounterType.Completed]: getLinkToTasks({
          templateId,
          stepId: task.id,
          status: ETaskListCompletionStatus.Completed,
        }),
      };

      const workflowsRouteMap = {
        [EDashboardCounterType.Started]: getLinkToWorkflows({
          status: EWorkflowsStatus.Running,
          templateId,
          stepId: task.id,
        }),
        [EDashboardCounterType.InProgress]: getLinkToWorkflows({
          status: EWorkflowsStatus.Running,
          templateId,
          stepId: task.id,
        }),
        [EDashboardCounterType.Overdue]: getLinkToWorkflows({
          status: EWorkflowsStatus.Running,
          templateId,
          stepId: task.id,
          sorting: EWorkflowsSorting.Overdue,
        }),
        [EDashboardCounterType.Completed]: getLinkToWorkflows({
          templateId,
          stepId: task.id,
          status: EWorkflowsStatus.Completed,
        }),
      };

      const routeMap = {
        [EDashboardModes.Workflows]: workflowsRouteMap,
        [EDashboardModes.Tasks]: tasksRouteMap,
      };

      return routeMap[mode][counterType];
    },
    [mode],
  );

  const countersParamsList: () => IDashboardCounterProps[] = () => [
    {
      count: task.started,
      color: 'blue',
      className: styles.breakdown__task_card,
      route: getRoute(EDashboardCounterType.Started),
    },
    {
      count: task.inProgress,
      color: 'yellow',
      className: styles.breakdown__task_card,
      route: getRoute(EDashboardCounterType.InProgress),
    },
    {
      count: task.overdue,
      color: 'red',
      className: styles.breakdown__task_card,
      route: getRoute(EDashboardCounterType.Overdue),
    },
    {
      count: task.completed,
      color: 'green',
      className: styles.breakdown__task_card,
      route: getRoute(EDashboardCounterType.Completed),
    },
  ];

  const taskLink =
    mode === EDashboardModes.Tasks
      ? getLinkToTasks({ templateId, stepId: task.id })
      : getLinkToWorkflows({ templateId, stepId: task.id });

  return (
    <div className={styles.task__container}>
      <div className={styles.task__name_container}>
        {mode === EDashboardModes.Workflows && (
          <span className={styles.task__number}>{`${index + 1}`.padStart(2, '0')}</span>
        )}
        <Link
          to={taskLink}
          className={classnames(
            styles.task__name,
            getTotalTasksCount(task) === 0 && styles['task__name_empty'],
            mode === EDashboardModes.Tasks && styles['my_tasks__name'],
          )}
        >
          <StepName initialStepName={task.name} templateId={templateId} />
        </Link>
      </div>
      <DashboardCounters
        countersParamsList={countersParamsList()}
        labelClassName={styles['breakdown__dashboard_task_label']}
        className={styles['breakdown__task_count']}
      />
    </div>
  );
}
