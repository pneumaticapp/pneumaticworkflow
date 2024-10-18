import * as React from 'react';

import { ProgressBar } from '../../ProgressBar';
import { ProgressbarTooltipContents } from '../utils/ProgressbarTooltipContents';
import { getWorkflowProgress } from '../utils/getWorkflowProgress';
import { getWorkflowProgressColor } from '../utils/getWorkflowProgressColor';
import { IWorkflow } from '../../../types/workflow';

interface IWorkflowsProgressProps {
  workflow: IWorkflow;
}
export function WorkflowsProgress({ workflow }: IWorkflowsProgressProps) {
  const { currentTask, tasksCount, status, task } = workflow;
  const progress = getWorkflowProgress({ currentTask, tasksCount, status });
  const color = getWorkflowProgressColor(status, [task.dueDate, workflow.dueDate]);

  return (
    <ProgressBar
      progress={progress}
      color={color}
      background="#fff"
      tooltipContent={<ProgressbarTooltipContents workflow={workflow} />}
    />
  );
}
