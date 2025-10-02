import * as React from 'react';

import { ProgressBar } from '../../ProgressBar';
import { ProgressbarTooltipContents } from '../utils/ProgressbarTooltipContents';
import { getWorkflowProgress } from '../utils/getWorkflowProgress';
import { getWorkflowProgressColor } from '../utils/getWorkflowProgressColor';
import { IWorkflowClient } from '../../../types/workflow';

interface IWorkflowsProgressProps {
  workflow: IWorkflowClient;
}
export function WorkflowsProgress({ workflow }: IWorkflowsProgressProps) {
  const { completedTasks, tasksCountWithoutSkipped, status, oldestDeadline, areOverdueTasks } = workflow;
  const progress = getWorkflowProgress({ completedTasks, tasksCountWithoutSkipped });
  const color = getWorkflowProgressColor(status, [areOverdueTasks ? oldestDeadline : '', workflow.dueDate]);

  return (
    <ProgressBar
      progress={progress}
      color={color}
      background="#fff"
      tooltipContent={<ProgressbarTooltipContents workflow={workflow} />}
    />
  );
}
